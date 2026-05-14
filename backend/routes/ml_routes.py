"""ML API routes - fraud prediction only.

Customer segmentation has been REMOVED per feedback; the endpoint is kept as
a 410 Gone response to make the removal explicit to any stale clients.
"""
from flask import Blueprint, request
from backend.api_response import ok, fail
from backend.ml.fraud_detection_model import detector

bp = Blueprint("ml", __name__)


@bp.post("/predict-fraud")
def predict_fraud():
    """Predict fraud probability for a transaction payload."""
    data = request.get_json(silent=True) or {}
    if "amount" not in data:
        return fail("amount required", 400)
    return ok(detector.predict(data))


@bp.post("/segment-customer")
def segment_customer():
    """Removed feature. Kept as a tombstone to inform legacy clients."""
    return fail(
        "Customer segmentation has been removed from this release.", 410
    )


@bp.get("/status")
def status():
    return ok({
        "fraud_model_ready": getattr(detector, "ready", False),
        "segmenter_ready": False,
    })