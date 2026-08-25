"""HP Compass — Fuzzy Comprehensive Evaluation Maturity Assessment (Φ₅)

Model §6: Six-dimension FCE maturity evaluation

For each dimension i ∈ {1,…,6}:
  1. Compute signal variables x_{i,j} from HPCard fields
  2. For each signal j, evaluate membership μ_{i,k}^{(j)}(x_{i,j}) to level k ∈ {0,…,5}
     via trapezoidal membership functions (a,b,c,d)_{i,k} calibrated by Delphi method
  3. Weighted synthesis: μ_{i,k} = Σ_j w_{i,j} · μ_{i,k}^{(j)}(x_{i,j}),  Σ_j w_{i,j} = 1
  4. Level determination:
     - Dominant case (∃k: μ_{i,k} > 0.5) → m_i = argmax_k μ_{i,k}  (max-membership)
     - Always compute m_i* = Σ(k·μ_k^γ)/Σ(μ_k^γ), γ=2  (level eigenvalue, §6.2)

The signal weights w_{i,j} and membership function parameters are defined in config.py
and calibrated by 3 experts via Delphi method (2 rounds, CV < 0.15).
"""

from __future__ import annotations

from .config import (
    MATURITY_MEMBERSHIP_PARAMS,
    MATURITY_SIGNAL_WEIGHTS,
)
from .schema import HPCard

# ═══════════════════════════════════════════════════════════════
#  Dimension labels (for display)
# ═══════════════════════════════════════════════════════════════

DIMENSION_ORDER: list[str] = [
    "design_reflection",
    "context_exploration",
    "diverse_perspectives",
    "impact_anticipation",
    "hp_response",
    "limitation_integrity",
]

DIMENSION_LABELS: dict[str, str] = {
    "design_reflection":      "Reflecting on design decisions",
    "context_exploration":    "Exploring context beyond the lab",
    "diverse_perspectives":   "Incorporating diverse perspectives",
    "impact_anticipation":    "Anticipating impacts",
    "hp_response":            "Responding to HP work",
    "limitation_integrity":   "Approaching limitations",
}

DIMENSION_SHORT: dict[str, str] = {
    "design_reflection":      "Design Reflection",
    "context_exploration":    "Context Exploration",
    "diverse_perspectives":   "Diverse Perspectives",
    "impact_anticipation":    "Impact Anticipation",
    "hp_response":            "HP Response",
    "limitation_integrity":   "Limitation Integrity",
}

# ═══════════════════════════════════════════════════════════════
#  Level anchor descriptions (for display / tooltips)
# ═══════════════════════════════════════════════════════════════

LEVEL_ANCHORS: dict[str, dict[int, str]] = {
    "design_reflection": {
        0: "无设计反思 — 仅有原始记录",
        1: "表层理解 — 未触及设计层面",
        2: "注意到设计含义 — 设计相关模块或关键词出现",
        3: "明确的设计变更 — 设计模块受影响且有具体修改",
        4: "跨模块设计迭代 — 多设计模块联动，有证据支撑",
        5: "系统性设计反思 — 含证据的完整设计迭代闭环",
    },
    "context_exploration": {
        0: "纯实验室视角 — 未涉及真实场景",
        1: "意识到真实场景 — 反馈中提及应用场景",
        2: "探索了一个真实场景 — Implementation或Environment模块受影响",
        3: "深度场景探索 — 多场景或真实场景stakeholder参与",
        4: "系统性场景探索 — 真实场景stakeholder+多模块+证据",
        5: "场景验证闭环 — 真实场景全链条+强证据支撑",
    },
    "diverse_perspectives": {
        0: "单一窄视角 — 仅0-1个模块",
        1: "有限视角 — 1-2个模块",
        2: "同域多角度 — 3-4个模块",
        3: "跨域视角 — 5+模块或独特stakeholder类型",
        4: "桥接多方视角 — 独特类型+4+模块",
        5: "综合多利益相关者 — 独特类型+6+模块+高跨模块影响",
    },
    "impact_anticipation": {
        0: "未考虑影响 — 无Safety/Environment模块",
        1: "仅关注正面影响 — 无风险语言",
        2: "意识到潜在负面影响 — 含风险关键词",
        3: "明确的负面风险识别 — Safety/Environment+风险关键词",
        4: "正负影响均有应对 — Safety+Environment+缓解措施",
        5: "系统化影响评估 — 完整的风险评估产物",
    },
    "hp_response": {
        0: "未响应 — L0",
        1: "反馈已理解 — L1，反馈文本已提取",
        2: "基础响应计划 — L1-L2，有行动方向",
        3: "具体行动已执行 — L2，行动内容充实",
        4: "证据支撑的响应 — L3，有实质证据",
        5: "闭环验证完成 — L4，已回访确认",
    },
    "limitation_integrity": {
        0: "未讨论局限性",
        1: "模糊承认不足 — 1个局限性关键词",
        2: "明确局限性识别 — 2+关键词",
        3: "多局限性讨论 — 3+关键词且触及Safety/Environment",
        4: "局限性+边界设定 — 明确边界语言+Safety模块",
        5: "系统化局限性框架 — 含边界文档产出",
    },
}

