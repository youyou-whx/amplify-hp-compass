"""HP Compass 知识图谱构建模块

使用 NetworkX 构建 Stakeholder-Feedback-Action-Evidence 知识图谱，
并提供图分析：中心性、PageRank、社区发现等。

设计要点：
- 文本自动摘要提炼（_summarize / LLM 精炼摘要）
- 主题去重（_fingerprint + theme registry），同类反馈/行动合并节点
- 三层信息层级（L1战略→L2执行→L3验证），节点大小/深浅随层级
- 跨循环连线：共享模块的 Feedback 节点相互连接
"""

from __future__ import annotations

import re
from typing import Any

import networkx as nx

from .schema import GraphData, HPCard


# ═══════════════════════════════════════════════════════════════
#   HP 标签清理
# ═══════════════════════════════════════════════════════════════


def _friendly_hp_label(hp_id: str) -> str:
    """将原始 hp_id 转为统一可读标签："XX HP小循环"。

    策略：找到 hp_id 中间的 _HP 标记，将其及之后所有内容替换为" HP小循环"。
    无论原文件如何命名，新老 HP 输出标签永远一致。
    """
    s = hp_id
    s = re.sub(r'^HP_\d{8}_', '', s)
    s = re.sub(r'_HP.+$', '', s)
    s = s.replace('_', ' ')
    return s.strip() + ' HP小循环'


# ═══════════════════════════════════════════════════════════════
#   信息层级定义
#   L1 战略层 — 核心决策与方向
#   L2 执行层 — 开发与行动
#   L3 验证层 — 证据与影响领域
#   层级越高 → 节点越大、颜色越深、边框越粗
# ═══════════════════════════════════════════════════════════════

NODE_LEVELS = {
    "HP":          1,   # L1 战略 — 每一次 HP 循环代表一次方向校准
    "Stakeholder": 1,   # L1 战略 — 利益相关者是决策来源
    "Feedback":    2,   # L2 执行 — 反馈驱动行动
    "Action":      2,   # L2 执行 — 行动改变项目
    "Module":      3,   # L3 验证 — 影响领域
    "Evidence":    3,   # L3 验证 — 证据支撑
    "NextStep":    3,   # L3 验证 — 后续步骤
}

LEVEL_LABELS = {1: "战略层", 2: "执行层", 3: "验证层"}


# ═══════════════════════════════════════════════════════════════
#   文本摘要引擎
# ═══════════════════════════════════════════════════════════════

# 高权重词 — 命中的句子优先保留
STRONG_TERMS = [
    # 方向性
    "改变", "修改", "调整", "转向", "推进", "明确", "关键", "核心", "直接",
    "不再", "加入", "引入", "构建", "确立", "决定", "确认",
    # 证据性
    "验证", "证据", "边界", "实验", "数据",
    # 影响性
    "影响", "重要", "必须", "需要", "要求", "约束",
    # 否定/纠正
    "不能", "不应", "无法", "缺乏",
]

# 项目实体词 — 命中加分，帮助保留具体内容
ENTITY_TERMS = [
    "AMPlify", "ESM", "TAM-Flow", "Oracle", "RAFT", "PDES",
    "MIC", "CCK-8", "TEM", "Field Score", "Evidence Matrix",
    "Risk Boundary Panel", "Environmental Degradation Panel",
    "One Health", "LoRA", "DiT", "RMSD", "RMSF", "ARG",
    "乳腺炎", "乳房炎", "耐药", "抗菌肽", "抗生素",
    "西安动物医院", "钱勋", "罗自卫", "赵天意", "刘军", "聂桓",
    "猫咪驿站", "除张村", "诚威", "散养",
]


def _summarize(text: str, max_chars: int = 100) -> str:
    """从原始文本中提取最关键的 1-3 个句子，生成精简摘要。

    算法：
    1. 按句号/问号/感叹号分句
    2. 每句按强词命中数 + 实体词命中数打分
    3. 取 Top-3 高分句，拼接后截断至 max_chars
    4. 若无有效句，退回 compact 截断
    """
    if not text:
        return ""

    # 分句
    raw = re.split(r'(?<=[。！？!?\n])\s*', text)
    sentences = [s.strip() for s in raw if len(s.strip()) >= 5]

    if not sentences:
        return compact(text, max_chars)

    # 去重（相似句只保留一个）
    unique: list[str] = []
    for s in sentences:
        if not any(_jaccard_words(s, u) > 0.7 for u in unique):
            unique.append(s)

    # 打分
    scored = []
    for s in unique:
        strong = sum(1 for kw in STRONG_TERMS if kw in s)
        entity = sum(1 for kw in ENTITY_TERMS if kw in s)
        score = strong * 3 + entity * 2
        scored.append((score, s))

    scored.sort(key=lambda x: x[0], reverse=True)

    # 取前 N 句，凑满 max_chars
    result = ""
    for _, s in scored:
        candidate = result + (" " if result else "") + s
        if len(candidate) > max_chars:
            break
        result = candidate

    if result:
        return result.strip()

    return compact(text, max_chars)


