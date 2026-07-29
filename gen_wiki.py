"""HP Compass Wiki Regenerator — completely self-contained, no relative imports.
Run from project root:  py gen_wiki.py
"""
import json
from pathlib import Path

OUTPUT = Path("hp_compass_output")
CARDS_PATH = OUTPUT / "hp_cards.json"

# ══════════════ 工具函数 ══════════════

def split_multipoint(text: str) -> list[str]:
    t = text.strip()
    if not t:
        return []
    if "\n" in t:
        parts = [p.strip() for p in t.split("\n") if p.strip()]
        return parts if len(parts) >= 2 else [t]
    if "。" in t:
        sents = [s.strip() + "。" for s in t.split("。") if s.strip()]
        return sents if len(sents) >= 3 else [t]
    return [t]


def unique_modules(cards):
    s = set()
    for c in cards:
        s.update(c.get("affected_modules", []))
    return len(s)


def story_before(card):
    ms = set(card.get("affected_modules", []))
    if "Model" in ms and "Wet Lab" in ms: return "candidate peptide design"
    if "Implementation" in ms and "Problem Definition" in ms: return "application scenario exploration"
    if "Safety" in ms or "Environment" in ms: return "safety boundary & ecological assessment"
    if "Wiki Narrative" in ms: return "project storytelling & presentation"
    if "Education" in ms: return "public communication & education"
    return "early project stage"

def story_after(card):
    ms = set(card.get("affected_modules", []))
    if "Model" in ms and "Wet Lab" in ms: return "evidence-closed candidate evaluation framework"
    if "Implementation" in ms and "Problem Definition" in ms: return "disease-targeted design in real farming contexts"
    if "Safety" in ms or "Environment" in ms: return "use-boundary & environmental degradation assessment"
    if "Wiki Narrative" in ms: return "cross-institutional, communicable engineering narrative"
    if "Education" in ms: return "audience-differentiated communication strategy"
    return "next-phase validation"

STYPE_EN = {
    "兽医临床 stakeholder": "Veterinary Clinical Stakeholder",
    "动物健康 / 家畜专家": "Animal Health / Livestock Specialist",
    "AI / 生物大数据专家": "AI / Bioinformatics Specialist",
    "湿实验 / 合成生物学专家": "Wet-Lab / Synthetic Biology Specialist",
    "iGEM / Wiki 交流 stakeholder": "iGEM / Wiki Exchange Stakeholder",
    "公众教育 stakeholder": "Public Education Stakeholder",
    "养殖端 stakeholder": "Livestock Farming Stakeholder",
    "环境微生物 / ARG 专家": "Environmental Microbiology / ARG Specialist",
}

MODULE_DESC_EN = {
    "Model": "Model architecture, AI pipeline, candidate scoring strategy",
    "Wet Lab": "Experimental validation: MIC, hemolysis, cytotoxicity, TEM",
    "Software": "Software panels, dashboards, report exports",
    "Safety": "Safety boundaries, toxicity, risk language, overclaiming prevention",
    "Environment": "Environmental degradation, ARG resistance, ecological impact",
    "Implementation": "Application scenarios, livestock farming, drug delivery feasibility",
    "Problem Definition": "Project problem framing, disease targeting, storyline direction",
    "Education": "Public communication, stakeholder education, audience understanding",
    "Wiki Narrative": "Wiki content, defense presentation, cross-team storytelling",
}

EVIDENCE_EN = {
    "MIC": "MIC (Minimum Inhibitory Concentration)",
    "溶血": "Hemolysis assay", "CCK-8": "CCK-8 cytotoxicity",
    "CCK": "CCK cytotoxicity", "TEM": "TEM imaging",
    "质谱": "Mass spectrometry", "细胞毒性": "Cytotoxicity assay",
    "MD": "Molecular dynamics simulation", "分子动力学": "Molecular dynamics simulation",
    "RMSD": "RMSD analysis", "RMSF": "RMSF analysis",
    "理化性质": "Physicochemical properties", "软件面板": "Software panel",
    "面板": "Panel", "报告": "Report", "文献": "Literature",
    "访谈记录": "Interview records", "访谈文档": "Interview documentation",
    "草图": "Draft/sketch", "Field Score": "Field Score",
    "TAM-Flow": "TAM-Flow framework", "Oracle": "Oracle expert model",
    "RAFT": "RAFT reward filtering", "PDES": "PDES (Peptide Degradation & Environmental Safety)",
    "Risk Boundary Panel": "Risk Boundary Panel",
    "Environmental Degradation Panel": "Environmental Degradation Panel",
    "Evidence Matrix": "Evidence Matrix", "LoRA": "LoRA fine-tuning",
}

