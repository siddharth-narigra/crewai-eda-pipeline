"""
Data Analysis Tools for CrewAI Agents
Provides tools for data profiling, cleaning, and transformation.
"""

import json
from typing import Any, Type

import numpy as np
import pandas as pd
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


# Global storage for dataframe (shared across tools)
class DataStore:
    """Singleton to store the current working dataframe and explainability metadata."""
    _instance = None
    _df: pd.DataFrame = None
    _original_df: pd.DataFrame = None
    _changelog: list = []
    _metadata: dict = {}
    _cleaning_logs: list = []
    _stats_history: dict = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def set_dataframe(cls, df: pd.DataFrame):
        cls._df = df.copy()
        cls._original_df = df.copy()
        cls._changelog = []
        cls._metadata = {}
        cls._cleaning_logs = []
        cls._stats_history = {}
    
    @classmethod
    def get_dataframe(cls) -> pd.DataFrame:
        return cls._df
    
    @classmethod
    def update_dataframe(cls, df: pd.DataFrame, change_description: str):
        cls._df = df
        cls._changelog.append(change_description)
    
    @classmethod
    def get_changelog(cls) -> list:
        return cls._changelog
    
    @classmethod
    def get_original_dataframe(cls) -> pd.DataFrame:
        return cls._original_df

    @classmethod
    def set_metadata(cls, key: str, value: Any):
        cls._metadata[key] = value

    @classmethod
    def get_metadata(cls, key: str = None) -> Any:
        if key is None:
            return cls._metadata
        return cls._metadata.get(key)

    @classmethod
    def add_cleaning_log(cls, log_entry: dict):
        cls._cleaning_logs.append(log_entry)

    @classmethod
    def get_cleaning_logs(cls) -> list:
        return cls._cleaning_logs

    @classmethod
    def update_stats_history(cls, column: str, stage: str, stats: dict):
        if column not in cls._stats_history:
            cls._stats_history[column] = {}
        cls._stats_history[column][stage] = stats

    @classmethod
    def get_stats_history(cls, column: str = None) -> Any:
        if column is None:
            return cls._stats_history
        return cls._stats_history.get(column)


# ============ Profile Dataset Tool ============

class ProfileDatasetInput(BaseModel):
    """Input for ProfileDatasetTool - no input needed."""
    pass


class ProfileDatasetTool(BaseTool):
    name: str = "profile_dataset"
    description: str = """
    Profile the current dataset to understand its structure.
    Returns column types, missing values, unique counts, and basic statistics.
    No input required - operates on the loaded dataset.
    """
    args_schema: Type[BaseModel] = ProfileDatasetInput
    
    def _run(self) -> str:
        df = DataStore.get_dataframe()
        if df is None:
            return "Error: No dataset loaded"
        
        profile = {
            "shape": {"rows": df.shape[0], "columns": df.shape[1]},
            "columns": {}
        }
        
        for col in df.columns:
            col_data = df[col]
            col_info = {
                "dtype": str(col_data.dtype),
                "missing_count": int(col_data.isna().sum()),
                "missing_percent": round(col_data.isna().sum() / len(df) * 100, 2),
                "unique_count": int(col_data.nunique()),
            }
            
            # Add type-specific info
            if pd.api.types.is_numeric_dtype(col_data):
                col_info["type"] = "numeric"
                col_info["stats"] = {
                    "min": float(col_data.min()) if not col_data.isna().all() else None,
                    "max": float(col_data.max()) if not col_data.isna().all() else None,
                    "mean": float(col_data.mean()) if not col_data.isna().all() else None,
                    "median": float(col_data.median()) if not col_data.isna().all() else None,
                    "std": float(col_data.std()) if not col_data.isna().all() else None,
                }
            elif pd.api.types.is_datetime64_any_dtype(col_data):
                col_info["type"] = "datetime"
                col_info["date_range"] = {
                    "min": str(col_data.min()),
                    "max": str(col_data.max()),
                }
            else:
                col_info["type"] = "categorical"
                top_values = col_data.value_counts().head(5).to_dict()
                col_info["top_values"] = {str(k): int(v) for k, v in top_values.items()}
            
            profile["columns"][col] = col_info
        
        # Identify potential issues
        issues = []
        for col, info in profile["columns"].items():
            if info["missing_percent"] > 50:
                issues.append(f"Column '{col}' has {info['missing_percent']}% missing values")
            if info["unique_count"] == 1:
                issues.append(f"Column '{col}' has only 1 unique value (constant)")
            if info["unique_count"] == profile["shape"]["rows"]:
                issues.append(f"Column '{col}' might be an ID column (all unique values)")
        
        profile["potential_issues"] = issues
        
        # Store metadata and quality flags for downstream agents
        DataStore.set_metadata("profiling_summary", profile)
        
        quality_flags = {}
        for col, info in profile["columns"].items():
            flags = []
            if info["missing_percent"] > 0:
                flags.append(f"MISSING_VALUES({info['missing_percent']}%)")
            if info["unique_count"] == 1:
                flags.append("CONSTANT_COLUMN")
            if info["unique_count"] == profile["shape"]["rows"] and info["type"] != "numeric":
                flags.append("ID_CANDIDATE")
            
            if flags:
                quality_flags[col] = flags
        
        DataStore.set_metadata("quality_flags", quality_flags)
        
        return json.dumps(profile, indent=2)


