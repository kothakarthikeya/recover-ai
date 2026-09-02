from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.health import router as health_router
from app.api.revenue import router as revenue_router
from app.api.risk import router as risk_router
from app.api.agent import router as agent_router
from app.api.policy import router as policy_router
from app.api.recovery import router as recovery_router
from app.api.analytics import router as analytics_router
from app.db.session import engine
from app.models.base import Base

# Auto-create tables in dev environment
Base.metadata.create_all(bind=engine)

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

app.include_router(health_router)
app.include_router(revenue_router)
app.include_router(risk_router)
app.include_router(agent_router)
app.include_router(policy_router)
app.include_router(recovery_router)
app.include_router(analytics_router)


@app.get("/")
def read_root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs": "/docs",
        "health": "/health"
    }
