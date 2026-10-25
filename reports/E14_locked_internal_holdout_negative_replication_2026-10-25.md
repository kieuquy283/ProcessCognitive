# E14 — Internal Holdout Replication of Minimal Practice-Provenance Features (2026-10-25)

**Research status: COMPLETED, one-time internal held-out evaluation.** Protocol was frozen in commit `1e868b4685c3012386c8d121ad0f393da4fdf14a` **before evaluating holdout labels**. The E14 candidate was selected post hoc from E13 development; therefore this is an INTERNAL replication, not a prospectively independent external study. The dataset is observational.

## 1. Motivation and frozen hypothesis

E13 compared a strong pretest/practice baseline with ordered traces, first-attempt correctness and student feedback/resubmission patterns. The full temporal sequence representation worsened predictive fit. An **exploratory** E13 ablation found the four attempt-distribution measures + six event-type counts promising on development (Log Loss 0.523262 vs B0 0.524361 at C=0.3), but its cluster-bootstrap confidence interval overlapped zero.

**E14 hypothesis H1:** The preselected minimal practice-attempt feature family (P_attempts) will improve prediction of correct/incorrect independent posttest items relative to the strong B0 baseline in E13's **125 reserved task IDs**.

**Null H0:** No meaningful incremental predictive contribution by P_attempts once pretest matching, practice totals, message volume, question and tutor are known.

## 2. Cohort, design, integrity

