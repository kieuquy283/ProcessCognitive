# StudentBench E0 extended audit and E1 research decision

**Date:** 2026-11-26. **Status:** exploratory source-backed check, not a full dataset reproduction.

## What was actually inspected
Eight real public AI-tutored GRE sessions (four Quant and four Verbal), from four AI configurations: GPT-5.4-mini, Gemini-3.7-Flash, Opus-5 and Gemma-4-31B. Eight profiles, 16 item-level assessment files and eight raw event trajectories were checked.

| Source QA metric | Observed |
|---|---:|
| Sessions checked | 8 |
| Quant / Verbal | 4 / 4 |
| Score sums match profile pretest/posttest on 27-item assessments | 8 / 8 |
| Nonblank student/tutor event counts match profile | 8 / 8 |
| Consecutive unique `trajectory_position` | 8 / 8 |
| Total student-authored messages | 228 |
| Total raw application events | 1,609 |
| Adjacent local timestamp reversals | 194 |
| Sessions with at least one reversal | 5 / 8 |
| Student messages of at most seven whitespace-separated words | 121 / 228 |

Source-backed methodological decisions: use `trajectory_position` to preserve recorded event ordering; treat timestamp reversals as a QA variable, not a reason to silently rearrange source events. Short or underspecified utterances motivate a *context ablation* hypothesis; they do not establish model gains.

## System event permutation negative control
In the original four-session slice, 500 within-session permutations of raw **system event types** produced 219 observed `practice_answer_submitted -> ai_tutor_message` edges versus 80.08 mean in the shuffled null (ratio 2.73). This measures platform/workflow regularity; it does NOT validate student behavior ontology, cognitive state, or learning gains. Unadjusted permutation p-values are not to be interpreted as educational evidence.

## Next experiment: E1 context pilot
A fixed 280-turn pilot (200 development, 80 held-out) is proposed; 140 Quant / 140 Verbal, independent sessions, outcome-blinded. The eight audited sessions contain **only 228 student messages**, so E1 is **blocked** in this slice. No 280-row CSV has been created or claimed. The sampler and unit tests are preparatory, not human annotation results.

## Research state / limitations
- Full official 2,139-session AI snapshot E0 audit: **NOT RUN** in this execution environment.
- Source pin recorded from upstream: HF `304c8d63c726e72b60510bba3a44454fc0726721`; the eight examined session files were read via `main`, not byte-for-byte verified against the pin.
- Independent human codebook annotation: **NOT RUN**. No Cohen kappa, model Macro-F1, or outcome MAE may be claimed.
- Even after E1 annotation, behavioral sequence E4 requires **complete contiguous sessions**, not sparse pilot turns.
- Existing E7-E9c research remains untouched. No inference here about behavioral causality or tutoring-policy effects.

## Sources
- https://huggingface.co/datasets/handshake-ai-research/studentbench
- https://github.com/Handshake-AI-Research/studentbench
- https://arxiv.org/abs/2503.07928
- https://doi.org/10.1145/3772318.3790459
