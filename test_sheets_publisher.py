from decimal import Decimal
from schemas import AAPRawMetadata
from sheets_publisher import format_aap_row_payload, publish_aaps_to_sheet


def create_sample_aap() -> AAPRawMetadata:
    return AAPRawMetadata(
        id="aap_sheets_test_01",
        source_url="https://fondation-sport.org/aap-2026",
        title="Appel à Projets Montagne 2026",
        funder_name="Fondation Sport",
        extracted_grant_ceiling=Decimal("12000.00"),
        required_annual_budget_ceiling=Decimal("300000.00"),
        submission_deadline="2026-10-15",
        geographic_scope="National",
        raw_guidelines_text="Règlement officiel...",
    )


def test_format_aap_row_payload():
    aap = create_sample_aap()
    row = format_aap_row_payload(aap)
    assert len(row) == 8
    assert row[0] == "aap_sheets_test_01"
    assert row[3] == 12000.0
    assert row[7] == "NON"
    print("✔ Test Formatage Ligne Google Sheets : Réussi")


def test_publish_aaps_to_sheet_mock():
    aap = create_sample_aap()
    result = publish_aaps_to_sheet("spreadsheet_mock_123", [aap])
    assert result["status"] == "success"
    assert result["updated_rows"] == 1
    assert result["mode"] == "mock"
    print("✔ Test Synchronisation Tableur (Mode Mock) : Réussi")


if __name__ == "__main__":
    print("=== Exécution des tests unitaires locaux pour sheets_publisher.py ===")
    test_format_aap_row_payload()
    test_publish_aaps_to_sheet_mock()
    print("✅ Validation complète du module sheets_publisher.py effectuée avec succès !")
