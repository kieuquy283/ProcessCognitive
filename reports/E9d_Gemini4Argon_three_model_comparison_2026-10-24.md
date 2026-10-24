# E9d — Gemini 4 Argon third-model annotation comparison (2026-10-24)

## Inputs and validation

A 41-row `Pasted text.txt` was supplied by the researcher as the **Gemini 4 Argon** result and compared, pair by pair, with the two original 120-row E9c annotator CSVs (GPT-6 Astra / Gemini Flash) and the blank blinded E9d 41-row template.

- All **41 IDs** exist in both original E9c files and the blinded 41-row source.
- GRE skill, subskill and concept titles match exactly.
- All D/S/N/U labels, two diagnostic axes and rationales are present. Rationales are between 14 and 20 words.
- Model names are researcher-declared; CSVs alone do **not authenticate runtime model identity or actual conversational isolation**.

## Results on 41 deliberately selected pairs

| Relationship | Exact agreement | Cohen's κ |
|---|---:|---:|
| Astra vs Gemini Argon | **40/41 = 97.56%** | **0.9604** |
| Gemini Flash vs Gemini Argon | **19/41 = 46.34%** | **0.2720** |
| Astra vs Gemini Flash | 20/41 = 48.78% | 0.3062 |
| All three agree | **19/41 = 46.34%** | n/a |

**Do not compare the 41-case κ to the original 120-case E9c κ = 0.631 as if computed on the same sample.** The 41-case sample deliberately contains all 21 disagreements plus only 20 originally concordant controls. Its model agreement percentages are not representative of the full 120 pairs, much less the StudentBench population.

### All 21 original disagreements resolved identically to Astra

| Astra / Gemini Flash | Cases | Gemini Argon |
|---|---:|---|
| S / N | 18 | **S on 18/18**, matching Astra |
| U / D | 2 | **U on 2/2**, matching Astra |
| U / N | 1 | **U on 1/1**, matching Astra |

Gemini Argon agreed with Astra on **21/21 discordant cases**, Gemini Flash on **0/21**. This is an **AI–AI agreement result**, **not accuracy** and **not proof Astra is correct**.

### Original concordant controls (n=20)

Argon agreed with both original models on **19/20** cases. One substantive exception:

- `E9C-E3CF5C2E6CC2`
- GRE subskill: *an identity vs a varying expression*
- Tutoring concept: *Algebraic Expressions, Factoring & QC Comparison Methods*
- Astra = **S**; Gemini Flash = **S**; Gemini Argon = **D**.
- Argon's two axes: `Specific match` + `Explicit general strategy`. This makes D internally coherent under the stated precedence rule, but a human GRE domain reviewer should determine whether the mathematics in the title **directly covers** the target subskill.

## Diagnostic axes and construct validity

Argon's 41 labels: **D=6, S=22, N=10, U=3**.

Math-content axis: **Specific match=6; Different topic=29; Unclear or partial=6**.

Explicit general-strategy axis: **Yes=23; No=18**.

No immediate conflicts were found between Argon's two axes and its final label under the high-level codebook. **However, these three judgments were produced by one model, so they are not independent verification.** A title containing a generic strategy is not necessarily a concept–subskill *content match*, nor evidence the student learned it.

## Inference and next decision gate

What the dataset supports: Astra and Argon classify this enriched 41-case audit extremely similarly, especially regarding the **S vs N** boundary. Model agreement cannot establish mapping validity.

What it does **not** support: any claim of ground truth, human inter-rater reliability, semantic mapping accuracy in the dataset, learner mastery or uplift in independent posttest prediction.

**Recommended next study:**
1. Obtain blinded ratings from a GRE-mathematics domain reviewer for the 21 disagreements, the single concordant-control exception and prespecified fresh control cases; prefer two independent human reviewers if possible.
2. Distinguish **direct mathematical content match** (D vs non-D) from **presence of broadly applicable strategy**, which may be conceptually orthogonal to content correspondence.
3. Keep the 120 original E9c labels and frozen protocol intact. After validated mappings are available, reevaluate E9's pretest+practice baseline vs matching evidence and shuffled-mapping negative control on development; only use holdout after locking model choice.

**Privacy:** Full per-item rationales and three-way joined CSV/XLSX are held locally in the user's ChatGPT environment and have not been committed to this public repository.

## Links

- [Shared E9c rubric](../annotations/E9c_COMMON_TASK_CODEX_ANTIGRAVITY.md)
- [E9d two-axis protocol](../docs/E9d_two_axis_expert_review_protocol_v0.1.md)
- [Earlier E9d disagreement sensitivity report](E9d_construct_validity_sensitivity_2026-10-24.md)
