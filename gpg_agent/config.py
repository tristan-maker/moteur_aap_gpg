from datetime import date

GPG_LEGAL_IDENTITY = {
    "denomination": "Gravir Pour Grandir (GPG)",
    "forme_juridique": "Association Loi 1901 d'intérêt général",
    "rna": "W751270417",
    "siret": "923 853 568 00015",
    "code_ape": "96.09Z",
    "date_creation": "16/05/2023",
    "siege_social": "2, rue Brisemiche, 75004 Paris",
    "antennes_operationnelles": ["Paris / Île-de-France (Seine-Saint-Denis 93)", "Lyon / Auvergne-Rhône-Alpes"],
    "representant_legal": "Tristan Mathon (Président co-fondateur - tristan@gravirpourgrandir.fr)",
    "contact_operationnel": "Yannig Loyer (Trésorier co-fondateur)",
    "gouvernance_complete": "Tristan Mathon (Président co-fondateur), Yannig Loyer (Trésorier co-fondateur), Stanislas Chastel (Secrétaire général), Caroline Quenardel (Membre du Bureau), appuyés par Jean-Louis Collange (Ingénierie financière - Mécénat de compétences Servier)",
    "eligibilite_mecenat": "Rescrit fiscal d'intérêt général obtenu le 30/06/2025 (éligibilité aux articles 200 et 238 bis du CGI - réduction d'impôt de 60 % pour les entreprises)",
    "audit_comptes": "Cabinet COFIREC (11 rue La Fayette, 75009 Paris) - Comptes annuels certifiés réguliers et sincères sans réserve",
    "iban": "FR76 1695 8000 0159 2956 0258 540 (BIC : QNTOFRP1XXX)"
}

GPG_CERTIFIED_PROOFS = {
    "jeunes_accompagnes_par_promotion": 24,
    "tranche_age": "16 à 25 ans (issus des QPV, NEET ou en décrochage)",
    "taux_sortie_positive_emploi_formation_pct": 82,
    "taux_assiduite_parcours_pct": 91,
    "heures_accompagnement_par_jeune": 120,
    "encadrement_securite": "Guides de Haute Montagne UIAGM et Skippers diplômés d'État"
}

DETERMINISTIC_BLOCKS = {
    "mission_courte": (
        "Gravir Pour Grandir (GPG) est une association Loi 1901 d'intérêt général qui accompagne "
        "les jeunes de 16 à 25 ans issus des Quartiers Prioritaires de la Ville (QPV) ou en "
        "situation d'isolement vers l'insertion sociale et professionnelle durable, en utilisant "
        "l'exigence de l'alpinisme, de la voile hauturière et du mentorat individuel."
    ),
    "constat_social_qpv": (
        "En Île-de-France comme en Auvergne-Rhône-Alpes, les jeunes de 16 à 25 ans résidant en QPV "
        "cumulent des freins invisibles à l'emploi : autocensure, absence de réseau professionnel "
        "et manque de cadres collectifs exigeants permettant de révéler leurs compétences transversales "
        "(gestion du stress, solidarité de cordée, prise de décision)."
    ),
    "methodologie_4_weekends_alpinisme": (
        "Un parcours progressif de 6 mois structuré autour de 4 week-ends d'immersion alpine "
        "(progression glaciaire, gestion du risque en cordée, bivouac en autonomie et ascension "
        "d'un sommet de 3 500 m à 4 000 m encadrée par des guides UIAGM) couplé à un parrainage "
        "individuel par des mentors issus d'entreprises partenaires pour traduire l'expérience "
        "de la cordée en projet professionnel concret."
    ),
    "methodologie_4_weekends_voile": (
        "Un parcours maritime de 6 mois articulé autour de 4 week-ends de navigation hauturière "
        "en équipage (quart de nuit, météorologie, manœuvres collectives et responsabilité à la barre "
        "sous la supervision de skippers professionnels) jumelé à des ateliers de coaching emploi "
        "et de prise de parole devant les recruteurs."
    ),
    "argumentaire_archetype": {
        "FONDATION_BANCAIRE_ECHELLE": (
            "Ce soutien permet de consolider notre changement d'échelle inter-régional (Paris / Lyon) "
            "avec un coût unitaire maîtrisé de 2 000 € par jeune accompagné sur 6 mois et une mesure "
            "d'impact longitudinal à M+6 et M+12 sur le retour à l'emploi ou la formation qualifiante."
        ),
        "FONDS_OUTDOOR_SPORT": (
            "En démocratisant l'accès à la haute montagne et à la mer pour des jeunes qui n'ont jamais "
            "quitté leur quartier, le programme forme une nouvelle génération de pratiquants autonomes, "
            "formés à la sécurité alpine/maritime et à la préservation des écosystèmes naturels."
        ),
        "ENTREPRISE_RSE_RH": (
            "Au-delà du mécénat financier, le programme offre un levier d'engagement fort pour les "
            "collaborateurs du Groupe : mentorat individuel des jeunes, ateliers CV/simulation "
            "d'entretien et rencontres inspirantes autour du dépassement de soi."
        ),
        "SUBVENTION_PUBLIQUE": (
            "L'action s'inscrit pleinement dans les priorités des Contrats de Ville et de l'insertion "
            "des publics QPV/NEET, en complémentarité directe avec les Missions Locales, les clubs de "
            "prévention spécialisée et les structures d'éducation populaire du territoire."
        ),
    }
}

