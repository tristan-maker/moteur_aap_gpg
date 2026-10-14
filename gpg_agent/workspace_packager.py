"""
Assembleur de Data Room Google Workspace (API Drive v3, Docs v1, Sheets v4) + copie des 6 pièces du Coffre-Fort.
"""
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import google.auth
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

WORKSPACE_SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
]

KEY_PATH = Path("/home/tristan/gpg-aap-clean/bot-key.json")
FALLBACK_KEY_PATH = Path(__file__).parent / "bot-key.json"

REQUIRED_ATTACHMENTS_CHECKLIST = [
    "01_Statuts_GPG_Mis_a_jour_Juillet_2026_Signes.pdf",
    "02_Avis_Situation_SIRENE_92385356800015.pdf",
    "03_Recepisse_RNA_W751270417.pdf",
    "04_Rescrit_Fiscal_Interet_General_2025.pdf",
    "05_RIB_Qonto_Signe_Gravir_Pour_Grandir.pdf",
    "06_Comptes_Annuels_2025_et_Rapport_CAC_Cofirec.pdf",
    "07_PV_AG_et_CA_08_Juillet_2026_Signes.pdf"
]

def _get_workspace_services():
    if KEY_PATH.exists():
        creds = service_account.Credentials.from_service_account_file(str(KEY_PATH), scopes=WORKSPACE_SCOPES)
    elif FALLBACK_KEY_PATH.exists():
        creds = service_account.Credentials.from_service_account_file(str(FALLBACK_KEY_PATH), scopes=WORKSPACE_SCOPES)
    else:
        creds, _ = google.auth.default(scopes=WORKSPACE_SCOPES)

    drive_service = build("drive", "v3", credentials=creds, cache_discovery=False)
    docs_service = build("docs", "v1", credentials=creds, cache_discovery=False)
    sheets_service = build("sheets", "v4", credentials=creds, cache_discovery=False)
    return drive_service, docs_service, sheets_service

