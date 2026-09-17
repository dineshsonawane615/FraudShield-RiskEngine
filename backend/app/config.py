import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "FraudShield AI Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./fraudshield.db")
    
    # CORS — Never use "*" with allow_credentials=True; list explicit origins only.
    # In production: set FRONTEND_URL env var in Railway to your Vercel deployment URL.
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Production frontend URL — set this in Railway env vars (e.g. https://your-app.vercel.app)
    FRONTEND_URL: str = ""
    
    # Model settings — config.py is at backend/app/config.py, go up one level to backend/
    MODELS_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "trained_models"))
    XGBOOST_MODEL_PATH: str = os.path.join(MODELS_DIR, "xgboost_model.joblib")
    ISOLATION_FOREST_PATH: str = os.path.join(MODELS_DIR, "isolation_forest.joblib")
    SCALER_PATH: str = os.path.join(MODELS_DIR, "scaler.joblib")
    METRICS_PATH: str = os.path.join(MODELS_DIR, "metrics.json")
    
    # Risk Engine Weights
    XGB_WEIGHT: float = 0.60
    IFOREST_WEIGHT: float = 0.40
    
    # Risk Thresholds
    LOW_THRESHOLD: float = 39.0
    MEDIUM_THRESHOLD: float = 69.0
    
    class Config:
        case_sensitive = True

settings = Settings()

# Dynamically add the production frontend URL to CORS whitelist at startup.
# Set FRONTEND_URL=https://your-app.vercel.app in Railway environment variables.
if settings.FRONTEND_URL and settings.FRONTEND_URL not in settings.ALLOWED_ORIGINS:
    settings.ALLOWED_ORIGINS.append(settings.FRONTEND_URL)
