from decimal import Decimal
from schemas import AAPRawMetadata, SearchQueryMatrix, SearchDork


def test_aap_raw_metadata_decimal_conversion():
    payload = {
        "id": "a" * 64,
        "source_url": "https://exemple.fr/aap-2026",
        "title": "Appel à projets Inclusion Sportive 2026",
        "funder_name": "Fondation Exemple",
        "extracted_grant_ceiling": "15000.50",
        "required_annual_budget_ceiling": 300000,
        "submission_deadline": "2026-06-30",
        "geographic_scope": "National",
        "raw_guidelines_text": "Règlement officiel...",
    }

    metadata = AAPRawMetadata(**payload)
    assert isinstance(metadata.extracted_grant_ceiling, Decimal)
    assert metadata.extracted_grant_ceiling == Decimal("15000.50")
    assert isinstance(metadata.required_annual_budget_ceiling, Decimal)
    assert metadata.required_annual_budget_ceiling == Decimal("300000")
    print("✔ Test AAPRawMetadata : Réussi")


def test_search_query_matrix_validity():
    matrix = SearchQueryMatrix(
        generated_dorks=[
            SearchDork(
                query_string='"appel à projets" "QPV" "montagne" 2026',
                strategic_rationale="Inclusion par le sport en banlieue",
                priority_level="HAUTE",
            )
        ]
    )
    assert len(matrix.generated_dorks) == 1
    assert matrix.execution_horizon_year == 2026
    print("✔ Test SearchQueryMatrix : Réussi")


if __name__ == "__main__":
    print("=== Exécution des tests unitaires locaux pour schemas.py ===")
    test_aap_raw_metadata_decimal_conversion()
    test_search_query_matrix_validity()
    print("✅ Validation complète du module schemas.py effectuée avec succès !")
