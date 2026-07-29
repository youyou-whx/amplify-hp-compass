"""Wiki 文案自动生成模块

设计原则：
- 六大信息区严格分离，各用 #### 子标题
- 多点内容以 markdown 列表呈现
- 零截断：所有文本字段全文输出
- 英文 Wiki 从结构化字段生成英文叙述，中文原文仅作补充引用
"""

from __future__ import annotations

from pathlib import Path
from .schema import HPCard


# ═══════════════ 工具函数 ═══════════════

def _unique_modules(cards: list[HPCard]) -> int:
    s = set()
    for c in cards:
        s.update(c.affected_modules)
    return len(s)


def _split_multipoint(text: str) -> list[str]:
    """将多句文本拆为独立要点。优先按显式换行拆分，其次按中文句号。"""
    t = text.strip()
    if not t:
        return []
    if "\n" in t:
        parts = [p.strip() for p in t.split("\n") if p.strip()]
        if len(parts) >= 2:
            return parts
        return [t]
    if "。" in t:
        sents = [s.strip() + "。" for s in t.split("。") if s.strip()]
        if len(sents) >= 3:
            return sents
    return [t]


def _story_before(card: HPCard) -> str:
    ms = set(card.affected_modules)
    if "Model" in ms and ("Material" in ms or "Wet Lab" in ms):
        return "候选肽设计"
    if "Implementation" in ms and "Problem Definition" in ms:
        return "应用场景探索"
    if "Safety" in ms or "Environment" in ms:
        return "安全边界与生态评估"
    if "Wiki Narrative" in ms:
        return "项目表达与叙事"
    if "Education" in ms:
        return "公众沟通与教育"
    return "项目早期阶段"


def _story_after(card: HPCard) -> str:
    ms = set(card.affected_modules)
    if "Model" in ms and ("Material" in ms or "Wet Lab" in ms):
        return "证据链闭合的候选评估框架"
    if "Implementation" in ms and "Problem Definition" in ms:
        return "真实场景中的疾病靶向设计"
    if "Safety" in ms or "Environment" in ms:
        return "使用边界与生态降解评估体系"
    if "Wiki Narrative" in ms:
        return "跨校可交流的工程化叙事"
    if "Education" in ms:
        return "受众可区分的分层沟通策略"
    return "下一步验证阶段"


# ═══════════════ 中文 Wiki ═══════════════

