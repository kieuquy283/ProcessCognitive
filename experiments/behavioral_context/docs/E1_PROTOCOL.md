# E1 provisional behavioral-context pilot protocol (v0.1)

**Not approved, not human-labeled.** This document records a proposed construct and a software-ready sampling protocol, not experimental evidence that the constructs are valid.

## Research unit and context
One nonblank student-authored message at a known `trajectory_position`. The response of the AI tutor and earlier student messages are context, not additional student behavior labels. `concept_id` and `practice_problem_id` are reference keys; neither is itself the full task text. Task wording may only be joined when the source provides exact valid linkage and the content was known before the target turn.

## Candidate single-label ontology (unverified)
| Proposed label | Observable criterion | Caution |
|---|---|---|
| ANSWER_REQUEST | Requests a completed answer or solution | Does not prove poor learning or overreliance |
| EXPLANATION_REQUEST | Asks for reasoning, concept, method, or clarification | May overlap verification; record ambiguity |
| REASONING_PRESENTATION | Presents an intermediate argument, calculation, or proposed solution | Mere isolated numeric answer is borderline |
| VERIFICATION | Asks AI to check the student's answer or reasoning | Not every occurrence of 'correct' is verification |
| REVISION | Explicitly modifies prior own reasoning/answer | Do not infer change from tutor reply alone |
| INTERACTION_MANAGEMENT | Coordinates pace, format, navigation or interaction | Very short replies may be unclear |

`UNCLEAR` and `OUT_OF_SCOPE` are allowed annotation dispositions, not validated behavioral states. Keep overlapping interpretations in the rationale rather than making up precedence rules before independent pilot review.

## Sampling
The provisional target is **280 real turns**: 200 development and 80 locked holdout, with 100/40 per GRE section. Partition by session first; sample turns only within those partitions. Enrich very short turns for stress testing without using this convenience sample to estimate population prevalence. **Never** use pretest, posttest, gains or model predictions to select or label utterances.

## Annotation and evaluation
Two human annotators independently fill local A/B sheets and preserve disagreements. Review construct ambiguity; freeze codebook on development; do not adapt it to maximize held-out agreement. Compare C0 student-only, C1 + last AI response, C2 + three prior turns, C3 + valid prior task context on exactly the same locked reference turns. Report raw agreement, Cohen kappa, uncertain/abstain rate, Macro-F1 and per-class F1 with session-aware uncertainty where feasible.

**Critical gate:** 280 isolated annotation units do not provide complete behavioral sequences. E4 requires complete contiguous session labeling; E5 requires separate held-out score prediction evaluation. Current eight-session convenience audit has 228 student turns: E1 has not run on a 280-row real sample.

Raw texts, participant-level records and annotator files must remain in ignored `annotation_work/`, never on public GitHub. Sources: StudentBench https://github.com/Handshake-AI-Research/studentbench ; StudyChat https://arxiv.org/abs/2503.07928 ; TurnStyle https://doi.org/10.1145/3772318.3790459 .


## E1 revision (2026-11-26): session-cluster dependence

The original 280-turn pilot quota was attainable on a 24-session convenience slice, but that was not sufficient independence for reliable confidence intervals. Revised sampler now requires at least **40 source sessions in each GRE section**, caps selected turns at **five per session**, and checks representation of **20 development and 8 held-out sessions per section**. Development/holdout designation is stored in `E1_split_manifest_PRIVATE.csv` and not shown to annotators. Human independent annotations and a pinned full dataset remain required.
