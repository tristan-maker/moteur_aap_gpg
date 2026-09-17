import logging
import os
from typing import Any, Dict, List, Optional
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import config
from schemas import AAPRawMetadata

logger = logging.getLogger("GravirPourGrandir.SheetsPublisher")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_sheets_credentials():
    try:
        creds, _ = google.auth.default(scopes=SCOPES)
        return creds
    except Exception as e:
        logger.warning(f"⚠️ Échec d'obtention des identifiants Google Auth: {e}")
        return None

def format_aap_row_payload(aap: AAPRawMetadata) -> List[Any]:
    return [
        aap.id,
        aap.title,
        aap.funder_name,
        float(aap.extracted_grant_ceiling) if aap.extracted_grant_ceiling else "N/A",
        aap.submission_deadline,
        aap.geographic_scope,
        aap.source_url,
        "NON",
    ]

def publish_aaps_to_sheet(
    spreadsheet_id: str,
    aaps: List[AAPRawMetadata],
    range_name: str = "Opportunites_Hebdo!A2:H",
) -> Dict[str, Any]:
    creds = get_sheets_credentials()

    if not creds:
        logger.info(f"[MOCK SHEETS] {len(aaps)} opportunité(s) synchronisée(s) localement dans {spreadsheet_id}.")
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
            .update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body,
            )
            .execute()
        )

        updated_rows = result.get('updatedRows', len(aaps))
        logger.info(f"✔ Synchronisation Google Sheets réussie : {updated_rows} ligne(s) mise(s) à jour à partir de A2.")
        return {
            "status": "success",
            "spreadsheet_id": spreadsheet_id,
            "updated_rows": updated_rows,
            "mode": "live",
        }

    except HttpError as error:
        logger.error(f"❌ Erreur lors de l'appel à l'API Google Sheets : {error}")
        return {
            "status": "error",
            "spreadsheet_id": spreadsheet_id,
            "error": str(error),
        }
