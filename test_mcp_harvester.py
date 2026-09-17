from mcp_harvester import (
    initialize_h_company_mcp_toolset,
    harvest_aap_content,
    mock_harvest_aap_content,
)
from schemas import AAPRawMetadata


def test_mock_harvest_aap_content():
    url = "https://exemple.fr/aap-2026-jeunesse"
    metadata = mock_harvest_aap_content(url)
    assert isinstance(metadata, AAPRawMetadata)
    assert metadata.source_url == url
    assert metadata.extracted_grant_ceiling == 15000.00
    assert "Jeunesse, Montagne" in metadata.title
    print("✔ Test Ingestion MCP (Mock) : Réussi")


def test_initialize_mcp_toolset_without_key():
    toolset = initialize_h_company_mcp_toolset()
    assert toolset is None
    print("✔ Test Initialisation MCP sans clé H_COMPANY_API_KEY : Réussi")


def test_harvest_aap_content_fallback():
    url = "https://exemple.fr/aap-fallback"
    metadata = harvest_aap_content(url, mcp_toolset=None)
    assert isinstance(metadata, AAPRawMetadata)
    assert metadata.source_url == url
    print("✔ Test Harvest AAP Content Fallback : Réussi")


if __name__ == "__main__":
    print("=== Exécution des tests unitaires locaux pour mcp_harvester.py ===")
    test_mock_harvest_aap_content()
    test_initialize_mcp_toolset_without_key()
    test_harvest_aap_content_fallback()
    print("✅ Validation complète du module mcp_harvester.py effectuée avec succès !")