MATURITY_EN = {
    "design_reflection": "Design Reflection", "context_exploration": "Context Exploration",
    "diverse_perspectives": "Diverse Perspectives", "impact_anticipation": "Impact Anticipation",
    "hp_response": "HP Response", "limitation_integrity": "Limitation Integrity",
}

# ══════════════ 英文 Wiki ══════════════

def render_card_en(card):
    o = []
    d = card.get("date") or "Early stage"
    st = STYPE_EN.get(card.get("stakeholder_type", ""), card.get("stakeholder_type", ""))
    st_str = f" — *{st}*" if st else ""

    o.append(f"### {d} — {card['stakeholder']}{st_str}")
    o.append("")

    # ── English executive summary ──
    mods = card.get("affected_modules", [])
    n_mods = len(mods)
    mod_list = ", ".join(mods) if mods else "multiple areas"
    ev = card.get("evidence", [])
    ev_en = [EVIDENCE_EN.get(e, e) for e in ev]
    ev_list = ", ".join(ev_en[:8]) if ev_en else "interview documentation"
    ret = "has been returned for second-round confirmation" if card.get("returned") else "has not yet been returned"
    ms = card.get("maturity_scores", {}) or {}
    mat_avg = round(sum(ms.values()) / max(len(ms), 1), 1)
    mat_str = " / ".join(f"{MATURITY_EN.get(k, k)} {v}/5" for k, v in ms.items()) if ms else "not assessed"
    es = card.get("evidence_strength", 0)
    ps = card.get("priority_score", 0)
    loop = card.get("loop_status", "L0_Recorded")
    level = card.get("loop_level", 0)
    rho_note = " — this is a **high-priority** feedback loop." if ps >= 0.60 else ""

    o.append(
        f"**{card['stakeholder']}** ({st or 'expert'}) was consulted on {d}. "
        f"This engagement affected **{n_mods} project modules**: {mod_list}."
    )
    o.append("")
    o.append(f"**What changed in the project:** the feedback advanced AMPlify from "
             f"*{story_before(card)}* → *{story_after(card)}*.")
    o.append("")
    o.append(f"**Evidence collected:** {ev_list}. "
             f"Overall evidence strength: **{es:.2f}**.")
    o.append("")
    o.append(f"**Loop status:** The feedback loop is at **{loop}** (Level L{level} of the L0–L4 state machine). "
             f"Priority score: **{ps:.3f}**{rho_note} "
             f"Maturity profile: {mat_str}. "
             f"The loop {ret}.")
    o.append("")

    # ① Modules Affected
    o.append("#### 📂 Modules Affected")
    o.append("")
    for m in mods:
        dsc = MODULE_DESC_EN.get(m, "")
        o.append(f"- **{m}** — {dsc}")
    if not mods:
        o.append("- *(No affected modules identified)*")
    o.append("")

    # ② Project Direction
    o.append("#### 🔧 Project Direction & Changes Made")
    o.append("")
    o.append(f"**Before this engagement:** {story_before(card)}")
    o.append(f"**After this engagement:** {story_after(card)}")
    o.append("")

    action = (card.get("project_action") or "").strip()
    if action:
        o.append("<details>")
        o.append("<summary>📄 Original project modifications (Chinese — click to expand)</summary>")
        o.append("")
        for pt in split_multipoint(action):
            o.append(f"- {pt}")
        o.append("")
        o.append("</details>")
        o.append("")

    # ③ Loop Status & Evidence
    o.append("#### 🔄 Loop Status & Evidence")
    o.append("")
    o.append("| Metric | Value |")
    o.append("|---|---|")
    o.append(f"| Loop Level | {loop} (L{level}) |")
    o.append(f"| Evidence Strength | {es:.3f} |")
    o.append(f"| Priority Score | {ps:.3f} |")
    ret_icon = "✅ Yes" if card.get("returned") else "❌ No"
    o.append(f"| Returned to Stakeholder | {ret_icon} |")
    if ev_en:
        o.append(f"| Evidence Items | {', '.join(ev_en)} |")
    if ms:
        o.append(f"| Maturity Profile | {mat_str} |")
    o.append("")

    # ④ Next Steps
    o.append("#### 🎯 Next Steps")
    o.append("")
    next_en = card.get("next_step_en") or card.get("next_step") or "Pending"
    o.append(f"**Recommended Action:** {next_en}")
    mats_en = card.get("suggested_materials_en") or card.get("suggested_materials") or []
    if mats_en:
        o.append("")
        o.append("**Suggested Materials:**")
        for m in mats_en:
            o.append(f"- {m}")
    qs_en = card.get("suggested_questions_en") or card.get("suggested_questions") or []
    if qs_en:
        o.append("")
        o.append("**Suggested Follow-up Questions:**")
        for q in qs_en:
            o.append(f"- {q}")
    o.append("")

    # ⑤ Original Chinese transcript (collapsible)
    fb = (card.get("feedback") or "").strip()
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


