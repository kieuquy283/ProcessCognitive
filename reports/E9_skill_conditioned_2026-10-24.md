# E9 — Skill-conditioned learning evidence: controlled pilot and negative results

**Date:** 2026-10-24. **Status:** exploratory development results; **not confirmatory** and not causal.

## Research question

Does selecting AI tutoring turns **relevant to the GRE subskill being assessed** add predictive value beyond a detailed pre-test + practice baseline when forecasting independently completed post-test items?

## Data and integrity

- Source: [StudentBench public GRE Quantitative data](https://huggingface.co/datasets/handshake-ai-research/studentbench), across 13 AI tutor configurations.
- Balanced availability-based sampling: **624 sessions selected**, **604 successfully downloaded**; **20 remote retrieval failures** not assumed randomly missing.
- **473 development sessions**, **131 predefined holdout sessions not evaluated**.
- **12,771 independent-assessment item outcomes** within development; all splitting and bootstrapping by session, **not by item**.
- **2,267 concept instances** in development, **2,043 with at least one student message**.
- Each trajectory event carries `concept_id`. Concepts are named in the *generated lesson plan*, not drawn from the same ontology as GRE assessment `subskill`.
- Frozen `sentence-transformers/all-MiniLM-L6-v2` model (384 dimensions).
- For each post-test item, cosine similarity between its public GRE subskill label and the names of lesson-plan concepts selects/weights concept-level student/tutor transcript embeddings. Use temperature 0.1 for weights, and a normalized pooled whole-session embedding as a comparable baseline. For each session, randomly permute the correspondence between concept embeddings and their label weights as a negative control.
- Strong baseline controls: pre-test total score, pre-test IRT, matching pre-test paired item correctness, pre-test accuracy by skill and subskill, GRE question ID/difficulty, AI tutor, form, practice counts/credits and message counts.
- Regularized item-level logistic regression with 4-fold grouped development CV. Regularization options C=0.03 and C=0.3 examined; **no heldout used for selection**.

## E9 results — C=0.03

| Feature set | Log Loss ↓ | AUC ↑ |
|---|---:|---:|
| Baseline (pre-test + practice + message counts) | **0.529720** | **0.77135** |
| + Pooled student embedding | 0.533444 | 0.76785 |
| + Skill-conditioned student embedding | 0.532304 | 0.76877 |
| + Skill-conditioned student embedding with concept contents mismatched | 0.531730 | 0.76956 |
| + Pooled tutor embedding | 0.530755 | 0.77026 |
| + Skill-conditioned tutor embedding | 0.531658 | 0.76929 |

Paired session-bootstrap estimated **Log Loss reduction** (positive is beneficial; exploratory percentile 95% CI):

| Comparison | Delta | 95% CI |
|---|---:|---|
| Baseline → pooled student | -0.003724 | [-0.006678, -0.000772] |
| Baseline → skill-conditioned student | **-0.002584** | [-0.004941, -0.000057] |
| Pooled student → skill-conditioned student | +0.001140 | [-0.000746, +0.003037] |
| Mismatched student concepts → skill-conditioned student concepts | -0.000573 | [-0.002078, +0.000938] |
| Pooled tutor → skill-conditioned tutor | -0.000903 | [-0.002272, +0.000379] |

At C=0.3, the baseline Log Loss was 0.529159; pooled student 0.549542; skill-conditioned student 0.545643; mismatched alignment 0.545117; pooled tutor 0.541010; skill-conditioned tutor 0.539874. The negative difference widens with weaker regularization.

**Finding:** weak evidence that skill conditioning is preferable to unconditioned pooled embeddings, but **no statistically compelling improvement over the strong baseline**. Importantly, **mismatching concept–skill assignments does not reliably hurt**; this fails a key falsification test for a meaningful mapping.

## E9b — Try lightweight, interpretable coverage before high-dimensional embeddings

To test whether 384-dimensional representations merely overfit, we reran the **same 473-session development sample** with interpretable per-item features:

- curriculum/concept count;
- cosine relevance (maximum concept-title/subskill similarity);
- student/tutor message counts weighted by concept-title relevance;
- permuted-concept message-volume negative control.

| Features (C=0.03) | Log Loss ↓ | AUC ↑ |
|---|---:|---:|
| Baseline | **0.529720** | **0.77135** |
| + Curriculum size / active concepts | 0.530097 | 0.77117 |
| + Relevance/coverage | 0.530125 | 0.77113 |
| + Skill-aligned activity volumes | 0.530312 | 0.77103 |
| + Wrong-concept activity volumes | 0.530523 | 0.77080 |

Bootstrap differences: baseline → aligned activity: -0.000593, 95% CI [-0.001734, +0.000505]; wrong-concept → correctly mapped activity: +0.000211, 95% CI [-0.000114, +0.000522]. Neither is robust evidence for incremental value.

## Data-quality / construct-validity problem: aligning skill taxonomies

The GRE bank comprises **27 distinct subskill labels**, while the generated tutoring lesson plan uses free-text concept titles. A frozen general-language embedding provides similarity, *not validation* that a concept teaches the measured subskill.

In a targeted qualitative spot check, generic concepts such as **“QC Strategy: Testing Edge Cases”** were selected as the most relevant concept for GRE subskills including **“exponent rules,” “probability with inclusion-exclusion,” and “coordinate geometry (perpendicular lines)”**. Such matches can be pedagogically relevant in limited contexts but are too broad to assume strict skill equivalence.

Cosine scores in E9 showed median best-match similarity **0.515** (10th–90th percentile **0.401–0.645**), but these are **not calibrated probabilities of correct matching**. No human-verified inter-rater agreement is available.

There are also 224 concept instances (2,267 minus 2,043) with no student-written message and therefore no student-text evidence. A missing or empty concept transcript should not be treated as proof of no learning.

## Scientific conclusion / self-criticism

1. **Negative:** The tested skill-conditioned embeddings and coverage features do not add reliable predictive value beyond pre-test + practice + question metadata.
2. **Negative control fails:** Deliberately permuted skill-to-concept evidence can match or beat the true mapping. This undercuts a causal or cognitive interpretation of the alignment.
3. **Weak positive signal only:** Skill-conditioned student embedding slightly outperforms pooled student embedding, yet its CI includes zero and it still underperforms the baseline.
4. **Serious construct-validity threat:** Generated lesson-plan concepts are *not* the GRE subskill taxonomy. Before proposing any skill-aware model, first measure human agreement over a codebook for their correspondence.
5. The full 1,139 quantitative sessions were **not** evaluated. Selection errors may matter. No multiple-comparison corrections or nested tuning were performed. Bootstrap CIs condition on already-chosen development predictions.
6. No independent holdout evaluated. We cannot conclude whether any model improvement is repeatable on unseen learners, tutors or questions.
7. The method uses truncated 1,800-character concept text per speaker, discarding later content; it omits detailed practice format and first-attempt grading provenance.
8. **Predictive performance is not mastery measurement and cannot establish a causal learning effect.**

## Recommended next decision gate: E9c annotation pilot

**Do not design a new neural architecture yet.** Conduct a preregistered human annotation of concept–GRE-subskill pair correspondence:

- Sample around 100–150 real candidate concept–subskill pairs, including high/medium/low cosine, generic strategy names, and hard negative pairs.
- Two independent annotators should label: **direct concept overlap / related general strategy / not related / indeterminate**. Explicitly distinguish topical match from the learner having *mastered* the concept.
- Report Cohen’s kappa or Krippendorff alpha as appropriate, per-class agreement, and calibration of embedding similarity to human labels.
- Only then compare `validated skill-aligned evidence` versus pooled and skill-shuffled controls. Use a frozen training-only mapping protocol to prevent evaluating with labels derived from post-test responses.
- Test sensitivity of the **practice baseline** to closed vs open questions and first-attempt vs final credit before claiming any dialogue increment.

The ultimate thesis may be a controlled, falsifiable analysis documenting conditions **under which observed learning traces do not add useful independent-performance prediction**. That is more defensible than asserting novelty for an unsupported feature extractor.

## Code / audit status

- [E9 script](../experiments/skill_conditioned_e9.py) added on a feature branch. It compiles and passed an end-to-end smoke test on **117 synthetic sessions**; synthetic results are not empirical results.
- Real numbers in this document come from separate exploratory execution on 604 downloaded real GRE Quantitative sessions. Local complete-dataset reproduction may differ, especially because 20 sessions could not be retrieved remotely.
- All raw person-level records stay outside GitHub. The `main` branch was not merged.

### Sources

- [StudentBench paper](https://arxiv.org/abs/2609.28470)
- [StudentBench data](https://huggingface.co/datasets/handshake-ai-research/studentbench)
- [Official StudentBench source code](https://github.com/Handshake-AI-Research/studentbench)
