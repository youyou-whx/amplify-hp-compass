from __future__ import annotations

import re
from pathlib import Path

from .config import ACTION_KEYWORDS, EVIDENCE_BLOCKED, EVIDENCE_KEYWORDS
from .schema import HPCard


DATE_RE = re.compile(r"(20\d{2})[年\-/\.]?(\d{1,2})[月\-/\.]?(\d{1,2})")


def extract_card(path: Path, text: str) -> HPCard:
    hp_id = build_hp_id(path, text)
    date = extract_date(path.name + "\n" + text)
    stakeholder = extract_stakeholder(path, text)
    stakeholder_type = infer_stakeholder_type(stakeholder, text)
    initial_question = extract_section(
        text,
        ["为什么：", "为什么:", "为什么", "设计问题：", "设计需要被验证的问题："],
        ["我们学到了什么", "专家反馈", "我们如何修改项目", "了解更多", "本轮 HP", "图 1"],
        520,
    )
    feedback = extract_section(
        text,
        ["我们学到了什么：", "我们学到了什么:", "我们学到了什么", "专家反馈", "学到了什么：", "反馈"],
        ["我们如何修改项目", "了解更多", "下一步", "本轮 HP", "图 1", "这次调研为什么"],
        900,
    )
    project_action = extract_project_action(text)
    evidence = extract_evidence(text)
    returned = detect_returned(text)

    return HPCard(
        hp_id=hp_id,
        source_file=str(path),
        date=date,
        stakeholder=stakeholder,
        stakeholder_type=stakeholder_type,
        initial_question=initial_question,
        feedback=feedback,
        project_action=project_action,
        evidence=evidence,
        returned=returned,
    )


def build_hp_id(path: Path, text: str) -> str:
    date = extract_date(path.name + "\n" + text)
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "_", path.stem).strip("_")
    # \u53bb\u9664\u6587\u4ef6\u540d\u4e2d\u5df2\u6709\u7684\u65e5\u671f\u524d\u7f00\uff08\u5982 20260315_xxx \u2192 xxx\uff09
    slug = re.sub(r"^20\d{6}_", "", slug)
    if date:
        return f"HP_{date.replace('-', '')}_{slug[:32]}"
    return f"HP_{slug[:48]}"


def extract_date(text: str) -> str | None:
    match = DATE_RE.search(text)
    if not match:
        return None
    year, month, day = match.groups()
    return f"{year}-{int(month):02d}-{int(day):02d}"


def extract_stakeholder(path: Path, text: str) -> str:
    filename = path.stem
    known_stakeholders = [
        ("赵天意", "赵天意老师"),
        ("钱勋", "西北农林科技大学资环学院钱勋教授"),
        ("罗自卫", "西北农林科技大学罗自卫老师"),
        ("聂桓", "哈尔滨工业大学生命科学与医学学部聂桓老师"),
        ("哈工大", "哈尔滨工业大学生命科学与医学学部聂桓老师"),
        ("东北地区交流会", "iGEM 东北地区交流会参会队伍与经验分享者"),
        ("刘军教授", "西北农林科技大学家畜生物学重点实验室刘军教授"),
        ("家畜生物学重点实验室", "西北农林科技大学家畜生物学重点实验室刘军教授"),
        ("西安动物医院", "西北农林科技大学西安动物医院的临床医生与院长"),
        ("猫咪驿站", "西安市浮生闲猫咪驿站工作人员"),
        ("张伟", "杨陵揉谷镇除张村羊场人员张伟"),
        ("杜欣愿", "武功县诚威奶山羊羊场负责人杜欣愿"),
        ("散养羊村民", "基层执业兽医与散养户"),
    ]
    for needle, label in known_stakeholders:
        if needle in filename:
            return label
    haystack = text[:1800]
    for needle, label in known_stakeholders:
        if needle in haystack:
            return label

    candidates = [
        r"我们联系了谁[:：]\s*([^\n。；;]+)",
        r"采访了([^\n。；;]+)",
        r"调研[:：]?([^\n。；;]+)",
        r"与([^\n。；;]{2,40}?)(?:交流|访谈|讨论)",
    ]
    for pattern in candidates:
        match = re.search(pattern, text)
        if match:
            return clean_short(match.group(1), 80)

    return clean_short(filename, 80)


def infer_stakeholder_type(stakeholder: str, text: str) -> str | None:
    stakeholder_rules = [
        ("环境微生物 / ARG 专家", ["钱勋", "资环"]),
        ("AI / 生物大数据专家", ["赵天意"]),
        ("湿实验 / 合成生物学专家", ["罗自卫"]),
        ("iGEM / Wiki 交流 stakeholder", ["聂桓", "交流会", "iGEM"]),
        ("动物健康 / 家畜专家", ["刘军", "家畜生物学"]),
        ("兽医临床 stakeholder", ["动物医院", "医生", "院长", "检验中心"]),
        ("养殖端 stakeholder", ["羊场", "养殖", "散养户", "村民", "张伟", "杜欣愿"]),
        ("公众教育 stakeholder", ["猫咪驿站", "公众"]),
        ("iGEM / Wiki 交流 stakeholder", ["交流会", "iGEM"]),
    ]
    for label, keywords in stakeholder_rules:
        if any(keyword in stakeholder for keyword in keywords):
            return label

    sample = stakeholder + "\n" + text[:900]
    rules = [
        ("环境微生物 / ARG 专家", ["钱勋", "环境", "ARG", "资环"]),
        ("AI / 生物大数据专家", ["赵天意", "ESM", "Oracle", "模型", "生物大数据"]),
        ("湿实验 / 合成生物学专家", ["罗自卫", "湿实验", "MIC", "工程菌"]),
        ("动物健康 / 家畜专家", ["刘军", "家畜", "乳腺炎"]),
        ("兽医临床 stakeholder", ["动物医院", "医生", "院长", "检验中心"]),
        ("养殖端 stakeholder", ["羊场", "养殖", "负责人", "村民"]),
        ("公众教育 stakeholder", ["猫咪驿站", "公众", "工作人员"]),
        ("iGEM / Wiki 交流 stakeholder", ["交流会", "Wiki", "答辩", "海报"]),
    ]
    for label, keywords in rules:
        if any(keyword in sample for keyword in keywords):
            return label
    return None


