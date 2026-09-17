import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    precision_score, recall_score, f1_score, precision_recall_curve, 
    auc, confusion_matrix
)
import xgboost as xgb

from data.prepare_dataset import generate_synthetic_dataset


FEATURE_COLUMNS = [
    "amount", "customer_avg_amount", "amount_ratio", "amount_z_score",
    "is_new_device", "transactions_last_10min", "transactions_last_1hour",
    "transactions_last_24hours", "unusual_time", "location_anomaly",
    "distance_from_usual_location", "customer_transaction_count", "hour", "day_of_week",
    "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10"
]

def train_and_save_models():
    # 1. Output directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    models_dir = os.path.join(base_dir, "trained_models")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)

    # 2. Dataset loading or generation
    csv_path = os.path.join(data_dir, "fraud_dataset.csv")
    if os.path.exists(csv_path):
        print(f"Loading dataset from {csv_path}...")
        df = pd.read_csv(csv_path)
    else:
        print("Generating synthetic dataset...")
        df = generate_synthetic_dataset(n_samples=10000, fraud_ratio=0.03)
        df.to_csv(csv_path, index=False)

    X = df[FEATURE_COLUMNS]
    y = df["is_fraud"]

    # 3. Train / Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 4. Standard Scaler
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 5. Train XGBoost Classifier (handling severe class imbalance with scale_pos_weight)
    num_neg = (y_train == 0).sum()
    num_pos = (y_train == 1).sum()
    scale_pos_weight = float(num_neg) / float(num_pos if num_pos > 0 else 1)

    print(f"Training XGBoost Classifier (Class imbalance ratio: {scale_pos_weight:.2f})...")
    xgb_model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        eval_metric="logloss"
    )
    xgb_model.fit(X_train, y_train)

    # Predictions & probabilities
    y_pred_proba = xgb_model.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)

    # Metrics computation
    precision = float(precision_score(y_test, y_pred, zero_division=0))
    recall = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))

    precision_curve, recall_curve, _ = precision_recall_curve(y_test, y_pred_proba)
    pr_auc = float(auc(recall_curve, precision_curve))

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    fpr = float(fp) / float(fp + tn) if (fp + tn) > 0 else 0.0
    fnr = float(fn) / float(fn + tp) if (fn + tp) > 0 else 0.0

    print("--- XGBoost Model Evaluation ---")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print(f"PR-AUC:    {pr_auc:.4f}")
    print(f"FPR:       {fpr:.4f}")
    print(f"FNR:       {fnr:.4f}")
    print(f"Confusion Matrix:\n{cm}")

    # 6. Train Isolation Forest (Unsupervised Anomaly Detection trained on legit baseline)
    print("Training Isolation Forest Anomaly Model...")
    X_legit_train = X_train[y_train == 0]
    iforest = IsolationForest(
        n_estimators=100,
        contamination=0.03,
        random_state=42
    )
    iforest.fit(X_legit_train)

    # 7. Save Models and Metrics
    xgb_path = os.path.join(models_dir, "xgboost_model.joblib")
    iforest_path = os.path.join(models_dir, "isolation_forest.joblib")
    scaler_path = os.path.join(models_dir, "scaler.joblib")
    metrics_path = os.path.join(models_dir, "metrics.json")

    joblib.dump(xgb_model, xgb_path)
    joblib.dump(iforest, iforest_path)
    joblib.dump(scaler, scaler_path)

    metrics_payload = {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "pr_auc": round(pr_auc, 4),
        "false_positive_rate": round(fpr, 4),
        "false_negative_rate": round(fnr, 4),
        "confusion_matrix": cm.tolist(),
        "feature_columns": FEATURE_COLUMNS
    }

    with open(metrics_path, "w") as f:
        json.dump(metrics_payload, f, indent=2)

    print(f"Successfully saved trained models and metrics to {models_dir}")

if __name__ == "__main__":
    train_and_save_models()
