"""
Détecteur de parrainage salarié & Générateur de Kit LinkedIn X-Ray + note d'invitation de 300 caractères.
"""
import re
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup

SPONSORSHIP_KEYWORDS = [
    "parrain", "marraine", "parrainage", "parrainé", "parrainés",
    "collaborateur", "collaboratrice", "salarié", "salarie",
    "correspondant local", "correspondants locaux", "soutenu par un",
    "porté par un salarié", "impliquer un collaborateur"
]

KNOWN_EMPLOYEE_SPONSOR_FUNDERS = [
    "transdev", "decathlon", "décathlon", "vinci", "sncf", "ratp",
    "air france", "edf", "engie", "bouygues", "veolia", "orange",
    "société générale", "societe generale", "bnp", "crédit agricole", "credit agricole"
]

def detect_and_build_sponsorship_kit(funder_name: str, urls: list[str], program_track: str = "ALPINISME_48K") -> dict:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    detected_sentences = []
    funder_lower = (funder_name or "").lower()

    for url in urls:
        if not url or not url.startswith("http"):
            continue
        try:
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            text = re.sub(r"\s+", " ", soup.get_text(separator=" "))
            sentences = re.split(r"(?<=[\.\!\?\n])", text)
            for s in sentences:
                s_low = s.lower()
                if any(k in s_low for k in SPONSORSHIP_KEYWORDS):
                    clean_s = s.strip()
                    if 20 < len(clean_s) < 300 and clean_s not in detected_sentences:
                        detected_sentences.append(clean_s)
        except Exception:
            continue

    is_known_corp = any(c in funder_lower for c in KNOWN_EMPLOYEE_SPONSOR_FUNDERS)
    requires_sponsor = len(detected_sentences) > 0 or is_known_corp

    company_clean = re.sub(r"(?i)\b(fondation|fonds de dotation|fonds|groupe|d'entreprise)\b", "", funder_name or "").strip()
    if not company_clean:
        company_clean = funder_name or "Entreprise"

    sport_kw = "voile OR nautisme" if "VOILE" in program_track else "alpinisme OR montagne OR escalade OR trail"
    xray_query = f'site:fr.linkedin.com/in/ "{company_clean}" ({sport_kw} OR "RSE" OR "Fondation" OR "mécénat" OR "engagement") ("Paris" OR "Lyon" OR "Grenoble")'
    linkedin_search_url = f"https://www.google.com/search?q={quote_plus(xray_query)}"

    linkedin_note_300 = (
        f"Bonjour [Prénom], je suis Tristan Mathon, président co-fondateur de Gravir Pour Grandir (insertion de jeunes 16-25 ans des QPV par l'alpinisme, la voile et le mentorat). "
        f"Nous candidatons à la {funder_name} et cherchons un(e) collaborateur(trice) {company_clean} sensible au sport/montagne pour parrainer notre dossier. Échangeons ?"
    )

    linkedin_followup = (
        f"Merci d'avoir accepté mon invitation ! Avec Gravir Pour Grandir, nous accompagnons des jeunes de 16 à 25 ans issus des Quartiers Prioritaires "
        f"à travers un parcours exigeant de 4 week-ends d'expédition (alpinisme / voile) couplé à un mentorat vers l'emploi (82% de sorties positives). "
        f"Notre dossier pour la {funder_name} est déjà entièrement rédigé et budgété : accepteriez-vous d'y jeter un œil et d'être notre parrain/marraine interne chez {company_clean} ?"
    )

    status_label = (
        "🤝 PARRAINAGE SALARIÉ REQUIS / FORTEMENT RECOMMANDÉ"
        if requires_sponsor
        else "ℹ️ DÉPÔT DIRECT (Parrainage salarié optionnel)"
    )

    proof_excerpt = detected_sentences[0] if detected_sentences else (
        f"Les fondations d'entreprise comme {funder_name} privilégient ou exigent la cooptation par un collaborateur du groupe."
        if requires_sponsor else "Aucune obligation de parrainage salarié détectée sur la page."
    )

    return {
        "requires_employee_sponsor": requires_sponsor,
        "sponsorship_status_label": status_label,
        "html_proof_excerpt": proof_excerpt,
        "company_target": company_clean,
        "linkedin_xray_search_url": linkedin_search_url,
        "linkedin_invite_note_300_chars": linkedin_note_300,
        "linkedin_followup_message": linkedin_followup
    }
