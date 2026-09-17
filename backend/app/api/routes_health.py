import os
from fastapi import APIRouter
from sqlalchemy import text
from app.config import settings
from app.database.database import engine

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
def health_check():
    xgb_loaded = os.path.exists(settings.XGBOOST_MODEL_PATH)
    iforest_loaded = os.path.exists(settings.ISOLATION_FOREST_PATH)

    # Actually verify the database connection rather than hardcoding "connected"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "error"

    overall_status = "healthy" if db_status == "connected" else "degraded"

    return {
        "status": overall_status,
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": db_status,
        "models": {
            "xgboost": "loaded" if xgb_loaded else "not_trained",
            "isolation_forest": "loaded" if iforest_loaded else "not_trained"
        }
    }
