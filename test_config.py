from decimal import Decimal
import config


def test_config_constants():
    assert config.MIN_GRANT_REQUEST_EURO == Decimal("2000.00")
    assert config.MAX_ASSOCIATION_BUDGET_EURO == Decimal("400000.00")
    assert config.MODEL_GEMINI_FLASH == "gemini-2.5-flash"
    assert config.MODEL_GEMINI_PRO == "gemini-3.8-pro"
    print("✔ Test Constantes Métiers et Modèles : Réussi")


def test_safety_settings_structure():
    assert "HARM_CATEGORY_HATE_SPEECH" in config.PROD_SAFETY_SETTINGS
    assert config.PROD_SAFETY_SETTINGS["HARM_CATEGORY_HATE_SPEECH"] == "BLOCK_LOW_AND_ABOVE"
    assert config.PROD_SAFETY_SETTINGS["HARM_CATEGORY_DANGEROUS_CONTENT"] == "BLOCK_MEDIUM_AND_ABOVE"
    print("✔ Test Matrice de Sécurité PROD_SAFETY_SETTINGS : Réussi")


def test_env_validation():
    result = config.validate_environment()
    assert result is True
    print("✔ Test Validation Environnement : Réussi")


if __name__ == "__main__":
    print("=== Exécution des tests unitaires locaux pour config.py ===")
    test_config_constants()
    test_safety_settings_structure()
    test_env_validation()
    print("✅ Validation complète du module config.py effectuée avec succès !")
