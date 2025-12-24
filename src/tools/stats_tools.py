"""
Statistical Analysis Tools for CrewAI Agents
Provides tools for computing correlations, descriptive statistics, and pattern detection.
"""

import json
from typing import Type

import numpy as np
import pandas as pd
from scipy import stats
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from src.tools.data_tools import DataStore


# ============ Descriptive Statistics Tool ============

class DescriptiveStatsInput(BaseModel):
    """Input - no input needed."""
    pass


class DescriptiveStatsTool(BaseTool):
    name: str = "compute_descriptive_stats"
    description: str = """
    Compute comprehensive descriptive statistics for all numeric columns.
    Returns: Mean, median, std, skewness, kurtosis, quartiles for each column.
    """
    args_schema: Type[BaseModel] = DescriptiveStatsInput
    
    def _run(self) -> str:
        df = DataStore.get_dataframe()
        if df is None:
            return "Error: No dataset loaded"
        
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return "No numeric columns found"
        
        stats_report = {}
        
        for col in numeric_df.columns:
            data = numeric_df[col].dropna()
            if len(data) == 0:
                continue
            
            stats_report[col] = {
                "count": int(len(data)),
                "mean": round(float(data.mean()), 4),
                "std": round(float(data.std()), 4),
                "min": round(float(data.min()), 4),
                "25%": round(float(data.quantile(0.25)), 4),
                "50%": round(float(data.median()), 4),
                "75%": round(float(data.quantile(0.75)), 4),
                "max": round(float(data.max()), 4),
                "skewness": round(float(data.skew()), 4),
                "kurtosis": round(float(data.kurtosis()), 4),
                "coefficient_of_variation": round(float(data.std() / data.mean() * 100), 2) if data.mean() != 0 else None,
            }
            
            # Interpret skewness
            skew = data.skew()
            if abs(skew) < 0.5:
                stats_report[col]["skewness_interpretation"] = "approximately symmetric"
            elif skew > 0:
                stats_report[col]["skewness_interpretation"] = "right-skewed (positive)"
            else:
                stats_report[col]["skewness_interpretation"] = "left-skewed (negative)"
        
        return json.dumps(stats_report, indent=2)


# ============ Correlation Analysis Tool ============

class CorrelationAnalysisInput(BaseModel):
    """Input for correlation analysis."""
    method: str = Field(default="pearson", description="Correlation method: 'pearson', 'spearman', or 'kendall'")
    threshold: float = Field(default=0.5, description="Minimum correlation threshold to report")


