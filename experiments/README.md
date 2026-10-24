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
