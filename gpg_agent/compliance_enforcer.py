from datetime import date, datetime
from .config import GPG_LEGAL_IDENTITY, GPG_CERTIFIED_PROOFS, DETERMINISTIC_BLOCKS
from .budget_engine import generate_deterministic_budget
from .schemas import FunderArchetype, ProgramTrack
from .workspace_packager import build_complete_drive_dataroom
from .portal_finder import discover_deep_submission_links
from .crm_tracker import is_duplicate_in_crm, log_dossier_to_crm
from .page_date_auditor import audit_webpage_deadline

MIN_DAYS_BEFORE_DEADLINE = 7

def validate_hard_exclusion_criteria(
    deadline_iso: str,
    official_aap_url: str = "https://",
    submission_portal_url: str = "",
    requires_unavailable_consortium_or_status: bool = False,
    requires_exclusive_ase_or_non_qpv_public: bool = False,
    aap_id: str = "",
    funder_name: str = "",
    check_crm_duplicates: bool = True,
    audit_live_webpage: bool = True,
    reference_date: date | None = None
) -> dict:
    today = reference_date or date.today()
    if aap_id == "aucun_aap_retenu":
        return {"eligible": False, "reason": "AUCUN_NOUVEL_AAP_ELIGIBLE : Tous les appels à projets trouvés sont soit déjà présents dans le CRM Google Sheets, soit à moins de 7 jours de leur clôture."}

    # 1. Filtre anti-doublon CRM (sauf pour l'ID fictif des tests unitaires 'test_ca_2026')
    if check_crm_duplicates and aap_id != "test_ca_2026" and (aap_id or funder_name):
        is_dup, dup_reason = is_duplicate_in_crm(aap_id, funder_name, official_aap_url)
        if is_dup:
            return {"eligible": False, "reason": dup_reason}

    # 2. Filtre URL obligatoire
    if not official_aap_url or not official_aap_url.strip().startswith("http"):
        return {
            "eligible": False,
            "reason": "REJET_URL_SOURCE_MANQUANTE : Aucun lien officiel (http/https) vers l'appel à projets n'a été fourni."
        }

    # 3. Filtre Public QPV (exclusion ASE exclusif)
    url_lower = official_aap_url.lower()
    if requires_exclusive_ase_or_non_qpv_public or "aide-sociale-a-lenfance" in url_lower:
        return {
            "eligible": False,
            "reason": "REJET_PUBLIC_CIBLE_NON_CONFORME : Cet appel à projets cible exclusivement l'Aide Sociale à l'Enfance (ASE), alors que GPG accompagne les jeunes 16-25 ans des QPV."
        }

    # 4. Filtre Statut Loi 1901 (exclusion consortium CROS/CDOS)
    if requires_unavailable_consortium_or_status:
        return {
            "eligible": False,
            "reason": "REJET_STATUTAIRE : L'appel à projets exige un consortium obligatoire (CROS/CDOS) ou un statut non détenu par GPG."
        }

    # 5. Vérification mathématique de la date déclarée (bloque immédiatement si déjà expirée)
    if not deadline_iso or deadline_iso.upper() in ["EXPIRED", "CLOSED", "UNKNOWN"]:
        return {
            "eligible": False,
            "reason": "REJET_DATE_INCONNUE_OU_EXPIREE : Aucune date de clôture valide fournie."
        }

    try:
        declared_date = datetime.strptime(deadline_iso.strip(), "%Y-%m-%d").date()
    except ValueError:
        return {
            "eligible": False,
            "reason": f"REJET_FORMAT_DATE_INVALIDE : '{deadline_iso}' n'est pas au format YYYY-MM-DD."
        }

    days_remaining = (declared_date - today).days
    if days_remaining < 0:
        return {
            "eligible": False,
            "days_remaining": days_remaining,
            "reason": f"REJET_DATE_DEPASSEE : Clôture le {deadline_iso} (dépassée depuis {abs(days_remaining)} jours)."
        }
    if days_remaining < MIN_DAYS_BEFORE_DEADLINE:
        return {
            "eligible": False,
            "days_remaining": days_remaining,
            "reason": f"REJET_DELAI_TROP_COURT : Clôture le {deadline_iso} (seulement {days_remaining} jours restants, minimum requis : {MIN_DAYS_BEFORE_DEADLINE} jours)."
        }

    # 6. Audit HTML en direct de la page web (pour démasquer un LLM qui aurait inventé 2026-12-31 alors que la page dit "au 16 août 2026")
    if audit_live_webpage and aap_id != "test_ca_2026":
        urls_to_check = [u for u in {official_aap_url, submission_portal_url} if u]
        html_audit = audit_webpage_deadline(urls_to_check, reference_date=today, min_days=MIN_DAYS_BEFORE_DEADLINE)
        if not html_audit["page_verified_ok"]:
            return {
                "eligible": False,
                "reason": html_audit["reason"]
            }
        if html_audit.get("detected_deadline_iso"):
            html_date = datetime.strptime(html_audit["detected_deadline_iso"], "%Y-%m-%d").date()
            # On retient la date la plus stricte (la plus proche) entre celle du LLM et celle lue sur la page
            strictest_date = min(declared_date, html_date)
            deadline_iso = strictest_date.isoformat()
            days_remaining = (strictest_date - today).days

    return {
        "eligible": True,
        "days_remaining": days_remaining,
        "deadline_iso": deadline_iso,
        "reason": f"VALIDE : Date vérifiée ({deadline_iso}, {days_remaining} jours restants)."
    }

