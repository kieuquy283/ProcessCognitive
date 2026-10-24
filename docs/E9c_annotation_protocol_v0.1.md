# E9c — Protocol for validating concept–subskill alignment (v0.1)

**Purpose:** Audit whether automated semantic matching genuinely links a tutoring lesson concept to the GRE subskill being assessed. This is a construct-validity study, **not** a student knowledge-state annotation.

## Annotation unit

One pair `GRE quantitative subskill label ↔ AI-generated tutoring concept title`. Annotators must ignore the student's assessment score, the AI tutor name, the student's identity and all automated model outputs.

**Four mutually exclusive labels:**

| Label | Definition | Typical interpretation |
|---|---|---|
| D — Direct coverage | The concept clearly teaches/tests the mathematical principle necessary for this subskill (may use different wording). | “Exponent Rules” ↔ “Simplifying powers and exponents” |
| S — General strategy | Broad problem-solving or exam technique could be applied, but does not by itself teach the mathematical content of the subskill. | “QC Strategy: Testing Edge Cases” ↔ “Exponent rules” |
| N — No meaningful link | Concept does not teach or materially support the subskill. | “Probability with combinations” ↔ “Triangle area” |
| U — Undetermined | Title too vague, truncated, ambiguous or outside the annotator's knowledge to establish relevance. | “Special cases” ↔ a precise algebraic subskill |

**Critical precedence:** D only if a mathematical content match is defendable from the titles. If a strategy may help solve any GRE quantitative question but not teach a subskill, use **S**, not D. Do not infer mastery, explanation correctness or actual causal learning from a topical match. If in doubt between S and D from titles alone, use U and flag for evidence review.

## Sampling and blinding

1. Sample from development sessions only. Use all distinct eligible concept–subskill candidates, but stratify by **cosine similarity tercile** (low, medium, high). Include a separate prespecified group of general-strategy concept titles (e.g. “QC Strategy”) if present. Avoid exposing post-test correctness or confidence to annotators.
2. Target **120 unique pairs** initially: 30 low, 30 medium, 30 high, 30 generic-strategy, while de-duplicating repeated titles/pairs. If strata are short, redistribute and document exact counts rather than invent examples.
3. Two annotators independently review shuffled pair IDs. Hide automated similarity scores, model predictions and each other's labels.
4. Record disagreements and adjudicate using the codebook, preserving raw labels. For U, optionally inspect an anonymized lesson-plan description; do not reveal student post-test results.
5. Measure raw agreement, class-level confusion, Cohen's kappa (nominal four classes) and optionally Krippendorff's alpha. A single point estimate without uncertainty is not a validity guarantee.

## Evaluation

- Treat **D versus S/N/U** as a strict content-coverage validity target; separately examine **D or S versus N** as a broad pedagogical relevance target.
- Plot/calibrate cosine similarity against these annotated targets, including precision among high-similarity matches, false-direct rate, and skill-specific variation.
- Compare a human-validated pairing rule against random/nearest-concept and broad-strategy baselines on development only.
- If agreement is low, **do not proceed with a skill-conditioned learner model** based on these annotations. Revise the ontology or change the research question.
- Do not let post-test correctness labels influence which concept–skill mappings are judged correct: that would cause outcome leakage.

## Data handling

Only share de-identified *concept titles* and GRE subskill labels for annotation. Do not upload student messages, raw transcripts, personal data or study records to GitHub. Keep annotator forms under ignored local directories, and publish only aggregate validity metrics and code.

## Decision gate

Proceed to a skill-conditioned predictive model only if:
- relevant pairs can be annotated consistently by independent reviewers;
- the mapping demonstrably distinguishes direct mathematical coverage from generic strategy matching; and
- a model using the **validated** mapping outperforms the same-information pooled and permuted-mapping controls during development.

This protocol is proposed and **not yet performed**; no human agreement statistics have been obtained.
