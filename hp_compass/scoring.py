"""HP Compass — Two-Level AHP-FCE Priority Evaluation (Φ₄)

Model §5: 二级模糊综合评价
  Level 1: U₁ (internal urgency) × U₂ (external constraints)
  Level 2: synthesize B₁, B₂ → B → centroid defuzzification → P
  Weights: AHP judgment matrices → square-root method → A₁, A₂, A
"""

from __future__ import annotations

from datetime import date, datetime

from .config import (
    A1_WEIGHTS, A2_WEIGHTS, A2ND_WEIGHTS,
    MEMBERSHIP_PARAMS, MODULE_CRITICALITY, QUANT_VECTOR,
    STAKEHOLDER_VALUE_KEYWORDS,
)
from .schema import HPCard


# ── Factor ordering (U₁: F₁,F₂,F₃; U₂: F₄,F₅,F₆) ──
_F1_IDX = 0  # loop_gap
_F2_IDX = 1  # cross_module_impact
_F3_IDX = 2  # project_criticality
_F4_IDX = 3  # time_urgency
_F5_IDX = 4  # evidence_weakness
_F6_IDX = 5  # stakeholder_value


# ═══════════════════════════════════════════════════════════════
#  Main entry: two-level AHP-FCE scoring
# ═══════════════════════════════════════════════════════════════

def score_priority(
    card: HPCard,
    today: date | None = None,
    deadline: date | None = None,
) -> HPCard:
    today = today or date.today()
    deadline = deadline or date(today.year, 10, 1)

    # ── Step 1: compute six factors ──
    F1 = _compute_F1(card)
    F2 = _compute_F2(card)
    F3 = _compute_F3(card)
    F4 = _compute_F4(today, deadline)
    F5 = _compute_F5(card)
    F6 = _compute_F6(card)

    factors = {
        "loop_gap":              round(F1, 3),
        "cross_module_impact":   round(F2, 3),
        "project_criticality":   round(F3, 3),
        "time_urgency":          round(F4, 3),
        "evidence_weakness":     round(F5, 3),
        "stakeholder_value":     round(F6, 3),
    }
    card.priority_factors = factors

    # ── Step 2: membership degrees → matrices R₁ (3×4) and R₂ (3×4) ──
    R1 = _build_R([F1, F2, F3])
    R2 = _build_R([F4, F5, F6])

    # ── Step 3: Level-1 FCE → B₁, B₂ ──
    B1_raw = _fce_synthesize(A1_WEIGHTS, R1)
    B2_raw = _fce_synthesize(A2_WEIGHTS, R2)

    # Normalize to sum=1 (M(·,+) with normalized weights guarantees this
    # algebraically, but we normalize to absorb float error)
    B1 = _normalize(B1_raw)
    B2 = _normalize(B2_raw)

    card.fce_u1_vector = {f"b1_{j+1}": round(B1[j], 4) for j in range(4)}
    card.fce_u2_vector = {f"b2_{j+1}": round(B2[j], 4) for j in range(4)}

    # ── Step 4: Level-2 FCE → B ──
    R_total = [B1, B2]  # 2×4
    B_raw = _fce_synthesize(A2ND_WEIGHTS, R_total)
    B = _normalize(B_raw)

    card.fce_vector = {f"b{j+1}": round(B[j], 4) for j in range(4)}

    # ── Step 5: centroid defuzzification → P ──
    P = sum(B[j] * QUANT_VECTOR[j] for j in range(4))
    card.priority_score = round(P, 3)

    return card


# ═══════════════════════════════════════════════════════════════
#  Factor computation §5.2
# ═══════════════════════════════════════════════════════════════

def _compute_F1(card: HPCard) -> float:
    """F₁: loop gap — linear decay with ℓ."""
    return (4 - min(max(card.loop_level, 0), 4)) / 4


def _compute_F2(card: HPCard) -> float:
    """F₂: cross-module impact — membership-weighted sum of μ_c.

    Uses the fuzzy membership vector c_i from stage Φ₂, NOT discrete count.
    """
    memberships = card.module_memberships
    if not memberships:
        # fallback: use affected_modules count
        return round(min(1.0, len(card.affected_modules) / 4), 3)
    weighted_sum = sum(memberships.values())
    return round(min(1.0, weighted_sum / 4), 3)


