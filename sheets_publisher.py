from typing import List, Dict, Any
from config import logger, SPREADSHEET_ID
from googleapiclient.discovery import build
import google.auth

class SheetsPublisherModule:
    """Gère la synchronisation bidirectionnelle avec le tableur de pilotage de l'association."""

    def __init__(self):
        self.creds, _ = google.auth.default()
        self.service = build('sheets', 'v4', credentials=self.creds)

    def sync_top_opportunities(self, top_opportunities: List[Dict[str, Any]]):
        """Publie le Top 5 dans l'onglet 'Opportunites_Hebdo'."""
        logger.info("=== [GOOGLE SHEETS SYSTEM] Publication du Top 5 Hebdomadaire ===")
        
        values = []
        for idx, item in enumerate(top_opportunities, 1):
            meta = item["metadata"]
            score = item["score"]
            # Formatage pour le tableur
            values.append([
                f"PENDING", # Status
                f"{score.strategic_fit_score:.2f}",
                meta.title,
                meta.funder_name,
                meta.source_url,
                str(meta.extracted_grant_ceiling or "N/A"),
                meta.submission_deadline,
                score.alignment_reasoning
            ])

        body = {'values': values}
        range_name = 'Opportunites_Hebdo!A2:H6' # On écrase les 5 premières lignes
        
        try:
            self.service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID, range=range_name,
                valueInputOption='USER_ENTERED', body=body).execute()
            logger.info("✅ Top 5 synchronisé sur Google Sheets.")
        except Exception as e:
            logger.error(f"Erreur Sheets API: {e}")

    def get_approved_aaps(self) -> List[Dict[str, Any]]:
        """Récupère les lignes où la colonne Statut (A) est passée à 'GO'."""
        range_name = 'Opportunites_Hebdo!A2:H6'
        result = self.service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
        rows = result.get('values', [])
        
        approved = []
        for i, row in enumerate(rows):
            if row and row[0] == "GO":
                approved.append({
                    "row_index": i + 2, # +2 car index 0 = Ligne 2 (après header)
                    "title": row[2],
                    "url": row[4],
                    "axis": "Sport_Montagne_Depassement" # Par défaut
                })
        return approved

    def mark_as_drafted(self, row_index: int, doc_url: str):
        """Met à jour le statut et ajoute le lien vers le Google Doc."""
        # On change Statut (Col A) en 'DRAFTED' et on ajoute l'URL en fin de ligne
        range_status = f'Opportunites_Hebdo!A{row_index}'
        range_url = f'Opportunites_Hebdo!I{row_index}'
        
        self.service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID, range=range_status,
            valueInputOption='USER_ENTERED', body={'values': [['DRAFTED']]}).execute()
            
        self.service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID, range=range_url,
            valueInputOption='USER_ENTERED', body={'values': [[doc_url]]}).execute()
            
        logger.info(f"✅ Ligne {row_index} mise à jour avec le lien G-Docs.")