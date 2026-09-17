from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "moteur-aap-gpg"
    print("✔ Test API Endpoint Santé (Health Check) : Réussi")


def test_trigger_discovery_pipeline_endpoint():
    payload = {
        "user_id": "test_operator",
        "session_id": "session_test_01",
        "initial_trigger_message": "Test de déclenchement",
    }
    response = client.post("/api/v1/trigger-discovery", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "initiated"
    assert data["session_id"] == "session_test_01"
    print("✔ Test API Endpoint Déclenchement Pipeline : Réussi")


if __name__ == "__main__":
    print("=== Exécution des tests unitaires locaux pour main.py ===")
    test_health_check_endpoint()
    test_trigger_discovery_pipeline_endpoint()
    print("✅ Validation complète de l'API Prod main.py effectuée avec succès !")
