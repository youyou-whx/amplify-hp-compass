%% HP Compass Model Flowchart
%  AMPlify (iGEM Conservation), June 2026
%  Run in MATLAB → generates HP_Compass_Flowchart.png + .pdf
clear; close all;

try  %#ok<*TRYNC>
    set(groot, 'defaultAxesFontName', 'Microsoft YaHei');
    set(groot, 'defaultTextFontName', 'Microsoft YaHei');
end

fig = figure('Name', 'HP Compass Model Flowchart', ...
             'Position', [100, 60, 1400, 950], ...
             'Color', 'white', 'NumberTitle', 'off');
ax = axes('Parent', fig, 'Position', [0 0 1 1], 'Visible', 'off');
hold(ax, 'on'); xlim([0, 16]); ylim([0, 12]);

% ── Colors ──
c_in  = [0.20 0.60 0.86];   c_pr  = [0.45 0.70 0.45];
c_fce = [1.00 0.60 0.10];   c_out = [0.85 0.30 0.30];
c_arr = [0.30 0.30 0.30];   c_txt = [0.15 0.15 0.15];
c_lbl = [0.45 0.45 0.45];   c_g2  = [0.20 0.42 0.20];
c_or2 = [0.70 0.35 0.00];

% ╔══════════════════════════════════════════════════════════════╗
% ║  TITLE                                                      ║
% ╚══════════════════════════════════════════════════════════════╝
text(8, 11.6, '\bf HP Compass: AHP-FCE Human Practices Decision Support', ...
     'FontSize', 15, 'HorizontalAlignment', 'center', 'Color', c_txt, 'Interpreter','tex');
text(8, 11.1, 'HP Compass: 基于AHP-模糊综合评价的HP决策支持模型  |  七阶段复合映射', ...
     'FontSize', 10, 'HorizontalAlignment', 'center', 'Color', c_lbl, 'Interpreter','none');

% ╔══════════════════════════════════════════════════════════════╗
% ║  INPUT                                                      ║
% ╚══════════════════════════════════════════════════════════════╝
drawBox(2.5, 10, 4.2, 1.1, c_in, 0.15);
text(2.5, 10.30, '\bf Input: HP Documents', 'FontSize', 11, 'Color', c_in, ...
     'HorizontalAlignment', 'center', 'Interpreter','tex');
text(2.5,  9.86, 'D = {D_1, ..., D_N}   (.docx interview records)', ...
     'FontSize', 9, 'HorizontalAlignment', 'center', 'Color', c_txt, 'Interpreter','none');
text(2.5,  9.50, 'N = 11', 'FontSize', 8, 'HorizontalAlignment', 'center', ...
     'Color', c_lbl, 'Interpreter','none');
arrow(2.5, 9.45, 2.5, 8.85, c_arr, 1.5);

% ╔══════════════════════════════════════════════════════════════╗
% ║  STAGE 1 — Phi1  Structured Extraction                      ║
% ╚══════════════════════════════════════════════════════════════╝
drawBox(2.5, 8.25, 4.2, 1.20, c_pr, 0.18);
text(2.5, 8.70, '\bf Stage 1: Structured Extraction  \Phi_1', 'FontSize', 10, ...
     'HorizontalAlignment', 'center', 'Color', c_g2, 'Interpreter','tex');
text(2.5, 8.35, 'Text predicates + position functions → 8-field tuple', ...
     'FontSize', 8, 'HorizontalAlignment', 'center', 'Color', c_txt, 'Interpreter','none');
text(2.5, 8.00, '(d, s, τ, q, f, a, E, r)    |    3-tier evidence construction', ...
     'FontSize', 7.5, 'HorizontalAlignment', 'center', 'Color', c_lbl, 'Interpreter','none');
arrow(4.60, 8.25, 5.20, 8.25, c_arr, 1.5);

