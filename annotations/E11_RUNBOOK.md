# E11 — Operational runbook

**Status:** 400 true StudentBench concept–subskill pairs sampled and checked. All 400 labels are EMPTY; no human-valid mapping results exist.

## Ground rules

GPT-6 Astra labels from E9c (120 pairs) may be assumed a SILVER reference for experiments, but do not call them verified human ground truth. E11's 400 pairs explicitly exclude all 120 previously labeled exact pairs.

The 400-case sample is three distinct panels (200 uniform unique-pair probability sample, 150 likely-match enrichment, 50 generic-strategy stress). **Do not infer D prevalence from all 400**. This can only be estimated over the unique-pair universe using the 200 uniform sample after reliable reference labeling.

## Step 1: independent annotation

Use two DIFFERENT, FRESH agent conversations and isolated local workspaces on research branch research/studentbench-diagnostics.

A — Codex, GPT-6 Astra: paste instructions in [E11_CODEX_A_TASK.md](E11_CODEX_A_TASK.md).

B — Antigravity, Gemini: paste instructions in [E11_ANTIGRAVITY_B_TASK.md](E11_ANTIGRAVITY_B_TASK.md).

Both read exactly [E11_COMMON_LABELING_CODEBOOK.md](E11_COMMON_LABELING_CODEBOOK.md) and [e11_pairs_blinded_400.csv](templates/e11_pairs_blinded_400.csv); neither sees results from the other, nor previous Astra annotations. Do not use a regex/Python model to assign labels. Save completed CSVs only under ignored annotation_work/.

A output: annotation_work/e11_astra/e11_annotator_A.csv.
B output: annotation_work/e11_gemini/e11_annotator_B.csv.

## Step 2: validate independently

From repo root:

```bash
python experiments/e11_validate_labels.py --source annotations/templates/e11_pairs_blinded_400.csv --file annotation_work/e11_astra/e11_annotator_A.csv
python experiments/e11_validate_labels.py --source annotations/templates/e11_pairs_blinded_400.csv --file annotation_work/e11_gemini/e11_annotator_B.csv
```

Each validator must return PASS_FORMAT_ONLY_NOT_LABEL_ACCURACY. Output must have 400 filled rows, exact original row order and six columns.

## Step 3: recover private stratum sidecar for analysis

Install dependencies from requirements-research.txt, then download original StudentBench dataset **at commit 304c8d63c726e72b60510bba3a44454fc0726721**.

Regenerate the same samples locally (only if the full pinned source files are present):

```bash
python experiments/e11_prepare_mapping_sample.py --data ./data --out-dir annotation_work/e11_rebuild
# Verify byte-wise identical public blinded input before using analyst-only strata:
cmp annotation_work/e11_rebuild/e11_blinded_400.csv annotations/templates/e11_pairs_blinded_400.csv
```

If the files differ, STOP: do not pair wrong sampling strata or substitute another release silently.

Analyst-only sidecar: annotation_work/e11_rebuild/e11_analyst_sidecar_PRIVATE.csv. **Neither annotator should read it**.

## Step 4: model agreement and human review preparation

Only after both agents finish, in a THIRD research workspace:

```bash
python experiments/e11_evaluate_agreement.py \
 --source annotations/templates/e11_pairs_blinded_400.csv \
 --model-a annotation_work/e11_astra/e11_annotator_A.csv \
 --model-b annotation_work/e11_gemini/e11_annotator_B.csv \
 --sidecar annotation_work/e11_rebuild/e11_analyst_sidecar_PRIVATE.csv \
 --out annotation_work/e11_agreement.json \
 --audit-out annotation_work/e11_human_review_blinded_160.csv
```

It produces overall & per-stratum model-model kappa, a binary D-vs-rest kappa, confusion counts and a THIRD blinded CSV of **160 review pairs: 80 randomly selected from the 200 uniform, 60 from 150 enriched, 20 from 50 strategy stress**. It never includes model labels/confidences in the human file.

## Step 5: construct-validity review and E11 predictive follow-up

Have preferably two GRE mathematics experts independently review the 160 blinded pairs. If only one, report an expert reference, NOT human inter-annotator reliability. Reserve some of those pairs for an out-of-sample codebook validation after adjudication.

Estimate D-class precision/recall, confusion and error categories on **human-rated pairs**. Use only the uniform 200-pair panel (or randomly selected human subset thereof) to assess class prevalence among unique pairs. Do not generalize it to messages, tutoring encounters or people.

**Only after mapping validity is demonstrated**, freeze one mapping model and rerun an independent posttest prediction experiment with a detailed pretest/practice baseline, concept bag, true alignment and within-session shuffled controls. Check session-level grouping, previously explored splits and model-selection bias. No E11 holdout metric exists yet.

## Prior E11 silver diagnostic — already executed

See [E11 report](../reports/E11_validated_mapping_sampling_silver_transfer_2026-10-24.md). Astra D has only 5 positives in 120 original labels. Subskill-grouped four-class CV D F1 is only 0.182; applying the uncalibrated class-weighted model to new E11 data produced 167 apparent D predictions out of 400. These are NOT validated D cases or measured true-positive counts.
