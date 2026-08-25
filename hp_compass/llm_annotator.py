"""HP Compass — LLM 标注编排器

每条记录 4 次调用：

  调用 1（温度 0，×2 次运行）：Φ₁ 结构化提取 + Φ₂ 九模块四梯度 + 延伸判断
  调用 2（温度 0，×2 次运行）：Φ₅ 六个成熟度文本信号四梯度
  调用 3（温度 0.3，×2 次运行）：Φ₆ 回访建议 + 图谱节点文本
  调用 4（温度 0.3）：英文 Wiki 文案（单次运行）

稳定性：比较调用 1/2 两次运行的四梯度结果（9 模块 + 6 信号 = 15 个字段）
的一致率，采用第一次运行的结果。原始 JSON 均存档。

四梯度映射：无→0.0，弱→0.35，中→0.7，强→1.0
映射后的代表性数值作为模块隶属度（Φ₂）或成熟度文本信号值（Φ₅）。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .llm_client import chat_json
from .llm_prompts import (
    GRADE_VALUES,
    MATURITY_TEXT_SIGNALS,
    MODULES,
    build_call1_messages,
    build_call2_messages,
    build_call3_messages,
    build_call4_messages,
)

# 温度设置：调用 1/2 用 0（近似确定），调用 3/4 用 0.3（文案自然一些）
TEMPERATURES = {"call1": 0.0, "call2": 0.0, "call3": 0.3, "call4": 0.3}


@dataclass
class LLMAnnotation:
    """一条记录经 LLM 标注后的完整结果（采用第一次运行）。"""

    # Φ₁ 提取字段
    date: str | None = None
    stakeholder: str = ""
    stakeholder_type: str | None = None
    initial_question: str = ""
    feedback: str = ""
    project_action: str = ""
    evidence: list[str] = field(default_factory=list)
    returned: bool = False
    has_action: bool = False    # 语义判断：是否已做出实际项目修改（计划不算）
    has_evidence: bool = False  # 语义判断：是否有实质证据支撑（提及打算做的不算）

    # Φ₂ 九模块四梯度 → 代表性数值（未归一化，直接作为 h_c）
    module_grades: dict[str, str] = field(default_factory=dict)
    module_values: dict[str, float] = field(default_factory=dict)

    # Φ₅ 六个成熟度文本信号四梯度 → 代表性数值
    maturity_grades: dict[str, str] = field(default_factory=dict)
    maturity_values: dict[str, float] = field(default_factory=dict)

    # Φ₆ 建议 + 图谱文本
    next_step_cn: str = ""
    next_step_en: str = ""
    materials_cn: list[str] = field(default_factory=list)
    materials_en: list[str] = field(default_factory=list)
    questions_cn: list[str] = field(default_factory=list)
    questions_en: list[str] = field(default_factory=list)
    feedback_summary: str = ""
    action_summary: str = ""

    # 英文 Wiki 文案（单次运行，非稳定性对象）
    wiki_en_section: str = ""

    # 延伸判断：这条记录是否是某条已有记录的回访
    is_extension_of: str | None = None   # 已有记录的编号，独立记录为 None

    # 审计信息
    stability_agreement: float | None = None   # 四梯度一致率 [0,1]
    stability_checked_fields: int = 0
    raw_dir: str = ""


def _parse_grades(raw: dict[str, Any], keys: list[str]) -> dict[str, str]:
    """从 LLM 原始 JSON 中提取四梯度，非法值回退为"无"。"""
    grades: dict[str, str] = {}
    for key in keys:
        value = str(raw.get(key, "无")).strip()
        grades[key] = value if value in GRADE_VALUES else "无"
    return grades


def _to_values(grades: dict[str, str]) -> dict[str, float]:
    return {key: GRADE_VALUES[grade] for key, grade in grades.items()}


def _extract_str(raw: dict[str, Any], key: str, max_len: int | None = None) -> str:
    value = str(raw.get(key, "") or "").strip()
    if max_len and len(value) > max_len:
        value = value[: max_len - 1].rstrip() + "…"
    return value


def _extract_list(raw: dict[str, Any], key: str, max_items: int = 8) -> list[str]:
    value = raw.get(key, [])
    if not isinstance(value, list):
        return []
    items = [str(v).strip() for v in value if str(v).strip()]
    return items[:max_items]


def _extract_bool(raw: dict[str, Any], key: str) -> bool:
    value = raw.get(key, False)
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("true", "yes", "是", "1", "已", "已经")


def _extract_date(raw: dict[str, Any]) -> str | None:
    value = str(raw.get("date") or "").strip()
    if not value or value.lower() == "null":
        return None
    match = re.search(r"(20\d{2})-(\d{1,2})-(\d{1,2})", value)
    if match:
        year, month, day = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"
    return None


def _stability_agreement(
    module_grades1: dict[str, str],
    module_grades2: dict[str, str],
    maturity_grades1: dict[str, str],
    maturity_grades2: dict[str, str],
) -> tuple[float, int]:
    """比较两次运行的四梯度结果（9 模块 + 6 信号 = 15 个字段）。

    返回 (一致率, 参与比较的字段数)。
    """
    total = 0
    agreed = 0

    for key in MODULES:
        total += 1
        if module_grades1.get(key, "无") == module_grades2.get(key, "无"):
            agreed += 1

    for key in MATURITY_TEXT_SIGNALS:
        total += 1
        if maturity_grades1.get(key, "无") == maturity_grades2.get(key, "无"):
            agreed += 1

    if total == 0:
        return 0.0, 0
    return agreed / total, total


def annotate_record(
    text: str,
    api_key: str,
    raw_dir: str | Path,
    hp_slug: str,
    existing_records: list[dict[str, str]] | None = None,
) -> LLMAnnotation:
    """对一条访谈记录执行 4 次调用，返回采用第一次运行结果的标注。

    原始 JSON 存档到 raw_dir/{hp_slug}/call{n}_run{m}.json，
    稳定性统计存档到 raw_dir/{hp_slug}/stability.json。
    """
    raw_path = Path(raw_dir) / hp_slug
    raw_path.mkdir(parents=True, exist_ok=True)

    # ── 调用 1 × 2 ──
    call1_run1 = chat_json(
        build_call1_messages(text, existing_records), api_key, TEMPERATURES["call1"]
    )
    call1_run2 = chat_json(
        build_call1_messages(text, existing_records), api_key, TEMPERATURES["call1"]
    )

    card_info = {
        "stakeholder": _extract_str(call1_run1, "stakeholder", 120),
        "stakeholder_type": _extract_str(call1_run1, "stakeholder_type", 60),
        "initial_question": _extract_str(call1_run1, "initial_question", 500),
        "feedback": _extract_str(call1_run1, "feedback", 900),
        "project_action": _extract_str(call1_run1, "project_action", 900),
        "evidence": _extract_list(call1_run1, "evidence"),
    }

    # ── 调用 2 × 2 ──
    call2_run1 = chat_json(build_call2_messages(card_info), api_key, TEMPERATURES["call2"])
    call2_run2 = chat_json(build_call2_messages(card_info), api_key, TEMPERATURES["call2"])

    # ── 先用 call1 第一次结果推闭环状态，供调用 3 使用 ──
    evidence = card_info["evidence"]
    returned = _extract_bool(call1_run1, "returned")
    has_action = _extract_bool(call1_run1, "has_action")
    has_evidence = _extract_bool(call1_run1, "has_evidence")
    module_grades = _parse_grades(call1_run1.get("module_grades", {}) or {}, MODULES)
    module_values = _to_values(module_grades)
    affected = [m for m in MODULES if module_values.get(m, 0.0) >= 0.35]
    if not affected:
        affected = [m for m, v in sorted(module_values.items(), key=lambda kv: kv[1], reverse=True) if v > 0][:3]

    # 闭环层级：LLM 做语义判断（是否实际行动/实质证据），数学做状态组合
    if not card_info["feedback"]:
        loop_level = 0
    else:
        loop_level = 1 + int(has_action) + int(has_evidence) + int(returned)
    loop_level = min(loop_level, 4)
    loop_status = ["L0_Recorded", "L1_Interpreted", "L2_Actioned", "L3_Evidenced", "L4_Returned"][loop_level]

    # ── 调用 3 × 2 ──
    call3_info = dict(card_info)
    call3_info["affected_modules"] = affected
    call3_info["loop_status"] = loop_status
    call3_run1 = chat_json(build_call3_messages(call3_info), api_key, TEMPERATURES["call3"])
    call3_run2 = chat_json(build_call3_messages(call3_info), api_key, TEMPERATURES["call3"])

    # ── 调用 4：英文 Wiki 文案（单次运行）──
    call4_info = dict(call3_info)
    call4_info["date"] = _extract_date(call1_run1)
    call4_run1 = chat_json(
        build_call4_messages(call4_info), api_key, TEMPERATURES["call4"]
    )

    # ── 稳定性统计（比较 9 模块 + 6 信号）──
    module_grades_run2 = _parse_grades(call1_run2.get("module_grades", {}) or {}, MODULES)
    maturity_grades_run2 = _parse_grades(call2_run2, MATURITY_TEXT_SIGNALS)
    maturity_grades = _parse_grades(call2_run1, MATURITY_TEXT_SIGNALS)
    agreement, checked = _stability_agreement(
        module_grades, module_grades_run2, maturity_grades, maturity_grades_run2
    )

    # ── 存档原始 JSON ──
    archive = {
        "call1_run1": call1_run1, "call1_run2": call1_run2,
        "call2_run1": call2_run1, "call2_run2": call2_run2,
        "call3_run1": call3_run1, "call3_run2": call3_run2,
        "call4_run1": call4_run1,
    }
    for name, payload in archive.items():
        (raw_path / f"{name}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    (raw_path / "stability.json").write_text(
        json.dumps(
            {
                "agreement": round(agreement, 4),
                "checked_fields": checked,
                "model": "deepseek-chat",
                "temperatures": TEMPERATURES,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # ── 组装结果（全部采用第一次运行）──
    raw_ext = call1_run1.get("is_extension_of")
    is_extension_of = str(raw_ext).strip() if raw_ext and str(raw_ext).strip() != "null" else None

    annotation = LLMAnnotation(
        date=_extract_date(call1_run1),
        stakeholder=card_info["stakeholder"],
        stakeholder_type=card_info["stakeholder_type"] or None,
        initial_question=card_info["initial_question"],
        feedback=card_info["feedback"],
        project_action=card_info["project_action"],
        evidence=evidence,
        returned=returned,
        has_action=has_action,
        has_evidence=has_evidence,
        is_extension_of=is_extension_of,
        module_grades=module_grades,
        module_values=module_values,
        maturity_grades=maturity_grades,
        maturity_values=_to_values(maturity_grades),
        next_step_cn=_extract_str(call3_run1, "next_step_cn", 300),
        next_step_en=_extract_str(call3_run1, "next_step_en", 400),
        materials_cn=_extract_list(call3_run1, "materials_cn"),
        materials_en=_extract_list(call3_run1, "materials_en"),
        questions_cn=_extract_list(call3_run1, "questions_cn"),
        questions_en=_extract_list(call3_run1, "questions_en"),
        feedback_summary=_extract_str(call3_run1, "feedback_summary", 120),
        action_summary=_extract_str(call3_run1, "action_summary", 120),
        wiki_en_section=_extract_str(call4_run1, "wiki_section_en", 4000),
        stability_agreement=round(agreement, 4),
        stability_checked_fields=checked,
        raw_dir=str(raw_path),
    )
    return annotation