% ╔══════════════════════════════════════════════════════════════╗
% ║  STAGE 2 — Phi2  Fuzzy Membership Classification  [FCE]     ║
% ╚══════════════════════════════════════════════════════════════╝
drawBox(7.2, 8.25, 4.0, 1.20, c_fce, 0.18);
text(7.2, 8.70, '\bf Stage 2: Fuzzy Membership  \Phi_2   ◆ FCE', ...
     'FontSize', 10, 'HorizontalAlignment', 'center', 'Color', c_or2, 'Interpreter','tex');
text(7.2, 8.35, 'Half-trapezoid membership  μ_c(h_c) ∈ [0,1]', ...
     'FontSize', 8, 'HorizontalAlignment', 'center', 'Color', c_txt, 'Interpreter','none');
text(7.2, 8.00, '9 modules × keyword hit density → 9-dim membership vector', ...
     'FontSize', 7.5, 'HorizontalAlignment', 'center', 'Color', c_lbl, 'Interpreter','none');
text(7.2, 7.70, 'c_i = (μ_1,…,μ_9)  |  Delphi-calibrated (α_c, β_c)', ...
     'FontSize', 7, 'HorizontalAlignment', 'center', 'Color', c_lbl, 'Interpreter','none');
arrow(9.20, 8.25, 9.90, 8.25, c_arr, 1.5);

% ╔══════════════════════════════════════════════════════════════╗
% ║  STAGE 3 — Phi3  Closed-Loop Determination                  ║
% ╚══════════════════════════════════════════════════════════════╝
drawBox(11.8, 8.25, 3.8, 1.20, c_pr, 0.18);
text(11.8, 8.70, '\bf Stage 3: Closed-Loop  \Phi_3', 'FontSize', 10, ...
     'HorizontalAlignment', 'center', 'Color', c_g2, 'Interpreter','tex');
text(11.8, 8.35, 'Max-achievement principle → discrete states', ...
     'FontSize', 8, 'HorizontalAlignment', 'center', 'Color', c_txt, 'Interpreter','none');
text(11.8, 8.00, 'ℓ ∈ {0,1,2,3,4}  (L0 Recorded – L4 Re-engaged)', ...
     'FontSize', 7.5, 'HorizontalAlignment', 'center', 'Color', c_lbl, 'Interpreter','none');
text(11.8, 7.70, 'σ_e evidence strength  |  qualitative change, not degree', ...
     'FontSize', 7, 'HorizontalAlignment', 'center', 'Color', c_lbl, 'Interpreter','none');
arrow(4.60, 7.88, 9.90, 7.88, [0.50 0.50 0.50], 1.0);  % Phi1->Phi3 data flow

% ╔══════════════════════════════════════════════════════════════╗
% ║  STAGE 4 — Phi4  AHP-FCE Priority Evaluation  ★ CENTERPIECE ║
% ╚══════════════════════════════════════════════════════════════╝
drawBox(7.2, 5.40, 5.2, 1.65, c_fce, 0.25);
text(7.2, 6.10, '\bf Stage 4: AHP-FCE Priority Evaluation  \Phi_4   ◆ CORE', ...
     'FontSize', 11, 'HorizontalAlignment', 'center', 'Color', c_or2, 'Interpreter','tex');
text(7.2, 5.74, '2-Level Fuzzy Comprehensive Evaluation  +  Centroid Defuzzification', ...
     'FontSize', 9, 'HorizontalAlignment', 'center', 'Color', c_txt, 'Interpreter','none');
text(7.2, 5.38, 'U_1 (Internal Urgency): F_1,F_2,F_3    |    U_2 (External Constraints): F_4,F_5,F_6', ...
     'FontSize', 8, 'HorizontalAlignment', 'center', 'Color', c_txt, 'Interpreter','none');
text(7.2, 5.05, 'AHP square-root → A_1,A_2,A  |  M(·, +) operator  |  B∈[0,1]^4  |  P∈[0.20,0.95]', ...
     'FontSize', 7.5, 'HorizontalAlignment', 'center', 'Color', c_lbl, 'Interpreter','none');
