# AMPlify Human Practices — HP Compass

AMPlify's Human Practices (HP) work is guided by the HP Compass, a decision-support model that transforms stakeholder interviews into a traceable loop of feedback, action, and evidence. Through 67 knowledge graph nodes and 114 edges, we systematically captured insights from diverse stakeholders—ranging from environmental microbiologists and wet-lab experts to veterinarians and farmers. These interactions directly reshaped our project: for instance, feedback from Prof. Qian on antibiotic resistance in the environment led us to integrate an environmental degradation panel into our peptide screening, while insights from Prof. Liu and Dr. Luo refined our wet-lab validation strategy and broadened our focus beyond mastitis. The HP Compass prioritizes actions using fuzzy comprehensive evaluation and analytic hierarchy process, ensuring that each decision is transparent and justified. Our narrative emphasizes that HP is not a box-ticking exercise but a continuous dialogue that improves scientific rigor, safety, and real-world relevance. We acknowledge the limitations of our current evidence and commit to iterative refinement based on ongoing stakeholder engagement.

---

## Stakeholder → Feedback → Action Knowledge Graph

![HP Compass Graph](hp_compass_graph.png)

---

### 2026-01-24 — Veterinary Clinicians at Northwest A&F University Animal Hospital

#### Key Feedback
- Animal infections cannot be generalized as "bacterial infections"; different body systems involve distinct pathogens, diagnostic methods, and administration routes.
- Pet clinics already have mature strategies including drug switching, combination therapy, topical cleaning, and oral antibiotics; antimicrobial peptides may be positioned more as adjunctive or health-care products in the pet market.
- Local applications (e.g., skin, ear canal) are more realistic than broad systemic infections for initial peptide use.
- Reducing antibiotic use, achieving antibiotic-free production, and controlling residues in food animals may offer higher value than pet applications.

#### Modules Affected
- Safety
- Model
- Implementation
- Material
- Problem Definition
- Environment
- Software
- Education

#### Project Changes
- Reframed AMPlify from a simple pet antimicrobial to a candidate peptide evaluation framework for animal health, antibiotic reduction, and One Health.
- Retained skin/ear topical use as a discussable scenario, while adding livestock, lactating animals, laying hens, and farming-side antibiotic reduction to future investigation directions.
- Incorporated fields for application scenario, administration route, evidence level, and safety boundaries into subsequent model and software narratives.

#### Storyline Position
This first stakeholder engagement grounded our project in real veterinary practice, shifting our focus from a narrow pet-drug mindset to a broader One Health perspective. It set the stage for later dialogues with livestock stakeholders and shaped our integrated framework for responsible peptide development.
### 2026-03-09 — Prof. Jun Liu, Key Laboratory of Animal Biology, Northwest A&F University

#### Key Feedback
- Mastitis is common in dairy sheep and cows, with clinical cases at 5%–10% and subclinical cases at 20%–30% in the Yangling area.
- Pathogen composition varies with region, barn hygiene, milking procedures, and teat dipping.
- AMPs hold promise, but the project should not focus solely on mastitis; the core science is designing peptides that kill resistant bacteria with low eukaryotic toxicity.
- Key barriers: cytotoxicity, delivery routes, stability in milk/digestive environments, production costs, and regulatory/residue concerns.

#### Modules Affected
- Safety, Model, Implementation, Material, Problem Definition, Environment, Software, Education

#### Project Changes
- Reframed mastitis as a representative scenario for antibiotic reduction and resistance pressure, not the sole target.
- Shifted main narrative to resistant bacteria screening, activity-safety window, and evidence-level reporting.
- Added scenario adaptation, toxicity window, delivery feasibility, production feasibility, and risk boundary tags to Model/Software.
- Emphasized in experimental narrative that MIC, hemolysis, CCK-8, TEM, MD, and physicochemical properties jointly support candidate evaluation, while clarifying current stage is in vitro and model-based screening.

#### Storyline Position
This consultation broadened our project from a single disease application to a robust scientific framework for AMP design, aligning with One Health by addressing antibiotic resistance in livestock. It set the stage for iterative feedback and refinement in subsequent human practices engagements.
### Date Unknown — Teacher Zhao Tianyi, AI & Biological Data Expert

