# E9c: two independent GPT annotation runs

**Status:** Shared codebook and executable runner are ready and dry-run validated. **No billed GPT calls or completed annotations have been made by this branch.**

This is **AI–AI agreement**, **not** human inter-rater reliability. For scientific construct validation, independently collected human annotations remain recommended.

## Fixed design

| Attribute | Definition |
|---|---|
| Source | [120 blinded real-data concept/subskill pairs](templates/e9c_pairs_blinded.csv) |
| Annotator A | `gpt-6-luna` |
| Annotator B | `gpt-5.6-terra` |
| Shared instructions | [E9c_shared_gpt_prompt_v1.md](E9c_shared_gpt_prompt_v1.md) |
| Task | Choose D=direct mathematical coverage, S=general strategy, N=no meaningful relation, U=undetermined |
| Isolation | Separate stateless Responses API requests, no previous-response IDs, no shared memory, neither model sees the other's outputs |
| Format | Strict JSON Schema, validated pair IDs and label values, CSV records preserving original IDs/order |
| Batch | 12 pairs per request, 10 independent calls/model (20 calls total if no retries) |
| Retention | `store=False`, results and request metadata saved locally under ignored `annotation_work/` |
| Analysis | Four-class Cohen's kappa, raw agreement, binary kappas, confusion matrix, conflict list |

## To execute (paid OpenAI API)

From repository root, install dependencies and set the API key in your local environment (never commit it):

```bash
pip install -r requirements.txt -r requirements-research.txt

# On macOS/Linux:
export OPENAI_API_KEY="YOUR_SECRET_API_KEY"

# Safe preview: verifies 120 items and prints two model IDs and hashes, zero requests:
python experiments/e9c_dual_gpt_annotate.py

# Start paid API labeling:
python experiments/e9c_dual_gpt_annotate.py --execute
```

The script writes:

```text
annotation_work/gpt_independent_e9c/
  run_manifest.json
  gpt-6-luna_annotations.csv
  gpt-5.6-terra_annotations.csv
  completed_runs.json
  gpt-6-luna/batch_000.json ... batch_009.json
  gpt-5.6-terra/batch_000.json ... batch_009.json
```

Each model gets identical shared rubric and the same pairs in the same order. No outputs are included in the other's prompt. Checkpoint/resume reuses **only the same model's own** verified completed batches. Do not modify the prompt or input sample halfway through. If you want a different model pair or rubric, use a new output directory.

When both complete, run:

```bash
python experiments/e9c_agreement.py \
  --source model \
  --model-a gpt-6-luna \
  --model-b gpt-5.6-terra \
  --annotator-a annotation_work/gpt_independent_e9c/gpt-6-luna_annotations.csv \
  --annotator-b annotation_work/gpt_independent_e9c/gpt-5.6-terra_annotations.csv \
  --output annotation_work/gpt_independent_e9c/model_agreement.json \
  --disagreements annotation_work/gpt_independent_e9c/model_disagreements.csv
```

Check that the output status is `GPT_GPT_MODEL_ANNOTATION_COMPLETED`, not `HUMAN_ANNOTATION_COMPLETED`.

## Interpret carefully

- **Agreement ≠ correctness**: Models sharing training sources and biases can agree on an incorrect mapping.
- Kappa from two GPTs is **not human inter-rater reliability**; report it as *model–model nominal agreement*. Independent human arbitration is strongly advised for D↔S disagreements.
- The 120-pair set is stratified by cosine similarity and generic concept classes. Raw sample proportions are **not** prevalence estimates for the 53,973 candidate pairs.
- If both models agree, it does **not** validate the mapping against ground truth; human-reviewed labels must be used for construct-validity claims.
- Both models call a billable API. Pricing and availability depend on the user's account, model and token usage. Running this script requires an explicit `--execute` flag. It was **not** run using the user's API credits by ChatGPT in this conversation.
- Do not push `annotation_work/` model outputs or secrets to the public repo without a separate disclosure review. Only the unlabelled de-identified sample is public.

API sources: https://developers.openai.com/api/docs/models/gpt-6-luna ,
https://developers.openai.com/api/docs/models/gpt-5.6-terra ,
https://developers.openai.com/api/docs/guides/structured-outputs .
