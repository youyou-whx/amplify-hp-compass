from __future__ import annotations

import json
from pathlib import Path

from .classifier import classify_card
from .docx_reader import load_inputs
from .extractor import extract_card
from .graph_builder import build_analytics_report, build_graph
from .maturity import score_maturity
from .recommender import recommend_next_step
from .report import write_dashboard, write_markdown_recommendations
from .schema import HPCard
from .scoring import parse_deadline, score_priority
from .sensitivity import run_sensitivity
from .status import assign_loop_status
from .wiki_generator import save_wiki_files


def run_pipeline(
    input_path: str | Path, output_dir: str | Path, deadline: str | None = None
) -> list[HPCard]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    # 1. 文档提取 → HP 卡片 (extract + classify + status + score + recommend)
    cards: list[HPCard] = []
    for path, text in load_inputs(input_path):
        card = extract_card(path, text)
        card = classify_card(card)
        card = assign_loop_status(card)
        card = score_priority(card, deadline=parse_deadline(deadline))
        card = score_maturity(card)
        card = recommend_next_step(card)
        cards.append(card)

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
    wiki_files = save_wiki_files(cards, analytics, output)
    for name, path in wiki_files.items():
        print(f"Wiki: {path}")

    return cards

