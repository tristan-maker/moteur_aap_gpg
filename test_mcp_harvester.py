import os
from mcp_harvester import initialize_h_company_mcp_toolset, mock_harvest_aap_content


def test_mcp_initialization_missing_key():
    # S'assurer que la clé est absente pour tester la levée d'exception
    old_key = os.environ.pop("H_COMPANY_API_KEY", None)
    try:
        exception_raised = False
        try:
            initialize_h_company_mcp_toolset()
        except ValueError as e:
            exception_raised = True
            assert "CRITICAL: La clé H_COMPANY_API_KEY est absente" in str(e)
        
        assert exception_raised, "Erreur : L'exception ValueError n'a pas été levée !"
        print("✔ Test Levée d'erreur sur clé API absente : Réussi")
    finally:
        if old_key:
            os.environ["H_COMPANY_API_KEY"] = old_key


def test_mcp_initialization_with_key():
    os.environ["H_COMPANY_API_KEY"] = "mock-h-company-key-12345"
    toolset = initialize_h_company_mcp_toolset()
    assert toolset is not None
    print("✔ Test Instanciation McpToolset avec clé : Réussi")


def test_mock_harvest_aap_content():
    sample_url = "https://fondation-exemple.fr/aap-2026"
    result = mock_harvest_aap_content(sample_url)
    assert result["status"] == "success"
    assert result["url"] == sample_url
    assert "extracted_text" in result
    assert result["has_pdf_attachments"] is True
    print("✔ Test Extraction Mock Content MCP : Réussi")


if __name__ == "__main__":
    print("=== Exécution des tests unitaires locaux pour mcp_harvester.py ===")
    test_mcp_initialization_missing_key()
    test_mcp_initialization_with_key()
    test_mock_harvest_aap_content()
    print("✅ Validation complète du module mcp_harvester.py effectuée avec succès !")
