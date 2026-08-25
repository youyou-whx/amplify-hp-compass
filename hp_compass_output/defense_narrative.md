## Human Practices Defense Narrative

**Core Value:** AMPlify's Human Practices (HP) work ensures that our AI-designed antimicrobial peptides are not just scientifically novel but also socially responsible, environmentally conscious, and practically viable, by embedding stakeholder feedback into every stage of our project through a transparent, data-driven decision loop.

### Three Most Influential HP Nodes

**1. Prof. Qian (Environmental Microbiology, ARG Expert)**
- **Feedback Core:** Over 70% of antibiotics globally are used in livestock, with 30-60% excreted unchanged. Environmental residues, even at low concentrations, drive ARG enrichment. Existing treatment systems don't monitor antibiotics or ARGs, and resistance may persist even after reducing antibiotic use.
- **Modules Affected:** Safety, Model, Problem Definition, Environment, Software
- **Our Actions:** We expanded our screening logic from activity-safety balance to activity-safety-environment balance, introducing the Peptide Degradation Ease Score (PDES) and an Environmental Degradation Panel in our software. We carefully reframed claims to avoid overstating environmental benefits, emphasizing that PDES is a predictive tool, not experimental evidence.
- **Narrative Progression:** This feedback shifted our project from a narrow focus on efficacy to a holistic One Health perspective, acknowledging the environmental lifecycle of antimicrobial peptides.

**2. Dr. Luo (Wet-Lab, Synthetic Biology Expert)**
- **Feedback Core:** Antibacterial targets must match application scenarios, include both Gram-positive and negative bacteria, and use strong controls. A complete evidence chain (MIC, hemolysis, cytotoxicity, expression, purification) is essential. Chemical synthesis can validate activity in parallel with expression system exploration. Candidate numbers should be justified, and HaCaT cells are not fully representative of target cells.
- **Modules Affected:** Safety, Model, Software, Implementation, Material
- **Our Actions:** We restructured our wet-lab roadmap to: model screening → chemical synthesis → MIC activity → hemolysis/CCK-8 safety → TEM/mechanism → expression/purification feasibility. We selected 7 representative candidates and added Evidence Level and Production Feasibility tags to our software reports.
- **Narrative Progression:** This feedback grounded our computational predictions in rigorous experimental validation, enhancing the credibility of our candidate peptides.

**3. Prof. Liu (Animal Health, Livestock Expert)**
- **Feedback Core:** Mastitis is common in dairy sheep/goats, with clinical incidence 5-10% and subclinical up to 20-30% in Yangling. The project should not focus solely on mastitis but on designing peptides that kill drug-resistant bacteria with low eukaryotic toxicity. Key barriers include cytotoxicity, delivery, stability, cost, and regulatory boundaries.
- **Modules Affected:** Safety, Model, Implementation, Problem Definition, Software
- **Our Actions:** We repositioned mastitis as a representative scenario for antibiotic reduction, shifting our mainline to drug-resistant bacteria screening, activity-safety window, and evidence-graded reporting. We added scenario adaptation, toxicity window, delivery feasibility, and risk boundary tags to our models.
- **Narrative Progression:** This feedback broadened our project's scope, making it more scientifically robust and clinically relevant.

### Graph Analysis Insights

Our knowledge graph comprises 67 nodes and 114 edges, with node types: Action, Evidence, Feedback, HP, Module, NextStep, Stakeholder. The modules most influenced by HP feedback were Problem Definition (10 times), Implementation (10 times), and Safety (9 times). This indicates that stakeholder input primarily shaped our problem framing, practical implementation strategies, and safety considerations, aligning with our goal of responsible innovation.

### HP Compass Methodology

HP Compass is a decision-support model integrating Fuzzy Comprehensive Evaluation (FCE) with Analytic Hierarchy Process (AHP) for weight determination. Each interview is structured into fields and classified into loop states (L0 recorded, L1 distilled, L2 action, L3 evidence, L4 follow-up). Nine project modules are classified via fuzzy membership. Priorities are computed using a two-level FCE, considering internal urgency (loop gaps, cross-module impact, module criticality) and external constraints (time urgency, evidence insufficiency, stakeholder value). AHP judgment matrices pass consistency checks (CR<0.10), and the M(·,+) operator synthesizes results with centroid defuzzification. Six-dimensional maturity assessment (design reflection, scenario exploration, diverse perspectives, impact anticipation, HP response, limitation honesty) uses fuzzy membership weighting and level characteristic values. Knowledge graph analysis employs degree centrality, betweenness centrality, and PageRank. Sensitivity analysis under ±20% parameter perturbations shows Spearman ρ≥0.999, max score deviation ≤0.042, and 0% maturity level jumps. The text parsing layer uses large language models, while the decision computation layer is deterministic mathematical modeling.

### HP Compass in Defense

HP Compass serves as our decision navigation system, ensuring every stakeholder insight is systematically processed and acted upon. It provides a closed-loop tracking mechanism from feedback to evidence, making our decision-making transparent and explainable. By quantifying priorities and maturity, we can defend our choices with data, demonstrating that our project is not only innovative but also responsive to real-world needs and ethical considerations.