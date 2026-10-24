# E12 — Astra Silver Mapping: Learnability, Incremental Prediction, Falsification (2026-10-24)

**Research status:** exploratory development experiments. The researcher explicitly assumes **GPT-6 Astra annotations are a SILVER reference**. No labels were human validated. No reserved test session scored.

## E12a — Learning Astra's E11 400 labels

The labels have D=178, S=43, N=147, U=32 across deliberately different sampling strata. The **200 uniformly sampled unique pairs** have D=12, S=24, N=145, U=19. Report evaluation **separately on the 200 random pairs**, rather than a misleading overall 400-sample accuracy.

Five-fold GroupKFold, grouping alternatively by exact lesson concept title and GRE subskill. Character TF-IDF (2–4 grams) and lexical features fit only within the training fold, Logistic Regression C=0.3. Trained against Astra silver, NOT human truth.

| Method | 200 random: 4-class accuracy (title-disjoint) | Macro-F1 | D-F1 | D TP of 12 |
|---|---:|---:|---:|---:|
| Always N | 0.725 | 0.210 | 0 | 0 |
| Fixed lexical rule | 0.750 | 0.314 | 0.133 | 1 |
| Numeric lexical LR | 0.820 | 0.587 | 0.476 | 5 |
| **Char TF-IDF LR** | **0.830** | **0.623** | **0.500** | **5** |
| Balanced char TF-IDF LR | 0.820 | 0.622 | 0.421 | 4 |
| Stratum-weighted char TF-IDF LR | 0.820 | 0.589 | 0.400 | 4 |
| Add 120 historical Astra labels | 0.810 | 0.623 | 0.421 | 4 |

On **subskill-disjoint GroupKFold**, natural char TF-IDF LR: accuracy 0.810, macro-F1 0.561, D-F1 0.526, D precision 5/7, D recall 5/12. On title-disjoint GroupKFold: D precision 5/8, D recall 5/12.

Difference in D-F1 (natural char TF-IDF minus fixed lexical rule): 4,000-resample cluster-bootstrap percentile CI by concept-title [0.067, 0.643], by GRE-subskill [0.108, 0.706]. These exploratory conditional CIs do not correct for trying variants; the rare **12 D positives** make them unstable.

Astra and Gemini happen to label **the same 12 D in the random 200-pair panel**, but model consensus is not truth.

## E12b — Predicting independent post-test correctness

### Data and precautions

StudentBench Quant pinned to dataset SHA `304c8d63c726e72b60510bba3a44454fc0726721`. Targeted 624 sessions from 13 AI arms, **582** successfully retrieved with required profile, pre/post responses, lesson plan and event trace. Missing 42 are not assumed random. Stratified arm/form session split has **456 development sessions**, **126 reserved and unscored sessions**. Development contains **12,312 post-test item outcomes**, with 4-fold session-grouped CV. The split is NOT globally pristine given E7–E11 model exploration.

Strong item baseline includes matched pre-test item correctness, total/IRT, skill/subskill pre-test performance, practice attempts/final-correctness and message counts, and question/difficulty/tutor/form IDs. Adding concept counts, lexical overlap, mapping predicted weights P(D)/P(S) over concept-level student/tutor message volumes (trained on Astra 120, 400 or 520 silver labels), and within-session permutation of mapping scores. Mapping probabilities are uncalibrated.

| Predictive feature set | Log Loss ↓ C=0.03 | AUC ↑ C=0.03 | Log Loss ↓ C=0.3 |
|---|---:|---:|---:|
| **Strong pre-test/practice baseline** | **0.526484** | **0.77225** | **0.525773** |
| + Concept counts | 0.527352 | 0.77146 | 0.526999 |
| + Lexical match | 0.527708 | 0.77107 | 0.527470 |
| + Mapping from Astra E9c 120 | 0.527951 | 0.77071 | 0.527767 |
| + Mapping from Astra E11 400 | 0.527854 | 0.77110 | 0.527799 |
| + Mapping from Astra 400 SHUFFLED | 0.527716 | 0.77121 | 0.527740 |
| + Mapping from Astra 520 | 0.527759 | 0.77112 | 0.527623 |
| + Mapping from Astra 520 SHUFFLED | 0.527869 | 0.77101 | 0.527821 |

