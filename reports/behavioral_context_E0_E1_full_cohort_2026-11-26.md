# E0 full AI-cohort audit and E1 context readiness — StudentBench
**Date:** 2026-11-26. **Evidence:** GitHub Actions run [45752503902](https://github.com/kieuquy283/ProcessCognitive/actions/runs/45752503902), both jobs completed successfully. **Scope:** selectively downloaded AI-tutored GRE Quant and Verbal data from requested HF revision `304c8d63c726e72b60510bba3a44454fc0726721`. Full 35,498-file official snapshot SHA256 **NOT VERIFIED**.

## E0 — source record integrity
| QA | Observed |
|---|---:|
| Quant AI sessions / Verbal AI sessions | 1,139 / 1,000 |
| Total AI sessions with profile / pre / post / trajectory checks passed | 2,139 / 2,139 |
| Raw interaction events | 332,430 |
| Nonempty student messages / AI tutor messages | 52,646 / 123,968 |
| Sessions with at least one adjacent event-timestamp reversal | 1,566 |
| Adjacent timestamp reversals | 36,425 |
| Failed sessions under E0 QA rules | 0 |

Checks: assessment file has 27 distinct item IDs; recomputed pretest and posttest correctness totals match profile scores; gain equals post-pre; sequential trajectory positions are consecutive; nonempty student/AI message counts reconcile with profile.

**Caution:** E0 passed a structural/score QA checklist, not a complete data provenance SHA256 audit. Source timestamp reversals mean do not sort behavior traces by timestamp alone.

## E1 — causally prior context extraction (conservative)
| Gate or content | Quant | Verbal | Total |
|---|---:|---:|---:|
| Student turns accepted for candidate extraction | 31,332 | 17,427 | 48,759 |
| Prior AI reply found among six preceding dialogue entries | 31,318 | 17,418 | 48,736 (99.95%) |
| Any preceding dialogue history found | 31,321 | 17,418 | 48,739 (99.96%) |
| Practice question text linked from earlier `practice_problem_shown` | 30,273 | 16,547 | 46,820 (96.02%) |
| Utterance length ≤ 7 whitespace-separated words | 19,931 | 7,646 | 27,577 (56.56%) |

The E1 extractor's **strict timestamp rule** excluded **185/2,139 sessions (8.65%)** if *any* event timestamp was >= `posttest_started_elapsed_seconds`, even if the event was not a student message. It retained **1,954/2,139 sessions (91.35%)** and **48,759/52,646 student messages (92.62%)**. The original E0 audit is not contradicted: E0 validates scores and source structure, whereas E1 has a stricter causal timestamp cutoff. Whether some exclusions are unnecessarily conservative is **unresolved**, under separate aggregate-only diagnosis.

## E1 — independent annotation sampling
The script produced an **unlabeled** sample of 280 genuine student turns: 200 development / 80 locked holdout; Quant 100/40 and Verbal 100/40. Selected turns come from **262 distinct sessions** (Quant dev/holdout 92/37, Verbal dev/holdout 98/35), with no overlap in sessions between dev and holdout and ≤5 sampled turns/session. The selected-key SHA256 is `7f17e5920d9ef6ba00f24d7496478bc84ae79dd7340082d0076c0c5180246cf3`.

The annotator A/B sheets include real dialogue and are **not uploaded to public artifacts or GitHub**. They were generated in an ephemeral CI workspace; the durable result currently available is the aggregate sampling manifest, **not an accessible completed human annotation file**. The candidate six-label codebook is **NOT APPROVED**. No κ, α, Macro-F1, or behavioral outcome MAE has yet been measured.

## Research interpretation and next gates
1. **RQ1 input feasibility PASS (partial):** recent AI replies and prior task text are available for nearly all accepted source messages; context's benefit for classification is a **hypothesis**, not established.
2. **Time boundary diagnosis pending:** inspect event types and causal boundary on the 185 excluded sessions. Do not silently relax leak prevention.
3. **Human validation NOT STARTED:** obtain local private copies of unlabelled A/B sheets, two independent humans, refine codebook only on 200 dev units, freeze before 80 heldout checks.
4. **E2 conditional:** compare text-only vs last AI response vs last three dialogue turns vs causally available GRE question on the SAME human reference labels, macro-F1 and per-class F1 with session-level sensitivity.
5. **E4/E5 conditional:** contiguous whole-session behavioral sequences are required; sampled 280 isolated turns cannot establish transition frequencies or posttest associations.
6. **E8R prior result:** system-event sequence transitions failed to provide incremental development MAE improvement beyond system-event counts on 634 Quant development sessions; this does **not** test validated pedagogical behavior sequences.

No causal educational effect is claimed. Source: [StudentBench official](https://huggingface.co/datasets/handshake-ai-research/studentbench), [GitHub experiment run](https://github.com/kieuquy283/ProcessCognitive/actions/runs/45752503902).
