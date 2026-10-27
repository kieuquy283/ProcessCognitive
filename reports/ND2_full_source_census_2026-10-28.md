# ND2: complete real-data StudentBench AI-tutoring source census (2026-10-28)

**Data-only empirical milestone; NOT a 280-sample Astra–Claude accuracy experiment.**

Source: official Hugging Face `handshake-ai-research/studentbench`, revision `304c8d63c726e72b60510bba3a44454fc0726721`. Successful run: https://github.com/kieuquy283/ProcessCognitive/actions/runs/40554114287 . The full by-arm aggregate is `reports/ND2_full_frame_aggregate_2026-10-28.json`. No participant-level rows were committed.

## Actual complete published AI-arm trajectory census

| Measure | Quant | Verbal | Total |
|---|---:|---:|---:|
| CSV files and source session directories | 1,139 | 1,000 | **2,139** |
| Eligible source sessions (>=1 nonblank student_message) | 1,139 | 1,000 | **2,139** |
| Event rows | 179,077 | 153,353 | **332,430** |
| Nonblank student_message events | 33,989 | 18,657 | **52,646** |
| Practice answer submitted events | 31,164 | 33,392 | **64,556** |
| Tutor context >950 chars | 13,967 | 12,925 | **26,892** |
| Percent of student turns >950 chars | **41.09%** | **69.28%** | **51.08%** |

Tutor context concatenates nonblank tutor messages *since the preceding student_message*, joined with two newline characters. Length is in **characters**, not tokens. This gives the proportion whose context would be shortened by an absolute 950-character cutoff; it **does not** measure any change in label accuracy.

## Capacity of overlapping keyword-defined challenge pools
Source sessions containing **at least one** candidate student turn: coordination **1,408**; reason/verification **1,498**; help/clarification **1,934**; reaction/feedback **1,653**. These counts overlap, measure *words*, not true behavioral labels, and are not necessarily the same as the capacity **after choosing one random turn per session**. A separate full-data preflight workflow tests 200+80 selection feasibility.

## Scientific corrections and caveats
- Earlier 24 **purposively chosen** sessions showed 296/464 = **63.79%** context exposure; the full frame yielded **51.08%**, a **12.71 percentage-point lower** true source-scope proportion. This is strong evidence of convenience-sample sensitivity, not an estimate of annotation improvement.
- The 2,139 sessions are all eligible under the nonblank-chat rule, but ND1 source-session provenance must be reconstructed and independently checked to certify ND2 holdout independence.
- The 64,556 practice submissions mean that a chat-only ontology does not capture the complete observable trace; **submission is not equivalent to feedback uptake**.
- Whole-frame counts are an observed census for the defined *published AI-arm main-leaderboard trajectories*, not a generalization to unreleased/other StudentBench sessions. Across domains and tutor arms, distributions may be confounded.
- **No independent Astra/Claude ND2 labels have been produced**, so ND2 accuracy, Macro-F1, generalization and educational construct-validity remain **PENDING**.

**Decision:** Source-data availability, all-file parsing and eligibility **PASS**; ND2 confirmatory annotation **PENDING**.
