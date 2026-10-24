# E11 — Concept–skill mapping validation: sampling, weak-label transfer and falsification (2026-10-24)

## Research question and status

**RQ:** Can a mapping learned from GPT-6 Astra's D/S/N/U labels reliably generalize to naturally encountered GRE concept–subskill pairs, and after measuring its validity, does it add independent posttest predictive information beyond a strong pretest/practice baseline?

**Current result:** E11 sampling and **silver-transfer risk diagnostic completed**. The new 400 pairs are **NOT annotated**. There is no human gold-standard quality score, no E11 predictive gain and no final holdout result yet. Astra is treated as an **assumed silver reference**, following the researcher's explicit counterfactual, not objective truth.

## Dataset and data acquisition

Official [StudentBench dataset](https://huggingface.co/datasets/handshake-ai-research/studentbench), GRE Quantitative, observed Hugging Face revision **304c8d63c726e72b60510bba3a44454fc0726721** on 2026-10-24.

- Selected and successfully downloaded **624/624** AI tutoring sessions across 13 AI model arms for **metadata sampling**. These files were session profiles, AI lesson-plan concept titles and event types (not student transcript text or posttest outcomes in the labeling input).
- Fixed session split on this sample: **489 development** sessions / **135 sessions excluded from annotation sampling**. The latter have not been used to construct E11 candidates, but should **not automatically be described as globally untouched confirmatory test data**: earlier E10 used a different split on a different remotely available subset.
- Student dialogue evidence requirement: concept appears in the trajectory with at least one nonempty `student_message` tagged to that `concept_id`.
- After conservative title-length and PII-pattern filters, **1,999 distinct concept titles**, 27 GRE quantitative subskills; **53,973** distinct possible pairs in the observed development sample, **53,853** remaining after removing the 120 previously used E9c pairs.
- Population unit: **distinct observed (GRE subskill, active concept title) pairs**. Not sessions, messages, human learners or exposure-weighted events.

## E11a — Real 400-pair audit data

[Blinded unlabeled 400-pair CSV](../annotations/templates/e11_pairs_blinded_400.csv) is checked to contain exactly **400 unique IDs, 27 subskills, 354 distinct titles, all D/S/N/U fields EMPTY**, with the original six-column format. No transcripts, grades, session IDs or similarity scores. The 120 E9c pairs used to fit Astra-silver models are excluded verbatim.

| Stratum | Sample count | Intended estimand |
|---|---:|---|
| **Uniform unique-pair sample** | **200** | Estimate class prevalence over the **53,853 distinct candidate pairs** in this development cohort, after actual blinded human review |
| **High-similarity enrichment** | **150** | Deliberately challenge/test direct coverage D; cosine and title-word overlap prioritization is a sampling heuristic, NOT proof of D |
| **Generic strategy stress cases** | **50** | Diagnose S/N ambiguity for explicitly general GRE strategies |

Enrichment score: 0.65×(cosine of frozen MiniLM subskill/title embeddings) + 0.35×(overlap of subskill content words). Enrichment chosen with caps on repeated subskills and titles where possible. Observed cosine range within enriched cases: **0.490–0.841**. **No D rate can be inferred from similarity alone.**

The complete sample is STRATIFIED. Treating the frequency of D in all 400 as its population prevalence would be invalid. After a validated reference is available, report prevalence from the **200 random pairs** only, with uncertainty appropriate for a finite unique-pair population. For any claim about actual sessions or student usage frequency, design a separate exposure-weighted sample.

## E11b — Weakly supervised Astra transfer: a diagnostic, not annotation

The existing **120 Astra reference labels** contain N=73, S=39, D=5, U=3. A four-class Logistic Regression with numeric lexical features plus character TF-IDF was trained on 120 labels, then evaluated with grouped cross-validation and *applied without labels* to the new 400 E11 pairs.

| Evaluation on the 120 original Astra labels | Unseen GRE subskill groups | Unseen concept-title groups |
|---|---:|---:|
| Accuracy | 0.7583 | 0.7917 |
| Macro F1 (4 classes) | 0.4990 | 0.5489 |
| **F1 for D only** | **0.1818** | **0.3077** |
| Correct D among true 5 D | **1/5** | **2/5** |

**Class-overfitting and extrapolation:**

| Regularization C | Argmax D on **unlabeled E11 400** |
|---|---:|
| 0.035 | 185 |
| 0.35 | 167 |
| 3.5 | 162 |

**69/400** E11 predictions differ between C=0.035 and 3.5. Some classifier P(D) values approach 1.0, but **are not calibrated** and cannot be interpreted as validity/confidence in actual concept coverage. Because of class-weight balancing with **only 5 D examples**, an apparently large quantity of predicted D is not a positive research result; it is a red flag for unsafe domain transfer. The same 400 items have no verified true labels yet. The 400 predictions were only analyzed in **aggregate** and never written back to the annotation CSV.

### Synthesis of E10 and E11

E10 demonstrated that Astra-silver alignment did **not** improve independent posttest correctness over a detailed pretest+practice baseline on 474 development sessions (12,798 posttest items; E10b Log Loss 0.525090 baseline vs 0.526015 Astra mapping at C=0.03). Shuffled alignment was not reliably worse.

E11 adds an explanatory measurement failure mode: the D-class signal in the 120 annotated examples is too sparse, and the trained map extrapolates aggressively to unseen concept names. Learning S/N strategy markers does not imply identifying mathematical coverage.

## Falsification and validity threats

1. **Silver ≠ valid.** Agreement with Astra is agreement with Astra's rubric interpretation. Human-anchored validity is still absent.
2. **Only five D positives.** Macro and D-class metrics are extremely sample-dependent. Predicting D on 167/400 unlabeled pairs does not demonstrate 167 true content matches.
3. **Selection distribution.** Original E9c 120 were deliberately similarity-stratified. E11 400 are a mix of uniform and targeted strata. Class-weight balanced probabilities are not calibrated for any natural prevalence.
4. **Train/evaluation overlap risk.** Although exact E9c pairs are excluded from E11, some **concept titles and subskills** recur. Title-disjoint and skill-disjoint tests are required. A 27-subskill bank limits the granularity of skill-group validation.
5. **Unit of analysis.** 27 posttest item responses from one session are dependent; `student_id` is a session key, not necessarily globally unique participant identifier. Cluster at session where identity linkage is not known.
6. **Selection and split history.** Earlier E10b split (605 retrieved, 474/131) is **not the same** as this E11 annotation split (624 retrieved, 489/135). We must not pretend E11 reserved sessions were globally pristine across all prior project exploration.
7. **Mapping target not learner mastery.** Even a perfectly aligned concept only means related instructional content was mentioned, not that the learner learned or understood it.
8. **Causal limits.** Posttest prediction is observational and cannot prove conversation content caused learning.

## E11c — Next executable protocol

1. Two independently operating model annotators — GPT-6 Astra in Codex and Gemini in Antigravity — each assign **400 labels** with [ONE frozen codebook](../annotations/E11_COMMON_LABELING_CODEBOOK.md), identical unlabeled sample, isolated workspaces and no inter-model leakage. Outputs remain private under `annotation_work/`.
2. Validate 400 rows per annotator with [E11 validator](../experiments/e11_validate_labels.py), then compute κ and D-vs-non-D confusion with [E11 agreement tool](../experiments/e11_evaluate_agreement.py); **these statistics are AI–AI reliability, not mapping accuracy**.
3. In a separately blinded expert review, target **160 items**: 80 of the 200 random items, 60 of 150 high-similarity items, 20 of 50 strategy items. Prefer two independent domain reviewers. Resolve D/N, D/S and S/N boundaries. Keep a fresh mini-holdout of expert labels not used for codebook revision.
4. Evaluate classwise D precision/recall and model agreement **against actual human review**, separately by stratum. Report unweighted prevalence only for the random-pair stratum.
5. Only after valid mapping, rerun the strong pretest+practice posttest prediction baseline and same-data-budget true/shuffled concept features, freeze design and evaluate an appropriately isolated session test once. E11 **has not yet done this**.

## Reproducible code and provenance

- [Source sampling script](../experiments/e11_prepare_mapping_sample.py). Use official dataset pinned at SHA above; default 48 tasks/arm, with optional `--remote`; private sampling sidecar is under gitignored `annotation_work/`.
- [400-pair blind input](../annotations/templates/e11_pairs_blinded_400.csv).
- [Astra silver transfer test](../experiments/e11_silver_risk_audit.py).
- [Fixed labeling codebook](../annotations/E11_COMMON_LABELING_CODEBOOK.md).
- [Codex task](../annotations/E11_CODEX_A_TASK.md), [Antigravity task](../annotations/E11_ANTIGRAVITY_B_TASK.md).
- [Validator](../experiments/e11_validate_labels.py) and [agreement/human-audit generator](../experiments/e11_evaluate_agreement.py).

**Engineering checks:** Sampling script generated 400 valid unique real pairs and an analyst-only sidecar. Silver diagnostic produced grouped-CV and 400-item aggregate transfer metrics using the prior actual Astra labels. Label validator and agreement script passed a **mock-label smoke test**, which must not be cited as a real annotation result.
