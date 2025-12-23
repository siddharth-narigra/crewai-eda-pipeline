"""
File Handler Utility
Handles loading and saving of CSV/Excel files with proper error handling.
"""

import os
import warnings
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
from rich.console import Console

console = Console()

# Suppress pandas datetime parsing warnings
warnings.filterwarnings('ignore', message='Could not infer format')


def validate_file(file_path: str) -> Tuple[bool, str]:
    """
    Validate that a file exists and is a supported format.
    
    Args:
        file_path: Path to the file to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    path = Path(file_path)
    
    if not path.exists():
        return False, f"File not found: {file_path}"
    
    if not path.is_file():
        return False, f"Path is not a file: {file_path}"
    
    supported_extensions = {'.csv', '.xlsx', '.xls'}
    if path.suffix.lower() not in supported_extensions:
        return False, f"Unsupported file format: {path.suffix}. Supported: {supported_extensions}"
    
    return True, "File is valid"


def load_dataset(file_path: str) -> Optional[pd.DataFrame]:
    """
    Load a CSV or Excel file into a pandas DataFrame.
    Auto-detects and parses datetime columns.
    
    Args:
        file_path: Path to the CSV or Excel file
        
    Returns:
        DataFrame if successful, None otherwise
    """
    is_valid, message = validate_file(file_path)
    if not is_valid:
        console.print(f"[red]Error:[/red] {message}")
        return None
    
    path = Path(file_path)
    
    try:
        if path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path)
        else:  # Excel files
            df = pd.read_excel(file_path)
        
        # Auto-detect and parse datetime columns
        for col in df.columns:
            if df[col].dtype == 'object':
                # Check if column looks like dates
                sample = df[col].dropna().head(10)
                try:
                    pd.to_datetime(sample, errors='raise')
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    console.print(f"  [dim]Parsed '{col}' as datetime[/dim]")
                except:
                    pass
        
        console.print(f"[green]✓[/green] Loaded dataset: {path.name}")
        console.print(f"  Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        
        return df
        
    except Exception as e:
        console.print(f"[red]Error loading file:[/red] {str(e)}")
        return None


def save_cleaned_data(df: pd.DataFrame, output_dir: str, filename: str = "cleaned_data.csv") -> Optional[str]:
    """
    Save a cleaned DataFrame to CSV.
    
    Args:
        df: DataFrame to save
        output_dir: Directory to save the file
        filename: Name of the output file
        
    Returns:
        Path to saved file if successful, None otherwise
    """
    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        file_path = output_path / filename
        df.to_csv(file_path, index=False)
        
        console.print(f"[green]✓[/green] Saved cleaned data: {file_path}")
        return str(file_path)
        
    except Exception as e:
        console.print(f"[red]Error saving file:[/red] {str(e)}")
        return None


def ensure_output_dirs(base_output_dir: str = "output") -> dict:
    """
    Create output directories for reports and charts.
    
    Args:
        base_output_dir: Base directory for all outputs
        
    Returns:
        Dictionary with paths to created directories
    """
    dirs = {
        'base': Path(base_output_dir),
        'charts': Path(base_output_dir) / 'charts',
    }
    
    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    return {k: str(v) for k, v in dirs.items()}
