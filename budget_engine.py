from decimal import Decimal
from typing import Any, Dict
from google.adk.tools import FunctionTool
from schemas import ExpenseLineItem, FinancialApplicationPlan


def calculate_itemized_budget(
    total_grant_requested: float,
    cohort_size: int = 10,
    aap_id: str = "default_aap",
) -> Dict[str, Any]:
    """Calcule déterministement la ventilation budgétaire avec exactitude au centime."""
    requested = Decimal(str(total_grant_requested))
    cost_per_pair = Decimal("1500.00")
    total_need = cost_per_pair * Decimal(str(cohort_size))

    if requested > total_need:
        requested = total_need

    self_financing = total_need - requested

    encadrement_ratio = Decimal("0.35")
    hebergement_ratio = Decimal("0.25")
    transport_ratio = Decimal("0.25")

    encadrement_grant = (requested * encadrement_ratio).quantize(
        Decimal("0.01")
    )
    hebergement_grant = (requested * hebergement_ratio).quantize(
        Decimal("0.01")
    )
    transport_grant = (requested * transport_ratio).quantize(Decimal("0.01"))

    equipement_grant = requested - (
        encadrement_grant + hebergement_grant + transport_grant
    )

    breakdown = [
        ExpenseLineItem(
            category="Encadrement_Guide",
            unit_cost_euro=Decimal("450.00"),
            units_count=10,
            total_cost_euro=Decimal("4500.00"),
            grant_allocation_euro=encadrement_grant,
            association_share_euro=Decimal("4500.00") - encadrement_grant,
        ),
        ExpenseLineItem(
            category="Hebergement_Refuge",
            unit_cost_euro=Decimal("65.00"),
            units_count=50,
            total_cost_euro=Decimal("3250.00"),
            grant_allocation_euro=hebergement_grant,
            association_share_euro=Decimal("3250.00") - hebergement_grant,
        ),
        ExpenseLineItem(
            category="Transport_Train",
            unit_cost_euro=Decimal("180.00"),
            units_count=20,
            total_cost_euro=Decimal("3600.00"),
            grant_allocation_euro=transport_grant,
            association_share_euro=Decimal("3600.00") - transport_grant,
        ),
        ExpenseLineItem(
            category="Equipement_Pret",
            unit_cost_euro=Decimal("365.00"),
            units_count=10,
            total_cost_euro=Decimal("3650.00"),
            grant_allocation_euro=equipement_grant,
            association_share_euro=Decimal("3650.00") - equipement_grant,
        ),
    ]

    plan = FinancialApplicationPlan(
        aap_id=aap_id,
        total_project_cost=total_need,
        total_grant_requested=requested,
        total_self_financing=self_financing,
        budget_breakdown=breakdown,
    )

    return plan.model_dump()


budget_calculation_tool = FunctionTool(func=calculate_itemized_budget)
