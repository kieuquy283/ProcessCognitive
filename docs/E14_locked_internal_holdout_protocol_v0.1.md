# E14 — Locked Internal-Holdout Replication of Minimal Practice Evidence

**Protocol frozen before accessing 125 E13 reserved-session posttest outcomes.** Researcher requested to continue following E13. This is *internal validation of a post-hoc chosen E13 feature family*, NOT prospective independent/external confirmation.

## Background: predetermined decisions from E13 (not derived from E14 holdout)

In E13 development 499 sessions / 13,473 posttest items, B0 pre-test+practice Logistic Regression scored Log Loss 0.524361 at regularization C=0.3; the exploratory **attempt-distribution-only** feature family (B0 + all five event counts + 4 retry/attempt-provenance features) scored 0.523262, a directional development benefit with bootstrap CI crossing zero.

**Freeze E14 before holdout**: primary comparator B0 vs E13 `P_attempts`, C=0.3, identical unmodified features/preprocessing, all available posttest item outcomes. Use SAME original E13 624 selected sessions, same deterministic random split by `student_id` task identifier: 499 dev / 125 reserved, SHA `304c8d63c726e72b60510bba3a44454fc0726721`. Set random_state 20261025; no holdout-driven hyperparameter/feature selection or posttest exclusion.

## Primary outcome

Within 125 reserved task IDs, assess per-item predictive Log Loss from models fit only on the 499 development task IDs. Primary paired improvement: **B0 logloss – P_attempts logloss** (positive favors new model). Report point estimate and **95% percentile bootstrap CI resampled by task**, not by 27 item rows. With fixed task item counts (normally 27), task-average and item-weighted losses coincide.

Secondary: Brier, AUC, sample count, arm subgroup descriptive deltas, calibration. Report results for 125 reserved sessions whether favorable or negative. Do NOT claim E14 is statistically confirmatory over the total prior research program; same public StudentBench sessions informed E7–E13 feature selection.

## Fixed models

- B0 numeric: `pre_total`, `pre_theta`, `pre_matched`, `pre_skill`, `pre_sub`, `practice_n`, `practice_good`, `practice_submissions`, `student_msgs`, `tutor_msgs`. Categorical: `question`, `skill`, `subskill`, `difficulty`, `arm`, `form`.
- N2: B0 plus all `count_*` trajectory-type counts; negative control for count redundancy.
- **Primary P_attempts**: B0 + all `count_*` plus EXACT E13 ablation columns `prov_repeated_fraction`, `prov_avg_attempts`, `prov_max_attempts`, `prov_n_attempted`.
- Secondary sensitivity **P_first**: B0 + all `count_*` plus `prov_first_correct_rate`, `prov_first_wrong_count`, `prov_answered_missing`.
- Secondary P_first+attempts: B0 + counts + seven union provenance features. No full E13 B2.
- Regularized LogisticRegression `solver=liblinear`, `C=0.3`, `max_iter=250`, default class weights. All continuous imputation, missing indicators, scaling, and one-hot categoricals fit on **development sessions only**.
- Diagnostic null: 20 seeded shuffles that PERMUTE the entire block of 4 attempt features across development task IDs (not across item rows) before fitting; holdout values remain unchanged. This preserves feature marginal distribution and case count while breaking outcome/skill correspondences in training. Compare holdout metrics descriptively; null shuffles are not alternative winners selected via holdout.
- Reproduce E13 4-fold task-grouped OOF B0 and P_attempts first to verify feature parity. No choice of hyperparameters on the held-out data.

## Statistical and methodological cautions

- E13 prior dev evaluation and E14 were both adaptive to past decisions. Single-use reserved subset provides a meaningful **internal stability check**, but not a fully new population sample; multiple previous experiments have explored StudentBench.
- Missing 0/624 selected sessions in E13 full trace collector. This is only 624 selected from the broader corpus; do not infer broad StudentBench population representativeness.
- AUC/Brier are secondary, unadjusted. Bootstrap is conditional on frozen trained model and cohort; no uncertainty from data curation/model selection.
- Practice item difficulty and AI arm are possible confounders. Observational prediction is not evidence of causal learning or true skill mastery.
- If features fail to add reliable holdout value, report failed internal replication and stop model expansion.

Frozen design commit is visible in git history. Holdout scoring should occur **after** this file is committed.

## References

- [E13 real results](../reports/E13_practice_process_temporal_real_results_2026-10-25.md)
- [E13 feature source](../experiments/e13_features.py)
- [Official StudentBench](https://huggingface.co/datasets/handshake-ai-research/studentbench)
