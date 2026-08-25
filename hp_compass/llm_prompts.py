"""HP Compass — LLM 提示词模块"""

from __future__ import annotations

# ═══════════════════════════════════════════════════════════════
#  公共部分
# ═══════════════════════════════════════════════════════════════

# 四梯度标度 —— LLM 输出定性等级，代码映射为代表性数值（见 llm_annotator）
GRADE_VALUES: dict[str, float] = {
    "无": 0.0,
    "弱": 0.35,
    "中": 0.7,
    "强": 1.0,
}

# 九大项目模块
MODULES = [
    "Safety", "Model", "Implementation", "Material",
    "Problem Definition", "Environment", "Software",
    "Education", "Social Media",
]

# 六个成熟度文本信号（对应 maturity.py 中由关键词密度计算的信号）
MATURITY_TEXT_SIGNALS = [
    "design_reflection",   # 设计反思充分度
    "context_scene",       # 真实场景探索深度
    "risk",                # 风险识别充分度
    "mitigation",          # 缓解措施充分度
    "limitation",          # 局限性讨论充分度
    "boundary",            # 边界语言明确度
]

SYSTEM_PROMPT = (
    "你是 AMPlify（iGEM 2026 Conservation 项目）的 Human Practices 分析助手。"
    "AMPlify 用 AI 设计抗菌肽，用于动物健康、抗生素减量与 One Health 生态保护。"
    "你的任务是从访谈记录中提取结构化信息并给出四梯度判断。"
    "只输出 JSON，不要输出任何解释或额外文本。"
)

# ═══════════════════════════════════════════════════════════════
#  调用 1：Φ₁ 结构化提取 + Φ₂ 九模块四梯度
# ═══════════════════════════════════════════════════════════════

CALL1_SYSTEM = SYSTEM_PROMPT

CALL1_USER_TEMPLATE = """下面是 AMPlify 团队的一轮 Human Practices 访谈记录。请通读全文，把里面的关键信息直接整理出来。

一次访谈记录通常包含这些信息：什么时候聊的、和谁聊的、团队带着什么问题去、对方给了什么建议、团队后来改了什么。请从文本里直接找出：

- date：这次访谈的日期（YYYY-MM-DD 格式，找不到就写 null）
- stakeholder：受访对象，机构加身份写完整
- stakeholder_type：对方属于哪类人，从下面这些里挑最贴切的一个：
  兽医临床 stakeholder / 动物健康、家畜专家 / AI、生物大数据专家 /
  湿实验、合成生物学专家 / 环境微生物、ARG 专家 /
  养殖端 stakeholder / 公众教育 stakeholder / iGEM、Wiki 交流 stakeholder
- initial_question：团队做这轮访谈是想弄清楚什么
- feedback：对方给出的核心信息（保留具体的事实和判断，不要泛泛而谈）
- project_action：团队根据这次交流实际做了什么改动
- evidence：这轮交流里实际出现过的证据（比如 MIC、溶血、CCK-8、TEM、分子动力学、理化性质、软件面板、报告、访谈记录等，只写确实提到的）
- returned：是否已经完成二轮确认（只是计划将来回访的不算）
- has_action：团队是否已经做出了实际的项目修改（明确写"我们做了/修改了/加入了"才算；只是计划或讨论不算）
- has_evidence：是否有实质证据支撑（MIC、溶血、CCK-8、TEM、软件面板、报告等实际产物；提及"计划做"的不算）
- is_extension_of：如果这次访谈是下面"已有记录"里某一条的后续回访，填那一条记录的编号；否则填 null。注意：只有受访对象是同一人/同一机构、且内容明确提到带着上一轮修改后的材料回去确认的才算回访；不同的受访对象即使主题相近，也是独立的访谈

另外，请判断这轮访谈对下面 9 个项目模块的关联程度，用四个等级：
"无"=不相关；"弱"=略微提到；"中"=明确相关；"强"=深度影响。
按语义理解判断，不要机械地数关键词。

模块：Safety、Model、Implementation、Material、Problem Definition、Environment、Software、Education、Social Media

{existing_records}

输出 JSON（字段名保持英文）：
{{
  "date": "...",
  "stakeholder": "...",
  "stakeholder_type": "...",
  "initial_question": "...",
  "feedback": "...",
  "project_action": "...",
  "evidence": ["...", "..."],
  "returned": false,
  "has_action": false,
  "has_evidence": false,
  "is_extension_of": null,
  "module_grades": {{
    "Safety": "无|弱|中|强",
    "Model": "...",
    "Implementation": "...",
    "Material": "...",
    "Problem Definition": "...",
    "Environment": "...",
    "Software": "...",
    "Education": "...",
    "Social Media": "..."
  }}
}}

访谈记录全文：
{text}"""

