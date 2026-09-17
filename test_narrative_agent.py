import config
from schemas import FullProposalDocument
from narrative_agent import strategic_narrative_drafter


def test_narrative_agent_configuration():
    # 1. Vérification des identifiants et du modèle
    assert strategic_narrative_drafter.name == "StrategicNarrativeDrafter"
    assert strategic_narrative_drafter.model == config.MODEL_GEMINI_PRO

    # 2. Vérification de la présence du planner et de la configuration de pensée
    assert strategic_narrative_drafter.planner is not None
    thinking_config = strategic_narrative_drafter.planner.thinking_config
    assert thinking_config.thinking_budget == 2048
    assert thinking_config.include_thoughts is False

    # 3. Vérification des outils et schémas
    assert len(strategic_narrative_drafter.tools) == 1
    assert strategic_narrative_drafter.output_schema == FullProposalDocument
    assert strategic_narrative_drafter.output_key == "temp:application_proposal_draft"
    print("✔ Validation StrategicNarrativeDrafter : Réussi")


if __name__ == "__main__":
    print("=== Exécution des tests unitaires locaux pour narrative_agent.py ===")
    test_narrative_agent_configuration()
    print("✅ Validation complète du module narrative_agent.py effectuée avec succès !")
