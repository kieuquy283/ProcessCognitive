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
