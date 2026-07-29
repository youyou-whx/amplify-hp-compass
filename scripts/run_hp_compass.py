from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hp_compass.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run HP Compass on AMPlify HP records.")
    parser.add_argument("--input", required=True, help="Path to a .docx file or a folder of .docx files.")
    parser.add_argument("--output", default="hp_compass_output", help="Output folder.")
    parser.add_argument("--deadline", default=None, help="Optional deadline in YYYY-MM-DD format.")
    args = parser.parse_args()

    cards = run_pipeline(args.input, args.output, args.deadline)
    output = Path(args.output).resolve()
    print(f"Processed {len(cards)} HP records.")
    print(f"Cards: {output / 'hp_cards.json'}")
    print(f"Graph: {output / 'graph.json'}")
    print(f"Recommendations: {output / 'recommendations.md'}")
    print(f"Dashboard: {output / 'dashboard.html'}")


if __name__ == "__main__":
    main()