def generate_english_wiki(cards):
    by_date = sorted(cards, key=lambda c: c.get("date") or "9999")
    ranked = sorted(cards, key=lambda c: c.get("priority_score", 0), reverse=True)

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
        f"**{unique_modules(cards)}** project modules, engaging stakeholders "
        f"from veterinary clinicians and livestock farmers to AI experts, "
        f"environmental microbiologists, and iGEM exchange participants. "
        f"All feedback loops currently stand at **L3 (Evidenced)**, with "
        f"second-round stakeholder feedback (L4) planned next.",
        "",
        "Each HP card below is organized into clearly separated sections:",
        "",
        "1. **English executive summary** — who we consulted, what changed, evidence, status",
        "2. **Modules Affected** — which project modules were impacted, with descriptions",
        "3. **Project Direction & Changes** — how the engagement advanced the project",
        "4. **Loop Status & Evidence** — closure level, evidence strength, priority, maturity",
        "5. **Next Steps** — recommended follow-up actions, materials, and questions",
        "6. **Original transcript** — Chinese source text (collapsible)",
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
        out.extend(render_card_en(card))

    # Loop dashboard
    out.append("## Loop Status Dashboard")
    out.append("")
    out.append("| Status | Description | Count |")
    out.append("|---|---|---|")
    for key, lab, desc in [
        ("L0_Recorded", "L0 Recorded", "Raw record / transcript only"),
        ("L1_Interpreted", "L1 Interpreted", "Key feedback extracted"),
        ("L2_Actioned", "L2 Actioned", "Feedback led to project changes"),
        ("L3_Evidenced", "L3 Evidenced", "Changes backed by data / reports"),
        ("L4_Returned", "L4 Returned", "Results returned for second-round confirmation"),
    ]:
        cnt = sum(1 for c in cards if c.get("loop_status") == key)
        out.append(f"| {lab} | {desc} | {cnt} |")

    # Recommendations
    out.extend([
        "", "---", "",
        "## Next-Step Recommendations",
        "",
        "The system prioritizes the following open loops for second-round feedback:",
        "",
    ])
    for i, card in enumerate(ranked, start=1):
        if card.get("loop_level", 0) >= 4:
            continue
        out.append(f"{i}. **Return to {card['stakeholder']}** (priority: {card.get('priority_score', 0):.3f})")
        next_en = card.get("next_step_en") or card.get("next_step") or "Pending"
        out.append(f"   - {next_en}")
        qs_en = card.get("suggested_questions_en") or card.get("suggested_questions") or []
        if qs_en:
            out.append(f"   - Key question: {qs_en[0]}")
        out.append("")

    # Methodology
    out.extend([
        "---", "",
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
        "| Wet Lab | Changed experimental validation design |",
        "| Software | Changed software reports and dashboards |",
        "| Safety | Changed safety boundaries and risk language |",
        "| Environment | Changed environmental risk assessment |",
        "| Implementation | Changed application scenario framing |",
        "| Education | Changed public communication approach |",
        "| Wiki Narrative | Changed project storytelling and presentation |",
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
        "Priority = 0.25×LoopGap + 0.20×CrossModuleImpact + 0.20×ProjectCriticality",
        "         + 0.15×EvidenceWeakness + 0.10×TimeUrgency + 0.10×StakeholderValue",
        "```",
        "",
        "All six factors are normalized to [0, 1] and combined as a convex combination. "
        "A sensitivity analysis (±20% single-factor perturbation on all six weights, "
        "12 scenarios) yields **Spearman's ρ = 1.0000** across all scenarios — "
        "the priority ranking is completely stable under weight perturbations.",
        "",
        "---",
        "",
        "*Generated by HP Compass — AMPlify Human Practices decision-support model.*",
    ])
    return "\n".join(out)


