import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database.database import engine, Base
from app.database.seed import seed_database
from app.api.routes_prediction import router as predict_router
from app.api.routes_transactions import router as transactions_router
from app.api.routes_alerts import router as alerts_router
from app.api.routes_customers import router as customers_router
from app.api.routes_feedback import router as feedback_router
from app.api.routes_metrics import router as metrics_router
from app.api.routes_health import router as health_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure DB tables are created and seed data is present
    logger.info("[Startup] Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("[Startup] Running database seeder...")
    seed_database()
    yield
    # Shutdown logic if needed
    logger.info("[Shutdown] Cleaning up FraudShield AI resources...")

# -- Security Headers Middleware --
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
        return response

# Gate Swagger docs in production
is_production = os.getenv("ENVIRONMENT", "development") == "production"

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Real-time, explainable AI fraud-risk detection engine.",
    openapi_url=None if is_production else f"{settings.API_V1_STR}/openapi.json",
    docs_url=None if is_production else f"{settings.API_V1_STR}/docs",
    redoc_url=None if is_production else f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# Configure CORS — no wildcard "*" allowed with allow_credentials=True
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)

# Security headers on every response
app.add_middleware(SecurityHeadersMiddleware)

# Register API Routers
app.include_router(predict_router, prefix=settings.API_V1_STR)
app.include_router(transactions_router, prefix=settings.API_V1_STR)
app.include_router(alerts_router, prefix=settings.API_V1_STR)
app.include_router(customers_router, prefix=settings.API_V1_STR)
app.include_router(feedback_router, prefix=settings.API_V1_STR)
app.include_router(metrics_router, prefix=settings.API_V1_STR)
app.include_router(health_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "message": "Welcome to FraudShield AI Backend API",
        "docs": "/api/docs",
        "health": "/api/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
