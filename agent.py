"""
Module principal de l'agent Gravir Pour Grandir.

Ce module orchestre le pipeline de découverte d'Appels à Projets (AAP) via 
le framework Google ADK. Il gère l'expansion de requêtes, la recherche web, 
l'extraction de données structurées et la publication automatisée.
"""

from decimal import Decimal
import logging
import os
import sys
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import google_search
from google.genai import types
from pydantic import BaseModel, Field
from utils import get_secret

import config
from schemas import (
    SearchQueryMatrix,
    AAPStrategicScore,
    AAPRawMetadata,
    FullProposalDocument,
    FinancialApplicationPlan,
    ExpenseLineItem,
    NarrativeResponseItem,
)
from budget_engine import calculate_itemized_budget

logger = logging.getLogger("GravirPourGrandir.Agent")

# Injection du répertoire courant dans le PYTHONPATH pour le chargeur ADK
current_dir = str(Path(__file__).parent.resolve())
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Chargement du fichier .env pour le développement local
load_dotenv()

# --- Configuration de l'authentification ---
# Si aucune clé n'est fournie, nous configurons le SDK pour utiliser Vertex AI (authentification automatique via IAM)
if not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
    os.environ["GOOGLE_CLOUD_PROJECT"] = config.GCP_PROJECT_ID
    os.environ["GOOGLE_CLOUD_LOCATION"] = config.GCP_LOCATION
    logger.info("Mode Vertex AI activé : authentification automatique via IAM (sans clé API).")

# --- SCHÉMAS DE DONNÉES ---

class SearchResults(BaseModel):
    """Schéma de sortie pour l'extraction structurée des résultats de recherche."""
    findings: List[AAPRawMetadata] = Field(description="Liste des opportunités identifiées avec leurs métadonnées.")

# --- 1. DÉFINITION DES AGENTS (ex agents.py) ---

# Agent responsable de transformer une requête simple en stratégies de recherche complexes (Google Dorks)
query_expansion_agent = LlmAgent(
    name="QueryExpansionSpecialist",
    model=config.MODEL_GEMINI_FLASH,
    instruction="""
    Tu es l'Expert en Renseignement Financier et Veille Subventions de Gravir Pour Grandir.
    Ton objectif est de concevoir une matrice de requêtes de recherche Google avancées (Google Dorks)
    pour dénicher les opportunités de financements les plus récentes, directes ou indirectes.

    Axes de recherche à croiser obligatoirement :
    - Axe 1 : Quartiers prioritaires (QPV), jeunesse défavorisée, inclusion sociale, décrochage, E2C, missions locales.
    - Axe 2 : Sport de pleine nature, montagne, alpinisme, dépassement de soi, séjour de rupture éducative.
    - Axe 3 : Mentorat en entreprise, égalité des chances, mécénat de compétences, fondations abritées.

    Consignes techniques :
    1. Génère des opérateurs stricts ("appel à projets" OR "subvention").
    2. Spécifie l'année courante 2026.
    3. Réponds strictement selon le schéma JSON SearchQueryMatrix.
    """,
    generate_content_config=types.GenerateContentConfig(temperature=0.7, top_p=0.95),
    output_schema=SearchQueryMatrix,
    output_key="temp:generated_queries",
)

# Agent utilisant l'outil google_search pour naviguer sur le web
web_radar_agent = LlmAgent(
    name="GlobalWebRadarAgent",
    model=config.MODEL_GEMINI_FLASH,
    instruction="""
    Tu es le Radar Web d'acquisition d'opportunités de l'association.
    Pour chaque requête générée dans {temp:generated_queries}, utilise l'outil google_search
    pour identifier les appels à projets actifs.

    Règles :
    1. Identifie les URLs officielles de dépôt.
    2. Fournis une synthèse claire et détaillée avec les URLs canoniques.
    """,
    tools=[google_search],
    generate_content_config=types.GenerateContentConfig(temperature=0.2, top_p=0.85),
    output_key="temp:discovered_urls_text",
)

# Agent convertissant le texte non structuré du web en objets Python (AAPRawMetadata)
aap_extraction_agent = LlmAgent(
    name="AAPExtractionSpecialist",
    model=config.MODEL_GEMINI_FLASH,
    instruction="""
    Tu es l'Expert en Extraction de Données de Gravir Pour Grandir.
    Analyse les résultats de recherche fournis dans {temp:discovered_urls_text}.
    Transforme ces informations en une liste structurée d'opportunités (AAP) en suivant strictement le schéma.
    Assure-toi de capturer les URLs sources canoniques.
    """,
    generate_content_config=types.GenerateContentConfig(temperature=0.1),
    output_schema=SearchResults,
    output_key="temp:search_results",
)

