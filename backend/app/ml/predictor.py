"""
Predictor Engine for RecoverAI Recovery Model.
Loads trained model artifact, extracts pre-action features,
predicts recovery probability, computes risk score, categorizes risk level,
and calculates expected recovery amount in integer paise.
"""

import os
import joblib
import numpy as np
from typing import Dict, Any, Optional

from app.models.revenue_event import RevenueEvent
from app.models.customer import Customer
from app.ml.features import extract_features, features_to_vector, FEATURE_NAMES

MODEL_PATH_DEFAULT = "backend/app/ml/artifacts/recovery_model.joblib"
MODEL_VERSION = "v1.0.0"


class RecoveryPredictor:
    def __init__(self, model_path: Optional[str] = None):
        self.model_version = MODEL_VERSION
        self.model = None
        self.feature_names = FEATURE_NAMES
        self._load_model(model_path)

    def _load_model(self, model_path: Optional[str]):
        paths_to_check = [
            model_path,
            MODEL_PATH_DEFAULT,
            "app/ml/artifacts/recovery_model.joblib",
            "../backend/app/ml/artifacts/recovery_model.joblib"
        ]
        chosen_path = None
        for p in paths_to_check:
            if p and os.path.exists(p):
                chosen_path = p
                break

        if chosen_path:
            try:
                artifact = joblib.load(chosen_path)
                self.model = artifact.get("model")
                self.feature_names = artifact.get("feature_names", FEATURE_NAMES)
                if "metrics" in artifact and "model_version" in artifact["metrics"]:
                    self.model_version = artifact["metrics"]["model_version"]
            except Exception as e:
                print(f"Warning: Failed to load model from {chosen_path}: {e}")
                self.model = None

    def predict_event(
        self,
        event: RevenueEvent,
        customer: Customer,
        previous_attempts_count: int = 0,
        previous_successful_count: int = 0
    ) -> Dict[str, Any]:
        """
        Run inference on a single revenue event and customer history.
        """
        features_dict = extract_features(
            event=event,
            customer=customer,
            previous_attempts_count=previous_attempts_count,
            previous_successful_count=previous_successful_count
        )
        vec = np.array([features_to_vector(features_dict)])

        if self.model is not None:
            try:
                prob_raw = self.model.predict_proba(vec)[0, 1]
                recovery_prob = float(np.clip(prob_raw, 0.0, 1.0))
            except Exception as e:
                print(f"Prediction fallback due to error: {e}")
                recovery_prob = self._heuristic_fallback(features_dict)
        else:
            recovery_prob = self._heuristic_fallback(features_dict)

        # Opt out rule: if customer opted out, recovery probability is 0
        if customer.opt_out:
            recovery_prob = 0.0

        risk_score = round(1.0 - recovery_prob, 4)
        recovery_prob = round(recovery_prob, 4)

        # Calculate expected recovery amount in integer paise
        expected_recovery_amount = int(round(float(event.amount) * recovery_prob))

        # Categorize risk level
        risk_level = self.determine_risk_level(recovery_prob)

        return {
            "recovery_probability": recovery_prob,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "expected_recovery_amount": expected_recovery_amount,
            "model_version": self.model_version,
            "features_snapshot": features_dict
        }

    @staticmethod
    def determine_risk_level(recovery_prob: float) -> str:
        """
        Risk Level Thresholds:
        - CRITICAL: recovery_probability < 0.25
        - HIGH: 0.25 <= recovery_probability < 0.50
        - MEDIUM: 0.50 <= recovery_probability < 0.75
        - LOW: recovery_probability >= 0.75
        """
        if recovery_prob < 0.25:
            return "CRITICAL"
        elif recovery_prob < 0.50:
            return "HIGH"
        elif recovery_prob < 0.75:
            return "MEDIUM"
        else:
            return "LOW"

    @staticmethod
    def _heuristic_fallback(features: Dict[str, Any]) -> float:
        """Heuristic calculation if trained model artifact is not loaded."""
        success_rate = features.get("customer_success_rate", 0.5)
        overdue = features.get("days_overdue", 0)
        prob = 0.50 + (success_rate - 0.5) * 0.4 - min(overdue * 0.005, 0.3)
        return float(np.clip(prob, 0.05, 0.95))


# Global Singleton Instance
predictor = RecoveryPredictor()
