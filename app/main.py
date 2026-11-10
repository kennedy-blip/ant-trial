"""
FastAPI Backend Application
Serves the lightweight analytics dashboard and provides API endpoints for:
- Uploading CSV files
- Loading pre-packaged sample datasets
- Processing files via Polars
- Returning statistical summaries and chart payloads
"""

import os
import io
from typing import List, Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.data_processor import read_csv_with_polars

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
SAMPLE_DIR = os.path.join(PROJECT_ROOT, "sample_data")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(
    title="Polars Data Analytics Dashboard",
    description="High-performance CSV analytics powered by Polars & FastAPI",
    version="1.0.0",
)

# Mount static assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    """Renders and serves the main dashboard user interface."""
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "engine": "Polars", "framework": "FastAPI"}


@app.get("/api/sample-files")
async def list_sample_files() -> List[Dict[str, Any]]:
    """Returns metadata for all available sample CSV files in the sample_data directory."""
    if not os.path.exists(SAMPLE_DIR):
        return []

    files = []
    for f in os.listdir(SAMPLE_DIR):
        if f.lower().endswith(".csv"):
            filepath = os.path.join(SAMPLE_DIR, f)
            size_kb = round(os.path.getsize(filepath) / 1024, 1)
            files.append({
                "filename": f,
                "size_kb": size_kb,
                "path": filepath,
            })
    return files


@app.get("/api/load-sample/{filename}")
async def load_sample_file(filename: str):
    """Loads a sample dataset by filename using Polars and computes its summary statistics."""
    # Sanitize filename to prevent directory traversal
    safe_filename = os.path.basename(filename)
    filepath = os.path.join(SAMPLE_DIR, safe_filename)

    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=404,
            detail=f"Sample dataset '{safe_filename}' not found. Run 'python generate_sample_data.py' first.",
        )

    result = read_csv_with_polars(filepath, file_name=safe_filename)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return JSONResponse(content=result)


@app.post("/api/upload")
async def upload_csv_file(file: UploadFile = File(...)):
    """Receives an uploaded CSV file, ingests it via Polars, and returns analytical metrics."""
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Please upload a standard CSV file (.csv).",
        )

    try:
        contents = await file.read()
        file_buffer = io.BytesIO(contents)
        result = read_csv_with_polars(file_buffer, file_name=file.filename)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
