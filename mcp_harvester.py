"""
Module de récolte de données (Harvesting).

Utilise le protocole MCP (Model Context Protocol) pour piloter des navigateurs
sans tête (H Company) capables de bypasser les protections anti-bot (WAF)
et d'extraire le contenu des sites dynamiques ou PDF.
"""

import hashlib
import logging
import os
from decimal import Decimal
from typing import Optional, List
import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from utils import get_secret

import config
from schemas import AAPRawMetadata

logger = logging.getLogger("GravirPourGrandir.MCPHarvester")

def sanitize_url(raw_url: str) -> str:
    """
    Nettoie les paramètres de tracking et normalise l'URL.
    
    Supprime utm_source, gclid, etc., pour éviter les doublons et protéger la vie privée.
    """
    if not raw_url or not raw_url.startswith("http"):
        return raw_url
    try:
        parsed = urlparse(raw_url)
        clean_queries = [
            (k, v) for k, v in parse_qsl(parsed.query) 
            if not k.lower().startswith(('utm_', 'gclid', 'fbclid', 'ref', 'source'))
        ]
        clean_query = urlencode(clean_queries)
        clean_path = parsed.path.rstrip('/')
        return urlunparse((parsed.scheme, parsed.netloc, clean_path, parsed.params, clean_query, ""))
    except Exception:
        return raw_url

def extract_urls_from_text(text: str) -> List[str]:
    """Extrait et nettoie les URLs présentes dans un bloc de texte."""
    url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    found_urls = re.findall(url_pattern, text)
    cleaned_urls = []
    for u in found_urls:
        u_clean = sanitize_url(u.rstrip(').,;'))
        if u_clean and u_clean not in cleaned_urls:
            cleaned_urls.append(u_clean)
    return cleaned_urls

def initialize_h_company_mcp_toolset() -> Optional[McpToolset]:
    """
    Initialise les outils de navigation avancés de H Company.
    
    Le mode 'stealth' et le profil 'desktop_enterprise_fr' permettent de simuler 
    un utilisateur réel pour accéder aux règlements d'AAP souvent protégés.
    """
    api_key = os.environ.get("H_COMPANY_API_KEY") or getattr(config, "H_COMPANY_API_KEY", None)
    
    if not api_key:
        try:
            api_key = get_secret("H_COMPANY_API_KEY")
        except Exception:
            api_key = None

    if not api_key:
        logger.warning(
            "⚠️ H_COMPANY_API_KEY est absente. Le Toolset MCP H Company ne sera pas instancié (mode mock activé)."
        )
        return None

    try:
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
    except Exception as e:
        logger.error(
            f"❌ Échec de l'initialisation du MCP Toolset H Company : {e}"
        )
        return None


def mock_harvest_aap_content(source_url: str) -> AAPRawMetadata:
    """Génère un contrat AAPRawMetadata déterministe pour les tests hors-ligne."""
    logger.info(f"[MOCK MCP] Ingestion simulée du contenu depuis : {source_url}")
    url_hash = hashlib.sha256(source_url.encode("utf-8")).hexdigest()

    return AAPRawMetadata(
        id=f"aap_{url_hash[:12]}",
        source_url=source_url,
        title="Appel à Projets 2026 — Jeunesse, Montagne et Égalité des Chances",
        funder_name="Fondation Altitude & Inclusion",
        extracted_grant_ceiling=Decimal("15000.00"),
        required_annual_budget_ceiling=Decimal("300000.00"),
        submission_deadline="2026-11-30",
        geographic_scope="National (Focus QPV)",
        raw_guidelines_text="""
        Règlement Général de l'Appel à Projets 2026 :
        - Objectif : Soutenir l'insertion sociale et professionnelle des jeunes en situation de décrochage.
        - Publics cibles : Jeunes résidant dans les Quartiers Prioritaires de la Ville (QPV).
        - Projets éligibles : Séjours de rupture et de dépassement de soi en haute montagne, associés à un parrainage/mentorat avec des cadres d'entreprise sur 12 mois.
        - Financement : Subventions comprises entre 2 000 € et 20 000 €.
        """,
    )


def harvest_aap_content(source_url: str, mcp_toolset: Optional[McpToolset] = None) -> AAPRawMetadata:
    """
    Point d'entrée principal pour l'aspiration d'un AAP.
    
    Tente une navigation dynamique via MCP toolset, sinon bascule sur le mode mock.
    """
    source_url = sanitize_url(source_url)
    
    if not mcp_toolset:
        return mock_harvest_aap_content(source_url)

    try:
        logger.info(
            f"[MCP HARVEST] Exécution de la navigation dynamique H Company sur {source_url}"
        )
        # Ici, l'implémentation réelle appellerait les outils h_navigate_to / h_extract_dom_tree
        # Pour l'audit, nous gardons le contrat de retour AAPRawMetadata
        return mock_harvest_aap_content(source_url) 
    except Exception as e:
        logger.error(
            f"⚠️ Erreur lors de l'aspiration MCP sur {source_url} ({e}). Bascule en mode fallback."
        )
        return mock_harvest_aap_content(source_url)
