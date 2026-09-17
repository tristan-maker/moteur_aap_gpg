import os
import logging
from typing import Dict, Any
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

logger = logging.getLogger("GravirPourGrandir.MCPHarvester")


def initialize_h_company_mcp_toolset() -> McpToolset:
    """Instancie le toolset MCP H Company pour la navigation dynamique et le téléchargement.

    Returns:
        McpToolset: Outil MCP configuré pour l'ADK.

    Raises:
        ValueError: Si la clé d'API H_COMPANY_API_KEY est absente de l'environnement.
    """
    api_key = os.environ.get("H_COMPANY_API_KEY")
    if not api_key:
        raise ValueError(
            "CRITICAL: La clé H_COMPANY_API_KEY est absente de l'environnement."
        )

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
                    "--user-agent-profile=desktop_enterprise_fr",
                ],
                env={
                    "H_API_KEY": api_key,
                    "NODE_OPTIONS": "--max-old-space-size=4096",
                },
            )
        ),
        tool_filter=[
            "h_navigate_to",
            "h_extract_dom_tree",
            "h_extract_input_fields",
            "h_capture_full_page_screenshot",
            "h_download_linked_binary",
        ],
    )


def mock_harvest_aap_content(url: str) -> Dict[str, Any]:
    """Bouchon (Mock) pour l'extraction de contenu sans appel au serveur MCP externe.

    Args:
        url (str): URL du portail AAP à ingérer.

    Returns:
        Dict[str, Any]: Contenu extrait simulé sous forme de dictionnaire structuré.
    """
    logger.info(f"[MOCK MCP] Ingestion simulée du contenu depuis : {url}")
    return {
        "status": "success",
        "url": url,
        "extracted_text": (
            "Appel à Projets 2026 - Inclusion et Sport de Montagne.\n"
            "Objectif : Financer des projets favorisant l'insertion des jeunes QPV.\n"
            "Plafond de subvention : 15 000 EUR. Date limite : 2026-10-31."
        ),
        "raw_dom_length": 1420,
        "has_pdf_attachments": True,
    }
