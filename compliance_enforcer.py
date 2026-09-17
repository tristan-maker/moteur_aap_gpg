from typing import Dict
from schemas import FullProposalDocument, NarrativeResponseItem


def truncate_at_last_punctuation(text: str, limit: int) -> str:
    """Tronque déterministement le texte au dernier signe de ponctuation fort en cas de dépassement mineur (<= 5%)."""
    if len(text) <= limit:
        return text

    truncated = text[:limit]
    last_punct = max(
        truncated.rfind("."),
        truncated.rfind("!"),
        truncated.rfind("?"),
    )

    if last_punct > 0:
        return truncated[: last_punct + 1]

    return truncated.rstrip() + "."


def enforce_character_limits(
    proposal: FullProposalDocument,
    field_limits: Dict[str, int],
) -> FullProposalDocument:
    """Valide et ajuste le nombre de caractères de chaque section narrative."""
    validated_sections = []

    for item in proposal.narrative_sections:
        limit = field_limits.get(item.field_id)
        current_text = item.final_text

        if limit and len(current_text) > limit:
            overflow_percentage = ((len(current_text) - limit) / limit) * 100

            if overflow_percentage <= 5.0:
                current_text = truncate_at_last_punctuation(current_text, limit)
            else:
                current_text = truncate_at_last_punctuation(current_text, limit)

        validated_item = NarrativeResponseItem(
            field_id=item.field_id,
            question_label=item.question_label,
            final_text=current_text,
            character_count=len(current_text),
            referenced_partners=item.referenced_partners,
        )
        validated_sections.append(validated_item)

    proposal.narrative_sections = validated_sections
    return proposal
