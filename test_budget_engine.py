from decimal import Decimal
from budget_engine import calculate_itemized_budget


def test_budget_arithmetic_exactness():
    # Demande de 10 000 € sur un projet de 15 000 € (10 binômes)
    result = calculate_itemized_budget(total_grant_requested=10000.0, cohort_size=10)

    assert result["status"] == "success"
    assert result["total_project_cost"] == 15000.0
    assert result["total_grant_requested"] == 10000.0
    assert result["total_self_financing"] == 5000.0

    # Vérification comptable : Somme des lignes = Totaux
    calculated_grant = sum(item["grant_allocation_euro"] for item in result["budget_breakdown"])
    calculated_self = sum(item["association_share_euro"] for item in result["budget_breakdown"])
    calculated_total = sum(item["total_cost_euro"] for item in result["budget_breakdown"])

    assert Decimal(str(calculated_grant)) == Decimal("10000.00")
    assert Decimal(str(calculated_self)) == Decimal("5000.00")
    assert Decimal(str(calculated_total)) == Decimal("15000.00")
    print("✔ Test Arithmétique & Ventilation Budgétaire : Réussi")


def test_budget_capping():
    # Demande excessive de 20 000 € alors que le besoin projet est de 15 000 €
    result = calculate_itemized_budget(total_grant_requested=20000.0, cohort_size=10)

    assert result["total_grant_requested"] == 15000.0
    assert result["total_self_financing"] == 0.0
    print("✔ Test Plafond Automatique : Réussi")


if __name__ == "__main__":
    print("=== Exécution des tests unitaires locaux pour budget_engine.py ===")
    test_budget_arithmetic_exactness()
    test_budget_capping()
    print("✅ Validation complète du module budget_engine.py effectuée avec succès !")
