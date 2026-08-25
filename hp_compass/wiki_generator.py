"""Wiki 文案自动生成模块

- 中文 Wiki 由结构化字段生成，按信息区分节
- 英文 Wiki 与答辩叙事由 LLM 直接撰写（处理模式为 llm 时可用）
- 多点内容以 markdown 列表呈现，零截断
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


def _split_rounds(text: str) -> list[str]:
    """把合并后的文本按回访分隔符拆成各轮内容。"""
    if not text:
        return []
    return [part.strip() for part in text.split("\n\n【二轮回访】\n")]


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

    return "\n".join(out)


def _render_card_cn(card: HPCard) -> list[str]:
    o = []
    d = card.date or "早期"
    t = f"（{card.stakeholder_type}）" if card.stakeholder_type else ""
    o.append(f"### {d} — {card.stakeholder}{t}")
    o.append("")

    # 回访访问记录（多轮访谈如实分开展示）
    for visit in card.visits:
        vd = visit.get("date") or "日期未知"
        o.append(f"> ↩ **二轮回访**：{vd}（{visit.get('source_file', '')}）")
    if card.visits:
        o.append("")

    # ① 反馈核心（两轮分开写）
    o.append("#### 🔍 反馈核心")
    o.append("")
    feedback_rounds = _split_rounds(card.feedback)
    if len(feedback_rounds) > 1 and card.visits:
        visit_date = card.visits[0].get("date") or "日期未知"
        o.append(f"**第一轮（{d}）**")
        o.append("")
        o.append(feedback_rounds[0] if feedback_rounds[0] else "（未提取到反馈文本）")
        o.append("")
        o.append(f"**第二轮回访（{visit_date}）**")
        o.append("")
        o.append(feedback_rounds[1])
        o.append("")
    else:
        o.append(card.feedback if card.feedback else "（未提取到反馈文本）")
        o.append("")

    # ② 影响模块
    o.append("#### 📂 影响模块")
    o.append("")
    for m in card.affected_modules:
        o.append(f"- {m}")
    o.append("")

    # ③ 项目修改（两轮分开写，多点拆行）
    o.append("#### 🔧 项目修改")
    o.append("")
    action_rounds = _split_rounds(card.project_action)
    if len(action_rounds) > 1 and card.visits:
        visit_date = card.visits[0].get("date") or "日期未知"
        o.append(f"**第一轮（{d}）**")
        o.append("")
        for pt in _split_multipoint(action_rounds[0]) or ["（未提取到项目修改）"]:
            o.append(f"- {pt}")
        o.append("")
        o.append(f"**第二轮回访（{visit_date}）**")
        o.append("")
        for pt in _split_multipoint(action_rounds[1]):
            o.append(f"- {pt}")
        o.append("")
    else:
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
    o.append("---")
    o.append("")
    return o


# ═══════════════ 英文 Wiki ═══════════════

def assemble_english_wiki(cards: list[HPCard], overview_en: str) -> str:
    """由 LLM 生成的英文段落拼装英文 Wiki 页面。"""
    ordered = []
    for card in cards:
        section = getattr(card, 'llm_wiki_en_section', '').strip()
        if section and section not in ordered:
            ordered.append(section)

    out = [
        '# AMPlify Human Practices — HP Compass',
        '',
        (overview_en.strip() if overview_en else ''),
        '',
        '---',
        '',
        '## Stakeholder → Feedback → Action Knowledge Graph',
        '',
        '![HP Compass Graph](hp_compass_graph.png)',
        '',
        '---',
        '',
    ]
    out.extend(ordered)
    return "\n".join(out)


# ═══════════════ 文件保存 ═══════════════

def save_wiki_files(
    cards: list[HPCard],
    analytics: dict | None,
    output_dir: Path,
    llm_meta: dict[str, str] | None = None,
) -> dict[str, Path]:
    """保存 Wiki 文案文件。

    llm_meta 提供 LLM 生成的英文内容（overview_en、defense_narrative_en）。
    规则模式下 llm_meta 为 None，英文 Wiki 与答辩叙事文件不写入。
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "wiki_cn.md": generate_wiki_text(cards, analytics),
    }
    if llm_meta is not None:
        files["wiki_en.md"] = assemble_english_wiki(cards, llm_meta.get("overview_en", ""))
        files["defense_narrative.md"] = llm_meta.get("defense_narrative_en", "")

    saved = {}
    for filename, content in files.items():
        path = output_dir / filename
        path.write_text(content, encoding="utf-8")
        saved[filename] = path

    return saved