# ═══════════════════════════════════════════════════════════════
#  Signal keyword libraries (for computing signal variables x_{i,j})
# ═══════════════════════════════════════════════════════════════

# Dimension 1: Design-related modules
DESIGN_MODULES = {"Model", "Software", "Problem Definition"}

# Dimension 1: Design reflection keywords
DESIGN_REFLECTION_KEYWORDS = [
    "设计", "修改", "调整", "迭代", "重新", "转向",
    "加入", "新增", "建立", "优化", "纳入", "补充",
    "扩展", "重构", "改进",
]

# Dimension 1: Iteration keywords (advanced signal)
DESIGN_ITERATION_KEYWORDS = [
    "迭代", "重新", "转向", "重构", "第二版", "v2",
    "再次调整", "反复", "进一步优化",
]

# Dimension 2: Real-world scenario keywords
REAL_WORLD_KEYWORDS = [
    "临床", "养殖", "村民", "羊场", "宠物医院",
    "应用场景", "真实场景", "场景", "实际应用",
    "乳腺炎", "乳房炎", "给药", "递送", "生产",
    "落地", "推广", "接受度",
]

# Dimension 2: Real-world stakeholder types
REAL_WORLD_STAKEHOLDER_TYPES = {
    "养殖端 stakeholder",
    "兽医临床 stakeholder",
    "公众教育 stakeholder",
}

# Dimension 2: Real-world modules
REAL_WORLD_MODULES = {"Implementation", "Environment"}

# Dimension 3: Unique (key / vulnerable) stakeholder types
UNIQUE_STAKEHOLDER_TYPES = {
    "养殖端 stakeholder",
    "公众教育 stakeholder",
    "兽医临床 stakeholder",
}

# Dimension 4: Risk keywords
RISK_KEYWORDS = [
    "风险", "安全", "毒性", "边界", "过度",
    "限制", "负面影响", "负面", "危害", "隐患",
    "残留", "监管", "过度承诺", "不能替代",
]

# Dimension 4: Risk evidence artifacts
RISK_EVIDENCE_ARTIFACTS = [
    "Risk Boundary Panel",
    "PDES",
    "Environmental Degradation Panel",
    "Evidence Matrix",
]

# Dimension 5: Response action keywords
RESPONSE_ACTION_KEYWORDS = [
    "修改", "调整", "加入", "新增", "建立", "形成",
    "转向", "优化", "纳入", "补充", "设计", "改为",
    "扩展", "重构", "改进", "完善",
]

# Dimension 6: Limitation keywords
LIMITATION_KEYWORDS = [
    "局限", "不足", "不能", "不应", "无法", "缺乏",
    "仍需", "边界", "过度承诺", "证据边界", "不能替代",
    "尚未", "还需", "有待", "仍需谨慎",
]

# Dimension 6: Boundary language (advanced signal)
BOUNDARY_LANGUAGE = [
    "不能替代", "证据边界", "过度承诺",
    "不能声称", "尚不能", "边界条件",
]