def extract_after_markers(text: str, markers: list[str], max_chars: int) -> str:
    for marker in markers:
        index = text.find(marker)
        if index >= 0:
            start = index + len(marker)
            chunk = text[start : start + max_chars]
            return clean_block(chunk, max_chars)
    return clean_block(text[:max_chars], max_chars)


def extract_section(text: str, markers: list[str], stops: list[str], max_chars: int) -> str:
    starts = [(text.find(marker), marker) for marker in markers if text.find(marker) >= 0]
    if not starts:
        return clean_block(text[:max_chars], max_chars)

    index, marker = min(starts, key=lambda item: item[0])
    start = index + len(marker)
    end = len(text)
    for stop in stops:
        stop_index = text.find(stop, start)
        if stop_index >= 0:
            end = min(end, stop_index)
    return clean_block(text[start:end], max_chars)


def extract_project_action(text: str) -> str:
    marker_text = extract_section(
        text,
        ["我们如何修改项目：", "我们如何修改项目", "AMPlify 的修改", "形成 v2", "Learn", "如何改变"],
        ["了解更多", "本轮 HP", "这次调研为什么", "为什么这一站", "图 1", "仍需谨慎"],
        900,
    )
    if any(keyword in marker_text for keyword in ACTION_KEYWORDS):
        return marker_text

    sentences = split_sentences(text)
    action_sentences = [
        sentence for sentence in sentences if any(keyword in sentence for keyword in ACTION_KEYWORDS)
    ]
    return clean_block(" ".join(action_sentences[:4]), 900)


def extract_evidence(text: str) -> list[str]:
    """提取证据关键词，自动过滤计划性/未来式表述。

    三层策略：
    1. 按权重从高到低匹配 EVIDENCE_KEYWORDS
    2. 匹配命名的项目产物（artifact）
    3. 兜底：访谈类文档至少保留"访谈记录"作为证据
    """
    evidence: list[str] = []

    # 按权重从高到低提取证据关键词
    for keyword in sorted(EVIDENCE_KEYWORDS, key=lambda k: EVIDENCE_KEYWORDS[k], reverse=True):
        if keyword in text and keyword not in evidence:
            # 排除弱信号词（计划、未来等）
            if keyword not in EVIDENCE_BLOCKED:
                evidence.append(keyword)

    # 提取命名的项目产物（artifact）
    named_artifacts = [
        "PDES",
        "Environmental Degradation Panel",
        "Field Score",
        "Evidence Matrix",
        "TAM-Flow",
        "Risk Boundary Panel",
        "Oracle",
        "RAFT",
    ]
    for artifact in named_artifacts:
        if artifact in text and artifact not in evidence:
            evidence.append(artifact)

    # 兜底：如果文本包含访谈/调研内容，但还没提取到"访谈记录"，则补上
    has_interview = any(term in text for term in ["访谈", "采访", "调研", "交流", "讨论"])
    has_strong_evidence = any(
        keyword in text
        for keyword in ["MIC", "溶血", "CCK", "TEM", "MD", "质谱", "PDES", "TAM-Flow"]
    )

    if has_interview and "访谈记录" not in evidence:
        # 如果有强证据，访谈记录作为辅助证据；否则作为主要证据
        evidence.append("访谈记录")

    # 清洗：合并重复含义的证据项
    return _dedupe_evidence(evidence)


def _dedupe_evidence(items: list[str]) -> list[str]:
    """合并语义重复的证据项"""
    # CCK 和 CCK-8 合并为 CCK-8（更精确）
    result = []
    for item in items:
        if item == "CCK" and "CCK-8" in items:
            continue  # CCK-8 更精确，跳过 CCK
        if item == "MD" and "分子动力学" in items:
            continue  # 分子动力学更完整
        result.append(item)
    return result


def detect_returned(text: str) -> bool:
    explicit_positive = [
        "已返回",
        "已经返回",
        "已回访",
        "已经回访",
        "获得二轮反馈",
        "完成二轮反馈",
        "完成了二轮反馈",
        "二轮反馈确认",
        "returned and confirmed",
        "second feedback confirmed",
    ]
    planned_patterns = [
        "下一步应",
        "下一步",
        "计划",
        "仍需",
        "需要",
        "将",
        "应把",
        "后续",
        "Second Feedback",
        "反馈计划",
    ]
    for line in text.splitlines():
        if any(marker in line for marker in planned_patterns):
            continue
        if any(marker.lower() in line.lower() for marker in explicit_positive):
            return True

    return_lines = [line.strip() for line in text.splitlines() if "返回" in line or "回访" in line]
    for line in return_lines:
        if any(marker in line for marker in planned_patterns):
            continue
        if ("已" in line or "已经" in line or "获得" in line) and "二轮" in line:
            return True
    return False


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[。！？!?])\s*", text)
    return [part.strip() for part in parts if part.strip()]


def clean_short(text: str, max_chars: int) -> str:
    return clean_block(text, max_chars).replace("\n", " ")


def clean_block(text: str, max_chars: int) -> str:
    text = text.strip(" :：\n\t-")
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"