# ═══════════════════════════════════════════════════════════════
#   主题指纹 & 去重
# ═══════════════════════════════════════════════════════════════

# 12 个项目主题关键词组 — 用于给 Feedback/Action 节点归类
THEME_PATTERNS: dict[str, list[str]] = {
    "临床场景定义":    ["临床", "动物医院", "治疗", "诊断", "场景", "宠物", "猫", "狗", "皮肤", "耳道", "泌尿"],
    "抗生素与耐药性":  ["耐药", "ARG", "抗性基因", "抗生素", "抗药", "选择压力"],
    "环境与OneHealth": ["环境", "生态", "One Health", "粪污", "径流", "气溶胶", "水体"],
    "AI模型与算法":    ["ESM", "模型", "TAM-Flow", "Oracle", "RAFT", "算法", "预测", "LoRA", "DiT", "判别器", "训练"],
    "实验验证体系":    ["MIC", "溶血", "CCK", "TEM", "湿实验", "验证", "合成", "质谱", "MD", "分子动力学", "RMSD", "RMSF"],
    "安全与毒性边界":  ["安全", "毒性", "细胞毒性", "边界", "风险", "PDES", "Risk Boundary"],
    "养殖场景定义":    ["羊", "养殖", "乳腺炎", "乳房炎", "生产动物", "散养", "羊场", "养殖户"],
    "公众教育与传播":  ["公众", "教育", "猫咪", "科普", "认知", "驿站"],
    "Wiki与叙事建设":  ["Wiki", "叙事", "交流", "iGEM", "答辩", "海报", "展示"],
    "实施与落地路径":  ["实施", "落地", "成本", "商业化", "产品", "推广", "信任"],
    "工程化与软件":    ["软件", "面板", "Software", "平台", "工具", "管线", "pipeline"],
    "问题定义与校准":  ["Problem Definition", "问题定义", "方向", "定位", "重新", "校正"],
}


def _fingerprint(text: str) -> tuple[str, ...]:
    """返回文本的主题指纹 — 命中的主题名元组。"""
    themes = []
    for theme, keywords in THEME_PATTERNS.items():
        if any(kw in text for kw in keywords):
            themes.append(theme)
    return tuple(themes[:3])


def _theme_label(text: str, kind: str, hp_label: str) -> str:
    """为去重后的主题节点生成简短标签。

    格式：「主题名」+ 首个 HP 简称
    例如：「AI模型与算法 · 赵天意老师访谈」
    """
    fp = _fingerprint(text)
    if fp:
        short_hp = hp_label.replace(" HP小循环", "")
        if len(short_hp) > 12:
            short_hp = short_hp[:10] + "…"
        return fp[0] + " · " + short_hp
    return compact(text, 40)


def _jaccard_words(a: str, b: str) -> float:
    """两个字符串的词级 Jaccard 相似度。"""
    set_a = set(a)
    set_b = set(b)
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


# ═══════════════════════════════════════════════════════════════
#   核心图谱构建
# ═══════════════════════════════════════════════════════════════