# Dimension 6: Boundary evidence artifacts
BOUNDARY_ARTIFACTS = [
    "Risk Boundary Panel",
    "use-boundary checklist",
    "Evidence Matrix",
]

# Dimension 4: Mitigation keywords
MITIGATION_KEYWORDS = [
    "降低", "避免", "防止", "控制", "限制",
    "不超过", "监测", "检测", "评估", "边界",
    "不替代", "不声称", "标注", "说明",
]

# Dimension 1: Saturation point for design reflection keyword density
_DESIGN_KW_SATURATION = 6

# Dimension 2: Saturation point for scene keyword density
_SCENE_KW_SATURATION = 6

# Dimension 4: Saturation point for risk keyword density
_RISK_KW_SATURATION = 6

# Dimension 4: Saturation point for mitigation keyword density
_MITIGATION_KW_SATURATION = 4

# Dimension 6: Saturation point for boundary language density
_BOUNDARY_KW_SATURATION = 3

# Dimension 6: Normalization denominator for limitation keyword count
_LIMITATION_KW_DENOM = 8

# Dimension 5: Normalization denominator for action text length
_ACTION_LEN_DENOM = 500

# Dimension 3: Normalization denominator for weighted module count
_MODULE_COUNT_DENOM = 6


# ═══════════════════════════════════════════════════════════════
#  Signal computation helpers
# ═══════════════════════════════════════════════════════════════

def _keyword_density(text: str, keywords: list[str], saturation: int) -> float:
    """Compute keyword hit density, saturated at `saturation` unique hits.

    Returns a value in [0, 1].
    """
    if not text or not keywords:
        return 0.0
    hits = sum(1 for kw in keywords if kw in text)
    return min(1.0, hits / max(1, saturation))


def _keyword_count(text: str, keywords: list[str]) -> int:
    """Count unique keyword hits in text."""
    if not text:
        return 0
    return sum(1 for kw in keywords if kw in text)


def _any_keyword(text: str, keywords: list[str]) -> bool:
    """Check whether any keyword appears in text."""
    if not text:
        return False
    return any(kw in text for kw in keywords)


def _any_artifact(text: str, artifacts: list[str]) -> bool:
    """Check whether any named artifact appears in the joined evidence text."""
    if not text:
        return False
    return any(a.lower() in text.lower() for a in artifacts)


def _stakeholder_type_membership(stype: str | None) -> float:
    """Map stakeholder type to a real-world relevance membership score.

    Clinical / veterinary  → 0.95  (highest real-world relevance)
    Enterprise / regulatory → 0.80
    NGO / public            → 0.65
    Academic / iGEM / other → 0.40  (baseline — lab-centric)
    """
    if not stype:
        return 0.40
    s = stype
    if any(kw in s for kw in ["医生", "兽医", "临床", "医院", "检验"]):
        return 0.95
    if any(kw in s for kw in ["企业", "监管", "养殖", "羊场", "负责人"]):
        return 0.80
    if any(kw in s for kw in ["NGO", "公众", "教育", "驿站"]):
        return 0.65
    return 0.40


def _key_type_membership(stype: str | None) -> float:
    """Map stakeholder type to a key-type membership score for dimension 3.

    Unique / vulnerable stakeholder types get high scores;
    common academic types get baseline.
    """
    if not stype:
        return 0.50
    if stype in UNIQUE_STAKEHOLDER_TYPES:
        return 1.00
    # iGEM / academic exchange types get intermediate score
    if any(kw in stype for kw in ["iGEM", "Wiki", "交流"]):
        return 0.65
    return 0.50


# ═══════════════════════════════════════════════════════════════
#  Signal variable computation (one function per dimension)
# ═══════════════════════════════════════════════════════════════

def _llm_signal(card: HPCard, signal_key: str) -> float | None:
    """LLM 模式下返回文本信号的四梯度代表性数值；否则返回 None。"""
    if card.processing_mode == "llm" and signal_key in card.llm_maturity_values:
        return card.llm_maturity_values[signal_key]
    return None


