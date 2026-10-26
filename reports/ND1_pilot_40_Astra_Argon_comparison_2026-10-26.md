# ND1 — Pilot 40: Astra × Gemini 4 Argon, blind silver-label comparison

**Analysis date:** 26 October 2026. **Source:** user-supplied `ND1_Astra_A_40.csv` and `ND1_Gemini4Argon_B_40.csv`. Model identities are researcher-provided and cannot be authenticated from CSV alone.

## Data quality

Both files contain 40 unique identically ordered episode IDs and exact matching source fields, all labels/rationales valid (rationale 8–35 words, all confidence levels in allowed values). After restoring blank annotations to the user-supplied Astra CSV, byte-reencoded CSV SHA-256 **matches the original independent 40-case source file**: `47eb2637083b1101720eb172fee0f08ce97e3de33df924dafe847b357f0ac4c9`.

All raw student dialogue, rationales, private IDs and case-specific comparisons remain **outside public GitHub**.

## Results

| Comparison | Agreement | Cohen κ |
|---|---:|---:|
| Primary Act | **30/40 = 75.0%** | **0.7006** |
| Feedback Uptake | **33/40 = 82.5%** | **0.7146** |
| Both axes simultaneously | **25/40 = 62.5%** | Not applicable as a single-axis measure |

There are **15 unique episode disagreements**, 10 on Primary Act and 7 on Feedback Uptake, with overlap in two episodes.

**Primary Act label counts (Astra / Argon):** RE 8/6, VE 5/9, CQ 3/3, HR 7/7, AN 10/7, AK 6/7, OT 1/1.

**Feedback Uptake counts:** NO 0/3, NR 1/2, AC 18/14, AP 19/19, RV **0/0**, UN 2/2.

**Most important negative finding:** Zero positive `RV` labels in either model. The pilot consequently **does not assess reliability or recall for the ontology's central claim, reasoned revision after feedback**. AI–AI agreement around κ≈.70 does NOT establish expert-grounded validity. Tutor excerpts can be truncated (five visible at the 950-character cap in these 40 cases). Argon reports 34/40 high confidence, Astra 23/40; self-reported confidence is not calibration.

## Major disagreements and codebook questions

1. **AN vs RE; RE vs VE:** distinguish a bare mathematical answer/claim from actual substantive justification and distinguish a check from a reasoned solution.
2. **CQ vs HR:** distinguish a conceptual explanation request from vague desire for more procedural detail.
3. **NO vs AC vs NR:** establish whether a completed worked example with no next action is still actionable tutor guidance; classify topic repair and interface problems without guessing disengagement.
4. **AC vs AP:** an isolated 'yes' shows acknowledgment, not application; a paraphrased procedure may not demonstrate application.
5. **Shared systematic error:** include some *concordant* cases in human evaluation; agreement alone cannot exclude both models choosing inappropriate labels.

## Decision and next step

**GO to a small blinded human construct-validity audit, NO-GO for treating the 40 AI labels as validated ground truth or immediately scaling machine annotation to 180.**

Private deliverables given directly to the researcher, NOT stored here:
- full 40-case analytic comparison workbook (both model labels, evidence and 15 disagreements);
- **25-case blind expert review file**, selected as all 15 disagreements plus 10 concordance controls, randomized, with all labels/rationales empty;
- reviewer instructions and scientific report.

Human reviewers should label both axes independently, and interpretation must disclose if only one expert is available. This 25-case enriched adjudication sample is NOT representative of natural population frequencies. Then draft ND1 codebook v0.2 (preserving v0.1) and test fresh non-overlapping cases, including a purposefully enriched *potential revision* set and a separate random set. Do not infer RV from an automatic keyword selection heuristic.

**No human ratings or model performance on the new behavioral task exist as of this report.**

See: [ND1 v0.1 codebook](../docs/ND1_behavioral_moves_feedback_uptake_codebook_v0.1.md).
