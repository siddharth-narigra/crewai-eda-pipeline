"""
EDA Crew Orchestration
Coordinates all agents to perform comprehensive exploratory data analysis.
"""

import os
import time
from typing import Optional

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
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the EDA Crew.
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = output_dir
        self.charts_dir = os.path.join(output_dir, "charts")
        
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
            
            Steps:
            1. Use detect_outliers to identify outliers in numeric columns
            2. Use clean_missing_values with strategy='auto' to handle missing data
            3. Use get_data_summary to verify the cleaning results
            
            Document every transformation you make, explaining WHY you chose 
            each cleaning strategy. The changelog is critical for explainability.
            """,
            expected_output="""A cleaning report containing:
            - List of all transformations applied
            - Explanation for each cleaning decision
            - Before/after comparison of data quality
            - The changelog of all changes made""",
            agent=self.cleaner,
            context=[profile_task],
        )
        
        visualize_task = Task(
            description=f"""
            Create insightful visualizations for the cleaned dataset.
            
            ⚠️ CRITICAL: You MUST call EACH of the following tools. Do NOT skip any.
            Call them one by one in this EXACT order:
            
            Step 1: Call generate_distribution_plots with max_columns=10
            Step 2: Call generate_correlation_heatmap with method="pearson"
            Step 3: Call generate_categorical_charts with max_categories=10
            Step 4: Call generate_box_plots (no input needed)
            Step 5: Call generate_cleaning_impact_plot for "income" column
            Step 6: Call generate_cleaning_impact_plot for "credit_score" column
            Step 7: Call generate_cleaning_impact_plot for "education" column
            
            Charts will be saved to: {self.charts_dir}
            
            After calling ALL tools, summarize the generated files and key insights.
            ⚠️ Your task is INCOMPLETE if you do not call ALL 7 tools above.
            """,
            expected_output="""A visualization report containing:
            - Confirmation that ALL 7 visualization tools were called
            - List of all generated chart file paths
            - Description of key insights from each visualization""",
            agent=self.visualizer,
            context=[clean_task],
        )
        
        stats_task = Task(
            description="""
            Perform comprehensive statistical analysis on the cleaned dataset.
            
            Analysis steps:
            1. Use compute_descriptive_stats for all numeric columns
            2. Use analyze_correlations to find significant relationships
            3. Use analyze_categorical for categorical columns
            4. Use detect_patterns.to find duplicates, constants, and other patterns
            5. Use test_normality on key numeric columns
            
            Focus on INSIGHTS, not just numbers. Explain what the statistics mean
            in practical terms.
            """,
            expected_output="""A statistical analysis report containing:
            - Key descriptive statistics with interpretations
            - Significant correlations and their implications
            - Categorical analysis insights
            - Detected patterns and recommendations
            - Normality test results where relevant""",
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
            description=f"""
            Consolidate all findings into a comprehensive EDA report with a focus on EXPLAINABILITY.
            
            Create a well-structured report that includes:
            
            1. **Executive Summary** (Key findings and high-level data health)
            2. **Dataset Overview** (Dimensions, types, memory)
            3. **Data Quality & Quality Flags** (Issues found, structured flags like HIGH_MISSING, etc.)
            4. **Decision Audit Trail** (Detailed log of every cleaning action, the reason, and the affected rows)
            5. **Cleaning Impact Analysis** (Pre- vs Post-cleaning statistics and reference to impact plots)
            6. **Statistical Analysis Rigor** (Results of normality tests, correlation significance with p-values)
            7. **Model Recommendations** (Suggested algorithms and why)
            8. **XAI Insights** (SHAP global importance, LIME local explanations)
            9. **Key Visualizations** (Reference the chart files in {self.charts_dir})
            10. **Recommendations** (Next steps for modeling based on the findings)
            
            Format the report in Markdown. Reference chart files using relative paths from the output directory.
            
            The "Decision Audit Trail" and "XAI Insights" are the most important sections for explainability.
            """,
            expected_output="""A complete Explainable EDA report in Markdown format that:
            - Features a prominent 'Decision Audit Trail' section
            - Quantifies the impact of cleaning with before/after stats
            - Reports statistical significance (p-values) for key findings
            - Includes SHAP/LIME explanations for model transparency
            - Clearly justifies every automated decision made by the agents""",
            agent=self.reporter,
            context=[profile_task, clean_task, visualize_task, stats_task, recommend_task, xai_task],
        )
        
        return [profile_task, clean_task, visualize_task, stats_task, recommend_task, train_task, xai_task, report_task]
    
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
        
        # Create crew with sequential process
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
            tasks=self._create_tasks(),
            process=Process.sequential,
            verbose=True,
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
                    time.sleep(wait_time)
                else:
                    raise
        
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