def _compute_signals_dim1(card: HPCard) -> list[float]:
    """Dimension 1: Reflecting on design decisions — 4 signals.

    x_{1,1} = ℓ / 4          (loop level normalised)
    x_{1,2} = |M ∩ D| / |D|  (design-module coverage, D={Model, Software, Problem Def})
    x_{1,3} = σ_e            (evidence strength)
    x_{1,4} = design-reflection keyword density（LLM 模式：design_reflection 四梯度）
    """
    x1 = card.loop_level / 4.0
    modules = set(card.affected_modules)
    design_hit = len(modules & DESIGN_MODULES)
    x2 = design_hit / max(1, len(DESIGN_MODULES))
    x3 = card.evidence_strength
    llm_x4 = _llm_signal(card, "design_reflection")
    if llm_x4 is not None:
        x4 = llm_x4
    else:
        action_text = card.project_action.lower()
        x4 = _keyword_density(action_text, DESIGN_REFLECTION_KEYWORDS, _DESIGN_KW_SATURATION)
    return [x1, x2, x3, x4]


def _compute_signals_dim2(card: HPCard) -> list[float]:
    """Dimension 2: Exploring context beyond the lab — 4 signals.

    x_{2,1} = τ type membership        (stakeholder-type → real-world relevance)
    x_{2,2} = |M ∩ R| / |R|            (real-world module coverage, R={Impl, Env})
    x_{2,3} = scene keyword density     (LLM 模式：context_scene 四梯度)
    x_{2,4} = σ_e                       (evidence strength)
    """
    x1 = _stakeholder_type_membership(card.stakeholder_type)
    modules = set(card.affected_modules)
    rw_hit = len(modules & REAL_WORLD_MODULES)
    x2 = rw_hit / max(1, len(REAL_WORLD_MODULES))
    llm_x3 = _llm_signal(card, "context_scene")
    if llm_x3 is not None:
        x3 = llm_x3
    else:
        scene_text = (card.feedback + " " + card.initial_question).lower()
        x3 = _keyword_density(scene_text, REAL_WORLD_KEYWORDS, _SCENE_KW_SATURATION)
    x4 = card.evidence_strength
    return [x1, x2, x3, x4]


def _compute_signals_dim3(card: HPCard) -> list[float]:
    """Dimension 3: Incorporating diverse perspectives — 3 signals.

    x_{3,1} = min(1, Σ_c μ_c / 6)  (normalised weighted module count)
    x_{3,2} = τ key-type membership (unique stakeholder → 1.0, baseline 0.5)
    x_{3,3} = F₂                    (cross-module impact factor from Φ₄)
    """
    weighted_sum = sum(card.module_memberships.values()) if card.module_memberships else 0.0
    x1 = min(1.0, weighted_sum / _MODULE_COUNT_DENOM)
    x2 = _key_type_membership(card.stakeholder_type)
    x3 = card.priority_factors.get("cross_module_impact", 0.0)
    return [x1, x2, x3]


def _compute_signals_dim4(card: HPCard) -> list[float]:
    """Dimension 4: Anticipating positive & negative impacts — 5 signals.

    x_{4,1} = μ_Safety              (Safety module fuzzy membership)
    x_{4,2} = μ_Environment         (Environment module fuzzy membership)
    x_{4,3} = risk keyword density   (in feedback ⊕ project_action)
    x_{4,4} = mitigation keyword density
    x_{4,5} = boundary evidence      (1 if any risk evidence artifact present, else 0)
    """
    x1 = card.module_memberships.get("Safety", 0.0)
    x2 = card.module_memberships.get("Environment", 0.0)
    llm_x3 = _llm_signal(card, "risk")
    if llm_x3 is not None:
        x3 = llm_x3
    else:
        risk_text = (card.feedback + " " + card.project_action).lower()
        x3 = _keyword_density(risk_text, RISK_KEYWORDS, _RISK_KW_SATURATION)
    llm_x4 = _llm_signal(card, "mitigation")
    if llm_x4 is not None:
        x4 = llm_x4
    else:
        x4 = _keyword_density(card.project_action.lower(), MITIGATION_KEYWORDS,
                              _MITIGATION_KW_SATURATION)
    evidence_text = " ".join(card.evidence).lower()
    x5 = 1.0 if _any_artifact(evidence_text, RISK_EVIDENCE_ARTIFACTS) else 0.0
    return [x1, x2, x3, x4, x5]


