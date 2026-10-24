# E11 — Astra / Gemini 400-pair model-model analysis (2026-10-24)

## Sources, data quality and interpretation

The researcher supplied two independent annotation files `e11_annotator_A.csv` (Codex / GPT-6 Astra per research workflow) and `e11_annotator_B.csv` (Antigravity / Gemini per workflow). Their exact model/runtime identities cannot be authenticated solely from CSVs.

Both files have **400 unique matching pair IDs**, identical GRE skill/subskill/title content and order, all D/S/N/U labels valid, and every rationale complete (maximum 25 words). The original blinded dataset was reproducibly regenerated from StudentBench revision `304c8d63c726e72b60510bba3a44454fc0726721`; the SHA-256 of the rebuilt blind 400 CSV matched the committed source **byte for byte**. Thus, analysis by the three ORIGINAL sampling strata is exact, not inferred using keywords.

**Model agreement is not verified mapping correctness.** At the researcher's request, Astra's label may be assumed a *silver reference* for falsification experiments; this does not prove it is ground truth.

## Overall paired results

| Metric | Value |
|---|---:|
| N | **400** |
| Agreements | **355/400 (88.75%)** |
| Disagreements | **45** |
| Cohen κ, four labels | **0.82581** |
| GRE-subskill-cluster bootstrap percentile 95% CI for κ (5,000 replicates, 27 clusters) | **[0.7503, 0.8941]** |
| Agreement on D vs non-D | **390/400 (97.5%)** |
| Binary D-vs-non-D κ | **0.94916** |
| Both models chose D | **169** |
| Exactly one model chose D | **10** |
| Astra label distribution | D=178, S=43, N=147, U=32 |
| Gemini label distribution | D=170, S=69, N=159, U=2 |

### Confusion matrix (Astra rows / Gemini columns)

| | D | S | N | U |
|---|---:|---:|---:|---:|
| D | **169** | 8 | 1 | 0 |
| S | 0 | **41** | 2 | 0 |
| N | 0 | 4 | **143** | 0 |
| U | 1 | 16 | 13 | **2** |

**30 of 45 disagreements** occur when Astra uses **U** and Gemini chooses another label. This suggests systematic differences about evidence sufficiency, not simply mathematical misunderstanding. The D binary agreement is strong **as a comparison of two machine annotators**; it is not verified classification accuracy.

If Astra is **assumed** silver truth (only for sensitivity analysis): Gemini D precision=169/170=99.41%; D recall=169/178=94.94%. These quantify agreement with Astra, not correctness according to a human domain standard.

## Sampling-stratum analysis — crucial selection bias

| Original panel | N | Agreement | Four-class κ | D/D | Disagreement |
|---|---:|---:|---:|---:|---:|
| Uniform unique candidate pairs | 200 | **178/200 (89.0%)** | **0.7310** | **12** | 22 |
| High-similarity enrichment | 150 | **146/150 (97.3%)** | **0.4920** | **145** | 4 |
| Generic strategy stress | 50 | **31/50 (62.0%)** | **0.4033** | **12** | 19 |

**The very high overall number of D/D cases is driven by sampling.** Only **12/200=6.0%** of the uniform panel received D from both models. The panel's sampling frame is a **cross-product of the 27 GRE Quant subskills with active lesson-concept titles** (excluding original E9c pairs), not a distribution of observed student skill mastery or exposure-weighted lesson events. Even 6% describes only *model consensus* over unique potential pairs, not genuine D prevalence.

The **145 D/D out of 150** deliberately high-similarity cases illustrate why the full 400-sample D fraction is not a population rate. Despite 97.3% observed agreement in that panel, κ≈0.492 because almost all labels are D and expected chance agreement is high (prevalence sensitivity).

Generic strategy cases remain the difficult point: **19/50=38% disagreed**, including **8 D/S** and **10 U/S**. The content-coverage axis and generic transferable-strategy axis should be assessed independently by a domain reviewer.

