"""
EDA Crew Orchestration
Coordinates all agents to perform comprehensive exploratory data analysis.
"""

import os
import time
from typing import Optional

import pandas as pd

from crewai import Agent, Crew, Process, Task, LLM
from dotenv import load_dotenv

from src.agents.profiler import create_profiler_agent
from src.agents.cleaner import create_cleaner_agent
from src.agents.visualizer import create_visualizer_agent
from src.agents.statistician import create_statistician_agent
from src.agents.reporter import create_reporter_agent
from src.agents.model_recommender import create_model_recommender_agent
from src.agents.xai_agent import create_xai_agent

from src.tools.data_tools import (
    ProfileDatasetTool,
    DetectOutliersTool,
    CleanMissingValuesTool,
    GetColumnInfoTool,
    GetDataSummaryTool,
    DataStore,
)
from src.tools.viz_tools import (
    GenerateDistributionPlotsTool,
    GenerateCorrelationHeatmapTool,
    GenerateCategoricalChartsTool,
    GenerateBoxPlotsTool,
    GenerateMissingValuesPlotTool,
    GenerateDataQualitySummaryTool,
    GenerateCleaningImpactPlotTool,
    VizConfig,
)
from src.tools.stats_tools import (
    DescriptiveStatsTool,
    CorrelationAnalysisTool,
    CategoricalAnalysisTool,
    DetectPatternsTool,
    NormalityTestTool,
)
from src.tools.ml_tools import (
    SuggestModelsBasedOnDataTool,
    TrainSimpleModelTool,
)
from src.tools.xai_tools import (
    GenerateSHAPSummaryTool,
    GenerateLIMEExplanationTool,
    CompareFeatureImportanceTool,
    XAIConfig,
)

# Load environment variables
load_dotenv()


