import logging
import os
from decimal import Decimal
from typing import Dict, Any

try:
    from google.genai.types import HarmCategory, HarmBlockThreshold
except Exception:
    try:
        from vertexai.generative_models import HarmCategory, HarmBlockThreshold
    except Exception:
        HarmCategory = None
        HarmBlockThreshold = None

logger = logging.getLogger("GravirPourGrandir.Config")

GCP_PROJECT_ID: str = os.getenv("GOOGLE_CLOUD_PROJECT", "aap-gpg")
GCP_LOCATION: str = os.getenv("GOOGLE_CLOUD_LOCATION", "europe-west9")

MODEL_GEMINI_FLASH: str = "gemini-2.5-flash"
MODEL_GEMINI_PRO: str = "gemini-3.8-pro"

H_COMPANY_API_KEY: str = os.getenv("H_COMPANY_API_KEY", "")

MIN_GRANT_REQUEST_EURO: Decimal = Decimal("2000.00")
MAX_ASSOCIATION_BUDGET_EURO: Decimal = Decimal("400000.00")
DEFAULT_COHORT_SIZE: int = 10

PROD_SAFETY_SETTINGS: Dict[Any, Any] = {}
if HarmCategory and HarmBlockThreshold:
    try:
        PROD_SAFETY_SETTINGS = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
    except Exception as e:
        logger.warning(f"Initialisation partielle des Safety Settings: {e}")

def validate_environment() -> bool:
    if not H_COMPANY_API_KEY:
        logger.warning("⚠️ H_COMPANY_API_KEY est absente. Le mode mock sera requis.")
    logger.info(f"✔ Configuration initialisée pour : {GCP_PROJECT_ID} ({GCP_LOCATION})")
    return True