## Exploratory E11d: transfer from deliberately enriched panel to uniform panel

**Train:** high-similarity + generic panels (n=200, Astra D=166=83%).  
**Test:** uniform panel (n=200, Astra D=12=6%); evaluation is against assumed Astra silver labels, **not human truth**. Text/lexical vectorizers fit solely on training data.

| Rule/model (fixed pilot settings) | D predictions / 200 | D precision vs Astra | D recall vs Astra | D F1 | Accuracy |
|---|---:|---:|---:|---:|---:|
| Always non-D | 0 | Undefined (reported 0) | 0% | 0.000 | 94% |
| Token-overlap recall ≥0.2 | 6 | 66.7% | 33.3% | 0.444 | 95% |
| Logistic char TF-IDF, C=.3, no class balancing | **76** | **9.2%** | 58.3% | **0.159** | 63% |
| Logistic char TF-IDF, C=.3, `class_weight=balanced` | 8 | 62.5% | 41.7% | 0.500 | 95% |

**Interpretation:** An enriched training panel can make the model massively over-predict D in the uniform panel due to class-prior shift. Model settings were explored after E11 labels were available: this is a **post-hoc exploratory pilot**, not an unbiased test for choosing the best model. Only 12 uniform positives mean high sampling uncertainty. No downstream independent StudentBench posttest model was evaluated in this turn.

## Blinded human adjudication — prepared, not performed

Two OFFLINE CSV files were generated privately from the user's 400 items:
- **160-case stratified blind sample**: 80 uniform + 60 enriched + 20 generic, sampled independently of outcomes; happens to contain 24 of the 45 machine disagreements.
- **181-case extended blind sample**: the above 160 + all 21 remaining machine disagreements, shuffled. **Do not use unweighted 181-case accuracy estimates for the target population.**

Both reviewer-facing CSVs have only pair ID, GRE skill/subskill, tutoring-concept title, and *blank* human label/rationale. Do **not** provide the analyst workbook to reviewers because it contains both AI labels and explanations on other sheets. If only one human reviewer participates, call it an expert reference, not human-human kappa.

After human ratings are locked, measure D recall/precision, error typology (notably D/S and U/S), title- and subskill-disjoint generalization, and finally incremental independent-posttest prediction versus baseline + same-budget pooled + shuffled skill-alignment controls. Retain negative results if there is no lift.

## Limitations and research recommendation

- Two model labels may share systematic bias and lexical similarity heuristics.
- Astra silver-ground-truth is a user-requested **assumption**, not a scientific certification.
- Uniform panel samples potential combinations, not verified lesson-to-item teaching pairs, individual learner mastery or causal learning effects.
- Expected κ depends strongly on prevalence; panel-specific κ values are not comparable without reference to marginal distributions.
- Many sampled pairs share GRE subskills and semantically related title families. The subskill-cluster bootstrap is exploratory.
- Prior E10b on 474 development sessions did not show predictive lift for Astra alignment; E11 agreement cannot reverse that without **new downstream evaluation**.
- Any future held-out test should note earlier project-wide model/split exploration and possible adaptive overfitting.

**Best next step:** obtain blinded domain review of the 160 stratified items, ideally by two independent GRE-mathematics experts. Use the extended 181 review only if full coverage of all 45 discordances is a priority. Keep all full model-label CSV files and individual rationales private.

## Reproducibility

- Source sample: [E11 400 blinded pairs](../annotations/templates/e11_pairs_blinded_400.csv).
- Protocol: [E11 annotation runbook](../annotations/E11_RUNBOOK.md).
- Code: [E11 agreement](../experiments/e11_evaluate_agreement.py).
- Dataset: [StudentBench](https://huggingface.co/datasets/handshake-ai-research/studentbench), revision `304c8d63c726e72b60510bba3a44454fc0726721`.

Full detailed comparisons, standalone private blind CSVs, quantitative JSON and spreadsheet were delivered directly to the researcher, **not published in this repository**.
