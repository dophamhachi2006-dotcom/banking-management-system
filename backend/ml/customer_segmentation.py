"""KMeans-based customer segmentation."""
import os, joblib, numpy as np

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(MODEL_DIR, "segmenter_model.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "segmenter_scaler.pkl")

FEATURES = ["total_balance", "tx_count", "avg_tx_amount"]
LABELS = {0: "VIP", 1: "Active", 2: "Regular", 3: "Inactive"}


class CustomerSegmenter:
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
        return self.model is not None

    def predict(self, payload: dict) -> dict:
        if not self.ready:
            bal = float(payload.get("total_balance", 0))
            seg = "VIP" if bal > 50000 else "Active" if bal > 10000 \
                else "Regular" if bal > 1000 else "Inactive"
            return {"segment": seg, "model": "fallback-rule"}
        x = np.array([[float(payload.get(f, 0)) for f in FEATURES]])
        x_scaled = self.scaler.transform(x)
        cluster = int(self.model.predict(x_scaled)[0])
        return {"segment": LABELS.get(cluster, str(cluster)),
                "cluster": cluster, "model": "kmeans"}


segmenter = CustomerSegmenter()
