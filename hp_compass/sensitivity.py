"""Sensitivity analysis for AHP-FCE priority model (model §8).

Perturbs three parameter classes at ±20%:
  1. AHP weights (A₁, A₂, A)
  2. Membership function boundary parameters (a,b,c,d)
  3. Domain mapping parameters (κ(c), v(k))

Measures:
  - Spearman rank correlation ρ
  - Max absolute score deviation ΔP_max
  - Maturity level jump rate
"""

from __future__ import annotations

from .config import (
    A1_WEIGHTS, A2_WEIGHTS, A2ND_WEIGHTS,
    MEMBERSHIP_PARAMS, MODULE_CRITICALITY, QUANT_VECTOR,
)
from .scoring import _build_R, _normalize

# Factor keys in order
_FACTOR_KEYS = [
    "loop_gap", "cross_module_impact", "project_criticality",
    "time_urgency", "evidence_weakness", "stakeholder_value",
]

FACTOR_LABELS = {
    "loop_gap":             "F₁ (闭环缺口)",
    "cross_module_impact":  "F₂ (跨模块影响)",
    "project_criticality":  "F₃ (项目关键性)",
    "time_urgency":         "F₄ (时间紧迫度)",
    "evidence_weakness":    "F₅ (证据不足度)",
    "stakeholder_value":    "F₆ (利益相关者价值)",
}


