# E11c — Pre-specified mapping and independent-posttest evaluation protocol (v0.1)

**Status:** Future experiments only. No E11c result, no final holdout score. Do not change this protocol after looking at E11 model agreement and post-test evaluation outcomes without documenting a preregistration amendment.

## What is being tested

**H1 (mapping):** An Astra-silver-trained concept↔GRE-subskill classifier can identify **direct mathematical coverage (D)** on genuinely new concept titles. Compare against always-not-D, generic-strategy heuristics, lexical similarity thresholds and frozen semantic similarity ranking. High S/N classification accuracy alone does not support H1.

**H2 (incremental predictive validity):** Skill-aligned concept-level **student action evidence** provides lower independent post-test item Log Loss after adjusting for detailed pre-test proficiency, item matching, practice and message volume, relative to identical same-data-budget pooled evidence and incorrectly shuffled subskill matching. H2 is predictive, not causal.

## Fixed datasets

- StudentBench GRE Quantitative, pin exact official Hugging Face revision before extraction and report its SHA.
- E11 sampling from **489 development sessions**, 135 sessions excluded from annotation sourcing, across 13 AI arms. **Caution:** previous E10b used a *different* split with overlapping records; neither 135 nor any previous "holdout" is guaranteed untouched over the entire project history.
- Annotation: 120 existing Astra silver labels + 400 new blinded E11 pairs (200 uniform unique-pair, 150 similarity-enriched, 50 strategy stress). Exact pairs from 120 excluded from new 400.
- Cross-model annotation by independent fresh Codex Astra and Gemini sessions; if different exact model/version used, report it. Model agreement is not human validity.
- Human domain validation recommended on prespecified 160 pairs: 80 uniform, 60 enriched, 20 strategy. Keep human labels, if acquired, independent of model predictions.

## Mapping evaluation (before any downstream performance selection)

1. Freeze one mapping training set and train baseline models with no access to evaluation D/S/N/U labels. Report D precision, D recall, D F1, calibration and four-class macro-F1.
2. Report two distinct group-shift tests: **concept-title-disjoint** and **GRE-subskill-group-disjoint**. 27 GRE Quant subskills impose limited subgroup resolution; bootstrap by subskill and concept title where appropriate.
3. For the 200 uniform candidate-pair sample, estimate class proportions among **unique naturally observed pairs** from a validated reference with binomial/finite-population uncertainty. Do not estimate population proportions from 150 enriched or 50 stress cases.
4. Threshold for an honest mapping-viability claim: show nontrivial D precision AND recall on held-out pairs with class-specific uncertainty. Do not announce any universal pass threshold after examining the results; if fewer than ~20 verified D items are present, explicitly say D evaluation remains underpowered.
5. Compare Astra label sensitivity against independent Gemini labels and human-reviewed labels where available. Agreement is not correctness.

## Predictive evaluation

Prediction target: correct/incorrect independent posttest item; session-grouped evaluation to avoid within-session label leakage.

**Primary metric:** per-item Log Loss, paired session-bootstrap differences. Secondary: Brier and AUC, calibration diagnostics and subgroup robustness.

**Reference baseline:** same paired pre-test item correctness, pretest total/IRT, skill/subskill prior evidence, practice attempts including first vs final and grading provenance where data permit, lesson/form/tutor ID, question identity/difficulty, student/tutor message counts.

**Models:** (i) reference, (ii) plus raw concept/message counts, (iii) plus pooled concept evidence, (iv) plus true skill-aligned concept evidence from frozen mapping, (v) plus identically engineered concept evidence with at least **20 independently seeded within-session alignment permutations**.

Report the incremental gain in Log Loss and CI relative to both (i) and (iii), plus gain over randomized (v). **Reject H2 (under tested conditions) if no credible positive gain** in development or if randomized mapping performs as well; do not silently redefine the outcome or baseline to favor the new method.

Always separate tuning from final evaluation. Given all prior E7–E10 exploration, a session holdout may be adaptively contaminated by project-level model design. Describe final inference as exploratory/limited unless genuinely external or prospectively collected data can be justified. Evaluate the selected frozen model only once on whatever held-out source is designated and report the selection history.

## Expected negative-result contribution

Finding no lift despite a demonstrably credible mapping would establish a meaningful *incremental predictive validity limit* for StudentBench GRE and tested feature sets. It would not imply AI tutoring causes no learning, nor that all semantic, temporal or sequence representations fail universally.

## Reproducibility checklist

Save the dataset SHA; row inclusion audit; exact 400 pair IDs; both model names and prompt version hashes; training-split seed; tuned hyperparameters; bootstrap cluster unit; pre/post time cut; all primary/secondary metrics and failure cases. Never commit private raw transcripts or annotation results without a data-handling review.