Official [StudentBench](https://huggingface.co/datasets/handshake-ai-research/studentbench) GRE Quant, pinned release SHA `304c8d63c726e72b60510bba3a44454fc0726721`. Retried original E13 selection of 48 task sessions per 13 AI arms = **624/624** fully retrieved, no missing records in targeted cohort. No user-visible chat transcripts stored or consumed as features.

- Development = **499 task IDs / 499 sessions / 13,473 posttest item outcomes**.
- Reserved internal holdout = **125 task IDs / 125 sessions / 3,375 posttest item outcomes**. Exactly 27 posttest questions per session.
- Identical task IDs never occur across development/holdout.
- Original E13 4-fold development parity check **passed before holdout scoring**:
  - Baseline B0 Log Loss = **0.5243614134736273**
  - P_attempts Log Loss = **0.5232622060011117**
- Logistic Regression `solver=liblinear`, `C=0.3`, `max_iter=250`; numeric median imputation+missingness indicators+standardization, one-hot of item/subskill/difficulty/arm/form; imputer, scaler, model fit **on 499 development sessions only**.
- All locked evaluation models scored once on the same 125 holdout sessions. Primary metric Log Loss. Secondary Brier and AUC. Paired CI: **10,000 bootstrap resamples of task clusters**.
- B0 numeric: pretest total and IRT, matched pretest item correctness, pretest skill/subskill correctness, practice total attempted/final correct/submission counts, student/tutor message totals. Category: question ID, skill/subskill/difficulty, tutor arm and assessment order.

Added features to P_attempts: full event type COUNT block, `prov_repeated_fraction`, `prov_avg_attempts`, `prov_max_attempts`, `prov_n_attempted`. The event-only N2 baseline and two explicitly secondary first-attempt feature variants are disclosed without choosing a new winner post hoc.

## 3. Primary internal-holdout results

| Candidate | Log Loss ↓ | Brier ↓ | AUC ↑ |
|---|---:|---:|---:|
| **B0 strong baseline** | **0.538238** | **0.178851** | **0.75981** |
| N2 B0+event counts | 0.538334 | 0.178910 | 0.75965 |
| **P_attempts, preselected E14 primary** | **0.540086** | **0.179747** | **0.75774** |
| P_first, secondary | 0.540477 | 0.179615 | 0.75774 |
| P_first + P_attempts, secondary | 0.540427 | 0.179747 | 0.75754 |

**Primary paired task-bootstrap contrast:** B0 Log Loss minus P_attempts Log Loss = **−0.00184844**, 95% bootstrap interval **[−0.00608979, +0.00146973]**. Negative point estimate favors baseline. **Interval spans zero**: NO verified incremental gain, and insufficient precision to assert universal deterioration.

Secondary comparisons (positive means addition is better):
- Event counts → P_attempts: **−0.00175205**, CI [−0.00624797,+0.00163123].
- B0 → P_first: **−0.00223850**, CI [−0.00496984,+0.00028277].
- B0 → P_first + attempts: **−0.00218896**, CI [−0.005600998,+0.00076525].

**Development vs reserved sign reversal:** E13 development B0 → P_attempts improvement **+0.00109921** (positive but CI crossed zero); E14 held-out point estimate **−0.00184844**. This is a failure to replicate the favorable development point estimate on the preselected internal held-out cohort.

## 4. Negative control (prespecified)

Twenty deterministic permutations reassigned the entire 4-feature attempt provenance block among **training task IDs**, preserving the joint block per session, feature marginal distributions, pretest controls, practice/event counts and holdout input untouched. This specifically disrupts putative task-specific predictive association of the new four features. These controls were predefined and **not used to choose the candidate**.

- True-feature P_attempts Log Loss: **0.540086**.
- Median across 20 shuffled-training models: **0.538453** (range **0.537734–0.541167**).
- **18/20** shuffled models scored better (lower Log Loss) than the true-feature P_attempts model.

This strengthens skepticism that the attempt-provenance features offer stable incremental value in this specification. It is **not a causal randomization test** and not a formal probability statement about scientific model superiority.

## 5. Descriptive covariate shifts

| Aggregate characteristic | Development 499 | Holdout 125 |
|---|---:|---:|
| Independent posttest item correctness | 67.05% | 67.56% |
| Mean pretest total | 13.78 | 13.65 |
| Mean first-attempt correctness (within tutoring practice) | 68.57% | 65.74% |
| Mean fraction of practice problems retried | 26.26% | 28.32% |
| Mean attempts per scored practice problem | 1.412 | 1.428 |

These differences are descriptive, not tested as causal explanations. Tutor-arm-specific held-out samples contain only approximately 6–14 tasks per arm, so individual arm deltas should **not** be interpreted as robust heterogeneity findings.

## 6. Critical scientific evaluation

1. **The best E13 exploratory family did not replicate.** A positive point estimate on development did not persist on 125 reserved tasks. This fails the primary E14 adoption criterion.
2. **Not evidence of no learning:** first→final practice gains remain descriptively large in E13, but may be driven by feedback/repeated attempts and are *not independent knowledge improvement*. E14 predicts independent posttest items, not causal tutoring effects.
3. **No leakage detected by the protocol's checks:** task IDs are disjoint, preprocessors fit only on development, original E13 development Log Loss reproduced to precision, and synthetic tests demonstrate task-block shuffle invariance.
4. **Very important scope restriction:** Although E14 protocol was frozen before holdout scoring, feature family came from E13 post-hoc ablation, and prior E7–E13 analyses explored the same underlying public StudentBench dataset. This internal holdout is **not globally independent prospective validation** and cannot be called definitive across educational populations.
5. **Measurement limitation:** Even corrected-answer statistics are affected by practice difficulty, generated item allocation, practice quantity and tutor policy. Model includes arm and counts but does not control all pedagogical confounding.
6. **Small signal and conditional inference:** Task-level CI crosses zero; observed shifts may be noise. Bootstrap does not adjust for researcher's model selection, earlier experiments, or future populations.
7. **No reverse engineering from holdout:** The observed arm differences and first-attempt shift must not be used to tune another E14 model on these 125 tasks.

## 7. Research decision and thesis consequence

**E14 result: NO-GO** for presenting P_attempts as a reproducible posttest prediction improvement. **B0 pretest+practice remains the best evidenced model in the internal holdout.** Do not proceed with architectural complexity purely to search for lift.

A scientifically defensible thesis contribution is taking form: across E7–E14, controls for prior ability and detailed practice appear very strong; several semantics/sequence features that look predictive in training do not have robust incremental validity and may be sensitive to sample selection and weak construct mapping.

For future truly confirmatory tests, prioritize either:
- an independently collected new cohort or a genuinely external educational platform; or
- a **different educational process outcome** grounded by expert/human annotations (reasoning revision, evidence uptake), with precise operational definitions before modeling.

If a new dataset is unavailable, present an explicitly scoped **negative reproducibility study** with transparent limitations, not a fictitious novel superior model.

## 8. Reproducibility and artifacts

1. [Locked E14 protocol — committed BEFORE scoring](../docs/E14_locked_internal_holdout_protocol_v0.1.md).
2. [Pinned metadata-only trace collector](../experiments/e13_collect_traces.py).
3. [E13 feature extraction with E14 reserved-only extension](../experiments/e13_features.py).
4. [E14 exact executable holdout scorer](../experiments/e14_locked_holdout.py).
5. [Synthetic regression tests for shuffled session blocks](../experiments/test_e14_locked_holdout.py) — passed.
6. [E14 aggregate metrics, 20 nulls, bootstrap and arm descriptives](E14_internal_holdout_metrics_2026-10-25.json).

All raw profile IDs, event timelines, per-item predictions and posttest item labels remain **private / uncommitted**. Model outputs represent **predictive patterns**, not measures of student cognitive states.