GPG_25_TARGET_FOUNDATIONS = [
    {"name": "Fondation Decathlon", "query": "Fondation Decathlon appel à projets sport insertion jeunes"},
    {"name": "Fondation Petzl", "query": "Fondation Petzl déposer un projet montagne jeunes solidarité"},
    {"name": "Fonds Impact 2024 / Héritage Sport", "query": "appel à projets sport inclusion jeunesse QPV insertion"},
    {"name": "Fondation FDJ", "query": "Fondation FDJ appel à projets sport égalité des chances jeunes"},
    {"name": "Fondation Lacoste", "query": "Fondation Lacoste appel à projets insertion jeunes par le sport"},
    {"name": "Fondation Transdev", "query": "Fondation Transdev appel à projets mobilité sociale jeunes"},
    {"name": "Fondation Vinci pour la Cité", "query": "Fondation Vinci pour la Cité déposer un projet insertion jeunes QPV"},
    {"name": "Fondation Groupe RATP", "query": "Fondation Groupe RATP appel à projets jeunesse insertion citoyenneté"},
    {"name": "Fondation SNCF", "query": "Fondation SNCF appel à projets jeunesse engagement insertion"},
    {"name": "Fondation Groupe EDF", "query": "Fondation Groupe EDF appel à projets inclusion jeunes éducation"},
    {"name": "Fondation Société Générale", "query": "Fondation Société Générale appel à projets insertion professionnelle jeunes sport"},
    {"name": "Fondation BNP Paribas Projet Banlieues", "query": "Fondation BNP Paribas Projet Banlieues appel à projets QPV jeunes"},
    {"name": "Fondation Crédit Agricole", "query": "Fondation Crédit Agricole jeunes insertion socio-professionnelle appel à projets"},
    {"name": "Fondation Macif", "query": "Fondation Macif appel à projets inclusion jeunesse mobilité"},
    {"name": "Fondation MAIF", "query": "Fondation MAIF appel à projets sport inclusion jeunesse"},
    {"name": "Fondation Air France", "query": "Fondation Air France déposer un projet jeunesse éducation insertion"},
    {"name": "Fondation Bouygues", "query": "Fondation Bouygues appel à projets engagement jeunes solidarité"},
    {"name": "Fondation Orange", "query": "Fondation Orange appel à projets insertion jeunes éducation"},
    {"name": "Fondation Veolia", "query": "Fondation Veolia déposer un projet insertion emploi solidarité"},
    {"name": "Fondation TotalEnergies", "query": "Fondation TotalEnergies jeunesse inclusion éducation insertion appel à projets"},
    {"name": "Fondation de France", "query": "site:fondationdefrance.org/fr/appels-a-projets jeunes sport insertion"},
    {"name": "Agence Nationale du Sport (ANS)", "query": "Agence Nationale du Sport appel à projets insertion par le sport QPV"},
    {"name": "Fondation Caritas France", "query": "Fondation Caritas appel à projets insertion jeunes emploi solidarité"},
    {"name": "Fonds du 11 Janvier", "query": "appel à projets jeunesse citoyenneté mixité sociale sport QPV"},
    {"name": "Portail Avise", "query": "site:avise.org/actualite appel à projets jeunesse sport inclusion"}
]