# ============ Detect Outliers Tool ============

class DetectOutliersInput(BaseModel):
    """Input for DetectOutliersTool."""
    method: str = Field(default="iqr", description="Method to detect outliers: 'iqr' or 'zscore'")


class DetectOutliersTool(BaseTool):
    name: str = "detect_outliers"
    description: str = """
    Detect outliers in numeric columns using IQR or Z-score method.
    Input: method ('iqr' or 'zscore')
    Returns: Summary of outliers found in each numeric column.
    """
    args_schema: Type[BaseModel] = DetectOutliersInput
    
    def _run(self, method: str = "iqr") -> str:
        df = DataStore.get_dataframe()
        if df is None:
            return "Error: No dataset loaded"
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols:
            return "No numeric columns found for outlier detection"
        
        outlier_report = {}
        
        for col in numeric_cols:
            col_data = df[col].dropna()
            
            if method == "iqr":
                Q1 = col_data.quantile(0.25)
                Q3 = col_data.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outliers = col_data[(col_data < lower_bound) | (col_data > upper_bound)]
            else:  # zscore
                z_scores = np.abs((col_data - col_data.mean()) / col_data.std())
                outliers = col_data[z_scores > 3]
            
            if len(outliers) > 0:
                outlier_report[col] = {
                    "count": len(outliers),
                    "percent": round(len(outliers) / len(col_data) * 100, 2),
                    "min_outlier": float(outliers.min()),
                    "max_outlier": float(outliers.max()),
                }
        
        if not outlier_report:
            return "No outliers detected in any numeric column"
        
        return json.dumps(outlier_report, indent=2)


# ============ Clean Missing Values Tool ============

class CleanMissingValuesInput(BaseModel):
    """Input for CleanMissingValuesTool."""
    strategy: str = Field(
        default="auto",
        description="Strategy: 'auto' (based on dtype), 'mean', 'median', 'mode', or 'drop'"
    )


