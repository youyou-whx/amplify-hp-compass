"""HP Compass — Fuzzy Membership Classification (Φ₂)

Model §4: 升半梯形隶属函数 μ_c(h_c)
  h_c = |M_c(T*)| / |K_c|  — hit density
  μ_c(h_c) ∈ [0,1]         — fuzzy membership degree
  Output: 9-dim membership vector c_i = (μ_1, …, μ_9)
"""

from __future__ import annotations

from .config import CATEGORIES, MODULE_THRESHOLDS
from .schema import Classification, HPCard


def classify_card(card: HPCard, min_score: float = 0.0) -> HPCard:
    """Compute fuzzy membership vector for all 9 modules.

    For each module c:
      1. Concatenate all text fields → T*
      2. Count keyword hits M_c(T*)
      3. Compute hit density h_c = |M_c| / |K_c|
      4. Apply trapezoidal membership μ_c(h_c; α_c, β_c)
      5. Store full 9-dim vector in card.module_memberships

    Affected modules = top-5 by μ_c (≥ 0.01).
    """
    text = "\n".join([
        card.stakeholder,
        card.stakeholder_type or "",
        card.initial_question,
        card.feedback,
        card.project_action,
        " ".join(card.evidence),
    ])

    classifications: list[Classification] = []
    memberships: dict[str, float] = {}

    for category, terms in CATEGORIES.items():
        matched = [term for term in terms if term.lower() in text.lower()]
        h_c = len(matched) / max(1, len(terms))  # hit density

        # Trapezoidal membership with module-specific (α_c, β_c)
        alpha_c, beta_c = MODULE_THRESHOLDS.get(category, (0.10, 0.33))
        mu_c = _trapezoidal_membership(h_c, alpha_c, beta_c)

        memberships[category] = round(mu_c, 3)

        if mu_c >= min_score:
            classifications.append(
                Classification(
                    category=category,
                    score=round(mu_c, 3),
                    matched_terms=matched,
                )
            )

    # Sort by membership descending, keep top 5 as affected modules
    classifications.sort(key=lambda item: item.score, reverse=True)
    card.categories = [c for c in classifications[:5] if c.score >= 0.01]
    card.affected_modules = [item.category for item in card.categories]
    card.module_memberships = memberships

    return card


def _trapezoidal_membership(h: float, alpha: float, beta: float) -> float:
    """Ascending half-trapezoid membership function.

    μ_c(h) = 0,                 h < α
             (h-α)/(β-α),      α ≤ h < β
             1,                 h ≥ β
    """
    if h < alpha:
        return 0.0
    if h < beta:
        return (h - alpha) / (beta - alpha)
    return 1.0


def low_confidence(card: HPCard, threshold: float = 0.10) -> bool:
    """Check if no module has meaningful membership."""
    return not card.categories or card.categories[0].score < threshold