text(7.2, 4.76, 'Output: fuzzy vector B=(b_1,b_2,b_3,b_4)  +  priority score P', ...
     'FontSize', 7, 'HorizontalAlignment', 'center', 'Color', c_txt, 'Interpreter','none');
arrow(7.2, 7.65, 7.2, 6.22, c_arr, 1.5);
arrow(11.8, 7.65, 9.80, 6.22, c_arr, 1.2);

% ╔══════════════════════════════════════════════════════════════╗
% ║  STAGE 5 — Phi5  Fuzzy Maturity Assessment  [FCE]           ║
% ╚══════════════════════════════════════════════════════════════╝
drawBox(2.5, 3.35, 4.5, 1.40, c_fce, 0.18);
text(2.5, 3.93, '\bf Stage 5: Fuzzy Maturity Assessment  \Phi_5   ◆ FCE', ...
     'FontSize', 10, 'HorizontalAlignment', 'center', 'Color', c_or2, 'Interpreter','tex');
text(2.5, 3.58, '6 dimensions × 6 levels × multi-signal membership functions', ...
     'FontSize', 8, 'HorizontalAlignment', 'center', 'Color', c_txt, 'Interpreter','none');
text(2.5, 3.25, 'Max-membership principle + Level Eigenvalue m_i*', ...
     'FontSize', 8, 'HorizontalAlignment', 'center', 'Color', c_txt, 'Interpreter','none');
text(2.5, 2.92, 'm=(m_1,…,m_6)  |  γ=2 power-weighted  |  non-dominant → m_i* continuous score', ...
     'FontSize', 7, 'HorizontalAlignment', 'center', 'Color', c_lbl, 'Interpreter','none');
arrow(4.75, 5.40, 4.70, 4.05, c_arr, 1.5);
arrow(2.5, 7.65, 2.5, 4.05, [0.55 0.55 0.55], 0.7, 'LineStyle', '--', ...
      'HeadStyle', 'plain', 'HeadWidth', 3, 'HeadLength', 3);

% ╔══════════════════════════════════════════════════════════════╗
% ║  STAGE 6 — Phi6  Action Recommendation                      ║
% ╚══════════════════════════════════════════════════════════════╝
drawBox(7.2, 2.10, 3.8, 1.10, c_pr, 0.18);
text(7.2, 2.52, '\bf Stage 6: Action Recommendation  \Phi_6', 'FontSize', 10, ...
     'HorizontalAlignment', 'center', 'Color', c_g2, 'Interpreter','tex');
text(7.2, 2.18, 'Lookup table: (ℓ, r) → action command', ...
     'FontSize', 8, 'HorizontalAlignment', 'center', 'Color', c_txt, 'Interpreter','none');
text(7.2, 1.85, '+ material & question suggestion templates', ...
     'FontSize', 7, 'HorizontalAlignment', 'center', 'Color', c_lbl, 'Interpreter','none');
arrow(4.50, 3.35, 5.30, 2.65, c_arr, 1.5);

% ╔══════════════════════════════════════════════════════════════╗
% ║  STAGE 7 — Phi7  Knowledge Graph                            ║
% ╚══════════════════════════════════════════════════════════════╝
drawBox(11.8, 2.10, 4.0, 1.10, c_pr, 0.18);
text(11.8, 2.52, '\bf Stage 7: Knowledge Graph  \Phi_7', 'FontSize', 10, ...
     'HorizontalAlignment', 'center', 'Color', c_g2, 'Interpreter','tex');
text(11.8, 2.18, 'G=(V,E) directed  |  7 node types  |  7 relation types', ...
     'FontSize', 8, 'HorizontalAlignment', 'center', 'Color', c_txt, 'Interpreter','none');
text(11.8, 1.85, 'PageRank + degree/betweenness centrality → S_h(v) hybrid rank', ...
     'FontSize', 7, 'HorizontalAlignment', 'center', 'Color', c_lbl, 'Interpreter','none');
