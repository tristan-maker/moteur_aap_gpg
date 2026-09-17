import os
from typing import Any, Dict

try:
    from google.adk.tools.mcp_tool import McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
    from mcp import StdioServerParameters
    HAS_MCP_DEPS = True
except ImportError:
    HAS_MCP_DEPS = False
    McpToolset = Any  # type: ignore


def initialize_h_company_mcp_toolset() -> Any:
    """Instancie le toolset MCP H Company pour la navigation dynamique."""
    if not HAS_MCP_DEPS:
        raise ImportError(
            "Les dépendances MCP sont manquantes. "
            "Installez-les via : pip install \"google-adk[mcp]\" mcp"
        )

    api_key = os.environ.get("H_COMPANY_API_KEY", "mock_h_company_key")

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


class MockMcpFormHarvester:
    """Harvesteur de formulaire simulant l'inspection DOM MCP hors-ligne."""

    def extract_target_form_schema(
        self, portal_url: str, aap_id: str
    ) -> Dict[str, Any]:
        """Simule l'extraction de la structure d'un formulaire de candidature."""
        return {
            "aap_id": aap_id,
            "portal_url": portal_url,
            "form_fields": [
                {
                    "field_id": "q1_pitch",
                    "question_label": "Présentation synthétique du projet",
                    "character_limit": 1000,
                    "expected_content_type": "narrative",
                },
                {
                    "field_id": "q2_impact_qpv",
                    "question_label": "Impact mesurable sur les jeunes des QPV et mentorat",
                    "character_limit": 1800,
                    "expected_content_type": "narrative",
                },
                {
                    "field_id": "q3_budget_total",
                    "question_label": "Montant total du projet et subvention sollicitée",
                    "character_limit": 500,
                    "expected_content_type": "budget",
                },
            ],
            "mandatory_attachments": [
                "RIB_Association.pdf",
                "Statuts_GPG_2026.pdf",
                "Attestation_Rescrit_Fiscal.pdf",
            ],
        }
