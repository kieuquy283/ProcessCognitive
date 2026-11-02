# ND2 recovery — 2026-11-02

**Status: annotation blocked; 0/280 completed.** No actual 280-case source data or annotator outputs have been created.

## Verified source correction
The original pilot-frozen ND1 v0.1 codebook is present in `research/studentbench-diagnostics/docs/ND1_behavioral_moves_feedback_uptake_codebook_v0.1.md` (Git blob `02468a3a5330ec39eadd7582f677444b6ff9be4a`). It defines **7 primary acts** (RE,VE,CQ,HR,AN,AK,OT) and **6 uptake labels** (NO,NR,AC,AP,RV,UN). `RV` is a reasoned revision, not a synonym for AP. Zero RV examples in the 40-record pilot does **not** authorize deleting RV. The previous ND2 validation scripts incorrectly allowed only five uptake codes; the main `nd2_pipeline.py` and `validate_nd2_annotation.py` have now been corrected to include RV.

## Outstanding data gates
- Original 40 ND1 episodes use deterministic `NV1-` IDs derived from the released GRE Quant session path and event position. Local recovery tooling can check all 40 against the pinned original StudentBench release; **full real-data source mapping has not been executed and signed**.
- The prior GitHub Actions 200+80 real-data run was only an **aggregate preflight**; it did not persist or securely deliver 280 private student turns. The three blinded CSVs in the previous handoff remain 0-row templates.
- The original v0.1 codebook is frozen for the **ND1 pilot**, but has not been explicitly reviewed/approved as the **ND2** measurement instrument after the RV/schema correction. Approval is a researcher decision, not an automated script flag.
- Original event ID matching is not a substitute for independent content/provenance review; student text and full context require PII screening before sending to external models.

## Reproducible preparation in a networked workspace
A corrected local handoff contains `PREPARE_ND2_SOURCE_ON_NETWORKED_MACHINE.sh`, `RECOVER_ND1_SESSIONS_FROM_IDS.py`, and a corrected six-code validator. Run the shell script from the repository root after placing the private ND1 40-row Astra reference in `annotation_work/ND1_Astra_A_40.csv`. It authenticates the original ND1 codebook Git blob, fetches pinned StudentBench, reconstructs matching session keys, and writes **private candidate** Astra/Opus/Sonnet 280-row CSVs. A synthetic 40-case ID-to-session-key test passed; **not evidence of real ND1 mapping**.

Human approval + a passed provenance/PII review must precede releasing candidate CSVs for Astra/Opus 4.6/Sonnet 4.6. Do not publish transcripts or annotations in this public repository. The final ND2 holdout evaluation remains PENDING.
