# ND2 private input status (2026-11-02)

## Why the three files are missing
The project intentionally does not commit episode-level StudentBench dialogue or original ND1 annotation codebooks into GitHub. The previous successful GitHub Actions run produced **aggregate 200+80 preflight statistics only**; it did not release 280 source rows or a completed ND2 sample. Thus these files do not legitimately exist in the repository:

- `annotation_work/nd2/ND2_Astra_blinded_private.csv`
- `annotation_work/nd2/ND2_Claude_blinded_private.csv` (Opus 4.6)
- `annotation_work/nd2/ND1_CODEBOOK_FROZEN.md` (original approved semantic codebook, still unavailable)

An updated local handoff bundle was created with **header-only 0-row placeholders** for the two CSV names (also a Sonnet 4.6 alternative), and a **NOT_VERIFIED / BLOCKED placeholder** for the codebook. THESE ARE NOT VALID ANNOTATION INPUTS.

## Authoritative codebook gate
The ND1 40-row Astra reference exists in the private research workspace but contains labeled examples and rationales, **not a complete verified label-definition/precedence codebook**. GitHub branch and connected Drive search did not find the original. Do not infer or pretend it is frozen. Require independently reviewed original codebook or a transparently new ND2-v2 rubric validated separately.

## How to generate authentic data privately
Use the pinned official StudentBench commit `304c8d63c726e72b60510bba3a44454fc0726721`, original 40-row ND1 Astra source, verified 40-source-session mapping, and human-reviewed provenance attestation. Download data locally with `experiments/nd2_fetch_studentbench.py`; reconstruct and review source matches with `experiments/nd2_reconstruct_nd1.py`. Then use the handoff `GENERATE_REAL_ND2_INPUTS.py` script alongside the current repository's `experiments/nd2_pipeline.py`.

The generator must reject placeholder codebooks and unreviewed/missing provenance, produce exactly **200 random + 80 challenge = 280 distinct sessions**, and ensure the Astra, Opus 4.6 and Sonnet 4.6 blinded CSVs contain identical immutable input fields and **blank** annotation columns.

Never commit private CSVs, source transcripts, input mapping or generated labels. Codebook and provenance reviewers must sign approvals before annotation begins.

This is a preparation status, **not** a claim that Astra, Opus 4.6 or Sonnet 4.6 completed the ND2 annotations.
