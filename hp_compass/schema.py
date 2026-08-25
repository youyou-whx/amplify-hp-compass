from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class HPInput:
    source_file: str
    raw_text: str


@dataclass
class Classification:
    category: str
    score: float          # fuzzy membership μ_c ∈ [0,1]
    matched_terms: list[str] = field(default_factory=list)


@dataclass
class HPCard:
    hp_id: str
    source_file: str
    date: str | None
    stakeholder: str
    stakeholder_type: str | None
    initial_question: str
    feedback: str
    project_action: str
    evidence: list[str]
    returned: bool

    # ── 处理模式：llm=大模型解析层 / rule=关键词规则层 ──
    processing_mode: str = "rule"

    # ── 多轮访问：卡片本身的 date/source_file 为首次访谈，
    #    后续回访记录追加到 visits（每条：date、source_file、summary）──
    visits: list[dict[str, str]] = field(default_factory=list)

    # ── 延伸判断：LLM 判定的已有记录编号/标识（合并后清空）──
    extension_ref: str = ""

    # ── LLM 覆盖值（仅 processing_mode="llm" 时使用）──
    llm_module_values: dict[str, float] = field(default_factory=dict)       # Φ₂ 模块隶属度
    llm_maturity_values: dict[str, float] = field(default_factory=dict)     # Φ₅ 文本信号
    llm_has_action: bool = False        # Φ₃ 语义判断：已做出实际修改
    llm_has_evidence: bool = False      # Φ₃ 语义判断：已有实质证据
    llm_feedback_summary: str = ""       # 图谱 Feedback 节点文本
    llm_action_summary: str = ""         # 图谱 Action 节点文本
    llm_wiki_en_section: str = ""        # 英文 Wiki 文案段落
    llm_stability: float | None = None   # 四梯度一致率
    llm_raw_dir: str = ""                # 原始 JSON 存档目录

    # ── LLM 生成的回访建议（Φ₆，LLM 模式直通）──
    llm_next_step_cn: str = ""
    llm_next_step_en: str = ""
    llm_materials_cn: list[str] = field(default_factory=list)
    llm_materials_en: list[str] = field(default_factory=list)
    llm_questions_cn: list[str] = field(default_factory=list)
    llm_questions_en: list[str] = field(default_factory=list)

    # ── Φ₂: fuzzy membership classification ──
    categories: list[Classification] = field(default_factory=list)
    affected_modules: list[str] = field(default_factory=list)
    module_memberships: dict[str, float] = field(default_factory=dict)  # c_i vector

    # ── Φ₃: closed-loop status ──
    loop_status: str = "L0_Recorded"
    loop_level: int = 0
    evidence_strength: float = 0.0

    # ── Φ₄: AHP-FCE priority ──
    priority_score: float = 0.0
    priority_factors: dict[str, float] = field(default_factory=dict)  # F_1…F_6
    fce_vector: dict[str, float] = field(default_factory=dict)        # B=(b_1…b_4)
    fce_u1_vector: dict[str, float] = field(default_factory=dict)     # B_1
    fce_u2_vector: dict[str, float] = field(default_factory=dict)     # B_2

    # ── Φ₅: maturity ──
    maturity_scores: dict[str, int] = field(default_factory=dict)       # m_i discrete
    maturity_eigenvalues: dict[str, float] = field(default_factory=dict) # m_i* continuous
    maturity_memberships: dict[str, dict[int, float]] = field(default_factory=dict)  # μ_{i,k}

    # ── Φ₆: recommendations ──
    next_step: str = ""
    next_step_en: str = ""
    suggested_materials: list[str] = field(default_factory=list)
    suggested_materials_en: list[str] = field(default_factory=list)
    suggested_questions: list[str] = field(default_factory=list)
    suggested_questions_en: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GraphData:
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
