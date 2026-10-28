# ND2 authentic execution checkpoint — 2026-10-28

**Scope:** Official StudentBench GRE AI tutoring main-leaderboard trajectories pinned to `304c8d63c726e72b60510bba3a44454fc0726721`. These are **genuine source-data experiments**, but not an Astra–Claude ND2 annotation/evaluation.

## Experiment 1: Full source census — PASS
Success: https://github.com/kieuquy283/ProcessCognitive/actions/runs/40554114287

- **2,139/2,139** official AI-arm session trajectory CSVs readable with nonblank student chat (Quant 1,139; Verbal 1,000).
- **332,430** total events, **52,646** nonblank student chat turns, **64,556** practice-answer-submission events.
- Tutor context since prior chat >950 characters in **26,892/52,646 = 51.08%** turns: Quant **13,967/33,989 = 41.09%**; Verbal **12,925/18,657 = 69.28%**.
- The earlier *purposive* 24-session subset had 63.79% above the cap, **12.71 pp higher** than the whole-source result: the earlier pilot was not representative.
- Among 12 tutor arm configurations shared exactly between Quant and Verbal, Verbal had the higher context exposure proportion in **all 12**; this is descriptive, not causal.

## Experiment 2: Source-driven sampling preflight — PASS (technical only)
Success: https://github.com/kieuquy283/ProcessCognitive/actions/runs/40556663031

- Fixed seed `27102026`: **200** session-random candidate episodes (Quant 107 / Verbal 93), **80** separately selected lexical-challenge episodes (Quant 32 / Verbal 48); each of the 280 sampled candidate turns came from a distinct session.
- Candidate pools encountered sequentially: coordination 168; reasoning/verification 236; help/clarification 483; reaction/feedback 235. Chose 20 from each, with no session overlap inside the preflight.
- **ND1 source session exclusions were NOT applied.** This is a sampling-feasibility run with no row-level output released, **not** a certified independently held-out ND2 annotation set.
- An initial CI attempt failed due to missing pandas/sklearn dependencies; after fixing the workflow, the complete download + audit + preflight succeeded.

## Experiment 3: Genuine ND1 label dependency — developmental
- Astra conventional reference, 40 rows: Claude primary accuracy **32/40 = 80%**, uptake **38/40 = 95%**.
- Reference act↔uptake mutual information **0.6455 nats**, exploratory label-permutation p≈0.0001.
- LOOCV uptake inference with Astra reference primary act **34/40 (85%)** (oracle) and with Claude-predicted primary act **31/40 (77.5%)** (non-oracle); direct Claude uptake is **38/40 (95%)**. McNemar direct vs non-oracle p=0.015625 unadjusted, exploratory.
- Uptake observed-label Macro-F1 **0.860** on 4 of 5 classes. `NO` has reference support zero; fixed-five-label zero-filled sensitivity is **0.688**, not evidence of model failure on nonexistent `NO` test instances.

## Scientific decision
**GO for source access and sampling feasibility. PENDING for scientific ND2 performance.** Full-context 950-character ablation is motivated but not yet executed; practice submissions do not inherently prove feedback uptake. Challenge-set lexical selection changes domain balance and must never be pooled unweighted with the random-set performance.

Before publishing ND2 accuracy/F1, independently verify ND1→source-session mapping, freeze the exact codebook/prompt/model provenance, securely produce 280 independent blinded annotation inputs *outside GitHub*, invoke actual Astra/Claude annotators, then evaluate random and challenge separately. No such 280-episode model predictions have been produced.

Reproduce/check aggregates:
- `reports/ND2_full_frame_aggregate_2026-10-28.json`
- `reports/ND2_sampling_preflight_2026-10-28.json`
- `reports/ND2_ND1_label_dependency_checkpoint_2026-10-28.md`

Only aggregate counts and scripts were committed; no participant/session-level rows or tutoring text.
