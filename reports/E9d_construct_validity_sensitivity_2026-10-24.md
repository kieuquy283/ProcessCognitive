# E9d — Rubric-boundary audit: Astra × Gemini, 2026-10-24

**Status:** Exploratory analysis completed on 120 supplied model-label pairs. **No completed human adjudications** exist in the 41-pair blinded worksheet. Model identifiers are researcher-reported; CSV data do not independently authenticate runtime identity.

## Research question

Do models consistently distinguish *mathematical content coverage* (D), *transferable strategy* (S), *unrelated content* (N), and *insufficiently specified* (U)? Why do they disagree despite the shared rubric?

## Verified quantitative results

| Measure | Value |
|---|---:|
| Complete matched pairs | 120 |
| Raw agreement | 99/120 = **82.5%** |
| Cohen κ, four-class | **0.6310** |
| 4-class disagreements | 21 |
| A=S, B=N | 18 |
| A=U, B=D | 2 |
| A=U, B=N | 1 |
| Agreement after collapsing S/N (D / R / U) | **117/120 = 97.5%** |
| κ after collapsing S/N | **0.7894** |
| Agreement on D vs non-D | **118/120 = 98.3%** |
| κ on D vs non-D | **0.8248** |

Only **five pairs** were jointly rated D. High binary D agreement should not be mistaken for adequate evaluation of diverse direct-coverage cases.

### Generic-strategy discordance

The original E9c title-keyword detector was applied to the 120 deliberately stratified pairs.

| Candidate class | Disagreement | Rate |
|---|---:|---:|
| Generic strategy title | 13/30 | **43.33%** |
| Non-generic title | 8/90 | **8.89%** |

Absolute excess disagreement: **34.44 percentage points**. Exploratory 2×2 Fisher odds ratio **7.84** (p ≈ **0.00007465**); **this test treats pairs as independent although multiple pairs share GRE subskills**.

A 15,000-resample bootstrap over the 27 **GRE-subskill clusters** gives a conditional percentile 95% interval for the excess disagreement of **[16.19, 53.63] percentage points**. This is not a population error rate and does not measure truth of either label. The asymmetry of the 18 S/N disagreements (all A=S and B=N) yields a descriptive two-sided exact binomial p ≈ **0.00000763** under a simplistic directional-symmetry null; it does not establish which model is correct.

## Main inference

**The S/N boundary is less stable between these two models than D vs non-D.** Merging S/N greatly increases agreement, but would erase a theoretically important distinction for educational process analysis. A third-party expert must assess whether a generic lesson-strategy title supports S or is irrelevant to the target GRE subskill.

Agreement is not accuracy, and no model-label data establish learning, mastery or improvement in posttest prediction.

## E9d follow-up

- **Blinded expert review:** 41 pairs: 21 model disagreements plus 5 D/D, 5 S/S, 10 N/N controls, randomized. Existing audit file is fully blank as of this report.
- **Two supplemental diagnostic axes:** (i) specific mathematical match / different topic / unclear; (ii) explicit general strategy / none / unclear. Then a four-way **D/S/N/U** label under the original **unchanged E9c codebook**.
- **No relabeling the original GPT outputs.** Diagnostic axes are extra measurements, not a retrospective change to the label scheme.
- **Analysis pipeline:** [expert audit comparison](../experiments/e9d_analyze_expert_review.py), [reproducible disagreement statistics](../experiments/e9d_model_conflict_stats.py), [two-axis protocol](../docs/E9d_two_axis_expert_review_protocol_v0.1.md).
- **Caveats:** The 41-pair sample is enriched for disagreements and cannot yield unweighted population accuracy. A single human expert is not human-human inter-rater reliability. Prefer two independent domain reviewers if resources permit.
- After construct validity is established, freeze the mapping and retest E9 against the pretest+practice baseline, using same-budget pooled and shuffled concept controls on development only; do not tune on held-out sessions.

A formatted **offline blinded expert workbook** named `E9d_blinded_two_axis_review_41.xlsx` was prepared for the researcher and not committed to public git. The original two model-label files also remain private.

## Related research

- Mukherjee et al. (2026), [The Geometry of LLM-as-Judge: Why Inter-LLM Consensus Is Not Human Alignment](https://www.microsoft.com/en-us/research/publication/the-geometry-of-llm-as-judge-why-inter-llm-consensus-is-not-human-alignment/).
- Kasner et al. (2026), [LLMs as Span Annotators: A Comparative Study of LLMs and Humans](https://aclanthology.org/2026.mme-main.1/).
