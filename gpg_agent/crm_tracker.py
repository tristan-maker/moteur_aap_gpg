import os
from datetime import datetime
from .workspace_packager import _get_workspace_services

DEFAULT_CRM_SHEET_ID = "1o2O-ERo_TDBA0rbhL1_YLOAOcBp6cCVeJy7TCzqZNts"

def _get_first_sheet_title_and_rows(sheets_service, spreadsheet_id: str) -> tuple[str, list[list[str]]]:
    meta = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    first_sheet_title = meta["sheets"][0]["properties"]["title"]
    res = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{first_sheet_title}'!A1:Z500"
    ).execute()
    return first_sheet_title, res.get("values", [])

def get_already_processed_aaps() -> dict:
    sheet_id = os.environ.get("CRM_SPREADSHEET_ID", DEFAULT_CRM_SHEET_ID)
    try:
        _, _, sheets_service = _get_workspace_services()
        sheet_title, rows = _get_first_sheet_title_and_rows(sheets_service, sheet_id)

        headers = rows[0] if rows else []
        data_rows = rows[1:] if len(rows) > 1 else []

        processed_ids = set()
        processed_funders = set()
        processed_urls = set()

        for r in data_rows:
            # Colonne B = ID AAP (index 1), Colonne C = Financeur (index 2), Colonne F = Lien Guichet (index 5)
            if len(r) > 1 and r[1].strip():
                processed_ids.add(r[1].strip().lower())
            if len(r) > 2 and r[2].strip():
                processed_funders.add(r[2].strip().lower())
            if len(r) > 5 and r[5].strip().startswith("http"):
                processed_urls.add(r[5].strip().lower().rstrip("/"))

        return {
            "status": "OK",
            "sheet_title": sheet_title,
            "headers": headers,
            "processed_ids": list(processed_ids),
            "processed_funders": list(processed_funders),
            "processed_urls": list(processed_urls),
            "rows_count": len(data_rows)
        }
    except Exception as exc:
        return {
            "status": "CRM_READ_ERROR",
            "error": str(exc),
            "headers": [],
            "processed_ids": [],
            "processed_funders": [],
            "processed_urls": []
        }

def is_duplicate_in_crm(aap_id: str, funder_name: str, official_aap_url: str = "") -> tuple[bool, str]:
    crm = get_already_processed_aaps()
    if crm["status"] != "OK":
        return False, ""

    clean_id = (aap_id or "").strip().lower()
    clean_funder = (funder_name or "").strip().lower()
    clean_url = (official_aap_url or "").strip().lower().rstrip("/")

    if clean_id and clean_id in crm["processed_ids"]:
        return True, f"REJET_DOUBLON_CRM : L'identifiant '{aap_id}' est déjà présent dans le Google Sheets de suivi."
    if clean_funder and clean_funder in crm["processed_funders"]:
        return True, f"REJET_DOUBLON_CRM : Le financeur '{funder_name}' a déjà un dossier généré dans le Google Sheets de suivi."
    if clean_url and len(clean_url) > 12 and clean_url in crm["processed_urls"]:
        return True, f"REJET_DOUBLON_CRM : L'URL '{official_aap_url}' figure déjà dans le Google Sheets de suivi."

    return False, ""

def log_dossier_to_crm(dossier: dict, dataroom_result: dict) -> dict:
    """
    Ajoute une ligne complète dans le Google Sheets CRM (Colonnes A à I) :
    A: Date | B: ID AAP | C: Financeur | D: Montant demandé | E: Date limite | F: Lien Guichet | G: Lien Data Room | H: Statut | I: Pertinence GPG
    """
    sheet_id = os.environ.get("CRM_SPREADSHEET_ID", DEFAULT_CRM_SHEET_ID)
    try:
        _, _, sheets_service = _get_workspace_services()
        sheet_title, rows = _get_first_sheet_title_and_rows(sheets_service, sheet_id)

        # S'assure que la colonne I ("Pertinence GPG") est bien présente dans l'en-tête
        expected_headers = [
            "Date", "ID AAP", "Financeur", "Montant demandé",
            "Date limite", "Lien Guichet", "Lien Data Room", "Statut", "Pertinence GPG"
        ]
        if not rows or len(rows[0]) < 9:
            sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=f"'{sheet_title}'!A1:I1",
                valueInputOption="USER_ENTERED",
                body={"values": [expected_headers]}
            ).execute()

        today_str = datetime.now().strftime("%Y-%m-%d")
        aap_id = dossier.get("aap_id", "")
        funder = dossier.get("funder_name", "")
        grant_euro = f"{dossier.get('plan_financier_decimal', {}).get('montant_sollicite_euro', 0):.2f} €"
        deadline = dossier.get("deadline_iso", "")
        portal_url = dataroom_result.get("guichet_depot_direct_url") or dossier.get("submission_portal_url") or dossier.get("official_aap_url", "")
        dataroom_url = dataroom_result.get("dossier_drive_url", "")
        status_label = "À relire (Prêt à 85%)"
        pertinence_gpg = dossier.get("paragraphe_miroir_sur_mesure_ia", "")

        new_row = [
            today_str,
            aap_id,
            funder,
            grant_euro,
            deadline,
            portal_url,
            dataroom_url,
            status_label,
            pertinence_gpg
        ]

        sheets_service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=f"'{sheet_title}'!A1",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [new_row]}
        ).execute()

        return {
            "crm_status": "LOGGED_IN_GOOGLE_SHEETS",
            "crm_spreadsheet_url": f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit",
            "row_added": new_row
        }
    except Exception as exc:
        return {
            "crm_status": "CRM_WRITE_ERROR",
            "error": str(exc)
        }
