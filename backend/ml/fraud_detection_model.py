"""Fraud detection model wrapper (RandomForest)."""
import os, joblib, numpy as np

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(MODEL_DIR, "fraud_model.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "fraud_scaler.pkl")

FEATURES = ["amount", "hour_of_day", "day_of_week", "amount_balance_ratio"]


class FraudDetector:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.load()

    def load(self):
        if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
            self.model = joblib.load(MODEL_PATH)
            self.scaler = joblib.load(SCALER_PATH)

    @property
    def ready(self) -> bool:
        return self.model is not None and self.scaler is not None

    def predict(self, payload: dict) -> dict:
        if not self.ready:
            # Fallback: simple rule
            amt = float(payload.get("amount", 0))
            ratio = float(payload.get("amount_balance_ratio", 0))
            prob = min(1.0, (amt / 20000) * 0.5 + ratio * 0.5)
            return {"is_fraud": prob > 0.7, "fraud_probability": prob,
                    "model": "fallback-rule"}
        x = np.array([[float(payload.get(f, 0)) for f in FEATURES]])
        x_scaled = self.scaler.transform(x)
        prob = float(self.model.predict_proba(x_scaled)[0][1])
        return {"is_fraud": prob > 0.7, "fraud_probability": prob,
                "model": "random-forest"}


detector = FraudDetector()