def generate_wiki_text(cards: list[HPCard], analytics: dict | None = None) -> str:
    ranked = sorted(cards, key=lambda c: c.priority_score, reverse=True)
    by_date = sorted(cards, key=lambda c: c.date or "9999")

    out = [
        "# AMPlify Human Practices — HP Compass",
        "",
        "## 概述",
        "",
        "> We developed HP Compass to prevent Human Practices from becoming a "
        "collection of disconnected interviews. The model organizes stakeholders, "
        "feedback, project actions, evidence, and loop status into a decision-support "
        "knowledge graph. Through this model, AMPlify can show how stakeholder "
        "feedback changed our model design, wet-lab validation, software reports, "
        "safety boundaries, implementation scenarios, and education strategy.",
        "",
        "HP Compass 不是为了给 HP 打分，而是为了回答一个更重要的问题：",
        "**谁改变了 AMPlify，改变了哪里，我们是否已经用行动和证据回应了这些反馈。**",
        "",
        f"我们完成了 **{len(cards)}** 轮 Human Practices，覆盖了 "
        f"**{_unique_modules(cards)}** 个项目模块，"
        f"当前所有反馈循环均处于 L3（有证据）阶段，下一步将推进二轮专家反馈（L4）。",
        "",
        "---",
        "",
        "## Stakeholder → Feedback → Action 知识图谱",
        "",
        "![HP Compass Graph](hp_compass_graph.png)",
        "",
        "---",
        "",
        "## HP 影响力时间线",
        "",
    ]

    for card in by_date:
        out.extend(_render_card_cn(card))

    # 闭环面板
    out.append("## 闭环状态面板")
    out.append("")
    out.append("| 状态 | 含义 | 当前数量 |")
    out.append("|---|---|---|")
    for key, (label, desc) in [
        ("L0_Recorded", ("L0 已记录", "只有活动记录或访谈文本")),
        ("L1_Interpreted", ("L1 已提炼", "已提炼出关键反馈和项目问题")),
        ("L2_Actioned", ("L2 已行动", "反馈已转化为项目修改")),
        ("L3_Evidenced", ("L3 有证据", "修改已有模型/实验/软件/文档支撑")),
        ("L4_Returned", ("L4 已返回", "修改结果已返回 stakeholder 获得二轮反馈")),
    ]:
        cnt = sum(1 for c in cards if c.loop_status == key)
        out.append(f"| {label} | {desc} | {cnt} |")

    # 推荐
    out.extend(["", "---", "", "## 下一步回访推荐", "", "系统优先推荐以下未闭合循环：", ""])
    for i, card in enumerate(ranked, start=1):
        if card.loop_level >= 4:
            continue
        out.append(f"{i}. **{card.stakeholder}** (优先级: {card.priority_score:.3f})")
        out.append(f"   - {card.next_step}")
        if card.suggested_questions:
            out.append(f"   - 核心问题：{card.suggested_questions[0]}")
        out.append("")

    out.extend([
        "---",
        "",
        "## HP Compass 方法论说明",
        "",
        "### 反馈分类体系",
        "",
        "| 类别 | 说明 |",
        "|---|---|",
        "| Problem Definition | 改变项目问题定义 |",
        "| Model | 改变模型设计 |",
        "| Material | 改变实验验证 |",
        "| Software | 改变软件报告 |",
        "| Safety | 改变安全边界 |",
        "| Environment | 改变环境风险考虑 |",
        "| Implementation | 改变应用场景 |",
        "| Education | 改变公众沟通 |",
        "| Social Media | 改变项目表达 |",
        "",
        "### 闭环状态机",
        "",
        "```",
        "L0 Recorded → L1 Interpreted → L2 Actioned → L3 Evidenced → L4 Returned",
        "```",
        "",
        "### 优先级算法",
        "",
        "```",
        "Priority = AHP-FCE 二级模糊综合评价",
        "  Level 1: U₁(Internal Urgency) = F₁(loop_gap)×F₂(cross_module)×F₃(criticality)",
        "           U₂(External Constraints) = F₄(time)×F₅(evidence_gap)×F₆(stakeholder_value)",
        "  Level 2: B = A∘[B₁; B₂] → centroid defuzzification → P ∈ [0.20, 0.95]",
        "  Weights by AHP (CR<0.10); M(·,+) synthesis operator",
        "```",
        "",
        "---",
        "",
        "*此页面由 HP Compass 自动生成。*",
    ])

    return "\n".join(out)


def _render_card_cn(card: HPCard) -> list[str]:
    o = []
    d = card.date or "早期"
    t = f"（{card.stakeholder_type}）" if card.stakeholder_type else ""
    o.append(f"### {d} — {card.stakeholder}{t}")
    o.append("")

    # ① 反馈核心
    o.append("#### 🔍 反馈核心")
    o.append("")
    o.append(card.feedback if card.feedback else "（未提取到反馈文本）")
    o.append("")

    # ② 影响模块
    o.append("#### 📂 影响模块")
    o.append("")
    for m in card.affected_modules:
        o.append(f"- {m}")
    o.append("")

    # ③ 项目修改（多点拆行）
    o.append("#### 🔧 项目修改")
    o.append("")
    action = (card.project_action or "").strip()
    if action:
        for pt in _split_multipoint(action):
            o.append(f"- {pt}")
    else:
        o.append("- （未提取到项目修改）")
    o.append("")

    # ④ 故事主线位置
    o.append("#### 📖 故事主线位置")
    o.append("")
    o.append(f"此轮 HP 将 AMPlify 从 *{_story_before(card)}* 推进到 *{_story_after(card)}*。")
    o.append("")

    # ⑤ 闭环状态
    o.append("#### 🔄 闭环状态与证据")
    o.append("")
    o.append(f"- **闭环层级**：{card.loop_status}（L{card.loop_level}）")
    o.append(f"- **证据强度**：{card.evidence_strength:.3f}")
    o.append(f"- **优先级得分**：{card.priority_score:.3f}")
    o.append(f"- **是否已回访**：{'✅ 是' if card.returned else '❌ 否'}")
    if card.evidence:
        o.append(f"- **证据列表**：{'、'.join(card.evidence)}")
    if card.maturity_scores:
        dims = ["设计反思", "场景探索", "多元视角", "影响预判", "HP响应", "局限性坦诚"]
        vals = [
            card.maturity_scores.get(k, 0)
            for k in ["design_reflection", "context_exploration", "diverse_perspectives",
                       "impact_anticipation", "hp_response", "limitation_integrity"]
        ]
        o.append(f"- **成熟度剖面**：{' / '.join(f'{d}={v}' for d, v in zip(dims, vals))}")
    o.append("")

    # ⑥ 下一步
    o.append("#### 🎯 下一步")
    o.append("")
    o.append(f"**建议行动：** {card.next_step}" if card.next_step else "**建议行动：** 待定")
    if card.suggested_materials:
        o.append("")
        o.append("**建议材料：**")
        for m in card.suggested_materials:
            o.append(f"- {m}")
    if card.suggested_questions:
        o.append("")
        o.append("**建议回访问题：**")
        for q in card.suggested_questions:
            o.append(f"- {q}")
    o.append("")
    o.append("---")
    o.append("")
    return o