def build_graph(cards: list[HPCard]) -> GraphData:
    """从 HP 卡片列表构建知识图谱。

    1. 文本摘要 — Feedback/Action 节点使用 LLM 精炼摘要或 _summarize 提炼关键句
    2. 主题去重 — 同主题 Feedback/Action 复用节点 + 增大 + 加边
    3. 三层信息层级 — 每节点标记 level∈{1,2,3}
    4. 跨循环连线 — 共享模块的 Feedback 节点互连
    """
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    # ── 主题注册表（跨 HP 循环共享） ──
    #   theme_node_map: theme_name → node_id
    #   theme_fingerprints: node_id → (theme1, theme2, ...)
    theme_node_map: dict[str, str] = {}
    theme_fingerprints: dict[str, tuple[str, ...]] = {}

    # ── 模块→Feedback 反向索引（用于跨循环连线） ──
    module_feedbacks: dict[str, list[str]] = {}

    def _add_node(node_id: str, label: str, kind: str, **extra: Any) -> dict[str, Any]:
        """添加或更新节点。已存在 → 更新 score/ref_count/importance。"""
        if node_id in nodes:
            existing = nodes[node_id]
            existing["ref_count"] = existing.get("ref_count", 1) + 1
            if "score" in extra:
                existing["score"] = max(existing.get("score", 0), extra["score"])
            return existing
        level = NODE_LEVELS.get(kind, 3)
        nodes[node_id] = {
            "id": node_id, "label": label, "kind": kind,
            "level": level, "ref_count": 1, **extra,
        }
        return nodes[node_id]

    def _add_edge(source: str, target: str, relation: str) -> None:
        key = (source, target, relation)
        if not any(
            e["source"] == source and e["target"] == target and e["relation"] == relation
            for e in edges
        ):
            edges.append({"source": source, "target": target, "relation": relation})

    def _resolve_feedback_node(card: HPCard) -> str:
        """为 feedback 文本找或建主题节点。

        先去重检查：若与已有主题指纹 Jaccard ≥ 0.25，则复用该节点。
        否则新建主题节点。
        """
        text = card.feedback
        fp = _fingerprint(text)
        hp_label = _friendly_hp_label(card.hp_id)

        if fp:
            fp_set = set(fp)
            primary = fp[0]

            # 仅当 primary theme 完全匹配时才考虑合并
            if primary in theme_node_map:
                node_id = theme_node_map[primary]
                existing_fp = set(theme_fingerprints.get(node_id, ()))
                overlap = len(fp_set & existing_fp) / max(len(fp_set | existing_fp), 1) if existing_fp else 0
                # 合并条件：共享 primary theme + 整体 overlap ≥ 0.40
                if overlap >= 0.40:
                    node = _add_node(node_id, "", "Feedback",
                                     score=card.priority_score)
                    existing_label = node.get("label", "")
                    if hp_label not in existing_label and node.get("ref_count", 1) <= 3:
                        sources = existing_label.split(" | ") if existing_label else []
                        sources.append(hp_label)
                        node["label"] = " | ".join(sources[-3:])
                    return node_id

            # 新建主题节点
            theme_name = primary
            node_id = f"theme_fb:{theme_name}"
            theme_node_map[theme_name] = node_id
            theme_fingerprints[node_id] = fp
            _add_node(node_id, _theme_label(text, "Feedback", hp_label),
                      "Feedback", score=card.priority_score,
                      themes=list(fp))
            return node_id

        # 无主题指纹 → per-HP 节点
        # LLM 模式优先用大模型精炼的一句话摘要
        node_id = f"feedback:{card.hp_id}"
        label = (
            getattr(card, "llm_feedback_summary", "") or _summarize(text, 90)
        )
        _add_node(node_id, label, "Feedback", score=card.priority_score)
        return node_id

    def _resolve_action_node(card: HPCard) -> str:
        """与 _resolve_feedback_node 对称，处理 action 文本。"""
        text = card.project_action
        fp = _fingerprint(text)
        hp_label = _friendly_hp_label(card.hp_id)

        if fp:
            fp_set = set(fp)
            primary = fp[0] + "_act"

            if primary in theme_node_map:
                node_id = theme_node_map[primary]
                existing_fp = set(theme_fingerprints.get(node_id, ()))
                overlap = len(fp_set & existing_fp) / max(len(fp_set | existing_fp), 1) if existing_fp else 0
                # Action 合并更保守：primary match + overlap ≥ 0.50
                if overlap >= 0.50:
                    node = _add_node(node_id, "", "Action",
                                     score=card.priority_score)
                    existing_label = node.get("label", "")
                    if hp_label not in existing_label and node.get("ref_count", 1) <= 3:
                        sources = existing_label.split(" | ") if existing_label else []
                        sources.append(hp_label)
                        node["label"] = " | ".join(sources[-3:])
                    return node_id

            node_id = f"theme_act:{primary}"
            theme_node_map[primary] = node_id
            theme_fingerprints[node_id] = fp
            _add_node(node_id, _theme_label(text, "Action", hp_label),
                      "Action", score=card.priority_score,
                      themes=list(fp))
            return node_id

        node_id = f"action:{card.hp_id}"
        label = (
            getattr(card, "llm_action_summary", "") or _summarize(text, 90)
        )
        _add_node(node_id, label, "Action", score=card.priority_score)
        return node_id

    # ── 主循环：逐卡片建图 ──
    for card in cards:
        hp_node = f"hp:{card.hp_id}"
        stakeholder_node = f"stakeholder:{card.stakeholder}"
        feedback_node = _resolve_feedback_node(card)
        action_node = _resolve_action_node(card)

        # HP 节点
        _add_node(hp_node, _friendly_hp_label(card.hp_id), "HP",
                  score=card.priority_score, status=card.loop_status)

        # Stakeholder 节点
        _add_node(stakeholder_node, card.stakeholder, "Stakeholder",
                  stakeholder_type=card.stakeholder_type)

        # 核心边
        _add_edge(stakeholder_node, feedback_node, "raised")
        _add_edge(feedback_node, hp_node, "recorded_in")
        _add_edge(feedback_node, action_node, "led_to")

        # Module 节点 + 反向索引
        for module in card.affected_modules:
            module_node = f"module:{module}"
            _add_node(module_node, module, "Module")
            _add_edge(feedback_node, module_node, "affects")
            module_feedbacks.setdefault(module, []).append(feedback_node)

        # Evidence 节点
        for evidence in card.evidence:
            evidence_node = f"evidence:{evidence}"
            _add_node(evidence_node, evidence, "Evidence")
            _add_edge(action_node, evidence_node, "supported_by")

        # NextStep
        if card.loop_level < 4:
            next_node = f"next:{card.hp_id}"
            _add_node(next_node, compact(card.next_step, 120), "NextStep")
            _add_edge(action_node, next_node, "requires")

    # ── 跨循环连线：共享同一模块的 Feedback 节点互连 ──
    for module, fb_list in module_feedbacks.items():
        unique_fbs = list(dict.fromkeys(fb_list))  # 去重
        if len(unique_fbs) >= 2:
            for i in range(len(unique_fbs)):
                for j in range(i + 1, len(unique_fbs)):
                    _add_edge(unique_fbs[i], unique_fbs[j], "related_via_module")

    return GraphData(nodes=list(nodes.values()), edges=edges)


