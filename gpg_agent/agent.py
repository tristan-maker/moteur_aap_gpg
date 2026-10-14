"""
Orchestrateur Principal ADK — Pipeline séquentiel en 3 étapes (Radar 360 -> Routeur Pydantic -> Packager Déterministe).
"""
import os
import json
import time
from datetime import date, timedelta
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search, FunctionTool
from google.genai import types

from .config import build_wide_net_discovery_queries
from .schemas import SemanticRoutingDecision
from .compliance_enforcer import assemble_deterministic_dossier
from .crm_tracker import get_already_processed_aaps

FLASH_MODEL_NAME = os.environ.get("FLASH_MODEL_ID", "gemini-2.5-flash")

RESILIENT_GEMINI = Gemini(
    model=FLASH_MODEL_NAME,
    retry_options=types.HttpRetryOptions(
        attempts=6,
        initial_delay=10.0,
        max_delay=60.0,
        exp_base=2.0,
        http_status_codes=[429, 500, 502, 503, 504]
    )
)

TODAY_ISO = date.today().isoformat()
MIN_VALID_DEADLINE_ISO = (date.today() + timedelta(days=7)).isoformat()

def preload_crm_and_wide_net_queries(callback_context: CallbackContext) -> None:
    """
    Exécuté 100% en Python pur avant le Radar :
    1. Lit le Google Sheets CRM pour bloquer les doublons.
    2. Génère les 3 axes de recherche Grand Angle 360° (Découverte ouverte sur toute la France + Subventions publiques IDF/AURA + Rotation Mécènes).
    """
    crm_data = get_already_processed_aaps()
    processed_funders = crm_data.get("processed_funders", [])
    wide_queries = build_wide_net_discovery_queries(processed_funders)

    already_done = {
        "identifiants_deja_traites_interdits": crm_data.get("processed_ids", []),
        "financeurs_deja_traites_interdits": processed_funders,
        "urls_deja_traitees_interdites": crm_data.get("processed_urls", [])
    }
    callback_context.state["temp:crm_memory_state"] = json.dumps(already_done, ensure_ascii=False)
    callback_context.state["temp:wide_net_queries"] = json.dumps(wide_queries, ensure_ascii=False)
    return None

def pace_between_agents(callback_context: CallbackContext) -> None:
    time.sleep(3)
    return None

# --- SOUS-AGENT 1 : RADAR WEB GRAND ANGLE 360° ---
web_radar_agent = LlmAgent(
    name="GlobalWebRadarAgent",
    model=RESILIENT_GEMINI,
    before_agent_callback=preload_crm_and_wide_net_queries,
    instruction=f"""
    Tu es le Radar de Veille Financière 360° de l'association Gravir Pour Grandir (Loi 1901 d'intérêt général).
    NOTRE PUBLIC CIBLE : Jeunes de 16 à 25 ans issus des Quartiers Prioritaires de la Ville (QPV) ou en fragilité socio-économique, accompagnés par l'alpinisme, la voile et le mentorat vers l'emploi.
    DATE DU JOUR : {TODAY_ISO}.

    MÉMOIRE ANTI-DOUBLONS (DOSSIERS DÉJÀ CRÉÉS DANS LE GOOGLE SHEETS CRM À IGNORER OBLIGATOIREMENT) :
    {{temp:crm_memory_state}}

    AXES DE RECHERCHE GRAND ANGLE DU JOUR (NE TE LIMITE JAMAIS AUX SEULES FONDATIONS CONNUES, RATISSE TOUT LE WEB FRANÇAIS) :
    {{temp:wide_net_queries}}

    Exécute 2 ou 3 appels `google_search` en utilisant prioritairement :
    1. `1_requete_grand_angle_decouverte_ouverte` (pour dénicher de nouveaux fonds de dotation, fondations familiales ou appels à projets nationaux méconnus).
    2. `2_requete_territoriale_et_publique_idf_aura` ou `3_requete_rotation_grands_mecenes`.

    Pour chaque opportunité trouvée (qu'il s'agisse d'un nouveau fonds inconnu, d'une subvention publique ou d'une grande fondation), applique ces 4 RÈGLES D'EXCLUSION STRICTES :
    1. DOUBLON CRM : Si le financeur figure déjà dans la mémoire CRM ci-dessus -> Marque [REJETÉE - DÉJÀ PRÉSENT DANS LE CRM GOOGLE SHEETS].
    2. DATE : Si la date de clôture est antérieure au {MIN_VALID_DEADLINE_ISO} (ex: session close le 16 août 2026) -> Marque [REJETÉE - DATE DÉPASSÉE OU < 7 JOURS].
    3. PUBLIC CIBLE : Si réservé EXCLUSIVEMENT à l'ASE -> Marque [REJETÉE - PUBLIC ASE EXCLUSIF].
    4. STATUT : Si exige un consortium CROS/CDOS ou collectivité -> Marque [REJETÉE - STATUT INCOMPATIBLE].
    5. Sinon -> Marque [RETENUE - NOUVELLE OPPORTUNITÉ ÉLIGIBLE QPV] avec l'URL officielle exacte (https://...) et sa vraie date limite YYYY-MM-DD.
    """,
    generate_content_config=types.GenerateContentConfig(temperature=0.2),
    tools=[google_search],
    output_key="temp:raw_radar_results"
)

