# E9c: Codex Astra and Antigravity Gemini independent annotations

Status: **READY; no real labels have been generated.**

Read the [shared codebook](E9c_COMMON_TASK_CODEX_ANTIGRAVITY.md), which is identical for both agents. Each receives the [same 120 blind concept–subskill pairs](templates/e9c_pairs_blinded.csv).

## Step 1: Codex

Open a fresh Codex workspace and chat, choose GPT-6 Astra manually, and assign [CODEX_A_TASK.md](CODEX_A_TASK.md). Output: `annotation_work/codex_astra/e9c_annotator_A.csv`.

## Step 2: Antigravity

Open a separate Antigravity workspace and new chat, choose Gemini 3.8 Flash manually, and assign [ANTIGRAVITY_B_TASK.md](ANTIGRAVITY_B_TASK.md). Output: `annotation_work/antigravity_gemini/e9c_annotator_B.csv`.

Never expose A's labels to B or vice versa until **both are completely finished and validated**. Record exact model labels and versions shown in the product UI, as platform names/availability can differ from public API model IDs.

## Step 3: Analyze in a third workspace

Copy both finished CSV files to a new analysis-only workspace, then run:

```bash
python experiments/e9c_agreement.py --source model \
  --model-a "GPT-6 Astra (Codex)" \
  --model-b "Gemini 3.8 Flash (Antigravity)" \
  --annotator-a annotation_work/codex_astra/e9c_annotator_A.csv \
  --annotator-b annotation_work/antigravity_gemini/e9c_annotator_B.csv \
  --output annotation_work/e9c_cross_model_agreement.json \
  --disagreements annotation_work/e9c_disagreements.csv
```

Calculate raw agreement, four-class Cohen kappa, binary kappas and confusion matrix. Report this as **AI–AI agreement, not human inter-rater reliability**. Do not regard consensus as ground truth: independently human-audit a sample of agreements and the D/S disagreements.

No transcript text, assessment scores or identity fields are sent to annotators. Do not commit final labels until disclosure is reviewed. All generated outputs belong under ignored `annotation_work/`.

Tools: [cross-platform CSV validator](../experiments/e9c_validate_cross_platform.py), [agreement script](../experiments/e9c_agreement.py).
