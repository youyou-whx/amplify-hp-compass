from __future__ import annotations

from .schema import HPCard


def recommend_next_step(card: HPCard) -> HPCard:
    """Generate next-step recommendations in Chinese (primary) and English.

    LLM 模式（processing_mode="llm" 且 next_step_cn 已由 LLM 生成）：
    直接采用 LLM 的自然语言建议，不走查表模板。
    """
    modules = set(card.affected_modules)
    materials: list[str] = []
    questions: list[str] = []
    materials_en: list[str] = []
    questions_en: list[str] = []

    # ── LLM 建议直通 ──
    llm_cn = getattr(card, "llm_next_step_cn", "") or ""
    if card.processing_mode == "llm" and llm_cn:
        card.next_step = llm_cn
        card.next_step_en = getattr(card, "llm_next_step_en", "") or llm_cn
        card.suggested_materials = list(getattr(card, "llm_materials_cn", []) or []) or \
            ["HP summary card", "project modification evidence"]
        card.suggested_materials_en = list(getattr(card, "llm_materials_en", []) or []) or \
            ["HP summary card", "Project modification evidence"]
        card.suggested_questions = list(getattr(card, "llm_questions_cn", []) or []) or [
            "该反馈是否已经被准确理解？",
            "目前的项目修改是否真正回应了 stakeholder 的关切？",
        ]
        card.suggested_questions_en = list(getattr(card, "llm_questions_en", []) or []) or [
            "Has this feedback been accurately understood?",
            "Do the current project changes genuinely address the stakeholder's concerns?",
        ]
        return card

    if card.loop_level < 2:
        action = "把该反馈转化为一个明确的项目修改，并补充对应证据。"
        action_en = "Translate this feedback into a concrete project modification, and collect supporting evidence."
    elif card.loop_level == 2:
        action = "补充可展示证据，例如模型输出、软件面板、实验数据、风险措辞或 Wiki 图表。"
        action_en = "Add demonstrable evidence — model outputs, software panels, experimental data, risk boundary statements, or Wiki figures."
    elif card.loop_level == 3 and not card.returned:
        action = f"将修改后的材料返回给 {card.stakeholder}，完成二轮反馈。"
        action_en = f"Return the revised materials to {card.stakeholder} for second-round feedback."
    else:
        action = "将该闭环整理为 Wiki/答辩中的完成案例。"
        action_en = "Document this closed loop as a completed case study in the Wiki and defense presentation."

    if "Model" in modules:
        materials.extend(["revised Field Score / model report", "candidate ranking change table"])
        materials_en.extend(["Revised Field Score / model report", "Candidate ranking change table"])
        questions.append("新的模型指标是否覆盖了 stakeholder 提出的关键判断？")
        questions_en.append("Do the new model metrics address the stakeholder's key concerns?")
        questions.append("候选排序变化是否容易解释，是否存在误导风险？")
        questions_en.append("Are candidate ranking changes easy to interpret? Is there any risk of misinterpretation?")
    if "Software" in modules:
        materials.extend(["software panel screenshot", "exported HP report card"])
        materials_en.extend(["Software panel screenshot", "Exported HP report card"])
        questions.append("软件报告中的标签和证据等级是否足够清楚？")
        questions_en.append("Are the labels and evidence levels in the software report sufficiently clear?")
    if "Safety" in modules or "Environment" in modules:
        materials.extend(["risk boundary wording draft", "environmental / safety panel"])
        materials_en.extend(["Risk boundary wording draft", "Environmental / safety panel"])
        questions.append("风险措辞是否避免了过度承诺？")
        questions_en.append("Does the risk language avoid overclaiming?")
        questions.append("哪些未来验证应被标注为优先？")
        questions_en.append("Which future validations should be flagged as priority?")
    if "Material" in modules:
        materials.extend(["Evidence Matrix", "wet-lab validation chain summary"])
        materials_en.extend(["Evidence Matrix", "Wet-lab validation chain summary"])
        questions.append("当前证据链是否足以支持候选筛选，而不是临床有效性声明？")
        questions_en.append("Is the current evidence chain sufficient to support candidate screening, rather than clinical efficacy claims?")
    if "Implementation" in modules:
        materials.extend(["application scenario card", "use-boundary checklist"])
        materials_en.extend(["Application scenario card", "Use-boundary checklist"])
        questions.append("该应用场景下最容易被忽略的使用限制是什么？")
        questions_en.append("What are the most easily overlooked use limitations in this application scenario?")
    if "Education" in modules:
        materials.extend(["education material v2", "public understanding feedback form"])
        materials_en.extend(["Education material v2", "Public understanding feedback form"])
        questions.append("受众是否能区分候选筛选、未来应用和现实治疗？")
        questions_en.append("Can the audience distinguish between candidate screening, future applications, and real-world treatment?")
    if "Social Media" in modules:
        materials.extend(["HP timeline card", "Stakeholder-Feedback-Action summary"])
        materials_en.extend(["HP timeline card", "Stakeholder-Feedback-Action summary"])
        questions.append("这段叙事是否清楚说明了谁改变了项目、改变了哪里？")
        questions_en.append("Does this narrative clearly explain who changed the project and what was changed?")

    card.next_step = action
    card.suggested_materials = dedupe(materials) or ["HP summary card", "project modification evidence"]
    card.suggested_questions = dedupe(questions) or [
        "该反馈是否已经被准确理解？",
        "目前的项目修改是否真正回应了 stakeholder 的关切？",
    ]

    # English fields (stored as extra attributes for wiki_generator)
    card.next_step_en = action_en
    card.suggested_materials_en = dedupe(materials_en) or ["HP summary card", "Project modification evidence"]
    card.suggested_questions_en = dedupe(questions_en) or [
        "Has this feedback been accurately understood?",
        "Do the current project changes genuinely address the stakeholder's concerns?",
    ]

    return card


def dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result