Primary paired session-bootstrap **Log Loss reduction** (positive would mean benefit), 1,800 resamples:

| Comparison | C=0.03 gain [95% CI] | C=0.3 gain [95% CI] |
|---|---|---|
| Baseline → Astra 400 | **−0.001370** [−0.002933,+0.000152] | **−0.002025** [−0.003800,−0.000425] |
| Shuffled 400 → correct 400 | −0.000138 [−0.000701,+0.000434] | −0.000059 [−0.000695,+0.000593] |
| Astra 120 → Astra 400 | +0.000097 [−0.000817,+0.000921] | −0.000031 [−0.001007,+0.000878] |
| Shuffled 520 → correct 520 | +0.000110 [−0.000498,+0.000737] | +0.000197 [−0.000489,+0.000907] |

**Observed finding:** No reproducible incremental predictive improvement from Astra-silver concept–skill alignment. The within-session shuffled control is as good as or better than correct 400-label matching by point estimate. For C=0.3, adding mapping degrades Log Loss relative to baseline with a conditional CI that excludes zero; avoid a universal conclusion due multiple exploratory comparisons.

## E12c — Exact Astra silver label coverage of post-test item × concept exposures

There are **57,834** concept–posttest item exposures in development sessions, but just **406** exact matches to any of the 400 Astra-labeled E11 pairs. Among those, **180** exactly match Astra's D label; **177** also have at least one student message within that concept. Consequently, only **177/12,312 post-test item observations (1.44%)** have an explicitly Astra-rated D concept with student activity, spread across **143/456** development sessions.

This is **coverage**, not actual mapping precision. The 400-label mapper uses extrapolation for the vast majority of observed concept–subskill links. A fitted P(D) is neither a calibrated skill-match probability nor evidence of student mastery.

## Scientific self-criticism and next gate

1. **Astra = assumed silver, not human truth**. Agreement with Astra measures imitation of Astra; 12 natural D examples cannot establish mapping validity.
2. 200 representative items are a **unique-pair cross-product sample**, not frequency-weighted learning encounters. Deliberate enrichment in the other 200 makes all-400 rates invalid population prevalence estimates.
3. Student/tutor message volume and lesson title are weak proxies for **reasoning quality, understanding, feedback uptake and temporal progression**. An E12b negative result for these features does not show all semantic or temporal representations are useless.
4. Remote data retrieval lost 42 sessions; E10 compared different available-case data, so avoid cross-experiment score comparisons.
5. No multiplicity-adjusted or globally clean confirmatory holdout; early exploration can influence methodological choices. CV CIs conditional on fixed OOF predictions.
6. Predicting independent post-test score from observed tutoring traces is not a causal estimate of knowledge gained.

**E13 recommended and pre-designed:** outcome-free, sequence-aware *practice-process* features derived from StudentBench `practice_answer_submitted`, `practice_problem_id`, `is_correct`, `answer_attempt_number`, `timestamp_elapsed_seconds` and conversational event ordering. Test first vs final correctness, answer revision after feedback, early/late correctness, and student explanation measures beyond the existing practice summary baseline. Include count-preserving sequence shuffles; train and evaluate by session and retain a strict independent outcome. Do not add a more complex neural model until this interpretable process-feature test demonstrates robust signal.

## Artifacts and provenance

- E12a code/results: delivered as a reproducibility bundle in this conversation (`e12_mapping_cv.py`, `e12_bootstrap.py` and aggregate JSONs).
- [E12b aggregate JSON](E12b_Astra_silver_posttest_2026-10-24.json) committed independently with exact metrics/contrasts; user CSV labels and individual student data are NEVER committed.
- Additional Vietnamese writeup provided as `E12_Astra_silver_research_report_2026-10-24.md` separately in ChatGPT.
- Source: [StudentBench dataset](https://huggingface.co/datasets/handshake-ai-research/studentbench), [paper](https://arxiv.org/abs/2609.28470), [official code](https://github.com/Handshake-AI-Research/studentbench).

**Research decision:** Improve measurement of learning-process evidence, not count of pseudolabels or model complexity. The hypothesis that these particular title-aligned silver representations offer incremental prediction remains unsupported.