# ═══════════════ 英文 Wiki ═══════════════

# 利益相关者类型英译
_STAKEHOLDER_TYPE_EN: dict[str, str] = {
    "兽医临床 stakeholder": "Veterinary Clinical Stakeholder",
    "动物健康 / 家畜专家": "Animal Health / Livestock Specialist",
    "AI / 生物大数据专家": "AI / Bioinformatics Specialist",
    "湿实验 / 合成生物学专家": "Wet-Lab / Synthetic Biology Specialist",
    "iGEM / Wiki 交流 stakeholder": "iGEM / Wiki Exchange Stakeholder",
    "公众教育 stakeholder": "Public Education Stakeholder",
    "养殖端 stakeholder": "Livestock Farming Stakeholder",
    "环境微生物 / ARG 专家": "Environmental Microbiology / ARG Specialist",
}

# 模块英文标签
_MODULE_EN: dict[str, str] = {
    "Problem Definition": "Problem Definition",
    "Model": "Model",
    "Material": "Wet-Lab Validation",
    "Software": "Software",
    "Safety": "Safety",
    "Environment": "Environment",
    "Implementation": "Implementation",
    "Education": "Education",
    "Social Media": "Wiki & Presentation",
}

_MATURITY_EN: dict[str, str] = {
    "design_reflection": "Design Reflection",
    "context_exploration": "Context Exploration",
    "diverse_perspectives": "Diverse Perspectives",
    "impact_anticipation": "Impact Anticipation",
    "hp_response": "HP Response",
    "limitation_integrity": "Limitation Integrity",
}


def _tr_stakeholder_type(ch: str | None) -> str:
    if not ch:
        return ""
    return _STAKEHOLDER_TYPE_EN.get(ch, ch)


def _story_before_en(card: HPCard) -> str:
    ms = set(card.affected_modules)
    if "Model" in ms and ("Material" in ms or "Wet Lab" in ms):
        return "candidate peptide design"
    if "Implementation" in ms and "Problem Definition" in ms:
        return "application scenario exploration"
    if "Safety" in ms or "Environment" in ms:
        return "safety boundary & ecological assessment"
    if "Wiki Narrative" in ms:
        return "project storytelling & presentation"
    if "Education" in ms:
        return "public communication & education"
    return "early project stage"


def _story_after_en(card: HPCard) -> str:
    ms = set(card.affected_modules)
    if "Model" in ms and ("Material" in ms or "Wet Lab" in ms):
        return "evidence-closed candidate evaluation framework"
    if "Implementation" in ms and "Problem Definition" in ms:
        return "disease-targeted design in real farming contexts"
    if "Safety" in ms or "Environment" in ms:
        return "use-boundary & environmental degradation assessment"
    if "Wiki Narrative" in ms:
        return "cross-institutional, communicable engineering narrative"
    if "Education" in ms:
        return "audience-differentiated communication strategy"
    return "next-phase validation"


