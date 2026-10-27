# ND2 progress: whole-frame discovery and clustering audit (2026-10-28)

**Research status:** real data-source audit only; ND2 Astra–Claude labeling remains **PENDING**. No performance estimates from ND2 have been measured.

Source: official StudentBench revision `304c8d63c726e72b60510bba3a44454fc0726721`. The Hugging Face REST tree API was queried for the AI tutor directory listing in all 13 GRE Quant and 13 GRE Verbal AI arms. **1,139 Quant + 1,000 Verbal = 2,139 session directories** were listed. Directory existence does not imply that each has an eligible nonblank student message.

Authentic real-data exploratory audit of 24 convenience-sampled sessions, limited to 3 tutor arms, found 3,492 events, 464 student messages, 720 practice-answer submissions; in 296/464 student turns (63.79%), assembled tutor context since the prior student message exceeded 950 characters: 147/282 (52.13%) Quant and 149/182 (81.87%) Verbal. This is context-length exposure, not evidence of label error.

A stratified, **session-resampled**, 10,000-iteration descriptive bootstrap on the same 24-session purposive subset gave intervals: Quant 41.04–68.52%, Verbal 78.28–87.88%, combined 54.98–74.70%. These intervals **do not account for selection bias** and must not be represented as population CIs.

A further trace-order audit of 6 of the 24 real sessions found 45/113 student chat turns following at least one practice-answer submission since the preceding student chat turn. This does **not** demonstrate feedback uptake or learner improvement.

## Interpretation
1. Short-cutting to 950 characters is a material input transformation. A prespecified paired full-context vs truncated-context ablation is warranted, with models and prompts fixed.
2. Chat-only feedback uptake does not automatically account for adjacent practice attempts. External construct validation is necessary.
3. One student turn per session yields session-weighted rather than turn-weighted accuracy.
4. Do not conflate directory counts with eligible session sample size, and do not conflate 24-session exploratory data auditing with 280-episode ND2 model evaluation.
5. ND1 session mappings and verified reference-model provenance are still required to certify independence. Astra remains a *conventional reference*, not human-established ground truth.

## Implementation tested locally
The local ND2 pipeline was strengthened to report Wilson 95% intervals and domain breakdowns, plus reject invalid schemas and preserve the ND1 leakage warning. Existing synthetic smoke tests and new synthetic validation-guard tests passed. **Those updated local scripts are not included in this GitHub commit**; source review and a separate script commit are still needed.

## Decision
Source-frame discovery: PASS.
Authentic limited data audit: PASS.
ND2 independent annotation and scientific performance evaluation: **PENDING**.

No participant-level rows, transcripts or raw model outputs have been committed.