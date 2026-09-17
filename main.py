import logging
import sys
from decimal import Decimal

import config
from schemas import AAPRawMetadata
from mcp_harvester import mock_harvest_aap_content
from pipeline import PipelineOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
)
logger = logging.getLogger("GravirPourGrandir.Main")


def run_e2e_pipeline_demo():
    logger.info("DÉMARRAGE DU MOTEUR UNIVERSEL AAP — GRAVIR POUR GRANDIR")

    config.validate_environment()

    logger.info("Étape 1 : Simulation de la collecte d'opportunités (MCP / DocAI)")
    mock_url = "https://fondation-partenaire.org/aap-2026-inclusion-montagne"
    harvested_payload = mock_harvest_aap_content(mock_url)

    sample_aaps = [
        AAPRawMetadata(
            id="aap_2026_qpv_montagne_01",
            source_url=mock_url,
            title="Appel à Projets 2026 — Jeunesse, Montagne et Égalité des Chances",
            funder_name="Fondation Altitude & Inclusion",
            extracted_grant_ceiling=Decimal("12000.00"),
            required_annual_budget_ceiling=Decimal("350000.00"),
            submission_deadline="2026-11-15",
            geographic_scope="National / QPV",
            raw_guidelines_text=harvested_payload["extracted_text"],
        ),
        AAPRawMetadata(
            id="aap_2026_rejected_small_grant",
            source_url="https://commune-exemple.fr/micro-don",
            title="Aide Équipement Club Sportif",
            funder_name="Ville Exemple",
            extracted_grant_ceiling=Decimal("500.00"),
            required_annual_budget_ceiling=Decimal("20000.00"),
            submission_deadline="2026-09-30",
            geographic_scope="Local",
            raw_guidelines_text="Micro-subvention locale...",
        ),
    ]

    orchestrator = PipelineOrchestrator()

    logger.info("Étape 2 : Exécution de la Phase 1 (Filtering & Screening)")
    screened_aaps = orchestrator.run_phase_1_discovery_and_screening(sample_aaps)

    if not screened_aaps:
        logger.warning("Aucun AAP n'a franchi le filtrage d'éligibilité. Fin du processus.")
        sys.exit(0)

    target_aap = screened_aaps[0]
    logger.info(f"AAP retenu pour arbitrage HITL #1 : {target_aap.title} (ID: {target_aap.id})")

    logger.info("BARRIÈRE HITL #1 : Simulation du feu vert opérateur (Bascule case GO)")
    approval_success = orchestrator.execute_hitl_checkpoint_1(approved_aap_id=target_aap.id)

    if not approval_success:
        logger.error("Refus ou absence de validation HITL #1. Interruption du workflow.")
        sys.exit(1)

    logger.info("Étape 3 : Exécution de la Phase 2 après déblocage humain")
    requested_amount = 10000.0
    final_output = orchestrator.run_phase_2_proposal_generation(
        aap_id=target_aap.id, requested_grant=requested_amount
    )

    print("\n" + "=" * 80)
    print("RAPPORT DE LIVRAISON DE COMPILATION D'APPEL À PROJETS")
    print("=" * 80)
    print(f" • Identifiant AAP      : {target_aap.id}")
    print(f" • Intitulé Programme   : {target_aap.title}")
    print(f" • Financeur            : {target_aap.funder_name}")
    print(f" • Statut Workflow      : {final_output['status'].upper()}")
    print(f" • URL Document G-Docs  : {final_output['doc_url']}")
    print(f" • Budget Total Projet  : {final_output['financial_plan']['total_project_cost']} €")
    print(f" • Subvention Demandée  : {final_output['financial_plan']['total_grant_requested']} €")
    print(f" • Autofinancement Asso : {final_output['financial_plan']['total_self_financing']} €")
    print("=" * 80)
    print("POINT D'ARRÊT HITL #2 ATTEINT : Transmis à l'équipe opérationnelle pour relecture et dépôt manuel.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_e2e_pipeline_demo()
