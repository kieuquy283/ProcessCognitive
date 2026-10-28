# ND2 Annotator A — Astra (isolated agent task)

Complete independent, semantic ND2 annotations on **280 original StudentBench turns**; do not merely create a plan.

**Before starting:** Verify the exact Astra model available in the platform model selector, and the actual model ID. Read the authoritative full **frozen ND1 codebook**, including definitions and precedence rules. If the codebook, pinned source integrity, 40 ND1 source-session exclusion, or exact model confirmation is absent, STOP and report the blocker — do not infer code meanings.

Read only:
- `annotation_work/nd2/ND2_Astra_blinded_private.csv` (four immutable source columns, four blank annotation columns).
- `annotation_work/nd2/ND1_CODEBOOK_FROZEN.md` (actual research codebook, provided by coordinator).
- `annotations/ND2_SHARED_BLIND_PROTOCOL.md`.

**Forbidden:** Access to Claude/Gemini labels, ND1 Astra labels, prior model results or reports, posttest/score fields or subsequent chat turns. Do not use another LLM, a hardcoded labeler or keyword rules to do semantic labeling. Keep your own agent isolated from Claude.

For each row: label `primary_act` with exactly one of AK/AN/CQ/HR/OT/RE/VE; `feedback_uptake` with exactly one of AC/AP/NO/NR/UN; write a concise evidence-grounded `annotation_rationale`; set `confidence` high/medium/low. Use definitions **only from the frozen codebook**, not guessed acronym meanings. Preserve `episode_id`, `previous_student_excerpt`, `tutor_context`, `student_turn` byte-for-byte at parsed CSV field level and preserve all 280 row IDs/order.

Deliver: `annotation_work/nd2/astra/ND2_Astra_A_280.csv`, valid UTF-8 CSV with exactly eight original columns. Save `annotation_work/nd2/astra/model_run.json` recording `annotator: Astra`, actual verified model ID, interface/API, date, codebook/source/prompt checksums, source revision, parameters and context limits. Missing/unreadable context is a blocker, not a valid student behavior code.

Validate source integrity and all 280 filled labels with the provided `validate_nd2_annotation.py`. Report file paths/checksums and any blockers. **Do not open Claude output or calculate agreement** before the two independent annotations have been finalized. Never commit transcripts or individual labels.
