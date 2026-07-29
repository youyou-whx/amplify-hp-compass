from __future__ import annotations

import json
from html import escape
from pathlib import Path

from .schema import GraphData, HPCard


def write_markdown_recommendations(cards: list[HPCard], output_path: Path) -> None:
    ranked = sorted(cards, key=lambda card: card.priority_score, reverse=True)
    lines = [
        "# HP Compass Recommendations",
        "",
        "This report is generated from AMPlify HP records. It supports the existing wet-lab, dry-lab, software, safety, education, and wiki materials by identifying unclosed feedback loops.",
        "",
    ]
    for index, card in enumerate(ranked, start=1):
        lines.extend(
            [
                f"## {index}. {card.stakeholder}",
                "",
                f"- Source: `{Path(card.source_file).name}`",
                f"- Status: `{card.loop_status}`",
                f"- Priority: `{card.priority_score}`",
                f"- Categories: {', '.join(card.affected_modules) or 'Unclassified'}",
                f"- Next step: {card.next_step}",
                f"- Materials: {', '.join(card.suggested_materials)}",
                "- Suggested questions:",
            ]
        )
        lines.extend([f"  - {question}" for question in card.suggested_questions])
        lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def write_dashboard(cards: list[HPCard], graph: GraphData, output_path: Path) -> None:
    # ── 预计算节点重要性，附加到 graph 节点上 ──
    hp_priorities: dict[str, float] = {}
    stakeholder_composites: dict[str, float] = {}
    module_feedback_counts: dict[str, int] = {}
    for card in cards:
        hp_priorities[card.hp_id] = card.priority_score
        module_feedback_counts[card.stakeholder] = module_feedback_counts.get(card.stakeholder, 0) + 1
    for module in (m for c in cards for m in c.affected_modules):
        module_feedback_counts[module] = module_feedback_counts.get(module, 0) + 1

    graph_dict = graph.to_dict()
    for node in graph_dict["nodes"]:
        kind = node.get("kind", "")
        nid = node.get("id", "")
        label = node.get("label", "")

        if kind == "HP":
            node["importance"] = hp_priorities.get(label, 0.5)
        elif kind == "Stakeholder":
            node["importance"] = stakeholder_composites.get(label, 0.5)
        elif kind == "Module":
            max_m = max(module_feedback_counts.values()) if module_feedback_counts else 1
            node["importance"] = min(1.0, module_feedback_counts.get(label, 1) / max(max_m, 1))
        elif kind in ("Feedback", "Action", "NextStep"):
            hp_id = nid.replace(f"{kind.lower()}:", "")
            node["importance"] = hp_priorities.get(hp_id, 0.5)
        elif kind == "Evidence":
            node["importance"] = node.get("score", 0.5)
        else:
            node["importance"] = 0.5

        # 附加 edge 的源/目标 importance 用于线宽
        node["_importance"] = node["importance"]

    payload = {
        "cards": [card.to_dict() for card in cards],
        "graph": graph_dict,
    }
    data_json = json.dumps(payload, ensure_ascii=False)
    html = DASHBOARD_HTML.replace("__HP_COMPASS_DATA__", data_json)
    output_path.write_text(html, encoding="utf-8")