EXISTING_RECORDS_TEMPLATE = """已有记录（判断 is_extension_of 时参考，编号+访谈日期+受访对象+文件名）：
{records}
"""


def build_call1_messages(text: str, existing_records: list[dict[str, str]] | None = None) -> list[dict[str, str]]:
    if existing_records:
        lines = "\n".join(
            f"- [{rec['id']}] {rec.get('date', '日期未知')} · {rec['stakeholder']} · {rec['file']}"
            for rec in existing_records
        )
        records_section = EXISTING_RECORDS_TEMPLATE.format(records=lines)
    else:
        records_section = ""
    return [
        {"role": "system", "content": CALL1_SYSTEM},
        {"role": "user", "content": CALL1_USER_TEMPLATE.format(text=text, existing_records=records_section)},
    ]

# ═══════════════════════════════════════════════════════════════
#  调用 2：Φ₅ 成熟度文本信号四梯度
# ═══════════════════════════════════════════════════════════════

CALL2_SYSTEM = SYSTEM_PROMPT

CALL2_USER_TEMPLATE = """这是一条 Human Practices 访谈的已提取信息。请从语义层面判断以下 6 个维度，用四梯度评分：
"无"=完全没有；"弱"=稍有体现；"中"=明确体现；"强"=深入且充分。

1. design_reflection —— 团队对设计决策的反思深度（是否重新审视设计、迭代修改，而非简单记录）
2. context_scene —— 对真实应用场景的探索深度（临床/养殖/环境等真实场景，而非纯实验室视角）
3. risk —— 对潜在负面影响和风险的识别充分度（安全性、毒性、残留、环境风险等）
4. mitigation —— 针对风险的缓解措施充分度（是否提出控制、边界、监测等具体措施）
5. limitation —— 对方法局限性的坦诚程度（是否承认证据边界、不能替代、未来需验证等）
6. boundary —— 应用边界语言的明确度（是否清晰划定了当前能做什么、不能声称什么）

依据语义判断，不要数关键词出现次数。

已提取信息：
- 利益相关者：{stakeholder}（{stakeholder_type}）
- 初始问题：{initial_question}
- 核心反馈：{feedback}
- 项目修改：{project_action}
- 证据列表：{evidence}

输出格式（严格 JSON）：
{{
  "design_reflection": "无|弱|中|强",
  "context_scene": "...",
  "risk": "...",
  "mitigation": "...",
  "limitation": "...",
  "boundary": "..."
}}"""

# ═══════════════════════════════════════════════════════════════
#  调用 3：Φ₆ 建议 + 图谱节点文本
# ═══════════════════════════════════════════════════════════════

CALL3_SYSTEM = SYSTEM_PROMPT

CALL3_USER_TEMPLATE = """这是一条 Human Practices 访谈的已提取信息与分析结果。请生成自然、具体、符合 AMPlify 项目语境的回访建议和图谱文本。

背景：AMPlify 是 iGEM 2026 Conservation 项目，用 AI 设计抗菌肽用于动物健康与抗生素减量。
注意措辞边界：这是候选筛选和体外评估阶段的科研项目，不要写成临床可用或商业产品。

已提取信息：
- 利益相关者：{stakeholder}（{stakeholder_type}）
- 核心反馈：{feedback}
- 项目修改：{project_action}
- 关联模块：{modules}
- 闭环状态：{loop_status}（L0记录/L1理解/L2行动/L3有证据/L4已回访）

输出格式（严格 JSON）：
{{
  "next_step_cn": "下一步建议（中文，一两句话，针对这条反馈的实际情况）",
  "next_step_en": "English next-step suggestion (1-2 sentences)",
  "materials_cn": ["回访应携带的材料，中文，2-4 项"],
  "materials_en": ["Materials in English, 2-4 items"],
  "questions_cn": ["回访时可直接提问的问题，中文，2-4 个"],
  "questions_en": ["Questions in English, 2-4 items"],
  "feedback_summary": "反馈一句话精炼（中文，60 字以内，用于知识图谱节点）",
  "action_summary": "项目修改一句话精炼（中文，60 字以内，用于知识图谱节点）"
}}"""


# ═══════════════════════════════════════════════════════════════
#  调用 4：英文 Wiki 文案（每条记录一段）
# ═══════════════════════════════════════════════════════════════

CALL4_SYSTEM = (
    "你是 AMPlify（iGEM 2026 Conservation 项目）的 Wiki 撰稿人。"
    "AMPlify 用 AI 设计抗菌肽，用于动物健康、抗生素减量与 One Health 生态保护。"
    "你的任务是为 Human Practices 页面撰写地道的英文叙述。"
    "只输出 JSON，不要输出任何解释或额外文本。"
)

