import sys
from decimal import Decimal
from budget_engine import calculate_itemized_budget
from schemas import FinancialApplicationPlan


def test_budget_calculation_exactness():
    raw_plan = calculate_itemized_budget(
        total_grant_requested=8000.00, cohort_size=10, aap_id="hash_1"
    )

    plan = FinancialApplicationPlan(**raw_plan)

    assert plan.total_project_cost == Decimal("15000.00")
    assert plan.total_grant_requested == Decimal("8000.00")
    assert plan.total_self_financing == Decimal("7000.00")

    allocated_grant_sum = sum(
        item.grant_allocation_euro for item in plan.budget_breakdown
    )
    assert allocated_grant_sum == plan.total_grant_requested

    total_cost_sum = sum(
        item.total_cost_euro for item in plan.budget_breakdown
    )
    assert total_cost_sum == plan.total_project_cost

    print("✅ TEST MOTEUR BUDGÉTAIRE RÉUSSI.")


if __name__ == "__main__":
    try:
        test_budget_calculation_exactness()
    except Exception as e:
        print(f"❌ ÉCHEC DU TEST : {e}")
        sys.exit(1)