class CorrelationAnalysisTool(BaseTool):
    name: str = "analyze_correlations"
    description: str = """
    Analyze correlations between numeric columns and identify significant relationships.
    Input: method (default 'pearson'), threshold (default 0.5)
    Returns: List of significant correlations above the threshold.
    """
    args_schema: Type[BaseModel] = CorrelationAnalysisInput
    
    def _run(self, method: str = "pearson", threshold: float = 0.5) -> str:
        try:
            df = DataStore.get_dataframe()
            if df is None:
                return json.dumps({"status": "error", "message": "No dataset loaded"})
            
            # Robust input validation - normalize method
            method = str(method).lower().strip()
            if method not in ["pearson", "spearman", "kendall"]:
                method = "pearson"  # Default fallback
            
            # Handle threshold as string or various types
            try:
                threshold = float(threshold)
                threshold = max(0.0, min(1.0, threshold))  # Clamp to valid range
            except (ValueError, TypeError):
                threshold = 0.5  # Default fallback
            
            numeric_df = df.select_dtypes(include=[np.number])
            if len(numeric_df.columns) < 2:
                return json.dumps({"status": "error", "message": "Need at least 2 numeric columns"})
            
            corr_matrix = numeric_df.corr(method=method)
            
            correlations = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    col1, col2 = corr_matrix.columns[i], corr_matrix.columns[j]
                    corr_val = corr_matrix.iloc[i, j]
                    
                    if abs(corr_val) >= threshold:
                        # Calculate p-value for significance
                        data1 = numeric_df[col1].dropna()
                        data2 = numeric_df[col2].dropna()
                        # Align data
                        common_idx = data1.index.intersection(data2.index)
                        if len(common_idx) > 2:
                            try:
                                if method == 'pearson':
                                    r, p_val = stats.pearsonr(data1[common_idx], data2[common_idx])
                                elif method == 'spearman':
                                    r, p_val = stats.spearmanr(data1[common_idx], data2[common_idx])
                                else:
                                    r, p_val = stats.kendalltau(data1[common_idx], data2[common_idx])
                            except Exception:
                                p_val = None
                        else:
                            p_val = None

                        correlations.append({
                            "column1": col1,
                            "column2": col2,
                            "correlation": round(float(corr_val), 4),
                            "p_value": round(float(p_val), 6) if p_val is not None else "N/A",
                            "is_significant": p_val < 0.05 if p_val is not None else False,
                            "strength": "strong" if abs(corr_val) >= 0.7 else "moderate",
                            "direction": "positive" if corr_val > 0 else "negative"
                        })
            
            # Sort by absolute correlation value
            correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
            
            summary = {
                "status": "success",
                "method": method,
                "test_used": f"{method.capitalize()} Correlation Coefficient",
                "null_hypothesis": "There is no correlation between the variables",
                "threshold": threshold,
                "total_pairs_analyzed": len(corr_matrix.columns) * (len(corr_matrix.columns) - 1) // 2,
                "significant_correlations": correlations,
            }
            
            # Store in DataStore for reporting
            DataStore.set_metadata("correlation_analysis", summary)
            
            return json.dumps(summary, indent=2)
        
        except Exception as e:
            return json.dumps({
                "status": "error", 
                "message": f"Correlation analysis failed: {str(e)}",
                "fallback": "Proceeding with pipeline - correlation data unavailable"
            })


# ============ Categorical Analysis Tool ============

class CategoricalAnalysisInput(BaseModel):
    """Input - no input needed."""
    pass


class CategoricalAnalysisTool(BaseTool):
    name: str = "analyze_categorical"
    description: str = """
    Analyze categorical columns including value counts, mode, and entropy.
    Returns: Analysis of each categorical column.
    """
    args_schema: Type[BaseModel] = CategoricalAnalysisInput
    
    def _run(self) -> str:
        df = DataStore.get_dataframe()
        if df is None:
            return "Error: No dataset loaded"
        
        # Identify categorical columns
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Also include numeric columns with few unique values
        for col in df.select_dtypes(include=[np.number]).columns:
            if df[col].nunique() <= 10:
                cat_cols.append(col)
        
        if not cat_cols:
            return "No categorical columns found"
        
        analysis = {}
        
        for col in cat_cols:
            data = df[col].dropna()
            value_counts = data.value_counts()
            
            # Calculate entropy (measure of randomness)
            probs = value_counts / len(data)
            entropy = -sum(probs * np.log2(probs))
            
            analysis[col] = {
                "unique_values": int(data.nunique()),
                "mode": str(value_counts.index[0]) if len(value_counts) > 0 else None,
                "mode_frequency": int(value_counts.iloc[0]) if len(value_counts) > 0 else 0,
                "mode_percentage": round(value_counts.iloc[0] / len(data) * 100, 2) if len(data) > 0 else 0,
                "entropy": round(entropy, 4),
                "entropy_interpretation": "high diversity" if entropy > 2 else "moderate diversity" if entropy > 1 else "low diversity",
                "top_5_values": {str(k): int(v) for k, v in value_counts.head(5).items()},
            }
            
            # Check for potential issues
            if analysis[col]["unique_values"] == len(data):
                analysis[col]["warning"] = "All values are unique - possible ID column"
            elif analysis[col]["mode_percentage"] > 95:
                analysis[col]["warning"] = "Highly imbalanced - one value dominates"
        
        return json.dumps(analysis, indent=2)


# ============ Pattern Detection Tool ============

class DetectPatternsInput(BaseModel):
    """Input - no input needed."""
    pass