class CleanMissingValuesTool(BaseTool):
    name: str = "clean_missing_values"
    description: str = """
    Handle missing values in the dataset.
    Strategies:
    - 'auto': Use mean for numeric, mode for categorical
    - 'mean': Fill with mean (numeric only)
    - 'median': Fill with median (numeric only)
    - 'mode': Fill with most frequent value
    - 'drop': Drop rows with missing values
    Returns: Summary of changes made.
    """
    args_schema: Type[BaseModel] = CleanMissingValuesInput
    
    def _run(self, strategy: str = "auto") -> str:
        df = DataStore.get_dataframe()
        if df is None:
            return "Error: No dataset loaded"
        
        changes = []
        df_clean = df.copy()
        
        def get_col_stats(series):
            if pd.api.types.is_numeric_dtype(series):
                return {
                    "mean": float(series.mean()) if not series.isna().all() else None,
                    "median": float(series.median()) if not series.isna().all() else None,
                    "std": float(series.std()) if not series.isna().all() else None,
                    "missing": int(series.isna().sum())
                }
            else:
                return {
                    "mode": str(series.mode()[0]) if not series.mode().empty else None,
                    "missing": int(series.isna().sum())
                }

        for col in df_clean.columns:
            missing_count = df_clean[col].isna().sum()
            if missing_count == 0:
                continue
            
            # Capture pre-stats
            pre_stats = get_col_stats(df_clean[col])
            DataStore.update_stats_history(col, "pre_cleaning", pre_stats)
            
            affected_indices = df_clean[df_clean[col].isna()].index.tolist()
            
            if strategy == "drop":
                df_clean = df_clean.dropna(subset=[col])
                change_msg = f"Dropped {missing_count} rows with missing '{col}'"
                changes.append(change_msg)
                
                DataStore.add_cleaning_log({
                    "column": col,
                    "action": "drop",
                    "reason": "Missing values detected",
                    "affected_rows_count": missing_count,
                    "affected_indices": affected_indices[:10], # Log first 10 for brevity
                    "pre_stats": pre_stats,
                    "post_stats": {"rows_remaining": len(df_clean)}
                })
            else:
                if pd.api.types.is_numeric_dtype(df_clean[col]):
                    if strategy in ["auto", "mean"]:
                        fill_value = df_clean[col].mean()
                        method = "mean"
                    elif strategy == "median":
                        fill_value = df_clean[col].median()
                        method = "median"
                    else:
                        fill_value = df_clean[col].mode().iloc[0] if not df_clean[col].mode().empty else 0
                        method = "mode"
                else:
                    fill_value = df_clean[col].mode().iloc[0] if not df_clean[col].mode().empty else "Unknown"
                    method = "mode"
                
                df_clean[col] = df_clean[col].fillna(fill_value)
                change_msg = f"Filled {missing_count} missing values in '{col}' with {method} ({fill_value})"
                changes.append(change_msg)
                
                # Capture post-stats
                post_stats = get_col_stats(df_clean[col])
                DataStore.update_stats_history(col, "post_cleaning", post_stats)
                
                DataStore.add_cleaning_log({
                    "column": col,
                    "action": "impute",
                    "method": method,
                    "fill_value": str(fill_value),
                    "reason": f"Missing values ({missing_count}) detected",
                    "affected_rows_count": missing_count,
                    "affected_indices": affected_indices[:10],
                    "pre_stats": pre_stats,
                    "post_stats": post_stats
                })
        
        if changes:
            DataStore.update_dataframe(df_clean, "; ".join(changes))
        
        return json.dumps({
            "status": "success",
            "changes_summary": changes,
            "rows_before": len(df),
            "rows_after": len(df_clean),
            "remaining_missing": int(df_clean.isna().sum().sum()),
            "detailed_logs_count": len(DataStore.get_cleaning_logs())
        }, indent=2)


# ============ Get Column Info Tool ============

class GetColumnInfoInput(BaseModel):
    """Input for GetColumnInfoTool."""
    column_name: str = Field(description="Name of the column to get info for")


class GetColumnInfoTool(BaseTool):
    name: str = "get_column_info"
    description: str = """
    Get detailed information about a specific column.
    Input: column_name
    Returns: Detailed statistics and distribution info for the column.
    """
    args_schema: Type[BaseModel] = GetColumnInfoInput
    
    def _run(self, column_name: str) -> str:
        df = DataStore.get_dataframe()
        if df is None:
            return "Error: No dataset loaded"
        
        if column_name not in df.columns:
            return f"Error: Column '{column_name}' not found. Available columns: {list(df.columns)}"
        
        col = df[column_name]
        info = {
            "name": column_name,
            "dtype": str(col.dtype),
            "count": int(col.count()),
            "missing": int(col.isna().sum()),
            "unique": int(col.nunique()),
        }
        
        if pd.api.types.is_numeric_dtype(col):
            info["statistics"] = {
                "min": float(col.min()),
                "max": float(col.max()),
                "mean": float(col.mean()),
                "median": float(col.median()),
                "std": float(col.std()),
                "skewness": float(col.skew()),
                "kurtosis": float(col.kurtosis()),
            }
            info["percentiles"] = {
                "25%": float(col.quantile(0.25)),
                "50%": float(col.quantile(0.50)),
                "75%": float(col.quantile(0.75)),
            }
        else:
            value_counts = col.value_counts().head(10).to_dict()
            info["top_values"] = {str(k): int(v) for k, v in value_counts.items()}
        
        return json.dumps(info, indent=2)


# ============ Get Data Summary Tool ============

class GetDataSummaryInput(BaseModel):
    """Input for GetDataSummaryTool - no input needed."""
    pass


class GetDataSummaryTool(BaseTool):
    name: str = "get_data_summary"
    description: str = """
    Get a quick summary of the current dataset state.
    Returns: Basic info about rows, columns, memory usage, and any changes made.
    """
    args_schema: Type[BaseModel] = GetDataSummaryInput
    
    def _run(self) -> str:
        df = DataStore.get_dataframe()
        if df is None:
            return "Error: No dataset loaded"
        
        summary = {
            "rows": df.shape[0],
            "columns": df.shape[1],
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
            "total_missing": int(df.isna().sum().sum()),
            "column_types": df.dtypes.astype(str).value_counts().to_dict(),
            "changelog": DataStore.get_changelog()
        }
        
        return json.dumps(summary, indent=2)
