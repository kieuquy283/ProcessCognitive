# ND1 — Student Behavioral Moves and Feedback Uptake Codebook v0.1 (FROZEN FOR PILOT)

**Status:** Proposed measurement instrument — not a validated student-cognition ontology. StudentBench GRE Quant tutoring. Source: real typed `student_message` plus **earlier** tutor context and optional earlier student turn. Never use later tutor replies, later practice correctness, pre/post-test scores, similarity scores or other annotator labels to decide the dialogue labels.

## 1. Scientific construct and sampling unit

**Unit:** one eligible student message anchored to its immediately preceding relevant tutor message (within nine logged events, normally same `practice_problem_id`). Prior student message is for context only. Real traces may interleave practice problems; record insufficient context rather than guessing. Label ONLY observable discourse, not internal cognition, latent mastery, dependency diagnosis or causal effect.

Two orthogonal outputs:
- **`primary_act`:** What observable conversational move dominates THIS student message? Seven mutually exclusive codes.
- **`feedback_uptake`:** Does THIS student message engage with the tutor's **immediately preceding** actionable feedback/instruction? Six mutually exclusive codes. Directly copying an answer from tutor is not the same as an independent, reasoned revision.

## 2. Primary student move (`primary_act`)

| Code | Definition | Positive evidence / exclusions |
|---|---|---|
| **RE** | Student explicitly states, revises, or justifies a mathematical step or reasoning | Formula with interpretation, comparison of quantities, causal “because…”, step-by-step explanation. An isolated number does NOT qualify |
| **VE** | Verifies or monitors an existing answer/procedure, expresses doubt or checks correctness | “Is my step right?”, “I got X, but am I missing...?” when **no meaningful reasoning** is supplied |
| **CQ** | Requests conceptual clarification or explanation | “Why is that the denominator?”, asks about a principle; not a pure answer request |
| **HR** | Seeks procedural/direct answer assistance | “What do I do next?”, “Tell me the answer”, “Can you solve it?” without conceptual why |
| **AN** | States a short answer or intermediate result without explanation | “70.6”, “x = 4”, a bare value even when correct |
| **AK** | Acknowledges, accepts/declines, or manages the session | “ok”, “thanks”, “next”, “yes”; no substantive math |
| **OT** | Other/unclear topic, unreadable message, mixed or insufficient evidence | Do not hallucinate a student's intention |

**Precedence in truly mixed turns:** substantive RE > VE > CQ > HR > AN > AK > OT. Apply precedence only when BOTH behaviors are independently explicit. If text is too fragmentary, prefer OT. **Question marks alone do not imply CQ/VE**, and technical tokens alone do not establish RE.

## 3. Feedback engagement / uptake (`feedback_uptake`)

Tutor instruction may be hinting, diagnostic feedback, a worked example, procedural guidance or a verification request. An ungrounded “Good job!” or greeting without usable content generally does not constitute actionable feedback.

| Code | Definition | Disambiguation |
|---|---|---|
| **NO** | No identifiable actionable tutor feedback or instruction in shown preceding tutor context | Cannot measure uptake; not learner disengagement |
| **NR** | Actionable context exists, but student turn is unrelated, declines to engage, or switches topic | Silence is not measured here; no inference from missing turns |
| **AC** | Student acknowledges, expresses confusion or asks a follow-up about the prior instruction, without demonstrating application | “Ok”, “why?”, “still confused” |
| **AP** | Student applies/echoes prior guidance in a new answer or step, but gives insufficient independent reasoning to establish a justified revision | Giving the requested value; repeating a tutor-supplied numerical answer |
| **RV** | Student explicitly updates a previous mathematical approach and **articulates** why/how the change follows prior guidance | Requires a reasoning span and attributable change or contrast, not merely a correct answer |
| **UN** | Cannot determine relation to tutor feedback because visible context is incomplete, ambiguous or interleaved | Short “yes” after incomplete tutor message may be AC or UN; note rationale |

