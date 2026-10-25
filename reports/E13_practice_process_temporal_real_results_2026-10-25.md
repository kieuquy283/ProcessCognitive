# E13 — Practice provenance, feedback and temporal traces on StudentBench (25 October 2026)

**Status:** Executed on real StudentBench GRE Quant data. **Exploratory development evaluation only**, no final holdout score, no causal learning claim. Results are intentionally reported even when negative.

## Research problem and design

E7–E12 did not establish meaningful incremental prediction from dialogue counts, semantic embeddings, temporal RNNs or GPT-6 Astra silver concept↔skill labels against a strong pre-test/practice baseline. **E13 changes the measurement**: can *observed practice process* (first correctness, corrective resubmission and event ordering) add predictive value for independent post-test item correctness?

Predictions are at **post-test item level**; evaluation groups **task/student IDs** (not posttest items) so all 27 posttest questions of one session stay in the same fold. Code additionally verifies unique task IDs in this cohort. No human mastery labels, unvalidated NLP mapping or silver E11 labels are used in E13.

StudentBench dataset revision: `304c8d63c726e72b60510bba3a44454fc0726721`, GRE Quant, 13 tutor arms × 48 selected sessions = **624/624 complete retrieval**.

- **499** development sessions, **13,473** held-out-fold post-test item outcomes.
- **125** reserved sessions NOT scored. Selected by fixed seed over task IDs before modeling.
- 4-fold task-ID GroupKFold. Logistic regression with C=0.03 and C=0.3, per-fold fit of imputer/scaler/one-hot encoders.
- Confidence intervals from **3,000 bootstrap samples of task clusters**; contrasts are equally weighted across tasks and conditional on these OOF predictions (not nested-selection adjusted).
- Input event traces contain `practice_answer_submitted`, `practice_problem_id`, `is_correct`, `trajectory_position`, `timestamp_elapsed_seconds`, `student_message` and `ai_tutor_message`. The private reduced session file **does not contain transcript text or AI response text**.

## Data integrity and descriptive findings

Source audit from 499 development sessions:

| Observation | Verified count/estimate |
|---|---:|
| Practice submissions | **13,262** |
| Distinct scored practice problems | **9,373** |
| Sessions with any repeated practice attempt | **459/499 (92.0%)** |
| Sessions with at least one first-wrong → final-correct problem | **442/499 (88.6%)** |
| Sessions with at least one first-correct → final-wrong problem | 4/499 |
| Mean session first-attempt correctness (per problem) | **68.57%** |
| Mean session final-attempt correctness (per problem) | **90.49%** |
| Mean fraction of problems with repeated answers | 26.26% |
| Mean corrected problems per session | 4.20 |
| Mean median resubmission time per session (459 valid) | 64.27 seconds |

Profile `practice_answer_submissions_count` and `practice_problems_final_correct_count` agree **exactly** with reconstructed event-derived totals (mean absolute differences zero). Event traces also record 359 `practice_problem_skipped` events in development, which were not separately modeled. These descriptives are **within-practice** changes after feedback and attempts; they are *NOT independently measured learning gains*.

## Primary E13 models

- **B0 strong:** matched pre-test item correctness, pre-test total and IRT, pre-test skill/subskill success, practice totals/final-correct/submissions, student/tutor message counts, question ID/difficulty, form, tutor arm.
- **N2 event count:** B0 + event-type counts with no order.
- **B1 practice provenance:** N2 + first/last practice correctness, fraction of repeated problems, attempt distribution, within-problem correction and regression counts.
- **S1:** B1 + ordered features but no timing-gap variables.
- **B2 full:** B1 + early vs late correctness, binary practice-correctness transition rates, feedback windows, normalised event bigrams, timing gaps and coverage flags.
- **N1 temporal negative controls:** 20 distinct within-session shuffles of first-attempt outcome ordering and event types/tutor/student placement, preserving B1 first/final correctness and event counts. Shuffles are synthetically generated controls, not physically realistic tutor interventions.

### Four-fold out-of-fold scores (lower Log Loss/Brier, higher AUC better)

| Feature family | Log Loss, C=.03 | AUC, C=.03 | Log Loss, C=.3 |
|---|---:|---:|---:|
| **B0 strong** | 0.524912 | 0.77509 | 0.524361 |
| N2 event counts | 0.525000 | 0.77505 | 0.524665 |
| **B1 practice provenance** | **0.524121** | **0.77588** | **0.523694** |
| S1 ordered, no timing | 0.527093 | 0.77263 | 0.527730 |
| B2 full sequence | 0.527893 | 0.77180 | 0.528707 |

For C=.03: Brier B0=0.174022, B1=0.173560, B2=0.175007.

### Paired task-bootstrap differences in mean item Log Loss (positive = adding features is better)

| Comparison | C=.03, mean [95% CI] | C=.3, mean [95% CI] |
|---|---|---|
| B0 → B1 | **+0.000791** [−0.001345,+0.002877] | **+0.000667** [−0.001696,+0.003038] |
| B1 → B2 | **−0.003773** [−0.006513,−0.001317] | **−0.005013** [−0.008161,−0.002159] |
| B0 → B2 | −0.002981 [−0.006382,+0.000267] | −0.004346 [−0.008286,−0.000519] |

