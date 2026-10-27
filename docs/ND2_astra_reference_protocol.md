# ND2 — Astra-reference out-of-sample protocol

**Status:** Protocol only; ND2 has not been sampled, annotated, or evaluated.

ND1 report: [Astra-reference 40-turn pilot](../reports/ND1_astra_reference_2026-10-27.md).

## Research questions

1. **Fidelity:** Can Claude reproduce Astra's `primary_act` and `feedback_uptake` on unseen StudentBench turns?
2. **Class coverage:** What happens on infrequent labels and ambiguous `AK/OT`, `RE/VE`, `AC/NR` cases?
3. **Selective prediction:** Does Claude's self-reported confidence identify cases needing independent human review?
4. **Exploratory transfer:** Are the findings similar across GRE Quant/Verbal and tutor configurations, where data are available?

Astra is **conventional/silver reference** here, not independently confirmed ground truth. Fidelity alone cannot validate the ontology or establish effects on achievement.

## Pre-register and freeze

Before drawing test labels, freeze and store versions/hashes of (a) codebook and precedence rules, (b) prompts, (c) exact callable model identifiers and settings, (d) source-dataset revision, (e) sampling seed and inclusion criteria. If rules change after ND1, version them; never retroactively rewrite ND1 outcomes. Hide all other annotators' predictions from each annotator.

## Sampling plan — 280 new student turns

- **200 randomly sampled turns** (primary representative estimate). Sample from independent sessions; stratify GRE Quant/Verbal or tutor arm only if feasible and record sampling weights or strata to avoid presenting an enriched sample as a population estimate.
- **80 challenge turns** (stress evaluation), about 20 each for: AK/OT-like task coordination; RE/VE-like reasoning versus checking; HR/CQ/VE-like help and verification; AC/NR/NO/UN-like feedback opportunities. Select by observable content, without assigning target labels in advance.
- Neither subset may overlap ND1; preserve session-disjoint development/test boundaries. Do not split turns from the same session across development and test.
- StudentBench's `student_id` may indicate a session rather than a unique person; verify documentation before claiming participant-level independence.
- Save a private sampling manifest: source revision, session ID, turn index, domain, tutor condition, selection stratum, input context and any truncation flag.
- Do not truncate at 950 characters by default; any unavoidable truncation must be recorded.

Keep random and challenge metrics **separate**; do not pool them to imply representative accuracy.

## Annotation and validation

1. Extract and validate 280 source inputs, check uniqueness and ND1 overlap.
2. Astra independently labels two dimensions plus rationale/confidence. Freeze Astra CSV as the reference.
3. Claude independently labels the same inputs without viewing Astra or earlier Gemini results. Verify the model identifier used; never silently substitute another model.
4. Assert one-to-one mapping by sample ID and source text, labels within the frozen codebook, no missing values, deterministic processing and run metadata.
5. Preserve both raw annotation CSVs **locally**, never in Git.

## Measurements

For **200 random turns**, report `primary_act` accuracy (primary endpoint), supported-class macro-F1, `feedback_uptake` accuracy, and exact accuracy across both labels. Also report per-class precision/recall/F1/support, confusion matrices, Cohen's kappa and breakdown by domain, missing context and tutor arm when sample sizes allow.

For the **80 challenge turns**, report the same metrics descriptively and discuss failure modes **separately**. Do not claim unbiased population performance from the challenge subset.

- Classes with zero reference support are **not estimable** (N/A), not F1=0.
- Classes with fewer than 10 reference examples are exploratory.
- Use confidence intervals respecting session clustering (e.g., cluster bootstrap with fixed seed) if more than one turn per session. If genuinely independent, consider Wilson intervals for accuracy.
- Predefine confidence-based coverage thresholds and report risk–coverage performance; do not select a threshold on the held-out set and then market it as independently validated.
- Keep secondary comparisons clearly marked and adjust for multiple testing when inferential claims are made.

## Proposed decision rules (design targets, not ND1 achievements)

**GO** to downstream behavioral modeling only if on the *200 random* subset:
- Primary-act accuracy ≥ 0.80
- Primary-act macro-F1 (reference-supported labels) ≥ 0.75
- Feedback-uptake accuracy ≥ 0.90
- Joint exact accuracy ≥ 0.75
- Schema/source alignment is perfect; no major systematic failures hidden by label imbalance

**REVISE** if numeric performance or specific boundaries are inadequate but rules remain interpretable. **RECONSIDER** if labels require unobservable assumptions or are not valid measures of behavior. These thresholds are provisional research targets, not established external benchmarks.

Regardless of passing thresholds, conduct a blinded human/expert audit (suggested 30 random + 10 challenging turns) if possible to test construct validity independently of Astra. Keep human agreement separate from Astra-fidelity estimates.

## Outputs and data safeguards

Local-only (under ignored `annotation_work/` or `results/`):

- Sampling manifest and episode/session IDs; episode inputs and annotations for Astra/Claude
- Validation results, full confusion matrices, row-level errors, metrics and plots
- Run logs: source revision, prompt/codebook hashes, model identifiers, seed and date

Safe to commit: code, protocol, **aggregate** statistics and report text with no raw transcripts, row-level participant records or keys. Do not publish the local CSVs.

## Research trajectory after ND2

Only after reproducibility and construct validity are evaluated should the study test whether label sequences add predictive value for independent posttest outcomes beyond strong baselines (pretest, practice correctness, session length and turn counts). Use appropriate session-disjoint evaluation and avoid future-information leakage. Observational associations do not prove causation.

## References

- StudentBench: https://huggingface.co/datasets/handshake-ai-research/studentbench
- Calderon et al. (ACL 2025), *Alternative Annotator Test*: https://aclanthology.org/2025.acl-long.782/
