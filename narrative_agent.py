from google.adk.agents import LlmAgent
from google.adk.planners import BuiltInPlanner
from google.genai import types
from budget_engine import budget_calculation_tool
from schemas import FullProposalDocument

strategic_narrative_drafter = LlmAgent(
    name="StrategicNarrativeDrafter",
    model="gemini-3.8-pro",
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=False,
            thinking_budget=2048,
        )
    ),
    instruction="""
Tu es le Directeur du Développement de l'association Gravir Pour Grandir.
Rédige un dossier de candidature complet, convaincant et ultra-ciblé pour l'Appel à Projets actif dans {session:active_context}.

Règles de rédaction stratégique :
1. Aligne le discours selon l'axe narratif dominant retenu dans {temp:current_aap_score} :
   - 'QPV_Inclusion' : focus sur les jeunes issus des quartiers prioritaires (suivis par Proxité / E2C93), la mixité sociale et le bris du déterminisme social.
   - 'Sport_Montagne_Depassement' : pédagogie de l'effort, cordée solidaire, haute altitude et séjours de rupture éducative.
   - 'Insertion_Mentorat' : transmission durable sur 12 mois avec les cadres de grands groupes partenaires (AXA Atout Cœur, Servier).
2. Respecte scrupuleusement la contrainte character_limit pour chaque champ de question présent dans {temp:target_form_schema}.
3. Appelle obligatoirement l'outil calculate_itemized_budget pour sceller les montants financiers et la ventilation au centime.
4. Réponds strictement selon le schéma JSON FullProposalDocument.
""",
    tools=[budget_calculation_tool],
    output_schema=FullProposalDocument,
    output_key="temp:application_proposal_draft",
)
