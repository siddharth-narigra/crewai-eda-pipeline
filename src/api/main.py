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

# Create FastAPI application
app = FastAPI(
    title="Explainable EDA API",
    description="REST API for automated, explainable exploratory data analysis",
    version="2.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "output"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Mount static files for charts
app.mount("/charts", StaticFiles(directory=os.path.join(OUTPUT_DIR, "charts")), name="charts")

# State tracking
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
    global analysis_status
    try:
        analysis_status = {"status": "running", "message": "Starting EDA pipeline...", "progress": 10}
        
        df = DataStore.get_dataframe()
        if df is None:
            analysis_status = {"status": "error", "message": "No dataset loaded", "progress": 0}
            return
        
        analysis_status["message"] = "Initializing agents..."
        analysis_status["progress"] = 20
        
        crew = EDACrew(output_dir=OUTPUT_DIR)
        
        analysis_status["message"] = "Running analysis..."
        analysis_status["progress"] = 50
        
        result = crew.run(df)
        
        analysis_status = {
            "status": "completed",
            "message": "Analysis complete!",
            "progress": 100,
            "report_path": os.path.join(OUTPUT_DIR, "report.md"),
            "html_path": os.path.join(OUTPUT_DIR, "report.html")
        }
    except Exception as e:
        analysis_status = {"status": "error", "message": str(e), "progress": 0}


@app.post("/api/eda/run")
async def run_eda(background_tasks: BackgroundTasks):
    """
    Start the EDA pipeline in the background.
    Use /api/eda/status to check progress.
    """
    global analysis_status
    
    if DataStore.get_dataframe() is None:
        raise HTTPException(status_code=400, detail="No dataset loaded. Upload a file first.")
    
    if analysis_status.get("status") == "running":
        return {"status": "already_running", "message": "Analysis is already in progress"}
    
    analysis_status = {"status": "running", "message": "Starting...", "progress": 0}
    background_tasks.add_task(run_eda_background)
    
    return {"status": "started", "message": "EDA pipeline started. Check /api/eda/status for progress."}


@app.get("/api/eda/status")
async def get_eda_status():
    """Get the current status of the EDA pipeline."""
    return analysis_status


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


# Run with: uvicorn src.api.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
