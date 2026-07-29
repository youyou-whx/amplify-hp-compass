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
