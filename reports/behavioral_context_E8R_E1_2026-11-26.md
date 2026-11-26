# StudentBench research checkpoint — 26 November 2026

**Evidence status:** real-data exploratory E0 source inspection and E8 source-code audit; no new full-cohort ML outcome metrics or human-validated behavioral labels.

## E0 extension, real source-backed convenience sample

Data read from 24 public main-release AI-tutored session transcripts (12 Quant, 12 Verbal), across GPT-5.4-mini, Gemini-3.7-Flash, Opus-5 and Gemma-4-31B configurations. The sample is purposive, not random, and remote files were read from Hugging Face `main` rather than fully hash-verified official snapshot.

| Audit | Observed |
|---|---:|
| Sessions (Quant / Verbal) | 24 (12 / 12) |
| Raw interaction events | 4,516 |
| Nonblank student messages | 564 |
| Student turns (Quant / Verbal) | 291 / 273 |
| Utterances <=7 words | 300 / 564 (53.2%) |
| Continuous `trajectory_position` order | 24 / 24 |
| Adjacent source timestamp decreases | 451 |
| Sessions with >=1 timestamp decrease | 14 / 24 |

Quality boundary: eight sessions were fully reconciled against their 27-item pre/post files; eight additional sessions had profile counts checked; the latest eight were inspected at the transcript level only. **Do not report 24/24 score audits.** Shortness does not establish cognitive ambiguity or context-model superiority.

## Research correction to original E8 GRU design

The existing [E8 source](https://github.com/kieuquy283/ProcessCognitive/blob/main/experiments/event_gru.py) compares static+event bag with static+GRU; the GRU does **not** retain the bag input. Furthermore, the event bag describes the complete sequence while the GRU sees at most the first and last 128 events. Therefore E8 does not isolate incremental value of order.

The corrected E8R design has four arms on the same data and same outcome:
- **M0:** pretest/IRT, practice, message counts, AI tutor/form and total event count;
- **M1:** M0 plus full-session event-type proportions;
- **M2:** M1 plus full-session adjacent transition features;
- **M2-shuffled:** M1 plus transitions extracted from a session-wise count-preserving permutation.

Use identical outer CV folds, tune Ridge only on training folds, estimate paired MAE differences at session level. Comparing M2 with both M1 and M2-shuffled tests a narrower temporal prediction hypothesis. **E8R has been implemented** in `experiments/behavioral_context/controlled_event_ablation.py` with synthetic unit tests in the adjacent `tests/` directory, but **has NOT run on the real full-cohort data**. The standalone snapshot verifier `verify_studentbench_snapshot.py` now supports a strict E0 provenance gate.

## E1 decision

The 24 real sessions yield more than 280 student messages. On the provisional session partition, both Quant and Verbal contain enough turns to satisfy the raw 100-development/40-holdout quotas. But only eight development and four holdout sessions per GRE section would be available: inflated effective sample sizes are a serious concern.

**New E1 gate:** use a source pool with >=40 sessions/section, sample <=5 messages/session, require >=20 development and >=8 locked holdout selected sessions per section, and hide split from annotators. Original human codebook remains **NOT APPROVED**; no kappa/F1 has been computed.

## Engineering verification

The local pilot package passed **25/25 synthetic unit tests**, including correct nested feature construction, a constructed temporal-signal sensitivity test, a snapshot digest verifier, and E1 outcome leakage/context/independence checks. Synthetic fixtures are not empirical StudentBench outcome evidence.

## Next scientific actions

1. Download the official pinned dataset revision `304c8d63c726e72b60510bba3a44454fc0726721`. Verify its published 35,498-file SHA256 manifest before full E0.
2. Evaluate E8R on real GRE Quant **development** sessions; reserve the holdout for preregistered final evaluation.
3. Generate E1 pilot using many distinct sessions; obtain two independent human annotations, adjudicate only development, then freeze ontology.
4. Label full contiguous sessions and evaluate validated behavior distribution vs behavior transitions for posttest prediction, separately from system event order.

**Current blocker:** no full local pinned StudentBench snapshot and no verified human behavioral labels. Never infer educational causality from E8/E8R associations.

Sources: [StudentBench](https://github.com/Handshake-AI-Research/studentbench), [public data](https://huggingface.co/datasets/handshake-ai-research/studentbench), [E8 report](https://github.com/kieuquy283/ProcessCognitive/blob/main/reports/semantic_gru_2026-10-24.md).