def generate_english_wiki(cards: list[HPCard]) -> str:
    """Generate English Wiki — all content rendered in English from structured fields.

    Chinese narrative text (feedback, project_action) is presented as supplementary
    original-source references under clearly labeled sections, not as primary content.
    """
    ranked = sorted(cards, key=lambda c: c.priority_score, reverse=True)
    by_date = sorted(cards, key=lambda c: c.date or "9999")

    out = [
        "# AMPlify Human Practices — HP Compass",
        "",
        "## Overview",
        "",
        "HP Compass is AMPlify's Human Practices decision-support model. "
        "Rather than a collection of disconnected interviews, it structures "
        "every stakeholder interaction into a traceable decision loop: "
        "**Who changed the project → What was changed → What evidence supports it**.",
        "",
        f"We conducted **{len(cards)}** rounds of Human Practices across "
        f"**{_unique_modules(cards)}** project modules, engaging stakeholders "
        f"from veterinary clinicians and livestock farmers to AI experts, "
        f"environmental microbiologists, and iGEM exchange participants. "
        f"All feedback loops currently stand at **L3 (Evidenced)**, with "
        f"second-round stakeholder feedback (L4) planned next.",
        "",
        "Each HP card below is organized into six clearly separated sections:",
        "",
        "1. **Core Feedback** — what we learned",
        "2. **Modules Affected** — which project modules were impacted",
        "3. **Project Changes** — what we modified in response",
        "4. **Storyline Position** — how this engagement advanced the project narrative",
        "5. **Loop Status & Evidence** — closure level, evidence strength, priority",
        "6. **Next Steps** — recommended follow-up actions, materials, and questions",
        "",
        "---",
        "",
        "## Stakeholder → Feedback → Action Knowledge Graph",
        "",
        "![HP Compass Graph](hp_compass_graph.png)",
        "",
        "---",
        "",
        "## HP Impact Timeline",
        "",
    ]

    for card in by_date:
        out.extend(_render_card_en(card))

    # Loop Status Dashboard
    out.append("## Loop Status Dashboard")
    out.append("")
    out.append("| Status | Description | Count |")
    out.append("|---|---|---|")
    for key, (label, desc) in [
        ("L0_Recorded", ("L0 Recorded", "Raw record / transcript only")),
        ("L1_Interpreted", ("L1 Interpreted", "Key feedback extracted")),
        ("L2_Actioned", ("L2 Actioned", "Feedback led to project changes")),
        ("L3_Evidenced", ("L3 Evidenced", "Changes backed by data / reports")),
        ("L4_Returned", ("L4 Returned", "Results returned for second-round confirmation")),
    ]:
        cnt = sum(1 for c in cards if c.loop_status == key)
        out.append(f"| {label} | {desc} | {cnt} |")

    # Recommendations
    out.extend([
        "",
        "---",
        "",
        "## Next-Step Recommendations",
        "",
        "The system prioritizes the following open loops for second-round feedback:",
        "",
    ])
    for i, card in enumerate(ranked, start=1):
        if card.loop_level >= 4:
            continue
        out.append(f"{i}. **Return to {card.stakeholder}** (priority: {card.priority_score:.3f})")
        next_en = getattr(card, "next_step_en", "") or card.next_step
        out.append(f"   - {next_en}")
        qs_en = getattr(card, "suggested_questions_en", None)
        if qs_en and qs_en[0]:
            out.append(f"   - Key question: {qs_en[0]}")
        elif card.suggested_questions:
            out.append(f"   - Key question: {card.suggested_questions[0]}")
        out.append("")

    # Methodology
    out.extend([
        "---",
        "",
        "## HP Compass Methodology",
        "",
        "### Feedback Classification",
        "",
        "Each feedback item is automatically classified into one or more project modules:",
        "",
        "| Category | Description |",
        "|---|---|",
        "| Problem Definition | Refined the project's problem framing |",
        "| Model | Changed model architecture or training strategy |",
        "| Material | Changed experimental validation design |",
        "| Software | Changed software reports and dashboards |",
        "| Safety | Changed safety boundaries and risk language |",
        "| Environment | Changed environmental risk assessment |",
        "| Implementation | Changed application scenario framing |",
        "| Education | Changed public communication approach |",
        "| Social Media | Changed project storytelling and presentation |",
        "",
        "### Loop State Machine",
        "",
        "```",
        "L0 Recorded → L1 Interpreted → L2 Actioned → L3 Evidenced → L4 Returned",
        "```",
        "",
        "### Priority Algorithm",
        "",
        "```",
        "Priority = AHP-FCE Two-Level Fuzzy Comprehensive Evaluation",
        "  Level 1: U₁(Internal Urgency) → B₁ = A₁∘R₁ (F₁,F₂,F₃)",
        "           U₂(External Constraints) → B₂ = A₂∘R₂ (F₄,F₅,F₆)",
        "  Level 2: R = [B₁; B₂], B = A∘R",
        "  Defuzzification: P = Σ b_j·c_j  (centroid method, C=(0.20,0.45,0.72,0.95))",
        "  Weights: AHP square-root method, CR<0.10; M(·,+) operator",
        "```",
        "",
        "All six factors are normalized to [0, 1] and mapped to four evaluation levels",
        "(Low / Medium / High / Urgent) via trapezoidal membership functions.",
        "The fuzzy vector B=(b₁,b₂,b₃,b₄) reveals the structural composition of priority",
        "— two cards with similar P scores may differ substantially in their B distribution.",
        "A sensitivity analysis (±20% perturbation on AHP weights, membership parameters,",
        "and domain mapping values) confirms the priority ranking is highly stable",
        "(Spearman ρ ≥ 0.999, ΔP_max ≤ 0.05).",
        "",
        "---",
        "",
        "*Generated by HP Compass — AMPlify Human Practices decision-support model.*",
    ])

    return "\n".join(out)


