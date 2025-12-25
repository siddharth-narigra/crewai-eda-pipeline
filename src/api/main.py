"""
FastAPI Backend for Explainable EDA System
Provides REST API endpoints for file upload, EDA execution, and XAI analysis.
"""

import os
import json
import shutil
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd

from src.crew.eda_crew import EDACrew
from src.tools.data_tools import DataStore
from src.tools.ml_tools import ModelStore
from src.api.progress_tracker import tracker

# Create FastAPI application
app = FastAPI(
    title="Explainable EDA API",
    description="REST API for automated, explainable exploratory data analysis",
    version="2.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "output"
CHARTS_DIR = os.path.join(OUTPUT_DIR, "charts")
MODELS_DIR = os.path.join(OUTPUT_DIR, "models")

# Create required directories on startup
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CHARTS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# Mount static files for charts
app.mount("/charts", StaticFiles(directory=CHARTS_DIR), name="charts")

# State tracking - now using ProgressTracker (kept for backwards compatibility)
analysis_status = {"status": "idle", "message": "", "progress": 0}


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Explainable EDA API", "version": "2.0.0"}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a CSV file for analysis.
    Returns file metadata and column information.
    """
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
    
    try:
        # Save uploaded file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Load and analyze
        df = pd.read_csv(file_path) if file.filename.endswith('.csv') else pd.read_excel(file_path)
        
        # Store for later use
        DataStore.set_dataframe(df)
        
        return {
            "status": "success",
            "filename": file.filename,
            "file_path": file_path,
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def run_eda_background():
    """Background task to run EDA pipeline."""
    try:
        tracker.reset()
        tracker.start()
        
        df = DataStore.get_dataframe()
        if df is None:
            tracker.error("No dataset loaded")
            return
        
        # Initialize crew with progress tracker
        crew = EDACrew(output_dir=OUTPUT_DIR, progress_tracker=tracker)
        
        result = crew.run(df)
        
        tracker.complete()
    except Exception as e:
        tracker.error(str(e))


@app.post("/api/eda/run")
async def run_eda(background_tasks: BackgroundTasks):
    """
    Start the EDA pipeline in the background.
    Use /api/eda/status to check progress.
    """
    if DataStore.get_dataframe() is None:
        raise HTTPException(status_code=400, detail="No dataset loaded. Upload a file first.")
    
    current_status = tracker.get_status()
    if current_status.get("status") == "running":
        return {"status": "already_running", "message": "Analysis is already in progress"}
    
    tracker.reset()
    background_tasks.add_task(run_eda_background)
    
    return {"status": "started", "message": "EDA pipeline started. Check /api/eda/status for progress."}


@app.get("/api/eda/status")
async def get_eda_status():
    """Get the current status of the EDA pipeline with detailed stage and activity info."""
    return tracker.get_status()


@app.get("/api/eda/report")
async def get_report(format: str = "md"):
    """
    Get the generated report.
    Format: 'md' for Markdown, 'html' for HTML.
    """
    if format == "html":
        file_path = os.path.join(OUTPUT_DIR, "report.html")
    else:
        file_path = os.path.join(OUTPUT_DIR, "report.md")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report not found. Run EDA first.")
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    return {"format": format, "content": content}


@app.get("/api/report/download")
async def download_report():
    """Download the report as a markdown file."""
    file_path = os.path.join(OUTPUT_DIR, "report.md")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report not found. Run EDA first.")
    
    return FileResponse(
        path=file_path,
        filename="eda_report.md",
        media_type="text/markdown"
    )


@app.get("/api/eda/charts")
async def list_charts():
    """List all generated chart files."""
    charts_dir = os.path.join(OUTPUT_DIR, "charts")
    
    if not os.path.exists(charts_dir):
        return {"charts": []}
    
    charts = []
    for filename in os.listdir(charts_dir):
        if filename.endswith('.png'):
            charts.append({
                "name": filename,
                "url": f"/charts/{filename}",
                "type": filename.split('_')[0] if '_' in filename else "other"
            })
    
    return {"charts": charts, "count": len(charts)}


@app.get("/api/eda/charts/{chart_name}")
async def get_chart(chart_name: str):
    """Get a specific chart image."""
    file_path = os.path.join(OUTPUT_DIR, "charts", chart_name)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Chart '{chart_name}' not found")
    
    return FileResponse(file_path, media_type="image/png")


@app.get("/api/xai/shap")
async def get_shap_summary():
    """Get SHAP summary data and plot path."""
    shap_data = DataStore.get_metadata("shap_values")
    
    if shap_data is None:
        raise HTTPException(status_code=404, detail="SHAP analysis not available. Run EDA first.")
    
    return {
        "status": "success",
        "plot_url": "/charts/shap_summary.png",
        "feature_importance": shap_data.get("mean_importance", {})
    }


@app.get("/api/xai/model")
async def get_model_info():
    """Get information about the trained model."""
    metadata = ModelStore.get_metadata()
    
    if metadata.get("model_type") is None:
        raise HTTPException(status_code=404, detail="No model trained yet. Run EDA first.")
    
    return {
        "status": "success",
        "model_type": metadata.get("model_type"),
        "target_column": metadata.get("target_column"),
        "features": metadata.get("feature_columns", []),
        "metrics": metadata.get("metadata", {})
    }


@app.get("/api/data/summary")
async def get_data_summary():
    """Get a summary of the loaded dataset."""
    df = DataStore.get_dataframe()
    
    if df is None:
        raise HTTPException(status_code=404, detail="No dataset loaded")
    
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "column_info": [
            {
                "name": col,
                "dtype": str(df[col].dtype),
                "missing": int(df[col].isnull().sum()),
                "unique": int(df[col].nunique())
            }
            for col in df.columns
        ],
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2)
    }


@app.get("/api/data/download")
async def download_cleaned_data():
    """Download the cleaned dataset as CSV."""
    file_path = os.path.join(OUTPUT_DIR, "cleaned_data.csv")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Cleaned data not found. Run EDA first.")
    
    return FileResponse(
        file_path, 
        media_type="text/csv",
        filename="cleaned_data.csv"
    )


@app.get("/api/data/comparison")
async def get_before_after_comparison():
    """Get before/after comparison stats for the dataset."""
    original_df = DataStore.get_original_dataframe()
    cleaned_df = DataStore.get_dataframe()
    
    if original_df is None or cleaned_df is None:
        raise HTTPException(status_code=404, detail="Data not available. Run EDA first.")
    
    # Calculate before stats
    before_stats = {
        "rows": len(original_df),
        "columns": len(original_df.columns),
        "missing_total": int(original_df.isnull().sum().sum()),
        "missing_percent": round(original_df.isnull().sum().sum() / (len(original_df) * len(original_df.columns)) * 100, 2),
        "completeness": round((1 - original_df.isnull().sum().sum() / (len(original_df) * len(original_df.columns))) * 100, 2),
    }
    
    # Calculate after stats
    after_stats = {
        "rows": len(cleaned_df),
        "columns": len(cleaned_df.columns),
        "missing_total": int(cleaned_df.isnull().sum().sum()),
        "missing_percent": round(cleaned_df.isnull().sum().sum() / (len(cleaned_df) * len(cleaned_df.columns)) * 100, 2) if len(cleaned_df) > 0 else 0,
        "completeness": round((1 - cleaned_df.isnull().sum().sum() / (len(cleaned_df) * len(cleaned_df.columns))) * 100, 2) if len(cleaned_df) > 0 else 100,
    }
    
    # Get cleaning logs
    cleaning_logs = DataStore.get_cleaning_logs()
    
    # Get column-level changes
    column_changes = []
    for col in original_df.columns:
        if col in cleaned_df.columns:
            orig_missing = int(original_df[col].isnull().sum())
            clean_missing = int(cleaned_df[col].isnull().sum())
            if orig_missing > 0:
                column_changes.append({
                    "column": col,
                    "before_missing": orig_missing,
                    "after_missing": clean_missing,
                    "fixed": orig_missing - clean_missing
                })
    
    return {
        "before": before_stats,
        "after": after_stats,
        "improvement": {
            "missing_fixed": before_stats["missing_total"] - after_stats["missing_total"],
            "completeness_gain": round(after_stats["completeness"] - before_stats["completeness"], 2)
        },
        "column_changes": column_changes,
        "cleaning_operations": cleaning_logs[:10] if cleaning_logs else []
    }


@app.get("/api/model/recommendations")
async def get_model_recommendations():
    """Get ML model recommendations from the analysis."""
    recommendations = DataStore.get_metadata("model_recommendations")
    
    if recommendations is None:
        raise HTTPException(status_code=404, detail="Model recommendations not available. Run EDA first.")
    
    return {
        "status": "success",
        "recommendations": recommendations
    }


@app.get("/api/model/stats")
async def get_model_stats():
    """Get comprehensive model statistics and metadata."""
    import pickle
    
    model_path = os.path.join(OUTPUT_DIR, "models", "trained_model.pkl")
    
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail="No trained model found. Run EDA first.")
    
    try:
        with open(model_path, "rb") as f:
            model_data = pickle.load(f)
        
        metrics = model_data.get("metrics", {})
        
        # Get file size
        file_size_mb = round(os.path.getsize(model_path) / 1024 / 1024, 2)
        
        return {
            "status": "success",
            "model_type": metrics.get("model_type", "Unknown"),
            "problem_type": metrics.get("problem_type", "Unknown"),
            "target_column": model_data.get("target", "Unknown"),
            "features": model_data.get("features", []),
            "feature_count": len(model_data.get("features", [])),
            "metrics": {
                # Classification metrics
                "train_accuracy": metrics.get("train_accuracy"),
                "test_accuracy": metrics.get("test_accuracy"),
                "n_classes": metrics.get("n_classes"),
                # Regression metrics
                "train_r2": metrics.get("train_r2"),
                "test_r2": metrics.get("test_r2"),
                "rmse": metrics.get("rmse"),
            },
            "top_features": metrics.get("top_features", {}),
            "file_size_mb": file_size_mb,
            "model_path": "output/models/trained_model.pkl"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading model: {str(e)}")


@app.get("/api/model/download")
async def download_model():
    """Download the trained model as a .pkl file."""
    model_path = os.path.join(OUTPUT_DIR, "models", "trained_model.pkl")
    
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail="No trained model found. Run EDA first.")
    
    return FileResponse(
        path=model_path,
        filename="trained_model.pkl",
        media_type="application/octet-stream"
    )


# Run with: uvicorn src.api.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

