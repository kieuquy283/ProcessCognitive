# ND2 implementation status — 2026-10-27

This is an implementation checkpoint, **not an ND2 experiment result**.

## Frozen design
- 200 natural student-turn samples and 80 challenge student-turn samples; distinct session per sample, challenge analysis separate from natural sample.
- Astra is a **conventional reference**; Claude is evaluated independently. No claim that this is validated human ground truth.
- Source: pinned official StudentBench dataset. Do not commit released individual tutoring trajectories or labels with raw text.
- Primary metrics: accuracy and observed-label Macro-F1 of primary_act; feedback_uptake accuracy; joint exact accuracy; label support and error analysis.

## Implementation and smoke test
A local Python ND2 pipeline and test have been authored and exercised with **synthetic fixtures only**, not raw StudentBench. It includes:
1. GRE Quant and Verbal trajectory discovery.
2. Session-based sample selection with a fixed seed 27102026, with a 200 natural / 80 challenge split.
3. Blinded inputs for Astra and Claude, preserving episode ID and source inputs.
4. Schema and source-text identity checks before scoring.
5. Separate evaluation of random and challenge splits.

The executable files are **not yet committed in this branch**; they must undergo a source-code review and be committed from the research workspace. Do not interpret this PR as a deployed pipeline.

## Gates not yet satisfied
- A complete, pinned local release of StudentBench is not available to this run. Therefore 280 authentic ND2 episodes have **not** been sampled or annotated.
- Genuine ND1 source-session provenance must be reconciled with ND2; random opaque ND1 episode IDs alone do not establish session-disjointness.
- The exact ND1 codebook, prompt version and verified Astra / Claude model IDs must be frozen before either annotation.
- Actual results, uncertainty intervals, class coverage, expert-validation pilot and ND2 decision require genuine annotations.

## Evidence standard
ND1's 80% primary-act and 95% uptake agreement relative to Astra is developmental evidence only. Do not restate these as ND2 results or report a GO/PASS for ND2 before independent evaluation.
