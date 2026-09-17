import os
import logging
from dotenv import load_dotenv
from google.genai import types

# Chargement automatique des variables d'environnement depuis le fichier .env local
load_dotenv()
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
# Suppression de l'import vertexai pour utiliser google.genai.types (plus stable pour l'ADK)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GravirPourGrandir")

# --- Configuration des Ressources Google Workspace ---
SPREADSHEET_ID = os.environ.get("GOOGLE_SHEETS_ID")
DOCS_FOLDER_ID = os.environ.get("GOOGLE_DOCS_FOLDER_ID")

# --- Configuration Globale des Safety Settings (Vertex AI) ---
PROD_SAFETY_SETTINGS = [
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_LOW_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_LOW_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_LOW_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
]

def initialize_h_company_mcp_toolset() -> McpToolset:
    """Instancie le toolset MCP H Company pour la navigation dynamique."""
    api_key = os.environ.get("H_COMPANY_API_KEY")
    if not api_key:
        raise ValueError("CRITICAL: La clé H_COMPANY_API_KEY est absente de l'environnement.")

    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="npx",
                args=[
                    "-y", 
                    "@h-company/mcp-runner@latest", 
                    "--headless", 
                    "--timeout=60000",
                    "--stealth-mode",
                    "--user-agent-profile=desktop_enterprise_fr"
                ],
                env={
                    "H_API_KEY": api_key,
                    "NODE_OPTIONS": "--max-old-space-size=4096"
                }
            )
        ),
        tool_filter=[
            "h_navigate_to", "h_extract_dom_tree", "h_extract_input_fields",
            "h_capture_full_page_screenshot", "h_download_linked_binary"
        ]
    )