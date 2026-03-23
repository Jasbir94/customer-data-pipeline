"""
backend/main.py  —  Part 3: FastAPI REST API
Run with:
    uvicorn backend.main:app --reload --port 8000
Or from the backend directory:
    uvicorn main:app --reload --port 8000
"""

import json
import pathlib

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# ── Paths ─────────────────────────────────────────────────────────────────────

ROOT = pathlib.Path(__file__).parent.parent          # project root
DATA = ROOT / "data" / "processed"
FRONTEND = ROOT / "frontend"

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Data Pipeline Dashboard API",
    description="REST API serving analytics CSV outputs from the data pipeline.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ── helpers ───────────────────────────────────────────────────────────────────


def _load(filename: str) -> list[dict]:
    """Load a CSV from the processed data directory.

    Raises:
        HTTPException 404 if the file does not exist.
        HTTPException 500 if the file is empty or unreadable.
    """
    path = DATA / filename
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Data file '{filename}' not found. Run analyze.py first.",
        )
    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=500,
            detail=f"Data file '{filename}' is empty.",
        )
    # Replace NaN with None for clean JSON serialisation
    return json.loads(df.where(pd.notna(df), None).to_json(orient="records"))


# ── API endpoints ─────────────────────────────────────────────────────────────


@app.get("/health", tags=["meta"])
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/api/revenue", tags=["analytics"])
def get_revenue():
    """Monthly revenue trend (completed orders, grouped by YYYY-MM)."""
    return _load("monthly_revenue.csv")


@app.get("/api/top-customers", tags=["analytics"])
def get_top_customers():
    """Top 10 customers by total spend, with churn indicator."""
    return _load("top_customers.csv")


@app.get("/api/categories", tags=["analytics"])
def get_categories():
    """Category performance: revenue, avg order value, order count."""
    return _load("category_performance.csv")


@app.get("/api/regions", tags=["analytics"])
def get_regions():
    """Regional analysis: customers, orders, revenue, avg revenue per customer."""
    return _load("regional_analysis.csv")


# ── Frontend static serving ───────────────────────────────────────────────────

if FRONTEND.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND), html=True), name="static")
