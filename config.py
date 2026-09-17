import logging
import os
from decimal import Decimal
from typing import Dict, Any
from vertexai.generative_models import HarmCategory, HarmBlockThreshold

logger = logging.getLogger("GravirPourGrandir.Config")

# Identifiants GCP & Modèles
GCP_PROJECT_ID: str = os.getenv("GOOGLE_CLOUD_PROJECT", "gravir-pour-grandir-prod")
GCP_LOCATION: str = os.getenv("GOOGLE_CLOUD_LOCATION", "europe-west9")

MODEL_GEMINI_FLASH: str = "gemini-2.5-flash"
MODEL_GEMINI_PRO: str = "gemini-3.8-pro"

# Clés d'outils tiers (MCP)
H_COMPANY_API_KEY: str = os.getenv("H_COMPANY_API_KEY", "")

# Seuils Déterministes & Ratios Métiers (DAA Section 1.1)
MIN_GRANT_REQUEST_EURO: Decimal = Decimal("2000.00")
MAX_ASSOCIATION_BUDGET_EURO: Decimal = Decimal("400000.00")

# Sécurité Vertex AI
PROD_SAFETY_SETTINGS: Dict[HarmCategory, HarmBlockThreshold] = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}

def validate_environment() -> bool:
    """Valide l'environnement de runtime et log l'état des dépendances."""
    if not H_COMPANY_API_KEY:
        logger.warning("⚠️ H_COMPANY_API_KEY est absente. Le mode mock sera requis pour les extractions MCP.")
    logger.info(f"✔ Configuration initialisée pour le projet GCP : {GCP_PROJECT_ID} ({GCP_LOCATION})")
    return True