CALL4_USER_TEMPLATE = """请根据下面这轮 Human Practices 访谈的信息，用英文撰写一段 Wiki 叙述。

格式要求（与中文 Wiki 结构一致，用 #### 小标题分节，每节用简洁的要点或 1-2 句短段落，不要堆成一大段）：
- 以三级标题（### 日期 — 受访对象）开头
- 然后依次四节：
  #### Key Feedback —— 对方的核心观点（分点列出具体事实，不要笼统概括）
  #### Modules Affected —— 影响了哪些项目模块（列表）
  #### Project Changes —— AMPlify 据此做了什么修改（分点列出具体行动）
  #### Storyline Position —— 这轮交流如何推进了项目故事线（一两句）

注意：
- 面向 iGEM 评委，语言自然、具体，不要翻译腔
- 不要出现闭环状态、证据强度、优先级分数、下一步建议这类内容

访谈信息：
- 日期：{date}
- 受访对象：{stakeholder}（{stakeholder_type}）
- 初始问题：{initial_question}
- 核心反馈：{feedback}
- 项目修改：{project_action}
- 影响模块：{modules}

输出 JSON：
{{
  "wiki_section_en": "..."
}}"""

# ═══════════════════════════════════════════════════════════════
#  调用 5：英文答辩叙事 + Wiki 总述
# ═══════════════════════════════════════════════════════════════

CALL5_SYSTEM = CALL4_SYSTEM

CALL5_USER_TEMPLATE = """请根据 AMPlify 全部 Human Practices 记录的摘要，用英文撰写两份文稿。

1. overview_en：Wiki Human Practices 页面的总述段落（150-250 词）。说明 HP Compass 模型如何把利益相关者访谈转化为可追溯的决策闭环，谁改变了项目、改变了哪里、证据是什么。语气诚恳，不做夸张承诺。

2. defense_narrative_en：答辩叙事稿（600-1000 词 markdown）。结构：
   - 一句话总结 HP 工作的核心价值
   - 三个最有影响力的 HP 节点（选优先级最高的三条记录），每条写：反馈核心、影响了哪些模块、我们做了什么、故事主线如何推进
   - 图分析洞察（使用下面提供的真实图数据，不要编造数字）
   - HP Compass 方法论（用下面提供的方法论要点，忠实转述，不要添加不存在的技术细节）
   - HP Compass 在答辩中的定位（决策导航系统、闭环追踪、透明可解释）

图数据（真实）：
{graph_facts}

方法论要点（真实）：
{methodology_facts}

记录摘要（按优先级排序）：
{cards_summary}

输出 JSON：
{{
  "overview_en": "...",
  "defense_narrative_en": "..."
}}"""

# ═══════════════════════════════════════════════════════════════
#  工具函数
# ═══════════════════════════════════════════════════════════════

def build_call4_messages(card_info: dict[str, object]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": CALL4_SYSTEM},
        {
            "role": "user",
            "content": CALL4_USER_TEMPLATE.format(
                date=card_info.get("date", "") or "日期未知",
                stakeholder=card_info.get("stakeholder", ""),
                stakeholder_type=card_info.get("stakeholder_type", "") or "未标注",
                initial_question=card_info.get("initial_question", ""),
                feedback=card_info.get("feedback", ""),
                project_action=card_info.get("project_action", ""),
                modules="、".join(card_info.get("affected_modules", []) or []) or "未分类",
            ),
        },
    ]


def build_call5_messages(
    cards_summary: str, graph_facts: str, methodology_facts: str
) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": CALL5_SYSTEM},
        {
            "role": "user",
            "content": CALL5_USER_TEMPLATE.format(
                cards_summary=cards_summary,
                graph_facts=graph_facts,
                methodology_facts=methodology_facts,
            ),
        },
    ]


def build_call2_messages(card_info: dict[str, object]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": CALL2_SYSTEM},
        {
            "role": "user",
            "content": CALL2_USER_TEMPLATE.format(
                stakeholder=card_info.get("stakeholder", ""),
                stakeholder_type=card_info.get("stakeholder_type", "") or "未标注",
                initial_question=card_info.get("initial_question", ""),
                feedback=card_info.get("feedback", ""),
                project_action=card_info.get("project_action", ""),
                evidence="、".join(card_info.get("evidence", []) or []) or "无",
            ),
        },
    ]


def build_call3_messages(card_info: dict[str, object]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": CALL3_SYSTEM},
        {
            "role": "user",
            "content": CALL3_USER_TEMPLATE.format(
                stakeholder=card_info.get("stakeholder", ""),
                stakeholder_type=card_info.get("stakeholder_type", "") or "未标注",
                feedback=card_info.get("feedback", ""),
                project_action=card_info.get("project_action", ""),
                modules="、".join(card_info.get("affected_modules", []) or []) or "未分类",
                loop_status=card_info.get("loop_status", "L0"),
            ),
        },
    ]
