from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from .classifier import classify_card
from .docx_reader import load_inputs
from .extractor import build_hp_id, extract_card
from .graph_builder import build_analytics_report, build_graph
from .llm_annotator import annotate_record
from .llm_client import chat_json
from .llm_prompts import build_call5_messages
from .maturity import score_maturity
from .recommender import recommend_next_step
from .report import write_dashboard, write_markdown_recommendations
from .schema import HPCard
from .scoring import parse_deadline, score_priority
from .sensitivity import run_sensitivity
from .status import assign_loop_status
from .wiki_generator import save_wiki_files


def run_pipeline(
    input_path: str | Path,
    output_dir: str | Path,
    deadline: str | None = None,
    mode: str = "rule",
    api_key: str | None = None,
    endpoint: str = "https://api.deepseek.com/chat/completions",
    model: str = "deepseek-chat",
    stability: bool = False,
) -> list[HPCard]:
    """处理管道。mode="rule" 走关键词规则层；mode="llm" 走大模型解析层。

    LLM 模式：每条记录 4 次调用，原始 JSON 存档到 output_dir/llm_raw/。
    新文件若被判定为某条已处理记录的回访，合并进该记录，
    层级/优先级/成熟度/建议整合后重新分析。
    """
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    cards: list[HPCard] = []
    for path, text in load_inputs(input_path):
        if mode == "llm" and api_key:
            card = _process_card_llm(path, text, output, api_key, cards,
                                     endpoint=endpoint, model=model, stability=stability)
        else:
            card = extract_card(path, text)
            card.processing_mode = "rule"
            card = classify_card(card)
            card = assign_loop_status(card)
            card = score_priority(card, deadline=parse_deadline(deadline))
            card = score_maturity(card)
            card = recommend_next_step(card)

        target = _find_extension_target(cards, card) if _is_extension_card(card) else None
        if target is not None:
            _merge_extension(target, card)
        else:
            cards.append(card)

    llm_meta = None
    if mode == "llm" and api_key and cards:
        llm_meta = _generate_llm_meta(cards, api_key, output, endpoint=endpoint, model=model)

    rebuild_outputs(cards, output, llm_meta=llm_meta)
    return cards


def run_llm_incremental(
    new_docx_files: list[Path],
    output_dir: str | Path,
    api_key: str,
    existing_cards: list[HPCard] | None = None,
    endpoint: str = "https://api.deepseek.com/chat/completions",
    model: str = "deepseek-chat",
    stability: bool = False,
) -> list[HPCard]:
    """LLM 增量处理：只对新上传的 docx 文件跑 LLM，旧卡片保持不变。

    新卡片按文件名去重（同 source_file 的旧卡被替换）；
    回访记录合并进原卡，不新增卡片。
    """
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    cards: list[HPCard] = list(existing_cards or [])

    for path in new_docx_files:
        loaded = load_inputs(path)
        if not loaded:
            continue
        text = loaded[0][1]
        if not text:
            continue
        card = _process_card_llm(path, text, output, api_key, cards,
                                 endpoint=endpoint, model=model, stability=stability)

        target = _find_extension_target(cards, card) if _is_extension_card(card) else None
        if target is not None:
            _merge_extension(target, card)
        else:
            # 同文件名旧卡替换
            name = Path(path).name
            cards = [c for c in cards if Path(c.source_file).name != name]
            cards.append(card)

    cards.sort(key=lambda c: c.date or "9999-99-99")

    llm_meta = None
    if cards and any(c.processing_mode == "llm" for c in cards):
        llm_meta = _generate_llm_meta(cards, api_key, output, endpoint=endpoint, model=model)

    rebuild_outputs(cards, output, llm_meta=llm_meta)
    return cards


