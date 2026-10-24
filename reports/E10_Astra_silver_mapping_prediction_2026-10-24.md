# E10 — Astra pseudo-ground-truth mapping: learnability vs independent post-test prediction (2026-10-24)

**Status: exploratory / development only.** Astra's labels are treated as **assumed silver ground truth**, not validated human truth. We explicitly test whether imitating the mapping adds any usable prediction signal.

## E10a: classify 120 Astra pseudo-label pairs

Astra distribution: **D=5, S=39, N=73, U=3**. Split by GRE subskill (5-fold GroupKFold) and separately by concept title. Train features only inside the training fold. Compared constant-N, generic strategy regex, numeric logistic, and regularized char TF-IDF logistic.

| Method | 4-label accuracy, unseen subskills | 4-label macro-F1 | 4-label accuracy, unseen concept titles |
|---|---:|---:|---:|
| Constant N | .608 | .189 | .608 |
| Generic-strategy regex | **.842** | .431 | **.842** |
| Numeric logistic | .667 | .491 | .633 |
| Char TF-IDF logistic | .733 | **.509** | .775 |

Among **only the 112 S/N items**, char TF-IDF achieves **93.75%** accuracy with unseen subskill groups vs **90.18%** for strategy-keyword rules (4 extra correct). The paired gain is **3.57 pp**, clustered-subskill bootstrap 95% CI **[0.86,7.02] pp**, *conditional on fixed OOF predictions*. With unseen concept titles, both models score **90.18%**, no benefit.

**Critical warning:** Accuracy primarily captures how Astra interprets the word “strategy” in the concept title. Only five direct D examples exist. Four-class performance is poor and title-group generalization shows no gain over a handcrafted regex. Using Gemini Flash labels as an alternative reference on Astra's original S/N subset reduces both accuracies to **83.04%**; this is *reference-source sensitivity*, not a test of which model is correct.

## E10b: use 120 Astra silver labels to add concept evidence to post-test prediction

**Actual StudentBench GRE Quantitative data:** 13 AI tutor arms; **624 sessions targeted, 605 sessions completely retrieved**, 19 missing due remote retrieval (not assumed random). Development: **474 sessions** with **12,798 independent post-test item labels**; **131 session holdout reserved and not scored**.

- Original dataset [StudentBench](https://huggingface.co/datasets/handshake-ai-research/studentbench) ([paper](https://arxiv.org/abs/2609.28470)).
- 27 GRE quantitative subskills × 2,131 observed development concept titles = **57,537 candidate label pairings**.
- A multiclass logistic alignment classifier was trained on the **120 Astra silver labels** (C=.35, balanced, char TF-IDF and lexical features). Its estimated P(D)/P(S) were aggregated over tutoring concepts using student/tutor message volumes. These *scores are not calibrated mapping probabilities* in natural data.
- A strong logistic item baseline controls pre-test item-pair correctness, pre-test score and theta, pre-test skill/subskill accuracy, practice count/correctness/submissions, student/tutor messages, question ID/difficulty, tutor arm/form.
- 4-fold session-grouped out-of-fold development predictions, regularization C=.03 and C=.3, paired bootstrap resampling **sessions**, not item rows. Features: neutral concept volume, lexical title/subskill overlap, Astra silver weighted activity, within-session shuffled alignment (negative control).

### E10b results C=.03 (lower Log Loss and Brier, higher AUC are better)

| Model | Log Loss | Brier | AUC |
|---|---:|---:|---:|
| **Strong baseline B0** | **.525090** | **.174516** | **.77099** |
| + concept counts B1 | .525497 | .174635 | .77058 |
| + lexical title overlap B2 | .525480 | .174614 | .77058 |
| + Astra-silver alignment | .526015 | .174702 | .76990 |
| + shuffled Astra alignment | .525619 | .174646 | .77040 |
| + Astra and lexical together | .526115 | .174740 | .76977 |

At C=.3: baseline **.524974**; Astra mapping **.526419**; shuffled **.525736**; lexical **.525525** (Log Loss).

Paired **improvement in Log Loss, positive = model B better than A**, on C=.03:
- Baseline → volume: **−.000407**, 95% CI **[−.000793,−.000034]** (counts degrade predictions under this setup).
- Volume → Astra: **−.000518**, 95% CI **[−.002044,+.001004]**.
- Lexical → Astra: **−.000535**, 95% CI **[−.002054,+.001003]**.
- Shuffled alignment → Astra: **−.000396**, 95% CI **[−.001588,+.000874]**.

**Negative result:** No defensible additional predictive value is established for this Astra-silver alignment; the shuffled negative control even yields a better point estimate, with uncertain difference.

### Coverage / identifiability crisis

Across **61,344** observed (post-test item × concept in a student session) exposures, only **87 exposures (0.142%)** exactly match any of Astra's 120 annotated concept–subskill pairs, and only **5 exposures (0.00815%)** match an Astra-labeled **D** pair.

This is *exact-label coverage*, **not precision**. The feature extractor therefore predominantly extrapolates from an extreme tiny silver, deliberately similarity-stratified label sample. Treating P(D) as mathematical coverage is unsafe.

## Scientific interpretation and self-critique

1. **Imitation ≠ skill validity:** High binary S/N accuracy is mostly recognition of labels/keywords describing generic strategies; direct mathematical D is undersampled.
2. **Predictive failure:** Even granting Astra's 120 labels as reference, the tested alignment estimator does not improve independent post-test correctness beyond strong pretest/practice evidence; no robust positive incremental gain.
3. **Alignment negative control fails:** Mismatching within-session concept relationships is not reliably worse; cannot claim skill specificity.
4. **Severe domain shift:** 120 intentionally stratified labels vs tens of thousands of naturally occurring pairings. The silver classifier is not calibrated in this deployment distribution.
5. **Observational predictive design:** No causal learning effect, no proof that concepts were understood; title and message volume omit accuracy and quality of student reasoning.
6. **Data and statistical limits:** Remote 605/624 available-case sample, not full 1,139 Quant sessions; same items and tutors reused across CV; multiple exploratory variants and regularization values; CIs conditional on predictions rather than nested model selection; no confirmatory held-out test.
7. **The right unit is sessions/learners**, not 12,798 independent individuals. Where student_id repeats across sessions, cluster by person in a final experiment.

## Research gate and next experiment E11

**Do not call this a successful new skill-conditioned model.** E11 should build a **stratified but weighted mapping-validation sample** of 300–500 natural candidate pairs with substantial true direct-content examples, get at least two independent human GRE annotators on 150–200, and measure D precision/recall, calibration, classwise confusion, title- and subskill-disjoint generalization. Then freeze a verified mapping and rerun the independent post-test task with a full pinned StudentBench release, practice first/final correctness provenance, repeated shuffled controls and a single genuinely untouched holdout evaluation.

The scientific contribution may be a controlled **negative/incremental validity result** about when tutoring trace semantics fail to improve independent performance prediction. Do not invent a new ontology/architecture until a measurement-valid signal is established.

## Reproducibility

An executable E10 package was delivered to the researcher in this ChatGPT turn (Python scripts, summary JSON and full report). The **numerical E10a metrics were run on the 120 real Astra-labeled pairs**, and the **E10b numbers were run on 605 remotely retrieved real StudentBench sessions**. E10b local scripts passed a synthetic smoke test, but full identical reproduction requires a pinned official dataset snapshot; missing remote records and library version differences may change exact figures.

No original transcripts, private per-person records, or complete annotator labels were committed to the public repository.