arrow(9.10, 2.10, 9.80, 2.10, c_arr, 1.5);

% ╔══════════════════════════════════════════════════════════════╗
% ║  FINAL OUTPUT                                               ║
% ╚══════════════════════════════════════════════════════════════╝
drawBox(7.2, 0.55, 6.2, 0.85, c_out, 0.15);
text(7.2, 0.85, '\bf Global Output', 'FontSize', 11, ...
     'HorizontalAlignment', 'center', 'Color', c_out, 'Interpreter','tex');
text(7.2, 0.48, '{(x_i, c_i, ℓ_i, P_i, m_i, r_i)}_{i=1…N}  +  G  +  hybrid stakeholder ranking S_h(v)', ...
     'FontSize', 7.5, 'HorizontalAlignment', 'center', 'Color', c_txt, 'Interpreter','none');
arrow(7.2, 1.55, 7.2, 0.98, c_arr, 1.5);
arrow(11.8, 1.55, 10.3, 0.98, c_arr, 1.5);

% ╔══════════════════════════════════════════════════════════════╗
% ║  SIDE PANEL: Data Flow Summary                              ║
% ╚══════════════════════════════════════════════════════════════╝
text(13.5, 9.8, '\bf Composite Mapping', 'FontSize', 9, 'Color', c_txt, 'Interpreter','tex');
text(13.5, 9.30, 'D_i →^{Φ1} x_i →^{Φ2} c_i', 'FontSize', 7.5, ...
     'HorizontalAlignment', 'center', 'Color', c_txt, 'Interpreter','tex');
text(13.5, 8.85, '→^{Φ3} ℓ_i →^{Φ4} P_i', 'FontSize', 7.5, ...
     'HorizontalAlignment', 'center', 'Color', c_txt, 'Interpreter','tex');
text(13.5, 8.40, '→^{Φ5} m_i →^{Φ6} r_i →^{Φ7} G', 'FontSize', 7.5, ...
     'HorizontalAlignment', 'center', 'Color', c_txt, 'Interpreter','tex');

% ╔══════════════════════════════════════════════════════════════╗
% ║  SIDE PANEL: Weight System                                  ║
% ╚══════════════════════════════════════════════════════════════╝
text(13.5, 7.30, '\bf Weight System', 'FontSize', 9, 'Color', c_txt, 'Interpreter','tex');
text(13.5, 6.85, 'AHP expert judgment matrix', 'FontSize', 7.5, ...
     'HorizontalAlignment', 'center', 'Color', c_g2, 'Interpreter','none');
text(13.5, 6.48, 'Square-root method', 'FontSize', 7, ...
     'HorizontalAlignment', 'center', 'Color', c_lbl, 'Interpreter','none');
text(13.5, 6.18, '+ consistency test (CR<0.10)', 'FontSize', 7, ...
     'HorizontalAlignment', 'center', 'Color', c_lbl, 'Interpreter','none');
text(13.5, 5.78, 'Delphi calibration (CV<0.15)', 'FontSize', 7, ...
     'HorizontalAlignment', 'center', 'Color', c_lbl, 'Interpreter','none');
text(13.5, 5.30, 'Entropy-weight diagnostic', 'FontSize', 7.5, ...
     'HorizontalAlignment', 'center', 'Color', c_fce, 'Interpreter','none');
text(13.5, 5.00, '(discrimination reference)', 'FontSize', 6.5, ...
     'HorizontalAlignment', 'center', 'Color', c_lbl, 'Interpreter','none');
arrow(13.5, 7.00, 9.80, 6.10, [0.45 0.45 0.45], 0.8, 'LineStyle', '-.', ...
      'HeadStyle', 'plain', 'HeadWidth', 3, 'HeadLength', 3);