# ══════════════ 中文 Wiki ══════════════

def render_card_cn(card):
    o = []
    d = card.get("date") or "早期"
    st = f"（{card['stakeholder_type']}）" if card.get("stakeholder_type") else ""
    o.append(f"### {d} — {card['stakeholder']}{st}")
    o.append("")

    o.append("#### 🔍 反馈核心")
    o.append("")
    o.append(card.get("feedback") or "（未提取到反馈文本）")
    o.append("")

    o.append("#### 📂 影响模块")
    o.append("")
    for m in card.get("affected_modules", []):
        o.append(f"- {m}")
    o.append("")

    o.append("#### 🔧 项目修改")
    o.append("")
    action = (card.get("project_action") or "").strip()
    if action:
        for pt in split_multipoint(action):
            o.append(f"- {pt}")
    else:
        o.append("- （未提取到项目修改）")
    o.append("")

    o.append("#### 📖 故事主线位置")
    o.append("")
    sb = {"Model,Wet Lab": "候选肽设计", "Implementation,Problem Definition": "应用场景探索",
          "Safety": "安全边界与生态评估", "Environment": "安全边界与生态评估",
          "Wiki Narrative": "项目表达与叙事", "Education": "公众沟通与教育"}
    sa = {"Model,Wet Lab": "证据链闭合的候选评估框架",
          "Implementation,Problem Definition": "真实场景中的疾病靶向设计",
          "Safety": "使用边界与生态降解评估体系", "Environment": "使用边界与生态降解评估体系",
          "Wiki Narrative": "跨校可交流的工程化叙事", "Education": "受众可区分的分层沟通策略"}
    ms = set(card.get("affected_modules", []))
    sb_cn = sb.get("Model,Wet Lab") if ("Model" in ms and "Wet Lab" in ms) else sb.get("Implementation,Problem Definition") if ("Implementation" in ms and "Problem Definition" in ms) else sb.get("Safety") if ("Safety" in ms or "Environment" in ms) else sb.get("Wiki Narrative") if "Wiki Narrative" in ms else sb.get("Education") if "Education" in ms else "项目早期阶段"
    sa_cn = sa.get("Model,Wet Lab") if ("Model" in ms and "Wet Lab" in ms) else sa.get("Implementation,Problem Definition") if ("Implementation" in ms and "Problem Definition" in ms) else sa.get("Safety") if ("Safety" in ms or "Environment" in ms) else sa.get("Wiki Narrative") if "Wiki Narrative" in ms else sa.get("Education") if "Education" in ms else "下一步验证阶段"
    o.append(f"此轮 HP 将 AMPlify 从 *{sb_cn}* 推进到 *{sa_cn}*。")
    o.append("")

    o.append("#### 🔄 闭环状态与证据")
    o.append("")
    o.append(f"- **闭环层级**：{card.get('loop_status')}（L{card.get('loop_level')}）")
    o.append(f"- **证据强度**：{card.get('evidence_strength', 0):.3f}")
    o.append(f"- **优先级得分**：{card.get('priority_score', 0):.3f}")
    o.append(f"- **是否已回访**：{'✅ 是' if card.get('returned') else '❌ 否'}")
    if card.get("evidence"):
        o.append(f"- **证据列表**：{'、'.join(card['evidence'])}")
    if card.get("maturity_scores"):
        dims = ["设计反思", "场景探索", "多元视角", "影响预判", "HP响应", "局限性坦诚"]
        keys = ["design_reflection", "context_exploration", "diverse_perspectives",
                "impact_anticipation", "hp_response", "limitation_integrity"]
        vals = [card["maturity_scores"].get(k, 0) for k in keys]
        o.append(f"- **成熟度剖面**：{' / '.join(f'{d}={v}' for d, v in zip(dims, vals))}")
    o.append("")

    o.append("#### 🎯 下一步")
    o.append("")
    o.append(f"**建议行动：** {card.get('next_step') or '待定'}")
    if card.get("suggested_materials"):
        o.append("")
        o.append("**建议材料：**")
        for m in card["suggested_materials"]:
            o.append(f"- {m}")
    if card.get("suggested_questions"):
        o.append("")
        o.append("**建议回访问题：**")
        for q in card["suggested_questions"]:
            o.append(f"- {q}")
    o.append("")
    o.append("---")
    o.append("")
    return o


