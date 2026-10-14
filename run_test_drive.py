import os
import json
from gpg_agent.workspace_packager import _get_workspace_services
from gpg_agent.compliance_enforcer import assemble_deterministic_dossier

# Force le nouvel ID du dossier 01_CANDIDATURES_AAP_GENERES dans le Drive partagé
os.environ["DRIVE_OUTPUT_PARENT_FOLDER_ID"] = "1-7DrkohVJjLcAgthjPoJ-1HAAxPhixYG"

# Détecte automatiquement l'ID du dossier 00_COFFRE_FORT_ADMIN_GPG
drive, _, _ = _get_workspace_services()
vaults = drive.files().list(
    q="name = '00_COFFRE_FORT_ADMIN_GPG' and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
    supportsAllDrives=True,
    includeItemsFromAllDrives=True,
    fields="files(id, name, driveId)"
).execute().get("files", [])

if vaults:
    vault_id = vaults[0]["id"]
    os.environ["DRIVE_VAULT_FOLDER_ID"] = vault_id
    print(f"Coffre-fort détecté avec ID : {vault_id}")

# Lance la création complète de la Data Room dans le Drive partagé
res = assemble_deterministic_dossier(
    aap_id="credit_agricole_2026",
    funder_name="Fondation Crédit Agricole",
    archetype="FONDATION_BANCAIRE_ECHELLE",
    program_track="PASSAGE_ECHELLE_3_ANS",
    requested_grant_euro=25000.0,
    custom_ai_paragraph="En soutenant Gravir Pour Grandir, la Fondation Crédit Agricole accélère l'insertion socio-professionnelle des jeunes des QPV par l'exigence de la cordée."
)

print(json.dumps(res["google_drive_dataroom"], indent=2, ensure_ascii=False))
