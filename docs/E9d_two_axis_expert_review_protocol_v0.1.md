# E9d — Two-axis blinded adjudication protocol (supplement; v0.1)

**Purpose:** Determine why Codex/Astra and Antigravity/Gemini disagree about whether a lesson concept matches a GRE quantitative subskill, while preserving the comparability of the ORIGINAL four-label codebook.

## Original output is frozen

The 120 original model labels must remain unmodified. Their agreement (99/120; nominal κ≈0.631) was calculated under the common E9c D/S/N/U rubric, which remains the governing rule for **E9d final label**. The extra axes below are *diagnostic*, not a new hidden gold standard or retrospective recoding.

## Reviewer input

The reviewer receives only the GRE skill/subskill, AI-generated lesson-concept title, and empty judgment fields for **41 pairs** (21 model disagreements + 20 concordant controls, order randomized). The reviewer does NOT see model labels/rationales, disagreements vs controls, cosine scores or StudentBench outcome labels.

[Human-review XLSX artifact](https://github.com/kieuquy283/ProcessCognitive/blob/research/studentbench-diagnostics/annotations/README.md) is provided separately as an offline workbook: `E9d_blinded_two_axis_review_41.xlsx`. It MUST NOT be uploaded to public GitHub after being filled without disclosure review.

## Diagnostic axis 1: Mathematical content relation

- `Specific match`: the title identifies the actual mathematics needed for the GRE subskill (e.g. exponent rules vs simplifying powers).
- `Different topic`: specific math topic named in the concept differs from the target skill (e.g. circle area vs factorial trailing zeros).
- `Unclear or partial`: title too general/partially specified to confirm direct coverage.

## Diagnostic axis 2: Presence of an explicit broad strategy

- `Explicit general strategy`: title expressly identifies a broadly transferable GRE/quantitative technique (e.g. QC case testing, estimating, systematic elimination).
- `No explicit strategy`: no such strategy in title.
- `Unclear`: a possible strategy is suggested but not identifiable.

This axis measures **presence in the title**, not whether the technique would help a particular assessment item. The title might contain both an unrelated mathematical topic AND a general strategy.

## Original four-label primary rating (maintain original E9c standard)

- **D** if specific mathematical content is clearly covered.
- **S** if an identifiable general transferable GRE strategy is present without direct content match. Give a rationale about potential transfer, but do not assert it improves score.
- **N** if content is materially different and no meaningful transferable general strategy is identifiable.
- **U** if titles are too vague for a grounded decision.

If your primary label conflicts with a diagnostic axis, retain your honest judgment and explain why in `Optional ambiguity note`. The axes are NOT formulaically mapped to the four labels.

## Audit rules

1. Have a reviewer knowledgeable in GRE Quantitative independently complete all 41 rows. Prefer two independent humans when feasible; if only one expert reviews, report **expert review**, NOT human-human inter-rater reliability.
2. Reviewer fills the original D/S/N/U label, English rationale (1–25 words), plus both diagnostic axes; no model outputs are shown until the reviewer seals the file.
3. After sealing, compare the reviewed file against model A and B only in a **separate analyst environment** with `experiments/e9d_analyze_expert_review.py`. Do not change any original labels.
4. Analyze separately the 21 conflict cases and the 20 randomly selected concordant controls. Never call the 41-case unweighted concordance a population accuracy estimate.
5. When documenting corrections to the ontology, create a *new version* for future relabeling, not retrospective modifications of the original E9c evaluation.

## Decision criteria

- If the disagreement is caused mainly by an ill-defined S/N concept boundary, revise the rubric and replicate on fresh independently assigned pairs before using concept–skill alignments as features.
- If expert review confirms content mismatch frequently despite model-model agreement, the semantic matching pipeline lacks construct validity.
- If mappings become reliable under an independently evaluated codebook, resume incremental predictive testing against E9's strong pretest+practice baseline and deliberately shuffled alignments.
- **No predictive performance, learning gain, or causality conclusion follows solely from κ or model agreement.**

## External context (not part of annotator input)

The rationale for expert anchoring is consistent with current LLM evaluation evidence that machine-machine agreement can diverge from human alignment (Mukherjee et al., June 2026, https://www.microsoft.com/en-us/research/publication/the-geometry-of-llm-as-judge-why-inter-llm-consensus-is-not-human-alignment/), while findings on LLM annotations have been task-dependent (Kasner et al., 2026, https://aclanthology.org/2026.mme-main.1/). Do not give those findings to blinded reviewers as priming context.
