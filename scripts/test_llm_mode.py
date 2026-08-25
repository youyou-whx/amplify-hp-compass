"""LLM 模式本地测试脚本

用法：
    python scripts/test_llm_mode.py --key sk-xxx --file "hp record/某记录.docx"
    python scripts/test_llm_mode.py --key sk-xxx --input "hp record" --output hp_compass_output_llm

单文件模式：打印 LLM 三次调用的完整结果（含稳定性分析），不写输出目录。
全量模式：对输入目录全部 docx 走 LLM 管道，输出到指定目录。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hp_compass.docx_reader import read_docx_text
from hp_compass.llm_annotator import annotate_record
from hp_compass.pipeline import run_pipeline

ENDPOINT = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"


def print_single(path: Path, api_key: str, raw_dir: Path) -> None:
    text = read_docx_text(path)
    annotation = annotate_record(text, api_key, raw_dir, path.stem[:40],
                                 endpoint=ENDPOINT, model=MODEL)

    print("=" * 70)
    print(f"文件: {path.name}")
    print("=" * 70)
    print(f"[Φ₁ 提取]")
    print(f"  日期: {annotation.date}")
    print(f"  利益相关者: {annotation.stakeholder}")
    print(f"  类型: {annotation.stakeholder_type}")
    print(f"  初始问题: {annotation.initial_question[:120]}…")
    print(f"  核心反馈: {annotation.feedback[:160]}…")
    print(f"  项目修改: {annotation.project_action[:160]}…")
    print(f"  证据: {annotation.evidence}")
    print(f"  已回访: {annotation.returned}")
    print(f"[Φ₂ 模块四梯度 → 数值]")
    for module in annotation.module_grades:
        grade = annotation.module_grades[module]
        value = annotation.module_values[module]
        print(f"  {module:20s} {grade}  ({value})")
    print(f"[Φ₅ 成熟度文本信号四梯度]")
    for signal in annotation.maturity_grades:
        print(f"  {signal:20s} {annotation.maturity_grades[signal]}")
    print(f"[Φ₆ 建议]")
    print(f"  下一步: {annotation.next_step_cn}")
    print(f"  材料: {annotation.materials_cn}")
    print(f"  问题: {annotation.questions_cn}")
    print(f"[图谱文本]")
    print(f"  反馈摘要: {annotation.feedback_summary}")
    print(f"  行动摘要: {annotation.action_summary}")
    print(f"[稳定性] 一致率 {annotation.stability_agreement} "
          f"({annotation.stability_checked_fields} 个四梯度字段)")
    print(f"[存档] {annotation.raw_dir}")


def main() -> None:
    global ENDPOINT, MODEL
    parser = argparse.ArgumentParser(description="HP Compass LLM 模式测试")
    parser.add_argument("--key", required=True, help="LLM API Key")
    parser.add_argument("--provider", default="DeepSeek",
                        help="厂商（DeepSeek/OpenAI/Moonshot Kimi/智谱 GLM/阿里通义千问/自定义）")
    parser.add_argument("--model", default="", help="模型名（默认取厂商首个模型）")
    parser.add_argument("--endpoint", default="", help="自定义端点（自定义厂商必填）")
    parser.add_argument("--file", help="单条 docx 文件（与 --input 二选一）")
    parser.add_argument("--input", help="docx 目录（全量管道）")
    parser.add_argument("--output", default="hp_compass_output_llm", help="全量模式输出目录")
    args = parser.parse_args()

    from hp_compass.llm_client import resolve_endpoint

    resolved_endpoint, models = resolve_endpoint(args.provider, args.endpoint)
    ENDPOINT = args.endpoint if args.endpoint else resolved_endpoint
    MODEL = args.model if args.model else (models[0] if models else "")
    print(f"[配置] 厂商={args.provider} 端点={ENDPOINT} 模型={MODEL}")

    if args.file:
        print_single(Path(args.file), args.key, ROOT / "llm_raw_test")
        return

    if args.input:
        cards = run_pipeline(args.input, args.output, mode="llm", api_key=args.key,
                             endpoint=ENDPOINT, model=MODEL)
        print(f"\n全量完成：{len(cards)} 条记录 → {args.output}")
        for card in cards:
            print(f"  {card.hp_id[:50]}  P={card.priority_score:.3f}  "
                  f"稳定率={card.llm_stability}")
        return

    parser.error("必须提供 --file 或 --input")


if __name__ == "__main__":
    main()
