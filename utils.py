"""
Utilitaires transverses pour le projet GPG.
"""

from google.cloud import secretmanager
import config

def get_secret(secret_id: str, project_id: str = config.GCP_PROJECT_ID, version_id: str = "latest"):
    """
    Récupère la valeur d'un secret depuis GCP Secret Manager.

    Cette méthode permet de ne pas stocker de clés en clair dans le code ou 
    sur le disque du serveur en production.

    Args:
        secret_id: Le nom du secret (ex: H_COMPANY_API_KEY).
        project_id: L'identifiant numérique du projet GCP.
        version_id: La version du secret à récupérer.
    Returns:
        La valeur brute du secret (string).
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")