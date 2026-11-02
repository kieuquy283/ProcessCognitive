# ND2 authentic StudentBench data-quality audit — 2026-10-27

**Status:** Real source-data analysis executed. **ND2 280-episode Astra/Claude annotation and model evaluation have NOT run.** No ND2 model performance metric is established.

## Provenance
- Source: [StudentBench, Hugging Face](https://huggingface.co/datasets/handshake-ai-research/studentbench), official revision `304c8d63c726e72b60510bba3a44454fc0726721`.
- 24 authentic `student_ai_tutor_interaction_trajectory.csv` files fetched successfully from pinned `/raw/<revision>/...` URLs, validated as CSV.
- Convenience sample: the **first four paths sorted** in each of three AI tutor arms (`gpt-5.5-high`, `opus-5-high`, `gemini-3.1-pro-high`) for both GRE Quant and GRE Verbal; 12 sessions/domain. **Not probabilistic and not representative** of all StudentBench.
- A context is the accumulated nonblank AI messages after the preceding chat turn; the immediate preceding student chat is stored separately. Measurements count characters, not model tokens.

## Actual observed results

| Metric | GRE Quant | GRE Verbal | Total |
|---|---:|---:|---:|
| Sessions | 12 | 12 | **24** |
| Event rows | 1,778 | 1,714 | **3,492** |
| Nonblank student-message turns | 282 | 182 | **464** |
| Practice-answer-submission events | 341 | 379 | **720** |
| Turns whose tutor context exceeds 950 chars | 147 | 149 | **296** |
| Share of student turns above 950 chars | 52.1% | 81.9% | **63.8%** |
| Student turns lacking an earlier student chat | 12 | 12 | **24** |
| Malformed CSV rows | 0 | 0 | **0** |

The largest assembled context observed: 24,887 chars (Quant) and 25,287 (Verbal). A 950-character hard cutoff would shorten **296/464** contexts. This is **not** a measured accuracy effect.

The 720 practice-answer submissions demonstrate that the dataset records observable work outside chat; they **do not establish** that each submission is feedback uptake. A chat-only ontology measures a narrower surface than complete learning behavior.

## Scientific critique
1. ND1 inputs with context capped at 950 chars are not preprocessing-equivalent to ND2's full-context extraction; record the intervention as a context variation and do not conflate it with an annotator improvement.
2. Treat `feedback_uptake` based on chat as a *verbal signal* unless adjacent practice and answer events are explicitly integrated and validated.
3. GRE Quant vs Verbal contrast is confounded by selected tutor arm and different turn counts. For instance, Quant Gemini has 40/149 long contexts, Quant Opus 55/64. No causal or population inference from this sample.
4. Sampling one turn uniformly per session estimates **session-weighted** annotation performance, not performance of a uniformly selected chat turn. Define the target estimand.
5. ND1 pseudonymous `NV1-...` IDs are not verifiable source-session IDs; ND1-vs-ND2 session disjointness must be checked from a private mapping.
6. Challenge-group regexes enrich keyword patterns, not necessarily rare behavioral labels. Measure actual reference support once annotations exist.

## Next experiments
- **ND2a:** freeze pinned dataset, ND1 session mapping, actual model identifiers, prompt and codebook. Obtain 200 independent session-sampled random cases + 80 separate lexical-challenge cases; independently run Astra reference and Claude. Report observed-label Macro-F1, accuracy, Wilson intervals, class support; challenge separately.
- **ND2b (ablation):** matched full-context vs 950-character input, with fixed prompts, on a *new* independently labeled set; pre-register before inspecting outcomes.
- **ND2c (construct validation):** independently review a bounded sample with chat **and** practice events to test whether uptake labels correspond to actual learner response.
- **ND3 (only after validation):** ask whether behavioral features improve pretest + practice-frequency baselines for held-out posttest prediction; split by session and prevent future-event leakage.

## Reproduce source-data audit
Install `huggingface_hub`, download pinned trajectories using `experiments/nd2_fetch_studentbench.py`, then:

```bash
python experiments/nd2_dataset_audit.py --data data/studentbench --per-arm 4
```

No raw text, participant/session rows or model-label CSVs are committed. Local Python audit code compiled and passed a **synthetic smoke test**; the genuine 24-session aggregates above were computed using the remote source CSVs. They are separate kinds of evidence.

**Decision:** Source-data accessibility and extraction audit PASS on inspected 24 sessions; **ND2 labeling/out-of-sample performance PENDING**, not a GO/PASS.