def build_complete_drive_dataroom(dossier: dict) -> dict:
    """Crée la Data Room Google Drive avec le lien du guichet de dépôt et le lien du règlement."""
    vault_folder_id = os.environ.get("DRIVE_VAULT_FOLDER_ID", "1zCnczHgBQW0Zk6FdcctWWjl6dUmcvBuN")
    parent_folder_id = os.environ.get("DRIVE_OUTPUT_PARENT_FOLDER_ID", "1-7DrkohVJjLcAgthjPoJ-1HAAxPhixYG")

    try:
        drive_service, docs_service, sheets_service = _get_workspace_services()
        date_str = datetime.now().strftime("%Y-%m-%d")
        deadline_str = dossier.get("deadline_iso", "N/A")
        folder_name = f"[{date_str}] {dossier['funder_name']} (Clôture {deadline_str})"

        # 1. Création du dossier principal dans 01_CANDIDATURES_AAP_GENERES
        folder_meta = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_folder_id]
        }
        created_folder = drive_service.files().create(
            body=folder_meta, fields="id, webViewLink", supportsAllDrives=True
        ).execute()
        app_folder_id = created_folder["id"]
        app_folder_url = created_folder["webViewLink"]

        # 2. Création du Google Docs avec les 2 URLs (Guichet de dépôt + Règlement) tout en haut
        doc_meta = {
            "name": f"01_Dossier_Candidature_{dossier['funder_name']}_GPG",
            "mimeType": "application/vnd.google-apps.document",
            "parents": [app_folder_id]
        }
        created_doc = drive_service.files().create(
            body=doc_meta, fields="id, webViewLink", supportsAllDrives=True
        ).execute()
        doc_id = created_doc["id"]
        doc_url = created_doc["webViewLink"]

        id_bloc = dossier["bloc_identite_juridique"]
        sec = dossier["sections_narratives_verrouillees"]
        fin = dossier["plan_financier_decimal"]
        source_url = dossier.get("official_aap_url", "Non renseigné")
        portal_url = dossier.get("submission_portal_url", source_url)
        days_left = dossier.get("days_remaining_before_deadline", "N/A")

        full_doc_text = (
            f"DOSSIER DE DEMANDE DE SUBVENTION / MÉCÉNAT — {dossier['funder_name'].upper()}\n"
            f"================================================================================\n"
            f"🚀 GUICHET DIRECT POUR DÉPOSER LE DOSSIER :\n"
            f"👉 {portal_url}\n\n"
            f"📖 PAGE OFFICIELLE DE L'APPEL À PROJETS (RÈGLEMENT & CRITÈRES) :\n"
            f"👉 {source_url}\n\n"
            f"📅 DATE LIMITE DE DÉPÔT : {deadline_str} ({days_left} jours restants)\n"
            f"📊 GRILLE BUDGÉTAIRE APPLIQUÉE : {dossier['program_track']} | Généré le : {date_str}\n"
            f"================================================================================\n\n"
            f"1. IDENTITÉ JURIDIQUE, FISCALE & BANCAIRE (CERTIFIÉE)\n"
            f"• Nom : {id_bloc['nom']} ({id_bloc['forme_juridique']})\n"
            f"• SIRET : {id_bloc['siret']} | RNA : {id_bloc['rna']} | APE : {id_bloc['code_ape']}\n"
            f"• Siège social : {id_bloc['siege_social']}\n"
            f"• Statut fiscal : {id_bloc['rescrit_fiscal']}\n"
            f"• Gouvernance : {id_bloc['gouvernance_bureau']}\n"
            f"• Audit des comptes : {id_bloc['commissaire_aux_comptes']}\n"
            f"• Coordonnées bancaires : {id_bloc['iban_qonto']}\n\n"
            f"2. POURQUOI CE PARTENARIAT AVEC {dossier['funder_name'].upper()} FAIT SENS\n"
            f"{dossier['paragraphe_miroir_sur_mesure_ia']}\n\n"
            f"3. MISSION DE L'ASSOCIATION\n"
            f"{sec['1_mission_association']}\n\n"
            f"4. CONSTAT SOCIAL & ANCRAGE QPV (« LE DERNIER KILOMÈTRE »)\n"
            f"{sec['2_constat_social_et_ancrage_qpv']}\n\n"
            f"5. DÉROULÉ OPÉRATIONNEL SUR 12 MOIS (4 WEEK-ENDS D'EXPÉDITION)\n"
            f"{sec['3_deroule_pedagogique_4_weekends']}\n\n"
            f"6. SOLIDITÉ DU MODÈLE & IMPACT SCIENTIFIQUE\n"
            f"{sec['4_argumentaire_specifique_archetype']}\n\n"
            f"7. SYNTHÈSE BUDGÉTAIRE\n"
            f"• Coût total du projet : {fin['cout_total_projet_euro']:.2f} €\n"
            f"• Montant sollicité : {fin['montant_sollicite_euro']:.2f} € ({fin['poids_subvention_pct']})\n"
            f"• Co-financements acquis : {fin['cofinancement_acquis_euro']:.2f} € ({fin['principaux_cofinanceurs']})\n"
            f"• Contributions volontaires en nature : {fin['contributions_volontaires_en_nature_euro']:.2f} €\n"
        )

        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": [{"insertText": {"location": {"index": 1}, "text": full_doc_text}}]}
        ).execute()

        # 3. Création du Google Sheets avec les 2 URLs en en-tête
        sheet_meta = {
            "name": f"02_Budget_Previsionnel_{dossier['funder_name']}_GPG",
            "mimeType": "application/vnd.google-apps.spreadsheet",
            "parents": [app_folder_id]
        }
        created_sheet = drive_service.files().create(
            body=sheet_meta, fields="id, webViewLink", supportsAllDrives=True
        ).execute()
        sheet_id = created_sheet["id"]
        sheet_url = created_sheet["webViewLink"]

        rows = [
            ["BUDGET PRÉVISIONNEL CERTIFIÉ — GRAVIR POUR GRANDIR", "", "", ""],
            ["Financeur cible", dossier["funder_name"], "Date limite de dépôt", deadline_str],
            ["Guichet de dépôt direct", portal_url, "Grille appliquée", fin["grille_utilisee"]],
            ["Page d'info de l'AAP", source_url, "SIRET", id_bloc["siret"]],
            ["", "", "", ""],
            ["Poste de dépense", "Coût Total (€)", "Subvention Sollicitée (€)", "Co-financement Acquis (€)"]
        ]
        for line in fin["lignes_budgetaires"]:
            rows.append([
                line["poste"],
                line["montant_total_euro"],
                line["subvention_sollicitee_euro"],
                line["cofinancement_acquis_euro"]
            ])
        rows.append(["", "", "", ""])
        rows.append([
            "TOTAL PROJET (ÉQUILIBRÉ AU CENTIME)",
            fin["cout_total_projet_euro"],
            fin["montant_sollicite_euro"],
            fin["cofinancement_acquis_euro"]
        ])

        sheets_service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range="A1",
            valueInputOption="USER_ENTERED",
            body={"values": rows}
        ).execute()

        # 4. Création du sous-dossier des pièces justificatives et copie du Coffre-Fort
        justif_meta = {
            "name": "03_Pieces_Justificatives_Officielles_A_Joindre",
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [app_folder_id]
        }
        justif_folder = drive_service.files().create(
            body=justif_meta, fields="id", supportsAllDrives=True
        ).execute()
        justif_folder_id = justif_folder["id"]

        vault_files = drive_service.files().list(
            q=f"'{vault_folder_id}' in parents and trashed = false",
            fields="files(id, name, mimeType)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute().get("files", [])

        copied_files = []
        for f in vault_files:
            if f["mimeType"] != "application/vnd.google-apps.folder":
                copied = drive_service.files().copy(
                    fileId=f["id"],
                    body={"name": f["name"], "parents": [justif_folder_id]},
                    fields="id, name",
                    supportsAllDrives=True
                ).execute()
                copied_files.append(copied["name"])

        return {
            "status": "DRIVE_DATAROOM_CREATED",
            "guichet_depot_direct_url": portal_url,
            "page_info_aap_url": source_url,
            "date_limite_depot": deadline_str,
            "jours_restants": days_left,
            "dossier_drive_url": app_folder_url,
            "google_docs_candidature_url": doc_url,
            "google_sheets_budget_url": sheet_url,
            "justificatifs_copies_depuis_coffre_fort": copied_files
        }

    except Exception as exc:
        return {
            "status": "DRIVE_ERROR",
            "error_detail": str(exc)
        }