#### Key Feedback
- A generator alone is insufficient; a discriminator is essential to evaluate antimicrobial potential, toxicity, and key properties.
- Mixing large amounts of unrelated protein sequences into antimicrobial peptide fine-tuning is misleading and should be avoided.
- With limited budget, synthesizing only a few candidates carries high failure risk; structural and membrane interaction analyses should guide candidate selection.

#### Modules Affected
- Safety
- Model
- Implementation
- Material
- Problem Definition
- Software

#### Project Changes
- Evolved the early ESM-2 fine-tuning approach into TAM-Flow: ESM-2 + LoRA encoding, DiT-Rectified Flow generation, Oracle expert model scoring, and RAFT reward filtering.
- Integrated physicochemical property analysis, molecular dynamics, synthesis with mass spectrometry, MIC assays, hemolysis tests, CCK-8 cytotoxicity, and TEM imaging to build a comprehensive evidence chain from prediction to experimental validation.

#### Storyline Position
This consultation sharpened our project's focus on rigorous validation, steering us from a purely generative model toward a robust discriminator-integrated pipeline. It reinforced the importance of combining computational predictions with experimental verification, a cornerstone of our One Health mission.
### 2026-03-20 — Prof. Zimei Luo, Northwest A&F University (Wet-lab & Synthetic Biology)

#### Key Feedback
- The antimicrobial target must match the intended application scenario; testing only easily available strains is insufficient.
- Both Gram-positive and Gram-negative bacteria should be covered, with strong positive controls (e.g., known high-activity AMPs or antibiotics).
- A complete wet-lab evidence chain requires MIC, hemolysis, cytotoxicity, expression yield, purification results, and product identification.
- Production system development can run in parallel with functional validation: first chemically synthesize peptides for activity tests, then explore expression and purification in E. coli, Pichia pastoris, or B. subtilis.
- The number of candidates should be justified by literature workload and budget; fewer than a paper screen is acceptable if the selection rationale is clear.
- HaCaT cells are low-cost and well-documented for initial screening, but they do not fully represent goat mammary cells; more scenario-specific validation is needed later.
- Total protein concentration does not prove the presence of the target peptide; short peptides may be hard to visualize on gels, requiring tags, Western blot, HPLC, or mass spectrometry.

#### Modules Affected
- Safety
- Model
- Implementation
- Material
- Problem Definition
- Environment
- Software
- Education

#### Project Changes
- Adjusted the wet-lab pipeline to: model screening → chemical synthesis → MIC activity validation → hemolysis/CCK-8 safety validation → TEM/mechanism support → expression and purification feasibility.
- Selected 7 representative candidate peptides from model outputs and candidate library for experimental validation, with clear explanation of selection criteria and evidence boundaries in the report.
- Added "Evidence Level" and "Production Feasibility" tags in the Software report to distinguish measured data, model predictions, literature support, and future validation.

#### Storyline Position
This consultation grounded our AI-driven design in rigorous experimental reality, transforming our wet-lab plan into a stepwise evidence chain. It also strengthened our One Health narrative by ensuring our peptides are validated against relevant pathogens and safety parameters, making our software predictions more actionable for real-world animal health applications.
### 2026-04-18 — Prof. Nie Huan, School of Life Science and Medicine, Harbin Institute of Technology

#### Key Feedback
- iGEM is a platform for interdisciplinary and inter-institutional exchange; meaningful collaboration should share non-replicable resources, lessons from failures, and project-building insights, rather than superficial interactions.
- The project must be understandable to other teams; the narrative should withstand external questioning.
- Engineering goals need to be articulated in clearer, more precise language.

#### Modules Affected
- Safety, Model, Implementation, Material, Problem Definition, Environment, Software, Education, Social Media

#### Project Changes
- Integrated "cross-institutional exchange and external perspectives" into the main Human Practices storyline.
- When presenting AMPlify, we now not only showcase candidate peptides and experimental results but also explicitly explain the project's engineering goals, collaborative value, and the boundaries of our evidence.
- Refined our communication to make the engineering logic more transparent and accessible to external reviewers.

#### Storyline Position
This conversation marked a turning point in our Human Practices journey, pushing us to frame AMPlify not just as a scientific output but as a collaborative, engineering-driven initiative. It set the stage for future exchanges by emphasizing the importance of shared, non-replicable knowledge and resilient storytelling.
### 2026-04-19 — Staff at Xi'an Fushengxian Cat Shelter

