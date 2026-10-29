"""
main.py
FastAPI Web Application Entry Point.
Configures CORS, registers API routers, sets up database schema,
runs startup checks, and serves the frontend dashboard.
"""

import os
import sys

# Ensure root directory is on Python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .database import engine, Base, SessionLocal
from .models import *
from .api import auth, predict, surveys, counselor, analytics
from .seed_data import seed_database_if_empty

app = FastAPI(
    title="AI-Based Student Burnout & Mental Health Risk Prediction System",
    description="Early-warning risk screening and intervention decision support for higher education.",
    version="1.0.0"
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(surveys.router)
app.include_router(counselor.router)
app.include_router(analytics.router)

# Frontend directories
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.on_event("startup")
def on_startup():
    print("\nStarting AI Student Burnout & Mental Health System...")
    # Initialize DB tables
    Base.metadata.create_all(bind=engine)
    
    # Check / seed data
    db = SessionLocal()
    try:
        seed_database_if_empty(db)
    finally:
        db.close()
    print("System startup initialization complete.\n")

@app.get("/", include_in_schema=False)
def serve_home():
    """Serves the main single page dashboard."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "AI Student Burnout Risk Prediction API is running. Access docs at /docs"}

@app.get("/manifest.json", include_in_schema=False)
def serve_manifest():
    manifest_path = os.path.join(STATIC_DIR, "manifest.json")
    if os.path.exists(manifest_path):
        return FileResponse(manifest_path, media_type="application/manifest+json")
    return {"error": "manifest not found"}

@app.get("/sw.js", include_in_schema=False)
def serve_service_worker():
    sw_path = os.path.join(STATIC_DIR, "sw.js")
    if os.path.exists(sw_path):
        return FileResponse(
            sw_path,
            media_type="application/javascript",
            headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"}
        )
    return {"error": "service worker not found"}

@app.get("/offline.html", include_in_schema=False)
def serve_offline():
    offline_path = os.path.join(STATIC_DIR, "offline.html")
    if os.path.exists(offline_path):
        return FileResponse(offline_path)
    return {"error": "offline page not found"}
