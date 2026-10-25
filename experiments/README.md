# StudentBench reproducible diagnostics

The repository contains **exploratory** benchmarks for GRE Quantitative. Only aggregate results are saved; raw participant data and transcripts must stay outside version control.

## Prepare data and environment

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-research.txt

# Download the official StudentBench dataset following:
# https://github.com/Handshake-AI-Research/studentbench
# The extracted dataset root should contain:
# data/1_main_leaderboard_data/gre_quant/...
# data/question_bank_quant.csv
```

## Experiments

```bash
# Session-total baselines with fourfold session-grouped development evaluation
python experiments/session_baseline.py --data ./data --output ./results/session_baseline.json

# Item-level lexical + event transition baseline
python experiments/item_trace_diagnostic.py --data ./data --output ./results/item_trace.json

# E7: item-level frozen MiniLM sentence embeddings vs detailed pretest + practice
python experiments/semantic_baseline.py --data ./data --output ./results/semantic.json

# E8: session-total neural baseline vs event bag vs GRU vs shuffled-order GRU
python experiments/event_gru.py --data ./data --output ./results/event_gru.json

# E9: concept-to-subskill alignment (requires lesson-plan JSONs)
python experiments/skill_conditioned_e9.py --data ./data --output ./results/e9.json
# E9b: low-dimensional curriculum coverage + alignment checks
python experiments/skill_coverage_e9b.py --data ./data --output ./results/e9b.json
```

E7 and E8 use the same stratified session-level fold partition and same sampled tutor arms **if loaded from the same local data snapshot**. They deliberately have **different targets** (item correctness versus overall post-test score), so their loss values cannot be compared directly.

The semantic encoder is frozen and downloaded by fastembed into `.cache/fastembed`; for offline work, pre-download the model or configure its cache. CPU execution is supported.

## Validity and reproduction notes

- Development results are not confirmatory. Holdout is excluded from fitting, model selection, and analysis. Never tune against the holdout.
- Reported remote pilot used **789/806** fetched sessions. Missing remote fetches mean rerunning with complete downloaded files may change sample counts and metrics. Treat the published numbers as a pilot record, not guaranteed byte-identical reproduction.
- The sample is capped at 62 per tutor arm for E7/E8; use `--per-tutor` to change it, and preregister such changes.
- E7 compares MiniLM + regularized logistic models with a detailed pre-test/item baseline; it does not fine-tune the encoder or explicitly align dialogue segments to assessed skills.
- E8 reduces learning traces to six symbol types and truncates sessions above 256 events; it does not model event semantics or timestamps, and its result measures session-total score.
- Bootstrap intervals are conditional on out-of-fold predictions; they are not nested model-selection confidence intervals.
- No claim that predictive association establishes learning, mastery, or causality.
- **Smoke tests of both scripts passed on synthetic data** as of 2026-10-24. Synthetic test results must never be cited as empirical evidence.

See [research report](../reports/semantic_gru_2026-10-24.md) for grounded numbers and limitations.

## E9 results and validation

E9/E9b inspect **automated concept–subskill correspondence**. The study uses 27 GRE subskill descriptions and AI-generated lesson-plan concept names, which are **not human-labeled equivalents**. A 604-session real-data pilot did not show reliable additional predictive benefit from aligned embeddings or coverage; see [the E9 research report](../reports/E9_skill_conditioned_2026-10-24.md). The next step is the [E9c independent double-annotation protocol](../docs/E9c_annotation_protocol_v0.1.md); it has **not** been executed. Both E9 and E9b scripts compiled and passed end-to-end synthetic smoke tests; they have not yet been rerun against a complete pinned official data snapshot.


## E9c — human-validation pilot (sample generation complete; human ratings pending)

A blinded 120-pair sample has been generated and published from real GRE Quant lesson-plan concept titles. See [annotations guide](../annotations/README.md) and [E9c sampling report](../reports/E9c_sampling_audit_2026-10-24.md).

```bash
# Rebuild blinded pair sample from official locally downloaded data
python experiments/e9c_sample_pairs.py --data ./data --out-dir ./annotation_work

# After independent completion of both rating sheets (D/S/N/U):
python experiments/e9c_agreement.py \
  --annotator-a ./annotation_work/e9c_annotator_A.csv \
  --annotator-b ./annotation_work/e9c_annotator_B.csv \
  --output ./annotation_work/e9c_agreement.json
