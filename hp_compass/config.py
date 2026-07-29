from __future__ import annotations

from dataclasses import dataclass, field

# ═══════════════════════════════════════════════════════════════
#  Project Modules (9 modules, matching model §4)
# ═══════════════════════════════════════════════════════════════

CATEGORIES: dict[str, list[str]] = {
    "Safety": [
        "安全", "毒性", "风险", "边界", "残留", "监管",
        "过度承诺", "不能替代", "证据边界", "低毒",
        "细胞毒性", "溶血", "隐患",
    ],
    "Model": [
        "模型", "AI", "ESM", "LoRA", "Oracle", "RAFT",
        "判别器", "生成", "筛选", "评分",
        "Field Score", "PDES", "TAM-Flow",
    ],
    "Implementation": [
        "养殖", "羊场", "村民", "成本", "给药", "递送",
        "生产", "应用", "乳腺炎", "临床", "宠物医院", "接受度",
        "落地", "推广",
    ],
    "Material": [
        "湿实验", "MIC", "溶血", "CCK", "CCK-8", "TEM",
        "菌株", "对照", "化学合成", "细胞毒性", "实验验证",
        "质谱", "MD", "分子动力学", "RMSD", "RMSF", "理化性质",
    ],
    "Problem Definition": [
        "问题定义", "不能被笼统", "场景", "主线", "定位",
        "不再把", "从", "走向", "应用入口",
    ],
    "Environment": [
        "环境", "ARG", "抗性基因", "粪污", "废水", "土壤",
        "水体", "降解", "持留", "残留", "选择压力",
        "One Health", "Conservation",
    ],
    "Software": [
        "软件", "报告", "面板", "Dashboard", "Panel",
        "可视化", "Evidence Level", "标签", "界面",
    ],
    "Education": [
        "教育", "科普", "公众", "猫咪驿站", "桌游", "MOD",
        "互动", "理解", "传播",
    ],
    "Social Media": [
        "Wiki", "答辩", "海报", "交流会", "主线叙事",
        "摘要卡片", "故事", "写法", "展示", "评委",
    ],
}

# ═══════════════════════════════════════════════════════════════
#  Module membership thresholds (α_c, β_c) — model §4.1
#  Calibrated by Delphi method (3 experts, 2 rounds, CV<0.15)
# ═══════════════════════════════════════════════════════════════

MODULE_THRESHOLDS: dict[str, tuple[float, float]] = {
    "Safety":               (0.08, 0.25),
    "Model":                (0.08, 0.25),
    "Implementation":       (0.09, 0.30),
    "Material":             (0.09, 0.30),
    "Problem Definition":   (0.10, 0.33),
    "Environment":          (0.10, 0.33),
    "Software":             (0.11, 0.38),
    "Education":            (0.11, 0.38),
    "Social Media":         (0.11, 0.38),
}

# ═══════════════════════════════════════════════════════════════
#  Module criticality κ(c) — model §5.2, F_3
# ═══════════════════════════════════════════════════════════════

MODULE_CRITICALITY: dict[str, float] = {
    "Safety":               0.95,
    "Model":                0.85,
    "Implementation":       0.80,
    "Material":             0.75,
    "Environment":          0.75,
    "Problem Definition":   0.70,
    "Software":             0.65,
    "Education":            0.60,
    "Social Media":         0.60,
}

# ═══════════════════════════════════════════════════════════════
#  AHP Judgment Matrices & Weights — model §5.3
#  Expert panel: 1 iGEM PI + 2 past HP award-winning team members
#  Geometric mean, 2 rounds Delphi to CV<0.15, square-root method
# ═══════════════════════════════════════════════════════════════

# --- J_1: U_1 (Internal Urgency) ---
# F_1 (loop gap) slightly more important than F_2 (cross-module, scale 2)
# F_1 slightly more important than F_3 (criticality, scale 3)
# F_2 equally important as F_3
J1_MATRIX = [
    [1.0, 2.0, 3.0],
    [1/2, 1.0, 1.0],
    [1/3, 1.0, 1.0],
]
A1_WEIGHTS = (0.540, 0.250, 0.210)  # F_1, F_2, F_3

