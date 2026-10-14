"""
Moteur comptable 100% déterministe en Decimal garantissant l'équilibre strict Charges == Produits au centime près.
"""
from decimal import Decimal, ROUND_HALF_UP
from google.adk.tools import FunctionTool
from .schemas import ProgramTrack

# Grilles budgétaires officielles de Gravir Pour Grandir
OFFICIAL_BUDGET_MATRICES = {
    "ALPINISME_48K": {
        "total_cost": Decimal("48000.00"),
        "valorisation_nature": Decimal("4480.00"),
        "cofinanceurs_mentionnes": "AXA Atout Cœur, Fondation 29 Haussmann (SG), Remises partenaires EPPM/ANCV",
        "lines": [
            ("Encadrement & Logistique Montagne EPPM (Guides diplômés, refuges, matériel)", Decimal("28000.00"), Decimal("0.55")),
            ("Transports bas-carbone SNCF TGV (10 binômes x 4 week-ends)", Decimal("14000.00"), Decimal("0.30")),
            ("Véhicules d'approche en vallée & logistique dernier kilomètre", Decimal("3000.00"), Decimal("0.10")),
            ("Soirée de lancement escalade (Arkose), formation mentors & frais", Decimal("3000.00"), Decimal("0.05")),
        ]
    },
    "ALPINISME_COMPLET_54K": {
        "total_cost": Decimal("54000.00"),
        "valorisation_nature": Decimal("4480.00"),
        "cofinanceurs_mentionnes": "AXA Atout Cœur (35 000 €), Fondation 29 Haussmann (25 000 €)",
        "lines": [
            ("Guides de haute montagne diplômés (EPPM) & Nuitées en refuges/gîtes", Decimal("30000.00"), Decimal("0.55")),
            ("Transports (SNCF / Voitures) & Restauration d'altitude", Decimal("24000.00"), Decimal("0.45")),
        ]
    },
    "VOILE_48K": {
        "total_cost": Decimal("48000.00"),
        "valorisation_nature": Decimal("3500.00"),
        "cofinanceurs_mentionnes": "Mécènes Entreprises (30 000 €) & Partenaires Territoriaux (Normandie / Deauville)",
        "lines": [
            ("Location de voiliers habitables & Frais de port (4 week-ends mer)", Decimal("18000.00"), Decimal("0.38")),
            ("Encadrement par Skippers professionnels diplômés d'État", Decimal("14000.00"), Decimal("0.30")),
            ("Transports SNCF Paris-Littoral & Avitaillement à bord", Decimal("11000.00"), Decimal("0.22")),
            ("Équipements de sécurité maritime & Journée d'intégration", Decimal("5000.00"), Decimal("0.10")),
        ]
    },
    "PASSAGE_ECHELLE_3_ANS": {
        "total_cost": Decimal("103000.00"),
        "valorisation_nature": Decimal("97458.00"),
        "cofinanceurs_mentionnes": "AXA Atout Cœur (35 000 €), Fondation 29 Haussmann (25 000 €/an sur 3 ans)",
        "lines": [
            ("Coûts directs d'expédition d'une promotion (Guides, Refuges, Transports)", Decimal("54000.00"), Decimal("0.50")),
            ("Direction Opérationnelle salariée (Pilotage essaimage, suivi binômes)", Decimal("29000.00"), Decimal("0.30")),
            ("Frais de structure certifiés (CAC Cofirec, Comptabilité, Assurance)", Decimal("12000.00"), Decimal("0.12")),
            ("Ingénierie de développement, mesure d'impact & recherche de mécènes", Decimal("8000.00"), Decimal("0.08")),
        ]
    }
}

def generate_deterministic_budget(
    requested_grant_euro: float,
    program_track: ProgramTrack = "ALPINISME_48K"
) -> dict:
    """Calcule au centime près la ventilation budgétaire sans intervention du LLM."""
    track = program_track if program_track in OFFICIAL_BUDGET_MATRICES else "ALPINISME_48K"
    matrix = OFFICIAL_BUDGET_MATRICES[track]
    total_cost: Decimal = matrix["total_cost"]

    requested = Decimal(str(requested_grant_euro)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    max_allowed = (total_cost * Decimal("0.80")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if requested > max_allowed:
        requested = max_allowed

    cofinancing = (total_cost - requested).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    ratio_pct = ((requested / total_cost) * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

    breakdown = []
    allocated_sum = Decimal("0.00")
    lines = matrix["lines"]

    for idx, (poste, line_total, weight) in enumerate(lines):
        if idx < len(lines) - 1:
            grant_part = (requested * weight).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            allocated_sum += grant_part
        else:
            grant_part = (requested - allocated_sum).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        cofi_part = (line_total - grant_part).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        breakdown.append({
            "poste": poste,
            "montant_total_euro": float(line_total),
            "subvention_sollicitee_euro": float(grant_part),
            "cofinancement_acquis_euro": float(cofi_part)
        })

    return {
        "grille_utilisee": track,
        "cout_total_projet_euro": float(total_cost),
        "montant_sollicite_euro": float(requested),
        "poids_subvention_pct": f"{ratio_pct} %",
        "cofinancement_acquis_euro": float(cofinancing),
        "principaux_cofinanceurs": matrix["cofinanceurs_mentionnes"],
        "contributions_volontaires_en_nature_euro": float(matrix["valorisation_nature"]),
        "lignes_budgetaires": breakdown
    }

budget_tool = FunctionTool(generate_deterministic_budget)
