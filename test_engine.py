from gpg_agent.budget_engine import generate_deterministic_budget
from gpg_agent.compliance_enforcer import assemble_deterministic_dossier

def test_all_budget_matrices_balance_to_the_cent():
    for track, expected_total in [
        ("ALPINISME_48K", 48000.0),
        ("ALPINISME_COMPLET_54K", 54000.0),
        ("VOILE_48K", 48000.0),
        ("PASSAGE_ECHELLE_3_ANS", 103000.0),
    ]:
        plan = generate_deterministic_budget(requested_grant_euro=20000.0, program_track=track)
        assert plan["cout_total_projet_euro"] == expected_total
        assert plan["montant_sollicite_euro"] + plan["cofinancement_acquis_euro"] == expected_total
        sum_lines_grant = round(sum(l["subvention_sollicitee_euro"] for l in plan["lignes_budgetaires"]), 2)
        assert sum_lines_grant == 20000.0

def test_deterministic_dossier_assembly():
    dossier = assemble_deterministic_dossier(
        aap_id="test_ca_2026",
        funder_name="Fondation Crédit Agricole",
        archetype="FONDATION_BANCAIRE_ECHELLE",
        program_track="PASSAGE_ECHELLE_3_ANS",
        requested_grant_euro=25000.0,
        custom_ai_paragraph="Alignement parfait avec l'insertion des jeunes sur nos territoires."
    )
    assert dossier["bloc_identite_juridique"]["siret"] == "923 853 568 00015"
    assert dossier["plan_financier_decimal"]["montant_sollicite_euro"] == 25000.0

def test_expired_or_too_close_deadline_blocks_drive_creation():
    # Cas 1 : Date déjà dépassée (ex: mars 2026) -> DOIT BLOQUER
    blocked_past = assemble_deterministic_dossier(
        aap_id="fdva_2026_clos",
        funder_name="FDVA 2026",
        archetype="SUBVENTION_PUBLIQUE",
        program_track="ALPINISME_48K",
        requested_grant_euro=15000.0,
        custom_ai_paragraph="Test",
        deadline_iso="2026-03-15"
    )
    assert blocked_past["status"] == "BLOCKED_BY_COMPLIANCE_ENFORCER"
    assert blocked_past["google_drive_dataroom"]["status"] == "CANCELLED_NO_FOLDER_CREATED"

    # Cas 2 : Consortium CROS/CDOS obligatoire -> DOIT BLOQUER
    blocked_consortium = assemble_deterministic_dossier(
        aap_id="socio_sport_2026",
        funder_name="Ministère des Sports",
        archetype="SUBVENTION_PUBLIQUE",
        program_track="ALPINISME_48K",
        requested_grant_euro=25000.0,
        custom_ai_paragraph="Test",
        deadline_iso="2026-11-30",
        requires_unavailable_consortium_or_status=True
    )
    assert blocked_consortium["status"] == "BLOCKED_BY_COMPLIANCE_ENFORCER"

def test_ase_exclusive_public_blocks_drive_creation():
    blocked_ase = assemble_deterministic_dossier(
        aap_id="ca_ase_2026",
        funder_name="Fondation Crédit Agricole ASE",
        archetype="FONDATION_BANCAIRE_ECHELLE",
        program_track="ALPINISME_48K",
        requested_grant_euro=15000.0,
        custom_ai_paragraph="Test",
        official_aap_url="https://www.fondation-ca-solidaritedeveloppement.org/actu/la-fondation-lance-son-deuxieme-appel-a-projets-en-faveur-des-jeunes-accompagnes-par-laide-sociale-a-lenfance/",
        deadline_iso="2026-11-09",
        requires_exclusive_ase_or_non_qpv_public=True
    )
    assert blocked_ase["status"] == "BLOCKED_BY_COMPLIANCE_ENFORCER"
    assert "REJET_PUBLIC_CIBLE_NON_CONFORME" in blocked_ase["exclusion_reason"]

def test_crm_duplicate_blocks_drive_creation():
    blocked_dup = assemble_deterministic_dossier(
        aap_id="fondation_transdev_2026_2027",
        funder_name="Fondation Transdev",
        archetype="ENTREPRISE_RSE_RH",
        program_track="ALPINISME_48K",
        requested_grant_euro=12000.0,
        custom_ai_paragraph="Test doublon",
        official_aap_url="https://www.avise.org/actualite/lappel-projets-2026-2027-de-la-fondation-transdev-pour-la-mobilite-sociale",
        deadline_iso="2026-10-31"
    )
    assert blocked_dup["status"] == "BLOCKED_BY_COMPLIANCE_ENFORCER"
    assert "REJET_DOUBLON_CRM" in blocked_dup["exclusion_reason"]
from gpg_agent.page_date_auditor import _extract_french_dates_from_text

def test_html_auditor_catches_august_16_2026_expired_window():
    html_text = "Candidatures 2026-2027 : Les candidatures sont ouvertes du 15 juin au 16 août 2026 à minuit (date de réception du mail faisant foi)."
    extracted = _extract_french_dates_from_text(html_text)
    assert len(extracted) >= 1
    latest_date = sorted(extracted, key=lambda x: x[0], reverse=True)[0][0]
    assert latest_date.isoformat() == "2026-08-16"
