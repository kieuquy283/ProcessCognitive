# E9c: Independent Codex Astra vs Antigravity Gemini labeling — model–model agreement

**Date:** 2026-10-24  
**Status:** Two completed CSVs were supplied by the researcher and analyzed locally. This is **model–model agreement**, not human inter-rater reliability or a validated ground truth dataset.

## Data verification

- 120 paired rows in both files. Exact matching `pair_id`, GRE skill/subskill, concept title, and input order.
- All categorical values within D/S/N/U, no missing labels or rationales; rationales respect the 25-word limit.
- Pair IDs match the generator's SHA-256 scheme for subskill/concept title.
- CSVs alone cannot verify the exact models used, whether hidden cross-contamination occurred, or whether annotators were genuinely isolated. Labels “Astra” and “Gemini” follow the researcher's declared pipeline.

## Overall agreement

| Metric | Result |
|---|---:|
| Matched observations | 120 |
| Exact agreement | 99 / 120 (**82.5%**) |
| Expected chance agreement from marginal labels | 52.57% |
| Nominal Cohen's κ, 4 categories | **0.6310** |
| 95% percentile CI, 4,500 pair-bootstrap replicates | [0.496, 0.759] |
| 95% percentile CI, 4,500 GRE-subskill-cluster bootstrap replicates (27 subskills) | [0.502, 0.741] |
| Strict D vs non-D κ | **0.8248** (raw agreement 98.3%) |
| Broad D/S vs N/U κ | **0.6114** (raw agreement 83.3%) |

The strict D κ must be interpreted cautiously: only **five** pairs were marked D by both models; just **seven** received D from at least one model. Gemini did not use U.

### Full confusion matrix

Astra (A) in rows, Gemini (B) in columns:

| A \ B | D | S | N | U | Row total |
|---|---:|---:|---:|---:|---:|
| D | 5 | 0 | 0 | 0 | 5 |
| S | 0 | 21 | **18** | 0 | 39 |
| N | 0 | 0 | 73 | 0 | 73 |
| U | **2** | 0 | 1 | 0 | 3 |
| Column total | 7 | 21 | 92 | 0 | 120 |

N accounts for **73 out of the 99 exact agreements**. The overall percentage is therefore strongly affected by N prevalence in this deliberately stratified sample.

## Central empirical finding: strategy-vs-unrelated interpretation

**18 of the 21 disagreements are directional S/N:** Astra assigned a general transferable strategy (S) and Gemini assigned no meaningful topical relation (N). No reverse N/S disagreements occurred.

Using the study's predefined generic-strategy title regex (QC, strategy, testing edge cases, guessing, exam techniques and similar):

| Subsample | Exact agreement | Disagreement |
|---|---:|---:|
| Generic-strategy candidate titles (30) | **17 / 30 (56.7%)** | 13 |
| Other concept titles (90) | **82 / 90 (91.1%)** | 8 |

The sample intentionally included 30 generic-strategy pairs; this difference cannot be converted directly into a population-wide misclassification rate. **Neither A nor B can be automatically deemed correct.**

The remaining three disagreements are **2 U/D** (broad percentage-related lesson titles vs more specific GRE percent subskills) and **1 U/N** (broad coordinate geometry title vs distance between parallel lines). These reveal a second unsettled boundary: the level of topic specificity required for D vs U.

## Scientific interpretation

1. κ = 0.6310 shows nontrivial consistency *between two models*, but not correct mapping. The original E9 predictive result remains negative; this labeling result does **not** demonstrate incremental posttest prediction or causal learning.
2. The annotation codebook needs an explicitly adjudicated boundary between a broadly applicable strategy and a fundamentally unrelated mathematical topic. Models may differ systematically even when both receive identical instructions.
3. A high strict D binary κ is fragile when positive labels are rare; independent human review is essential to establish construct validity.
4. Agreement percentages cannot estimate population class proportions: the 120-pair set was deliberately balanced by cosine similarity and generic titles.
5. Additional dependencies exist between items sharing GRE subskills and lesson title semantics; intervals and any inferential testing should be treated as exploratory.
6. The analysis should NOT be described as *human* inter-rater reliability. CSV data do not independently certify the model identity specified by a product UI.

## E9d decision gate

Complete a **blinded human adjudication** of all **21 discordant pairs**, plus a prespecified control sample of **20 concordant pairs** (5 D/D, 5 S/S, 10 N/N). The audit file should expose only the two topical descriptions and blank human fields; it should hide Astra/Gemini labels, their explanations, automated cosine scores and whether a pair was disputed. Do not alter the original two model label files.

Once independent human judgments exist:
- assess how frequently each GPT label agrees with human judgment in each **sampling stratum**;
- specifically review the 18 S/N and two U/D boundaries;
- document a revised codebook with concrete edge cases;
- then freeze concept–subskill mapping and re-evaluate E9 against the pretest+practice baseline and shuffled-mapping negative control on development only.

**Privacy:** The original complete model-labeled CSVs and per-item disagreement rationales are kept in the researcher's local `annotation_work/`, not committed to this public GitHub repository. Local detailed files are provided separately to the researcher.
