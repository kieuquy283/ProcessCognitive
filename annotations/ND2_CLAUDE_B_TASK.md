# ND2 Annotator B — Claude Opus 4.6 (isolated agent task)

Complete ND2 annotations on the **same frozen 280 original StudentBench turns**, independently of Astra.

**Preflight:** Require the full authoritative ND1 codebook with examples/precedence, verified session-disjoint dataset, matching source checksum and correct model. **Use Claude Opus 4.6; API model ID `claude-opus-4-6`.** Verify the actual model shown by the platform and its request metadata; **do not silently substitute any other Claude version**, including Opus 5.5 or Sonnet 4.6. Model selection differs from the earlier ND1 Claude Opus 5.5 pilot and therefore tests a different model. If the approved model is unavailable, STOP and disclose the actual available model ID.

Read only:
- `annotation_work/nd2/ND2_Claude_blinded_private.csv` (same cases; zero other-model labels).
- `annotation_work/nd2/ND1_CODEBOOK_FROZEN.md`.
- `annotations/ND2_SHARED_BLIND_PROTOCOL.md`.

Never inspect Astra output, old ND1 outputs, Gemini labels, agreement statistics or downstream posttest outcomes. Never use an external model to choose categories. For each of 280 student turns, use source `student_turn` and only its pre-turn context, frozen codebook and precedence. Write exactly one `primary_act` of AK/AN/CQ/HR/OT/RE/VE and exactly one `feedback_uptake` of AC/AP/RV/NO/NR/UN, a short English evidence-based `annotation_rationale`, and high/medium/low confidence.

**Immutable** input columns: `episode_id,previous_student_excerpt,tutor_context,student_turn`. Do not reorder, edit or drop any row; quote CSV correctly. Stop and flag incomplete/transmission-truncated records; never use `UN` to hide unread data.

Save `annotation_work/nd2/opus46/ND2_Opus46_B_280.csv` as UTF-8 with the eight-column original schema. Save `annotation_work/nd2/opus46/model_run.json` with real verified model ID, source/codebook/prompt SHA-256, date, interface, generation settings and any read limitations. Run the provided structural validator; report completion, not agreement. Keep student-level results private and **do not access Annotator A** before all three files (Astra, Opus 4.6, Sonnet 4.6) are finalized.
