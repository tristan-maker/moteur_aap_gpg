import os
import logging
from typing import Dict, Any
from decimal import Decimal

# --- 1. Configuration du Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
)
logger = logging.getLogger("GravirPourGrandir.Config")

# --- 2. Paramètres d'Infrastructure & GCP ---
GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "gravir-pour-grandir-prod")
GCP_REGION: str = os.getenv("GCP_REGION", "europe-west9")

# --- 3. Modèles de Langage Gemini ---
MODEL_GEMINI_FLASH: str = "gemini-2.5-flash"
MODEL_GEMINI_PRO: str = "gemini-3.8-pro"

# --- 4. Règles Métiers & Seuils Financiers Déterministes ---
MIN_GRANT_REQUEST_EURO: Decimal = Decimal("2000.00")
MAX_ASSOCIATION_BUDGET_EURO: Decimal = Decimal("400000.00")
DEFAULT_COHORT_SIZE: int = 10
EXECUTION_YEAR: int = 2026

# --- 5. Matrice Global de Sécurité (Safety Settings Vertex AI) ---
# Note : Ces configurations sont passées aux instances LlmAgent de l'ADK
PROD_SAFETY_SETTINGS: Dict[str, str] = {
    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_LOW_AND_ABOVE",
    "HARM_CATEGORY_HARASSMENT": "BLOCK_LOW_AND_ABOVE",
    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_LOW_AND_ABOVE",
    "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE",
}

def validate_environment() -> bool:
    """Vérifie la présence des clés d'API requises pour les intégrations tierces."""
    h_key = os.getenv("H_COMPANY_API_KEY")
    if not h_key:
        logger.warning(
            "⚠️ H_COMPANY_API_KEY est absente. Le mode mock sera requis pour les extractions MCP."
        )
    else:
        logger.info("✔ Clé API H Company détectée.")
    
    logger.info(f"✔ Configuration initialisée pour le projet GCP : {GCP_PROJECT_ID} ({GCP_REGION})")
    return True

if __name__ == "__main__":
    validate_environment()