def _compute_signals_dim5(card: HPCard) -> list[float]:
    """Dimension 5: Responding to human practices work — 4 signals.

    x_{5,1} = ℓ / 4       (loop level normalised)
    x_{5,2} = σ_e          (evidence strength)
    x_{5,3} = |a| / 900    (action text richness, 900 = max_chars in extractor)
    x_{5,4} = r            (returned flag, 0 or 1)
    """
    x1 = card.loop_level / 4.0
    x2 = card.evidence_strength
    x3 = min(1.0, len(card.project_action.strip()) / _ACTION_LEN_DENOM)
    x4 = 1.0 if card.returned else 0.0
    return [x1, x2, x3, x4]


def _compute_signals_dim6(card: HPCard) -> list[float]:
    """Dimension 6: Approaching limitations with integrity — 4 signals.

    x_{6,1} = λ / 15              (limitation keyword count normalised)
    x_{6,2} = μ_Safety            (Safety module fuzzy membership)
    x_{6,3} = boundary language density
    x_{6,4} = boundary evidence    (1 if any boundary artifact present, else 0)
    """
    llm_x1 = _llm_signal(card, "limitation")
    if llm_x1 is not None:
        x1 = llm_x1
    else:
        lim_text = (card.feedback + " " + card.project_action).lower()
        lam = _keyword_count(lim_text, LIMITATION_KEYWORDS)
        x1 = min(1.0, lam / _LIMITATION_KW_DENOM)
    x2 = card.module_memberships.get("Safety", 0.0)
    llm_x3 = _llm_signal(card, "boundary")
    if llm_x3 is not None:
        x3 = llm_x3
    else:
        lim_text = (card.feedback + " " + card.project_action).lower()
        x3 = _keyword_density(lim_text, BOUNDARY_LANGUAGE, _BOUNDARY_KW_SATURATION)
    evidence_text = " ".join(card.evidence).lower()
    x4 = 1.0 if _any_artifact(evidence_text, BOUNDARY_ARTIFACTS) else 0.0
    return [x1, x2, x3, x4]


# ── Signal dispatcher ──

_SIGNAL_COMPUTERS = {
    "design_reflection":    _compute_signals_dim1,
    "context_exploration":  _compute_signals_dim2,
    "diverse_perspectives": _compute_signals_dim3,
    "impact_anticipation":  _compute_signals_dim4,
    "hp_response":          _compute_signals_dim5,
    "limitation_integrity": _compute_signals_dim6,
}


# ═══════════════════════════════════════════════════════════════
#  Membership function evaluation
# ═══════════════════════════════════════════════════════════════

def _membership_degree(x: float, params: tuple[float, float, float, float]) -> float:
    """Evaluate trapezoidal membership μ(x; a, b, c, d).

    Shape auto-detection from parameters:
      a == b == 0               → descending half-trapezoid
      c == d == 1               → ascending half-trapezoid
      otherwise                  → triangle / trapezoid (up a→b, plateau b→c, down c→d)
    """
    a, b, c, d = params

    # Descending half-trapezoid: r=1 for x≤b, linear down to 0 at x≥c
    if a == 0.0 and b == 0.0:
        if x <= b:
            return 1.0
        if x < c:
            return (c - x) / (c - b) if c != b else 0.0
        return 0.0

    # Ascending half-trapezoid: r=0 for x≤a, linear up to 1 at x≥b
    if c == 1.0 and d == 1.0:
        if x <= a:
            return 0.0
        if x < b:
            return (x - a) / (b - a) if b != a else 1.0
        return 1.0

    # Triangle / trapezoid: up a→b, plateau b→c, down c→d
    if x <= a:
        return 0.0
    if x < b:
        return (x - a) / (b - a) if b != a else 1.0
    if x <= c:
        return 1.0
    if x < d:
        return (d - x) / (d - c) if d != c else 0.0
    return 0.0


