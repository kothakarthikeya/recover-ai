"""
Training Script for RecoverAI Recovery Prediction Model.
Generates synthetic outcome labels, trains an XGBoost/GradientBoosting classifier,
evaluates metrics (ROC-AUC, PR-AUC, F1, Precision, Recall, Brier Score),
and saves the trained model artifact.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
    brier_score_loss
)

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    from sklearn.ensemble import GradientBoostingClassifier
    HAS_XGBOOST = False

from app.ml.features import FEATURE_NAMES, extract_features, features_to_vector


def generate_synthetic_label(row: pd.Series) -> int:
    """
    Deterministic synthetic label generator for training/demo purposes ONLY.
    Note: Labels are synthesized based on customer history, event type, and overdue days.
    """
    if row.get("opt_out", 0) == 1:
        return 0

    base_prob = 0.50

    # Success rate influence (+0.25 max)
    base_prob += (row.get("customer_success_rate", 0.5) - 0.5) * 0.50

    # Overdue penalty (-0.005 per day)
    days_overdue = row.get("days_overdue", 0)
    base_prob -= min(days_overdue * 0.005, 0.35)

    # Failure reason impact
    reason = row.get("failure_reason_encoded", 0)
    if reason in [0, 4, 6]:  # insufficient funds, network timeout, session expired (high recovery)
        base_prob += 0.15
    elif reason in [3, 10, 12, 15]:  # expired card, frozen account, severe overdue (low recovery)
        base_prob -= 0.20

    # Event type impact
    event_type = row.get("event_type_encoded", 0)
    if event_type == 0:  # payment failure
        base_prob += 0.05
    elif event_type == 3:  # overdue invoice
        base_prob -= 0.10

    # Bound probability
    final_prob = np.clip(base_prob, 0.05, 0.95)

    # Pseudo-random choice derived from row values for reproducibility
    seed_val = int(row.get("amount", 1000) + row.get("transaction_count", 1) * 100 + days_overdue * 10) % 10000
    rng = np.random.RandomState(seed_val)
    return 1 if rng.rand() < final_prob else 0


def load_dataset_and_features(dataset_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """Load dataset from synthetic JSON, extract features and generate labels."""
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    customers = {c["id"]: c for c in data["customers"]}
    events = data["revenue_events"]

    # Mock object classes for feature extractor compatibility
    class MockCustomer:
        def __init__(self, d):
            self.successful_tx_count = d.get("successful_tx_count", 0)
            self.failed_tx_count = d.get("failed_tx_count", 0)
            self.total_spent_paise = d.get("total_spent_paise", 0)
            self.opt_out = d.get("opt_out", False)

    class MockEvent:
        def __init__(self, d):
            self.amount = d.get("amount", 0)
            self.event_type = d.get("event_type", "payment_failure")
            self.failure_reason = d.get("failure_reason", "insufficient_funds")
            self.days_overdue = d.get("days_overdue", 0)
            self.event_time = None

    X_list = []
    for e in events:
        cust_data = customers.get(e["customer_id"], {})
        mock_c = MockCustomer(cust_data)
        mock_e = MockEvent(e)
        feat_dict = extract_features(mock_e, mock_c)
        vec = features_to_vector(feat_dict)
        X_list.append(vec)

    X = np.array(X_list)
    df_feat = pd.DataFrame(X, columns=FEATURE_NAMES)
    y = df_feat.apply(generate_synthetic_label, axis=1).values

    return X, y


def train_model(
    dataset_path: str = "scripts/synthetic_dataset.json",
    artifact_dir: str = "backend/app/ml/artifacts"
) -> Dict[str, Any]:
    """Train XGBoost / GradientBoosting model on features and save artifact."""
    if not os.path.exists(dataset_path):
        # Fallback path if run from backend/ directory
        if os.path.exists("../scripts/synthetic_dataset.json"):
            dataset_path = "../scripts/synthetic_dataset.json"

    print(f"Loading synthetic dataset from '{dataset_path}'...")
    X, y = load_dataset_and_features(dataset_path)

    # 80/20 Stratified train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    print(f"Dataset split: {len(X_train)} training samples, {len(X_test)} test samples.")

    if HAS_XGBOOST:
        print("Training XGBoost Classifier...")
        model = XGBClassifier(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=4,
            random_state=42,
            eval_metric="logloss"
        )
        model_name = "XGBoost"
    else:
        print("Training GradientBoosting Classifier (scikit-learn fallback)...")
        model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=4,
            random_state=42
        )
        model_name = "GradientBoosting"

    model.fit(X_train, y_train)

    # Evaluate
    y_pred_prob = model.predict_proba(X_test)[:, 1]
    y_pred_binary = (y_pred_prob >= 0.50).astype(int)

    roc_auc = float(roc_auc_score(y_test, y_pred_prob))
    pr_auc = float(average_precision_score(y_test, y_pred_prob))
    precision = float(precision_score(y_test, y_pred_binary, zero_division=0))
    recall = float(recall_score(y_test, y_pred_binary, zero_division=0))
    f1 = float(f1_score(y_test, y_pred_binary, zero_division=0))
    brier = float(brier_score_loss(y_test, y_pred_prob))

    metrics = {
        "model_type": model_name,
        "model_version": "v1.0.0",
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "brier_score": round(brier, 4)
    }

    print("\n--- Model Evaluation Results ---")
    for k, v in metrics.items():
        print(f"  {k}: {v}")

    # Ensure artifact directory exists
    os.makedirs(artifact_dir, exist_ok=True)
    model_path = os.path.join(artifact_dir, "recovery_model.joblib")
    joblib.dump({"model": model, "feature_names": FEATURE_NAMES, "metrics": metrics}, model_path)

    metadata_path = os.path.join(artifact_dir, "model_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nTrained model successfully saved to '{model_path}'.")
    return metrics


if __name__ == "__main__":
    train_model()