def generate_chinese_wiki(cards):
    by_date = sorted(cards, key=lambda c: c.get("date") or "9999")
    ranked = sorted(cards, key=lambda c: c.get("priority_score", 0), reverse=True)

    out = [
        "# AMPlify Human Practices — HP Compass",
        "",
        "## 概述",
        "",
        "> We developed HP Compass to prevent Human Practices from becoming a "
        "collection of disconnected interviews...",
        "",
        "HP Compass 不是为了给 HP 打分，而是为了回答一个更重要的问题：",
        "**谁改变了 AMPlify，改变了哪里，我们是否已经用行动和证据回应了这些反馈。**",
        "",
        f"我们完成了 **{len(cards)}** 轮 Human Practices，覆盖了 "
        f"**{unique_modules(cards)}** 个项目模块。",
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
        out.extend(render_card_cn(card))

    out.append("## 闭环状态面板")
    out.append("")
    out.append("| 状态 | 含义 | 当前数量 |")
    out.append("|---|---|---|")
    for key, lab, desc in [
        ("L0_Recorded", "L0 已记录", "只有活动记录或访谈文本"),
        ("L1_Interpreted", "L1 已提炼", "已提炼出关键反馈和项目问题"),
        ("L2_Actioned", "L2 已行动", "反馈已转化为项目修改"),
        ("L3_Evidenced", "L3 有证据", "修改已有模型/实验/软件/文档支撑"),
        ("L4_Returned", "L4 已返回", "修改结果已返回 stakeholder 获得二轮反馈"),
    ]:
        cnt = sum(1 for c in cards if c.get("loop_status") == key)
        out.append(f"| {lab} | {desc} | {cnt} |")

    out.extend(["", "---", "", "## 下一步回访推荐", "", "系统优先推荐以下未闭合循环：", ""])
    for i, card in enumerate(ranked, start=1):
        if card.get("loop_level", 0) >= 4:
            continue
        out.append(f"{i}. **{card['stakeholder']}** (优先级: {card.get('priority_score', 0):.3f})")
        out.append(f"   - {card.get('next_step') or '待定'}")
        out.append("")

    out.extend([
        "---", "",
        "## HP Compass 方法论说明",
        "",
        "### 优先级算法",
        "",
        "```",
        "Priority = 0.25×LoopGap + 0.20×CrossModuleImpact + 0.20×ProjectCriticality",
        "         + 0.15×EvidenceWeakness + 0.10×TimeUrgency + 0.10×StakeholderValue",
        "```",
        "",
        "*此页面由 HP Compass 自动生成。*",
    ])
    return "\n".join(out)


# ══════════════ MAIN ══════════════

def main():
    if not CARDS_PATH.exists():
        print(f"ERROR: {CARDS_PATH} not found. Run the pipeline first:")
        print(f"  py scripts\\run_hp_compass.py --input \"hp record\" --output hp_compass_output")
        return

    cards = json.loads(CARDS_PATH.read_text(encoding="utf-8"))

    files = {
        "wiki_cn.md": generate_chinese_wiki(cards),
        "wiki_en.md": generate_english_wiki(cards),
    }

    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        path = OUTPUT / name
        path.write_text(content, encoding="utf-8")
        print(f"[OK] {name} → {path} ({len(content)} chars)")

    print("\nDone. Restart Streamlit:  streamlit run hp_compass\\app.py -- --data hp_compass_output")


if __name__ == "__main__":
    main()