def _process_card_llm(
    path: Path,
    text: str,
    output: Path,
    api_key: str,
    existing_cards: list[HPCard] | None = None,
    endpoint: str = "https://api.deepseek.com/chat/completions",
    model: str = "deepseek-chat",
    stability: bool = False,
) -> HPCard:
    """LLM 模式处理单条记录：4 次调用 → 卡片 → 数学模块。"""
    slug = Path(path).stem[:48].replace(" ", "_")
    records_info = _build_records_info(existing_cards or [])
    annotation = annotate_record(text, api_key, output / "llm_raw", slug, records_info,
                                 endpoint=endpoint, model=model, stability=stability)

    card = HPCard(
        hp_id=build_hp_id(path, text),
        source_file=str(path),
        date=annotation.date,
        stakeholder=annotation.stakeholder,
        stakeholder_type=annotation.stakeholder_type,
        initial_question=annotation.initial_question,
        feedback=annotation.feedback,
        project_action=annotation.project_action,
        evidence=annotation.evidence,
        returned=annotation.returned,
        processing_mode="llm",
        llm_has_action=annotation.has_action,
        llm_has_evidence=annotation.has_evidence,
        llm_module_values=annotation.module_values,
        llm_maturity_values=annotation.maturity_values,
        llm_feedback_summary=annotation.feedback_summary,
        llm_action_summary=annotation.action_summary,
        llm_stability=annotation.stability_agreement,
        llm_raw_dir=annotation.raw_dir,
        llm_next_step_cn=annotation.next_step_cn,
        llm_next_step_en=annotation.next_step_en,
        llm_materials_cn=annotation.materials_cn,
        llm_materials_en=annotation.materials_en,
        llm_questions_cn=annotation.questions_cn,
        llm_questions_en=annotation.questions_en,
        llm_wiki_en_section=annotation.wiki_en_section,
    )

    if annotation.is_extension_of:
        card.extension_ref = annotation.is_extension_of

    # 数学模块执行（Φ₂ 的模块隶属度、Φ₅ 的文本信号由 LLM 四梯度数值提供）
    card = classify_card(card)
    card = assign_loop_status(card)
    card = score_priority(card)
    card = score_maturity(card)
    card = recommend_next_step(card)
    return card


def _generate_llm_meta(
    cards: list[HPCard],
    api_key: str,
    output: Path,
    endpoint: str = "https://api.deepseek.com/chat/completions",
    model: str = "deepseek-chat",
) -> dict[str, str]:
    """生成英文总述与答辩叙事（一次 LLM 调用），原始 JSON 存档。"""
    ranked = sorted(cards, key=lambda c: c.priority_score, reverse=True)
    summary_lines = []
    for i, card in enumerate(ranked, start=1):
        modules = "、".join(card.affected_modules) if card.affected_modules else "未分类"
        visits = ""
        if card.visits:
            visits = "；含二轮回访（" + "、".join(v.get("date", "") for v in card.visits) + "）"
        summary_lines.append(
            f"{i}. {card.stakeholder}（{card.stakeholder_type or '未标注'}，{card.date or '日期未知'}）"
            f"{visits}\n   反馈：{(card.feedback or '')[:400]}"
            f"\n   项目修改：{(card.project_action or '')[:400]}"
            f"\n   影响模块：{modules}\n"
        )
    cards_summary = "\n".join(summary_lines)

    graph = build_graph(cards)
    graph_facts = (
        f"知识图谱共 {len(graph.nodes)} 个节点、{len(graph.edges)} 条边；"
        f"节点类型：{', '.join(sorted({n['kind'] for n in graph.nodes}))}。"
    )
    module_impact: dict[str, int] = {}
    for card in cards:
        for module in card.affected_modules:
            module_impact[module] = module_impact.get(module, 0) + 1
    top_modules = sorted(module_impact, key=module_impact.get, reverse=True)[:3]
    graph_facts += (
        f"被 HP 反馈影响最多的模块："
        + "、".join(f"{m}（{module_impact[m]} 次）" for m in top_modules)
        + "。"
    )

    methodology_facts = (
        "HP Compass 是以模糊综合评价（FCE）为核心、层次分析法（AHP）确定权重的决策支持模型："
        "每条访谈提取结构化字段并判定闭环状态（L0 记录/L1 提炼/L2 行动/L3 证据/L4 回访）；"
        "九大项目模块经模糊隶属度分类；优先级由二级 FCE 计算"
        "（内部紧迫性：闭环缺口、跨模块影响、模块关键性；外部约束：时间紧迫、证据不足、利益相关者价值），"
        "AHP 判断矩阵经一致性检验（CR<0.10），M(·,+) 算子合成，重心法去模糊化；"
        "六维成熟度评估（设计反思、场景探索、多元视角、影响预判、HP响应、局限性坦诚）"
        "采用模糊隶属度加权合成与级别特征值判定；"
        "知识图谱用度中心性、中介中心性、PageRank 分析；"
        "敏感性分析：±20% 参数扰动下优先级排名 Spearman ρ≥0.999，最大得分偏差≤0.042，成熟度等级跳变率 0%。"
        "文本解析层由大模型完成，决策计算层为确定性数学模型。"
    )

    result = chat_json(
        build_call5_messages(cards_summary, graph_facts, methodology_facts),
        api_key,
        0.3,
        endpoint=endpoint,
        model=model,
    )

    meta_path = output / "llm_raw" / "overview_defense.json"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return {
        "overview_en": str(result.get("overview_en", "") or "").strip(),
        "defense_narrative_en": str(result.get("defense_narrative_en", "") or "").strip(),
    }


