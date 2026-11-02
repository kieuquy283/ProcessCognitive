# ND2 Annotator C — Claude Sonnet 4.6 (independent comparison)

Use **Claude Sonnet 4.6**, canonical Claude API ID `claude-sonnet-4-6`. Do not silently use a default model or a substituted Sonnet version. The model's identity and version must be verified in its actual UI or model request logs.

This is a third, **independent** annotation arm for the SAME 280 StudentBench student turns used by Astra A and Opus 4.6 B. Its purpose is to compare per-label reliability, accuracy against the Astra conventional reference and efficiency—not to vote with Opus or create a human ground truth.

**Gates:** DO NOT start until the authoritative full ND1 codebook (definitions, precedence and examples), verified ND1→session exclusion, and pinned data/source checksums are available. The procedural shared document is NOT a substitute for the semantic codebook.

You may read ONLY:
- `annotation_work/nd2/ND2_Sonnet46_blinded_private.csv` created by copying the exact first four input columns and blank annotation columns from `ND2_Claude_blinded_private.csv`;
- `annotation_work/nd2/ND1_CODEBOOK_FROZEN.md`;
- `annotations/ND2_SHARED_BLIND_PROTOCOL.md`;
- this task.

**Do not read** Astra or Opus annotations, prior ND1 labels, disagreement reports, outcome scores, future messages, or hidden research statistics. Use source text and context only; never rule-based keyword labeling or delegation to another model.

Return EXACT eight CSV columns, without adding or modifying any source text or changing order:
```csv
episode_id,previous_student_excerpt,tutor_context,student_turn,primary_act,feedback_uptake,annotation_rationale,confidence
```
- `primary_act`: one of AK, AN, CQ, HR, OT, RE, VE.
- `feedback_uptake`: one of AC, AP, NO, NR, UN.
- `annotation_rationale`: short, nonempty, evidence-grounded English explanation, NOT a copy of another annotator's rationale.
- `confidence`: high / medium / low.

Output only to PRIVATE `annotation_work/nd2/sonnet46/ND2_Sonnet46_C_280.csv`. Save `annotation_work/nd2/sonnet46/model_run.json` with exact `annotator: "Sonnet46"`, `verified_model_id: "claude-sonnet-4-6"`, interface or API, run date, source/codebook/prompt hashes, actual inference settings and any context truncations. Use the repository's three-model validator after outputs are independently finalized.

Never commit raw transcripts, row-level labels, model outputs or session maps to GitHub. Report file paths and real completion counts, not a quality score before comparison.