class EDACrew:
    """
    Orchestrates the multi-agent EDA workflow.
    """
    
    def __init__(self, output_dir: str = "output", progress_tracker=None):
        """
        Initialize the EDA Crew.
        
        Args:
            output_dir: Directory for output files
            progress_tracker: Optional progress tracker for real-time updates
        """
        self.output_dir = output_dir
        self.charts_dir = os.path.join(output_dir, "charts")
        self.progress_tracker = progress_tracker
        
        # Create output directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.charts_dir, exist_ok=True)
        
        # Configure visualization output
        VizConfig.set_output_dir(self.charts_dir)
        
        # Initialize LLM
        self.llm = self._create_llm()
        
        # Create agents
        self.profiler = create_profiler_agent(self.llm)
        self.cleaner = create_cleaner_agent(self.llm)
        self.visualizer = create_visualizer_agent(self.llm)
        self.statistician = create_statistician_agent(self.llm)
        self.model_recommender = create_model_recommender_agent(self.llm)
        self.xai_agent = create_xai_agent(self.llm)
        self.reporter = create_reporter_agent(self.llm)
        
        # Configure XAI output
        XAIConfig.set_output_dir(self.charts_dir)
        
        # Assign tools to agents
        self._assign_tools()
    
    def _create_llm(self) -> LLM:
        """Create the LLM instance for agents."""
        api_key = os.getenv("OPENROUTER_API_KEY")
        model = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b:free")
        
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not found. Please set it in your .env file."
            )
        
        # Set environment variable for litellm to use OpenRouter
        os.environ["OPENROUTER_API_KEY"] = api_key
        
        return LLM(
            model=f"openrouter/{model}",
        )
    
    def _assign_tools(self):
        """Assign appropriate tools to each agent."""
        # Profiler tools - includes data quality summary chart
        self.profiler.tools = [
            ProfileDatasetTool(),
            GetColumnInfoTool(),
            GetDataSummaryTool(),
            GenerateDataQualitySummaryTool(),
        ]
        
        # Cleaner tools
        self.cleaner.tools = [
            ProfileDatasetTool(),
            DetectOutliersTool(),
            CleanMissingValuesTool(),
            GetDataSummaryTool(),
        ]
        
        # Visualizer tools
        self.visualizer.tools = [
            GenerateDistributionPlotsTool(),
            GenerateCorrelationHeatmapTool(),
            GenerateCategoricalChartsTool(),
            GenerateBoxPlotsTool(),
            GenerateMissingValuesPlotTool(),
            GenerateCleaningImpactPlotTool(),
        ]
        
        # Statistician tools
        self.statistician.tools = [
            DescriptiveStatsTool(),
            CorrelationAnalysisTool(),
            CategoricalAnalysisTool(),
            DetectPatternsTool(),
            NormalityTestTool(),
        ]
        
        # Model Recommender tools
        self.model_recommender.tools = [
            SuggestModelsBasedOnDataTool(),
            TrainSimpleModelTool(),
        ]
        
        # XAI Agent tools
        self.xai_agent.tools = [
            GenerateSHAPSummaryTool(),
            GenerateLIMEExplanationTool(),
            CompareFeatureImportanceTool(),
        ]
        
        # Reporter has no tools - uses results from other agents
        self.reporter.tools = []
    
    def _create_tasks(self) -> list[Task]:
        """Create the task sequence for EDA workflow."""
        
        profile_task = Task(
            description="""
            Profile the dataset to understand its structure and quality.
            
            Steps:
            1. Use generate_data_quality_summary to create a visual overview of data quality
            2. Use profile_dataset tool to get a comprehensive overview including:
               - Column types (numeric, categorical, datetime)
               - Missing value patterns
               - Basic statistics for each column
               - Potential data quality issues
            
            Provide a detailed summary of your findings, highlighting:
            1. Dataset dimensions (rows × columns)
            2. Column types breakdown
            3. Missing values summary
            4. Any data quality concerns
            5. Potential target columns or interesting features
            """,
            expected_output="""A comprehensive data profile report containing:
            - Path to the data quality summary chart
            - Dataset shape and memory usage
            - Column-by-column analysis with types, missing values, and statistics
            - List of potential issues and recommendations""",
            agent=self.profiler,
        )
        
        clean_task = Task(
            description="""
            Clean the dataset based on the profiling results.
            
            ⚠️ CRITICAL: You MUST call EACH of these tools in order. Do NOT skip any.
            
            Step 1: Call detect_outliers with method="iqr" and columns=[] (empty = all numeric)
                    → This identifies outliers in the data
            
            Step 2: Call clean_missing_values with strategy="auto"
                    → This is MANDATORY - it fills missing values with mean/median/mode
                    → You MUST call this tool even if there are few missing values
            
            Step 3: Call get_data_summary to verify the cleaning worked
                    → Check that missing counts are now 0 or reduced
            
            ⚠️ Your task is INCOMPLETE if you do not call ALL 3 tools above.
            ⚠️ The clean_missing_values call is CRITICAL for the before/after comparison.
            
            Document every transformation explaining WHY you chose each strategy.
            """,
            expected_output="""A cleaning report containing:
            - Confirmation that ALL 3 tools were called
            - List of all transformations applied
            - Count of missing values fixed per column
            - Before/after comparison of data quality""",
            agent=self.cleaner,
            context=[profile_task],
        )
        
        visualize_task = Task(
            description=f"""
            Create insightful visualizations for the cleaned dataset.
            
            ⚠️ CRITICAL: You MUST call EACH tool type below. Do NOT skip any.
            
            Step 1: generate_distribution_plots with max_columns=10
            Step 2: generate_correlation_heatmap with method="pearson"
            Step 3: generate_categorical_charts with max_categories=10
            Step 4: generate_box_plots (no parameters needed)
            Step 5: generate_cleaning_impact_plot - Call 2-3 times for NUMERIC columns 
                    that had missing values (check the profiling/cleaning results)
                    Examples: age, income, credit_score, annual_income, etc.
            
            Charts will be saved to: {self.charts_dir}
            
            ⚠️ Your task is INCOMPLETE if you skip any of the 5 tool types.
            
            For each visualization, briefly describe what pattern or insight it reveals.
            """,
            expected_output="""A visualization report containing:
            - Confirmation that ALL 5 tool types were called
            - List of all generated chart file paths
            - Description of key insights from each visualization""",
            agent=self.visualizer,
            context=[clean_task],
        )
        
        stats_task = Task(
            description="""
            Perform comprehensive statistical analysis on the cleaned dataset.
            
            ⚠️ CRITICAL: Call tools with EXACT parameters shown:
            
            1. compute_descriptive_stats - no parameters needed
            2. analyze_correlations with method="pearson", threshold=0.5
            3. analyze_categorical - no parameters needed
            4. detect_patterns - no parameters needed
            5. test_normality - no parameters needed
            
            ⚠️ ERROR HANDLING:
            - If analyze_correlations fails, MOVE ON to the next tool immediately
            - Do NOT retry failed tools more than once
            - Partial results are acceptable
            
            Focus on INTERPRETING the numbers. Explain what statistics mean in practical terms.
            For example: "High correlation (0.85) suggests these variables move together..."
            """,
            expected_output="""A statistical analysis report containing:
            - Descriptive statistics with interpretations
            - Correlation analysis results (or note if it failed)
            - Categorical analysis insights
            - Detected patterns
            - Normality test results""",
            agent=self.statistician,
            context=[clean_task],
        )
        
        # Model Recommendation Task
        recommend_task = Task(
            description="""
            Analyze the cleaned dataset and recommend suitable machine learning models.
            
            Steps:
            1. Call suggest_models with the most appropriate target column for prediction
               (Look for columns like 'is_member', 'status', 'category', or any binary/categorical column)
            2. Review the recommendations and explain why each model is suitable
            
            Focus on practical business value and model interpretability.
            """,
            expected_output="""A model recommendation report containing:
            - Identified target variable and problem type (classification/regression)
            - Top 3 recommended algorithms with justifications
            - Data characteristics that influenced the recommendations""",
            agent=self.model_recommender,
            context=[profile_task, stats_task],
        )
        
        # Model Training Task
        train_task = Task(
            description="""
            Train a baseline machine learning model for XAI analysis.
            
            Steps:
            1. Call train_simple_model with the target column identified in the recommendation
            2. Report the model performance metrics
            
            This model will be used for generating SHAP and LIME explanations.
            """,
            expected_output="""Model training results containing:
            - Model type and performance metrics (accuracy/R²)
            - Top 10 most important features
            - Confirmation that model was saved for XAI""",
            agent=self.model_recommender,
            context=[recommend_task],
        )
        
        # XAI Task
        xai_task = Task(
            description=f"""
            Generate explainability visualizations using SHAP and LIME.
            
            ⚠️ CRITICAL: You MUST call EACH of these tools in order:
            
            Step 1: Call generate_shap_summary to create global feature importance
            Step 2: Call generate_lime_explanation for row_index=0 (first sample)
            Step 3: Call compare_feature_importance to compare methods
            
            All charts will be saved to: {self.charts_dir}
            
            ⚠️ Your task is INCOMPLETE if you do not call ALL 3 tools above.
            """,
            expected_output="""An XAI report containing:
            - Path to SHAP summary plot
            - Path to LIME explanation plot
            - Path to feature importance comparison chart
            - Key insights about which features drive predictions""",
            agent=self.xai_agent,
            context=[train_task],
        )
        
        report_task = Task(
            description=f'''
            Generate a professional, evidence-based EDA report following STRICT formatting rules.
            
            ═══════════════════════════════════════════════════════════════════════════
            SECTION ORDER (MANDATORY):
            ═══════════════════════════════════════════════════════════════════════════
            1. Executive Summary
            2. Dataset Overview  
            3. Data Quality & Cleaning
            4. Decision Audit Trail
            5. Cleaning Impact Analysis
            6. Statistical Analysis
            7. Model Recommendation
            8. XAI Insights
            9. Next Steps
            
            ═══════════════════════════════════════════════════════════════════════════
            WRITING RULES (MANDATORY):
            ═══════════════════════════════════════════════════════════════════════════
            
            TONE: Use neutral, factual language only.
            - Use: "identified", "observed", "measured", "compared", "retained", "rejected"
            - NEVER use: "excellent", "robust", "successful", "actionable", "high confidence",
                         "revenue", "growth", "efficiency", "validated" unless with numeric proof
            
            STRUCTURE: Each section = 3-6 bullet points maximum. Be concise.
            
            EVIDENCE-FIRST: Numbers and data references come BEFORE interpretations.
            - Correct: "Missing values: 45 (3.2%). Imputed using median."
            - Wrong: "We successfully handled the missing values."
            
            ═══════════════════════════════════════════════════════════════════════════
            SECTION GUIDELINES:
            ═══════════════════════════════════════════════════════════════════════════
            
            ## 1. Executive Summary
            - 3-5 bullet points of the MOST IMPORTANT facts only
            - Include: row count, column count, missing %, key correlations found, recommended model
            - NO business projections, NO persuasive language
            
            ## 2. Dataset Overview
            - Dimensions: {{rows}} rows × {{columns}} columns
            - Memory usage: {{X}} MB
            - Column types: {{N}} numeric, {{M}} categorical, {{K}} datetime
            - List columns by type
            
            ## 3. Data Quality & Cleaning
            - Report quality flags found (e.g., HIGH_MISSING, OUTLIERS_DETECTED)
            - List imputation methods with exact counts:
              "Column 'age': 12 missing values imputed using median (value=35)"
            
            ## 4. Decision Audit Trail
            Format each operation as:
            | Column | Operation | Method | Affected Rows | Rationale |
            |--------|-----------|--------|---------------|-----------|
            - NO emotional words, just facts
            
            ## 5. Cleaning Impact Analysis
            Before vs After comparison:
            - "Column 'income': Mean 45,230→45,180, Std 12,450→12,380, Missing 8→0"
            - One validation statement per variable
            - Reference impact charts: charts/impact_*.png
            
            ## 6. Statistical Analysis
            Report test results neutrally:
            - "Shapiro-Wilk test on 'age': W=0.987, p=0.342. Null hypothesis not rejected (α=0.05)."
            - "Pearson correlation 'age' vs 'income': r=0.72, p<0.001"
            - NO adverbs like "extremely" or "highly"
            
            ## 7. Model Recommendation
            Technical justification only:
            - Problem type: Classification/Regression
            - Recommended: RandomForest because [data has N features, mixed types, potential non-linearity]
            - Alternative: LogisticRegression if interpretability required
            - NO accuracy estimates without validation, NO business KPIs
            
            ## 8. XAI Insights
            Frame as model behavior analysis:
            - "SHAP global importance: feature_1 (0.42), feature_2 (0.28), feature_3 (0.15)"
            - "LIME explanation for row 0: feature_1 contributed +0.32 to prediction"
            - Reference charts: charts/shap_summary.png, charts/lime_explanation.png
            - NO "insights for action" language
            
            ## 9. Next Steps
            Concrete analytical steps only:
            - Train model with cross-validation
            - Monitor for feature drift
            - Validate on holdout set
            - NO marketing or speculative strategy language
            
            ═══════════════════════════════════════════════════════════════════════════
            OUTPUT FORMAT:
            ═══════════════════════════════════════════════════════════════════════════
            - Markdown format
            - Reference charts using: charts/{{filename}}.png
            - Use tables for structured data
            - Max 2 pages equivalent length
            ''',
            expected_output='''A precise, evidence-based Markdown report that:
            - Follows the exact 9-section structure
            - Uses neutral, factual language throughout
            - Places numbers before interpretations
            - Contains NO buzzwords or unsupported claims
            - Includes table-formatted audit trail
            - References all chart files correctly''',
            agent=self.reporter,
            context=[profile_task, clean_task, visualize_task, stats_task, recommend_task, xai_task],
        )
        
        return [profile_task, clean_task, visualize_task, stats_task, recommend_task, train_task, xai_task, report_task]
    
    def _step_callback(self, step_output):
        """
        Callback for each crew step - used for live activity log only.
        """
        if not self.progress_tracker:
            return
        
        try:
            # Extract action/tool info for activity log
            action = "processing"
            agent_name = "Agent"
            
            # Try to get tool name
            if hasattr(step_output, 'tool') and step_output.tool:
                action = str(step_output.tool)
            elif hasattr(step_output, 'result') and step_output.result:
                action = str(step_output.result)[:40]
            
            # Try to get agent via thought/log for context
            if hasattr(step_output, 'thought') and step_output.thought:
                thought = str(step_output.thought)[:30]
                action = thought if action == "processing" else action
            
            self.progress_tracker.log_activity(agent_name, action, "running")
            
        except Exception as e:
            print(f"Step callback error (non-fatal): {e}")
    
    def _task_callback(self, task_output):
        """
        Callback after each task completes - used for stage completion tracking.
        This is the RELIABLE way to track progress since it fires after each task.
        """
        if not self.progress_tracker:
            return
        
        try:
            # Get the agent role from the task output
            agent_role = None
            if hasattr(task_output, 'agent') and task_output.agent:
                agent_role = task_output.agent
            
            # Map agent roles to stages
            stage_map = {
                "Data Profiler": "profiling",
                "Data Cleaner": "cleaning", 
                "Data Visualizer": "visualization",
                "Statistician": "statistics",
                "Machine Learning Strategist": "ml_xai",
                "Explainability Specialist": "ml_xai",
                "Technical Report Writer": "report",
            }
            
            # Stage order for progress tracking
            stage_order = ["profiling", "cleaning", "visualization", "statistics", "ml_xai", "report"]
            
            # Find and complete the stage
            if agent_role and agent_role in stage_map:
                completed_stage = stage_map[agent_role]
                self.progress_tracker.complete_stage(completed_stage)
                self.progress_tracker.log_activity(agent_role, "task completed", "completed")
                
                # Start next stage
                try:
                    current_idx = stage_order.index(completed_stage)
                    if current_idx < len(stage_order) - 1:
                        next_stage = stage_order[current_idx + 1]
                        self.progress_tracker.start_stage(next_stage)
                except ValueError:
                    pass
            
        except Exception as e:
            print(f"Task callback error (non-fatal): {e}")
    
    def run(self, df) -> dict:
        """
        Run the EDA workflow on the provided dataframe.
        
        Args:
            df: pandas DataFrame to analyze
            
        Returns:
            Dictionary with analysis results
        """
        # Set the dataframe in the shared data store
        DataStore.set_dataframe(df)
        
        # Helper to update progress
        def update_progress(stage_id: str, agent_name: str, action: str = "processing"):
            if self.progress_tracker:
                self.progress_tracker.start_stage(stage_id)
                self.progress_tracker.log_activity(agent_name, action, "running")
        
        def complete_progress(stage_id: str, agent_name: str, action: str = "completed"):
            if self.progress_tracker:
                self.progress_tracker.complete_stage(stage_id)
                self.progress_tracker.log_activity(agent_name, action, "completed")
        
        # Create tasks with progress tracking
        tasks = self._create_tasks()
        
        # Map tasks to stages for tracking
        task_stage_map = [
            ("profiling", "Data Profiler", "profile_dataset"),
            ("cleaning", "Data Cleaner", "clean_missing_values"),
            ("visualization", "Data Visualizer", "generate_visualizations"),
            ("statistics", "Statistician", "analyze_statistics"),
            ("ml_xai", "ML Strategist", "train_model"),
            ("ml_xai", "XAI Agent", "generate_explanations"),
            ("report", "Report Writer", "generate_report"),
        ]
        
        # Start profiling stage
        if self.progress_tracker:
            update_progress("profiling", "Data Profiler", "profile_dataset")
        
        # Create crew with sequential process and both callbacks
        crew = Crew(
            agents=[
                self.profiler,
                self.cleaner,
                self.visualizer,
                self.statistician,
                self.model_recommender,
                self.xai_agent,
                self.reporter,
            ],
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
            step_callback=self._step_callback if self.progress_tracker else None,
            task_callback=self._task_callback if self.progress_tracker else None,
        )
        
        # Execute the crew with retry logic for transient API errors
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = crew.kickoff()
                break
            except Exception as e:
                error_msg = str(e).lower()
                if attempt < max_retries - 1 and any(x in error_msg for x in ['rate', 'limit', 'provider', 'timeout', 'api']):
                    wait_time = (attempt + 1) * 30  # 30s, 60s, 90s
                    print(f"\n⚠️  API error (attempt {attempt + 1}/{max_retries}). Waiting {wait_time}s before retry...")
                    if self.progress_tracker:
                        self.progress_tracker.log_activity("System", f"API retry in {wait_time}s", "running")
                    time.sleep(wait_time)
                else:
                    raise
        
        # ═══════════════════════════════════════════════════════════════════════════
        # FALLBACK: Ensure cleaning happens even if LLM skipped tool calls
        # ═══════════════════════════════════════════════════════════════════════════
        cleaned_df = DataStore.get_dataframe()
        if cleaned_df is not None:
            missing_before = cleaned_df.isnull().sum().sum()
            if missing_before > 0:
                print(f"\n⚠️  Fallback cleaning: {missing_before} missing values found, applying auto-imputation...")
                for col in cleaned_df.columns:
                    missing_count = cleaned_df[col].isnull().sum()
                    if missing_count > 0:
                        if pd.api.types.is_numeric_dtype(cleaned_df[col]):
                            fill_value = cleaned_df[col].mean()
                            method = "mean"
                        else:
                            fill_value = cleaned_df[col].mode().iloc[0] if not cleaned_df[col].mode().empty else "Unknown"
                            method = "mode"
                        cleaned_df[col] = cleaned_df[col].fillna(fill_value)
                        print(f"   → {col}: {missing_count} missing → filled with {method}")
                        
                        # Log the cleaning
                        DataStore.add_cleaning_log({
                            "column": col,
                            "action": "fallback_impute",
                            "method": method,
                            "fill_value": str(fill_value),
                            "affected_rows_count": int(missing_count),
                        })
                
                DataStore.update_dataframe(cleaned_df, "Fallback cleaning applied")
                print(f"✓ Fallback cleaning complete. Missing values: {cleaned_df.isnull().sum().sum()}")
        
        # Save the final report
        self._save_reports(result)
        
        # Save cleaned data
        cleaned_df = DataStore.get_dataframe()
        if cleaned_df is not None:
            cleaned_df.to_csv(
                os.path.join(self.output_dir, "cleaned_data.csv"),
                index=False
            )
        
        return {
            "result": result,
            "output_dir": self.output_dir,
            "changelog": DataStore.get_changelog(),
        }
    
    def _save_reports(self, result):
        """Save the final reports to files."""
        # Save Markdown report
        md_path = os.path.join(self.output_dir, "report.md")
        with open(md_path, "w", encoding="utf-8") as f:
            if hasattr(result, 'raw'):
                f.write(str(result.raw))
            else:
                f.write(str(result))
        
        # Generate HTML report
        html_path = os.path.join(self.output_dir, "report.html")
        self._generate_html_report(md_path, html_path)
    
    def _generate_html_report(self, md_path: str, html_path: str):
        """Convert Markdown report to HTML."""
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                md_content = f.read()
            
            # Simple Markdown to HTML conversion
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EDA Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }}
        h1 {{ font-size: 2.5em; }}
        h2 {{ font-size: 1.8em; margin-top: 30px; }}
        h3 {{ font-size: 1.4em; }}
        pre {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        code {{
            background: #e9ecef;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        img {{
            max-width: 100%;
            height: auto;
            border-radius: 5px;
            margin: 10px 0;
        }}
        ul, ol {{
            padding-left: 20px;
        }}
        li {{
            margin: 8px 0;
        }}
        .chart-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <pre style="white-space: pre-wrap; font-family: inherit; background: none; padding: 0;">{md_content}</pre>
    </div>
</body>
</html>"""
            
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
                
        except Exception as e:
            print(f"Warning: Could not generate HTML report: {e}")
