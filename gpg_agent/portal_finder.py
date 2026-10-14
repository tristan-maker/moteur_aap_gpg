"""
Chasseur de guichet officiel — Traverse les annuaires relais (Avise, Carenews) pour extraire le vrai lien de dépôt et les PDF.
"""
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

RELAY_DOMAINS = [
    "avise.org",
    "carenews.com",
    "associations.gouv.fr",
    "centre-francais-fondations.org",
    "fonda.asso.fr",
    "ess-france.org"
]

SUBMISSION_URL_KEYWORDS = [
    "deposer-un-projet",
    "deposer-un-dossier",
    "deposer-votre-projet",
    "soumettre-un-projet",
    "candidater",
    "optimytool",
    "optimy",
    "demarches-simplifiees.fr",
    "plateforme",
    "formulaire"
]

SUBMISSION_TEXT_KEYWORDS = [
    "déposer un projet",
    "déposer un dossier",
    "déposer votre demande",
    "accéder à la plateforme",
    "démarrer le questionnaire",
    "déposer ma candidature",
    "candidater",
    "postuler"
]

AAP_PAGE_KEYWORDS = [
    "appel-a-projets",
    "appel-a-projet",
    "lance-son-appel",
    "fondation",
    "mecenat",
    "soutenir"
]

def _scan_single_page(url: str, headers: dict) -> tuple[list, list, list, list]:
    """Scanne une page et retourne (subs, aaps, pdfs, external_funder_links)."""
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return [], [], [], []
    except Exception:
        return [], [], [], []

    soup = BeautifulSoup(resp.text, "html.parser")
    base_domain = urlparse(url).netloc.lower()
    is_relay = any(r in base_domain for r in RELAY_DOMAINS)

    subs, aaps, pdfs, externals = [], [], [], []

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        full_url = urljoin(url, href)
        text = (a_tag.get_text() or "").strip().lower()
        url_lower = full_url.lower()
        link_domain = urlparse(full_url).netloc.lower()

        if any(x in url_lower for x in [
            "mailto:", "tel:", "javascript:", "linkedin.", "facebook.",
            "twitter.", "x.com", "instagram.", "youtube.", "google.com"
        ]):
            continue

        if url_lower.endswith(".pdf") and full_url not in pdfs:
            pdfs.append(full_url)

        # Si on est sur un site relais (ex: avise.org), tout lien sortant vers un autre site est un candidat "vrai site de la fondation"
        if is_relay and link_domain and not any(r in link_domain for r in RELAY_DOMAINS):
            score_ext = 10
            if any(k in url_lower or k in text for k in ["fondation", "deposer", "appel", "projet", "site", "accéder", "en savoir plus"]):
                score_ext += 20
            externals.append((score_ext, full_url))

        # On ne considère jamais une page interne d'avise.org comme un vrai guichet de dépôt !
        if not any(r in link_domain for r in RELAY_DOMAINS):
            score_sub = 0
            if any(k in url_lower for k in SUBMISSION_URL_KEYWORDS):
                score_sub += 25
            if any(k in text for k in SUBMISSION_TEXT_KEYWORDS):
                score_sub += 20
            if score_sub > 0:
                subs.append((score_sub, full_url))

            score_aap = 0
            if any(k in url_lower for k in AAP_PAGE_KEYWORDS):
                score_aap += 15
            if any(k in text for k in ["appel à projets", "critères", "éligibilité", "règlement"]):
                score_aap += 10
            if score_aap > 0:
                aaps.append((score_aap, full_url))

    return subs, aaps, pdfs, externals

def discover_deep_submission_links(start_url: str) -> dict:
    """
    Si start_url est un site relais (ex: avise.org), traverse jusqu'au vrai site de la fondation,
    puis extrait :
    - official_aap_url (ex: https://fondation.transdev.com/la-fondation-transdev-lance-son-appel-a-projets-2026-2027/)
    - submission_portal_url (ex: https://fondation.transdev.com/deposer-un-projet/)
    """
    if not start_url or not start_url.startswith("http"):
        return {
            "official_aap_url": start_url,
            "submission_portal_url": start_url,
            "pdf_rules_urls": [],
            "scan_status": "INVALID_URL"
        }

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    subs, aaps, pdfs, externals = _scan_single_page(start_url, headers)

    current_best_base = start_url

    # Saut 1 : Si on était sur avise.org et qu'on a trouvé le site externe de la Fondation, on va le scanner !
    if externals:
        externals.sort(key=lambda x: x[0], reverse=True)
        funder_site_url = externals[0][1]
        current_best_base = funder_site_url
        s2, a2, p2, _ = _scan_single_page(funder_site_url, headers)
        subs.extend(s2)
        aaps.extend(a2)
        pdfs.extend(p2)

    # Saut 2 : Si on a trouvé la page d'appel à projets sur le site de la fondation, on la scanne aussi pour trouver le bouton "Déposer un projet"
    if aaps:
        aaps.sort(key=lambda x: x[0], reverse=True)
        best_aap_page = aaps[0][1]
        s3, _, p3, _ = _scan_single_page(best_aap_page, headers)
        subs.extend(s3)
        pdfs.extend(p3)

    subs.sort(key=lambda x: x[0], reverse=True)
    aaps.sort(key=lambda x: x[0], reverse=True)

    best_submission_url = subs[0][1] if subs else (aaps[0][1] if aaps else current_best_base)
    best_aap_url = aaps[0][1] if aaps else current_best_base

    return {
        "official_aap_url": best_aap_url,
        "submission_portal_url": best_submission_url,
        "pdf_rules_urls": list(dict.fromkeys(pdfs))[:3],
        "scan_status": "DEEP_LINKS_EXTRACTED"
    }
