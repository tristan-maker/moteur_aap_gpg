from typing import Dict, List
from schemas import AAPRawMetadata, AAPStrategicScore


class GoogleSheetsSyncManager:
    """Gère l'I/O transactionnelle Google Sheets et la barrière synchrone HITL #1."""

    def __init__(self, spreadsheet_id: str = "mock_sheet_id"):
        self.spreadsheet_id = spreadsheet_id
        self._mock_sheet_db: Dict[str, Dict[str, str]] = {}

    def publish_top_5_opportunities(
        self, top5_list: List[tuple]
    ) -> Dict[str, int]:
        """Publie les 5 opportunités retenues dans l'onglet Opportunites_Hebdo."""
        row_mapping = {}
        for index, item in enumerate(top5_list, start=2):
            metadata, score_obj, composite_score = item[0], item[1], item[2]
            
            row_data = {
                "row_id": index,
                "aap_id": metadata.id,
                "title": metadata.title,
                "funder": metadata.funder_name,
                "grant_ceiling": str(metadata.extracted_grant_ceiling or "N/C"),
                "fit_score": str(score_obj.strategic_fit_score),
                "composite_score": str(composite_score),
                "status": "EN_ATTENTE_ARBITRAGE",
                "decision_go": "NON",
            }
            self._mock_sheet_db[metadata.id] = row_data
            row_mapping[metadata.id] = index

        return row_mapping

    def check_hitl_approval(self, aap_id: str) -> bool:
        """Vérifie si l'opérateur humain a coché 'GO' pour un dossier spécifique."""
        record = self._mock_sheet_db.get(aap_id)
        if not record:
            return False
        return record.get("decision_go") == "OUI"

    def simulate_human_operator_approval(self, aap_id: str) -> None:
        """Méthode utilitaire de test pour simuler le clic humain 'GO'."""
        if aap_id in self._mock_sheet_db:
            self._mock_sheet_db[aap_id]["decision_go"] = "OUI"
            self._mock_sheet_db[aap_id]["status"] = "VALIDE_POUR_PHASE_2"