% ╔══════════════════════════════════════════════════════════════╗
% ║  SIDE PANEL: Sensitivity Validation                         ║
% ╚══════════════════════════════════════════════════════════════╝
text(13.5, 4.20, '\bf Sensitivity Validation', 'FontSize', 9, 'Color', c_txt, 'Interpreter','tex');
text(13.5, 3.80, '±20% perturbation → ρ ≥ 0.9990', 'FontSize', 7.5, ...
     'HorizontalAlignment', 'center', 'Color', c_lbl, 'Interpreter','none');
text(13.5, 3.45, 'ΔP_{max} ≤ 0.042', 'FontSize', 7.5, ...
     'HorizontalAlignment', 'center', 'Color', c_lbl, 'Interpreter','none');
text(13.5, 3.12, 'maturity jump rate = 0%', 'FontSize', 7.5, ...
     'HorizontalAlignment', 'center', 'Color', c_lbl, 'Interpreter','none');

% ╔══════════════════════════════════════════════════════════════╗
% ║  LEGEND                                                     ║
% ╚══════════════════════════════════════════════════════════════╝
ly = 0.85;
rectangle('Position', [0.4, ly-0.10, 0.35, 0.22], 'Curvature', 0.10, ...
          'FaceColor', [c_fce, 0.55], 'EdgeColor', c_fce, 'LineWidth', 2);
text(1.05, ly, '◆  FCE Fuzzy Comprehensive Evaluation stage', ...
     'FontSize', 7, 'Color', c_txt, 'HorizontalAlignment', 'left', 'Interpreter','none');
rectangle('Position', [5.5, ly-0.10, 0.35, 0.22], 'Curvature', 0.10, ...
          'FaceColor', [c_pr, 0.55], 'EdgeColor', c_pr, 'LineWidth', 2);
text(6.15, ly, 'Precise method stage (extraction / determination / recommendation / graph)', ...
     'FontSize', 7, 'Color', c_txt, 'HorizontalAlignment', 'left', 'Interpreter','none');
rectangle('Position', [11.3, ly-0.10, 0.35, 0.22], 'Curvature', 0.10, ...
          'FaceColor', [c_in, 0.55], 'EdgeColor', c_in, 'LineWidth', 2);
text(11.95, ly, 'Input / Output', 'FontSize', 7, 'Color', c_txt, ...
     'HorizontalAlignment', 'left', 'Interpreter','none');

% ╔══════════════════════════════════════════════════════════════╗
% ║  SAVE                                                       ║
% ╚══════════════════════════════════════════════════════════════╝
outDir = fileparts(mfilename('fullpath'));
if isempty(outDir), outDir = pwd; end
pngPath = fullfile(outDir, 'HP_Compass_Flowchart.png');
pdfPath = fullfile(outDir, 'HP_Compass_Flowchart.pdf');
exportgraphics(fig, pngPath, 'Resolution', 300);
fprintf('Saved: %s\n', pngPath);
exportgraphics(fig, pdfPath, 'ContentType', 'vector');
fprintf('Saved: %s\n', pdfPath);
disp('Done.');

% ═══════════════════════════════════════════════════════════════
%  LOCAL FUNCTIONS  (must be at end of script)
% ═══════════════════════════════════════════════════════════════
function drawBox(xc, yc, w, h, clr, alpha_val)
    rectangle('Position', [xc-w/2, yc-h/2, w, h], ...
              'Curvature', 0.10, 'FaceColor', [clr, alpha_val], ...
              'EdgeColor', clr, 'LineWidth', 2.2);
end

function ah = arrow(x1, y1, x2, y2, clr, lw, varargin)
    dx = 0.06; dy = 0.04;
    fx = @(x) dx + (1-2*dx) * (x / 16);
    fy = @(y) dy + (1-2*dy) * (y / 12);
    ah = annotation('arrow', [fx(x1), fx(x2)], [fy(y1), fy(y2)], ...
                    'Color', clr, 'LineWidth', lw, 'HeadStyle', 'cback2', ...
                    'HeadWidth', 7, 'HeadLength', 5.5, varargin{:});
end
