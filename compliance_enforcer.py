import logging
from typing import Dict
from schemas import FullProposalDocument

logger = logging.getLogger("GravirPourGrandir.Compliance")

def enforce_character_limits(
    proposal: FullProposalDocument, 
    limits: Dict[str, int]
) -> FullProposalDocument:
    """
    Vérifie et applique les limites de caractères sur les sections narratives.
    Conformément à la DAA : troncature déterministe si dépassement léger.
    """
    for section in proposal.narrative_sections:
        limit = limits.get(section.field_id)
        if limit and len(section.final_text) > limit:
            logger.warning(f"Dépassement détecté pour {section.field_id} : {len(section.final_text)}/{limit}")
            
            # Troncature déterministe simple (DAA: < 5%)
            truncated = section.final_text[:limit].rsplit(' ', 1)[0]
            if not truncated.endswith(('.', '!', '?')):
                truncated += "..."
            
            section.final_text = truncated
            section.character_count = len(truncated)
            
    return proposal