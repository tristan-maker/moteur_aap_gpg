from google.adk.agents import LlmAgent
from google.adk.planners import BuiltInPlanner
from google.genai import types

import config
from budget_engine import budget_calculation_tool
from schemas import FullProposalDocument

# --- Agent de Rédaction Narrative Stratégique (Gemini 3.8 Pro) ---

strategic_narrative_drafter = LlmAgent(
    name="StrategicNarrativeDrafter",
    model=config.MODEL_GEMINI_PRO,
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=False,
            thinking_budget=2048,
        )
    ),
    instruction="""
    Tu es le Directeur du Développement et de la Stratégie de l'association Gravir Pour Grandir.
    Ta mission est de rédiger l'intégralité du dossier de candidature pour l'Appel à Projets (AAP) sélectionné.

    Contextualisation & Lignes Directrices :
    1. Aligne scrupuleusement la rhétorique et le discours selon l'axe stratégique identifié dans l'état ({temp:current_aap_score}):
       - 'QPV_Inclusion' : Mets l'accent sur les jeunes issus des Quartiers Prioritaires de la Ville (E2C93, Proxité), la rupture du déterminisme social et l'égalité des chances.
       - 'Sport_Montagne_Depassement' : Mets l'accent sur la pédagogie de l'effort, les cordées en haute montagne, le dépassement de soi et les séjours de rupture éducative.
       - 'Insertion_Mentorat' : Valorise le parrainage individuel et le mentorat durable sur 12 mois mené par les cadres de grands groupes (AXA, Servier).

    2. Contraintes de Rédaction :
       - Respecte strictement les contraintes de limites de caractères autorisées pour chaque champ.
       - Adopte une posture institutionnelle, humaine et convaincante.

    3. Exécution Financière Obligatoire :
       - Appelle OBLIGATOIREMENT l'outil `calculate_itemized_budget` pour sceller les montants financiers et la ventilation au centime près.
       - N'invente AUCUN chiffre budgétaire toi-même.

    Réponds strictly en te conformant au schéma JSON `FullProposalDocument`.
    """,
    tools=[budget_calculation_tool],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.4,
        top_p=0.95,
    ),
    output_schema=FullProposalDocument,
    output_key="temp:application_proposal_draft",
)