# ═══════════════════════════════════════════════════════════════
#  回访延伸识别与合并
# ═══════════════════════════════════════════════════════════════

_EXTENSION_HINT_KEYWORDS = ["回访", "二轮", "返访", "复核", "再次确认"]


def _is_extension_card(card: HPCard) -> bool:
    """判断卡片是否可能是延伸记录（LLM 判定或文件名提示）。"""
    if getattr(card, "extension_ref", ""):
        return True
    name = Path(card.source_file).stem
    return any(kw in name for kw in _EXTENSION_HINT_KEYWORDS)


def _build_records_info(cards: list[HPCard]) -> list[dict[str, str]]:
    return [
        {
            "id": str(i + 1),
            "date": card.date or "日期未知",
            "stakeholder": card.stakeholder,
            "file": Path(card.source_file).name,
        }
        for i, card in enumerate(cards)
    ]


def _find_extension_target(cards: list[HPCard], card: HPCard) -> HPCard | None:
    """在已处理卡片中寻找延伸目标。

    优先用 LLM 给出的编号/标识，其次按文件名相似度 + 利益相关者匹配。
    """
    if not cards:
        return None

    ref = getattr(card, "extension_ref", "")
    if ref:
        # LLM 返回编号（对应 records_info 的 id）
        if ref.isdigit():
            index = int(ref) - 1
            if 0 <= index < len(cards):
                target = cards[index]
                if _stakeholder_match(target.stakeholder, card.stakeholder):
                    return target
                return None  # 利益相关者不匹配 → 误判，按独立记录处理
        # LLM 可能直接返回 hp_id 或利益相关者名
        for target in cards:
            if ref == target.hp_id or ref == target.stakeholder:
                if _stakeholder_match(target.stakeholder, card.stakeholder):
                    return target
            elif ref in target.hp_id or ref in target.stakeholder:
                if _stakeholder_match(target.stakeholder, card.stakeholder):
                    return target

    # 规则匹配：文件名相似度 + 利益相关者匹配
    name = Path(card.source_file).stem
    best, best_score = None, 0.0
    for target in cards:
        tname = Path(target.source_file).stem
        score = _name_similarity(tname, name)
        if target.stakeholder and target.stakeholder == card.stakeholder:
            score += 0.5
        if score > best_score:
            best, best_score = target, score
    if best is not None and best_score >= 0.5:
        return best
    return None


def _name_similarity(a: str, b: str) -> float:
    """文件名相似度：去掉日期前缀与回访标记后的字符级 Jaccard。"""
    a2 = re.sub(r"^20\d{6}_", "", a)
    b2 = re.sub(r"^20\d{6}_", "", b)
    for kw in _EXTENSION_HINT_KEYWORDS:
        a2 = a2.replace(kw, "")
        b2 = b2.replace(kw, "")
    set_a, set_b = set(a2), set(b2)
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def _stakeholder_match(a: str, b: str) -> bool:
    """判断两个利益相关者是否为同一对象（回访合并的安全闸门）。

    完全相同、互为包含、或字符重合率 ≥ 0.6 视为同一对象。
    不同机构/不同身份即使主题相近也不会误合并。
    """
    if not a or not b:
        return False
    if a == b:
        return True
    if a in b or b in a:
        return True
    set_a, set_b = set(a), set(b)
    if not set_a or not set_b:
        return False
    return len(set_a & set_b) / len(set_a | set_b) >= 0.6


