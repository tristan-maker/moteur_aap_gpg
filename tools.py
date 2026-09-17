from decimal import Decimal
from google.adk.tools import FunctionTool
from schemas import AAPRawMetadata, FinancialApplicationPlan, ExpenseLineItem

class DocumentParserModule:
    """Gère l'extraction de texte à partir de PDFs ou HTML complexes."""
    def parse(self, raw_payload: dict) -> str:
        text = raw_payload.get("text", "")
        if not text and "pdf_content" in raw_payload:
            return "Texte extrait du PDF via Document AI..."
        return text

def calculate_itemized_budget(aap_id: str, total_grant_requested: float, cohort_size: int = 10) -> dict:
    """Calcule déterministement la ventilation budgétaire sans intervention du LLM."""
    requested = Decimal(str(total_grant_requested))
    cost_per_pair = Decimal("1500.00")
    total_need = cost_per_pair * Decimal(cohort_size)
    
    if requested > total_need:
        requested = total_need

    self_financing = total_need - requested
    
    # Application stricte des ratios FinOps définis par la direction
    breakdown = [
        {
            "category": "Encadrement_Guide",
            "unit_cost_euro": Decimal("450.00"),
            "units_count": 10,
            "total_cost_euro": Decimal("4500.00"),
            "grant_allocation_euro": requested * Decimal("0.35"),
            "association_share_euro": Decimal("4500.00") - (requested * Decimal("0.35"))
        },
        {
            "category": "Hebergement_Refuge",
            "unit_cost_euro": Decimal("65.00"),
            "units_count": 50,
            "total_cost_euro": Decimal("3250.00"),
            "grant_allocation_euro": requested * Decimal("0.25"),
            "association_share_euro": Decimal("3250.00") - (requested * Decimal("0.25"))
        },
        {
            "category": "Transport_Train",
            "unit_cost_euro": Decimal("180.00"),
            "units_count": 20,
            "total_cost_euro": Decimal("3600.00"),
            "grant_allocation_euro": requested * Decimal("0.25"),
            "association_share_euro": Decimal("3600.00") - (requested * Decimal("0.25"))
        },
        {
            "category": "Equipement_Pret",
            "unit_cost_euro": Decimal("365.00"),
            "units_count": 10,
            "total_cost_euro": Decimal("3650.00"),
            "grant_allocation_euro": requested * Decimal("0.15"),
            "association_share_euro": Decimal("3650.00") - (requested * Decimal("0.15"))
        }
    ]
    
    plan = FinancialApplicationPlan(
        aap_id=aap_id,
        total_project_cost=total_need,
        total_grant_requested=requested,
        total_self_financing=self_financing,
        budget_breakdown=[ExpenseLineItem(**b) for b in breakdown]
    )
    return plan.model_dump()

def deterministic_nogo_filter(aap: AAPRawMetadata) -> bool:
    """Applique les seuils financiers stricts sans LLM."""
    MIN_GRANT = Decimal("2000.00")
    MAX_ASSO_BUDGET = Decimal("400000.00")
    
    if aap.extracted_grant_ceiling and aap.extracted_grant_ceiling < MIN_GRANT:
        return False
    if aap.required_annual_budget_ceiling and aap.required_annual_budget_ceiling > MAX_ASSO_BUDGET:
        return False
    return True

budget_calculation_tool = FunctionTool(func=calculate_itemized_budget)