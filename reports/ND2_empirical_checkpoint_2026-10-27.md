# ND2 empirical checkpoint — 2026-10-27

**ND2 remains blocked, NOT failed.** The official complete StudentBench dataset and independent Astra/Claude ND2 annotations were not available in this environment. No 280-real-episode ND2 result exists. Synthetic ND2 sampling/evaluation smoke tests passed, but these are not research data.

## Empirical findings from the genuine ND1 pilot (40 aligned records)
Astra is treated as a **conventional reference**, not human-validated ground truth.

| Metric | Claude vs Astra | Gemini vs Astra |
|---|---:|---:|
| Primary accuracy | 32/40 = 80% | 30/40 = 75% |
| Uptake accuracy | 38/40 = 95% | 33/40 = 82.5% |
| Joint accuracy | 32/40 = 80% | 25/40 = 62.5% |
| Primary macro-F1, observed classes | 0.754 | 0.773 |
| Uptake macro-F1, observed classes | 0.860 | 0.690 |

Claude joint accuracy Wilson 95% CI: **0.652–0.895**. Exact paired McNemar for joint correctness Claude vs Gemini: p=0.0391 unadjusted, **p=0.1172 Holm-adjusted** across primary, uptake and joint outcomes. No robust superiority claim.

Post-hoc confidence gating: Claude high only **11/11**, coverage 27.5%, Wilson CI for conditional accuracy 0.741–1.000. High+medium **27/31**, coverage 77.5%, accuracy 87.1% (CI 0.712–0.949). Selective prediction remains unvalidated outside the pilot.

Context sensitivity, exploratory joint accuracy: missing previous excerpt 8/11 vs present 24/29; tutor context of exactly 950 characters 5/5 vs other lengths 27/35; student turns <=10 characters 9/9 vs longer 23/31. These tests are underpowered and no causal/quality inference is justified.

Astra reference class support: primary AK=6, AN=10, CQ=3, HR=7, OT=1, RE=8, VE=5; uptake AC=18, AP=19, NO=0, NR=1, UN=2. Sparse/absent labels forbid robust rare-class claims.

## Critical reproducibility gates
1. Obtain and pin the full official StudentBench release locally; the remote dataset was not downloadable in the analysis runtime.
2. Reconstruct ND1 source-session IDs; opaque NV1 IDs do not prove session-disjointness from newly generated ND2 IDs.
3. Freeze the actual ND1 codebook, prompts, model IDs and annotation settings; authenticate model provenance.
4. Use independent, blinded Astra and Claude annotation on 200 randomly selected samples and 80 separate challenge cases.
5. Report random and challenge scores separately; stratify sparse labels, attach uncertainty intervals; no inflated GO based on pilot or synthetic tests.
6. Avoid committing raw tutoring text, participant-level trajectories, model-labeled episode CSVs, or private data.

**Scientific judgment:** ND1 supports further pilot verification only. It does not yet establish behavioral construct validity, useful downstream learning-outcome prediction, or ND2 generalization. Next decision on ND2 must await genuine external-sample evidence.

Full reproducibility files and detailed local report are held outside the GitHub repository pending review.
