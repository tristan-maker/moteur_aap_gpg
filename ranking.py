from decimal import Decimal
from typing import List, Tuple
from schemas import AAPRawMetadata, AAPStrategicScore


def calculate_budget_score(grant_ceiling: Decimal, max_capacity: Decimal = Decimal("400000.00")) -> float:
    """Calcule un score budgétaire normalisé entre 0.0 et 1.0."""
    if grant_ceiling is None or grant_ceiling <= Decimal("0.00"):
        return 0.5
    ratio = float(grant_ceiling / max_capacity)
    return min(ratio, 1.0)


def compute_composite_score(fit_score: float, budget_score: float) -> float:
    """Calcule le score composite déterministe S_score = 0.6 * S_fit + 0.4 * S_budget."""
    return round((0.6 * fit_score) + (0.4 * budget_score), 4)


def rank_and_select_top_5(
    candidates: List[Tuple[AAPRawMetadata, AAPStrategicScore]]
) -> List[Tuple[AAPRawMetadata, AAPStrategicScore, float]]:
    """Trie les opportunités selon S_score et extrait le Top 5 strict."""
    scored_list = []
    for metadata, strategic_score in candidates:
        b_score = calculate_budget_score(metadata.extracted_grant_ceiling)
        c_score = compute_composite_score(strategic_score.strategic_fit_score, b_score)
        scored_list.append((metadata, strategic_score, c_score))
    
    sorted_candidates = sorted(scored_list, key=lambda x: x[2], reverse=True)
    return sorted_candidates[:5]
