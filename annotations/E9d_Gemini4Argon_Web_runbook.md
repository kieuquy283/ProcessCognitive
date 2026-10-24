# E9d: Gemini 4 Argon on Gemini Web — blinded third-model audit

**Status:** Ready to run. Third-model annotations have NOT been executed from ChatGPT. This produces an independent MODEL judgment, not human expert adjudication.

## Input

Download the private preparation kit shared in the ChatGPT conversation:
- `E9d_Gemini4Argon_Blind_41.csv` — exactly 41 original blinded pairs, nine columns, all judgment fields blank.
- `E9d_Gemini4Argon_Web_Prompt.md` — complete self-contained rubric and strict output contract.
- `E9d_Gemini4Argon_Validate.py` — verifies final 41 CSV rows, original IDs/text/order, categorical values, and short rationales.
- Optional original `E9d_blinded_two_axis_review_41.xlsx` (41 pairs, same evidence).

The input CSV is derived from `Audit_41` in the original E9d blind workbook, with 21 Astra/Gemini Flash disagreements and 20 concordant controls. **No Astra/Gemini Flash labels, explanations, similarity scores, or test outcomes are included.**

## Gemini Web workflow

1. Open https://gemini.google.com and start a **new chat**; select **Gemini 4 Argon** if available under your Google AI plan.
2. Upload **only the blinded 41-pair CSV**; do not upload earlier two models' results or any label-agreement reports.
3. Paste the WHOLE `E9d_Gemini4Argon_Web_Prompt.md` as your request, without altering definitions or giving examples drawn from earlier model labels.
4. Gemini should classify every pair on TWO axes: exact mathematical content relation and presence of explicit generic strategy, plus one final D/S/N/U label and a 1–25-word rationale. All fields are defined in the master prompt.
5. Request a downloadable CSV named `E9d_Gemini4Argon_review_41.csv`; if downloads are unavailable, ask for the entire 42-line CSV text (header + 41 rows) and save it locally as UTF-8.
6. Run locally:
   python E9d_Gemini4Argon_Validate.py E9d_Gemini4Argon_Blind_41.csv E9d_Gemini4Argon_review_41.csv
7. Freeze the resulting third-model CSV before comparing with previous Astra and Gemini Flash labels. Report the third model as **MODEL-based blinded adjudication**, never human or ground truth.

## Methodological cautions

Three AI models can share biases; consensus is not ground truth and is not a substitute for a domain expert's independent review. The 41-pair audit intentionally oversamples disagreements; it is not a representative estimate of population-wide concept–skill match accuracy.

For the eventual cross-model comparison use the existing `experiments/e9d_analyze_expert_review.py` only if you correctly rename the expert terminology or write an AI-specific comparison; do not record Gemini Argon as a human expert.
