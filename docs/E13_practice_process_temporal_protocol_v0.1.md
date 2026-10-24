# E13 — Practice-process evidence vs strong practice baseline: prospective protocol v0.1

**Status:** DESIGN ONLY, not executed. Motivated by E12b's negative result for concept-title alignment using GPT-6 Astra **silver** labels. Do not report E13 gains before the actual evaluation.

## Why E13

E12a learned Astra's D/S/N/U labels better than fixed lexical rules, but E12b showed **no incremental posttest predictive gain** relative to pretest+practice baseline; 400-label alignment did not beat within-session concept shuffling. E12c found that only 177/12,312 posttest item observations had an exact Astra-silver D concept pair with student-message activity.

The tested features were title matching and message volume. They *did not measure student feedback uptake or evidence quality*. The StudentBench trajectory CSV includes `event_type`, `trajectory_position`, `timestamp_elapsed_seconds`, `concept_id`, `practice_problem_id`, `is_correct`, `answer_attempt_number`, `student_message`, `ai_tutor_message`, and practice submission events. These allow an outcome-free process-level test. The published StudentBench paper also found correlations between practice correctness and learning gains, making detailed practice proficiency a necessary strong control rather than a novel standalone signal.

## Questions, target and preregistered outcomes

**RQ1:** After controlling for detailed pre-test and practice totals/final-correct, do ordered *practice transitions* from wrong to correct add predictive value for independent post-test item correctness?

**RQ2:** Do time-ordered behavioral transitions and early→late practice changes add value beyond counts of the same events?

**RQ3 (negative control):** Does preserving counts but permuting within-session order destroy whatever signal is found?

Primary: item-level **Log Loss**; secondary Brier, AUC, reliability/calibration. Main inference: paired **session-level bootstrap** Log Loss difference, not independent-item bootstrap. No causal claims.

## Fixed data and eligibility

Use StudentBench GRE Quantitative with a **pinned dataset commit**, record the complete eligible session list and actual retrieval failures; never use outcome-dependent exclusion. Primary feature timestamps are within tutor-interaction trajectory, before independent posttest. Keep session IDs, raw transcripts and test labels outside public GitHub.

Split sessions before any outcome modeling, grouping as appropriate by task/session and, if linkage exists, by student across sessions. Do not claim a globally untouched holdout: E7–E12 adapted on overlapping data. A genuinely new/external or prospectively sampled test is needed for confirmatory conclusions.

## Feature families

**B0: existing strong baseline** — pre-test score and IRT, matched pre-test question correct, pretest skill/subskill correctness, item ID/difficulty, model arm and form, practice problems attempted, practice final-correct count, practice answer submissions, student/tutor message totals.

**B1: outcome-free practice provenance**, computed from `practice_answer_submitted` grouped by `practice_problem_id` and ordered by `trajectory_position`, with missingness indicators:
- accuracy of FIRST attempt per unique practice problem, and of FINAL attempt; distribution of attempts/problem;
- number/fraction of corrections (first wrong → final correct) and regressions (first correct → final wrong);
- fraction with repeat attempts; per-problem first-attempt vs final-attempt discrepancy;
- distinct problems attempted and ratio of wrong answers requiring feedback;
- **prevent redundancy**: explicitly control the total/aggregate final-correct and submission counts in B0.

**B2: sequence features**, not just practice totals:
- early vs late practice-first-attempt correctness and difference, with denominator/coverage indicators;
- transition counts among ordered event classes (practice shown, student answer, tutor feedback, student message) and normalized bigrams;
- student reply between feedback and resubmission, correction on next attempt;
- time gaps/response latency where recorded; cap long waits and report missingness.

**B3 (separate hypothesis): semantic *quality* of student explanation**; require an independently defined, human-reviewed codebook. Do not use unvalidated concept titles or LLM labels as if they were mastery.

## Planned comparisons and falsification

| Arm | Predictors | Purpose |
|---|---|---|
| B0 | Pretest + matched item + practice totals + message counts | Strong benchmark |
| B1 | B0 + first/final practice provenance | Incremental correctness evidence |
| B2 | B1 + ordered transitions + early/late progress | Incremental temporal signal |
| N1 | B1 + **time-shuffled** ordered features within session, 20 independent seeds, same event counts | Control for spurious sequence effects |
| N2 | B0 + event counts only, excluding temporal order | Measure effect attributable to volume |
| S1 | B2 excluding high-missingness temporal variables | Robustness to timeline completeness |

Fit preprocessors inside development folds. Keep model family initially regularized logistic; only escalate to GRU/transformer if interpretable sequence test has a replicated gain. Report paired bootstrap interval for B1–B0, B2–B1 and B2–N1; analyze matched-pretest wrong vs correct strata without cherry-picking.

**Go criterion:** A positive repeatable B2 gain relative to both B0 and count-preserving permutations with a clear measurement mechanism. Otherwise report the rigorously controlled negative result rather than adding model complexity.

## Threats to validity

- All tutoring/practice evidence is observational, not randomized.
- First-attempt correctness depends on generated practice-item difficulty, tutor arm and task content.
- Some practice problems are created mid-session; account for `problem_origin` and possibility of skipped, missing or rejected attempts.
- Feedback and corrections may be recorded differently across arms; quantify event missingness per arm.
- Session duration and message volume may proxy motivation, not knowledge.
- An event-level temporal model is not automatically a cognitive ontology; avoid mastery interpretations without construct validation.
- Adaptive model selection from E7–E12 raises risk of researcher degrees of freedom. Mark E13 as exploratory unless a new untouched evaluation source is available.

## Source

- [StudentBench data and field definitions](https://huggingface.co/datasets/handshake-ai-research/studentbench).
- [StudentBench scientific paper](https://arxiv.org/abs/2609.28470).
- [E12 report](../reports/E12_silver_mapping_incremental_prediction_2026-10-24.md).
