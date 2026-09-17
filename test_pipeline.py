from decimal import Decimal
from schemas import AAPRawMetadata
from pipeline import PipelineOrchestrator, apply_deterministic_nogo_filter


def create_sample_aaps():
    return [
        AAPRawMetadata(
            id="aap_001_valid",
            source_url="https://fondation-sport.fr/aap-2026",
            title="Appel à Projets Sport et Inclusion QPV",
            funder_name="Fondation Sport & Jeunesse",
            extracted_grant_ceiling=Decimal("15000.00"),
            required_annual_budget_ceiling=Decimal("300000.00"),
            submission_deadline="2026-11-30",
            geographic_scope="National",
            raw_guidelines_text="Règlement officiel...",
        ),
        AAPRawMetadata(
            id="aap_002_nogo_grant_too_low",
            source_url="https://commune-locale.fr/micro-subvention",
            title="Micro Subvention Équipement",
            funder_name="Mairie Locale",
            extracted_grant_ceiling=Decimal("500.00"),  # < 2000 € (No-Go)
            required_annual_budget_ceiling=Decimal("50000.00"),
            submission_deadline="2026-08-15",
            geographic_scope="Communal",
            raw_guidelines_text="Règlement micro-subvention...",
        ),
        AAPRawMetadata(
            id="aap_003_nogo_budget_too_high",
            source_url="https://grand-groupe.fr/fondation",
            title="Mécénat Grand Groupe Projets Nationaux",
            funder_name="Fondation Grand Groupe",
            extracted_grant_ceiling=Decimal("20000.00"),
            required_annual_budget_ceiling=Decimal("1000000.00"),  # > 400 000 € (No-Go)
            submission_deadline="2026-12-01",
            geographic_scope="National",
            raw_guidelines_text="Règlement grands acteurs...",
        ),
    ]


def test_nogo_filter():
    raw_aaps = create_sample_aaps()
    filtered = apply_deterministic_nogo_filter(raw_aaps)
    assert len(filtered) == 1
    assert filtered[0].id == "aap_001_valid"
    print("✔ Test Filtre Déterministe No-Go : Réussi")


def test_pipeline_hitl_workflow():
    orchestrator = PipelineOrchestrator()
    raw_aaps = create_sample_aaps()

    # 1. Phase 1 Execution
    screened = orchestrator.run_phase_1_discovery_and_screening(raw_aaps)
    assert len(screened) == 1

    # 2. Tentative d'exécution Phase 2 Sans HITL #1 -> Doit lever PermissionError
    permission_error_raised = False
    try:
        orchestrator.run_phase_2_proposal_generation(
            aap_id="aap_001_valid", requested_grant=10000.0
        )
    except PermissionError:
        permission_error_raised = True

    assert permission_error_raised, "Erreur : La Phase 2 aurait dû être bloquée sans validation HITL #1 !"
    print("✔ Test Blocage Phase 2 sans validation HITL #1 : Réussi")

    # 3. Validation HITL #1 (Simulation case GO)
    hitl_ok = orchestrator.execute_hitl_checkpoint_1(approved_aap_id="aap_001_valid")
    assert hitl_ok is True

    # 4. Exécution Phase 2 Après HITL #1
    result = orchestrator.run_phase_2_proposal_generation(
        aap_id="aap_001_valid", requested_grant=10000.0
    )
    assert result["status"] == "completed"
    assert "https://docs.google.com/document/d/" in result["doc_url"]
    assert result["financial_plan"]["total_grant_requested"] == 10000.0
    print("✔ Test Exécution complète Phase 2 & Barrière HITL #2 : Réussi")


if __name__ == "__main__":
    print("=== Exécution des tests unitaires locaux pour pipeline.py ===")
    test_nogo_filter()
    test_pipeline_hitl_workflow()
    print("✅ Validation complète du module pipeline.py effectuée avec succès !")
