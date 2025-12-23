"""
Visualization Tools for CrewAI Agents
Provides tools for generating charts and plots using Matplotlib/Seaborn.
"""

import json
import os
from typing import Type

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for saving figures

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from src.tools.data_tools import DataStore


class VizConfig:
    """Configuration for visualization output."""
    output_dir: str = "output/charts"
    dpi: int = 150
    figsize: tuple = (10, 6)
    
    @classmethod
    def set_output_dir(cls, path: str):
        cls.output_dir = path
        os.makedirs(path, exist_ok=True)


# Set seaborn style
sns.set_theme(style="whitegrid", palette="husl")


# ============ Distribution Plots Tool ============

class GenerateDistributionPlotsInput(BaseModel):
    """Input for GenerateDistributionPlotsTool."""
    max_columns: int = Field(default=10, description="Maximum number of columns to plot")


class GenerateDistributionPlotsTool(BaseTool):
    name: str = "generate_distribution_plots"
    description: str = """
    Generate histogram/distribution plots for numeric columns.
    Creates individual PNG files for each numeric column.
    Input: max_columns (default 10) - maximum number of columns to plot
    Returns: List of generated chart file paths.
    """
    args_schema: Type[BaseModel] = GenerateDistributionPlotsInput
    
    def _run(self, max_columns: int = 10) -> str:
        df = DataStore.get_dataframe()
        if df is None:
            return "Error: No dataset loaded"
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols:
            return "No numeric columns found for distribution plots"
        
        # Limit columns
        cols_to_plot = numeric_cols[:max_columns]
        generated_files = []
        
        os.makedirs(VizConfig.output_dir, exist_ok=True)
        
        for col in cols_to_plot:
            try:
                fig, ax = plt.subplots(figsize=VizConfig.figsize)
                
                data = df[col].dropna()
                sns.histplot(data=data, kde=True, ax=ax, color='steelblue')
                
                ax.set_title(f'Distribution of {col}', fontsize=14, fontweight='bold')
                ax.set_xlabel(col)
                ax.set_ylabel('Frequency')
                
                # Add statistics annotation
                stats_text = f'Mean: {data.mean():.2f}\nMedian: {data.median():.2f}\nStd: {data.std():.2f}'
                ax.text(0.95, 0.95, stats_text, transform=ax.transAxes, fontsize=10,
                       verticalalignment='top', horizontalalignment='right',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
                
                filepath = os.path.join(VizConfig.output_dir, f'dist_{col.replace(" ", "_")}.png')
                plt.tight_layout()
                plt.savefig(filepath, dpi=VizConfig.dpi)
                plt.close(fig)
                
                generated_files.append(filepath)
            except Exception as e:
                continue
        
        return json.dumps({
            "generated_files": generated_files,
            "columns_plotted": cols_to_plot,
            "total_plots": len(generated_files)
        }, indent=2)


# ============ Correlation Heatmap Tool ============

class GenerateCorrelationHeatmapInput(BaseModel):
    """Input for GenerateCorrelationHeatmapTool."""
    method: str = Field(default="pearson", description="Correlation method: 'pearson', 'spearman', or 'kendall'")


class GenerateCorrelationHeatmapTool(BaseTool):
    name: str = "generate_correlation_heatmap"
    description: str = """
    Generate a correlation heatmap for numeric columns.
    Input: method ('pearson', 'spearman', or 'kendall')
    Returns: Path to the generated heatmap image.
    """
    args_schema: Type[BaseModel] = GenerateCorrelationHeatmapInput
    
    def _run(self, method: str = "pearson") -> str:
        df = DataStore.get_dataframe()
        if df is None:
            return "Error: No dataset loaded"
        
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return "No numeric columns found for correlation heatmap"
        
        if len(numeric_df.columns) < 2:
            return "Need at least 2 numeric columns for correlation"
        
        os.makedirs(VizConfig.output_dir, exist_ok=True)
        
        try:
            corr_matrix = numeric_df.corr(method=method)
            
            # Adjust figure size based on number of columns
            n_cols = len(corr_matrix.columns)
            fig_size = max(8, n_cols * 0.8)
            
            fig, ax = plt.subplots(figsize=(fig_size, fig_size))
            
            mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
            sns.heatmap(
                corr_matrix,
                mask=mask,
                annot=True,
                fmt='.2f',
                cmap='RdBu_r',
                center=0,
                square=True,
                linewidths=0.5,
                ax=ax,
                cbar_kws={"shrink": 0.8}
            )
            
            ax.set_title(f'Correlation Matrix ({method.capitalize()})', fontsize=14, fontweight='bold')
            
            filepath = os.path.join(VizConfig.output_dir, f'correlation_heatmap_{method}.png')
            plt.tight_layout()
            plt.savefig(filepath, dpi=VizConfig.dpi)
            plt.close(fig)
            
            # Find strong correlations
            strong_correlations = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_val = corr_matrix.iloc[i, j]
                    if abs(corr_val) > 0.7:
                        strong_correlations.append({
                            "column1": corr_matrix.columns[i],
                            "column2": corr_matrix.columns[j],
                            "correlation": round(corr_val, 3)
                        })
            
            return json.dumps({
                "filepath": filepath,
                "method": method,
                "strong_correlations": strong_correlations
            }, indent=2)
            
        except Exception as e:
            return f"Error generating heatmap: {str(e)}"


# ============ Categorical Charts Tool ============

class GenerateCategoricalChartsInput(BaseModel):
    """Input for GenerateCategoricalChartsTool."""
    max_columns: int = Field(default=10, description="Maximum number of categorical columns to plot")
    max_categories: int = Field(default=15, description="Maximum categories per chart")


class GenerateCategoricalChartsTool(BaseTool):
    name: str = "generate_categorical_charts"
    description: str = """
    Generate bar charts for categorical columns.
    Input: max_columns, max_categories
    Returns: List of generated chart file paths.
    """
    args_schema: Type[BaseModel] = GenerateCategoricalChartsInput
    
    def _run(self, max_columns: int = 10, max_categories: int = 15) -> str:
        df = DataStore.get_dataframe()
        if df is None:
            return "Error: No dataset loaded"
        
        # Get categorical columns (object type or few unique values)
        cat_cols = []
        for col in df.columns:
            if df[col].dtype == 'object' or (df[col].nunique() <= 20 and df[col].nunique() > 1):
                if not pd.api.types.is_numeric_dtype(df[col]) or df[col].nunique() <= 10:
                    cat_cols.append(col)
        
        if not cat_cols:
            return "No suitable categorical columns found"
        
        cols_to_plot = cat_cols[:max_columns]
        generated_files = []
        
        os.makedirs(VizConfig.output_dir, exist_ok=True)
        
        for col in cols_to_plot:
            try:
                value_counts = df[col].value_counts().head(max_categories)
                
                fig, ax = plt.subplots(figsize=VizConfig.figsize)
                
                colors = sns.color_palette("husl", len(value_counts))
                bars = ax.barh(value_counts.index.astype(str), value_counts.values, color=colors)
                
                ax.set_title(f'Distribution of {col}', fontsize=14, fontweight='bold')
                ax.set_xlabel('Count')
                ax.set_ylabel(col)
                
                # Add value labels
                for bar, val in zip(bars, value_counts.values):
                    ax.text(val + 0.5, bar.get_y() + bar.get_height()/2, 
                           str(val), va='center', fontsize=9)
                
                ax.invert_yaxis()  # Largest at top
                
                filepath = os.path.join(VizConfig.output_dir, f'cat_{col.replace(" ", "_")}.png')
                plt.tight_layout()
                plt.savefig(filepath, dpi=VizConfig.dpi)
                plt.close(fig)
                
                generated_files.append(filepath)
            except Exception as e:
                continue
        
        return json.dumps({
            "generated_files": generated_files,
            "columns_plotted": cols_to_plot,
            "total_plots": len(generated_files)
        }, indent=2)


# ============ Box Plots Tool ============

class GenerateBoxPlotsInput(BaseModel):
    """Input for GenerateBoxPlotsTool."""
    max_columns: int = Field(default=10, description="Maximum number of columns to plot")


class GenerateBoxPlotsTool(BaseTool):
    name: str = "generate_box_plots"
    description: str = """
    Generate box plots for numeric columns to visualize distributions and outliers.
    Input: max_columns (default 10)
    Returns: Path to the generated combined box plot image.
    """
    args_schema: Type[BaseModel] = GenerateBoxPlotsInput
    
    def _run(self, max_columns: int = 10) -> str:
        df = DataStore.get_dataframe()
        if df is None:
            return "Error: No dataset loaded"
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols:
            return "No numeric columns found for box plots"
        
        cols_to_plot = numeric_cols[:max_columns]
        
        os.makedirs(VizConfig.output_dir, exist_ok=True)
        
        try:
            # Create subplots
            n_cols = len(cols_to_plot)
            n_rows = (n_cols + 2) // 3  # 3 plots per row
            
            fig, axes = plt.subplots(n_rows, 3, figsize=(15, 4 * n_rows))
            axes = axes.flatten() if n_cols > 1 else [axes]
            
            for idx, col in enumerate(cols_to_plot):
                ax = axes[idx]
                data = df[col].dropna()
                
                sns.boxplot(x=data, ax=ax, color='steelblue')
                ax.set_title(col, fontsize=11, fontweight='bold')
                ax.set_xlabel('')
            
            # Hide unused subplots
            for idx in range(len(cols_to_plot), len(axes)):
                axes[idx].set_visible(False)
            
            fig.suptitle('Box Plots - Numeric Columns', fontsize=14, fontweight='bold', y=1.02)
            
            filepath = os.path.join(VizConfig.output_dir, 'box_plots.png')
            plt.tight_layout()
            plt.savefig(filepath, dpi=VizConfig.dpi, bbox_inches='tight')
            plt.close(fig)
            
            return json.dumps({
                "filepath": filepath,
                "columns_plotted": cols_to_plot
            }, indent=2)
            
        except Exception as e:
            return f"Error generating box plots: {str(e)}"


# ============ Missing Values Visualization Tool ============

class GenerateMissingValuesPlotInput(BaseModel):
    """Input - no input needed."""
    pass


class GenerateMissingValuesPlotTool(BaseTool):
    name: str = "generate_missing_values_plot"
    description: str = """
    Generate a visualization of missing values pattern in the dataset.
    Returns: Path to the generated missing values chart.
    """
    args_schema: Type[BaseModel] = GenerateMissingValuesPlotInput
    
    def _run(self) -> str:
        df = DataStore.get_dataframe()
        if df is None:
            return "Error: No dataset loaded"
        
        missing = df.isnull().sum()
        missing = missing[missing > 0].sort_values(ascending=True)
        
        if len(missing) == 0:
            return "No missing values found in the dataset"
        
        os.makedirs(VizConfig.output_dir, exist_ok=True)
        
        try:
            fig, ax = plt.subplots(figsize=VizConfig.figsize)
            
            colors = ['#ff6b6b' if v / len(df) > 0.5 else '#feca57' if v / len(df) > 0.2 else '#48dbfb' 
                     for v in missing.values]
            
            bars = ax.barh(missing.index, missing.values, color=colors)
            
            ax.set_title('Missing Values by Column', fontsize=14, fontweight='bold')
            ax.set_xlabel('Number of Missing Values')
            
            # Add percentage labels
            for bar, val in zip(bars, missing.values):
                pct = val / len(df) * 100
                ax.text(val + 0.5, bar.get_y() + bar.get_height()/2, 
                       f'{val} ({pct:.1f}%)', va='center', fontsize=9)
            
            filepath = os.path.join(VizConfig.output_dir, 'missing_values.png')
            plt.tight_layout()
            plt.savefig(filepath, dpi=VizConfig.dpi)
            plt.close(fig)
            
            return json.dumps({
                "filepath": filepath,
                "columns_with_missing": list(missing.index),
                "missing_counts": missing.to_dict()
            }, indent=2)
            
        except Exception as e:
            return f"Error generating missing values plot: {str(e)}"


# ============ Data Quality Summary Chart Tool ============

class GenerateDataQualitySummaryInput(BaseModel):
    """Input - no input needed."""
    pass


class GenerateDataQualitySummaryTool(BaseTool):
    name: str = "generate_data_quality_summary"
    description: str = """
    Generate a comprehensive data quality summary chart showing:
    - Missing values per column (from ORIGINAL data before cleaning)
    - Data type distribution
    - Completeness percentage
    Returns: Path to the generated summary chart.
    No input required - operates on the loaded dataset.
    """
    args_schema: Type[BaseModel] = GenerateDataQualitySummaryInput
    
    def _run(self) -> str:
        # Use ORIGINAL dataframe to show pre-cleaning state
        df = DataStore.get_original_dataframe()
        if df is None:
            df = DataStore.get_dataframe()
        if df is None:
            return "Error: No dataset loaded"
        
        os.makedirs(VizConfig.output_dir, exist_ok=True)
        
        try:
            fig, axes = plt.subplots(1, 2, figsize=(14, 6))
            
            # Chart 1: Missing Values
            ax1 = axes[0]
            missing = df.isnull().sum().sort_values(ascending=True)
            missing_pct = (missing / len(df) * 100).round(1)
            
            colors = ['#28a745' if v == 0 else '#dc3545' if v > 20 else '#ffc107' 
                     for v in missing_pct.values]
            
            bars = ax1.barh(missing.index, missing.values, color=colors)
            ax1.set_title('Missing Values by Column (Pre-Cleaning)', fontsize=12, fontweight='bold')
            ax1.set_xlabel('Count of Missing Values')
            
            # Add value labels
            for bar, val, pct in zip(bars, missing.values, missing_pct.values):
                label = f'{val} ({pct}%)' if val > 0 else '0'
                ax1.text(val + 0.5, bar.get_y() + bar.get_height()/2, label, 
                        va='center', fontsize=8)
            
            # Chart 2: Data Type Distribution
            ax2 = axes[1]
            dtype_counts = df.dtypes.astype(str).value_counts()
            colors2 = sns.color_palette("husl", len(dtype_counts))
            wedges, texts, autotexts = ax2.pie(
                dtype_counts.values, 
                labels=dtype_counts.index,
                autopct='%1.1f%%',
                colors=colors2,
                startangle=90
            )
            ax2.set_title('Column Data Types', fontsize=12, fontweight='bold')
            
            # Add summary stats as text
            total_cells = df.size
            missing_cells = df.isnull().sum().sum()
            completeness = (1 - missing_cells / total_cells) * 100
            
            summary_text = f"Dataset: {df.shape[0]} rows × {df.shape[1]} cols\n"
            summary_text += f"Completeness: {completeness:.1f}%\n"
            summary_text += f"Missing Cells: {missing_cells}"
            
            fig.text(0.5, -0.05, summary_text, ha='center', fontsize=10, 
                    bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
            
            filepath = os.path.join(VizConfig.output_dir, 'data_quality_summary.png')
            plt.tight_layout()
            plt.savefig(filepath, dpi=VizConfig.dpi, bbox_inches='tight')
            plt.close(fig)
            
            return json.dumps({
                "filepath": filepath,
                "total_rows": df.shape[0],
                "total_columns": df.shape[1],
                "completeness_percent": round(completeness, 2),
                "columns_with_missing": list(missing[missing > 0].index)
            }, indent=2)
            
        except Exception as e:
            return f"Error generating data quality summary: {str(e)}"


# ============ Cleaning Impact Plot Tool ============

class GenerateCleaningImpactPlotInput(BaseModel):
    """Input for GenerateCleaningImpactPlotTool."""
    column: str = Field(description="Name of the numeric column to show impact for")


class GenerateCleaningImpactPlotTool(BaseTool):
    name: str = "generate_cleaning_impact_plot"
    description: str = """
    Generate a before-and-after distribution comparison for a column affected by cleaning.
    Shows how imputation or outlier handling changed the data distribution.
    Input: column name
    Returns: Path to the generated impact chart.
    """
    args_schema: Type[BaseModel] = GenerateCleaningImpactPlotInput
    
    def _run(self, column: str) -> str:
        df_original = DataStore.get_original_dataframe()
        df_cleaned = DataStore.get_dataframe()
        
        if df_original is None or df_cleaned is None:
            return "Error: Dataset not loaded"
        
        if column not in df_cleaned.columns:
            return f"Error: Column '{column}' not found"

        os.makedirs(VizConfig.output_dir, exist_ok=True)
        
        try:
            fig, ax = plt.subplots(figsize=VizConfig.figsize)
            
            # Check if numeric or categorical
            if pd.api.types.is_numeric_dtype(df_cleaned[column]):
                # Plot distributions
                sns.kdeplot(data=df_original[column].dropna(), label='Before (Original)', 
                            color='gray', fill=True, alpha=0.3, ax=ax)
                sns.kdeplot(data=df_cleaned[column], label='After (Cleaned)', 
                            color='steelblue', fill=True, alpha=0.5, ax=ax)
                
                # Add mean lines
                orig_mean = df_original[column].mean()
                clean_mean = df_cleaned[column].mean()
                if not pd.isna(orig_mean): ax.axvline(orig_mean, color='gray', linestyle='--', alpha=0.8)
                if not pd.isna(clean_mean): ax.axvline(clean_mean, color='steelblue', linestyle='--', alpha=0.8)
                
                ax.set_ylabel('Density')
            else:
                # Categorical impact: Compare value counts
                orig_counts = df_original[column].value_counts(dropna=False).head(10)
                clean_counts = df_cleaned[column].value_counts(dropna=False).head(10)
                
                comparison_df = pd.DataFrame({
                    'Original': orig_counts,
                    'Cleaned': clean_counts
                }).fillna(0)
                
                comparison_df.plot(kind='bar', ax=ax, color=['lightgray', 'steelblue'], alpha=0.8)
                ax.set_ylabel('Count')
                plt.xticks(rotation=45, ha='right')

            ax.set_title(f'Cleaning Impact: {column}', fontsize=14, fontweight='bold')
            ax.set_xlabel(column)
            ax.legend()
            
            # Add summary box
            stats = DataStore.get_stats_history(column)
            if stats and 'pre_cleaning' in stats and 'post_cleaning' in stats:
                pre = stats['pre_cleaning']
                post = stats['post_cleaning']
                
                if pd.api.types.is_numeric_dtype(df_cleaned[column]):
                    textstr = '\n'.join((
                        f"PRE: mean={pre.get('mean', 0):.2f}, missing={pre.get('missing', 0)}",
                        f"POST: mean={post.get('mean', 0):.2f}, missing={post.get('missing', 0)}"
                    ))
                else:
                    textstr = '\n'.join((
                        f"PRE: mode={pre.get('mode', 'N/A')}, missing={pre.get('missing', 0)}",
                        f"POST: mode={post.get('mode', 'N/A')}, missing={post.get('missing', 0)}"
                    ))
                    
                props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
                ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=10,
                        verticalalignment='top', bbox=props)

            filepath = os.path.join(VizConfig.output_dir, f'impact_{column.replace(" ", "_")}.png')
            plt.tight_layout()
            plt.savefig(filepath, dpi=VizConfig.dpi)
            plt.close(fig)
            
            return json.dumps({
                "filepath": filepath,
                "column": column,
                "type": "numeric" if pd.api.types.is_numeric_dtype(df_cleaned[column]) else "categorical",
                "message": f"Generated impact visualization for {column}"
            }, indent=2)
            
        except Exception as e:
            plt.close(fig)
            return f"Error generating impact plot for {column}: {str(e)}"

