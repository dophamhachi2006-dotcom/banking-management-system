"""Backend configuration."""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    DEBUG      = os.getenv("FLASK_ENV", "development") == "development"
    PORT       = int(os.getenv("FLASK_PORT", "5000"))
    LARGE_TX_THRESHOLD = float(os.getenv("LARGE_TX_THRESHOLD", "50000"))
    PAGE_SIZE_DEFAULT  = 25
    PAGE_SIZE_MAX      = 200
