import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

API_BASE_URL = os.getenv("KITUNGA_API_BASE_URL", "http://127.0.0.1:8000")
DEVICE_ID = os.getenv("KITUNGA_DEVICE_ID", "KITUNGA-PI-001")
BASKET_CODE = os.getenv("KITUNGA_BASKET_CODE", "SB-001")

CONFIDENCE_THRESHOLD = float(os.getenv("KITUNGA_CONFIDENCE_THRESHOLD", "0.75"))
COOLDOWN_SECONDS = float(os.getenv("KITUNGA_COOLDOWN_SECONDS", "4"))
SCAN_INTERVAL_SECONDS = float(os.getenv("KITUNGA_SCAN_INTERVAL_SECONDS", "2"))
API_TIMEOUT_SECONDS = float(os.getenv("KITUNGA_API_TIMEOUT_SECONDS", "5"))

CAMERA_INDEX = int(os.getenv("KITUNGA_CAMERA_INDEX", "0"))
CAPTURES_DIR = BASE_DIR / "captures"
MODEL_PATH = BASE_DIR / "models" / "best.pt"
TEST_IMAGE_PATH = os.getenv("KITUNGA_TEST_IMAGE_PATH", "")