class DetectPatternsTool(BaseTool):
    name: str = "detect_patterns"
    description: str = """
    Detect various patterns and anomalies in the dataset.
    Checks for: duplicates, constant columns, high cardinality, potential date columns.
    Returns: List of detected patterns and issues.
    """
    args_schema: Type[BaseModel] = DetectPatternsInput
    
    def _run(self) -> str:
        df = DataStore.get_dataframe()
        if df is None:
            return "Error: No dataset loaded"
        
        patterns = {
            "duplicate_rows": {
                "count": int(df.duplicated().sum()),
                "percentage": round(df.duplicated().sum() / len(df) * 100, 2)
            },
            "constant_columns": [],
            "high_cardinality_columns": [],
            "potential_date_columns": [],
            "potential_id_columns": [],
            "binary_columns": [],
        }
        
        for col in df.columns:
            unique_count = df[col].nunique()
            
            # Constant columns
            if unique_count == 1:
                patterns["constant_columns"].append(col)
            
            # High cardinality
            elif unique_count > 0.9 * len(df) and df[col].dtype == 'object':
                patterns["high_cardinality_columns"].append(col)
            
            # Potential ID columns
            if unique_count == len(df):
                patterns["potential_id_columns"].append(col)
            
            # Binary columns
            if unique_count == 2:
                patterns["binary_columns"].append(col)
            
            # Potential date columns (check if parseable as date)
            if df[col].dtype == 'object':
                try:
                    sample = df[col].dropna().head(5)
                    pd.to_datetime(sample, errors='raise')
                    patterns["potential_date_columns"].append(col)
                except:
                    pass
        
        # Add recommendations
        patterns["recommendations"] = []
        
        if patterns["duplicate_rows"]["count"] > 0:
            patterns["recommendations"].append(
                f"Consider removing {patterns['duplicate_rows']['count']} duplicate rows"
            )
        
        if patterns["constant_columns"]:
            patterns["recommendations"].append(
                f"Consider removing constant columns: {patterns['constant_columns']}"
            )
        
        if patterns["potential_date_columns"]:
            patterns["recommendations"].append(
                f"Consider converting to datetime: {patterns['potential_date_columns']}"
            )
        
        return json.dumps(patterns, indent=2)


# ============ Normality Test Tool ============

class NormalityTestInput(BaseModel):
    """Input for normality test."""
    alpha: float = Field(default=0.05, description="Significance level for the test")


class NormalityTestTool(BaseTool):
    name: str = "test_normality"
    description: str = """
    Test numeric columns for normality using the Shapiro-Wilk test.
    Input: alpha (significance level, default 0.05)
    Returns: Normality test results for each numeric column.
    """
    args_schema: Type[BaseModel] = NormalityTestInput
    
    def _run(self, alpha: float = 0.05) -> str:
        df = DataStore.get_dataframe()
        if df is None:
            return "Error: No dataset loaded"
        
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return "No numeric columns found"
        
        results = {
            "test_name": "Shapiro-Wilk Test",
            "null_hypothesis": "Data is drawn from a normal distribution",
            "significance_level": alpha,
            "variable_results": {}
        }
        
        for col in numeric_df.columns:
            data = numeric_df[col].dropna()
            
            # Shapiro-Wilk works best with sample size <= 5000
            if len(data) > 5000:
                sample = data.sample(5000, random_state=42)
            else:
                sample = data
            
            if len(sample) < 3:
                continue
            
            try:
                stat, p_value = stats.shapiro(sample)
                
                results["variable_results"][col] = {
                    "statistic": round(float(stat), 4),
                    "p_value": round(float(p_value), 6),
                    "is_normal": bool(p_value > alpha),
                    "interpretation": f"Fail to reject H0: Likely normal" if p_value > alpha else "Reject H0: Unlikely normal"
                }
            except Exception as e:
                results["variable_results"][col] = {"error": str(e)}
        
        # Store in DataStore for reporting
        DataStore.set_metadata("normality_tests", results)
        
        return json.dumps(results, indent=2)