def generate_deterministic_search_queries() -> list[str]:
    current_year = date.today().year
    next_year = current_year + 1
    return [
        f"appel à projets fondation sport insertion jeunes QPV {current_year} {next_year}",
        f"appel à projets mécénat jeunesse égalité des chances mentorat association {current_year} {next_year}"
    ]

def get_next_unprocessed_radar_targets(processed_funders_lower: list[str], batch_size: int = 3) -> list[dict]:
    fresh_targets = []
    for f in GPG_25_TARGET_FOUNDATIONS:
        f_name_low = f["name"].lower()
        already_in_crm = any(
            (crm_f in f_name_low or f_name_low in crm_f)
            for crm_f in processed_funders_lower if len(crm_f) > 3
        )
        if not already_in_crm:
            fresh_targets.append(f)
    return fresh_targets[:batch_size]

def build_wide_net_discovery_queries(processed_funders_lower: list[str]) -> dict:
    current_year = date.today().year
    next_year = current_year + 1

    open_discovery_pool = [
        f'"appel à projets" ({current_year} OR {next_year}) ("jeunes" OR "16-25 ans") ("QPV" OR "quartiers prioritaires" OR "insertion") ("sport" OR "éducation" OR "mentorat")',
        f'"appel à projets" ({current_year} OR {next_year}) ("fonds de dotation" OR "fondation") ("insertion professionnelle" OR "égalité des chances") "jeunes" "association"',
        f'"appel à candidatures" ({current_year} OR {next_year}) "association" ("sport" OR "plein air" OR "montagne" OR "voile" OR "dépassement de soi") "jeunes"',
        f'site:fondationdefrance.org/fr/appels-a-projets ({current_year} OR {next_year}) ("jeunes" OR "sport" OR "insertion" OR "santé")',
        f'("appel à projets" OR "mécénat") ({current_year} OR {next_year}) ("décrochage" OR "NEET" OR "insertion sociale") "jeunes" "Loi 1901"'
    ]

    territorial_public_pool = [
        f'"appel à projets" ({current_year} OR {next_year}) ("Île-de-France" OR "Auvergne-Rhône-Alpes") ("jeunes" OR "QPV" OR "sport" OR "politique de la ville")',
        f'"appel à projets" ({current_year} OR {next_year}) ("ANCT" OR "contrat de ville" OR "cités éducatives" OR "DRAJES" OR "Agence nationale du sport") "jeunes"',
        f'"appel à projets" ({current_year} OR {next_year}) ("département" OR "région" OR "CAF") ("jeunesse" OR "insertion" OR "autonomie des jeunes")'
    ]

    day_seed = date.today().toordinal()
    axe_1_open = open_discovery_pool[day_seed % len(open_discovery_pool)]
    axe_2_territorial = territorial_public_pool[day_seed % len(territorial_public_pool)]

    fresh_25 = get_next_unprocessed_radar_targets(processed_funders_lower, batch_size=3)
    funder_names = " OR ".join([f'"{f["name"]}"' for f in fresh_25])
    axe_3_targeted = f'({funder_names}) ("appel à projets" OR "déposer un projet") ({current_year} OR {next_year})'

    return {
        "1_requete_grand_angle_decouverte_ouverte": axe_1_open,
        "2_requete_territoriale_et_publique_idf_aura": axe_2_territorial,
        "3_requete_rotation_grands_mecenes": axe_3_targeted,
        "exemples_mecenes_du_jour": [f["name"] for f in fresh_25]
    }