**Important boundaries:**
1. `RE` on the primary axis does NOT automatically mean `RV`. A student may reason without responding to tutor feedback.
2. `AN` + `AP` is possible and common, if the student supplies the requested answer after a tutorial prompt.
3. A wrong answer may still contain genuine reasoning; correctness is NOT part of the label definition.
4. A corrected practice submission **after** the student turn is a separate observed outcome and MUST NOT be shown to the annotators.
5. `RV` is a high-evidence category. If no visible prior student claim/step is available, require explicit self-correction in the current turn (“I was wrong because...”) or use `AP`.

## 4. Original examples for boundary testing (NOT copied from StudentBench)

- Tutor: “Why divide by the total cost?” Student: “Because percent of total uses total as denominator, so my previous denominator was wrong.” → **RE / RV**.
- Tutor: “The ratio is 120/170; compute it.” Student: “70.6” → **AN / AP**, not RV.
- Tutor: “Try substituting numbers into the equation.” Student: “Why are we allowed to choose arbitrary values?” → **CQ / AC**.
- Tutor: “Correct.” Student: “Next.” → **AK / NO** (no actionable instruction).
- Tutor: “Check both signs.” Student: “What’s the final answer?” → **HR / NR** if ignores feedback, or **HR / AC** if explicitly asks how to perform requested check. Adjudicate from exact text.
- Tutor: “Now solve for x.” Student: “I think x = 7 because 2x = 14.” → **RE / AP**, unless a prior visible wrong solution is clearly corrected.

## 5. Annotation protocol

1. Show exactly: `episode_id`, `previous_student_excerpt`, `tutor_context`, `student_turn`.
2. First assign `primary_act`, then `feedback_uptake`; provide 8–35-word `annotation_rationale` quoting specific evidence. Confidence = **low / medium / high** (subjective reviewer certainty, NOT a calibrated probability).
3. Two human reviewers independently label the same **40-pair feasibility pilot**; reviewer B must never see reviewer A's responses. If only model reviewers are available, report results as **model–model reliability** rather than human-human IAA.
4. Compute nominal Cohen κ plus agreement **separately for both axes**, per-class confusion, prevalence. For rare `RV`, report recall/positive agreement and counts instead of relying on a large aggregate κ.
5. Resolve disagreements; document decision in codebook v0.2 but **do not overwrite original v0.1 ratings**. A fresh 150–200 case batch must test any revised rules.
6. The sampling pool is lexically **stratified** for feasibility; class proportions from all 180 are NOT representative of StudentBench. The full 180 pilot contains intentionally selected reasoning, feedback follow-up, short answers and unrestricted text.

## 6. Predictive evaluation after label validity

Only after two-rater agreement/construct validity:
- **Task A:** student-turn `primary_act` classification. Baselines: majority, student-text TF-IDF Logistic Regression, contextual (preceding tutor+student) TF-IDF; eventually sentence embedding/LLM with honest validation. **Grouped by session/task**.
- **Task B:** conditional `feedback_uptake` prediction with tutor-context versus no-tutor-context and context-shuffled negatives, reported only on cases where feedback is observable (`NO` excluded from uptake-eligible subset; report exclusion counts).
- **Task C:** external behavioral criterion `next-practice answer correction`, computed on strictly subsequent practice events, with baseline prior practice answer correctness/difficulty and tutor arm. This is **behavioral action**, not proof of retained learning; posttest is exploratory external validity, not necessary for the model to "succeed".
- No ground-truth correctness is invented using a model consensus or keywords; original educational interpretations require explicit human validation.

## 7. Privacy and release

StudentBench conversation text may contain volunteered personal details even in a de-identified release. All episode CSVs, rationale, and sidecars remain under gitignored `annotation_work/`. Remove PII manually before sending to external annotators. GitHub may contain **only extraction code, codebook and aggregated nonidentifying statistics**, not dialogue snippets, session identifiers, or model-generated adjudications treated as human truth.

### Related research (inspiration, not exact codebook replication)

- StudentBench: Northcutt et al. (2026), https://arxiv.org/abs/2609.28470
- StudyChat: McNichols et al. (2026), https://arxiv.org/abs/2503.07928
- MathDial: Macina et al. (2023), https://aclanthology.org/2023.findings-emnlp.372/
- TutorBench: Srinivasa et al. (2025), https://arxiv.org/abs/2510.02663

**Scientific caveat:** It is NOT yet established that this codebook is novel, reliable or useful. The pilot is designed to falsify that conjecture.
