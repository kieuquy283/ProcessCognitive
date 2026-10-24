# E9c annotation pilot

This folder contains **one real-data-derived, blinded, unlabelled 120-pair pilot**:

- [e9c_pairs_blinded.csv](templates/e9c_pairs_blinded.csv): 120 unique GRE quantitative subskill ↔ AI-generated lesson-concept title candidate pairs. Labels and rationale fields are intentionally empty.

## Annotator instructions

1. Each of two independent annotators downloads a **separate copy**; name them `e9c_annotator_A.csv` and `e9c_annotator_B.csv`.
2. Without consulting an embedding cosine score, model prediction, other annotator or the student's test performance, choose one of four labels:
   - **D:** direct mathematical content coverage;
   - **S:** related exam strategy, but not direct content coverage;
   - **N:** no meaningful relationship;
   - **U:** insufficient information from concept/subskill titles.
3. Write a short rationale for any unclear or disputed pair. Do not change `pair_id`, `gre_subskill` or `tutoring_concept_title`.
4. Keep the completed sheets locally under `annotation_work/` (ignored by Git), not in the public repository. This avoids public raw judgments becoming unblinded for other annotators.
5. Once both independent sheets are complete, run:

```bash
python experiments/e9c_agreement.py \
  --annotator-a annotation_work/e9c_annotator_A.csv \
  --annotator-b annotation_work/e9c_annotator_B.csv \
  --output annotation_work/e9c_agreement.json
```

The script computes raw agreement, nominal four-class Cohen's kappa, D-vs-non-D and (D or S)-vs-others kappas, confusion matrix, and private disagreements. It **fails** on blank labels. No human annotation has been completed yet.

Related resources:
- [Research protocol](../docs/E9c_annotation_protocol_v0.1.md)
- [Sampling and data audit](../reports/E9c_sampling_audit_2026-10-24.md)
- [Reproducible sample generation](../experiments/e9c_sample_pairs.py)

The pilot is stratified by lexical-semantic rank and generic strategy type. It cannot estimate population-level mapping error rates without accounting for selection probabilities. The labels measure relation of **concept titles** to **GRE subskills**, not student mastery.

## Optional: two independent GPT model annotators

For an **AI–AI comparison** (not a substitute for two independent human coders), use the [fixed shared E9c prompt](E9c_shared_gpt_prompt_v1.md) and [dual-GPT execution guide](E9c_dual_GPT_execution_guide.md).

The runner uses `gpt-6-luna` and `gpt-5.6-terra`, identical 120 blind pairs, separately stateless calls, local model-specific output files, and explicit opt-in for billed API requests. See `experiments/e9c_dual_gpt_annotate.py`. **No real API annotations were run by the research assistant; only code and mock/dry-run validations.** Always use `e9c_agreement.py --source model` for AI–AI results so that model agreement is never presented as human reliability.
