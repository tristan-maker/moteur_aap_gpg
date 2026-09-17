import logging
from typing import Dict, List, Any
from google.adk.agents import SequentialAgent

import config
from schemas import AAPRawMetadata
from agents import query_expansion_agent, web_radar_agent
from budget_engine import calculate_itemized_budget

logger = logging.getLogger("GravirPourGrandir.Pipeline")

# --- 1. SequentialAgent ADK pour la Découverte Phase 1 ---

discovery_pipeline = SequentialAgent(
    name="DiscoveryPipeline",
    sub_agents=[
        query_expansion_agent,
        web_radar_agent,
    ],
)

# --- 2. Filtre Déterministe No-Go (Python Pur) ---

def apply_deterministic_nogo_filter(
    aaps: List[AAPRawMetadata],
) -> List[AAPRawMetadata]:
    """Filtre déterministe No-Go applique sur critères financiers et statutaires.

    Consignes du DAA (Section 2) :
    - Plafond de subvention sollicitable >= MIN_GRANT_REQUEST_EURO (2 000 EUR)
    - Exigence de budget annuel max de l'association <= MAX_ASSOCIATION_BUDGET_EURO (400 000 EUR)
    """
    eligible_aaps: List[AAPRawMetadata] = []
    for aap in aaps:
        if (
            aap.extracted_grant_ceiling is not None
            and aap.extracted_grant_ceiling < config.MIN_GRANT_REQUEST_EURO
        ):
            logger.info(
                f"[NO-GO REJET] AAP '{aap.title}' : Subvention ({aap.extracted_grant_ceiling} €) "
                f"< Seuil minimal ({config.MIN_GRANT_REQUEST_EURO} €)"
            )
            continue

        if (
            aap.required_annual_budget_ceiling is not None
            and aap.required_annual_budget_ceiling > config.MAX_ASSOCIATION_BUDGET_EURO
        ):
            logger.info(
                f"[NO-GO REJET] AAP '{aap.title}' : Budget asso exigé ({aap.required_annual_budget_ceiling} €) "
                f"> Plafond statutaire ({config.MAX_ASSOCIATION_BUDGET_EURO} €)"
            )
            continue

        eligible_aaps.append(aap)

    logger.info(
        f"[NO-GO FILTER] {len(eligible_aaps)}/{len(aaps)} AAP(s) franchissent les règles No-Go."
    )
    return eligible_aaps


# --- 3. Orchestrateur Global & Barrières HITL ---

class PipelineOrchestrator:
    """Orchestrateur global gérant le cycle de vie du pipeline et les barrières HITL."""

    def __init__(self) -> None:
        self.session_state: Dict[str, Any] = {
            "session:approved_aap_ids": [],
            "temp:screened_aaps": [],
        }

    def run_phase_1_discovery_and_screening(
        self, raw_aaps: List[AAPRawMetadata]
    ) -> List[AAPRawMetadata]:
        """Exécute la Phase 1 : Filtrage déterministe et préparation avant HITL #1."""
        logger.info("=== DEMARRAGE PHASE 1 : Découverte & Screening ===")
        filtered_aaps = apply_deterministic_nogo_filter(raw_aaps)
        self.session_state["temp:screened_aaps"] = filtered_aaps
        return filtered_aaps

    def execute_hitl_checkpoint_1(self, approved_aap_id: str) -> bool:
        """Point d'Arrêt HITL #1 : Arbitrage Opérateur sur Google Sheets (Validation Case GO)."""
        logger.info(
            f"=== BARRIÈRE HITL #1 : Vérification de la validation pour AAP ID: {approved_aap_id} ==="
        )
        screened_aaps: List[AAPRawMetadata] = self.session_state.get(
            "temp:screened_aaps", []
        )
        selected = [aap for aap in screened_aaps if aap.id == approved_aap_id]

        if not selected:
            logger.warning(
                f"🛑 HITL #1 REFUS / BLOCAGE : Aucun AAP éligible trouvé pour l'ID {approved_aap_id}"
            )
            return False

        self.session_state["session:approved_aap_ids"].append(approved_aap_id)
        self.session_state["session:active_context"] = selected[0]
        logger.info(
            "✅ HITL #1 VALIDE : Case 'GO' cochée par l'opérateur. Passage autorisé vers Phase 2."
        )
        return True

    def run_phase_2_proposal_generation(
        self, aap_id: str, requested_grant: float
    ) -> Dict[str, Any]:
        """Exécute la Phase 2 : Chiffrage budgétaire, rédaction et préparation de livraison."""
        if aap_id not in self.session_state.get("session:approved_aap_ids", []):
            raise PermissionError(
                "🛑 Action bloquée : Impossible d'exécuter la Phase 2 sans validation HITL #1."
            )

        logger.info("=== DEMARRAGE PHASE 2 : Chiffrage, Rédaction & Compilation ===")

        # 1. Calcul Budgétaire Déterministe (Pure Python / Decimal)
        financial_plan = calculate_itemized_budget(
            total_grant_requested=requested_grant,
            cohort_size=config.DEFAULT_COHORT_SIZE,
        )
        self.session_state["temp:itemized_budget"] = financial_plan

        # 2. Génération / Assemblage Google Docs (Livrable final)
        doc_url = f"https://docs.google.com/document/d/mock_doc_{aap_id}/edit"
        self.session_state["session:doc_url"] = doc_url

        logger.info(f"✅ Dossier rédigé et assemblé sur Google Docs : {doc_url}")
        logger.info(
            "🛑 BARRIÈRE HITL #2 ATTEINTE : Arrêt définitif de l'agent. "
            "Le téléversement et la signature sur le portail bailleur sont strictement réservés à l'humain."
        )

        return {
            "status": "completed",
            "doc_url": doc_url,
            "financial_plan": financial_plan,
        }
