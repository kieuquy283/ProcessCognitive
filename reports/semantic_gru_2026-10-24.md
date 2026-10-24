# StudentBench E7/E8 research report — 2026-10-24

## Research objective

**Question:** Does tutoring dialogue semantics or interaction-event order provide **incremental out-of-session predictive validity** for independently measured post-test performance, beyond prior proficiency and practice evidence?

The question is narrower than causal learning effects or latent student-mastery measurement. A successful classifier does not establish that an interaction caused learning.

## Primary evidence and context

- [StudentBench](https://arxiv.org/abs/2609.28470) and [data release](https://huggingface.co/datasets/handshake-ai-research/studentbench): paired 27-item pre-test/post-test, tutor-assisted practice and student/AI interaction traces.
- [StudentBench original code](https://github.com/Handshake-AI-Research/studentbench): provides validated study analyses and engagement feature engineering; avoid presenting aggregate engagement counts as new.
- [Scarlatos, Baker & Lan (LAK 2025)](https://doi.org/10.1145/3706468.3706501): dialogue-based knowledge tracing already established; their target is within-tutoring student response correctness, not necessarily independent post-tutoring assessment performance.
- [Huang et al. (BEA 2026)](https://aclanthology.org/2026.bea-1.43/): dialogue knowledge tracing can incorporate question difficulty explicitly and obtain meaningful performance improvements in other tutoring datasets. This contradicts any overgeneralization that all dialogue representations are ineffective.
- StudentBench Appendix F has six transcript pedagogical indicators that were **not validated as predictors of learning lift** by the study authors; include them as a future baseline.

## Data / protocol

- GRE Quantitative, 13 AI tutor arms; 806 sessions sampled (up to 62 per arm); **789 complete session records downloaded** for this experiment. Remaining 17 are remote retrieval failures, **not proven unavailable in the public release**.
- Balanced-by-tutor sample differs from the full set of 1,139 Quantitative AI sessions.
- Pre-designated **620 development sessions and 169 unused holdout sessions**.
- For E7, assessment target is *post-test item correctness*. Train and validation are grouped by entire session. All candidate features occur before post-test, except for **public item metadata** available at prediction time.
- For E8, assessment target is *overall post-test percentage score*. This is a different task; compare model variants within E8, not raw E7 vs E8 losses.
- All metrics below are development out-of-fold results. The held-out sessions were **not used for model selection or reported evaluation**. Bootstrap intervals resample session-level paired losses.

## E7: frozen semantic embeddings vs strong item-level baseline

**Implementation:** frozen `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions). Two beginning/end windows per student and tutor text, 2,200 characters each, embedded and averaged; linear classifier with regularization. Structured baseline includes matched pre-test correctness, pre-test score and IRT estimate, skill/subskill pre-test accuracy, practice attempt summaries, item identity/skill/subskill/difficulty and tutor/form.

| Model (C=0.03) | Log Loss ↓ | Brier ↓ | AUC ↑ |
|---|---:|---:|---:|
| Baseline | **0.528096** | **0.175571** | **0.7716** |
| + Student embedding | 0.532264 | 0.177209 | 0.7669 |
| + Tutor embedding | 0.531598 | 0.176937 | 0.7677 |
| + Both embeddings | 0.534606 | 0.178136 | 0.7644 |
| + Student beginning/end semantic-difference representation | 0.532865 | 0.177499 | 0.7660 |
| + Student embedding permuted within tutor/form | 0.528875 | 0.175737 | 0.7709 |

Paired session bootstrap for **reduction in Log Loss** relative to baseline, C=0.03:

| Comparison | Delta (higher is better) | 95% CI |
|---|---:|---|
| + Student embedding | -0.004168 | [-0.006853, -0.001681] |
| + Tutor embedding | -0.003502 | [-0.005481, -0.001584] |
| + Both | -0.006510 | [-0.010056, -0.003398] |
| + Student semantic change | -0.004769 | [-0.007538, -0.002235] |
| + Permuted student | -0.000780 | [-0.003096, +0.001452] |

**Regularization sensitivity:** at C=0.3, baseline Log Loss = 0.527843, student embedding = 0.551494, tutor embedding = 0.546530 and both embeddings = 0.565444. We observe *worse*, not better generalization when fitting embeddings more aggressively.

**Interpretation:** This specific *pooled session-level* semantic representation is not supported as incrementally predictive by the development sample. It is not evidence that **skill-aligned dialogue segments**, deep contextual turn sequences, or other educational tasks are uninformative.

## E8: GRU sequence vs event-bag comparison

**Implementation:** 6 event symbols — student message, AI reply, practice shown, credited practice attempt, uncredited attempt, unknown credit. Session event lists are truncated at 256 events (first 128 and last 128). Static neural predictor compared with static + count bag, GRU over chronological events, and identically configured GRU over randomly permuted events. Within each training fold, early stopping uses a separate validation split.

| Model | RMSE (points / 27) ↓ | MAE (points / 27) ↓ |
|---|---:|---:|
| Neural static baseline | 4.10924 | 3.13885 |
| + Event bag | **4.06724** | **3.11128** |
| + Ordered GRU | 4.07747 | 3.14810 |
| + Shuffled-order GRU | 4.10979 | 3.15517 |

Paired session bootstrap **reduction in MSE**, expressed for score fractions in [0,1]:

| Comparison | Delta (higher better) | 95% CI |
|---|---:|---|
| Static → Event bag | +0.000471 | [-0.000457, +0.001560] |
| Event bag → Ordered GRU | -0.000114 | [-0.001101, +0.000877] |
| Shuffled GRU → Ordered GRU | +0.000363 | [-0.000753, +0.001345] |
| Static → Ordered GRU | +0.000357 | [-0.000769, +0.001571] |

**Interpretation:** Ordering alone has not shown robust, additional predictive value in this particular event-only, low-data GRU configuration. Note that event symbols lose semantic content, timing gaps and concept alignment.

## Critical self-review / threats to validity

1. **Sample selection**: remote download had 17 failures; missingness might be associated with request order or size and cannot be assumed random. Local full-download reproduction is preferable.
2. **Model selection bias**: compared regularization settings, architecture variants and two distinct tasks on development folds. CIs are exploratory and unadjusted for multiple tests.
3. **Target mismatch**: E7 evaluates item-level independent correctness, while E8 evaluates 27-item total score, so reported metrics cannot be pooled across experiments.
4. **Limited independence**: E7 item labels share a session. Correct session-cluster bootstrap and split by session are essential.
5. **Embedding bottleneck**: embeddings are from limited transcript windows; compressing all tutoring into one 384-dimensional vector can drown out skill-specific signals and session progression.
6. **Weak temporal supervision**: E8 asks a 620-session GRU to learn a 27-item total outcome with event types only. It need not succeed even if skill-specific sequential knowledge is present.
7. **Temporal truncation and randomization**: truncation discards middle events in long sessions. A shuffle changes transition distribution, but not student ability; negative controls should hold event counts fixed as done here, and evaluate across more seeds.
8. **Possible practice grading ambiguity**: open-response attempts are not interchangeable with graded closed-response correctness. A better baseline uses first attempt, question type, correctness provenance.
9. **Generalization limits**: holdout is unseen sessions on the *same* GRE question bank and tutoring systems. Held-out tutors, unseen assessment items, and cross-domain performance are harder tests not yet completed.
10. **Research novelty**: dialogue-based KT already exists. Merely appending embeddings or adding a GRU is not an algorithmic contribution.

## Decision gates

**Not justified now:** claiming that new cognitive ontology, TARE, raw transcript embedding, or generic sequential deep learning improves independent GRE assessment prediction.

**Next experimental hypotheses, in order:**

1. **E9 skill-conditioned evidence**: map actual dialogue turns and generated lesson-plan concepts to GRE subskills using validated mappings. Compare against a same-budget skill-agnostic model and shuffled skill alignments. Keep all text from target post-test assessments out of tutoring-derived features unless equally available to all baselines.
2. **Quality-aware practice baseline**: first versus final answer, closed versus open questions, credited versus ungraded. Compare against strong pre-test + item + tutor baseline, then re-evaluate any dialogue contribution.
3. **Robustness**: freeze one model from E9 on development; evaluate only once on the untouched holdout. Then re-run from complete 1,139 Quantitative sessions and replicate on GRE Verbal if metadata alignments support it.
4. **Potential negative thesis**: a careful, reproducible finding that interaction-trace representations offer little incremental value for independent learning assessment *under these tested conditions* is scientifically meaningful and methodologically defensible, provided final controls and uncertainty are adequate.

### Reproduction and code

- [ProcessCognitive diagnostic branch](https://github.com/kieuquy283/ProcessCognitive/tree/research/studentbench-diagnostics)
- [E7 frozen semantic embeddings](../experiments/semantic_baseline.py)
- [E8 event GRU and shuffled control](../experiments/event_gru.py)
- [Local dataset loader](../experiments/studentbench_loader.py)

**Code status:** scripts compile and passed a smoke execution on **synthetic fixture data** (which are not evidential results). Actual numeric results in this report derive from separate experiments run on retrieved StudentBench session records on 2026-10-24; due remote retrieval failures, re-runs on complete official downloads may differ.
