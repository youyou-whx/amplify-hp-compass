# 🧭 HP Compass — Human Practices Decision Support Model

**AMPlify · iGEM 2026 Conservation**

[![Streamlit](https://img.shields.io/badge/Streamlit-Live%20Demo-FF4B4B?logo=streamlit)](https://amplify-hp-compass.streamlit.app)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)

HP Compass is an **AHP-Fuzzy Comprehensive Evaluation (FCE)** decision-support system for iGEM Human Practices. It transforms stakeholder interviews into traceable, auditable decision loops — showing *who changed the project, what they changed, and what evidence backs it up.*

> 📍 Built for **AMPlify**: AI-designed antimicrobial peptides for animal health, AMR mitigation, and One Health conservation.

---

## Table of Contents

- [Architecture](#architecture)
- [Methodology](#methodology)
- [Sensitivity & Robustness](#sensitivity--robustness)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Results](#results)
- [Limitations](#limitations)
- [References](#references)

---

## Architecture

HP Compass uses a two-layer design: an **LLM parsing layer** for semantic understanding, and a **deterministic math layer** for decision computation.

```
HP Interview (.docx)
       │
       ▼
┌──────────────────────────────────────────────┐
│  LLM Parsing Layer                           │
│  Φ₁  Structured extraction (8 fields)        │
│  Φ₂  Module relevance (4-level grades)       │
│  Φ₃  Loop semantics (action/evidence/return) │
│  Φ₆  Recommendations · Wiki text (CN/EN)     │
├──────────────────────────────────────────────┤
│  Math Decision Layer                         │
│  Φ₃  Loop level combination (L0–L4)          │
│  Φ₄  AHP-FCE priority scoring                │
│  Φ₅  6-dimension maturity assessment         │
│  Φ₇  Knowledge graph + centrality analysis   │
└──────────────────────────────────────────────┘
       │
       ▼
  Wiki (CN/EN) · Dashboard · Recommendations · Sensitivity
```

**Follow-up merging:** new records judged as follow-ups to existing interviews (by title/content + stakeholder match) are merged into the original loop — evidence unioned, loop upgraded to L4, and priority/maturity/suggestions recomputed. Timelines and wiki show each visit separately.

---

## Methodology

### 1. Module Classification (Φ₂)

For each of the 9 project modules, relevance is graded by the LLM on a 4-level scale mapped to membership values:

```math
\text{无} \to 0.0, \quad \text{弱} \to 0.35, \quad \text{中} \to 0.7, \quad \text{强} \to 1.0
```

The grade value is used directly as the fuzzy membership $\mu_c$ — the LLM acts as a semantic membership function. Without an API key, a rule-based fallback computes hit density $h_c = |M_c(T^*)| / |K_c|$ through an ascending half-trapezoid membership function $\mu_c(h_c)$ with module-specific thresholds $(\alpha_c, \beta_c)$.

### 2. Loop Status (Φ₃)

LLM judges whether the team has actually acted / produced evidence (plans don't count); the math layer combines deterministically:

```math
\ell = 1 + \mathbb{1}_{\text{has\_action}} + \mathbb{1}_{\text{has\_evidence}} + \mathbb{1}_{\text{returned}} \in \{1,2,3,4\}
```

| Level | Name | Meaning |
|:-----:|------|---------|
| L0 | Recorded | Interview documented |
| L1 | Interpreted | Core feedback extracted |
| L2 | Actioned | Concrete project change made |
| L3 | Evidenced | Evidence generated |
| L4 | Returned | Second-round feedback completed |

Evidence strength: $\sigma_e = \frac{1}{|E|} \sum_i \sigma(e_i)$ over weighted evidence items (MIC 1.0, hemolysis 1.0, CCK-8 1.0, TEM 1.0, MD 0.85, report 0.65, interview 0.55, …).

### 3. Priority Scoring (Φ₄, AHP-FCE)

A two-level FCE with AHP weights (CR < 0.10, consistent):

| Sub-system | Factors | Weights |
|-----------|---------|---------|
| $U_1$ Internal urgency | Loop gap $F_1$, Cross-module impact $F_2$, Module criticality $F_3$ | (0.540, 0.250, 0.210) |
| $U_2$ External constraints | Time urgency $F_4$, Evidence insufficiency $F_5$, Stakeholder value $F_6$ | (0.493, 0.253, 0.254) |
| Level 2 | $U_1$ vs $U_2$ | (0.667, 0.333) |

Factor values map to 4 rating levels (low/medium/high/urgent) via trapezoidal membership functions, synthesized with the $M(\cdot,+)$ operator, and de-fuzzified by centroid method:

```math
P = 0.20\,b_1 + 0.45\,b_2 + 0.72\,b_3 + 0.95\,b_4 \in [0.20, 0.95]
```

Entropy weights are computed in parallel as a diagnostic — AHP says "what matters in theory", entropy says "what discriminates in the data".

### 4. Maturity Assessment (Φ₅)

Six dimensions scored via FCE — Design Reflection, Context Exploration, Diverse Perspectives, Impact Anticipation, HP Response, Limitation Integrity. Text signals come from LLM 4-level grades; structural signals (loop level, module coverage, evidence strength) are computed mathematically. Levels are determined by max-membership rule, with a level eigenvalue as the continuous score:

```math
m_i^* = \frac{\sum_{k=0}^{5} k \cdot \mu_{i,k}^{\gamma}}{\sum_{k=0}^{5} \mu_{i,k}^{\gamma}}, \quad \gamma = 2
```

### 5. Knowledge Graph (Φ₇)

Directed Stakeholder → Feedback → Action → Evidence graph with node text summarized by the LLM. Graph analysis uses degree centrality, betweenness centrality, and PageRank; hybrid stakeholder ranking combines topology (30%) with FCE-derived semantic scores (70%).

---

## Sensitivity & Robustness

Under **±20% parameter perturbation** across all parameter classes:

| Metric | Result |
|--------|--------|
| Spearman $\rho$ (ranking) | $\geq 0.9990$ |
| Max absolute score deviation $\Delta P_{\max}$ | $\leq 0.042$ |
| Maturity level jump rate | 0% |

LLM layer stability is checked by running extraction twice per record and comparing the 15 grade fields (9 modules + 6 maturity signals); the first run is used and both raw JSONs are archived.

---

## Project Structure

```
hp_compass/
├── app.py              # Streamlit web application
├── config.py           # AHP weights, membership params, keyword dicts
├── docx_reader.py      # .docx file parser (no external deps)
├── extractor.py        # Structured field extraction (rule mode)
├── classifier.py       # Fuzzy module classification (LLM / rule)
├── llm_client.py       # DeepSeek API client
├── llm_prompts.py      # Prompt templates (extraction, grades, wiki)
├── llm_annotator.py    # LLM orchestration + stability check
├── scoring.py          # AHP-FCE priority scoring
├── maturity.py         # 6-dimension maturity assessment
├── graph_builder.py    # Knowledge graph construction + NetworkX analysis
├── recommender.py      # Action recommendation engine
├── sensitivity.py      # Sensitivity analysis
├── wiki_generator.py   # Wiki text assembly (CN rule-based, EN via LLM)
├── report.py           # Dashboard HTML + markdown recommendations
├── pipeline.py         # End-to-end pipeline (rule / llm modes)
└── schema.py           # Data models

hp_compass_output/      # Generated outputs (JSON, MD, HTML, PNG)
hp record/              # Source .docx interview records
lib/                    # Frontend libraries (vis-network, Tom Select)
```

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the pipeline (rule mode, no API key needed)
python scripts/run_hp_compass.py --input "hp record" --output hp_compass_output

# 3. Launch the web app
streamlit run hp_compass/app.py
```

Or visit the live demo: [https://amplify-hp-compass.streamlit.app](https://amplify-hp-compass.streamlit.app)

**LLM mode:** enable "🤖 大模型增强" in the sidebar and paste a DeepSeek API key (session-only, never stored) — new uploads then go through the LLM parsing layer; without a key the rule mode is used automatically.

**Upload workflow:** drop `.docx` interview records via the sidebar → one-click pipeline run → instant refresh across all 5 pages (HP Map, Timeline, Loop Dashboard, Next Step, Wiki Text).

---

## Results

From **11 HP interviews** across **9 project modules** (LLM mode):

| Metric | Value |
|--------|-------|
| Avg LLM grade stability (15 fields × 2 runs) | 0.952 |
| Highest priority | 0.855 (Prof. Qian Xun, Environmental Microbiology/ARG) |
| Knowledge graph | 67 nodes · 114 edges |
| LLM-written outputs | EN wiki · defense narrative · recommendations |

---

## Limitations

1. **Linear membership approximation:** real transitions between rating levels may not be linear.
2. **Factor independence:** $M(\cdot,+)$ assumes additive independence; non-additive synthesis could capture interaction effects.
3. **Small-sample context:** N=11 limits statistical power; parameters should be re-calibrated as the corpus grows.
4. **LLM probabilistic output:** controlled via temperature 0 and dual-run stability checking; raw outputs are archived for audit.

---

## References

1. Brin, S. & Page, L. (1998). The anatomy of a large-scale hypertextual Web search engine. *Computer Networks*, 30, 107–117.
2. Freeman, L. C. (1977). A set of measures of centrality based on betweenness. *Sociometry*, 40, 35–41.
3. Newman, M. E. J. & Girvan, M. (2004). Finding and evaluating community structure in networks. *Physical Review E*, 69, 026113.
4. Saaty, T. L. (1980). *The Analytic Hierarchy Process*. McGraw-Hill.
5. Shannon, C. E. (1948). A mathematical theory of communication. *Bell System Technical Journal*, 27, 379–423.
6. Zadeh, L. A. (1965). Fuzzy sets. *Information and Control*, 8(3), 338–353.
7. Wang, P. Z. (1983). *Fuzzy Set Theory and Its Applications*. Shanghai Science & Technology Press.
8. Chen, S. L., Li, J. G., & Wang, X. G. (2005). *Fuzzy Set Theory and Its Applications*. Science Press.

---

*HP Compass is AMPlify's Model & Software contribution to iGEM 2026. It turns Human Practices from a meeting log into a structured, auditable decision system.*
