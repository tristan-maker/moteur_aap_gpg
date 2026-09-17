import sys
from decimal import Decimal
from ranking import rank_and_select_top_5
from schemas import AAPRawMetadata, AAPStrategicScore
from sheets_sync import GoogleSheetsSyncManager


def test_ranking_and_hitl_flow():
    # 1. Création de 2 candidats mockés
    meta1 = AAPRawMetadata(
        id="hash_1",
        source_url="https://example.org/1",
        title="Appel Montagne et Jeunesse 2026",
        funder_name="Fondation Petzl",
        extracted_grant_ceiling=Decimal("20000.00"),
        submission_deadline="2026-11-30",
        geographic_scope="National",
        raw_guidelines_text="Règlement 1...",
    )
    score1 = AAPStrategicScore(
        aap_id="hash_1",
        strategic_fit_score=0.90,
        primary_axis="Sport_Montagne_Depassement",
        alignment_reasoning="Excellente adéquation.",
        recommended_for_selection=True,
    )

    meta2 = AAPRawMetadata(
        id="hash_2",
        source_url="https://example.org/2",
        title="Subvention Micro-Projet",
        funder_name="Mairie",
        extracted_grant_ceiling=Decimal("2000.00"),
        submission_deadline="2026-12-15",
        geographic_scope="Local",
        raw_guidelines_text="Règlement 2...",
    )
    score2 = AAPStrategicScore(
        aap_id="hash_2",
        strategic_fit_score=0.60,
        primary_axis="QPV_Inclusion",
        alignment_reasoning="Adéquation moyenne.",
        recommended_for_selection=False,
    )

    # 2. Tri déterministe
    top5 = rank_and_select_top_5([(meta1, score1), (meta2, score2)])
    assert len(top5) == 2
    assert top5[0][0].id == "hash_1"  # Doit être classé premier
    assert top5[0][2] > top5[1][2]  # Score composite supérieur

    # 3. Publication Sheets & Barrière HITL
    sheets_manager = GoogleSheetsSyncManager()
    row_ids = sheets_manager.publish_top_5_opportunities(top5)
    assert row_ids["hash_1"] == 2

    # Vérification que le statut HITL est bloqué au départ (NON)
    assert sheets_manager.check_hitl_approval("hash_1") is False

    # Simulation de la validation par l'opérateur humain (Case GO cochée)
    sheets_manager.simulate_human_operator_approval("hash_1")
    assert sheets_manager.check_hitl_approval("hash_1") is True

    print("✅ TEST RANKING & SYNCHRONISATION SHEETS HITL #1 RÉUSSI.")


if __name__ == "__main__":
    try:
        test_ranking_and_hitl_flow()
    except Exception as e:
        print(f"❌ ÉCHEC DU TEST : {e}")
        sys.exit(1)
