# ND2: Coordinator's ready-to-run handoff

**Prepared:** 2026-10-28. **Status:** prompts and validators prepared; the 280-row authentic label sheets and genuine Astra/Claude annotations are NOT yet completed.

- Source: `handshake-ai-research/studentbench`, revision `304c8d63c726e72b60510bba3a44454fc0726721`; sampling seed `27102026`.
- Use the existing `experiments/nd2_fetch_studentbench.py`, `experiments/nd2_reconstruct_nd1.py`, `experiments/nd2_pipeline.py`.
- Frozen classes: `primary_act` AK/AN/CQ/HR/OT/RE/VE, `feedback_uptake` AC/AP/NO/NR/UN; confidence high/medium/low.
- **Unresolved blocker:** the repository branch contains no verified complete ND1 codebook defining the semantic codes and their precedence rules; do NOT have models guess from old CSVs. Independently corroborate all 40 ND1 source session IDs before sampling.

## Phase 0: Freeze and protect

1. Place authorized, complete ND1 codebook in PRIVATE `annotation_work/nd2/ND1_CODEBOOK_FROZEN.md` after review and record SHA-256. Do not accept old example rationales or E9c rubrics as a replacement.
2. Put the previously collected ND1 Astra CSV in PRIVATE `annotation_work/ND1_Astra_A_40.csv`.
3. On a networked local machine, download the pinned dataset and reconstruct session mapping:
```bash
python -m pip install huggingface_hub pandas numpy scikit-learn
python experiments/nd2_fetch_studentbench.py --data-dir data/studentbench
python experiments/nd2_reconstruct_nd1.py --data data/studentbench \
  --nd1 annotation_work/ND1_Astra_A_40.csv \
  --out annotation_work/nd2/ND1_source_match_audit_private.csv
```
4. All 40 ND1 records must be linked to trustworthy source sessions and independently checked. If ambiguous, manually resolve and document. Make private `ND1_sessions_private.csv` with `episode_id,session_key`, each key a 20-char SHA-256 prefix using the repo's exact algorithm. Keep reviewer/date/file-hashes attestation. **Do not represent automated unique text matches alone as conclusive provenance.**
5. Run the standalone `validate_nd2_annotation.py source-gate` script from the handoff package. Stop on any failure.

## Phase 1: Create the actual private 280 inputs

```bash
python experiments/nd2_pipeline.py sample \
 --data data/studentbench --nd1 annotation_work/ND1_Astra_A_40.csv \
 --nd1-sessions annotation_work/nd2/ND1_sessions_private.csv \
 --outdir annotation_work/nd2 --seed 27102026
```
Check 280 unique session keys, 200 random / 80 challenge, no overlap with ND1 mapping, and frozen source/checksums. Previous 200+80 Github Actions data was just **feasibility preflight**, no source rows persisted. This command is the real private export.

## Phase 2: Two isolated annotators
- Astra receives ONLY `ND2_Astra_blinded_private.csv`, the same frozen codebook, `annotations/ND2_SHARED_BLIND_PROTOCOL.md`, and `annotations/ND2_ASTRA_A_TASK.md`. Writes `annotation_work/nd2/astra/ND2_Astra_A_280.csv` and model metadata.
- Claude receives ONLY `ND2_Claude_blinded_private.csv`, the same frozen codebook, common protocol and `annotations/ND2_CLAUDE_B_TASK.md`. Writes `annotation_work/nd2/claude/ND2_Claude_B_280.csv` and model metadata.
- Two separate workspaces; never share prior annotation results, source outcome fields or future context. Actual model IDs must be verified; do not relabel a substitute model.
- All outputs and model run metadata stay in `annotation_work/`. Never post individual chat data to PR/issue/workflow logs.

## Phase 3: Validate before evaluating
Use `validate_nd2_annotation.py annotations` with `--source`, `--manifest`, `--astra`, `--claude`, `--codebook`, `--astra-meta`, `--claude-meta`. Compare original inputs, 280-row order, label vocabulary, hashes, provenance. After success, run `experiments/nd2_pipeline.py evaluate` using the 200/80 manifest. Report 200 random as headline; 80 challenge separately. All claims remain Astra-conventional-reference, not human ground truth.

**DO NOT call ND2 completed** until both model outputs exist, source/mapping provenance and codebook have been documented, and independent evaluation has run. A separate human validity audit is still required before claims about learning behavior constructs.
