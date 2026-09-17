import json
import os
from typing import List
from config import logger
from schemas import DiscoveredUrlCandidate

class CrawlFrontierManager:
    """Gère la déduplication et l'antériorité des opportunités d'appels à projets."""
    
    def __init__(self, db_path: str = "/home/tristan/processed_urls.json"):
        self.db_path = db_path
        self.processed_urls = self._load_db()

    def _load_db(self) -> dict:
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erreur lors du chargement de la frontier locale: {e}")
        return {}

    def _save_db(self):
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.processed_urls, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la frontier locale: {e}")

    def filter_fresh_urls(self, candidates: List[DiscoveredUrlCandidate]) -> List[DiscoveredUrlCandidate]:
        """Filtre déterministement les URLs pour ne conserver que les nouvelles opportunités."""
        fresh = []
        for candidate in candidates:
            if candidate.url not in self.processed_urls:
                fresh.append(candidate)
        return fresh

    def mark_as_processed(self, url: str, aap_id: str):
        """Enregistre l'URL pour éviter toute ré-inférence ou double traitement FinOps."""
        self.processed_urls[url] = {
            "aap_id": aap_id,
            "timestamp": os.environ.get("CURRENT_TIME", "2026")
        }
        self._save_db()