# ═══════════════════════════════════════════════════════════════
#   NetworkX 图分析
# ═══════════════════════════════════════════════════════════════


def to_networkx(graph_data: GraphData) -> nx.DiGraph:
    """将 GraphData 转换为 NetworkX 有向图，用于图分析"""
    G = nx.DiGraph()
    for node in graph_data.nodes:
        G.add_node(node["id"], **{k: v for k, v in node.items() if k != "id"})
    for edge in graph_data.edges:
        G.add_edge(edge["source"], edge["target"], relation=edge["relation"])
    return G


def compute_centrality(G: nx.DiGraph) -> dict[str, dict[str, float]]:
    if G.number_of_nodes() == 0:
        return {}
    degree = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G) if G.number_of_nodes() > 1 else {}
    result: dict[str, dict[str, float]] = {}
    for node_id in G.nodes():
        result[node_id] = {
            "degree": round(degree.get(node_id, 0), 4),
            "betweenness": round(betweenness.get(node_id, 0), 4),
        }
    return result


def compute_pagerank(G: nx.DiGraph, alpha: float = 0.85) -> dict[str, float]:
    if G.number_of_nodes() == 0:
        return {}
    pr = nx.pagerank(G, alpha=alpha)
    return {node_id: round(score, 4) for node_id, score in pr.items()}


def compute_community(G: nx.DiGraph) -> dict[str, int]:
    if G.number_of_nodes() < 3:
        return {node_id: 0 for node_id in G.nodes()}
    undirected = G.to_undirected()
    try:
        from networkx.algorithms.community import greedy_modularity_communities
        communities = greedy_modularity_communities(undirected)
        result: dict[str, int] = {}
        for comm_id, comm_set in enumerate(communities):
            for node_id in comm_set:
                result[node_id] = comm_id
        return result
    except ImportError:
        comps = list(nx.connected_components(undirected))
        result = {}
        for comp_id, comp_set in enumerate(comps):
            for node_id in comp_set:
                result[node_id] = comp_id
        return result


def top_stakeholders(G: nx.DiGraph, top_n: int = 5) -> list[dict[str, Any]]:
    pagerank = compute_pagerank(G)
    centrality = compute_centrality(G)
    stakeholder_nodes = [
        node_id for node_id, attr in G.nodes(data=True) if attr.get("kind") == "Stakeholder"
    ]
    scored = []
    for node_id in stakeholder_nodes:
        pr = pagerank.get(node_id, 0)
        deg = centrality.get(node_id, {}).get("degree", 0)
        between = centrality.get(node_id, {}).get("betweenness", 0)
        composite = round(0.5 * pr + 0.3 * deg + 0.2 * between, 4)
        scored.append({
            "node_id": node_id,
            "label": G.nodes[node_id].get("label", ""),
            "stakeholder_type": G.nodes[node_id].get("stakeholder_type", ""),
            "pagerank": pr,
            "degree_centrality": deg,
            "betweenness_centrality": between,
            "composite_score": composite,
        })
    scored.sort(key=lambda x: x["composite_score"], reverse=True)
    return scored[:top_n]