# Outil Python enregistré pour être appelé par l'agent PublicationSpecialist
def publish_top_aaps_tool(findings: List[Dict[str, Any]]) -> str:
    """
    Filtre les AAPs selon les critères financiers (No-Go), sélectionne le Top 5 par 
    montant de subvention et publie les résultats vers le Google Sheet de l'association.
    
    Args:
        findings: Liste des dictionnaires représentant les AAPs extraits.
    """
    from sheets_publisher import publish_aaps_to_sheet
    
    # Conversion des dictionnaires bruts en modèles Pydantic pour le filtrage
    raw_aaps = [AAPRawMetadata(**f) for f in findings]
    
    # 1. Application du filtrage déterministe (Budget association vs Plafond subvention)
    eligible = apply_deterministic_nogo_filter(raw_aaps)
    
    # 2. Tri déterministe et extraction du Top 5
    top_aaps = sorted(eligible, key=lambda x: x.extracted_grant_ceiling or 0, reverse=True)[:5]
    
    if not top_aaps:
        return "Analyse terminée : Aucun AAP ne remplit les critères d'éligibilité financière (No-Go filter)."

    # 3. Résolution de l'ID Spreadsheet
    spreadsheet_id = os.getenv("SPREADSHEET_ID") or os.getenv("GOOGLE_SHEETS_ID")
    if not spreadsheet_id:
        spreadsheet_id = getattr(config, "SPREADSHEET_ID", None) or getattr(config, "GOOGLE_SHEETS_ID", None)
    if not spreadsheet_id:
        try:
            spreadsheet_id = get_secret("SPREADSHEET_ID")
        except Exception:
            return "Erreur : ID Google Sheet introuvable (Env/Secret Manager)."

    try:
        publish_aaps_to_sheet(spreadsheet_id, top_aaps)
        return f"Succès : {len(top_aaps)} AAPs éligibles ont été publiés dans le Google Sheet (ID: {spreadsheet_id})."
    except Exception as e:
        return f"Erreur lors de la publication technique : {str(e)}"

# Agent final gérant le reporting et l'archivage dans Google Sheets
aap_publisher_agent = LlmAgent(
    name="PublicationSpecialist",
    model=config.MODEL_GEMINI_FLASH,
    instruction="""
    Tu es l'Expert en Archivage de Gravir Pour Grandir.
    Prends les résultats extraits dans {temp:search_results} et utilise l'outil publish_top_aaps_tool.
    Cet outil va filtrer les projets non éligibles et envoyer le Top 5 vers Google Sheets.
    Rends compte du succès ou de l'échec de cette opération finale.
    """,
    tools=[publish_top_aaps_tool],
    output_key="session:publication_report",
)

# Agent spécialisé dans l'analyse de pertinence stratégique (Scoring)
aap_scoring_specialist = LlmAgent(
    name="AAPScoringSpecialist",
    model=config.MODEL_GEMINI_FLASH,
    instruction="""
    Analyse le règlement brut extrait de l'AAP et produis une notation objective (strategic_fit_score).
    Mission : Émancipation QPV via alpinisme et mentorat (AXA, Servier).
    """,
    generate_content_config=types.GenerateContentConfig(temperature=0.0, top_p=0.80),
    output_schema=AAPStrategicScore,
    output_key="temp:current_aap_score",
)

# --- 2. LOGIQUE DE PIPELINE & ORCHESTRATION (ex pipeline.py) ---

# Pipeline séquentiel : chaque agent passe son résultat au suivant
discovery_pipeline = SequentialAgent(
    name="DiscoveryPipeline",
    sub_agents=[query_expansion_agent, web_radar_agent, aap_extraction_agent, aap_publisher_agent],
)

def apply_deterministic_nogo_filter(aaps: List[AAPRawMetadata]) -> List[AAPRawMetadata]:
    """
    Applique les règles métier strictes pour écarter les projets non viables.
    
    Args:
        aaps: Liste d'AAPs bruts.
    Returns:
        Liste filtrée des AAPs éligibles selon les constantes du fichier config.py.
    """
    eligible_aaps: List[AAPRawMetadata] = []
    for aap in aaps:
        if aap.extracted_grant_ceiling is not None and aap.extracted_grant_ceiling < config.MIN_GRANT_REQUEST_EURO:
            continue
        if aap.required_annual_budget_ceiling is not None and aap.required_annual_budget_ceiling > config.MAX_ASSOCIATION_BUDGET_EURO:
            continue
        eligible_aaps.append(aap)
    return eligible_aaps

