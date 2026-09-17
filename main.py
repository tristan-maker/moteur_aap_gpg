import os
from google.adk.agents import LlmAgent, SequentialAgent
from budget_engine import budget_calculation_tool
from narrative_agent import strategic_narrative_drafter
from query_expansion_agent import query_expansion_agent
from schemas import AAPStrategicScore, FullProposalDocument
from web_radar_agent import web_radar_agent

aap_scoring_specialist = LlmAgent(
    name="AAPScoringSpecialist",
    model="gemini-2.5-flash",
    instruction="""
Tu es l'Analyste Stratégique Senior de l'association Gravir Pour Grandir.
Analyse les opportunités d'appels à projets présentes dans {temp:discovered_urls}.

Consignes :
1. Évalue la pertinence thématique et calcule strategic_fit_score entre 0.0 et 1.0.
2. Détermine l'axe narratif dominant ('QPV_Inclusion', 'Sport_Montagne_Depassement', 'Insertion_Mentorat').
3. Justifie ton analyse en 3 phrases maximum.
4. Réponds strictement selon le schéma JSON AAPStrategicScore.
""",
    output_schema=AAPStrategicScore,
    output_key="temp:current_aap_score",
)

discovery_pipeline = SequentialAgent(
    name="DiscoveryAndScreeningPipeline",
    sub_agents=[
        query_expansion_agent,
        web_radar_agent,
        aap_scoring_specialist,
    ],
)

root_agent = SequentialAgent(
    name="UniversalAAPEngine",
    sub_agents=[
        discovery_pipeline,
        strategic_narrative_drafter,
    ],
)
