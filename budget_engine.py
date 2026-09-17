from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any
from google.adk.tools import FunctionTool


def calculate_itemized_budget(
    total_grant_requested: float, cohort_size: int = 10
) -> Dict[str, Any]:
    """Calcule la ventilation budgétaire déterministe d'un projet Gravir Pour Grandir.

    Cette fonction est strictement arithmétique (Decimal) et garantit :
    1. L'absence totale d'hallucination ou de dérive sur les sommes.
    2. L'égalité absolue : Coût Total Projet = Subvention Demandée + Autofinancement.

    Args:
        total_grant_requested (float): Montant de la subvention sollicitée en EUR.
        cohort_size (int): Nombre de binômes (jeune QPV / mentor) accompagnés.

    Returns:
        Dict[str, Any]: Dictionnaire de ventilation budgétaire au format d'état ADK.
    """
    requested = Decimal(str(total_grant_requested)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    cost_per_pair = Decimal("1500.00")
    total_need = (cost_per_pair * Decimal(cohort_size)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    # Plafond automatique : la demande ne peut excéder le besoin global du projet
    if requested > total_need:
        requested = total_need

    self_financing = total_need - requested

    # Barème certifié et ratios de prise en charge par la subvention
    allocations = {
        "Encadrement_Guide": (Decimal("450.00"), 10, Decimal("0.35")),
        "Hebergement_Refuge": (Decimal("65.00"), 50, Decimal("0.25")),
        "Transport_Train": (Decimal("180.00"), 20, Decimal("0.25")),
        "Equipement_Pret": (Decimal("365.00"), 10, Decimal("0.15")),
    }

    breakdown = []
    allocated_grant_sum = Decimal("0.00")
    categories_list = list(allocations.keys())

    for idx, (cat, (unit_cost, count, ratio)) in enumerate(allocations.items()):
        total_cat_cost = unit_cost * Decimal(count)

        # Ajustement sur la dernière ligne pour éliminer les erreurs d'arrondi de centime
        if idx == len(categories_list) - 1:
            grant_part = requested - allocated_grant_sum
        else:
            grant_part = (requested * ratio).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            allocated_grant_sum += grant_part

        asso_part = total_cat_cost - grant_part

        breakdown.append(
            {
                "category": cat,
                "unit_cost_euro": float(unit_cost),
                "units_count": count,
                "total_cost_euro": float(total_cat_cost),
                "grant_allocation_euro": float(grant_part),
                "association_share_euro": float(asso_part),
            }
        )

    return {
        "status": "success",
        "total_project_cost": float(total_need),
        "total_grant_requested": float(requested),
        "total_self_financing": float(self_financing),
        "budget_breakdown": breakdown,
    }


# Déclaration du composant ADK FunctionTool (argument correct: func=...)
budget_calculation_tool = FunctionTool(func=calculate_itemized_budget)
