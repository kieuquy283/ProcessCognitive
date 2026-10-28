# ND2 — Context exposure depends on unit of analysis (2026-10-28)

**Status:** An additional real-data, descriptive methodological experiment has been completed. **Not an ND2 Astra–Claude annotation or accuracy result.**

## Source and experiment
Official StudentBench dataset commit `304c8d63c726e72b60510bba3a44454fc0726721`.

Sample: 24 authentic GRE tutoring trajectories inspected previously (4 sorted session folders in each of 3 chosen AI-tutor arms per GRE domain). 464 nonblank `student_message` turns were available. The sampled sessions are a convenience subset, NOT a probability sample of all StudentBench.

For each message, count accumulated nonblank `ai_tutor_message` text since the preceding student message, joined with two newlines. Flag contexts longer than 950 characters. The binary outcome is context-length exposure, NOT the correctness of behavioral annotations.

Compare:
- **Turn-weighted:** total exposed turns divided by total student turns.
- **Session-weighted:** average of each session's own exposure rate, giving each session equal weight.
- Bootstrap 10,000 times by sampling sessions with replacement; report descriptive variation only, not population uncertainty.

## Actual results

| Stratum | Sessions | Student turns | Turn-weighted | Session-weighted | Difference |
|---|---:|---:|---:|---:|---:|
| GRE Quant | 12 | 282 | 52.13% | 67.58% | +15.45 pp |
| GRE Verbal | 12 | 182 | 81.87% | 85.42% | +3.55 pp |
| All | **24** | **464** | **63.79%** | **76.50%** | **+12.71 pp** |

Descriptive session-bootstrap 95% ranges for the difference in points: Quant +2.35 to +24.14; Verbal +0.15 to +6.34; all +2.88 to +21.37. These ranges **do not correct sample selection bias** and should not be described as population confidence intervals.

Sessions contributed between **4 and 58 turns**; unequal conversational lengths explain why these estimands differ. The finite-sample Kish effective number of equally weighted sessions under *turn* weighting is approximately 15.0 out of 24 (descriptive, not a formal independent sample size).

## Scientific implications
1. ND2 selecting one turn per session estimates a **session-weighted target**; any claim about a randomly selected **turn** requires an independently designed turn-weighted evaluation, with clustering respected.
2. A reported 950-character exposure rate has different meaning under the two estimands. This matters for the proposed full-context vs truncation ablation.
3. Neither weighting rate proves the effect of truncation on label quality. A matched controlled annotation ablation is still required.
4. Sampling was purposive and the 24-session results must not be extrapolated to all 2,139 source AI session directories.

## Reproduction
The repository now includes:
- `experiments/nd2_fetch_studentbench.py` — fetch the pinned original trajectories into ignored `data/`, write `.studentbench_revision` locally.
- `experiments/nd2_session_aggregate.py` — write **private per-session aggregate rows** to `annotation_work/nd2/context_session_aggregate_private.csv`.
- `experiments/nd2_session_weighting.py` — print session/turn weighting comparison with descriptive resampling.

```bash
python -m pip install huggingface_hub pandas numpy
python experiments/nd2_fetch_studentbench.py
python experiments/nd2_session_aggregate.py --data data/studentbench
python experiments/nd2_session_weighting.py annotation_work/nd2/context_session_aggregate_private.csv
```

The local aggregate CSV remains outside version control. The ND2 sampling/evaluation implementation is now committed as `experiments/nd2_pipeline.py`, together with three synthetic-only regression tests. The local code has passed all three tests. These tests do not establish model performance on authentic ND2 annotations. The private ND1 provenance mapping is still required.

## Current ND2 evaluation status
- Official frame discovery: 2,139 AI-arm session *directories* (not all certified eligible).
- Authentic limited source-data audits: completed.
- Certified session-disjoint real 200 random + 80 challenge samples: **not completed**.
- Independent verified Astra and Claude outputs on those 280 records: **not completed**.
- ND2 out-of-sample accuracy and macro-F1: **not measured**.

Next gates: authoritative ND1 episode-to-source mapping, local complete pinned download, frozen codebook/prompt + exact model IDs, blind independent annotation. Until then **ND2 is PENDING**, not PASS.