#### Key Feedback
- Cats are not frequent antibiotic users, but improper use, overuse, and recurrent skin or localized infections can still lead to treatment difficulties.
- The real-world problem is not simply 'whether to use antibiotics' but a complex interplay of diagnosis, dosage, combination therapy, and owner awareness.
- The shelter staff emphasized that the decision to use antibiotics is often influenced by practical constraints and owner behavior, not just clinical need.

#### Modules Affected
- Safety
- Implementation
- Problem Definition
- Environment
- Education
- Social Media

#### Project Changes
- Reframed the pet companion animal context as a 'daily care and medication awareness' layer within AMPlify's main storyline.
- Clarified that AMPlify's alternative antimicrobials must be cautious, explainable, and have clear boundaries in this context.
- Reaffirmed that the primary validation scenarios should focus on higher-risk, more controllable animal infections, rather than pet use cases.
- Incorporated the shelter's insights into our educational and social media materials to raise awareness about responsible antibiotic use in pets.

#### Storyline Position
This conversation added a nuanced layer to our project narrative, highlighting the importance of understanding real-world antibiotic use behaviors. It reinforced that AMPlify's role is not to replace all antibiotics but to provide targeted alternatives where they are most needed, while promoting responsible use across all animal care settings.
### 2026-04-20 — Zhang Wei, Sheep Farm Worker, Chuchu Village, Rougu Town, Yangling

#### Key Feedback
- The farm prioritizes prevention over treatment; mastitis is not frequent but causes significant losses when it occurs.
- Mixed infections are common, so farm workers prefer broad-spectrum antimicrobial alternatives that are low-damage, easy to administer, and cost-effective.\- Farmers are not swayed by novel technology; they first ask whether it works, whether it affects sheep health and milk quality, whether it reduces treatment and labor costs, and whether it fits group management.
- They favor broad-spectrum antimicrobial peptides because sheep may be exposed to multiple pathogens simultaneously, and it is impractical to run diagnostic tests before each treatment.

#### Modules Affected
- Problem Definition
- Safety
- Model
- Implementation
- Material
- Environment
- Software
- Education

#### Project Changes
- Shifted the project's main line from "designing candidate AMPs" to "candidate peptides must address real farming constraints."
- Specified the application context to lactating sheep farms, milk safety, and group-based prevention.
- Incorporated the delivery method (feed mixing) into the project narrative.
- Added a caution to temper claims about AI-designed outcomes.

#### Storyline Position
This interview grounded the project in the realities of livestock management, steering the design toward practical, broad-spectrum solutions that farmers would trust and adopt. It reinforced the importance of integrating stakeholder feedback early, shaping the project's trajectory from lab-focused design to field-ready application.
### 2026-04-22 — Du Xinyuan, Manager of Chengwei Dairy Goat Farm, Wugong County

#### Key Feedback
- Annual mastitis incidence around 10%, with chronic cases being common and prone to relapse, leading to reduced milk yield, udder hardening, and atrophy.
- Acute or septicemic mastitis is rare but severe, often associated with *Staphylococcus aureus* and anaerobic bacteria.
- Current treatment relies on ampicillin sodium, administered via intramuscular injection and intramammary infusion, over a 7-day course; full recovery takes 10–14 days and costs 200–300 RMB per case. Chronic cases may recur the following year.
- Grassroots farms lack pathogen detection capabilities, so they prefer broad-spectrum, universal treatments that do not require pathogen identification and cover multiple pathogens.
- Farmers trust real-world validation on 2–4 affected goats and word-of-mouth over theoretical claims.

#### Modules Affected
- Safety
- Model
- Implementation
- Material
- Problem Definition
- Environment
- Education
- Social Media

#### Project Changes
- Shifted the project's core focus from "whether candidate AMPs are antimicrobial" to "whether candidate AMPs can address the real treatment constraints of dairy goat mastitis."
- Strengthened the broad-spectrum approach, ensuring the AMP candidates are designed to cover multiple pathogens without requiring prior identification.
- Defined the disease boundaries and application standards that the final product must meet, based on the farm's practical conditions (e.g., cost, treatment duration, and ease of use).
- Incorporated the need for on-farm validation on a small number of animals (2–4) into the implementation strategy.