DASHBOARD_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>HP Compass Dashboard</title>
  <style>
    :root {
      --bg: #FFF2CC;
      --panel: #fff8e1;
      --text: #3d2b1f;
      --muted: #5c4a3a;
      --line: #cedbe1;
      --model: #1b5e8a;
      --safety: #b8382b;
      --software: #0d7b6b;
      --environment: #8dba94;
      --wetlab: #7e9fc4;
      --implementation: #e08e4a;
      --education: #e4b8b6;
      --wiki: #f5e4c8;
      --problem: #f4d9a8;
      --accent: #f0a659;
      --highlight: #f9ce99;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    header {
      padding: 14px 28px 10px;
      border-bottom: 1px solid var(--line);
      background: #fff8e1;
      display: flex;
      align-items: center;
      gap: 18px;
    }
    .header-logos {
      display: flex;
      align-items: center;
      gap: 20px;
      flex-shrink: 0;
      background: #ffffff;
      border-radius: 13px;
      padding: 14px 24px;
      box-shadow: 0 3px 12px rgba(0,0,0,0.10);
      border: 1px solid #e8dcc8;
    }
    .header-logos img {
      height: 64px;
      width: auto;
    }
    .header-text { flex: 1; }
    h1 { margin: 0 0 6px; font-size: 26px; }
    .subtitle { color: var(--muted); max-width: 980px; line-height: 1.55; }
    main { padding: 20px 28px 32px; }
    .metrics {
      display: grid;
      grid-template-columns: repeat(4, minmax(160px, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }
    .metric, .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
    }
    .metric .value { font-size: 28px; font-weight: 700; color: var(--model); }
    .metric .label { color: var(--muted); margin-top: 4px; }
    .score { font-variant-numeric: tabular-nums; font-weight: 700; color: var(--model); }
    .layout {
      display: grid;
      grid-template-columns: minmax(0, 1.25fr) minmax(360px, 0.75fr);
      gap: 16px;
      align-items: start;
    }
    .panel h2 { margin: 0 0 12px; font-size: 18px; }
    #graph {
      width: 100%;
      min-height: 560px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff8e1;
    }
    .cards {
      display: grid;
      gap: 10px;
      max-height: 760px;
      overflow: auto;
      padding-right: 4px;
    }
    .card {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: #fff8e1;
      cursor: pointer;
    }
    .card.active { border-color: #f0a659; box-shadow: 0 0 0 2px rgba(240, 166, 89, 0.18); }
    .row { display: flex; justify-content: space-between; gap: 10px; align-items: start; }
    .name { font-weight: 700; line-height: 1.35; }
    /* .score now defined above with color */
    .tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
    .tag {
      border-radius: 999px;
      padding: 3px 8px;
      font-size: 12px;
      color: #fff;
      background: #64748b;
    }
    .tag.Model { background: var(--model); color: #fff; }
    .tag.Safety { background: var(--safety); color: #fff; }
    .tag.Software { background: var(--software); color: #fff; }
    .tag.Environment { background: var(--environment); color: #3d2b1f; }
    .tag.Material { background: var(--wetlab); color: #3d2b1f; }
    .tag.WetLab { background: var(--wetlab); color: #3d2b1f; }
    .tag.Implementation { background: var(--implementation); color: #fff; }
    .tag.Education { background: var(--education); color: #3d2b1f; }
    .tag.SocialMedia { background: var(--wiki); color: #3d2b1f; }
    .tag.WikiNarrative { background: var(--wiki); color: #3d2b1f; }
    .tag.ProblemDefinition { background: var(--problem); color: #3d2b1f; }
    .detail {
      margin-top: 10px;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.5;
    }
    .timeline {
      margin-top: 16px;
      display: grid;
      gap: 8px;
    }
    .timeline-item {
      background: #fff8e1;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px 12px;
    }
    .small { font-size: 13px; color: var(--muted); line-height: 1.45; }
    svg text { font-family: "Segoe UI", "Microsoft YaHei", Arial, sans-serif; }
    @media (max-width: 980px) {
      .metrics, .layout { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <div class="header-logos">
      <img src="amplify_logo.png" alt="AMPlify" title="AMPlify Team">
      <img src="igem_logo.png" alt="iGEM" title="iGEM 2026">
    </div>
    <div class="header-text">
      <h1>HP Compass Dashboard</h1>
      <div class="subtitle">
        Automated classification, L0-L4 loop status, priority scoring, next-step recommendation,
        and Stakeholder-Feedback-Action graph for AMPlify Human Practices.
      </div>
    </div>
  </header>
  <main>
    <section class="metrics" id="metrics"></section>
    <section class="layout">
      <div class="panel">
        <h2>Stakeholder-Feedback-Action Graph</h2>
        <svg id="graph" viewBox="0 0 1000 620" role="img" aria-label="HP Compass graph"></svg>
      </div>
      <div class="panel">
        <h2>Ranked HP Loops</h2>
        <div class="cards" id="cards"></div>
      </div>
    </section>
    <section class="panel" style="margin-top:16px;">
      <h2>Timeline</h2>
      <div class="timeline" id="timeline"></div>
    </section>
  </main>
  <script>
    const data = __HP_COMPASS_DATA__;
    const cards = [...data.cards].sort((a, b) => b.priority_score - a.priority_score);
    const graph = data.graph;

    function cssClass(label) {
      return String(label).replace(/\s+/g, "");
    }

    function renderMetrics() {
      const returned = data.cards.filter(c => c.loop_level === 4).length;
      const high = data.cards.filter(c => c.priority_score >= 0.65).length;
      const modules = new Set(data.cards.flatMap(c => c.affected_modules));
      const metrics = [
        ["HP Loops", data.cards.length],
        ["L4 Returned", returned],
        ["High Priority", high],
        ["Affected Modules", modules.size],
      ];
      document.getElementById("metrics").innerHTML = metrics.map(([label, value]) => `
        <div class="metric"><div class="value">${value}</div><div class="label">${label}</div></div>
      `).join("");
    }

    function renderCards() {
      const root = document.getElementById("cards");
      root.innerHTML = cards.map((card, index) => `
        <article class="card ${index === 0 ? "active" : ""}" data-id="${card.hp_id}">
          <div class="row">
            <div class="name">${escapeHtml(card.stakeholder)}</div>
            <div class="score">${card.priority_score}</div>
          </div>
          <div class="small">${card.loop_status} · ${card.date || "No date"}</div>
          <div class="tags">
            ${card.affected_modules.map(m => `<span class="tag ${cssClass(m)}">${escapeHtml(m)}</span>`).join("")}
          </div>
          <div class="detail">${escapeHtml(card.next_step)}</div>
        </article>
      `).join("");
      root.querySelectorAll(".card").forEach(el => {
        el.addEventListener("click", () => {
          root.querySelectorAll(".card").forEach(item => item.classList.remove("active"));
          el.classList.add("active");
          highlightCard(el.dataset.id);
        });
      });
    }

    function renderTimeline() {
      const timeline = [...data.cards].sort((a, b) => String(a.date).localeCompare(String(b.date)));
      const statusLabels = {"L0_Recorded":"L0","L1_Interpreted":"L1","L2_Actioned":"L2","L3_Evidenced":"L3","L4_Returned":"L4"};
      const statusColors = {"L0_Recorded":"#cedbe1","L1_Interpreted":"#72b6cd","L2_Actioned":"#f0a659","L3_Evidenced":"#bcddae","L4_Returned":"#79a3d1"};
      document.getElementById("timeline").innerHTML = timeline.map(card => {
        const sc = statusColors[card.loop_status] || "#cedbe1";
        const sl = statusLabels[card.loop_status] || "?";
        const mods = (card.affected_modules || []).slice(0, 4);
        const actionText = escapeHtml((card.project_action || card.feedback || "").substring(0, 200));
        return `
        <div class="timeline-item" style="border-left:4px solid ${sc}; padding-left:16px; position:relative">
          <div style="position:absolute; left:-10px; top:18px; width:16px; height:16px; border-radius:50%; background:${sc}; box-shadow:0 0 8px ${sc}60"></div>
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px">
            <strong>${escapeHtml(card.date || "No date")} · ${escapeHtml(card.stakeholder)}</strong>
            <span style="font-weight:700; color:#79a3d1; font-size:14px">${card.priority_score.toFixed(3)}</span>
          </div>
          <div style="font-size:13px; color:#5c4a3a; line-height:1.5; margin-bottom:6px">${actionText}</div>
          <div style="display:flex; gap:6px; flex-wrap:wrap; align-items:center">
            <span style="display:inline-block;background:${sc};color:#fff;padding:1px 8px;border-radius:8px;font-size:10px;font-weight:600">${sl}</span>
            ${mods.map(m => `<span class="tag ${cssClass(m)}" style="font-size:10px;padding:1px 6px">${escapeHtml(m)}</span>`).join("")}
            <span style="margin-left:auto;font-size:11px;color:#79a3d1">Ev:${card.evidence_strength.toFixed(2)}</span>
          </div>
        </div>`;
      }).join("");
    }

    function renderGraph() {
      const svg = document.getElementById("graph");
      const width = 1000, height = 620;
      const nodes = graph.nodes.map((n, i) => ({...n, x: 120 + (i % 6) * 150, y: 90 + Math.floor(i / 6) * 80}));
      const nodeById = new Map(nodes.map(n => [n.id, n]));
      const edges = graph.edges.filter(e => nodeById.has(e.source) && nodeById.has(e.target));

      // ── 预计算边重要性（用于线宽）──
      for (const edge of edges) {
        const a = nodeById.get(edge.source), b = nodeById.get(edge.target);
        const aImp = a.importance || 0.5, bImp = b.importance || 0.5;
        edge._avgImp = (aImp + bImp) / 2;
      }

      for (let iter = 0; iter < 220; iter++) {
        for (const edge of edges) {
          const a = nodeById.get(edge.source), b = nodeById.get(edge.target);
          const dx = b.x - a.x, dy = b.y - a.y;
          const dist = Math.max(1, Math.sqrt(dx * dx + dy * dy));
          const force = (dist - 130) * 0.006;
          const fx = dx / dist * force, fy = dy / dist * force;
          a.x += fx; a.y += fy; b.x -= fx; b.y -= fy;
        }
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            const a = nodes[i], b = nodes[j];
            const dx = b.x - a.x, dy = b.y - a.y;
            const dist2 = Math.max(100, dx * dx + dy * dy);
            const force = 360 / dist2;
            a.x -= dx * force; a.y -= dy * force;
            b.x += dx * force; b.y += dy * force;
          }
        }
        for (const n of nodes) {
          n.x = Math.max(55, Math.min(width - 55, n.x));
          n.y = Math.max(35, Math.min(height - 35, n.y));
        }
      }

      svg.innerHTML = `
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#cedbe1"></path>
          </marker>
        </defs>
      `;

      // ── 边：线宽随重要性 ──
      for (const edge of edges) {
        const a = nodeById.get(edge.source), b = nodeById.get(edge.target);
        const lw = 0.6 + edge._avgImp * 3.8;  // 0.6–4.4
        const alpha = 0.35 + edge._avgImp * 0.55;
        // 边的颜色根据 relation 变化
        const edgeColors = {raised:"#79a3d1", recorded_in:"#cedbe1", led_to:"#f0a659", affects:"#7aaa8a", supported_by:"#e79c98", requires:"#db6254", related_via_module:"#e08e4a"};
        const ec = edgeColors[edge.relation] || "#cedbe1";
        svg.insertAdjacentHTML("beforeend", `
          <line x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}" stroke="${ec}" stroke-width="${lw.toFixed(1)}" marker-end="url(#arrow)" opacity="${alpha.toFixed(2)}"></line>
        `);
      }

      // ── 节点：大小 + 颜色深度随 importance ──
      for (const n of nodes) {
        const imp = n.importance || 0.5;
        const baseColor = colorForKind(n.kind, n.label);
        const fadedColor = lightenColor(baseColor, (1 - imp) * 0.55);
        const r = radiusForKind(n.kind, imp);
        // 边框加粗用于高重要性节点
        const sw = 0.8 + imp * 2.4;
        svg.insertAdjacentHTML("beforeend", `
          <g class="node" data-id="${n.id}">
            <circle cx="${n.x}" cy="${n.y}" r="${r}" fill="${fadedColor}" opacity="0.92" stroke="#3d2b1f" stroke-width="${sw.toFixed(1)}" stroke-opacity="${(0.2+imp*0.6).toFixed(2)}"></circle>
            <text x="${n.x}" y="${n.y + r + 14}" font-size="${(10+imp*4).toFixed(0)}" text-anchor="middle" fill="#3d2b1f" font-weight="${imp>0.6?'600':'400'}">${escapeHtml(truncate(n.label, 80))}</text>
          </g>
        `);
      }
    }

    function lightenColor(hex, factor) {
      hex = hex.replace('#', '');
      const r = Math.round(parseInt(hex.substring(0,2), 16) + (255 - parseInt(hex.substring(0,2), 16)) * factor);
      const g = Math.round(parseInt(hex.substring(2,4), 16) + (255 - parseInt(hex.substring(2,4), 16)) * factor);
      const b = Math.round(parseInt(hex.substring(4,6), 16) + (255 - parseInt(hex.substring(4,6), 16)) * factor);
      return '#' + [r,g,b].map(v => Math.min(255, v).toString(16).padStart(2,'0')).join('');
    }

    function highlightCard(hpId) {
      const svg = document.getElementById("graph");
      svg.querySelectorAll("circle").forEach(circle => circle.setAttribute("stroke", "none"));
      const group = svg.querySelector(`[data-id="hp:${CSS.escape(hpId)}"]`);
      if (group) {
        const circle = group.querySelector("circle");
        circle.setAttribute("stroke", "#f0a659");
        circle.setAttribute("stroke-width", "5");
      }
    }

    function colorForKind(kind, label) {
      // 图谱中所有 Module 节点统一着色
      if (kind === "Module") return "#b8382b";
      return {
        HP: "#3d2b1f",
        Stakeholder: "#79a3d1",
        Feedback: "#72b6cd",
        Action: "#f0a659",
        Evidence: "#e79c98",
        NextStep: "#db6254",
      }[kind] || "#cedbe1";
    }

    function radiusForKind(kind, imp) {
      imp = imp || 0.5;
      const ranges = {
        HP: [12, 31], Stakeholder: [13, 34], Feedback: [9, 20],
        Module: [9, 25], Action: [9, 18], Evidence: [6, 11], NextStep: [7, 11]
      };
      const rng = ranges[kind] || [8, 18];
      return rng[0] + imp * (rng[1] - rng[0]);
    }

    function truncate(value, max) {
      value = String(value || "");
      return value.length <= max ? value : value.slice(0, max - 1) + "…";
    }

    function escapeHtml(value) {
      return String(value || "").replace(/[&<>"']/g, c => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
      }[c]));
    }

    renderMetrics();
    renderCards();
    renderTimeline();
    renderGraph();
  </script>
</body>
</html>
"""