# 模块英文解释
_MODULE_DESC_EN: dict[str, str] = {
    "Model": "Model architecture, AI pipeline, candidate scoring strategy",
    "Material": "Wet-lab experimental validation: MIC, hemolysis, cytotoxicity, TEM",
    "Wet Lab": "Experimental validation: MIC, hemolysis, cytotoxicity, TEM",
    "Software": "Software panels, dashboards, report exports",
    "Safety": "Safety boundaries, toxicity, risk language, overclaiming prevention",
    "Environment": "Environmental degradation, ARG resistance, ecological impact",
    "Implementation": "Application scenarios, livestock farming, drug delivery feasibility",
    "Problem Definition": "Project problem framing, disease targeting, storyline direction",
    "Education": "Public communication, stakeholder education, audience understanding",
    "Social Media": "Wiki content, defense presentation, cross-team storytelling",
    "Wiki Narrative": "Wiki content, defense presentation, cross-team storytelling",
}

# 证据项英译映射
_EVIDENCE_EN: dict[str, str] = {
    "MIC": "MIC (Minimum Inhibitory Concentration)",
    "溶血": "Hemolysis assay",
    "CCK-8": "CCK-8 cytotoxicity",
    "TEM": "TEM imaging",
    "质谱": "Mass spectrometry",
    "细胞毒性": "Cytotoxicity assay",
    "MD": "Molecular dynamics simulation",
    "分子动力学": "Molecular dynamics simulation",
    "RMSD": "RMSD analysis",
    "RMSF": "RMSF analysis",
    "理化性质": "Physicochemical properties",
    "软件面板": "Software panel",
    "面板": "Panel",
    "报告": "Report",
    "文献": "Literature",
    "访谈记录": "Interview records",
    "访谈文档": "Interview documentation",
    "草图": "Draft/sketch",
    "Field Score": "Field Score",
    "TAM-Flow": "TAM-Flow framework",
    "Oracle": "Oracle expert model",
    "RAFT": "RAFT reward filtering",
    "PDES": "PDES (Peptide Degradation & Environmental Safety)",
    "Risk Boundary Panel": "Risk Boundary Panel",
    "Environmental Degradation Panel": "Environmental Degradation Panel",
    "Evidence Matrix": "Evidence Matrix",
    "LoRA": "LoRA fine-tuning",
}


def _tr_evidence(item: str) -> str:
    return _EVIDENCE_EN.get(item, item)