def _merge_extension(target: HPCard, followup: HPCard) -> None:
    """把回访记录合并进原始记录（原地修改 target）。

    - 文本内容合并（回访部分在后），证据取并集，returned 置真
    - visits 追加一次访问（时间线/Wiki 分开展示两次访问）
    - LLM 覆盖值取两轮并集（max），建议合并去重
    - 闭环状态、优先级、六维成熟度、下一步建议整合后重新计算
    """
    sep = "\n\n【二轮回访】\n"
    target.feedback = (target.feedback + sep + followup.feedback).strip()
    target.project_action = (target.project_action + sep + followup.project_action).strip()
    target.evidence = _dedupe(target.evidence + followup.evidence)
    target.returned = True

    target.visits = list(target.visits) + [{
        "date": followup.date or "",
        "source_file": Path(followup.source_file).name,
        "summary": (
            followup.llm_feedback_summary
            or _shorten(followup.feedback, 120)
        ),
    }]

    if followup.processing_mode == "llm":
        target.processing_mode = "llm"
        for key, value in followup.llm_module_values.items():
            target.llm_module_values[key] = max(target.llm_module_values.get(key, 0.0), value)
        for key, value in followup.llm_maturity_values.items():
            target.llm_maturity_values[key] = max(target.llm_maturity_values.get(key, 0.0), value)
        if followup.llm_next_step_cn:
            target.llm_next_step_cn = _join_texts(target.llm_next_step_cn, followup.llm_next_step_cn)
        if followup.llm_next_step_en:
            target.llm_next_step_en = _join_texts(target.llm_next_step_en, followup.llm_next_step_en)
        target.llm_materials_cn = _dedupe(target.llm_materials_cn + followup.llm_materials_cn)
        target.llm_materials_en = _dedupe(target.llm_materials_en + followup.llm_materials_en)
        target.llm_questions_cn = _dedupe(target.llm_questions_cn + followup.llm_questions_cn)
        target.llm_questions_en = _dedupe(target.llm_questions_en + followup.llm_questions_en)

    # 整合后重新计算全部数学模块
    classify_card(target)
    assign_loop_status(target)
    score_priority(target)
    score_maturity(target)
    recommend_next_step(target)


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


def _join_texts(a: str, b: str) -> str:
    if not a:
        return b
    if not b or b in a:
        return a
    return a + "\n" + b


def _shorten(text: str, limit: int) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def rebuild_outputs(
    cards: list[HPCard],
    output_dir: str | Path,
    llm_meta: dict[str, str] | None = None,
) -> None:
    """由卡片列表重建图谱、分析、敏感性、所有输出文件与 Wiki。

    rule 与 llm 两种模式的卡片可混存，重建逻辑一致。
    llm_meta 提供 LLM 生成的英文总述与答辩叙事；为 None 时
    英文 Wiki 与答辩叙事文件不写入。
    """
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    # 2. 构建知识图谱
    graph = build_graph(cards)

    # 3. NetworkX 图分析
    analytics = build_analytics_report(cards, graph)

    # 3.5 敏感性分析
    sensitivity_result = run_sensitivity([c.to_dict() for c in cards])
    (output / "sensitivity.json").write_text(
        json.dumps(sensitivity_result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 4. 写入输出文件
    (output / "hp_cards.json").write_text(
        json.dumps([card.to_dict() for card in cards], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output / "graph.json").write_text(
        json.dumps(graph.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output / "analytics.json").write_text(
        json.dumps(analytics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    write_markdown_recommendations(cards, output / "recommendations.md")
    write_dashboard(cards, graph, output / "dashboard.html")

    # 5. 生成 Wiki 文案
    wiki_files = save_wiki_files(cards, analytics, output, llm_meta=llm_meta)
    for name, path in wiki_files.items():
        print(f"Wiki: {path}")

    # 6. 确保输出目录包含 Logo（Dashboard 与侧边栏引用）
    _ensure_output_logos(output)


def _ensure_output_logos(output: Path) -> None:
    """输出目录缺少 Logo 时，从项目根或默认输出目录补齐。"""
    if not (output / "amplify_logo.png").exists():
        for src in (Path("AMPLIFY.png"), Path("hp_compass_output") / "amplify_logo.png"):
            if src.exists():
                shutil.copy(src, output / "amplify_logo.png")
                break
    if not (output / "igem_logo.png").exists():
        src = Path("hp_compass_output") / "igem_logo.png"
        if src.exists():
            shutil.copy(src, output / "igem_logo.png")