class PipelineOrchestrator:
    """
    Orchestrateur haut niveau gérant les sessions utilisateur et les phases du workflow.
    """
    def __init__(self, session_service=None) -> None:
        # On passe le session_service pour utiliser la persistance Firestore
        self.session_service = session_service
        self.app_name = "gravir_pour_grandir_aap"

    async def _get_state(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Récupère l'état de la session depuis le stockage persistant."""
        if not self.session_service:
            return {"session:approved_aap_ids": [], "temp:screened_aaps": []}
        session = await self.session_service.get_session(self.app_name, user_id, session_id)
        return session.state if session else {}

    async def _save_state(self, user_id: str, session_id: str, state: Dict[str, Any]):
        """Sauvegarde les modifications de l'état de session."""
        if self.session_service:
            session = await self.session_service.get_session(self.app_name, user_id, session_id)
            if session:
                session.state.update(state)
                await self.session_service.update_session(session)

    async def run_phase_1_discovery_and_screening(self, user_id: str, session_id: str, raw_aaps: List[AAPRawMetadata]) -> List[AAPRawMetadata]:
        """Filtre les opportunités et synchronise le Top 5 vers Google Sheets."""
        filtered_aaps = apply_deterministic_nogo_filter(raw_aaps)
        # Tri déterministe par plafond de subvention pour extraire le Top 5
        top_aaps = sorted(filtered_aaps, key=lambda x: x.extracted_grant_ceiling or 0, reverse=True)[:5]
        
        # Sauvegarde persistante dans Firestore via ADK
        await self._save_state(user_id, session_id, {"temp:screened_aaps": [aap.model_dump() for aap in top_aaps]})

        # Publication vers Google Sheets (Point final de la Phase 1)
        from sheets_publisher import publish_aaps_to_sheet

        # Résolution de l'ID Spreadsheet via Env, Config ou Secret Manager
        spreadsheet_id = os.getenv("SPREADSHEET_ID") or os.getenv("GOOGLE_SHEETS_ID")
        if not spreadsheet_id:
            spreadsheet_id = getattr(config, "SPREADSHEET_ID", None) or getattr(config, "GOOGLE_SHEETS_ID", None)
        if not spreadsheet_id:
            try:
                spreadsheet_id = get_secret("SPREADSHEET_ID")
            except Exception:
                try:
                    spreadsheet_id = get_secret("GOOGLE_SHEETS_ID")
                except Exception:
                    spreadsheet_id = None

        if spreadsheet_id and top_aaps:
            publish_aaps_to_sheet(spreadsheet_id, top_aaps)

        return top_aaps

    async def execute_hitl_checkpoint_1(self, user_id: str, session_id: str, approved_aap_id: str) -> bool:
        state = await self._get_state(user_id, session_id)
        screened_aaps = state.get("temp:screened_aaps", [])
        selected = [aap for aap in screened_aaps if aap['id'] == approved_aap_id]
        if not selected:
            return False
        
        approved_ids = state.get("session:approved_aap_ids", [])
        approved_ids.append(approved_aap_id)
        await self._save_state(user_id, session_id, {"session:approved_aap_ids": approved_ids, "session:active_context": selected[0]})
        return True

    async def run_phase_2_proposal_generation(self, user_id: str, session_id: str, aap_id: str, requested_grant: float) -> Dict[str, Any]:
        state = await self._get_state(user_id, session_id)
        if aap_id not in state.get("session:approved_aap_ids", []):
            raise PermissionError("Validation HITL #1 absente.")
        
        financial_plan = calculate_itemized_budget(
            total_grant_requested=requested_grant,
            cohort_size=getattr(config, "DEFAULT_COHORT_SIZE", 10),
        )

        # Récupération de l'AAP validé par l'opérateur
        active_aap_data = state.get("session:active_context")
        active_aap = AAPRawMetadata(**active_aap_data) if active_aap_data else None

        # Préparation du plan financier pour le document final
        fin_plan = FinancialApplicationPlan(
            aap_id=aap_id,
            total_project_cost=Decimal(str(financial_plan['total_project_cost'])),
            total_grant_requested=Decimal(str(financial_plan['total_grant_requested'])),
            total_self_financing=Decimal(str(financial_plan['total_self_financing'])),
            budget_breakdown=[ExpenseLineItem(**item) for item in financial_plan['budget_breakdown']]
        )

        # Construction de l'objet de proposition (Phase 2)
        proposal = FullProposalDocument(
            aap_id=aap_id,
            project_title=active_aap.title if active_aap else f"Projet {aap_id}",
            executive_pitch=f"Proposition de financement pour {active_aap.funder_name if active_aap else aap_id}.",
            narrative_sections=[
                NarrativeResponseItem(
                    field_id="presentation",
                    question_label="1. Présentation synthétique du projet",
                    final_text="Dossier en attente de rédaction narrative approfondie par l'agent Gemini Pro.",
                    character_count=85
                )
            ],
            financial_plan=fin_plan
        )

        # Assemblage du document Google Docs réel via l'API Docs v1
        try:
            from docs_assembler import GoogleDocsAssembler
            assembler = GoogleDocsAssembler()
            doc_url = assembler.assemble(proposal)
        except Exception as e:
            logger.error(f"Échec de l'assemblage Google Docs : {e}")
            doc_url = "https://docs.google.com/document/create"

        return {"status": "completed", "doc_url": doc_url, "financial_plan": financial_plan}

# Variable racine requise par le CLI ADK (adk web / adk run / adk deploy)
root_agent = discovery_pipeline