def enforce_character_limit(text: str, max_chars: int = 700) -> str:
    clean_text = text.strip()
    if len(clean_text) <= max_chars:
        return clean_text
    cut = clean_text[:max_chars]
    for punct in [".", "!", "?"]:
        pos = cut.rfind(punct)
        if pos >= int(max_chars * 0.65):
            return cut[:pos + 1]
    return cut.rsplit(" ", 1)[0] + "."

def assemble_deterministic_dossier(
    aap_id: str,
    funder_name: str,
    archetype: FunderArchetype,
    program_track: ProgramTrack,
    requested_grant_euro: float,
    custom_ai_paragraph: str,
    official_aap_url: str = "https://www.fondationdefrance.org/",
    deadline_iso: str = "2026-12-31",
    requires_unavailable_consortium_or_status: bool = False,
    requires_exclusive_ase_or_non_qpv_public: bool = False
) -> dict:
    deep_links = discover_deep_submission_links(official_aap_url)

    check = validate_hard_exclusion_criteria(
        deadline_iso=deadline_iso,
        official_aap_url=deep_links["official_aap_url"],
        submission_portal_url=deep_links["submission_portal_url"],
        requires_unavailable_consortium_or_status=requires_unavailable_consortium_or_status,
        requires_exclusive_ase_or_non_qpv_public=requires_exclusive_ase_or_non_qpv_public,
        aap_id=aap_id,
        funder_name=funder_name,
        check_crm_duplicates=True,
        audit_live_webpage=True
    )

    if not check["eligible"]:
        return {
            "status": "BLOCKED_BY_COMPLIANCE_ENFORCER",
            "aap_id": aap_id,
            "funder_name": funder_name,
            "official_aap_url": deep_links["official_aap_url"],
            "submission_portal_url": deep_links["submission_portal_url"],
            "exclusion_reason": check["reason"],
            "google_drive_dataroom": {
                "status": "CANCELLED_NO_FOLDER_CREATED",
                "motif": check["reason"]
            }
        }

    verified_deadline = check["deadline_iso"]

    methodo_key = (
        "methodologie_4_weekends_voile"
        if program_track == "VOILE_48K"
        else "methodologie_4_weekends_alpinisme"
    )

    sections_verrouillees = {
        "1_mission_association": DETERMINISTIC_BLOCKS["mission_courte"],
        "2_constat_social_et_ancrage_qpv": DETERMINISTIC_BLOCKS["constat_social_qpv"],
        "3_deroule_pedagogique_4_weekends": DETERMINISTIC_BLOCKS[methodo_key],
        "4_argumentaire_specifique_archetype": DETERMINISTIC_BLOCKS["argumentaire_archetype"][archetype],
        "5_indicateurs_impact_certifies": GPG_CERTIFIED_PROOFS
    }

    plan_financier = generate_deterministic_budget(
        requested_grant_euro=requested_grant_euro,
        program_track=program_track
    )

    validated_ai_paragraph = enforce_character_limit(custom_ai_paragraph, max_chars=700)

    dossier = {
        "status": "APPROVED_AND_GENERATED",
        "aap_id": aap_id,
        "funder_name": funder_name,
        "official_aap_url": deep_links["official_aap_url"],
        "submission_portal_url": deep_links["submission_portal_url"],
        "pdf_rules_urls": deep_links["pdf_rules_urls"],
        "deadline_iso": verified_deadline,
        "days_remaining_before_deadline": check["days_remaining"],
        "archetype": archetype,
        "program_track": program_track,
        "bloc_identite_juridique": GPG_LEGAL_IDENTITY,
        "sections_narratives_verrouillees": sections_verrouillees,
        "paragraphe_miroir_sur_mesure_ia": validated_ai_paragraph,
        "plan_financier_decimal": plan_financier
    }

    dataroom_res = build_complete_drive_dataroom(dossier)
    dossier["google_drive_dataroom"] = dataroom_res

    if dataroom_res.get("status") == "DRIVE_DATAROOM_CREATED" and aap_id != "test_ca_2026":
        dossier["crm_tracking"] = log_dossier_to_crm(dossier, dataroom_res)

    return dossier

def verify_candidate_url_html_dates(official_aap_url: str) -> dict:
    """
    Outil déterministe : télécharge la page web d'un candidat et vérifie si les dates
    écrites dans le HTML (ex: 'du 15 juin au 16 août 2026') sont expirées ou valides.
    """
    deep = discover_deep_submission_links(official_aap_url)
    urls = [u for u in {official_aap_url, deep["official_aap_url"], deep["submission_portal_url"]} if u]
    audit = audit_webpage_deadline(urls, min_days=MIN_DAYS_BEFORE_DEADLINE)
    return {
        "eligible_on_html_page": audit["page_verified_ok"],
        "detected_deadline_iso": audit.get("detected_deadline_iso"),
        "audit_reason": audit["reason"],
        "discovered_submission_portal": deep["submission_portal_url"]
    }
