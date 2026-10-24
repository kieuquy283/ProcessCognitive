# TASK — Annotator A: GPT-6 Astra in Codex

Select "GPT-6 Astra" in Codex's model picker, not an automatically substituted model. Use a FRESH Codex conversation and a separate workspace/clone from Antigravity.

Read and obey the EXACT COMMON RESEARCH CODEBOOK:
annotations/E9c_COMMON_TASK_CODEX_ANTIGRAVITY.md

Read the SAME blinded input that Annotator B receives:
annotations/templates/e9c_pairs_blinded.csv

YOUR ONLY OUTPUT FILE:
annotation_work/codex_astra/e9c_annotator_A.csv

The current GPT-6 Astra model itself must semantically judge ALL 120 pairs using the shared codebook, with label D/S/N/U and a brief English rationale. Do NOT call another LLM or external API, use string-matching labeling code, inspect the Gemini output, consult E9 study results, change input/rubric or commit completed labels. Python is permitted only for reliable CSV IO and format checks.

After saving, VALIDATE:
python experiments/e9c_validate_cross_platform.py --file annotation_work/codex_astra/e9c_annotator_A.csv --source annotations/templates/e9c_pairs_blinded.csv

Do not see or access annotation_work/antigravity_gemini/ or the other model's results before you finish.
At completion report the actual model shown in the Codex UI, 120/120, file path, validator PASS and any unresolved uncertainty. Do not compute agreement with Gemini.