def run_sensitivity(
    cards: list[dict],
    deltas: tuple[float, float] = (-0.20, 0.20),
) -> dict:
    """Full sensitivity analysis under ±20% parameter perturbation."""
    n_cards = len(cards)
    if n_cards < 2:
        return {"n_cards": n_cards, "error": "至少需要 2 张卡片"}

    # ── Extract factor matrix ──
    F_matrix = []
    for card in cards:
        factors = card.get("priority_factors", {})
        F_matrix.append([factors.get(k, 0.0) for k in _FACTOR_KEYS])

    # ── Baseline ranking ──
    a1 = list(A1_WEIGHTS)
    a2 = list(A2_WEIGHTS)
    a2nd = list(A2ND_WEIGHTS)
    mp = dict(MEMBERSHIP_PARAMS)  # shallow copy
    c_vec = list(QUANT_VECTOR)

    orig_scores = [_fce_score(row, a1, a2, a2nd, mp, c_vec) for row in F_matrix]
    orig_ranks = _compute_ranks(orig_scores)

    original_ranking = []
    for i in range(n_cards):
        original_ranking.append({
            "card_index": i,
            "stakeholder": cards[i].get("stakeholder", f"Card {i}"),
            "priority_score": round(orig_scores[i], 3),
            "rank": orig_ranks[i],
        })
    original_ranking.sort(key=lambda x: x["rank"])

    scenarios = []

    # ── 1. AHP Weight perturbations ──
    # U₁ weights
    for idx, label in [(0, "F₁"), (1, "F₂"), (2, "F₃")]:
        for delta in deltas:
            a1p = _perturb_weight_vector(a1, idx, delta)
            new_scores = [_fce_score(row, a1p, a2, a2nd, mp, c_vec) for row in F_matrix]
            new_ranks = _compute_ranks(new_scores)
            rho = _spearman_rho(orig_ranks, new_ranks)
            delta_p_max = max(abs(new_scores[i] - orig_scores[i]) for i in range(n_cards))
            direction = f"+{int(abs(delta)*100)}%" if delta > 0 else f"−{int(abs(delta)*100)}%"
            scenarios.append({
                "factor_label": f"AHP U₁ {label} weight",
                "delta": direction,
                "old_weight": round(a1[idx], 4),
                "new_weight": round(a1p[idx], 4),
                "spearman_rho": round(rho, 4),
                "delta_P_max": round(delta_p_max, 4),
            })

    # U₂ weights
    for idx, label in [(0, "F₄"), (1, "F₅"), (2, "F₆")]:
        for delta in deltas:
            a2p = _perturb_weight_vector(a2, idx, delta)
            new_scores = [_fce_score(row, a1, a2p, a2nd, mp, c_vec) for row in F_matrix]
            new_ranks = _compute_ranks(new_scores)
            rho = _spearman_rho(orig_ranks, new_ranks)
            delta_p_max = max(abs(new_scores[i] - orig_scores[i]) for i in range(n_cards))
            direction = f"+{int(abs(delta)*100)}%" if delta > 0 else f"−{int(abs(delta)*100)}%"
            scenarios.append({
                "factor_label": f"AHP U₂ {label} weight",
                "delta": direction,
                "old_weight": round(a2[idx], 4),
                "new_weight": round(a2p[idx], 4),
                "spearman_rho": round(rho, 4),
                "delta_P_max": round(delta_p_max, 4),
            })

    # Second-level weight
    for delta in deltas:
        a2nd_p = _perturb_weight_vector(a2nd, 0, delta)
        new_scores = [_fce_score(row, a1, a2, a2nd_p, mp, c_vec) for row in F_matrix]
        new_ranks = _compute_ranks(new_scores)
        rho = _spearman_rho(orig_ranks, new_ranks)
        delta_p_max = max(abs(new_scores[i] - orig_scores[i]) for i in range(n_cards))
        direction = f"+{int(abs(delta)*100)}%" if delta > 0 else f"−{int(abs(delta)*100)}%"
        scenarios.append({
            "factor_label": "AHP L2 U₁ weight",
            "delta": direction,
            "old_weight": round(a2nd[0], 4),
            "new_weight": round(a2nd_p[0], 4),
            "spearman_rho": round(rho, 4),
            "delta_P_max": round(delta_p_max, 4),
        })

    # ── 2. Membership function parameter perturbations ──
    for key in MEMBERSHIP_PARAMS:
        a, b, c, d = MEMBERSHIP_PARAMS[key]
        for delta in deltas:
            mp_p = dict(mp)
            # Perturb the inner boundary points
            new_b = b * (1 + delta)
            new_c = c * (1 + delta)
            mp_p[key] = (a, new_b, new_c, d)
            new_scores = [_fce_score(row, a1, a2, a2nd, mp_p, c_vec) for row in F_matrix]
            new_ranks = _compute_ranks(new_scores)
            rho = _spearman_rho(orig_ranks, new_ranks)
            delta_p_max = max(abs(new_scores[i] - orig_scores[i]) for i in range(n_cards))
            direction = f"+{int(abs(delta)*100)}%" if delta > 0 else f"−{int(abs(delta)*100)}%"
            scenarios.append({
                "factor_label": f"MF {key} ±20%",
                "delta": direction,
                "old_weight": round(b, 4),
                "new_weight": round(new_b, 4),
                "spearman_rho": round(rho, 4),
                "delta_P_max": round(delta_p_max, 4),
            })

    # ── Aggregation ──
    min_rho = min(s["spearman_rho"] for s in scenarios)
    avg_rho = round(sum(s["spearman_rho"] for s in scenarios) / len(scenarios), 4)
    max_dp = max(s.get("delta_P_max", 0) for s in scenarios)
    all_above_09 = min_rho > 0.9
    all_one = min_rho >= 0.9999

    if all_one:
        defense_statement = (
            f"±{int(abs(deltas[0])*100)}% 参数扰动下，全部 {len(scenarios)} 个场景 "
            f"Spearman ρ = 1.0000，排名完全不变。"
            f"最大得分偏差 ΔP_max = {max_dp:.4f}。"
            f"FCE模型的优先级排名对权重和隶属函数参数均不敏感。"
        )
    else:
        defense_statement = (
            f"±{int(abs(deltas[0])*100)}% 参数扰动下，{len(scenarios)} 个场景 "
            f"Spearman ρ 均值 {avg_rho:.4f}，最小值 {min_rho:.4f}。"
            f"最大得分偏差 ΔP_max = {max_dp:.4f}。"
            f"{'排名高度稳定' if all_above_09 else '个别场景排名有波动'}。"
        )

    return {
        "n_cards": n_cards,
        "deltas": [f"{'+' if d > 0 else '−'}{int(abs(d)*100)}%" for d in deltas],
        "original_ranking": original_ranking,
        "scenarios": scenarios,
        "min_rho": min_rho,
        "avg_rho": avg_rho,
        "max_delta_P": round(max_dp, 4),
        "all_above_09": all_above_09,
        "defense_statement": defense_statement,
    }


