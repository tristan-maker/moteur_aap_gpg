from config import logger, DOCS_FOLDER_ID
from schemas import FullProposalDocument
from googleapiclient.discovery import build
import google.auth

class GoogleDocsAssembler:
    """Compile les sections narratives et les tableaux financiers au format corporate."""

    def __init__(self):
        self.creds, _ = google.auth.default()
        self.docs_service = build('docs', 'v1', credentials=self.creds)
        self.drive_service = build('drive', 'v3', credentials=self.creds)

    def assemble(self, proposal: FullProposalDocument) -> str:
        """Génère le document Google Docs réel avec mise en page corporate."""
        logger.info(f"=== [GOOGLE DOCS ENGINE] Assemblage du dossier : {proposal.project_title} ===")
        
        # 1. Création du document via Drive API pour spécifier le dossier parent
        file_metadata = {
            'name': f"Candidature Subvention - {proposal.project_title}",
            'mimeType': 'application/vnd.google-apps.document'
        }
        if DOCS_FOLDER_ID:
            file_metadata['parents'] = [DOCS_FOLDER_ID]
            
        doc_file = self.drive_service.files().create(body=file_metadata, fields='id').execute()
        document_id = doc_file.get('id')
        
        # 2. Construction de la pile de requêtes batchUpdate
        requests = []
        
        # Insertion et style du Titre Principal (Heading 1)
        title_text = f"{proposal.project_title}\n"
        requests.append({'insertText': {'location': {'index': 1}, 'text': title_text}})
        requests.append({'updateParagraphStyle': {
            'range': {'startIndex': 1, 'endIndex': len(title_text)},
            'paragraphStyle': {'namedStyleType': 'HEADING_1'},
            'fields': 'namedStyleType'
        }})
        
        # Synthèse du Projet (Heading 2)
        current_pos = len(title_text) + 1
        pitch_header = "Synthèse Stratégique du Projet\n"
        requests.append({'insertText': {'location': {'index': current_pos}, 'text': pitch_header}})
        requests.append({'updateParagraphStyle': {
            'range': {'startIndex': current_pos, 'endIndex': current_pos + len(pitch_header)},
            'paragraphStyle': {'namedStyleType': 'HEADING_2'},
            'fields': 'namedStyleType'
        }})
        current_pos += len(pitch_header)
        
        pitch_body = f"{proposal.executive_pitch}\n\n"
        requests.append({'insertText': {'location': {'index': current_pos}, 'text': pitch_body}})
        current_pos += len(pitch_body)
        
        # Itération sur les sections narratives (Titre de question + Réponse)
        for section in proposal.narrative_sections:
            header = f"{section.question_label}\n"
            requests.append({'insertText': {'location': {'index': current_pos}, 'text': header}})
            requests.append({'updateParagraphStyle': {
                'range': {'startIndex': current_pos, 'endIndex': current_pos + len(header)},
                'paragraphStyle': {'namedStyleType': 'HEADING_2'},
                'fields': 'namedStyleType'
            }})
            current_pos += len(header)
            
            content = f"{section.final_text}\n\n"
            requests.append({'insertText': {'location': {'index': current_pos}, 'text': content}})
            current_pos += len(content)

        # 3. Exécution de la mise à jour
        try:
            self.docs_service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()
            url = f"https://docs.google.com/document/d/{document_id}/edit"
            logger.info(f"✅ Document Google Docs assemblé : {url}")
            return url
        except Exception as e:
            logger.error(f"Erreur lors de l'assemblage Google Docs : {e}")
            return f"Erreur d'assemblage : {document_id}"