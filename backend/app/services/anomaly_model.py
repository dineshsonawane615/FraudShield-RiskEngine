import os
import joblib
import numpy as np
import pandas as pd
from app.config import settings

class AnomalyModelService:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AnomalyModelService, cls).__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        model_path = settings.ISOLATION_FOREST_PATH
        if os.path.exists(model_path):
            try:
                self._model = joblib.load(model_path)
                print(f"[AnomalyModelService] Loaded Isolation Forest model from {model_path}")
            except Exception as e:
                print(f"[AnomalyModelService] Error loading Isolation Forest: {e}")
                self._model = None
        else:
            print(f"[AnomalyModelService] Warning: Isolation Forest model file not found at {model_path}")
            self._model = None

    def predict_anomaly_score(self, features_df: pd.DataFrame) -> float:
        """
        Returns normalized anomaly score between 0.0 (normal) and 1.0 (highly anomalous).
        """
        if self._model is None:
            # Fallback heuristic
            z_score = features_df.get("amount_z_score", [0]).iloc[0]
            loc_anom = features_df.get("location_anomaly", [0]).iloc[0]
            if z_score > 4.0 or loc_anom == 1:
                return 0.80
            return 0.10

        try:
            # IsolationForest decision_function returns negative values for anomalies, positive for normal
            raw_score = float(self._model.decision_function(features_df)[0])
            # Transform raw score to [0, 1] anomaly score where 1 is extreme anomaly
            anomaly_score = 1.0 / (1.0 + np.exp(raw_score * 8.0))
            return float(np.clip(anomaly_score, 0.0, 1.0))
        except Exception as e:
            print(f"[AnomalyModelService] Prediction error: {e}")
            return 0.10

anomaly_model_service = AnomalyModelService()
