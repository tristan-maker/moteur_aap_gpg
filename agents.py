from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from google.genai import types

import config
from schemas import (
    SearchQueryMatrix,
    AAPStrategicScore,
)

# --- 1. Agent d'Expansion de Requêtes & Diversification Lexicale ---

query_expansion_agent = LlmAgent(
    name="QueryExpansionSpecialist",
    model=config.MODEL_GEMINI_FLASH,
    instruction="""
    Tu es l'Expert en Renseignement Financier et Veille Subventions de Gravir Pour Grandir.
    Ton objectif est de concevoir une matrice de requêtes de recherche Google avancées (Google Dorks)
    pour dénicher les opportunités de financements les plus récentes, directes ou indirectes.

    Axes de recherche à croiser obligatoirement :
    - Axe 1 : Quartiers prioritaires (QPV), jeunesse défavorisée, inclusion sociale, décrochage, E2C, missions locales.
    - Axe 2 : Sport de pleine nature, montagne, alpinisme, dépassement de soi, séjour de rupture éducative.
    - Axe 3 : Mentorat en entreprise, égalité des chances, mécénat de compétences, fondations abritées.
    - Typologies de financeurs : Fondations familiales, fonds de dotation, comités d'entreprise, ministères, régions, mécénats d'assurances/banques.

    Consignes techniques :
    1. Génère des opérateurs stricts ("appel à projets" OR "subvention" OR "fonds de dotation" OR "mécénat").
    2. Exclus les formations professionnelles payantes et les articles de presse via des exclusions déterministes.
    3. Spécifie l'année courante 2026.
    4. Réponds strictly selon le schéma JSON SearchQueryMatrix.
    """,
    generate_content_config=types.GenerateContentConfig(
        temperature=0.7,
        top_p=0.95,
    ),
    output_schema=SearchQueryMatrix,
    output_key="temp:generated_queries",
)

# --- 2. Agent Radar Web Universel (ADK Google Search Grounding) ---
# NOTE VERTEX AI : Le grounding google_search est incompatible avec output_schema (Controlled Generation).

web_radar_agent = LlmAgent(
    name="GlobalWebRadarAgent",
    model=config.MODEL_GEMINI_FLASH,
    instruction="""
    Tu es le Radar Web d'acquisition d'opportunités de l'association.
    Pour chaque requête générée dans {temp:generated_queries}, utilise l'outil google_search
    pour identifier les appels à projets actifs, les notices de subventions et les formulaires de mécénat.

    Règles :
    1. Ne te restreins jamais à un nombre prédéfini de domaines.
    2. Identifie les URLs officielles de dépôt ou de téléchargement des règlements.
    3. Extrais le nom de l'entité financeuse et le titre exact du programme.
    4. Fournis une synthèse claire et détaillée des opportunités trouvées avec leurs URLs canoniques.
    """,
    tools=[google_search],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2,
        top_p=0.85,
    ),
    output_key="temp:discovered_urls_text",
)

# --- 3. Agent d'Analyse d'Éligibilité et de Scoring Stratégique ---

aap_scoring_specialist = LlmAgent(
    name="AAPScoringSpecialist",
    model=config.MODEL_GEMINI_FLASH,
    instruction="""
    Tu es l'Analyste Stratégique Senior de l'association Gravir Pour Grandir.
    Analyse le règlement brut extrait de l'AAP et produis une notation objective.

    Périmètre associatif :
    - Mission : Émancipation de jeunes de banlieues défavorisées via cordées d'alpinisme et mentorat professionnel.
    - Partenaires opérationnels : E2C93, Proxité, missions locales.
    - Mécènes engagés : AXA, Servier.

    Consignes :
    1. Évalue la pertinence thématique et calcule strategic_fit_score entre 0.0 et 1.0.
    2. Détermine l'axe narratif dominant ('QPV_Inclusion', 'Sport_Montagne_Depassement', 'Insertion_Mentorat').
    3. Justifie en 3 phrases maximum. Réponds strictement en JSON structuré.
    """,
    generate_content_config=types.GenerateContentConfig(
        temperature=0.0,
        top_p=0.80,
    ),
    output_schema=AAPStrategicScore,
    output_key="temp:current_aap_score",
)