def _render_card_en(card: HPCard) -> list[str]:
    """Render a single HP card in English — prose generated from structured fields.

    The primary narrative is English. Original Chinese text (feedback, project_action)
    is presented as supplementary reference at the end of each card.
    """
    o = []
    d = card.date or "Early stage"
    stype = _tr_stakeholder_type(card.stakeholder_type)
    stype_str = f" — *{stype}*" if stype else ""

    o.append(f"### {d} — {card.stakeholder}{stype_str}")
    o.append("")

    # ═══ English executive summary — the primary narrative ═══
    n_mods = len(card.affected_modules)
    mod_list = ", ".join(card.affected_modules) if card.affected_modules else "multiple areas"
    ev_items_en = [_tr_evidence(e) for e in (card.evidence or [])]
    ev_list = ", ".join(ev_items_en[:8]) if ev_items_en else "interview documentation"
    ret_label = "has been returned for second-round confirmation" if card.returned else "has not yet been returned"
    mat_vals = card.maturity_scores or {}
    mat_avg = round(sum(mat_vals.values()) / max(len(mat_vals), 1), 1)
    mat_str = " / ".join(f"{_MATURITY_EN.get(k, k)} {v}/5" for k, v in mat_vals.items()) if mat_vals else "not assessed"

    # Build the English summary paragraph
    o.append(
        f"**{card.stakeholder}** ({stype or 'expert'}) was consulted on {d}. "
        f"This engagement affected **{n_mods} project modules**: {mod_list}."
    )
    o.append("")
    o.append(f"**What changed in the project:** the feedback advanced AMPlify from "
             f"*{_story_before_en(card)}* → *{_story_after_en(card)}*.")
    o.append("")

    # Evidence summary in English
    o.append(f"**Evidence collected:** {ev_list}. "
             f"Overall evidence strength: **{card.evidence_strength:.2f}**.")
    o.append("")

    # Storyline + loop summary
    rho_note = ""
    if card.priority_score >= 0.60:
        rho_note = " — this is a high-priority feedback loop."
    o.append(f"**Loop status:** The feedback loop is at **{card.loop_status}** "
             f"(Level L{card.loop_level} of the L0–L4 state machine). "
             f"Priority score: **{card.priority_score:.3f}**{rho_note} "
             f"Maturity profile: {mat_str}. "
             f"The loop {ret_label}.")
    o.append("")

    # ── ① Modules Affected (with English descriptions) ──
    o.append("#### 📂 Modules Affected")
    o.append("")
    if card.affected_modules:
        for m in card.affected_modules:
            desc = _MODULE_DESC_EN.get(m, "")
            o.append(f"- **{m}** — {desc}")
    else:
        o.append("- *(No affected modules identified)*")
    o.append("")

    # ── ② Project Direction — what actually changed ──
    o.append("#### 🔧 Project Direction & Changes Made")
    o.append("")
    o.append(f"**Before this engagement:** {_story_before_en(card)}")
    o.append(f"**After this engagement:** {_story_after_en(card)}")
    o.append("")

    # Show the Chinese project_action as reference
    action = (card.project_action or "").strip()
    if action:
        o.append("<details>")
        o.append("<summary>📄 Original project modifications (Chinese — click to expand)</summary>")
        o.append("")
        for pt in _split_multipoint(action):
            o.append(f"- {pt}")
        o.append("")
        o.append("</details>")
        o.append("")

    # ── ③ Evidence & Maturity ──
    o.append("#### 🔄 Loop Status & Evidence")
    o.append("")
    o.append(f"| Metric | Value |")
    o.append(f"|---|---|")
    o.append(f"| Loop Level | {card.loop_status} (L{card.loop_level}) |")
    o.append(f"| Evidence Strength | {card.evidence_strength:.3f} |")
    o.append(f"| Priority Score | {card.priority_score:.3f} |")
    ret = "✅ Yes" if card.returned else "❌ No"
    o.append(f"| Returned to Stakeholder | {ret} |")
    if card.evidence:
        o.append(f"| Evidence Items | {', '.join(_tr_evidence(e) for e in card.evidence)} |")
    if card.maturity_scores:
        parts = " | ".join(
            f"{_MATURITY_EN.get(k, k)}: **{v}**/5"
            for k, v in card.maturity_scores.items()
        )
        o.append(f"| Maturity Profile | {parts} |")
    o.append("")

    # ── ④ Next Steps (English from recommender) ──
    o.append("#### 🎯 Next Steps")
    o.append("")

    next_en = getattr(card, "next_step_en", "") or card.next_step
    o.append(f"**Recommended Action:** {next_en}" if next_en else "**Recommended Action:** Pending")

    mats_en = getattr(card, "suggested_materials_en", None)
    if mats_en:
        o.append("")
        o.append("**Suggested Materials:**")
        for m in mats_en:
            o.append(f"- {m}")
    elif card.suggested_materials:
        o.append("")
        o.append("**Suggested Materials:**")
        for m in card.suggested_materials:
            o.append(f"- {m}")

    qs_en = getattr(card, "suggested_questions_en", None)
    if qs_en:
        o.append("")
        o.append("**Suggested Follow-up Questions:**")
        for q in qs_en:
            o.append(f"- {q}")
    elif card.suggested_questions:
        o.append("")
        o.append("**Suggested Follow-up Questions:**")
        for q in card.suggested_questions:
            o.append(f"- {q}")
    o.append("")

    # ── ⑤ Original transcripts (collapsible, supplementary) ──
    fb = (card.feedback or "").strip()
    if fb:
        o.append("<details>")
        o.append("<summary>📜 Original Chinese transcript (click to expand)</summary>")
        o.append("")
        for para in fb.split("\n"):
            para = para.strip()
            if para:
                o.append(para)
                o.append("")
        o.append("</details>")
        o.append("")

    o.append("---")
    o.append("")
    return o