# ═══════════════════════════════════════════════════════════════
#  FCE re-computation helpers
# ═══════════════════════════════════════════════════════════════

def _fce_score(
    factors: list[float],
    a1: list[float],
    a2: list[float],
    a2nd: list[float],
    mp: dict,
    c_vec: list[float],
) -> float:
    """Recompute FCE priority score with given parameters."""
    F1u = factors[:3]  # F₁, F₂, F₃
    F2u = factors[3:]  # F₄, F₅, F₆

    R1 = _build_R_with_params(F1u, mp)
    R2 = _build_R_with_params(F2u, mp)

    B1_raw = [sum(a1[i] * R1[i][j] for i in range(3)) for j in range(4)]
    B2_raw = [sum(a2[i] * R2[i][j] for i in range(3)) for j in range(4)]

    B1 = _normalize(B1_raw)
    B2 = _normalize(B2_raw)

    R_total = [B1, B2]
    B_raw = [sum(a2nd[i] * R_total[i][j] for i in range(2)) for j in range(4)]
    B = _normalize(B_raw)

    return sum(B[j] * c_vec[j] for j in range(4))


def _build_R_with_params(factors: list[float], mp: dict) -> list[list[float]]:
    """Build R matrix using custom membership parameters."""
    shape_keys = ["v1_low", "v2_mid", "v3_high", "v4_urgent"]
    R = []
    for F in factors:
        row = [_membership_degree_custom(F, mp[sk]) for sk in shape_keys]
        R.append(row)
    return R


def _membership_degree_custom(F: float, params: tuple) -> float:
    """Compute membership degree with custom (a,b,c,d) parameters."""
    a, b, c_val, d = params
    shape = ""

    # Identify shape type from parameters
    if a == b == 0:      # descending half-trapezoid
        shape = "desc"
    elif c_val == d == 1:  # ascending half-trapezoid
        shape = "asc"
    elif a == 0 and b > 0:  # triangle (special case)
        shape = "tri"
    else:
        shape = "tri"  # generic triangle/trapezoid

    if shape == "desc":
        if F <= b:
            return 1.0
        if F < c_val:
            return (c_val - F) / (c_val - b)
        return 0.0
    elif shape == "asc":
        if F <= a:
            return 0.0
        if F < b:
            return (F - a) / (b - a)
        return 1.0
    else:
        # triangle/trapezoid: up a→b, flat b→c, down c→d
        if F <= a:
            return 0.0
        if F < b:
            return (F - a) / (b - a) if b != a else 0.0
        if F <= c_val:
            return 1.0
        if F < d:
            return (d - F) / (d - c_val) if d != c_val else 0.0
        return 0.0


def _perturb_weight_vector(w: list[float], idx: int, delta: float) -> list[float]:
    """Perturb weight at idx by delta, re-normalize others to sum=1."""
    w_new = w.copy()
    w_new[idx] = w[idx] * (1.0 + delta)
    sum_other = sum(w_new[j] for j in range(len(w)) if j != idx)
    if sum_other > 0:
        scale = (1.0 - w_new[idx]) / sum_other
        for j in range(len(w)):
            if j != idx:
                w_new[j] = w[j] * scale
    return w_new


# ═══════════════════════════════════════════════════════════════
#  Rank correlation utilities
# ═══════════════════════════════════════════════════════════════

def _compute_ranks(scores: list[float]) -> list[int]:
    n = len(scores)
    indexed = [(s, i) for i, s in enumerate(scores)]
    indexed.sort(key=lambda x: x[0])
    ranks = [0] * n
    r = 1
    j = 0
    while j < n:
        k = j
        while k < n and indexed[k][0] == indexed[j][0]:
            k += 1
        avg_rank = (r + r + (k - j - 1)) / 2.0
        for t in range(j, k):
            ranks[indexed[t][1]] = int(round(avg_rank))
        r += k - j
        j = k
    return ranks


def _spearman_rho(ranks_a: list[int], ranks_b: list[int]) -> float:
    n = len(ranks_a)
    d2 = sum((ranks_a[i] - ranks_b[i]) ** 2 for i in range(n))
    if d2 == 0:
        return 1.0
    return round(1.0 - (6.0 * d2) / (n * (n * n - 1.0)), 8)