def _compute_F3(card: HPCard) -> float:
    """F₃: project criticality — membership-weighted max κ(c)·μ_c."""
    memberships = card.module_memberships
    if not memberships:
        # fallback
        best = 0.2
        for m in card.affected_modules:
            kappa = MODULE_CRITICALITY.get(m, 0.5)
            if kappa > best:
                best = kappa
        return round(best, 3)
    best = 0.0
    for c_name, mu in memberships.items():
        if mu > 0:
            kappa = MODULE_CRITICALITY.get(c_name, 0.5)
            val = kappa * mu
            if val > best:
                best = val
    return round(best, 3)


def _compute_F4(today: date, deadline: date) -> float:
    """F₄: time urgency — piecewise constant."""
    days = max(0, (deadline - today).days)
    if days >= 120:
        return 0.20
    if days >= 60:
        return 0.45
    if days >= 30:
        return 0.70
    return 1.00


def _compute_F5(card: HPCard) -> float:
    """F₅: evidence weakness — complement of evidence strength."""
    return round(1.0 - card.evidence_strength, 3)


def _compute_F6(card: HPCard) -> float:
    """F₆: stakeholder value — max role value, floor 0.50."""
    text = card.stakeholder + " " + (card.stakeholder_type or "")
    value = 0.50
    for keyword, score in STAKEHOLDER_VALUE_KEYWORDS.items():
        if keyword in text:
            value = max(value, score)
    return round(value, 3)


# ═══════════════════════════════════════════════════════════════
#  Membership function evaluation §5.5–5.6
# ═══════════════════════════════════════════════════════════════

def _membership_degree(F: float, shape_key: str) -> float:
    """Compute r_{ij}(F) for a given membership function shape.

    shapes (a, b, c, d):
      - v1_low:    descending half-trapezoid   r=1 for x≤a, linear decay b→c, r=0 for x≥d
                    actually: [0, 0, 0.25, 0.45] → flat 1 then linear down
      - v2_mid:    triangle [0.25, 0.45, 0.55, 0.75] → up, flat 1, down
      - v3_high:   trapezoid [0.55, 0.75, 0.85, 1.0] → up, flat 1, down
      - v4_urgent: ascending half-trapezoid [0.75, 0.90, 1.0, 1.0] → up then flat 1
    """
    a, b, c, d = MEMBERSHIP_PARAMS[shape_key]

    if shape_key == "v1_low":
        # descending half-trapezoid: r=1 for F≤a(b), linear down to 0 at d(c)
        if F <= b:
            return 1.0
        if F < c:
            return (c - F) / (c - b)
        return 0.0

    elif shape_key == "v2_mid":
        # triangle: up a→b, plateau b→c, down c→d
        if F <= a:
            return 0.0
        if F < b:
            return (F - a) / (b - a)
        if F <= c:
            return 1.0
        if F < d:
            return (d - F) / (d - c)
        return 0.0

    elif shape_key == "v3_high":
        # trapezoid: up a→b, plateau b→c, down c→d
        if F <= a:
            return 0.0
        if F < b:
            return (F - a) / (b - a)
        if F <= c:
            return 1.0
        if F < d:
            return (d - F) / (d - c)
        return 0.0

    elif shape_key == "v4_urgent":
        # ascending half-trapezoid: 0→0, up a→b, r=1 for F≥b(c)
        if F <= a:
            return 0.0
        if F < b:
            return (F - a) / (b - a)
        return 1.0

    return 0.0


def _build_R(factors: list[float]) -> list[list[float]]:
    """Build fuzzy evaluation matrix R (n_factors × 4).

    For each factor F_k, compute membership to 4 evaluation levels.
    """
    shape_keys = ["v1_low", "v2_mid", "v3_high", "v4_urgent"]
    R = []
    for F in factors:
        row = [_membership_degree(F, sk) for sk in shape_keys]
        R.append(row)
    return R


# ═══════════════════════════════════════════════════════════════
#  FCE synthesis operators §5.6–5.8
# ═══════════════════════════════════════════════════════════════

def _fce_synthesize(
    weights: tuple[float, ...],
    R: list[list[float]],
) -> list[float]:
    """M(·,+) weighted average operator: B = A ∘ R.

    b_j = Σ_i a_i · r_ij
    """
    n_factors = len(weights)
    n_levels = len(R[0]) if R else 0
    B = [0.0] * n_levels
    for j in range(n_levels):
        B[j] = sum(weights[i] * R[i][j] for i in range(n_factors))
    return B


def _normalize(vec: list[float]) -> list[float]:
    """Normalize vector to sum to 1."""
    total = sum(vec)
    if total == 0:
        return vec
    return [v / total for v in vec]


# ═══════════════════════════════════════════════════════════════
#  Utility (backward compatible)
# ═══════════════════════════════════════════════════════════════

def parse_deadline(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()
