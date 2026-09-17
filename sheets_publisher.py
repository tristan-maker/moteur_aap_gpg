import json
import logging
import os
from typing import Any, Dict, List, Optional
from google.cloud import secretmanager
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import config
from schemas import AAPRawMetadata

logger = logging.getLogger("GravirPourGrandir.SheetsPublisher")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_sheets_credentials(
    secret_id: str = "workspace-service-account-key",
    project_id: str = config.GCP_PROJECT_ID,
) -> Optional[service_account.Credentials]:
    """Charge les identifiants IAM depuis Secret Manager ou le fichier ADC local."""
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        logger.info("✔ Identifiants Sheets chargés via ADC local.")
        return service_account.Credentials.from_service_account_file(
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS"), scopes=SCOPES
        )

    try:
        client = secretmanager.SecretManagerServiceClient()
        secret_path = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": secret_path})
        secret_data = response.payload.data.decode("UTF-8")
        service_account_info = json.loads(secret_data)
        logger.info("✔ Identifiants Service Account chargés depuis GCP Secret Manager.")
        return service_account.Credentials.from_service_account_info(
            service_account_info, scopes=SCOPES
        )
    except Exception as e:
        logger.warning(
            f"⚠️ Secret Manager non accessible ({e}). Mode fallback local activé."
        )
        return None


def format_aap_row_payload(aap: AAPRawMetadata) -> List[Any]:
    """Formate une instance AAPRawMetadata en ligne d'éléments pour Google Sheets."""
    return [
        aap.id,
        aap.title,
        aap.funder_name,
        float(aap.extracted_grant_ceiling) if aap.extracted_grant_ceiling else "N/A",
        aap.submission_deadline,
        aap.geographic_scope,
        aap.source_url,
        "NON",  # Colonne H : Case à cocher "GO" pour arbitrage HITL #1
    ]


def publish_aaps_to_sheet(
    spreadsheet_id: str,
    aaps: List[AAPRawMetadata],
    range_name: str = "Opportunites_Hebdo!A2:H",
) -> Dict[str, Any]:
    """Insère la liste des opportunités qualifiées dans le tableur Google Sheets.

    Args:
        spreadsheet_id (str) : ID du document Google Sheets cible.
        aaps (List[AAPRawMetadata]) : Liste des appels à projets retenus.
        range_name (str) : Plage de cellules cibles.

    Returns:
        Dict[str, Any] : Rapport de mise à jour de l'API Google Sheets.
    """
    creds = get_sheets_credentials()

    if not creds:
        logger.info(
            f"[MOCK SHEETS] {len(aaps)} opportunité(s) synchronisée(s) localement dans {spreadsheet_id}."
        )
        return {
            "status": "success",
            "spreadsheet_id": spreadsheet_id,
            "updated_rows": len(aaps),
            "mode": "mock",
        }

    try:
        service = build("sheets", "v4", credentials=creds)
        values = [format_aap_row_payload(aap) for aap in aaps]
        body = {"values": values}

        result = (
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body,
            )
            .execute()
        )

        logger.info(
            f"✔ Synchronisation Google Sheets réussie : {result.get('updates', {}).get('updatedRows', 0)} ligne(s) ajoutée(s)."
        )
        return {
            "status": "success",
            "spreadsheet_id": spreadsheet_id,
            "updated_rows": result.get("updates", {}).get("updatedRows", 0),
            "mode": "live",
        }

    except HttpError as error:
        logger.error(f"❌ Erreur lors de l'appel à l'API Google Sheets : {error}")
        return {
            "status": "error",
            "spreadsheet_id": spreadsheet_id,
            "error": str(error),
        }
