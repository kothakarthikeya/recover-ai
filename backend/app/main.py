import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.api.health import router as health_router
from app.api.revenue import router as revenue_router
from app.api.risk import router as risk_router
from app.api.agent import router as agent_router
from app.api.policy import router as policy_router
from app.api.recovery import router as recovery_router
from app.api.analytics import router as analytics_router
from app.db.session import engine, SessionLocal
from app.models.base import Base
from app.db.init_db import ensure_demo_data_seeded

# Auto-create database tables
Base.metadata.create_all(bind=engine)

# Auto-seed synthetic demo dataset if DB is empty
try:
    with SessionLocal() as db:
        ensure_demo_data_seeded(db)
except Exception as e:
    print(f"Startup DB seed check: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="RecoverAI Revenue Recovery API",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(health_router)
app.include_router(revenue_router)
app.include_router(risk_router)
app.include_router(agent_router)
app.include_router(policy_router)
app.include_router(recovery_router)
app.include_router(analytics_router)

# Locate production React frontend build if available
possible_dist_paths = [
    os.path.abspath("frontend/dist"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist"),
    "/app/frontend/dist"
]

frontend_dist = None
for p in possible_dist_paths:
    if os.path.exists(p) and os.path.isdir(p):
        frontend_dist = p
        break

if frontend_dist:
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str, request: Request):
        # Serve static asset file if exact file exists
        file_path = os.path.join(frontend_dist, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)

        # For root path /, serve index.html to browser requests (text/html) and JSON to API clients
        accept_header = request.headers.get("accept", "")
        if not full_path:
            if "text/html" in accept_header:
                index_file = os.path.join(frontend_dist, "index.html")
                if os.path.exists(index_file):
                    return FileResponse(index_file)
            return {
                "message": f"Welcome to {settings.PROJECT_NAME} API",
                "docs": "/docs",
                "health": "/health"
            }

        # For SPA client routes (/opportunities, /analytics, etc.), serve index.html
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)

        return {
            "message": f"Welcome to {settings.PROJECT_NAME} API",
            "docs": "/docs",
            "health": "/health"
        }
else:
    @app.get("/")
    def read_root():
        return {
            "message": f"Welcome to {settings.PROJECT_NAME} API",
            "docs": "/docs",
            "health": "/health"
        }