```

**Important:** No human ratings have been completed. Technical smoke tests with fictitious labels only validate the reliability-analysis script and must not be interpreted as scientific results. Do not copy analyst-only cosine scores into blinded annotation sheets.

## Independent two-GPT labels (optional, billable)

The research repo also includes [one identical prompt](../annotations/E9c_shared_gpt_prompt_v1.md) and a [dual-GPT runner](e9c_dual_gpt_annotate.py) for a separate **model–model agreement** experiment. No paid API requests are made by default. For safe dry-run and instructions to authorize live requests, see [the guide](../annotations/E9c_dual_GPT_execution_guide.md). Not a replacement for human construct-validity annotation.

## E9d — Model disagreement sensitivity and blinded expert construct audit

The 120-item Astra/Gemini model–model agreement has been analyzed beyond a single κ value, including 15,000 GRE-subskill-cluster bootstrap resamples and a sensitivity analysis collapsing S/N. See [E9d report](../reports/E9d_construct_validity_sensitivity_2026-10-24.md).

Run on **your local private original two model-labeled CSVs**:

```bash
python experiments/e9d_model_conflict_stats.py \
  --model-a annotation_work/codex_astra/e9c_annotator_A.csv \
  --model-b annotation_work/antigravity_gemini/e9c_annotator_B.csv \
  --out annotation_work/e9d_conflict_stats.json
```

The **41-pair blinded review** remains unfilled (21 disagreements + 20 controls). A formatted two-axis XLSX was supplied privately to the researcher: record (1) direct mathematical content relation, (2) presence of general strategy, and (3) the original four-class label D/S/N/U, under the **unchanged original E9c codebook**. [Protocol](../docs/E9d_two_axis_expert_review_protocol_v0.1.md).

Only after obtaining genuine independent expert labels, export the `Audit_41` worksheet to CSV and run:

```bash
python experiments/e9d_analyze_expert_review.py \
  --expert-csv annotation_work/e9d_review_filled.csv \
  --model-a annotation_work/codex_astra/e9c_annotator_A.csv \
  --model-b annotation_work/antigravity_gemini/e9c_annotator_B.csv \
  --out annotation_work/e9d_expert_comparison.json
```

The analyzer has passed a smoke test using **fictional** labels but has NOT generated any actual human verification. A single expert reviewer supplies a reference, **not** human–human inter-rater agreement. Original model outputs are not modified or committed.

## E11 — sampling + Astra-silver mapping validity stress test

**Status:** E11 sampling and silver-classifier diagnostic completed, human and new AI labels pending. [Real 400-pair sample](../annotations/templates/e11_pairs_blinded_400.csv), [report](../reports/E11_validated_mapping_sampling_silver_transfer_2026-10-24.md), [step-by-step E11 runbook](../annotations/E11_RUNBOOK.md).

The E11 pairing pool is drawn only from 489 development sessions of a pinned StudentBench revision. The **400 label cells remain blank**. The silver transfer diagnostic shows D F1=0.182 on grouped unseen GRE subskills (only five positive Astra labels); do not interpret 167 model-predicted D labels on the E11 sample as 167 true matches.

Scripts: e11_prepare_mapping_sample.py, e11_silver_risk_audit.py, e11_validate_labels.py and e11_evaluate_agreement.py. Execute annotation in two separate Codex and Antigravity sessions with the frozen [codebook](../annotations/E11_COMMON_LABELING_CODEBOOK.md). Analyst-only strata sidecar and completed labels stay under ignored annotation_work/.

## E12 — Astra-silver mapping / post-test incremental-prediction study

Exploratory E12a grouped OOF silver-label tests and E12b on 456 development sessions (12,312 post-test items) found **no reliable additional Log Loss benefit** from skill-aligned concept-title/message-volume features over the pretest/practice baseline, including versus within-session permuted concept alignment. See [E12 report](../reports/E12_silver_mapping_incremental_prediction_2026-10-24.md) and [exact aggregate E12b metrics](../reports/E12b_Astra_silver_posttest_2026-10-24.json). Full standalone E12a code and synthetic-tested E12b reimplementation were delivered as a private downloadable reproducibility ZIP in the ChatGPT research conversation; the exact E12b execution and local reimplementation have not been independently checked for byte-identical parity.

**Important:** The 400 private GPT-6 Astra labels are SILVER by research assumption, NOT verified human truth. The remote run fully downloaded 582/624 targeted sessions; 126 reserved sessions were not scored. A positive model-label F1 does not imply added posttest predictive validity.

The proposed next gate is [E13 practice-process and temporal evidence protocol](../docs/E13_practice_process_temporal_protocol_v0.1.md), **not yet executed**.

## E13 — Actual event-level practice-process evaluation (2026-10-25)

**Executed**, not just proposed. Source revision `304c8d63c726e72b60510bba3a44454fc0726721`; 624/624 targeted GRE Quant sessions retrieved; **499 development sessions, 13,473 out-of-fold post-test items, 125 unscored reserved**. Four-fold CV groups by `student_id`/task ID.

- B0 strong baseline Log Loss: **0.524912** (C=.03).
- B1 + practice first/final and resubmission provenance: **0.524121**; session-bootstrap benefit CI crosses zero.
- B2 + all ordered/timed events: **0.527893**; significantly worse vs B1 in the conditional task-bootstrap comparison.
- Twenty sequence-shuffled controls have median Log Loss **0.528667**; genuine B2 order sometimes helps over corrupted event orders, **but not enough to beat B0/B1**.
- Exploratory narrow attempt-distribution family reaches **0.523731**, though its cluster-bootstrap CI of incremental gain crosses zero. NO-GO for full B2; restricted E14 replication is only a proposal.
- **No final 125-session reserved test run.** Not a validated causal mastery model.

Complete evidence: [E13 research report](../reports/E13_practice_process_temporal_real_results_2026-10-25.md), [source audit](../reports/E13_feature_audit_2026-10-25.json), [all development metrics and 20 null controls](../reports/E13_dev_metrics_2026-10-25.json), [exploratory ablations](../reports/E13_exploratory_ablation_2026-10-25.json).

Reproduce (Python packages numpy, pandas, scikit-learn, scipy; network for official data):

```bash
python experiments/e13_collect_traces.py \
  --output annotation_work/e13_private_trajectories.json.gz