# ═══════════════════════════════════════════════════════════════
#  FCE membership synthesis
# ═══════════════════════════════════════════════════════════════

def _synthesize_membership(
    signals: list[float],
    weights: list[float],
) -> list[float]:
    """M(·,+) weighted-average synthesis for one maturity dimension.

    μ_k = Σ_j w_j · μ_k^{(j)}(x_j),  k = 0,…,5

    Zero-valued signals (x ≈ 0) contribute a uniform 1/6 to all levels,
    representing "no evidence" rather than biasing toward L0.
    This prevents dimensions with sparse signals (e.g. boundary evidence,
    limitation keywords) from being irrecoverably dragged to L0.

    Returns a 6-element membership vector.
    """
    n_levels = 6
    mu = [0.0] * n_levels
    membership_keys = [f"m{k}" for k in range(n_levels)]

    for j, x in enumerate(signals):
        w = weights[j]
        if x <= 0.001:
            # Absent signal → uniform prior across all levels
            for k in range(n_levels):
                mu[k] += w * (1.0 / n_levels)
        else:
            for k, mkey in enumerate(membership_keys):
                params = MATURITY_MEMBERSHIP_PARAMS[mkey]
                mu[k] += w * _membership_degree(x, params)

    # Normalise to sum = 1 (M(·,+) with normalised weights guarantees this
    # algebraically; we normalise to absorb float error)
    total = sum(mu)
    if total > 0:
        mu = [v / total for v in mu]

    return mu


def _level_eigenvalue(mu: list[float], gamma: float = 2.0) -> float:
    """Compute level eigenvalue (weighted average maturity score).

    m_i* = Σ(k · μ_k^γ) / Σ(μ_k^γ)  ∈ [0, 5]

    γ = 2: power-weighted — amplifies high-membership levels,
    suppresses low-membership noise.
    γ = 1: ordinary weighted average.
    γ → ∞: max-membership principle.
    """
    numer = sum(k * (mu[k] ** gamma) for k in range(len(mu)))
    denom = sum(mu[k] ** gamma for k in range(len(mu)))
    if denom == 0:
        return 0.0
    return numer / denom


# ═══════════════════════════════════════════════════════════════
#  Public entry point
# ═══════════════════════════════════════════════════════════════

def score_maturity(card: HPCard) -> HPCard:
    """Score all six maturity dimensions via FCE (model §6).

    For each dimension:
      1. Compute signal variables x_{i,j}
      2. Evaluate fuzzy membership μ_{i,k}^{(j)}(x_{i,j}) per level
      3. Weighted synthesis: μ_{i,k} = Σ_j w_{i,j} · μ_{i,k}^{(j)}
      4. Discrete level: m_i = argmax_k μ_{i,k}
      5. Continuous eigenvalue: m_i* = Σ(k·μ_k^γ)/Σ(μ_k^γ), γ=2

    Writes:
      card.maturity_scores       — discrete levels m_i ∈ {0,…,5}
      card.maturity_eigenvalues  — continuous scores m_i* ∈ [0, 5]
      card.maturity_memberships  — full 6-dim membership vectors μ_{i,k}
    """
    card.maturity_scores = {}
    card.maturity_eigenvalues = {}
    card.maturity_memberships = {}

    for dim_key in DIMENSION_ORDER:
        # Step 1: Compute signal variables
        compute_fn = _SIGNAL_COMPUTERS[dim_key]
        signals = compute_fn(card)

        # Step 2–3: FCE membership synthesis
        weights = MATURITY_SIGNAL_WEIGHTS[dim_key]
        mu = _synthesize_membership(signals, weights)

        # Store full 6-dim membership vector
        card.maturity_memberships[dim_key] = {
            k: round(v, 4) for k, v in enumerate(mu)
        }

        # Step 4: Max-membership discrete level
        m_i = max(range(6), key=lambda k: mu[k])
        card.maturity_scores[dim_key] = m_i

        # Step 5: Level eigenvalue (continuous score, always computed)
        m_star = _level_eigenvalue(mu, gamma=2.0)
        card.maturity_eigenvalues[dim_key] = round(m_star, 3)

    return card