# --- SOUS-AGENT 2 : AIGUILLEUR SÉMANTIQUE ---
semantic_router_agent = LlmAgent(
    name="SemanticRouterAgent",
    model=RESILIENT_GEMINI,
    before_agent_callback=pace_between_agents,
    instruction=f"""
    Tu es l'Aiguilleur Stratégique de Gravir Pour Grandir. Date du jour : {TODAY_ISO}.
    Lis la mémoire CRM dans {{temp:crm_memory_state}} et les résultats de veille dans {{temp:raw_radar_results}}.
    Sélectionne la meilleure opportunité marquée [RETENUE - NOUVELLE OPPORTUNITÉ ÉLIGIBLE QPV] (qu'elle provienne de la découverte Grand Angle ouverte, d'un guichet public territorial ou d'une fondation privée) qui NE figure PAS dans le CRM :
    - `deadline_iso` doit être la date réelle de clôture (>= {MIN_VALID_DEADLINE_ISO}) au format YYYY-MM-DD.
    - `requested_grant_euro` doit être un entier (ex: 15000 par défaut).
    - Si AUCUNE opportunité n'est éligible, mets `go_recommendation=False` et `deadline_iso="EXPIRED"`.
    """,
    generate_content_config=types.GenerateContentConfig(temperature=0.0),
    output_schema=SemanticRoutingDecision,
    output_key="temp:routing_decision"
)

dossier_assembly_tool = FunctionTool(assemble_deterministic_dossier)

# --- SOUS-AGENT 3 : RÉDACTEUR & PACKAGER DRIVE + CRM + KIT PARRAINAGE ---
mirror_drafter_agent = LlmAgent(
    name="TailoredMirrorDrafter",
    model=RESILIENT_GEMINI,
    before_agent_callback=pace_between_agents,
    instruction=f"""
    Tu es le Directeur des Partenariats de Gravir Pour Grandir.
    Lis la décision dans {{temp:routing_decision}} et appelle OBLIGATOIREMENT `assemble_deterministic_dossier`.
    - Si `assemble_deterministic_dossier` renvoie `BLOCKED_BY_COMPLIANCE_ENFORCER`, affiche le motif exact (`exclusion_reason`) et confirme qu'aucun dossier Drive inutile n'a été créé.
    - Si `assemble_deterministic_dossier` renvoie `APPROVED_AND_GENERATED`, affiche :
      1. 🚀 Le GUICHET DIRECT DE DÉPÔT (`guichet_depot_direct_url`)
      2. 📖 La PAGE D'INFORMATION DE L'AAP (`page_info_aap_url`)
      3. 📅 La DATE LIMITE VÉRIFIÉE (`date_limite_depot`) et le nombre de jours restants
      4. 🤝 Le KIT PARRAINAGE SALARIÉ & LINKEDIN (`sponsorship_kit`)
      5. 📊 La CONFIRMATION D'AJOUT AU CRM GOOGLE SHEETS (`crm_tracking`)
      6. 📁 Les liens vers le Dossier Google Drive, le Google Docs et le Google Sheets.
    """,
    generate_content_config=types.GenerateContentConfig(temperature=0.2),
    tools=[dossier_assembly_tool],
    output_key="temp:final_assembled_dossier"
)

root_agent = SequentialAgent(
    name="GPGFullVeilleAndDossierPipeline",
    sub_agents=[
        web_radar_agent,
        semantic_router_agent,
        mirror_drafter_agent
    ]
)