def module_impact_ranking(G: nx.DiGraph) -> list[dict[str, Any]]:
    module_nodes = [
        node_id for node_id, attr in G.nodes(data=True) if attr.get("kind") == "Module"
    ]
    ranked = []
    for node_id in module_nodes:
        in_deg = G.in_degree(node_id) if G.is_directed() else G.degree(node_id)
        ranked.append({
            "module": G.nodes[node_id].get("label", node_id),
            "hp_feedback_count": in_deg,
        })
    ranked.sort(key=lambda x: x["hp_feedback_count"], reverse=True)
    return ranked


def build_analytics_report(cards: list[HPCard], graph_data: GraphData) -> dict[str, Any]:
    G = to_networkx(graph_data)
    report: dict[str, Any] = {
        "graph_stats": {
            "total_nodes": G.number_of_nodes(),
            "total_edges": G.number_of_edges(),
            "density": round(nx.density(G), 4),
        },
        "top_stakeholders": top_stakeholders_hybrid(G, cards),
        "module_impact": module_impact_ranking(G),
    }
    kind_counts: dict[str, int] = {}
    for _, attr in G.nodes(data=True):
        kind = attr.get("kind", "Unknown")
        kind_counts[kind] = kind_counts.get(kind, 0) + 1
    report["node_type_counts"] = kind_counts
    return report


def top_stakeholders_hybrid(G: nx.DiGraph, cards: list[HPCard], top_n: int = 5) -> list[dict[str, Any]]:
    card_map: dict[str, HPCard] = {}
    for card in cards:
        card_map[card.stakeholder] = card

    pagerank = compute_pagerank(G)
    centrality = compute_centrality(G)
    stakeholder_nodes = [
        node_id for node_id, attr in G.nodes(data=True) if attr.get("kind") == "Stakeholder"
    ]
    if not stakeholder_nodes:
        return []

    max_modules = max((len(card.affected_modules) for card in cards), default=1)
    max_pr = max((pagerank.get(n, 0) for n in stakeholder_nodes), default=0.001)
    max_deg = max((centrality.get(n, {}).get("degree", 0) for n in stakeholder_nodes), default=0.001)

    scored = []
    for node_id in stakeholder_nodes:
        label = G.nodes[node_id].get("label", node_id)
        stype = G.nodes[node_id].get("stakeholder_type", "")
        card = card_map.get(label)
        pr_norm = pagerank.get(node_id, 0) / max_pr if max_pr else 0
        deg_norm = centrality.get(node_id, {}).get("degree", 0) / max_deg if max_deg else 0
        between_norm = centrality.get(node_id, {}).get("betweenness", 0) / max_deg if max_deg else 0

        if card is not None:
            module_count = len(card.affected_modules)
            module_norm = module_count / max_modules if max_modules else 1
            priority = card.priority_score
            evidence_strength = card.evidence_strength
        else:
            module_norm = 0.5
            priority = 0.5
            evidence_strength = 0.5

        composite = round(
            0.30 * (0.4 * pr_norm + 0.35 * deg_norm + 0.25 * between_norm)
            + 0.35 * priority
            + 0.25 * module_norm
            + 0.10 * evidence_strength,
            4,
        )
        scored.append({
            "node_id": node_id, "label": label, "stakeholder_type": stype,
            "pagerank": round(pagerank.get(node_id, 0), 4),
            "degree_centrality": round(centrality.get(node_id, {}).get("degree", 0), 4),
            "betweenness_centrality": round(centrality.get(node_id, {}).get("betweenness", 0), 4),
            "composite_score": composite,
            "hp_priority": priority if card is not None else 0.5,
            "modules_affected": len(card.affected_modules) if card is not None else 0,
        })

    scored.sort(key=lambda x: x["composite_score"], reverse=True)
    return scored[:top_n]


# ═══════════════════════════════════════════════════════════════
#   工具函数
# ═══════════════════════════════════════════════════════════════


def compact(text: str, limit: int) -> str:
    """压缩文本到指定长度"""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
