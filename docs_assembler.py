import logging
from schemas import FullProposalDocument
from googleapiclient.discovery import build
import google.auth

logger = logging.getLogger("GravirPourGrandir.DocsAssembler")

class GoogleDocsAssembler:
    """Compile les sections narratives et crée un vrai Google Doc."""

    def __init__(self):
        self.creds, _ = google.auth.default(scopes=[
            'https://www.googleapis.com/auth/documents',
            'https://www.googleapis.com/auth/drive'
        ])
        self.docs_service = build('docs', 'v1', credentials=self.creds)
        self.drive_service = build('drive', 'v3', credentials=self.creds)

    def assemble(self, proposal: FullProposalDocument) -> str:
        logger.info(f"=== Création réelle du document Google Docs : {proposal.project_title} ===")
        
        # 1. Création du fichier Google Docs
        file_metadata = {
            'name': f"Candidature Subvention — {proposal.project_title}",
            'mimeType': 'application/vnd.google-apps.document'
        }
        doc_file = self.drive_service.files().create(body=file_metadata, fields='id').execute()
        document_id = doc_file.get('id')

        # 2. Rendre le document accessible à toute personne disposant du lien
        try:
            self.drive_service.permissions().create(
                fileId=document_id,
                body={'type': 'anyone', 'role': 'writer'}
            ).execute()
        except Exception as e:
            logger.warning(f"⚠️ Attribution des permissions Drive : {e}")

        # 3. Insertion du contenu rédigé
        requests = []
        
        title_text = f"{proposal.project_title}\n"
        requests.append({'insertText': {'location': {'index': 1}, 'text': title_text}})
        
        pitch_header = "1. Synthèse Stratégique du Projet\n"
        pitch_body = f"{proposal.executive_pitch}\n\n"
        requests.append({'insertText': {'location': {'index': len(title_text) + 1}, 'text': pitch_header + pitch_body}})
        
        current_pos = len(title_text) + len(pitch_header) + len(pitch_body) + 1
        for section in proposal.narrative_sections:
            header = f"{section.question_label}\n"
            content = f"{section.final_text}\n\n"
            requests.append({'insertText': {'location': {'index': current_pos}, 'text': header + content}})
            current_pos += len(header) + len(content)

        self.docs_service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()
        
        doc_url = f"https://docs.google.com/document/d/{document_id}/edit"
        logger.info(f"✅ Document Google Docs assemblé : {doc_url}")
        return doc_url