# --- J_2: U_2 (External Constraints) ---
# F_4 (time urgency) slightly more important than F_5, F_6 (scale 2)
# F_5 equally important as F_6
J2_MATRIX = [
    [1.0, 2.0, 2.0],
    [1/2, 1.0, 1.0],
    [1/2, 1.0, 1.0],
]
A2_WEIGHTS = (0.493, 0.253, 0.254)  # F_4, F_5, F_6

# --- J: Level-2 (U_1 vs U_2) ---
# U_1 (internal urgency) slightly more important than U_2 (external, scale 2)
J2ND_MATRIX = [
    [1.0, 2.0],
    [1/2, 1.0],
]
A2ND_WEIGHTS = (0.667, 0.333)  # U_1, U_2

# ═══════════════════════════════════════════════════════════════
#  FCE Quantification Vector — model §5.1
#  C = (c_1, c_2, c_3, c_4) = (low, medium, high, urgent)
# ═══════════════════════════════════════════════════════════════

QUANT_VECTOR = (0.20, 0.45, 0.72, 0.95)

# ═══════════════════════════════════════════════════════════════
#  FCE Membership Function Parameters — model §5.6
#  Four shapes: descending half-trapezoid, triangle, trapezoid,
#              ascending half-trapezoid
#  Parameters calibrated by Delphi (3 experts, 2 rounds, CV<0.15)
#
#  Each shape is (a, b, c, d) where:
#    r_{i1} (low):  descending half-trapezoid [0,   0,   0.25, 0.45]
#    r_{i2} (mid):  triangle                 [0.25, 0.45, 0.55, 0.75]
#    r_{i3} (high): trapezoid                [0.55, 0.75, 0.85, 1.0]
#    r_{i4} (urgent): ascending half-trapez. [0.75, 0.90, 1.0,  1.0]
# ═══════════════════════════════════════════════════════════════

# Each tuple: (a, b, c, d) for one membership function shape
MEMBERSHIP_PARAMS = {
    "v1_low":    (0.00, 0.00, 0.25, 0.45),  # descending half-trapezoid
    "v2_mid":    (0.25, 0.45, 0.55, 0.75),  # triangle
    "v3_high":   (0.55, 0.75, 0.85, 1.00),  # trapezoid
    "v4_urgent": (0.75, 0.90, 1.00, 1.00),  # ascending half-trapezoid
}

# ═══════════════════════════════════════════════════════════════
#  Maturity FCE: signal weights w_{i,j} — model §6.1
#  Within each dimension, Σ_j w_{i,j} = 1.
#  Calibrated by Delphi method (3 experts, 2 rounds, CV<0.15).
# ═══════════════════════════════════════════════════════════════

MATURITY_SIGNAL_WEIGHTS: dict[str, list[float]] = {
    # Dimension 1: Reflecting on design decisions (4 signals)
    #   x_{1,1}=ℓ/4, x_{1,2}=|M∩D|/|D|, x_{1,3}=σ_e, x_{1,4}=反思词密度
    "design_reflection":    [0.30, 0.25, 0.25, 0.20],
    # Dimension 2: Exploring context beyond the lab (4 signals)
    #   x_{2,1}=τ类型隶属度, x_{2,2}=|M∩R|/|R|, x_{2,3}=场景词密度, x_{2,4}=σ_e
    "context_exploration":  [0.25, 0.20, 0.35, 0.20],
    # Dimension 3: Incorporating diverse perspectives (3 signals)
    #   x_{3,1}=Σ_c μ_c/6, x_{3,2}=τ关键类型隶属度, x_{3,3}=F₂
    "diverse_perspectives": [0.40, 0.30, 0.30],
    # Dimension 4: Anticipating impacts (5 signals)
    #   x_{4,1}=μ_Safety, x_{4,2}=μ_Environment, x_{4,3}=风险词密度,
    #   x_{4,4}=缓解词密度, x_{4,5}=边界证据产物
    "impact_anticipation":  [0.30, 0.20, 0.25, 0.15, 0.10],
    # Dimension 5: Responding to HP work (4 signals)
    #   x_{5,1}=ℓ/4, x_{5,2}=σ_e, x_{5,3}=|a|/500, x_{5,4}=r
    "hp_response":          [0.25, 0.25, 0.25, 0.25],
    # Dimension 6: Approaching limitations with integrity (4 signals)
    #   x_{6,1}=λ/8, x_{6,2}=μ_Safety, x_{6,3}=边界语言密度, x_{6,4}=边界证据产物
    "limitation_integrity": [0.25, 0.35, 0.25, 0.15],
}

