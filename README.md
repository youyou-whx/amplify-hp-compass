# 🧭 HP Compass — Human Practices Decision Support Model

**AMPlify · iGEM 2026 Conservation**

[![Streamlit](https://img.shields.io/badge/Streamlit-Live%20Demo-FF4B4B?logo=streamlit)](https://amplify-hp-compass.streamlit.app)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)

HP Compass is an **AHP-Fuzzy Comprehensive Evaluation (FCE)** decision-support system for iGEM Human Practices. Instead of collecting disconnected interview notes, it transforms every stakeholder conversation into a traceable, auditable decision loop — showing *who changed the project, what they changed, and what evidence backs it up.*

> 📍 Built for **AMPlify**: AI-designed antimicrobial peptides for animal health, AMR mitigation, and One Health conservation.

---

## Table of Contents

- [Core Idea](#core-idea)
- [Architecture](#architecture)
- [Methodology](#methodology)
  - [Module Classification](#1-module-classification)
  - [Loop Status](#2-loop-status)
  - [Priority Scoring (AHP-FCE)](#3-priority-scoring-ahp-fce)
  - [Maturity Assessment](#4-maturity-assessment)
  - [Knowledge Graph](#5-knowledge-graph)
- [Sensitivity & Robustness](#sensitivity--robustness)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Results](#results)
- [Limitations](#limitations)
- [References](#references)

---

## Core Idea

Real HP feedback is **fuzzy**: "high priority" vs "medium priority", "strongly affects Safety" vs "slightly touches Safety" — these don't have sharp numerical boundaries. HP Compass uses fuzzy mathematics to model these gradients, then de-fuzzifies into actionable outputs.

**Input:**  `.docx` stakeholder interview records

**Output:**
- 9-dimensional fuzzy membership vector per record (module relevance)
- L0–L4 loop closure status
- Priority score with fuzzy distribution vector *B*
- 6-dimension maturity profile with eigenvalue `m*`
- Action recommendations
- Interactive knowledge graph (77 nodes, 137 edges)
- Auto-generated English & Chinese wiki text

---

## Architecture

```
HP Interview (.docx)
       │
       ▼
┌──────────────────────────────────────────────────┐
│  Φ₁  Structured Extraction                       │
│      → 8 fields (date, stakeholder, feedback…)   │
├──────────────────────────────────────────────────┤
│  Φ₂  Fuzzy Multi-label Classification            │
│      → 9-dim membership vector (trapezoid MF)    │
├──────────────────────────────────────────────────┤
│  Φ₃  Loop Status Determination                   │
│      → L0–L4 state machine                       │
├──────────────────────────────────────────────────┤
│  Φ₄  AHP-FCE Priority Scoring (2-level)          │
│      → Priority score + fuzzy distribution       │
├──────────────────────────────────────────────────┤
│  Φ₅  6-Dimension Maturity Assessment (FCE)       │
│      → Eigenvalue m* + max-membership level      │
├──────────────────────────────────────────────────┤
│  Φ₆  Action Recommendation                       │
│      → Lookup table (ℓ × r → action)             │
├──────────────────────────────────────────────────┤
│  Φ₇  Knowledge Graph Construction                │
│      → 77 nodes / 137 edges + centrality analysis│
└──────────────────────────────────────────────────┘
       │
       ▼
  Wiki Text (CN/EN) · Dashboard · Recommendations
```

---

## Methodology

### Core Assumptions

| # | Assumption | Justification |
|---|-----------|---------------|
| 1 | **Small-sample expert parameterization** | N=11 is far below ML thresholds; all parameters are expert-calibrated |
| 2 | **Full auditability** | Every membership degree $r_{ij}$ traces to input $F_k$ and parameters $(a,b,c,d)$ |
| 3 | **Domain knowledge encoding** | Expert judgments as inspectable parameters $\theta \in \Theta$ |
| 4 | **Membership quantifiability** | Fuzzy predicates mathematized via Zadeh's membership functions $\mu(x): X \to [0,1]$ |

### 1. Module Classification

Each of the 9 project modules has a feature keyword set $\mathcal{K}_c$. Module relevance is determined by keyword hit density $h_c$ passed through an ascending half-trapezoid membership function:

```math
\mu_c(h_c) = \begin{cases}
0 & \text{if } h_c < \alpha_c \\[4pt]
\dfrac{h_c - \alpha_c}{\beta_c - \alpha_c} & \text{if } \alpha_c \leq h_c < \beta_c \\[8pt]
1 & \text{if } h_c \geq \beta_c
\end{cases}
```

Parameters $(\alpha_c, \beta_c)$ were calibrated by team-wide module voting consensus.

### 2. Loop Status

Feedback follows a 5-level state machine:

| Level | Name | Meaning |
|:-----:|------|---------|
| L0 | Recorded | Interview documented |
| L1 | Interpreted | Core feedback extracted |
| L2 | Actioned | Concrete project change made |
| L3 | Evidenced | Evidence (data/model/report) generated |
| L4 | Returned | Second-round stakeholder feedback completed |

### 3. Priority Scoring (AHP-FCE)

A **two-level Fuzzy Comprehensive Evaluation** is used:

**Factor sets:**
- $U_1$ (Internal Urgency): Loop gap $F_1$, Cross-module impact $F_2$, Module criticality $F_3$
- $U_2$ (External Constraints): Time urgency $F_4$, Evidence insufficiency $F_5$, Stakeholder value $F_6$

**AHP Weights** ($\text{CR} < 0.10$, consistent):

| Sub-system | Weight vector | Notes |
|-----------|---------------|-------|
| $U_1$ | $(0.540, 0.250, 0.210)$ | $F_1$ dominates (loop gap drives priority) |
| $U_2$ | $(0.493, 0.253, 0.254)$ | $F_4$ strongest near deadline |
| Level 2 | $(0.667, 0.333)$ | Internal urgency weighted higher |

**Membership functions** use trapezoidal/triangular shapes satisfying:
- **Coverability:** $\sum_j r_{ij}(F) = 1$ for any $F \in [0,1]$
- **Convexity:** Peak membership at center of each category
- **Smooth transition:** Overlap at adjacent boundaries

**De-fuzzification** via centroid method:

```math
P = 0.20\,b_1 + 0.45\,b_2 + 0.72\,b_3 + 0.95\,b_4
```

**Fuzzy operator:** $M(\cdot,+)$ (weighted average) — selected over $M(\wedge,\vee)$, $M(\cdot,\vee)$, and $M(\wedge,\oplus)$ for maximum information retention and additive decomposability.

**Entropy-weight parallel diagnosis:** Shannon entropy weights computed alongside AHP weights provide a "theoretical importance vs. actual data discrimination" comparison.

### 4. Maturity Assessment

Six dimensions evaluated via FCE:

| Dimension | Signals | Logic |
|-----------|:-------:|-------|
| Design Reflection Depth | 4 | Loop level × design module coverage × evidence |
| Context Exploration | 4 | Stakeholder type × implementation/env coverage |
| Diverse Perspectives | 3 | Module breadth × stakeholder diversity |
| Impact Anticipation | 5 | Safety/Environment membership × risk language × mitigation |
| HP Response | 4 | Loop level × evidence × modification richness |
| Limitation Integrity | 4 | Limitation discourse × Safety membership × boundary evidence |

**Two-trigger scoring:**
- **Rule 1:** Max membership principle (when $\mu_k > 0.5$ — unique by Theorem 6.1)
- **Rule 2:** Eigenvalue method (when all $\mu_k \leq 0.5$):

```math
m_i^* = \frac{\sum_{k=0}^{5} k \cdot \mu_{i,k}^{\gamma}}{\sum_{k=0}^{5} \mu_{i,k}^{\gamma}}, \quad \gamma = 2
```

### 5. Knowledge Graph

Directed graph $G = (V, E)$ with 7 node types and 7 edge types:

**Centrality metrics:**
- Degree centrality: $C_D(v) = \deg(v) / (|V|-1)$
- Betweenness centrality: $C_B(v) = \sum_{s \neq v \neq t} \sigma_{st}(v) / \sigma_{st}$
- PageRank: $\mathbf{pr} = \alpha \mathbf{S}^\top \mathbf{pr} + (1-\alpha) \mathbf{1}/|V|$, $\alpha = 0.85$, power iteration to $\|\Delta\|_\infty < 10^{-6}$

**Hybrid stakeholder ranking:** combines graph topology scores (30%) with FCE-derived HP semantic scores (70%: priority 35%, module coverage 25%, evidence strength 10%).

---

## Sensitivity & Robustness

Under **±20% parameter perturbation** across all parameter classes:

| Metric | Result |
|--------|--------|
| Spearman $\rho$ (ranking) | $\geq 0.9990$ |
| Max absolute score deviation $\Delta P_{\max}$ | $\leq 0.042$ |
| Maturity level jump rate | 0% |

**Most sensitive parameters** (still well below decision-relevance threshold):
1. Membership function plateau width: $\Delta P_{\max} = 0.042$
2. Safety module criticality $\kappa(\text{Safety})$: $\Delta P_{\max} = 0.038$

Robustness derives from three structural properties: membership function coverability, AHP normalization constraints, and two-level architecture damping.

---

## Project Structure

```
hp_compass/
├── app.py              # Streamlit web application
├── config.py           # AHP weights, membership params, keyword dicts
├── docx_reader.py      # .docx file parser (no external deps)
├── extractor.py        # Structured field extraction
├── classifier.py       # Fuzzy multi-label module classification
├── scoring.py          # AHP-FCE priority scoring
├── maturity.py         # 6-dimension maturity assessment
├── graph_builder.py    # Knowledge graph construction + NetworkX analysis
├── recommender.py      # Action recommendation engine
├── sensitivity.py      # Monte Carlo sensitivity analysis
├── wiki_generator.py   # Auto wiki text generation (CN + EN)
├── report.py           # Dashboard HTML + markdown recommendations
├── pipeline.py         # End-to-end processing pipeline
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

# 2. Run the pipeline
python scripts/run_hp_compass.py --input "hp record" --output hp_compass_output

# 3. Launch the web app
streamlit run hp_compass/app.py
```

Or visit the live demo: [https://amplify-hp-compass.streamlit.app](https://amplify-hp-compass.streamlit.app)

**Upload workflow:** drop `.docx` interview records via the sidebar → one-click pipeline run → instant refresh across all 5 pages (HP Map, Timeline, Loop Dashboard, Next Step, Wiki Text).

---

## Results

From **11 HP interviews** across **9 project modules**:

| Metric | Value |
|--------|-------|
| Avg priority score | 0.619 |
| Highest priority | 0.823 (Prof. Qian Xun, Environmental Microbiology/ARG) |
| Avg maturity eigenvalue | 2.80 |
| Highest maturity dimension | Diverse Perspectives (3.10) |
| Knowledge graph | 77 nodes · 137 edges |
| All loops | L3 (Evidenced), advancing to L4 |

---

## Limitations

1. **Linear membership approximation:** Real-world category transitions may not be linear; smoother MF shapes could reduce boundary artifacts.
2. **Factor independence assumption:** $M(\cdot,+)$ assumes additive independence; future work could incorporate non-additive synthesis for interaction effects (e.g., loop gap × Safety criticality synergy).
3. **Keyword-based classification:** Feature-word matching cannot distinguish repeated shallow mentions from condensed expert judgment; semantic dispersion could serve as a calibration factor.
4. **Unidirectional state machine:** L0→L4 is a chain; real HP involves iterative spirals (e.g., second feedback triggering new modifications → L4→L2 return edges).
5. **Small-sample context:** N=11 limits statistical power; parameters should be re-calibrated as the interview corpus grows.

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

*HP Compass is AMPlify's Model & Software contribution to iGEM 2026. It turns Human Practices from a meeting log into a structured, auditable decision system — not to replace team judgment, but to sharpen it.*
