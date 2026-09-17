from google.adk.agents import LlmAgent
from google.adk.planners import BuiltInPlanner
from google.adk.tools import google_search
from google.genai import types
from config import PROD_SAFETY_SETTINGS, initialize_h_company_mcp_toolset
from tools import budget_calculation_tool
from schemas import (
    AAPStrategicScore,
    DiscoveredUrlList,
    ExtractedAAPAttributes,
    FormStructureDefinition,
    FullProposalDocument,
    SearchQueryMatrix,
)

mcp_toolset = initialize_h_company_mcp_toolset()
mcp_tools = mcp_toolset.to_tools()

query_expansion_agent = LlmAgent(
    name="QueryExpansionSpecialist",
    model="gemini-2.5-flash",
    instruction="""
    Tu es l'Expert en Renseignement Financier et Veille Subventions de Gravir Pour Grandir.
    Ton objectif est de concevoir une matrice de requêtes de recherche Google avancées (Google Dorks)
    pour dénicher les opportunités de financements les plus récentes, directes ou indirectes.

    Axes de recherche à croiser obligatoirement :
    - Axe 1 : Quartiers prioritaires (QPV), jeunesse défavorisée, inclusion sociale, décrochage, E2C, missions locales.
    - Axe 2 : Sport de pleine nature, montagne, alpinisme, dépassement de soi, séjour de rupture éducative.
    - Axe 3 : Mentorat en entreprise, égalité des chances, mécénat de compétences, fondations abritées.

    Consignes techniques :
    1. Génère des opérateurs stricts ("appel à projets" OR "subvention" OR "fonds de dotation").
    2. Exclus les formations payantes et les articles de presse via des exclusions déterministes (-filetype:pdf).
    3. Spécifie l'année courante 2026. Réponds strictement selon le schéma JSON SearchQueryMatrix.
    """,
    generate_content_config=types.GenerateContentConfig(
        temperature=0.7, top_p=0.95, safety_settings=PROD_SAFETY_SETTINGS
    ),
    output_schema=SearchQueryMatrix,
    output_key="temp:generated_queries"
)

web_radar_agent = LlmAgent(
    name="GlobalWebRadarAgent",
    model="gemini-2.5-flash",
    instruction="""Radar Web acquisition...""",
    tools=[google_search],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2, top_p=0.85, safety_settings=PROD_SAFETY_SETTINGS
    ),
    output_schema=DiscoveredUrlList,
    output_key="temp:discovered_urls"
)

content_harvester_agent = LlmAgent(
    name="DeepContentHarvester",
    model="gemini-2.5-flash",
    instruction="""Expert en Extraction de Données...""",
    tools=mcp_tools,
    generate_content_config=types.GenerateContentConfig(
        temperature=0.1, top_p=0.9, safety_settings=PROD_SAFETY_SETTINGS
    ),
    output_key="temp:raw_web_payload"
)

metadata_extractor_agent = LlmAgent(
    name="AAPMetadataExtractor",
    model="gemini-2.5-flash",
    instruction="""
    Tu es un Expert en Analyse de Règlements de Subventions.
    Analyse le texte brut fourni et extrais les métadonnées structurées.
    
    Champs à extraire :
    - Montant maximum de la subvention (extracted_grant_ceiling)
    - Budget annuel max de l'association pour être éligible (required_annual_budget_ceiling)
    - Date limite de dépôt (submission_deadline) au format AAAA-MM-JJ.
    - Périmètre géographique (geographic_scope).
    """,
    generate_content_config=types.GenerateContentConfig(
        temperature=0.0, safety_settings=PROD_SAFETY_SETTINGS
    ),
    output_schema=ExtractedAAPAttributes,
    output_key="temp:extracted_metadata"
)

form_fields_extractor_agent = LlmAgent(
    name="FormFieldsExtractor",
    model="gemini-2.5-flash",
    instruction="""
    Tu es l'Expert en Analyse de Portails de Subvention.
    Utilise les outils MCP pour inspecter la page de formulaire à l'URL : {session:portal_url}.
    
    Objectifs :
    1. Identifier tous les champs de saisie (input, textarea).
    2. Extraire les labels des questions.
    3. Détecter les limites de caractères ou de mots si indiquées.
    """,
    tools=mcp_tools,
    output_schema=FormStructureDefinition,
    generate_content_config=types.GenerateContentConfig(
        temperature=0.0, safety_settings=PROD_SAFETY_SETTINGS
    ),
    output_key="temp:target_form_schema"
)

compliance_enforcer_agent = LlmAgent(
    name="CharacterLimitCompactor",
    model="gemini-2.5-flash",
    instruction="""
    Tu es l'Expert en Concision Éditoriale.
    Le texte fourni dépasse la limite de caractères autorisée.
    Reformule le texte pour qu'il respecte strictement la limite de {limit} caractères,
    tout en préservant l'impact émotionnel et les données clés.
    """,
    generate_content_config=types.GenerateContentConfig(
        temperature=0.0, safety_settings=PROD_SAFETY_SETTINGS
    ),
    output_key="temp:validated_draft"
)

aap_scoring_specialist = LlmAgent(
    name="AAPScoringSpecialist",
    model="gemini-2.5-flash",
    instruction="""
    Tu es l'Analyste Stratégique Senior de l'association Gravir Pour Grandir.
    Analyse le règlement brut extrait de l'AAP et produis une notation objective.
    
    Périmètre associatif :
    - Mission : Émancipation de jeunes de banlieues défavorisées via cordées d'alpinisme et mentorat.
    - Partenaires opérationnels : E2C93, Proxité, missions locales.
    - Mécènes engagés : AXA, Servier.
    
    Calcule strategic_fit_score entre 0.0 et 1.0. Réponds strictement en JSON structuré.
    """,
    generate_content_config=types.GenerateContentConfig(
        temperature=0.0, top_p=0.80, safety_settings=PROD_SAFETY_SETTINGS
    ),
    output_schema=AAPStrategicScore,
    output_key="temp:current_aap_score"
)

strategic_narrative_drafter = LlmAgent(
    name="StrategicNarrativeDrafter",
    model="gemini-3.8-pro",
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(include_thoughts=False, thinking_budget=2048)
    ),
    instruction="""
    Tu es le Directeur du Développement de Gravir Pour Grandir.
    Rédige l'intégralité du dossier pour le projet validé.
    
    Règles :
    1. Aligne le discours selon l'axe sélectionné ('QPV_Inclusion', 'Sport_Montagne_Depassement', 'Insertion_Mentorat').
    2. Respecte scrupuleusement la limite character_limit pour chaque champ de question.
    3. Appelle obligatoirement l'outil calculate_itemized_budget pour sceller les montants financiers.
    """,
    generate_content_config=types.GenerateContentConfig(
        temperature=0.4, top_p=0.95, safety_settings=PROD_SAFETY_SETTINGS
    ),
    tools=[budget_calculation_tool],
    output_schema=FullProposalDocument,
    output_key="temp:application_proposal_draft"
)