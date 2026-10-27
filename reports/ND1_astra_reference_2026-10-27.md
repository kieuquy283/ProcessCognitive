# ND1 — Astra-reference annotation evaluation (2026-10-27)

**Status:** Exploratory pilot; 40 StudentBench student-turns, not session-level independent evidence. Astra labels are a **conventional reference**, not independently validated human ground truth. The supplied filename “ClaudeOpus55” does not independently authenticate the model version.

## Data and protocol

- 40 aligned episode IDs; Astra, Claude, and historical Gemini input text and order match.
- 11/40 records lack `previous_student_excerpt`; 5/40 tutor contexts have exactly 950 characters, suggesting possible truncation.
- Annotate one student turn with limited context: `primary_act` (AK, AN, CQ, HR, OT, RE, VE) and `feedback_uptake` (AC, AP, NO, NR, UN).
- Claude is evaluated against Astra; Gemini is retained only as a historical comparator. Prompt and model-version equivalence is not established.

## Results

| Metric | Claude vs Astra | Gemini vs Astra |
|---|---:|---:|
| Primary-act accuracy | **80.0% (32/40)** | 75.0% (30/40) |
| Primary-act macro-F1 (reference-supported classes) | 0.754 | **0.773** |
| Primary-act Cohen's kappa | 0.762 | 0.701 |
| Feedback-uptake accuracy | **95.0% (38/40)** | 82.5% (33/40) |
| Feedback-uptake macro-F1 (reference-supported classes) | **0.860** | 0.690 |
| Feedback-uptake Cohen's kappa | 0.915 | 0.715 |
| Joint exact accuracy | **80.0% (32/40)** | 62.5% (25/40) |

### Per-class Claude results

| Dimension | Label | Astra support | Claude predicted | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|---:|
| primary_act | AK | 6 | 3 | 1.000 | 0.500 | 0.667 |
| primary_act | AN | 10 | 9 | 1.000 | 0.900 | 0.947 |
| primary_act | CQ | 3 | 4 | 0.750 | 1.000 | 0.857 |
| primary_act | HR | 7 | 6 | 1.000 | 0.857 | 0.923 |
| primary_act | OT | 1 | 4 | 0.250 | 1.000 | 0.400 |
| primary_act | RE | 8 | 6 | 0.833 | 0.625 | 0.714 |
| primary_act | VE | 5 | 8 | 0.625 | 1.000 | 0.769 |
| feedback_uptake | AC | 18 | 16 | 1.000 | 0.889 | 0.941 |
| feedback_uptake | AP | 19 | 19 | 1.000 | 1.000 | 1.000 |
| feedback_uptake | NO | 0 | 0 | N/A | N/A | N/A |
| feedback_uptake | NR | 1 | 3 | 0.333 | 1.000 | 0.500 |
| feedback_uptake | UN | 2 | 2 | 1.000 | 1.000 | 1.000 |

The reference distribution for feedback is dominated by AC/AP (37/40, 92.5%). NO has zero support; OT and NR have one reference sample each. No class-level claim for these rare classes is robust.

### Paired exact McNemar: Claude vs Gemini

| Outcome | Claude only correct | Gemini only correct | Two-sided exact p | Holm-adjusted p (3 outcomes) |
|---|---:|---:|---:|---:|
| primary_act | 5 | 3 | 0.7266 | 0.7266 |
| feedback_uptake | 5 | 0 | 0.0625 | 0.1250 |
| joint exact | 8 | 1 | 0.0391 | 0.1172 |

The apparent joint improvement does **not** survive the stated three-outcome Holm correction; the 40-sample comparison is exploratory.

## Error audit (row numbers only; no transcript or episode identifiers)

- Rows **8, 20, 30**: Astra `AK` → Claude `OT` (three errors).
- Rows **14, 28**: `RE` → `VE` (two errors).
- Row **26**: `HR` → `VE`; row **27**: `RE` → `CQ`; row **32**: `AN` → `RE`.
- Feedback uptake differs at rows **8, 20**: Astra `AC` → Claude `NR`.

### Claude confidence as a retrospective selection signal

| Confidence | n | Joint correct | Joint accuracy |
|---|---:|---:|---:|
| high | 11 | 11 | 100.0% |
| medium | 20 | 16 | 80.0% |
| low | 9 | 5 | 55.6% |

Excluding low-confidence items retrospectively gives 27/31 = 87.1% joint accuracy at 77.5% coverage. This is **not** an independently validated rejection policy or calibrated probability.

## Scientific interpretation and next step

**Decision: proceed to an ND2 out-of-sample validation pilot, not publication-grade validation.** Freeze annotation prompts and codebook before ND2. Separate session-level samples and report random and challenge subsets separately. Use small blinded human review for construct validity if possible. Do not claim that agreement with Astra proves ontology correctness, learning gains, or causal impact.

## Reproduce locally (do not commit record-level outputs)

Store the three input files under `annotation_work/nd1/` (ignored by Git):

```bash
python -m pip install -r requirements.txt
python experiments/nd1_astra_reference_eval.py
```

Expected outputs live under `results/nd1/` (also ignored): aggregate `metrics.json`, `per_class.csv`, confusion matrices, and a **local-only** `errors_local_only.csv` containing episode identifiers. Inputs and row-level outputs must never be committed.
