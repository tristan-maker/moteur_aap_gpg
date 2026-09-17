import config
from schemas import SearchQueryMatrix, AAPStrategicScore
from agents import query_expansion_agent, web_radar_agent, aap_scoring_specialist


def test_agent_instantiations():
    assert query_expansion_agent.name == "QueryExpansionSpecialist"
    assert query_expansion_agent.model == config.MODEL_GEMINI_FLASH
    assert query_expansion_agent.output_key == "temp:generated_queries"
    assert query_expansion_agent.output_schema == SearchQueryMatrix
    print("✔ Validation QueryExpansionSpecialist : Réussi")

    assert web_radar_agent.name == "GlobalWebRadarAgent"
    assert web_radar_agent.model == config.MODEL_GEMINI_FLASH
    assert web_radar_agent.output_key == "temp:discovered_urls_text"
    assert web_radar_agent.output_schema is None
    assert len(web_radar_agent.tools) == 1
    print("✔ Validation GlobalWebRadarAgent : Réussi")

    assert aap_scoring_specialist.name == "AAPScoringSpecialist"
    assert aap_scoring_specialist.model == config.MODEL_GEMINI_FLASH
    assert aap_scoring_specialist.output_key == "temp:current_aap_score"
    assert aap_scoring_specialist.output_schema == AAPStrategicScore
    print("✔ Validation AAPScoringSpecialist : Réussi")


if __name__ == "__main__":
    print("=== Exécution des tests unitaires locaux pour agents.py ===")
    test_agent_instantiations()
    print("✅ Validation complète du module agents.py effectuée avec succès !")