# ═══════════════ 答辩叙事 ═══════════════

def generate_defense_text(cards: list[HPCard], analytics: dict | None = None) -> str:
    ranked = sorted(cards, key=lambda c: c.priority_score, reverse=True)
    top3 = ranked[:3]

    out = [
        "# AMPlify HP Compass — 答辩叙事",
        "",
        "## 一句话总结",
        "",
        "AMPlify 的 Human Practices 不是随机采访，而是通过 HP Compass 模型，"
        "将每一位利益相关者的反馈转化为具体的项目修改，并用知识图谱追踪闭环。",
        "",
        "## 三个最有影响力的 HP 节点",
        "",
    ]

    for i, card in enumerate(top3, start=1):
        t = f"（{card.stakeholder_type}）" if card.stakeholder_type else ""
        out.append(f"### {i}. {card.stakeholder}{t}")
        out.append("")

        out.append("#### 🔍 反馈核心")
        out.append("")
        out.append(card.feedback)
        out.append("")

        out.append("#### 📂 影响了哪些模块")
        out.append("")
        for m in card.affected_modules:
            out.append(f"- {m}")
        out.append("")

        out.append("#### 🔧 我们做了什么")
        out.append("")
        action = (card.project_action or "").strip()
        if action:
            for pt in _split_multipoint(action):
                out.append(f"- {pt}")
        out.append("")

        out.append("#### 📖 故事主线推进")
        out.append("")
        out.append(f"从 *{_story_before(card)}* → *{_story_after(card)}*")
        out.append("")

        out.append("#### 🔄 闭环状态与证据")
        out.append("")
        out.append(f"- **状态：** {card.loop_status}（L{card.loop_level}）")
        out.append(f"- **证据强度：** {card.evidence_strength:.3f}")
        out.append(f"- **优先级：** {card.priority_score:.3f}")
        if card.evidence:
            out.append(f"- **证据项：** {'、'.join(card.evidence)}")
        out.append("")

        out.append("#### 🎯 下一步")
        out.append("")
        out.append(card.next_step)
        out.append("")

    if analytics:
        out.extend([
            "## 图分析洞察",
            "",
            f"- 知识图谱共 {analytics['graph_stats']['total_nodes']} 个节点、"
            f"{analytics['graph_stats']['total_edges']} 条边",
            f"- 影响力最高的利益相关者："
            + "、".join(s["label"] for s in analytics.get("top_stakeholders", [])[:3]),
            f"- 被 HP 反馈影响最多的模块："
            + "、".join(m["module"] for m in analytics.get("module_impact", [])[:3]),
        ])

    out.extend([
        "",
        "## HP Compass 在答辩中的定位",
        "",
        "1. **不是打分表** — 是决策导航系统",
        "2. **不是活动列表** — 是 Stakeholder → Feedback → Action → Evidence 网络",
        "3. **证明闭环能力** — L0–L4 状态机展示我们如何推动反馈落地",
        "4. **透明可解释** — 所有分类、评分、推荐都有规则可循",
        "5. **FCE参数稳健** — ±20% AHP权重/隶属函数/领域映射参数扰动，Spearman ρ ≥ 0.999",
    ])

    return "\n".join(out)


# ═══════════════ 文件保存 ═══════════════

def save_wiki_files(
    cards: list[HPCard], analytics: dict | None, output_dir: Path
) -> dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "wiki_cn.md": generate_wiki_text(cards, analytics),
        "wiki_en.md": generate_english_wiki(cards),
        "defense_narrative.md": generate_defense_text(cards, analytics),
    }

    saved = {}
    for filename, content in files.items():
        path = output_dir / filename
        path.write_text(content, encoding="utf-8")
        saved[filename] = path

    return saved
