import os
import joblib
import pandas as pd
from app.config import settings

class FraudModelService:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FraudModelService, cls).__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        model_path = settings.XGBOOST_MODEL_PATH
        if os.path.exists(model_path):
            try:
                self._model = joblib.load(model_path)
                print(f"[FraudModelService] Loaded XGBoost model from {model_path}")
            except Exception as e:
                print(f"[FraudModelService] Error loading XGBoost model: {e}")
                self._model = None
        else:
            print(f"[FraudModelService] Warning: XGBoost model file not found at {model_path}")
            self._model = None

    def predict_proba(self, features_df: pd.DataFrame) -> float:
        """
        Returns supervised fraud probability P(Fraud) between 0.0 and 1.0.
        """
        if self._model is None:
            # Fallback heuristic if model file hasn't been generated yet
            z_score = features_df.get("amount_z_score", [0]).iloc[0]
            new_dev = features_df.get("is_new_device", [0]).iloc[0]
            if z_score > 5.0 or new_dev == 1:
                return 0.85
            return 0.05

        try:
            proba = float(self._model.predict_proba(features_df)[:, 1][0])
            return min(max(proba, 0.0), 1.0)
        except Exception as e:
            print(f"[FraudModelService] Prediction error: {e}")
            return 0.10

fraud_model_service = FraudModelService()
