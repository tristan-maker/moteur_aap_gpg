"""
Auditeur HTML de dates réelles — Scanne le code source de la page du financeur pour bloquer les appels clos ou < J+7.
"""
import re
from datetime import date
import requests
from bs4 import BeautifulSoup

FRENCH_MONTHS = {
    "janvier": 1, "janv": 1,
    "fevrier": 2, "février": 2, "fevr": 2, "févr": 2,
    "mars": 3,
    "avril": 4, "avr": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7, "juil": 7,
    "aout": 8, "août": 8,
    "septembre": 9, "sept": 9,
    "octobre": 10, "oct": 10,
    "novembre": 11, "nov": 11,
    "decembre": 12, "décembre": 12, "dec": 12, "déc": 12,
}

CLOSED_PHRASES = [
    "candidatures sont closes",
    "appel à projets est clos",
    "appel a projets est clos",
    "dépôt des dossiers est clos",
    "session est close",
]

def _extract_french_dates_from_text(text: str) -> list[tuple[date, str]]:
    """
    Extrait les dates de clôture en français (ex: 'du 15 juin au 16 août 2026', 'jusqu'au 31 octobre 2026').
    """
    found_dates = []
    clean_text = re.sub(r"\s+", " ", text)
    sentences = re.split(r"(?<=[\.\!\?\n])|\s{2,}", clean_text)

    pattern_words = re.compile(
        r"\b(\d{1,2})(?:er)?\s+(janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)\s+(202[4-9])\b",
        re.IGNORECASE
    )
    pattern_slash = re.compile(r"\b(\d{1,2})/(\d{1,2})/(202[4-9])\b")

    for sent in sentences:
        sent_lower = sent.lower()
        is_deadline_context = any(k in sent_lower for k in [
            "candidature", "dossier", "dépôt", "depot", "limite", "clôture", "cloture",
            "ouvertes du", "ouvert du", "jusqu", "avant le", "date de réception"
        ])
        if not is_deadline_context:
            continue

        for match in pattern_words.finditer(sent):
            day = int(match.group(1))
            month = FRENCH_MONTHS.get(match.group(2).lower())
            year = int(match.group(3))
            if month and 1 <= day <= 31:
                try:
                    found_dates.append((date(year, month, day), sent.strip()[:180]))
                except ValueError:
                    pass

        for match in pattern_slash.finditer(sent):
            day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
            if 1 <= month <= 12 and 1 <= day <= 31:
                try:
                    found_dates.append((date(year, month, day), sent.strip()[:180]))
                except ValueError:
                    pass

    return found_dates

def audit_webpage_deadline(urls: list[str], reference_date: date | None = None, min_days: int = 7) -> dict:
    today = reference_date or date.today()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    all_extracted_dates: list[tuple[date, str]] = []

    for url in urls:
        if not url or not url.startswith("http"):
            continue
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            page_text = soup.get_text(separator=" ")
            text_lower = page_text.lower()

            for closed_kw in CLOSED_PHRASES:
                if closed_kw in text_lower:
                    return {
                        "page_verified_ok": False,
                        "detected_deadline_iso": "CLOSED",
                        "reason": f"REJET_PAGE_OFFICIELLE_CLOSE : La page web ({url}) mentionne explicitement '{closed_kw}'."
                    }

            extracted = _extract_french_dates_from_text(page_text)
            all_extracted_dates.extend(extracted)
        except Exception:
            continue

    if not all_extracted_dates:
        return {
            "page_verified_ok": True,
            "detected_deadline_iso": None,
            "reason": "Aucune date contradictoire détectée dans le HTML."
        }

    all_extracted_dates.sort(key=lambda x: x[0], reverse=True)
    latest_date_on_page, proof_sentence = all_extracted_dates[0]
    days_remaining = (latest_date_on_page - today).days

    if days_remaining < 0:
        return {
            "page_verified_ok": False,
            "detected_deadline_iso": latest_date_on_page.isoformat(),
            "proof_sentence": proof_sentence,
            "reason": (
                f"REJET_DATE_REELLE_DEPASSEE_SUR_SITE : Le site officiel indique une clôture le "
                f"{latest_date_on_page.isoformat()} (dépassée depuis {abs(days_remaining)} jours). "
                f"Extrait officiel : « {proof_sentence} »"
            )
        }

    if days_remaining < min_days:
        return {
            "page_verified_ok": False,
            "detected_deadline_iso": latest_date_on_page.isoformat(),
            "proof_sentence": proof_sentence,
            "reason": (
                f"REJET_DELAI_REEL_TROP_COURT_SUR_SITE : Le site officiel indique une clôture le "
                f"{latest_date_on_page.isoformat()} ({days_remaining} jours restants). "
                f"Extrait officiel : « {proof_sentence} »"
            )
        }

    return {
        "page_verified_ok": True,
        "detected_deadline_iso": latest_date_on_page.isoformat(),
        "proof_sentence": proof_sentence,
        "reason": f"VALIDE_SUR_SITE : Date vérifiée dans le HTML = {latest_date_on_page.isoformat()} ({days_remaining} jours restants)."
    }