#### Storyline Position
This conversation grounded the project in the real-world context of a local dairy goat farm, moving the narrative from laboratory-centric AMP discovery to a solution-oriented approach that addresses the specific pain points of livestock producers. It reinforced the One Health mission by aligning our technical development with the practical needs of animal health and antibiotic reduction.
### 2026-05-01 — Rural Livestock Farmers and Practicing Veterinarians

#### Key Feedback
- Farmers prioritize vaccines, ventilation, and preventive care over treatment.
- They recognize that mastitis is caused by bacterial infections, but remain skeptical of 'high-tech' solutions like antimicrobial peptides.
- A farmer questioned whether AMPs would replace vaccines entirely, highlighting concerns about zoonotic diseases such as anthrax and brucellosis.

#### Modules Affected
- Safety
- Model
- Implementation
- Material
- Problem Definition
- Environment
- Education
- Social Media

#### Project Changes
- Emphasized that AMPs are not a universal substitute for vaccines or other preventive measures.
- Adopted simpler, more accurate language to explain the project to non-specialist audiences.
- Clearly defined the intended use cases and validation boundaries of AMPs in the context of rural farming.

#### Storyline Position
This conversation grounded our project in the realities of rural livestock management, reminding us that trust is built through clarity and humility. It reinforced that our solution must complement, not replace, existing practices, and that effective communication is as vital as the science itself.
### 2026-05-02 — iGEM Northeast Regional Exchange, Jilin University

#### Key Feedback
- The exchange emphasized that high-quality Human Practices is not about the number of activities, but about clearly demonstrating the chain: Stakeholder → Feedback → Action → Impact.
- Education efforts should not focus on quantity, but on ensuring the audience truly understands the problem.
- The Wiki, poster, and presentation must share a single, coherent storyline.

#### Modules Affected
- Implementation
- Problem Definition
- Environment
- Education
- Social Media

#### Project Changes
- We shifted our HP writing focus to the overview, summary cards, and the main storyline.
- We reoriented our Education module from quantity-driven to interaction-quality-driven.
- We now require that every research activity explicitly states its position in the storyline and how it influenced our project's expression or design.

#### Storyline Position
This exchange served as a pivotal checkpoint, helping us consolidate our extensive research into a clear, unified narrative. It reinforced that our project's impact is best communicated through a coherent story that connects stakeholder feedback to concrete actions, rather than a collection of isolated activities.
### 2026-05-27 — Prof. Xun Qian, College of Natural Resources and Environment, Northwest A&F University

#### Key Feedback
- Globally, over 70% of antibiotics are used in livestock production, and 30–60% are excreted unchanged or as partially metabolized compounds via urine and feces.
- These residues can enter the environment through manure recycling, wastewater effluent (municipal or farm), surface runoff, soil and water transport, and even aerosol exposure from farms.
- Current wastewater and manure treatment systems typically do not monitor antibiotics, resistant bacteria, or ARGs as routine parameters, so it is unclear whether treatment fully removes these risks.
- Even low concentrations of antibiotic residues in the environment can exert long-term selective pressure, enriching resistance genes.
- Environmental reservoirs already harbor a high background of resistance genes, and reducing antibiotic use alone will not quickly revert resistance levels.

#### Modules Affected
- Safety
- Model
- Implementation
- Material
- Problem Definition
- Environment
- Software
- Education

#### Project Changes
- Expanded the peptide screening logic from an activity-safety balance to an activity-safety-environment balance.
- Developed a Peptide Degradation Ease Score (PDES) model to estimate the predicted degradability of candidate peptides.
- Added an Environmental Degradation Panel to the software report, presenting PDES as a model-based decision support tool, not as experimental evidence of degradation.
- Revised safety language from claiming peptides are "more eco-friendly" to stating they "may have lower environmental persistence risk, but still require degradation experiments and microecological validation."

#### Storyline Position
This consultation grounded AMPlify's environmental responsibility in concrete data, shifting our design from a purely efficacy-driven approach to one that proactively considers the fate of peptides in the environment. It reinforced our commitment to transparent, evidence-based claims and set the stage for future degradation studies.