python experiments/e13_features.py \
  --input annotation_work/e13_private_trajectories.json.gz \
  --output annotation_work/e13_features_private.pkl \
  --audit results/E13_feature_audit.json \
  --shuffles 20

python experiments/e13_evaluate.py \
  --input annotation_work/e13_features_private.pkl \
  --output results/E13_dev_metrics.json \
  --boot 3000

python experiments/e13_exploratory_ablation.py \
  --input annotation_work/e13_features_private.pkl \
  --output results/E13_exploratory_ablation.json

# Synthetic tests never use real student records.
python experiments/test_e13_features.py
```

Private `annotation_work/` contains task IDs, event metadata, post-test outcomes and intermediate features. NEVER commit those private files. Source retrieval and full evaluation were executed in a separate remote environment. The detailed report discloses exploration and missingness assumptions.

## E14 — LOCKED 125-session internal holdout (completed October 25, 2026)

The [E14 protocol](../docs/E14_locked_internal_holdout_protocol_v0.1.md) was committed at `1e868b4685c3012386c8d121ad0f393da4fdf14a` **before** scoring the reserved E13 125 task IDs. The fixed C=0.3 Logistic Regression included the preselected E13 post-hoc attempt-count feature family; E13 development parity was verified to 1e-6 before holdout labels were evaluated.

**Result: no replicated improvement.** B0 held-out Log Loss **0.538238**, attempt-provenance candidate **0.540086**, paired task-bootstrap improvement **−0.001848**, 95% CI **[−0.006090,+0.001470]**. Eighteen of twenty training-only task-block shuffles yielded lower loss than the unshuffled attempt-feature candidate. This is a **negative internal replication**, not external causal validation.

- [Complete E14 report](../reports/E14_locked_internal_holdout_negative_replication_2026-10-25.md)
- [Exact aggregate results and 20 negative controls](../reports/E14_internal_holdout_metrics_2026-10-25.json)
- [Locked holdout runner](e14_locked_holdout.py)
- [Synthetic invariants test](test_e14_locked_holdout.py)

To reproduce on pinned official GRE Quant sessions:

```bash
python experiments/e13_collect_traces.py --output annotation_work/e13_private_trajectories.json.gz
python experiments/e14_locked_holdout.py \
  --input annotation_work/e13_private_trajectories.json.gz \
  --output results/E14_locked_holdout_aggregate.json \
  --bootstrap 10000 --null-seeds 20
python experiments/test_e14_locked_holdout.py
```

No private session-level data or student answer records are committed. Do not tune or rescore on the 125 internal holdout sessions and call it an independent test.

## ND1 — New research direction after E7–E14 (2026-10-25)

**Research pivot:** stop searching for pre/posttest Log Loss lift with concept-title alignment or raw event sequences; assess *observable student conversational acts* and *feedback uptake* as separate educational constructs, with reliability assessed before model training.

- [Scientific redesign report in Vietnamese](../reports/ProcessCognitive_E7-E14_review_ND1_research_redesign_2026-10-25.md)
- [Frozen pilot codebook v0.1](../docs/ND1_behavioral_moves_feedback_uptake_codebook_v0.1.md)
- [Operational runbook for pilot blind double annotation](../docs/ND1_pilot_runbook_2026-10-25.md)
- [Pinned StudentBench real-episode extractor](nd1_extract_feedback_episodes.py)
- [Annotation CSV format validator](nd1_validate_annotations.py)
- [Agreement calculation after two independent labels](nd1_agreement.py)
- [Actual extraction aggregate (no text/PII)](../reports/ND1_real_pilot_extraction_audit_2026-10-25.json)

Real first run: **78/78 GRE Quant sessions retrieved, 1,795 eligible student-turn candidates, 180 UNIQUE unlabeled episodes, 68 distinct sessions, 13 tutor arms.** No gold human labels, no new classifier trained, no behavioral outcome analyzed. Private dialogue texts and sidecars MUST remain in ignored `annotation_work/`. The very first 40-case double annotation is a feasibility test. A separate synthetic test validated the CSV checker and agreement script, but synthetic κ is NOT research data.

To reproduce the 180 real episodes:

```bash
python experiments/nd1_extract_feedback_episodes.py \
  --out annotation_work/new_direction/nd1_pilot_180_PRIVATE.csv \
  --n 180 --per-arm 6
```