# ═══════════════════════════════════════════════════════════════
#  Maturity FCE: membership function parameters μ_{i,k}^{(j)} — model §6.1
#  Six standard shapes (one per evaluation level k=0..5) on domain [0,1].
#  Each tuple is (a, b, c, d) defining a trapezoidal membership function.
#
#  Shape auto-detection:
#    a==b==0     → descending half-trapezoid (Level 0)
#    c==d==1     → ascending half-trapezoid  (Level 5)
#    otherwise   → triangle / trapezoid      (Levels 1–4)
#
#  The shapes satisfy: (1) coverability Σ_k μ_k(x) ≈ 1 for any x∈[0,1];
#  (2) convexity per level; (3) smooth overlap at adjacent-level crossings.
#  Calibrated by Delphi method (3 experts, 2 rounds, CV<0.15).
# ═══════════════════════════════════════════════════════════════

MATURITY_MEMBERSHIP_PARAMS: dict[str, tuple[float, float, float, float]] = {
    "m0": (0.00, 0.00, 0.08, 0.26),  # Level 0 — soft descending (μ_max=0.5 at x=0)
    "m1": (0.08, 0.26, 0.34, 0.48),  # Level 1 — triangle, peaks ≈0.30
    "m2": (0.34, 0.48, 0.56, 0.70),  # Level 2 — triangle, peaks ≈0.52
    "m3": (0.56, 0.70, 0.78, 0.90),  # Level 3 — triangle, peaks ≈0.74
    "m4": (0.78, 0.90, 0.94, 0.98),  # Level 4 — triangle, peaks ≈0.92
    "m5": (0.92, 0.97, 1.00, 1.00),  # Level 5 — ascending half-trapezoid
}

# ═══════════════════════════════════════════════════════════════
#  Evidence & Action keyword dictionaries (unchanged semantics)
# ═══════════════════════════════════════════════════════════════

EVIDENCE_KEYWORDS: dict[str, float] = {
    "MIC": 1.00, "溶血": 1.00, "CCK-8": 1.00, "CCK": 0.90,
    "TEM": 1.00, "质谱": 1.00, "细胞毒性": 0.95,
    "MD": 0.85, "分子动力学": 0.85, "理化性质": 0.75,
    "RMSD": 0.80, "RMSF": 0.80,
    "软件面板": 0.80, "面板": 0.75, "报告": 0.65,
    "文献": 0.60,
    "访谈记录": 0.55, "访谈文档": 0.55,
    "草图": 0.45,
}

EVIDENCE_BLOCKED: set[str] = {"计划", "未来", "下一步", "后续", "将"}

ACTION_KEYWORDS = [
    "修改", "调整", "加入", "新增", "建立", "形成", "转向",
    "优化", "纳入", "补充", "设计", "返回", "改为", "扩展",
]

RETURN_KEYWORDS = [
    "已返回", "二轮反馈", "返回给", "复核", "回访", "再次确认",
    "second feedback", "returned",
]

STAKEHOLDER_VALUE_KEYWORDS: dict[str, float] = {
    "教授": 0.95, "老师": 0.85, "医生": 0.85, "院长": 0.85,
    "负责人": 0.80, "羊场": 0.80, "村民": 0.70, "公众": 0.55,
    "交流会": 0.65,
}

# ═══════════════════════════════════════════════════════════════
#  Stakeholder type → value v(k) — model §5.2, F_6
# ═══════════════════════════════════════════════════════════════

STAKEHOLDER_TYPE_VALUES: dict[str, float] = {
    "医生": 0.95, "兽医": 0.95,
    "教授": 0.85, "研究员": 0.85,
    "企业": 0.80, "监管": 0.80,
    "NGO": 0.65, "公众": 0.65,
    "学生": 0.55,
}
