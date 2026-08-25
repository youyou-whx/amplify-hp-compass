#!/usr/bin/env python3
"""HP Compass — AMPlify Human Practices 决策导航系统

Usage:
    streamlit run app.py

Or generate data first:
    python scripts/run_hp_compass.py --input "hp record" --output hp_compass_output
    streamlit run hp_compass/app.py -- --data hp_compass_output
"""

from __future__ import annotations

import argparse
import json
import re
from html import escape as _escape_html
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import sys as _sys
_HP_COMPASS_ROOT = Path(__file__).resolve().parents[1]
if str(_HP_COMPASS_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_HP_COMPASS_ROOT))

from hp_compass.pipeline import run_pipeline, run_llm_incremental
from hp_compass.schema import HPCard

st.set_page_config(
    page_title="HP Compass — AMPlify",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════
#   色板
#   ───────── 三层模块色 ─────────
#   Tier 1 (核心)    Safety 深红 · Model 宝蓝 · Software 深青
#                    高饱和 + 深色 → 一眼抓住，不可忽视
#   Tier 2 (支撑)    Wet Lab · Environment · Implementation
#                    中等饱和度 → 可见但不抢戏
#   Tier 3 (周边)    Education · Problem Definition · Wiki Narrative
#                    低饱和浅色 → 自然退后
#   基底色           60% 暖奶油底 / 30% 蓝系功能色 / 10% 橙红强调
# ═══════════════════════════════════════════════════════════════

C = {
    # ── 核心层 (bold dark) ──
    "deep_red":        "#b8382b",   # Safety — 深绯红，安全无小事
    "royal_blue":      "#1b5e8a",   # Model — 深宝蓝，算法权威
    "deep_teal":       "#0d7b6b",   # Software — 深青，工程可靠

    # ── 支撑层 (medium) ──
    "steel_blue":      "#7e9fc4",   # Wet Lab — 钢蓝，实验支撑
    "sage_green":      "#8dba94",   # Environment — 灰绿，生态考量
    "amber":           "#e08e4a",   # Implementation — 琥珀，落地行动

    # ── 周边层 (light / muted) ──
    "dusty_pink":      "#e4b8b6",   # Education — 灰粉，教育普及
    "warm_sand":       "#f4d9a8",   # Problem Definition — 暖沙，问题探索
    "light_cream":     "#f5e4c8",   # Wiki Narrative — 浅奶，文档叙事

    # ── 通用功能色 ──
    "warm_orange":     "#f0a659",
    "bean_paste_pink": "#e79c98",
    "haze_blue":       "#79a3d1",
    "pale_icy_blue":   "#cedbe1",
    "cream_apricot":   "#fff8e1",
    "mint_pea_green":  "#bcddae",
    "honey_yellow":    "#f9ce99",
    "retro_brick_red": "#db6254",
    "lake_cyan_blue":  "#72b6cd",
}

# ── 模块标签色 ──  知识卡片 / 气泡图中按模块区分的颜色
MODULE_COLORS = {
    "Safety":             C["deep_red"],
    "Model":              C["royal_blue"],
    "Software":           C["deep_teal"],
    "Material":           C["steel_blue"],
    "Environment":        C["sage_green"],
    "Implementation":     C["amber"],
    "Education":          C["dusty_pink"],
    "Problem Definition": C["warm_sand"],
    "Social Media":       C["light_cream"],
}

# ── 图谱中所有 Module 节点统一颜色 ──
MODULE_GRAPH_COLOR = C["deep_red"]  # 统一深绯红，九个模块在图中同为一级别

# ── 闭环状态色 ──  冷→渐暖→完成：讲述 L0→L4 的旅程
STATUS_COLORS = {
    "L0_Recorded":    C["pale_icy_blue"],   # 冰冷 — 刚记录
    "L1_Interpreted": C["lake_cyan_blue"],  # 流动 — 开始理解
    "L2_Actioned":    C["warm_orange"],     # 升温 — 付诸行动
    "L3_Evidenced":   C["mint_pea_green"],  # 生长 — 证据积累
    "L4_Returned":    C["haze_blue"],       # 深厚 — 闭环完成
}

STATUS_LABELS = {
    "L0_Recorded":    "L0 已记录",
    "L1_Interpreted": "L1 已提炼",
    "L2_Actioned":    "L2 已行动",
    "L3_Evidenced":   "L3 有证据",
    "L4_Returned":    "L4 已回访",
}

# ── 图节点色 ──  Module 在渲染时按模块名查 MODULE_COLORS（三层着色）
NODE_COLORS = {
    "HP":          "#3d2b1f",
    "Stakeholder": C["haze_blue"],
    "Feedback":    C["lake_cyan_blue"],
    "Module":      "#8899aa",       # 实际着色用 MODULE_COLORS
    "Action":      C["warm_orange"],
    "Evidence":    C["bean_paste_pink"],
    "NextStep":    C["retro_brick_red"],
}

NODE_SIZES = {
    "HP": 16, "Stakeholder": 14, "Feedback": 12,
    "Module": 13, "Action": 12, "Evidence": 9, "NextStep": 10,
}

# ── 节点大小动态映射：根据重要性/影响力缩放 ──
#    基数 + (归一化指标 × 缩放区间)，大 = 越重要
NODE_SIZE_RANGES = {
    "HP":          (12, 34),   # priority_score 驱动
    "Stakeholder": (14, 38),   # composite_score 驱动
    "Feedback":    (10, 22),   # 父 HP priority 驱动
    "Module":      (10, 28),   # 被反馈次数驱动
    "Action":      (10, 20),   # 证据数量驱动
    "Evidence":    (7, 12),    # 证据强度驱动
    "NextStep":    (8, 12),    # 父 HP priority 驱动
}


def _lighten(hex_color: str, factor: float) -> str:
    """将 hex 颜色按 factor ∈ [0,1] 线性提亮。

    0.0 = 原色, 1.0 = 白色。用于低重要性节点"褪色"。
    """
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


def _node_importance(kind: str, node: dict,
                     hp_priorities: dict[str, float],
                     stakeholder_composites: dict[str, float],
                     module_feedback_counts: dict[str, int]) -> float:
    """返回节点的重要性归一化值 ∈ [0, 1]。

    不同类型用不同指标：
    - HP / Feedback / Action / NextStep → priority_score + ref_count 加成
    - Stakeholder → composite_score (图拓扑 + HP 优先级混合)
    - Module → 被反馈次数归一化
    - Evidence → evidence_strength
    - 所有节点均受 level（信息层级）和 ref_count（被引用次数）影响
    """
    nid = node.get("id", "")
    ref_count = node.get("ref_count", 1)
    level = node.get("level", 3)

    # ref_count 加成：被引用越多越重要（+0.15 per extra ref, capped at +0.45）
    ref_bonus = min(0.45, (ref_count - 1) * 0.15)

    base = 0.5

    if kind == "HP":
        hp_id = node.get("label", "")
        base = hp_priorities.get(nid.replace("hp:", ""), 0.5)
        # 用 label 匹配
        if base == 0.5:
            for hid, pri in hp_priorities.items():
                if hid.endswith(node.get("label", "")[:16]):
                    base = pri
                    break
    elif kind == "Stakeholder":
        label = node.get("label", "")
        base = stakeholder_composites.get(label, 0.5)
    elif kind == "Module":
        label = node.get("label", "")
        max_count = max(module_feedback_counts.values()) if module_feedback_counts else 8
        count = module_feedback_counts.get(label, 1)
        base = min(1.0, count / max(max_count, 1))
        # 模块受益于 level=3，不做额外 level 惩罚
    elif kind in ("Feedback", "Action"):
        # 主题节点：score + ref_count
        score = node.get("score", 0.5) or 0.5
        base = score + ref_bonus
        base = min(1.0, base)
    elif kind == "Evidence":
        base = node.get("score", 0.5) or 0.5
    elif kind == "NextStep":
        base = 0.4  # NextStep 默认较低

    # level 惩罚：非核心层节点降低重要度基准
    # L1=1.0x, L2=0.90x, L3=0.80x
    level_mult = {1: 1.0, 2: 0.90, 3: 0.80}.get(level, 0.85)
    return min(1.0, base * level_mult)


# ═══════════════════════════════════════════════════════════════
#   全局 CSS — 60% 奶油底 / 30% 蓝系 / 10% 橙红强调
# ═══════════════════════════════════════════════════════════════

GLOBAL_CSS = f"""
<style>
    /* ── 主内容区确保透明 ── */
    .stApp {{
        background: #FFF2CC !important;
    }}
    .stApp > header {{
        background: transparent !important;
    }}
    .main .block-container {{
        padding-top: 2rem;
        background: #FFF2CC !important;
    }}

    /* ── 卡片/容器统一背景 ── */
    .stExpander, .stExpander > div, [data-testid="stExpander"] {{
        background: #fff8e1 !important;
    }}
    section[data-testid="stSidebar"] ~ div .block-container {{
        background: #FFF2CC !important;
    }}

    /* ── 侧边栏渐变 ── */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(175deg, #fdf3e4 0%, {C["cream_apricot"]} 60%, #fdf3e4 100%);
        border-right: 1px solid {C["pale_icy_blue"]};
    }}

    /* ── Expander 标题：禁止截断，允许换行 ── */
    .streamlit-expanderHeader {{
        background-color: {C["cream_apricot"]};
        border-radius: 8px;
        border: 1px solid {C["pale_icy_blue"]};
    }}
    .streamlit-expanderHeader p {{
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: unset !important;
        word-break: break-word;
    }}

    /* ── Radio 选中态 ── */
    div[data-testid="stRadio"] label[data-selected="true"] {{
        background-color: {C["haze_blue"]}18;
        border-left: 3px solid {C["haze_blue"]};
        border-radius: 4px;
    }}

    /* ── 控件 ── */
    .stButton > button {{
        background-color: {C["warm_orange"]} !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }}
    .stButton > button:hover {{
        background-color: {C["retro_brick_red"]} !important;
        color: white !important;
    }}
    [data-testid="stMetricValue"] {{
        color: {C["haze_blue"]} !important;
        font-weight: 700 !important;
    }}
    .stProgress > div > div > div {{
        background-color: {C["mint_pea_green"]} !important;
    }}
    hr {{
        border-color: {C["pale_icy_blue"]} !important;
        opacity: 0.6;
    }}
    input:focus, textarea:focus {{
        border-color: {C["haze_blue"]} !important;
        box-shadow: 0 0 0 1px {C["haze_blue"]}40 !important;
    }}
    .stTabs [aria-selected="true"] {{
        border-bottom-color: {C["warm_orange"]} !important;
    }}
</style>
"""

def _render_impact_bubble_chart(cards: list[dict]) -> None:
    """HP 影响力气泡图：交互式 Plotly 散点图。

    X=时间, Y=优先级, 气泡大小=证据强度, 颜色=主模块。
    鼠标悬停显示完整信息，不再有标签重叠问题。
    """
    try:
        import plotly.express as px
        import plotly.graph_objects as go
    except ImportError:
        st.info("需要 plotly 来渲染交互式气泡图: `pip install plotly`")
        return

    from datetime import date as dt_date

    if not cards:
        st.info("暂无 HP 数据")
        return

    # ── 解析日期，计算实际时间跨度 ──
    from datetime import timedelta

    parsed: list[tuple[str | None, dt_date | None]] = []
    for c in cards:
        ds = c.get("date")
        if ds:
            try:
                parts = ds.split("-")
                d = dt_date(int(parts[0]), int(parts[1]), int(parts[2]))
                parsed.append((ds, d))
            except (ValueError, IndexError):
                parsed.append((ds, None))
        else:
            parsed.append((None, None))

    valid_dates = [d for _, d in parsed if d is not None]
    if valid_dates:
        min_date = min(valid_dates)
        max_date = max(valid_dates)
        mid_date = min_date + (max_date - min_date) // 2
    else:
        min_date = dt_date(2026, 1, 1)
        max_date = dt_date(2026, 12, 31)
        mid_date = dt_date(2026, 6, 15)

    # ── 构建 rows ──
    rows: list[dict] = []
    for c in cards:
        ds = c.get("date")
        try:
            parts = ds.split("-") if ds else None
            d = dt_date(int(parts[0]), int(parts[1]), int(parts[2])) if parts else mid_date
        except (ValueError, IndexError):
            d = mid_date

        mods = c.get("affected_modules", [])
        primary_module = mods[0] if mods else "Unclassified"
        all_modules = ", ".join(mods) if mods else "Unclassified"

        ev_count = len(c.get("evidence", []))
        ev_strength = c.get("evidence_strength", 0)

        rows.append({
            "date": d,
            "date_label": ds or "日期未知",
            "priority": c.get("priority_score", 0.5),
            "stakeholder": c.get("stakeholder", "?"),
            "stakeholder_type": c.get("stakeholder_type", ""),
            "module": primary_module,
            "all_modules": all_modules,
            "evidence_count": ev_count,
            "evidence_strength": ev_strength,
            "loop_status": c.get("loop_status", ""),
            "bubble_size": max(14, (ev_count + 1) * (1 + ev_strength) * 18),
        })

    # ── 模块颜色映射 ──
    unique_modules = list(dict.fromkeys(r["module"] for r in rows))
    color_map = {m: MODULE_COLORS.get(m, C["pale_icy_blue"]) for m in unique_modules}

    # ── 自定义 hover 模板 ──
    hovertemplate = (
        "<b>%{customdata[0]}</b><br>"
        "日期: %{customdata[1]}<br>"
        "类型: %{customdata[2]}<br>"
        "优先级: %{y:.3f}<br>"
        "证据: %{customdata[3]} 项 · 强度 %{customdata[4]:.2f}<br>"
        "模块: %{customdata[5]}<br>"
        "状态: %{customdata[6]}<br>"
        "<extra></extra>"
    )

    fig = go.Figure()

    for mod in unique_modules:
        idxs = [i for i, r in enumerate(rows) if r["module"] == mod]
        if not idxs:
            continue
        fig.add_trace(go.Scatter(
            x=[rows[i]["date"] for i in idxs],
            y=[rows[i]["priority"] for i in idxs],
            mode="markers+text",
            name=mod,
            marker=dict(
                size=[rows[i]["bubble_size"] for i in idxs],
                color=color_map[mod],
                line=dict(color="#3d2b1f", width=0.8),
                opacity=0.85,
                sizemode="area",
                sizeref=0.7,
            ),
            customdata=[[
                rows[i]["stakeholder"],
                rows[i]["date_label"],
                rows[i]["stakeholder_type"],
                rows[i]["evidence_count"],
                rows[i]["evidence_strength"],
                rows[i]["all_modules"],
                rows[i]["loop_status"],
            ] for i in idxs],
            hovertemplate=hovertemplate,
            text=[rows[i]["stakeholder"] for i in idxs],
            textposition="top center",
            textfont=dict(size=9, color="#3d2b1f"),
        ))

    # ── X 轴范围：数据区间 ±15 天 ──
    x_padding = timedelta(days=15)
    x_min = (min_date - x_padding).isoformat()
    x_max = (max_date + x_padding).isoformat()

    fig.update_layout(
        paper_bgcolor="#FFF2CC",
        plot_bgcolor="#FFF2CC",
        font=dict(family="Microsoft YaHei, Segoe UI, sans-serif", color="#3d2b1f"),
        title=dict(
            text="<b>HP Impact Overview</b> — 悬停查看详情 · 气泡越大 = 证据越充分 · 位置越高 = 优先级越高",
            font=dict(size=13, color="#3d2b1f"),
            x=0.01,
        ),
        xaxis=dict(
            title="2026",
            gridcolor="rgba(206,219,225,0.38)",
            zeroline=False,
            tickformat="%m/%d",
            range=[x_min, x_max],
            autorange=False,
        ),
        yaxis=dict(
            title="Priority Score",
            gridcolor="rgba(206,219,225,0.25)",
            range=[-0.02, 1.12],
            zeroline=False,
        ),
        legend=dict(
            title=dict(text="Affected Module", font=dict(size=10)),
            font=dict(size=9),
            bgcolor="#fff8e1",
            bordercolor=C["pale_icy_blue"],
        ),
        hoverlabel=dict(
            bgcolor="#fff8e1",
            bordercolor=C["haze_blue"],
            font=dict(size=12, color="#3d2b1f"),
        ),
        margin=dict(l=50, r=20, t=50, b=40),
        height=480,
    )

    fig.update_xaxes(type="date")

    st.plotly_chart(fig, use_container_width=True, config={
        "displayModeBar": True,
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
        "displaylogo": False,
    })


# ═══════════════════════════════════════════════════════════════
#   数据加载
# ═══════════════════════════════════════════════════════════════


@st.cache_data(ttl=30)
def load_data(data_dir: str, _cache_version: str = "") -> dict:
    """加载 HP Compass 输出数据。TTL=30s 确保 pipeline 重跑后缓存自动刷新。"""
    data_path = Path(data_dir)
    cards_file = data_path / "hp_cards.json"
    graph_file = data_path / "graph.json"
    analytics_file = data_path / "analytics.json"

    if not cards_file.exists():
        st.error(f"数据文件未找到: {cards_file}")
        st.info("请先运行: python scripts/run_hp_compass.py --input <docx_folder> --output <output_dir>")
        st.stop()

    return {
        "cards": json.loads(cards_file.read_text(encoding="utf-8")),
        "graph": json.loads(graph_file.read_text(encoding="utf-8"))
        if graph_file.exists()
        else None,
        "analytics": json.loads(analytics_file.read_text(encoding="utf-8"))
        if analytics_file.exists()
        else None,
    }


# ═══════════════════════════════════════════════════════════════
#   页面 1: HP Map — 知识图谱
# ═══════════════════════════════════════════════════════════════


def page_hp_map(cards: list[dict], graph: dict, analytics: dict | None) -> None:
    st.title("🧭 HP Map — Stakeholder-Feedback-Action 知识图谱")
    st.markdown(
        "展示每一位利益相关者 → 反馈 → 行动 → 证据的知识网络。\n\n"
        "**节点越大 = 越重要/影响力越高**；"
        "**颜色越深 = 优先级越高**，褪色节点表示影响较低；"
        "**连线粗细** 表示关系紧密程度。"
    )

    # ── 预计算指标映射 ──
    hp_priorities: dict[str, float] = {}
    stakeholder_composites: dict[str, float] = {}
    for c in cards:
        hp_id = c.get("hp_id", "")
        hp_priorities[hp_id] = c.get("priority_score", 0.5)
    if analytics:
        for s in analytics.get("top_stakeholders", []):
            stakeholder_composites[s.get("label", "")] = s.get("composite_score", 0.5)

    module_feedback_counts: dict[str, int] = {}
    if analytics:
        for m in analytics.get("module_impact", []):
            module_feedback_counts[m.get("module", "")] = m.get("hp_feedback_count", 1)
    # fallback: compute from graph edges
    if not module_feedback_counts:
        for node in graph.get("nodes", []):
            if node.get("kind") == "Module":
                label = node.get("label", "")
                module_feedback_counts[label] = max(module_feedback_counts.get(label, 0), 1)

    # ── 左侧：交互式知识图谱 ──
    col1, col2 = st.columns([3, 1])

    with col1:
        view_mode = st.radio(
            "视图模式",
            ["🗺️ 交互式知识图谱", "📊 HP 影响力气泡图"],
            horizontal=True,
            label_visibility="collapsed",
        )

        if view_mode == "📊 HP 影响力气泡图":
            _render_impact_bubble_chart(cards)
        else:
            try:
                from pyvis.network import Network

                net = Network(
                    height="660px", width="100%",
                    bgcolor="#fff8e1",
                    font_color="#3d2b1f",
                )
                net.force_atlas_2based()
                # 调优物理参数：让大节点更"重"，小节点环绕
                net.set_options("""
                {
                  "physics": {
                    "barnesHut": {
                      "gravitationalConstant": -2800,
                      "centralGravity": 0.25,
                      "springLength": 160,
                      "springConstant": 0.02
                    },
                    "minVelocity": 0.75
                  }
                }
                """)

                node_ids: set[str] = set()
                max_importance = 0.01  # avoid div-by-zero

                # First pass: compute importance for sizing
                node_importances: dict[str, float] = {}
                for node in graph.get("nodes", []):
                    nid = node["id"]
                    kind = node.get("kind", "")
                    imp = _node_importance(kind, node, hp_priorities,
                                           stakeholder_composites, module_feedback_counts)
                    node_importances[nid] = imp
                    if imp > max_importance:
                        max_importance = imp

                # Second pass: add nodes with variable size & color depth
                for node in graph.get("nodes", []):
                    nid = node["id"]
                    if nid in node_ids:
                        continue
                    node_ids.add(nid)

                    kind = node.get("kind", "")
                    # Non-HP node labels are content text → allow up to 160 chars
                    label = node.get("label", nid)
                    if len(label) > 160:
                        label = label[:159].rstrip() + "…"
                    base_color = NODE_COLORS.get(kind, C["pale_icy_blue"])
                    # 图谱中所有 Module 节点统一着色（#b8382b）
                    if kind == "Module":
                        base_color = MODULE_GRAPH_COLOR
                    imp = node_importances.get(nid, 0.5)

                    # ── Size: importance-scaled ──
                    lo, hi = NODE_SIZE_RANGES.get(kind, (8, 20))
                    size = lo + imp * (hi - lo)

                    # ── Color depth: low importance → lighter (faded) ──
                    #  Module 节点都统一颜色，重要性高 → 饱和，低 → 褪色
                    fade = (1.0 - imp) * 0.55
                    color = _lighten(base_color, fade)

                    # ── Rich tooltip with hierarchy level ──
                    level = node.get("level", 3)
                    level_label = {1: "L1 战略层", 2: "L2 执行层", 3: "L3 验证层"}.get(level, "")
                    title_parts = [f"<b>{label}</b>", f"Type: {kind} · {level_label}"]
                    if node.get("stakeholder_type"):
                        title_parts.append(f"Category: {node['stakeholder_type']}")
                    if node.get("score"):
                        title_parts.append(f"Priority: {node['score']:.3f}")
                    if node.get("status"):
                        title_parts.append(f"Status: {node['status']}")
                    if node.get("ref_count", 1) > 1:
                        title_parts.append(f"Referenced by: {node['ref_count']} cycles")
                    if node.get("themes"):
                        title_parts.append(f"Themes: {', '.join(node['themes'])}")
                    # Module-specific
                    if kind == "Module" and label in module_feedback_counts:
                        title_parts.append(f"HP feedbacks: {module_feedback_counts[label]}")
                    title_parts.append(f"<i>Impact: {imp:.2f}</i>")
                    title_text = "<br>".join(title_parts)

                    net.add_node(
                        nid, label=label, color=color, size=size,
                        title=title_text,
                        borderWidth=2,
                        borderWidthSelected=4,
                    )

                # ── Edges with variable width ──
                for edge in graph.get("edges", []):
                    src, tgt = edge.get("source"), edge.get("target")
                    if src not in node_ids or tgt not in node_ids:
                        continue
                    relation = edge.get("relation", "")
                    # Edge width: scale by importance of connected nodes
                    src_imp = node_importances.get(src, 0.5)
                    tgt_imp = node_importances.get(tgt, 0.5)
                    avg_imp = (src_imp + tgt_imp) / 2
                    width = 0.6 + avg_imp * 3.4  # range: 0.6–4.0

                    # Edge color: different tints per relation type
                    edge_colors = {
                        "raised":              C["haze_blue"],
                        "recorded_in":         C["pale_icy_blue"],
                        "led_to":              C["warm_orange"],
                        "affects":             "#7aaa8a",
                        "supported_by":        C["bean_paste_pink"],
                        "requires":            C["retro_brick_red"],
                        "related_via_module":  C["amber"],
                    }
                    edge_color = edge_colors.get(relation, C["pale_icy_blue"])

                    net.add_edge(
                        src, tgt,
                        title=relation,
                        arrows="to",
                        color={"color": edge_color, "opacity": 0.55 + avg_imp * 0.45},
                        width=width,
                    )

                html_path = Path("hp_compass_graph_temp.html")
                net.save_graph(str(html_path))
                html_text = html_path.read_text(encoding="utf-8")

                # 内联本地 vis-network JS/CSS，避免依赖外部 CDN
                vis_js_path = Path("lib/vis-9.1.2/vis-network.min.js")
                if vis_js_path.exists():
                    vis_js_content = vis_js_path.read_text(encoding="utf-8")
                    # 用 lambda 避免 re.sub 把 JS 中的反斜杠当转义符解析
                    import re as _re
                    html_text = _re.sub(
                        r'<script[^>]*src="[^"]*vis-network[^"]*"[^>]*></script>',
                        lambda _m: f'<script>{vis_js_content}</script>',
                        html_text,
                    )
                    vis_css_path = Path("lib/vis-9.1.2/vis-network.css")
                    if vis_css_path.exists():
                        vis_css_content = vis_css_path.read_text(encoding="utf-8")
                        html_text = _re.sub(
                            r'<link[^>]*href="[^"]*vis-network[^"]*"[^>]*/?>',
                            lambda _m: f'<style>{vis_css_content}</style>',
                            html_text,
                        )

                components.html(html_text, height=680)
                html_path.unlink(missing_ok=True)

            except ImportError:
                _fallback_graph_svg(graph)

    # ── 右侧：图分析洞察 ──
    with col2:
        st.subheader("📊 图分析洞察")

        # 基础统计：优先从 analytics，否则从 graph 实时计算
        stats = analytics.get("graph_stats") if analytics else None
        if stats:
            n_nodes = stats.get("total_nodes", 0)
            n_edges = stats.get("total_edges", 0)
            density = stats.get("density", 0.0)
        else:
            # 从 graph 对象实时计算
            g_nodes = graph.get("nodes", []) if graph else []
            g_edges = graph.get("edges", []) if graph else []
            n_nodes = len(g_nodes)
            n_edges = len(g_edges)
            max_edges = n_nodes * (n_nodes - 1)
            density = n_edges / max_edges if max_edges > 0 else 0.0

        # DEBUG: 显示数据来源
        st.caption(f"DEBUG: analytics={analytics is not None}, stats={stats is not None}, "
                   f"graph nodes={len(graph.get('nodes', [])) if graph else 0}, "
                   f"n_nodes={n_nodes}, n_edges={n_edges}, density={density}")

        c_a, c_b, c_c = st.columns(3)
        with c_a:
            st.metric("总节点数", n_nodes)
        with c_b:
            st.metric("总边数", n_edges)
        with c_c:
            st.metric("图密度", round(density, 4))

        st.divider()

        # ── 图例：节点大小 & 颜色含义 ──
        st.markdown(
            f"<span style='background:{C['haze_blue']};color:white;"
            f"padding:4px 14px;border-radius:12px;font-size:13px;font-weight:600'>"
            f"📐 视觉编码说明</span>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<small style='color:#5c4a3a'>"
            f"<b>节点越大</b> → 影响力/优先级越高<br>"
            f"<b>颜色越深</b> → 越重要；褪色节点影响较低<br>"
            f"<b>连线越粗</b> → 关系越紧密<br>"
            f"<b>连线颜色</b>：<br>"
            f"<span style='color:{C['haze_blue']}'>● raised</span> "
            f"<span style='color:{C['pale_icy_blue']}'>● recorded_in</span> "
            f"<span style='color:{C['warm_orange']}'>● led_to</span><br>"
            f"<span style='color:{C['mint_pea_green']}'>● affects</span> "
            f"<span style='color:{C['bean_paste_pink']}'>● supported_by</span> "
            f"<span style='color:{C['retro_brick_red']}'>● requires</span><br>"
            f"<span style='color:{C['amber']}'>● related（共享模块）</span>"
            f"</small>",
            unsafe_allow_html=True,
        )

        st.divider()

        # 子标题用雾蓝底白字 chip（依赖 analytics，无数据时跳过）
        top_stakeholders = analytics.get("top_stakeholders", []) if analytics else []
        if top_stakeholders:
            st.markdown(
                f"<span style='background:{C['haze_blue']};color:white;"
                f"padding:4px 14px;border-radius:12px;font-size:13px;font-weight:600'>"
                f"影响力最高的 Stakeholder</span>",
                unsafe_allow_html=True,
            )
            for s in top_stakeholders[:5]:
                composite = s.get('composite_score', 0)
                st.markdown(
                    f"<div style='margin-bottom:6px'>"
                    f"<div style='display:flex;justify-content:space-between;font-size:13px'>"
                    f"<span><b>{s.get('label', '')}</b> "
                    f"<small>({s.get('stakeholder_type', '')})</small></span>"
                    f"<span style='color:{C['haze_blue']};font-weight:700'>{composite:.3f}</span>"
                    f"</div>"
                    f"<div style='background:{C['pale_icy_blue']}60;border-radius:4px;"
                    f"height:4px;margin-top:2px'>"
                    f"<div style='background:{C['haze_blue']};width:{composite*100:.0f}%;"
                    f"height:100%;border-radius:4px'></div>"
                    f"</div></div>",
                    unsafe_allow_html=True,
                )
            st.divider()

        module_impact = analytics.get("module_impact", []) if analytics else []
        if module_impact:
            st.markdown(
                f"<span style='background:{C['mint_pea_green']};color:#3d2b1f;"
                f"padding:4px 14px;border-radius:12px;font-size:13px;font-weight:600'>"
                f"被 HP 影响最多的模块</span>",
                unsafe_allow_html=True,
            )
            max_impact = max(
                (x.get("hp_feedback_count", 1) for x in module_impact),
                default=1,
            )
            for m in module_impact[:5]:
                count = m.get("hp_feedback_count", 0)
                st.progress(
                    min(1.0, count / max_impact),
                    text=f"{m.get('module', '')} ({count} 次反馈)",
                )


# ═══════════════════════════════════════════════════════════════
#   辅助：拆分反馈中内嵌的「HP 摘要卡片」
# ═══════════════════════════════════════════════════════════════


def _parse_feedback(feedback_text):
    """Split feedback into (pure_feedback, summary_dict).

    Many HP records embed a summary card inside the feedback field.
    This function extracts it cleanly.
    """
    text = str(feedback_text).strip()
    if not text:
        return "", None

    # Locate marker: "摘要卡片" or "摘要卡⽚片" or "Human Practices 摘要卡片"
    # Use Unicode escapes: 摘要=摘要 卡=卡 片=片
    marker_pat = (
        r"(?:Human\s*Practices?\s*)?" +
        "摘要[卡⼚片]"
    )
    m = re.search(marker_pat, text)
    if not m:
        return text, None

    pure_feedback = text[:m.start()].strip()

    # Remove first line (the marker line) with simple string split
    summary_block = text[m.start():]
    summary_block = summary_block.split("\n", 1)[-1].strip()

    summary = {"headline": "", "who": "", "why": "", "learned": ""}

    # Section patterns using \u escapes:
    # 访谈对象是谁？ = 访谈对象是谁？
    # 访谈对象： = 访谈对象：
    # 为什么？ = 为什么？
    # 缘由： = 缘由：
    # 我们学到了什么？ = 我们学到了什么？
    # 学到了什么？ = 学到了什么？
    section_pats = [
        ("who", [
            "我们联系了谁[？?：:]?",
            "访谈对象是谁[？?]?",
            "访谈对象[：:]?",
        ]),
        ("why", [
            "为什么[？?]?",
            "缘由[：:]?",
        ]),
        ("learned", [
            "我们学到了什么[？?]?",
            "学到了什么[？?]?",
        ]),
    ]

    remaining = summary_block
    first_sec = len(remaining)
    for _key, pats in section_pats:
        for pat in pats:
            m2 = re.search(pat, remaining)
            if m2 and m2.start() < first_sec:
                first_sec = m2.start()

    if first_sec > 0:
        summary["headline"] = remaining[:first_sec].strip().lstrip("：: ")
        remaining = remaining[first_sec:]

    for key, pats in section_pats:
        for pat in pats:
            m2 = re.search(pat, remaining)
            if m2:
                start = m2.end()
                end = len(remaining)
                for k2, pats2 in section_pats:
                    if k2 == key:
                        continue
                    for p2 in pats2:
                        m3 = re.search(p2, remaining[start:])
                        if m3 and start + m3.start() < end:
                            end = start + m3.start()
                content = remaining[start:end].strip().rstrip("?？").strip()
                content = re.sub(r"^[：:\s]+", "", content)
                summary[key] = content
                break

    return pure_feedback, summary


def _render_knowledge_card(
    date: str,
    stakeholder: str,
    stakeholder_type: str,
    who_text: str,
    why_text: str,
    learned_text: str,
    action_text: str,
    modules: list[str],
    status: str,
    status_color: str,
    status_label: str,
    priority: float,
    evidence_count: int,
    evidence_strength: float,
) -> str:
    """Render a single HP interaction as a knowledge card,
    following the iGEM wiki format:

        Who we contacted → Why → What we learned → How we changed

    Inspired by JU Krakow 2024 and NYU Abu Dhabi 2025 HP pages.
    """

    # ── Section builder ──
    def _section(icon: str, label: str, content: str, accent: str) -> str:
        if not content.strip():
            return ""
        return (
            f"<div style='margin-bottom:14px'>"
            f"<div style='font-weight:700;font-size:12px;color:{accent};"
            f"letter-spacing:0.3px;margin-bottom:4px'>"
            f"{icon}  {label}</div>"
            f"<div style='font-size:13.5px;color:#3d2b1f;line-height:1.7;"
            f"padding-left:4px'>{_escape_html(content)}</div>"
            f"</div>"
        )

    # ── Module tags ──
    tag_html = ""
    if modules:
        tags = []
        for m in modules:
            mc = MODULE_COLORS.get(m, C["pale_icy_blue"])
            tc = "#3d2b1f" if m in ("Wet Lab", "Environment",
                                     "Problem Definition", "Wiki Narrative",
                                     "Education") else "#fff"
            tags.append(
                f"<span style='display:inline-block;background:{mc};color:{tc};"
                f"padding:2px 10px;border-radius:10px;font-size:11px;"
                f"margin:2px 4px 2px 0;font-weight:500'>{m}</span>"
            )
        tag_html = (
            f"<div style='margin-top:4px;padding-top:12px;"
            f"border-top:1px solid {C['pale_icy_blue']}60'>"
            f"<span style='font-size:11px;color:#5c4a3a;font-weight:600;"
            f"margin-right:8px'>AFFECTED MODULES</span>"
            f"{''.join(tags)}"
            f"</div>"
        )

    # ── Status bar ──
    status_bar = (
        f"<div style='margin-bottom:16px;display:flex;align-items:center;"
        f"gap:14px;flex-wrap:wrap'>"
        f"<span style='display:inline-block;background:{status_color};color:#fff;"
        f"padding:2px 12px;border-radius:10px;font-size:11px;font-weight:600'>"
        f"{status_label}</span>"
        f"<span style='font-size:11px;color:{C['haze_blue']};font-weight:600'>"
        f"Priority  {priority:.3f}</span>"
        f"<span style='font-size:11px;color:{C['mint_pea_green']};font-weight:600'>"
        f"Evidence  {evidence_count} items  ·  strength {evidence_strength:.2f}</span>"
        f"<span style='font-size:11px;color:#5c4a3a;margin-left:auto'>"
        f"{stakeholder_type}</span>"
        f"</div>"
    )

    # ── Knowledge card sections ──
    sections = "".join(filter(None, [
        _section("👤", "WHO WE CONTACTED", who_text, C["haze_blue"]),
        _section("🎯", "WHY WE DID THIS", why_text, C["lake_cyan_blue"]),
        _section("💡", "WHAT WE LEARNED", learned_text, C["warm_orange"]),
        _section("🔧", "HOW WE CHANGED OUR PROJECT", action_text, C["mint_pea_green"]),
    ]))

    # ── Assemble card ──
    return (
        f"<div style='background:#fff8e1;border-radius:12px;"
        f"border:1px solid {C['pale_icy_blue']}90;"
        f"padding:20px 24px 16px;margin-bottom:28px;"
        f"box-shadow:0 2px 10px rgba(61,43,31,0.05)'>"
        f"<div style='font-size:16px;font-weight:700;color:#3d2b1f;"
        f"margin-bottom:14px'>{_escape_html(stakeholder)}</div>"
        f"{status_bar}"
        f"{sections}"
        f"{tag_html}"
        f"</div>"
    )


# ═══════════════════════════════════════════════════════════════
#   成熟度雷达图渲染
# ═══════════════════════════════════════════════════════════════

# 维度短标签（用于雷达图轴，支持换行）
_RADAR_LABELS = [
    "Reflecting on<br>design decisions",
    "Exploring and reflecting<br>on context beyond the lab",
    "Incorporating<br>diverse perspectives",
    "Anticipating positive<br>and negative impacts",
    "Responding to human<br>practices work",
    "Approaching limitations<br>with integrity",
]

# 维度 key（对应 maturity_scores 的键）
_RADAR_KEYS = [
    "design_reflection",
    "context_exploration",
    "diverse_perspectives",
    "impact_anticipation",
    "hp_response",
    "limitation_integrity",
]

# 各维度各等级的锚定描述（用于 hover）
_RADAR_ANCHORS = {
    "design_reflection": {
        0: "L0 无设计反思 — 仅有原始记录",
        1: "L1 表层理解 — 未触及设计层面",
        2: "L2 注意到设计含义 — 设计模块或关键词出现",
        3: "L3 明确的设计变更 — 有具体修改行动",
        4: "L4 跨模块设计迭代 — 多设计模块联动+证据",
        5: "L5 系统性设计反思 — 完整设计迭代闭环",
    },
    "context_exploration": {
        0: "L0 纯实验室视角 — 未涉及真实场景",
        1: "L1 意识到真实场景 — 提及应用场景",
        2: "L2 探索了一个真实场景 — Implementation/Environment",
        3: "L3 深度场景探索 — 多场景或真实stakeholder",
        4: "L4 系统性场景探索 — 真实场景+证据",
        5: "L5 场景验证闭环 — 全链条+强证据",
    },
    "diverse_perspectives": {
        0: "L0 单一窄视角 — 0-1个模块",
        1: "L1 有限视角 — 1-2个模块",
        2: "L2 同域多角度 — 3-4个模块",
        3: "L3 跨域视角 — 5+模块或独特stakeholder",
        4: "L4 桥接多方视角 — 独特类型+4+模块",
        5: "L5 综合多利益相关者 — 最高广度",
    },
    "impact_anticipation": {
        0: "L0 未考虑影响 — 无Safety/Environment",
        1: "L1 仅关注正面影响 — 无风险语言",
        2: "L2 意识到潜在负面影响 — 含风险关键词",
        3: "L3 明确负面风险识别 — Safety/Env+风险",
        4: "L4 正负影响均有应对 — 含缓解措施",
        5: "L5 系统化影响评估 — 完整风险评估产物",
    },
    "hp_response": {
        0: "L0 未响应",
        1: "L1 反馈已理解 — 反馈文本已提取",
        2: "L2 基础响应计划 — 有行动方向",
        3: "L3 具体行动已执行 — 行动内容充实",
        4: "L4 证据支撑的响应 — 有实质证据",
        5: "L5 闭环验证完成 — 已回访确认",
    },
    "limitation_integrity": {
        0: "L0 未讨论局限性",
        1: "L1 模糊承认不足 — 1个局限性关键词",
        2: "L2 明确局限性识别 — 2+关键词",
        3: "L3 多局限性讨论 — 触及Safety/Env",
        4: "L4 局限性+边界设定 — 明确边界语言",
        5: "L5 系统化局限性框架 — 含边界文档",
    },
}


def _render_maturity_radar(card: dict, key_suffix: str = "") -> None:
    """在 Streamlit 中渲染一张 HP 卡片的六维成熟度雷达图。

    使用 Plotly Scatterpolar + 分层背景环，暖橙系配色，
    与 HP Compass 整体设计协调。
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        st.info("需要 plotly 来渲染成熟度雷达图: `pip install plotly`")
        return

    scores = card.get("maturity_scores", {})
    if not scores:
        st.caption("暂无成熟度评分数据。请重新运行 pipeline。")
        return

    values = [scores.get(key, 0) for key in _RADAR_KEYS]
    display_labels = list(_RADAR_LABELS)

    # ── 颜色方案（暖橙系） ──
    fill_color = "rgba(240, 166, 89, 0.32)"       # warm_orange 半透明填充
    stroke_color = "#e08e4a"                        # amber 描边
    marker_color = "#f0a659"                        # warm_orange 顶点
    marker_edge = "#3d2b1f"                         # 深棕顶点边框
    grid_color = "rgba(206, 219, 225, 0.45)"       # pale_icy_blue 网格
    bg_color = "#FFF2CC"                            # 主背景暖奶油

    # ── 构建 hover 文本 ──
    hover_texts = []
    for key, val in zip(_RADAR_KEYS, values):
        anchor_desc = _RADAR_ANCHORS.get(key, {}).get(val, f"Level {val}")
        short_label = _RADAR_LABELS[_RADAR_KEYS.index(key)].replace("<br>", " ")
        hover_texts.append(
            f"<b>{short_label}</b><br>"
            f"Level: {val}/5<br>"
            f"<i>{anchor_desc}</i>"
        )

    fig = go.Figure()

    # ── 主数据：填充 + 描边 + 顶点（六边形）──
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=display_labels,
        fill="toself",
        fillcolor=fill_color,
        line=dict(color=stroke_color, width=2.8, shape="linear"),
        marker=dict(
            color=marker_color,
            size=10,
            line=dict(color=marker_edge, width=1.4),
        ),
        name="Maturity",
        hovertemplate="%{hovertext}<extra></extra>",
        hovertext=hover_texts,
    ))

    # ── 布局：六边形网格 + 分层刻度环 ──
    fig.update_layout(
        polar=dict(
            gridshape="linear",
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickmode="linear",
                tick0=0,
                dtick=1,
                gridcolor=grid_color,
                gridwidth=1,
                linecolor="rgba(206, 219, 225, 0.7)",
                linewidth=1,
                tickfont=dict(size=9, color="#5c4a3a"),
                ticks="",
                showticklabels=True,
                ticklen=0,
            ),
            angularaxis=dict(
                gridcolor=grid_color,
                gridwidth=1,
                linecolor="rgba(206, 219, 225, 0.7)",
                linewidth=1,
                tickfont=dict(
                    size=10,
                    color="#3d2b1f",
                    family="Microsoft YaHei, Segoe UI, sans-serif",
                ),
                ticks="",
            ),
            bgcolor=bg_color,
        ),
        paper_bgcolor=bg_color,
        font=dict(family="Microsoft YaHei, Segoe UI, sans-serif", color="#3d2b1f"),
        margin=dict(l=50, r=50, t=30, b=30),
        height=440,
        showlegend=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=f"radar_{key_suffix}",
        config={
            "displayModeBar": False,
            "displaylogo": False,
        },
    )

    # ── 六维得分摘要卡片 ──
    cols = st.columns(6)
    for j, (key, label) in enumerate(zip(_RADAR_KEYS, _RADAR_LABELS)):
        val = scores.get(key, 0)
        # 每级一个实心点 + 灰色空心点补足到 5
        filled = "●" * val
        empty = "○" * (5 - val)
        dots = filled + empty
        short = label.replace("<br>", " ")
        with cols[j]:
            st.markdown(
                f"<div style='text-align:center;font-size:10px;color:#5c4a3a;"
                f"margin-bottom:2px'>{short}</div>"
                f"<div style='text-align:center;font-size:9px;color:{C['warm_orange']};"
                f"letter-spacing:1px'>{dots}</div>"
                f"<div style='text-align:center;font-weight:700;font-size:15px;"
                f"color:{C['warm_orange']}'>{val}/5</div>",
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════════
#   页面 2: Timeline — 时间线 (Knowledge Card 风格)
# ═══════════════════════════════════════════════════════════════


def page_timeline(cards: list[dict]) -> None:
    st.title("📅 HP Timeline — 时间线")
    st.markdown(
        "每条 Human Practices 互动都以 **知识卡片 (Knowledge Card)** 形式呈现，"
        "沿用 iGEM wiki 的经典结构："
        "**Who → Why → What We Learned → How We Changed**。"
        "同一循环的多次访问（初次访谈与二轮回访）各按日期独立呈现。"
    )

    # ── 把初次访谈与回访访问展开成扁平条目，按日期统一排序 ──
    entries: list[dict] = []
    for card in cards:
        entries.append({"date": card.get("date") or "9999-99-99", "card": card, "visit": None})
        for visit in card.get("visits", []):
            entries.append({
                "date": visit.get("date") or "9999-99-99",
                "card": card,
                "visit": visit,
            })
    entries.sort(key=lambda e: e["date"])

    for i, entry in enumerate(entries):
        card = entry["card"]
        visit = entry["visit"]

        # ── 回访访问条目 ──
        if visit is not None:
            visit_date = visit.get("date") or "—"
            visit_summary = visit.get("summary", "")
            vcols = st.columns([1, 24])
            with vcols[0]:
                st.markdown(
                    f"<div style='text-align:center;padding-top:14px'>"
                    f"<div style='font-size:10px;font-weight:700;"
                    f"color:{C['retro_brick_red']};margin-bottom:4px'>{visit_date}</div>"
                    f"<div style='width:16px;height:16px;border-radius:50%;"
                    f"background:{C['retro_brick_red']};margin:0 auto;"
                    f"box-shadow:0 0 10px {C['retro_brick_red']}50'></div>"
                    f"<div style='width:2px;height:32px;"
                    f"background:{C['pale_icy_blue']}60;margin:0 auto;margin-top:4px'></div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            with vcols[1]:
                st.markdown(
                    f"<div style='background:#fff8e1;border:1px dashed "
                    f"{C['retro_brick_red']}60;border-radius:10px;padding:12px 16px;"
                    f"margin-bottom:10px'>"
                    f"<span style='display:inline-block;background:{C['retro_brick_red']};"
                    f"color:white;padding:2px 10px;border-radius:9px;font-size:11px;"
                    f"font-weight:600;margin-right:8px'>↩ 二轮回访</span>"
                    f"<b style='color:#3d2b1f'>{card.get('stakeholder', 'Unknown')}</b>"
                    f"<div style='color:#5c4a3a;font-size:13px;margin-top:6px'>"
                    f"{_escape_html(visit_summary)}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            continue

        # ── 初次访谈条目（完整知识卡片）──
        date = card.get("date") or "—"
        stakeholder = card.get("stakeholder", "Unknown")
        modules = card.get("affected_modules", [])
        priority = card.get("priority_score", 0)
        status = card.get("loop_status", "L0_Recorded")
        action = card.get("project_action", "")
        raw_feedback = card.get("feedback", "")
        question = card.get("initial_question", "")

        pure_feedback, summary = _parse_feedback(raw_feedback)

        status_color = STATUS_COLORS.get(status, C["pale_icy_blue"])
        status_label = STATUS_LABELS.get(status, status)

        # ── Extract Who / Why / Learned ──
        who_text = ""
        why_text = ""
        learned_text = ""

        if summary:
            who_text = summary.get("who", "")
            why_text = summary.get("why", "")
            learned_text = summary.get("learned", "")

        # Fallback: use initial_question for "why" if summary didn't capture it
        if not why_text and question:
            why_text = question

        # Fallback: use pure_feedback for "learned" if summary didn't capture it
        if not learned_text and pure_feedback:
            learned_text = pure_feedback

        # ── Timeline marker ──
        cols = st.columns([1, 24])
        with cols[0]:
            st.markdown(
                f"<div style='text-align:center;padding-top:18px'>"
                f"<div style='font-size:10px;font-weight:700;color:{status_color};"
                f"margin-bottom:4px'>{date}</div>"
                f"<div style='width:16px;height:16px;border-radius:50%;"
                f"background:{status_color};margin:0 auto;"
                f"box-shadow:0 0 10px {status_color}50'></div>"
                f"<div style='width:2px;height:40px;background:{C['pale_icy_blue']}60;"
                f"margin:0 auto;margin-top:4px'></div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with cols[1]:
            with st.expander(
                f"{date}  {stakeholder}",
                expanded=(i == 0),
            ):
                st.markdown(
                    _render_knowledge_card(
                        date=date,
                        stakeholder=stakeholder,
                        stakeholder_type=card.get("stakeholder_type", ""),
                        who_text=who_text,
                        why_text=why_text,
                        learned_text=learned_text,
                        action_text=action,
                        modules=modules,
                        status=status,
                        status_color=status_color,
                        status_label=status_label,
                        priority=priority,
                        evidence_count=len(card.get("evidence", [])),
                        evidence_strength=card.get("evidence_strength", 0),
                    ),
                    unsafe_allow_html=True,
                )

                # ── 成熟度雷达图 ──
                st.divider()
                st.markdown(
                    f"<span style='display:inline-block;background:{C['haze_blue']};"
                    f"color:white;padding:3px 12px;border-radius:10px;"
                    f"font-size:12px;font-weight:600'>"
                    f"🎯  HP 成熟度六维评估</span>",
                    unsafe_allow_html=True,
                )
                _render_maturity_radar(card, key_suffix=card.get("hp_id", str(i)))


# ═══════════════════════════════════════════════════════════════
#   页面 3: Loop Dashboard — 闭环状态面板
# ═══════════════════════════════════════════════════════════════


def page_loop_dashboard(cards: list[dict]) -> None:
    st.title("🔄 Loop Dashboard — 闭环状态面板")
    st.markdown("L0-L4 状态机追踪：每条反馈是否已完成 记录 → 提炼 → 行动 → 证据 → 回访。")

    status_order = ["L0_Recorded", "L1_Interpreted", "L2_Actioned",
                    "L3_Evidenced", "L4_Returned"]
    status_icons = ["📋", "🔍", "⚡", "✅", "🔁"]

    # 顶部统计卡片：浅底 + 彩色数字
    cols = st.columns(5)
    for col, status_key, icon in zip(cols, status_order, status_icons):
        count = sum(1 for c in cards if c.get("loop_status") == status_key)
        color = STATUS_COLORS[status_key]
        label = STATUS_LABELS[status_key]
        with col:
            st.markdown(
                f"<div style='text-align:center;padding:18px 8px;"
                f"background:#fff8e1;border-radius:10px;"
                f"border-top:3px solid {color}'>"
                f"<div style='font-size:30px;font-weight:800;color:{color}'>{count}</div>"
                f"<div style='font-size:11px;color:#5c4a3a;margin-top:2px'>{icon} {label}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.divider()

    for status_key in status_order:
        status_cards = [c for c in cards if c.get("loop_status") == status_key]
        if not status_cards:
            continue

        color = STATUS_COLORS[status_key]
        label = STATUS_LABELS[status_key]
        st.markdown(
            f"<span style='display:inline-block;border-left:4px solid {color};"
            f"padding:2px 12px;font-size:15px;font-weight:600;color:#3d2b1f'>"
            f"{label} ({len(status_cards)} 条)</span>",
            unsafe_allow_html=True,
        )
        st.markdown("")

        for card in sorted(status_cards, key=lambda c: c.get("priority_score", 0),
                           reverse=True):
            with st.container():
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.markdown(f"**{card.get('stakeholder', 'Unknown')}**")
                    st.caption(card.get("next_step", ""))
                with c2:
                    st.metric("优先级", f"{card.get('priority_score', 0):.3f}")
                with c3:
                    st.metric("证据", f"{len(card.get('evidence', []))} 项")
                st.progress(
                    card.get("evidence_strength", 0),
                    text=f"证据强度: {card.get('evidence_strength', 0):.2f}",
                )
            st.divider()


# ═══════════════════════════════════════════════════════════════
#   页面 4: Next Step — 下一步推荐
# ═══════════════════════════════════════════════════════════════


def page_next_step(cards: list[dict], data_dir: str = "") -> None:
    st.title("🎯 Next Step — 下一步回访建议")
    st.markdown(
        "自动识别未闭合循环，推荐下一步回访对象、材料和问题。"
        "优先级越高，越应尽快完成二轮反馈。"
    )

    ranked = sorted(cards, key=lambda c: c.get("priority_score", 0), reverse=True)

    for i, card in enumerate(ranked):
        priority = card.get("priority_score", 0)

        with st.container():
            # 用暖橙做左竖线强调，白底卡片
            st.markdown(
                f"<div style='background:#fff8e1;padding:20px 20px 14px;border-radius:10px;"
                f"border-left:4px solid {C['warm_orange']};margin-bottom:14px;'>",
                unsafe_allow_html=True,
            )

            c1, c2 = st.columns([3, 1])
            with c1:
                rank_icon = {0: "🥇", 1: "🥈", 2: "🥉"}.get(i, f"#{i+1}")
                st.markdown(f"### {rank_icon}  {card.get('stakeholder', 'Unknown')}")

                # 因子标签：只用雾蓝 + 暖橙两色，不再六色散打
                factors = card.get("priority_factors", {})
                factor_labels = {
                    "loop_gap":             "闭环缺口",
                    "cross_module_impact":  "跨模块影响",
                    "project_criticality":  "项目关键性",
                    "evidence_weakness":    "证据不足度",
                    "time_urgency":         "时间紧迫度",
                    "stakeholder_value":    "利益相关者价值",
                }
                tag_pairs = [
                    (C["haze_blue"], C["haze_blue"]),
                    (C["haze_blue"], C["haze_blue"]),
                    (C["warm_orange"], C["warm_orange"]),
                    (C["warm_orange"], C["warm_orange"]),
                    (C["haze_blue"], C["haze_blue"]),
                    (C["warm_orange"], C["warm_orange"]),
                ]
                tags = []
                for j, (k, v) in enumerate(factors.items()):
                    border_c, _ = tag_pairs[j % 6]
                    tags.append(
                        f"<span style='background:transparent;border:1px solid {border_c};"
                        f"color:#3d2b1f;padding:2px 10px;border-radius:12px;"
                        f"font-size:12px;margin:2px;display:inline-block'>"
                        f"{factor_labels.get(k, k)}: {v:.2f}</span>"
                    )
                st.markdown(" ".join(tags), unsafe_allow_html=True)

            with c2:
                st.metric("优先级", f"{priority:.3f}")
                st.caption(
                    STATUS_LABELS.get(card.get("loop_status", ''),
                                      card.get("loop_status", '')))

            st.markdown("---")

            # 推荐区：只用暖橙 / 雾蓝 / 薄荷绿三个 accent
            st.markdown(
                f"<span style='border-left:3px solid {C['warm_orange']};padding-left:8px;"
                f"font-weight:600;font-size:14px'>📌 建议行动</span>",
                unsafe_allow_html=True,
            )
            st.markdown(f"> {card.get('next_step', '待定')}")

            if card.get("suggested_materials"):
                st.markdown("")
                st.markdown(
                    f"<span style='border-left:3px solid {C['haze_blue']};padding-left:8px;"
                    f"font-weight:600;font-size:14px'>📦 建议材料</span>",
                    unsafe_allow_html=True,
                )
                for mat in card["suggested_materials"]:
                    st.markdown(f"- {mat}")

            if card.get("suggested_questions"):
                st.markdown("")
                st.markdown(
                    f"<span style='border-left:3px solid {C['mint_pea_green']};padding-left:8px;"
                    f"font-weight:600;font-size:14px'>❓ 建议回访问题</span>",
                    unsafe_allow_html=True,
                )
                for q in card["suggested_questions"]:
                    st.markdown(f"- {q}")

            st.markdown("</div>", unsafe_allow_html=True)

    # ── 敏感性分析展示区 ──
    if data_dir:
        sensitivity_path = Path(data_dir) / "sensitivity.json"
        if sensitivity_path.exists():
            try:
                sens = json.loads(sensitivity_path.read_text(encoding="utf-8"))
                with st.expander("📊 权重敏感性分析 — Spearman 秩相关稳健性检验", expanded=False):
                    # 结论 callout
                    if sens.get("min_rho", 0) >= 0.9999:
                        st.success(
                            f"✅ 全部 {len(sens.get('scenarios', []))} 个场景 "
                            f"Spearman **ρ = 1.0000**，排名完全不变。"
                            f"核心优先级结论对权重设定不敏感。"
                        )
                    elif sens.get("all_above_09"):
                        st.success(
                            f"✅ 全部 {len(sens.get('scenarios', []))} 个场景 "
                            f"Spearman **ρ > 0.9**（最低 {sens['min_rho']:.4f}），排序高度稳定。"
                        )
                    else:
                        st.warning(
                            f"⚠️ 最低 ρ = {sens['min_rho']:.4f}，部分场景排序有波动。"
                        )

                    # 结果表格
                    scenarios = sens.get("scenarios", [])
                    if scenarios:
                        import pandas as pd
                        df = pd.DataFrame([
                            {
                                "扰动因子": s["factor_label"],
                                "方向": s["delta"],
                                "原权重": f"{s['old_weight']:.4f}",
                                "新权重": f"{s['new_weight']:.4f}",
                                "Spearman ρ": f"{s['spearman_rho']:.4f}",
                            }
                            for s in scenarios
                        ])
                        st.dataframe(df, use_container_width=True, hide_index=True)

                    # 答辩陈述
                    if sens.get("defense_statement"):
                        st.markdown("##### 🎤 答辩陈述")
                        st.markdown(f"> {sens['defense_statement']}")

                    # 原始排名参考
                    orig_rank = sens.get("original_ranking", [])
                    if orig_rank:
                        st.markdown("##### 📋 基准排序")
                        st.caption(
                            " ".join(
                                f"#{r['rank']} {r['stakeholder'][:12]}"
                                for r in orig_rank
                            )
                        )

            except Exception:
                pass  # 加载失败则静默跳过


# ═══════════════════════════════════════════════════════════════
#   页面 5: Wiki Text — Wiki 文案
# ═══════════════════════════════════════════════════════════════


def page_wiki_text(data_dir: str) -> None:
    st.title("📝 Wiki 文案生成")
    st.markdown("自动生成的中英文 Wiki Human Practices 页面文案和答辩叙事。")

    data_path = Path(data_dir)

    tab1, tab2, tab3 = st.tabs(["🇨🇳 中文 Wiki", "🇬🇧 English Wiki", "🎤 答辩叙事"])

    wiki_cn = data_path / "wiki_cn.md"
    wiki_en = data_path / "wiki_en.md"
    defense = data_path / "defense_narrative.md"

    with tab1:
        if wiki_cn.exists():
            st.markdown(wiki_cn.read_text(encoding="utf-8"))
        else:
            st.info("中文 Wiki 文案尚未生成，请先运行 pipeline。")

    with tab2:
        if wiki_en.exists():
            st.markdown(wiki_en.read_text(encoding="utf-8"))
        else:
            st.info("英文 Wiki 文案尚未生成。")

    with tab3:
        if defense.exists():
            st.markdown(defense.read_text(encoding="utf-8"))
        else:
            st.info("答辩叙事尚未生成。")


# ═══════════════════════════════════════════════════════════════
#   辅助
# ═══════════════════════════════════════════════════════════════


def _clip(text: str, max_chars: int) -> str:
    text = " ".join(str(text).split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def _fallback_graph_svg(graph: dict) -> None:
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    importances: dict[str, float] = {}
    for n in nodes:
        imp = n.get("importance", n.get("score", 0.5)) or 0.5
        importances[n["id"]] = imp

    svg_parts = [
        '<svg width="100%" height="560" viewBox="0 0 1000 620"'
        ' xmlns="http://www.w3.org/2000/svg" style="background:#FFF2CC;border-radius:8px">',
        '<defs><marker id="arr" viewBox="0 0 10 10" refX="8" refY="5"'
        ' markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        '<path d="M0 0L10 5L0 10z" fill="#cedbe1"/></marker></defs>',
    ]

    # 简易布局：按 kind 分组放置
    pos: dict[str, tuple[int, int]] = {}
    kind_groups: dict[str, list[dict]] = {}
    for n in nodes:
        kind_groups.setdefault(n.get("kind", "Other"), []).append(n)
    group_order = ["Stakeholder", "Feedback", "HP", "Action", "Evidence", "Module", "NextStep"]
    for idx, kind in enumerate(group_order):
        group = kind_groups.pop(kind, [])
        for j, n in enumerate(group):
            x = 120 + idx * 140
            y = 60 + j * 70
            if y > 550:
                y = 60 + (j % 8) * 70
            pos[n["id"]] = (x, y)
    # 剩余种类
    for kind, group in kind_groups.items():
        for j, n in enumerate(group):
            pos[n["id"]] = (100, 60 + j * 70)

    # 边
    for edge in edges:
        src, tgt = edge.get("source"), edge.get("target")
        if src not in pos or tgt not in pos:
            continue
        x1, y1 = pos[src]
        x2, y2 = pos[tgt]
        imp = (importances.get(src, 0.5) + importances.get(tgt, 0.5)) / 2
        lw = 0.6 + imp * 3.0
        rel_colors = {
            "raised": "#79a3d1", "recorded_in": "#cedbe1", "led_to": "#f0a659",
            "affects": "#7aaa8a", "supported_by": "#e79c98", "requires": "#db6254",
            "related_via_module": "#e08e4a",
        }
        ec = rel_colors.get(edge.get("relation", ""), "#cedbe1")
        svg_parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"'
            f' stroke="{ec}" stroke-width="{lw:.1f}"'
            f' marker-end="url(#arr)" opacity="{0.35+imp*0.55:.2f}"/>'
        )

    # 节点
    for n in nodes:
        nid = n["id"]
        if nid not in pos:
            continue
        x, y = pos[nid]
        kind = n.get("kind", "")
        label = n.get("label", nid)
        base_color = NODE_COLORS.get(kind, C["pale_icy_blue"])
        # 图谱中所有 Module 节点统一着色
        if kind == "Module":
            base_color = MODULE_GRAPH_COLOR
        imp = importances.get(nid, 0.5)
        fade = (1.0 - imp) * 0.55
        color = _lighten(base_color, fade)
        lo, hi = NODE_SIZE_RANGES.get(kind, (8, 20))
        r = lo + imp * (hi - lo)
        svg_label = _escape_html(n.get("label", nid))
        if len(svg_label) > 120:
            svg_label = svg_label[:119].rstrip() + "…"
        sw = 0.8 + imp * 2.0
        svg_parts.append(
            f'<circle cx="{x}" cy="{y}" r="{r:.1f}" fill="{color}"'
            f' stroke="#3d2b1f" stroke-width="{sw:.1f}"'
            f' stroke-opacity="{0.2+imp*0.6:.2f}" opacity="0.92"/>'
        )
        svg_parts.append(
            f'<text x="{x}" y="{y+r+14:.0f}" font-size="{10+imp*4:.0f}"'
            f' text-anchor="middle" fill="#3d2b1f"'
            f' font-weight="{600 if imp>0.6 else 400}">{svg_label}</text>'
        )

    svg_parts.append("</svg>")
    st.markdown(
        f"*图谱包含 {len(nodes)} 个节点、{len(edges)} 条边。"
        f"安装 pyvis 可启用交互式图谱: `pip install pyvis`*\n\n"
        + "".join(svg_parts),
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════
#   主入口
# ═══════════════════════════════════════════════════════════════


def main() -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="hp_compass_output", help="数据输出目录")
    try:
        args, _ = parser.parse_known_args()
    except SystemExit:
        args = argparse.Namespace(data="hp_compass_output")

    # ── 侧边栏 ──
    with st.sidebar:
        # ── Logo 区域：AMPlify 团队 Logo，居中 ──
        # 查找顺序：数据目录 → 项目根 → 默认输出目录
        amplify_logo = next(
            (p for p in (
                Path(args.data) / "amplify_logo.png",
                Path("AMPLIFY.png"),
                Path("hp_compass_output") / "amplify_logo.png",
            ) if p.exists()),
            None,
        )

        if amplify_logo is not None:
            # Logo 区域：白底卡片，居中展示 AMPlify Logo
            st.markdown(
                "<div style='background:#ffffff;border-radius:15px;padding:20px 20px 14px;"
                "margin-bottom:12px;box-shadow:0 3px 12px rgba(0,0,0,0.10);"
                "border:1px solid #e8dcc8;text-align:center'>",
                unsafe_allow_html=True,
            )
            st.image(str(amplify_logo), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        st.markdown(
            f"<div style='text-align:center;padding:20px 8px 14px;"
            f"background:#fff8e1;border-radius:12px;"
            f"border:1px solid {C['pale_icy_blue']};margin-bottom:14px'>"
            f"<div style='font-size:38px'>🧭</div>"
            f"<div style='font-size:19px;font-weight:700;color:#3d2b1f;"
            f"margin-top:4px'>HP Compass</div>"
            f"<div style='font-size:11px;color:#5c4a3a;margin-top:2px'>"
            f"AMPlify · Human Practices 决策导航</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        st.divider()

        data_dir = st.text_input("📁 数据目录", value=args.data,
                                 help="运行 pipeline 后的输出目录")
        if not Path(data_dir).exists():
            st.warning(f"目录不存在: {data_dir}")

        st.divider()

        # ── LLM 解析层设置 ──
        st.markdown("### 🤖 大模型解析")
        use_llm = st.toggle(
            "使用大模型增强（DeepSeek）",
            value=False,
            key="llm_toggle",
            help="开启后用大模型做文本解析，数学模型负责决策计算。关闭时走关键词规则模式。",
        )
        api_key = ""
        if use_llm:
            api_key = st.text_input(
                "🔑 DeepSeek API Key",
                type="password",
                value=st.session_state.get("ds_api_key", ""),
                key="ds_api_key_input",
                help="仅保存在当前会话内存中，不写入任何文件。",
                placeholder="sk-...",
            )
            if api_key:
                st.session_state["ds_api_key"] = api_key
        if not use_llm:
            st.caption("🟡 规则模式：关键词匹配（无需 API Key）")
        elif not api_key:
            st.caption("🟡 未提供 Key，使用规则模式")

        st.divider()

        # ── 文件上传 ──
        st.markdown("### 📤 上传新记录")

        uploaded_files = st.file_uploader(
            "选择 .docx 访谈文件",
            type=["docx"],
            accept_multiple_files=True,
            key="hp_docx_uploader",
            label_visibility="collapsed",
        )

        # 文件一旦上传就暂存到 session_state，防止按钮触发 rerun 时丢失
        if uploaded_files:
            st.session_state["pending_uploads"] = uploaded_files

        has_pending = "pending_uploads" in st.session_state and bool(st.session_state["pending_uploads"])

        col_up, col_re = st.columns(2)
        with col_up:
            upload_clicked = st.button(
                "⬆️ 处理上传",
                use_container_width=True,
                disabled=not has_pending,
            )
        with col_re:
            rerun_clicked = st.button(
                "🔄 重新分析全部",
                use_container_width=True,
            )

        HP_RECORD_DIR = Path("hp record")

        def _mode_label() -> str:
            return "LLM 解析模式" if (use_llm and api_key) else "规则模式"

        def _load_existing_cards(data_dir: str) -> list[HPCard]:
            """从 hp_cards.json 读取现有卡片为 HPCard 对象。"""
            cards_file = Path(data_dir) / "hp_cards.json"
            if not cards_file.exists():
                return []
            raw = json.loads(cards_file.read_text(encoding="utf-8"))
            fields = set(HPCard.__dataclass_fields__)
            return [HPCard(**{k: v for k, v in item.items() if k in fields}) for item in raw]

        if upload_clicked and has_pending:
            HP_RECORD_DIR.mkdir(exist_ok=True)
            files_to_process = st.session_state["pending_uploads"]
            saved: list[Path] = []
            for uf in files_to_process:
                if not uf.name.endswith(".docx"):
                    continue
                dest = HP_RECORD_DIR / uf.name
                dest.write_bytes(uf.getvalue())
                saved.append(dest)

            if saved:
                mode = _mode_label()
                with st.spinner(f"正在用{mode}分析 {len(saved)} 个新文件..."):
                    try:
                        if use_llm and api_key:
                            existing = _load_existing_cards(data_dir)
                            run_llm_incremental(saved, data_dir, api_key, existing)
                        else:
                            run_pipeline(str(HP_RECORD_DIR), data_dir)
                        st.session_state["pipeline_ok"] = True
                        st.session_state["pipeline_msg"] = (
                            f"已用{mode}处理 {len(saved)} 个文件"
                        )
                    except Exception as e:
                        st.session_state["pipeline_ok"] = False
                        st.session_state["pipeline_msg"] = str(e)
                del st.session_state["pending_uploads"]
                st.rerun()

        if rerun_clicked:
            if HP_RECORD_DIR.exists() and list(HP_RECORD_DIR.glob("*.docx")):
                mode = _mode_label()
                with st.spinner(f"正在用{mode}重新分析全部记录..."):
                    try:
                        if use_llm and api_key:
                            run_pipeline(
                                str(HP_RECORD_DIR), data_dir,
                                mode="llm", api_key=api_key,
                            )
                        else:
                            run_pipeline(str(HP_RECORD_DIR), data_dir)
                        st.session_state["pipeline_ok"] = True
                        st.session_state["pipeline_msg"] = f"已用{mode}重新分析完成"
                    except Exception as e:
                        st.session_state["pipeline_ok"] = False
                        st.session_state["pipeline_msg"] = str(e)
                st.rerun()
            else:
                st.warning("hp record 目录为空，请先上传文件")

        # 管道执行结果反馈（显示一次后自动清除）
        if "pipeline_msg" in st.session_state:
            if st.session_state.get("pipeline_ok", False):
                st.success(st.session_state["pipeline_msg"])
            else:
                st.error(f"处理失败: {st.session_state['pipeline_msg']}")
            if "pipeline_shown" in st.session_state:
                del st.session_state["pipeline_msg"]
                del st.session_state["pipeline_ok"]
                del st.session_state["pipeline_shown"]
            else:
                st.session_state["pipeline_shown"] = True

        st.divider()

        page = st.radio(
            "页面导航",
            ["🧭 HP Map", "📅 Timeline", "🔄 Loop Dashboard",
             "🎯 Next Step", "📝 Wiki Text"],
            label_visibility="collapsed",
        )

        st.divider()

        cache_ver = str((Path(data_dir) / "hp_cards.json").stat().st_mtime) if (Path(data_dir) / "hp_cards.json").exists() else ""
        data = load_data(data_dir, _cache_version=cache_ver)
        cards = data.get("cards", [])
        returned = sum(1 for c in cards if c.get("loop_level") == 4)
        high_priority = sum(1 for c in cards if c.get("priority_score", 0) >= 0.8)

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("📋", len(cards))
        with col_b:
            st.metric("🔁", returned)
        with col_c:
            st.metric("🔥", high_priority)
        st.caption(
            f"HP 循环 {len(cards)} · L4 回访 {returned} · 高优先级 {high_priority}"
        )

        st.divider()
        st.caption(
            f"<span style='color:{C['haze_blue']}'>AMPlify 2026</span> · "
            f"<span style='color:{C['retro_brick_red']}'>iGEM Conservation</span>",
            unsafe_allow_html=True,
        )

    # ── 页面路由 ──
    cache_ver = str((Path(data_dir) / "hp_cards.json").stat().st_mtime) if (Path(data_dir) / "hp_cards.json").exists() else ""
    data = load_data(data_dir, _cache_version=cache_ver)
    cards = data["cards"]
    graph = data.get("graph")
    analytics = data.get("analytics")

    if page == "🧭 HP Map":
        page_hp_map(cards, graph or {"nodes": [], "edges": []}, analytics)
    elif page == "📅 Timeline":
        page_timeline(cards)
    elif page == "🔄 Loop Dashboard":
        page_loop_dashboard(cards)
    elif page == "🎯 Next Step":
        page_next_step(cards, data_dir)
    elif page == "📝 Wiki Text":
        page_wiki_text(data_dir)


if __name__ == "__main__":
    main()