**Findings:** B1's positive point estimate is NOT a statistically secure gain; the 95% CI includes zero at both C values. Adding the full B2 sequence feature set is **worse than B1** in this setting. These results should not be presented as a validated model upgrade or proof that ordered traces contain no information whatsoever.

### Negative temporal controls

| Metric | C=.03 | C=.3 |
|---|---:|---:|
| B2 actual Log Loss | 0.527893 | 0.528707 |
| Median Log Loss across 20 shuffled N1 controls | 0.528667 | 0.529764 |
| Shuffles with worse Log Loss than actual B2 | **17/20** | **16/20** |
| Shuffled-control Log Loss range | 0.527678–0.531205 | 0.528138–0.532595 |

B2 is somewhat better than shuffled sequences, showing a *possible order-related signal*, but **still loses to the unshuffled strong B0 and B1 benchmarks**. This is **not** a passed incremental predictive-validity test. Randomly shuffling event types may create implausible interactions; N1 is a diagnostic, not a causal experiment.

## Post-hoc component ablation (exploratory only)

The full B2 model adds many noisy and correlated temporal features. An exploratory ablation evaluated narrower, interpretable feature families against B0:

| Features | Log Loss C=.03 | Log Loss C=.3 |
|---|---:|---:|
| B0 | 0.524912 | 0.524361 |
| First-attempt correctness | 0.524058 | 0.523350 |
| **Attempt-distribution features only** | **0.523731** | **0.523262** |
| Correction/regression only | 0.524277 | 0.523781 |
| Combined B1 provenance | 0.524121 | 0.523694 |
| B1 + early/late and binary practice transitions | 0.524111 | 0.523861 |
| B1 + all event bigrams | 0.526409 | 0.526516 |
| B1 + feedback trajectory windows | 0.524625 | 0.524424 |
| B1 + time-gap variables | 0.525015 | 0.524611 |

For the attempt-distribution-only family, the **post-hoc** B0→ablation gain at C=.03 is **+0.001181**, task-bootstrap 95% CI **[−0.000408,+0.002904]**; at C=.3: **+0.001099**, 95% CI **[−0.000767,+0.003123]**. Neither excludes zero. Selecting the best after comparing multiple families biases estimated generalization, so these are *hypothesis-generating*, not confirmatory.

## Falsification / scientific rebuttal

1. **Practice gain ≠ independent learning gain:** First-attempt 68.6% vs last-attempt 90.5% is within-practice correction under feedback, not an independent skill outcome or causal improvement.
2. **Incremental signal weak:** B1 is directionally encouraging, but the task-bootstrap interval contains zero. It would be inaccurate to say E13 reliably improves prediction.
3. **No robust benefit from rich sequences:** Temporal/bigram-heavy B2 hurts versus B1; only relative to implausible randomized sequences does it occasionally help.
4. **Mechanisms compete:** Repeated attempts can reflect uncertainty, struggle or motivation; generated practice-problem difficulty is not fully controlled. Event-type distribution can proxy tutor style, not student cognition.
5. **Conditional and adaptive uncertainty:** 3,000 bootstrap CI replicates condition on the model selection/training protocol; two C settings, exploratory ablations and E7–E12 prior experiments mean there is no multiplicity-adjusted or prospectively validated improvement.
6. **Reserved samples not globally clean:** E13 holds 125 task IDs apart, but previous research examined the same public dataset extensively. Do NOT claim new external prospective test.
7. **Observational design:** no causal interpretation of tutoring traces, ability, practice improvements or AI's contribution.

## Decision

**NO-GO for adopting the full E13 temporal representation as a superior final predictive model.** The narrower **first-attempt / attempt-count provenance** feature family is worth a carefully constrained E14 replication, on a genuinely new held-out or external cohort if available, not further hyperparameter searches on the same development folds. This is a defensible scientific *negative + measurement-specific* result.

## Reproduction and source

- [E13 data collector](../experiments/e13_collect_traces.py): pinned official revision, 624 selected sessions, zero transcript text in saved data.
- [E13 feature extractor](../experiments/e13_features.py): content-free practice correction, ordered and 20 null features.
- [E13 evaluator](../experiments/e13_evaluate.py): grouped 4-fold, primary scores, task bootstrap.
- [E13 exploratory ablation](../experiments/e13_exploratory_ablation.py).
- [Synthetic regression tests](../experiments/test_e13_features.py) pass for correctness extraction and null shuffle invariance.
- [Data/completeness audit JSON](E13_feature_audit_2026-10-25.json).
- [Full E13 metrics + 20 controls + comparisons JSON](E13_dev_metrics_2026-10-25.json).
- [Exploratory ablation results JSON](E13_exploratory_ablation_2026-10-25.json).
- Source: [StudentBench public dataset](https://huggingface.co/datasets/handshake-ai-research/studentbench), revision `304c8d63c726e72b60510bba3a44454fc0726721`.

**Privacy:** Raw transcripts were not stored in the reduced cache. Private event trajectories, profile identifiers, posttest outcomes and per-item features are not committed to public GitHub. No E13 model was assessed on the 125 reserved sessions.
