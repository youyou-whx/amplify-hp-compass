from __future__ import annotations

from .config import EVIDENCE_KEYWORDS
from .schema import HPCard


STATUS_NAMES = {
    0: "L0_Recorded",
    1: "L1_Interpreted",
    2: "L2_Actioned",
    3: "L3_Evidenced",
    4: "L4_Returned",
}


def assign_loop_status(card: HPCard) -> HPCard:
    level = 0
    if card.feedback.strip():
        level = 1
    if card.categories or card.affected_modules:
        level = max(level, 1)
    if card.project_action.strip():
        level = max(level, 2)
    card.evidence_strength = calculate_evidence_strength(card.evidence)
    if card.evidence and card.evidence_strength > 0:
        level = max(level, 3)
    if card.returned:
        level = 4

    card.loop_level = level
    card.loop_status = STATUS_NAMES[level]
    return card


def calculate_evidence_strength(evidence_items: list[str]) -> float:
    if not evidence_items:
        return 0.0
    scores: list[float] = []
    for item in evidence_items:
        score = 0.35
        for keyword, weight in EVIDENCE_KEYWORDS.items():
            if keyword.lower() in item.lower():
                score = max(score, weight)
        scores.append(score)
    return round(min(1.0, sum(scores) / max(1, len(scores))), 3)

