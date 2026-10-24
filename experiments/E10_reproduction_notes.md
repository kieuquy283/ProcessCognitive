# E10 reproduction and data restrictions

E10 treats the **120 GPT-6 Astra labels as an assumed SILVER reference**, not human-validated truth.

A companion E10 code/output ZIP has been supplied to the researcher separately in the ChatGPT conversation. The scripts were executed with real labels (E10a), and E10b was run in a separate remote StudentBench environment on an available-case 605-session sample. The offline implementation was syntax-checked and passed a synthetic end-to-end smoke test; exact numerical reruns on full data may differ.

**Repository research report:** [E10 Astra mapping/prediction results](../reports/E10_Astra_silver_mapping_prediction_2026-10-24.md).

## Reproduce locally

Unzip `E10_Astra_silver_research_package.zip`. It contains:
- `e10_research/silver_mapping_benchmark.py`: four-class and S/N silver classifier benchmark with unseen-title and unseen-subskill group folds.
- `e10_research/e10a_robustness.py`: cluster bootstrap and alternative-annotator sensitivity.
- `e10_research/e10b_prepare_local.py`: reduce downloaded public StudentBench GRE Quant files to profiles, assessment responses and concept-level message COUNTS; no raw chat transcripts exported.
- `e10_research/e10b_astra_silver_from_csv.py`: convert your PRIVATE Astra CSV to minimal silver training labels.
- `e10_research/e10b_studentbench_predict.py`: E10b grouped item prediction with balanced weak-supervision alignment and shuffled concept negative control.
- `e10_research/e10b_observed_metrics.json`, `e10_research/e10a_silver_metrics.json`, `e10_research/e10a_robustness.json`: study aggregate outputs.

Use existing `requirements.txt` to install numpy, pandas, scipy, scikit-learn. **Do not commit the private Astra CSV or reduced session JSON.** Keep data in ignored `annotation_work/`.

Typical commands after you place the scripts from the ZIP under the repo's `experiments/` folder:

```bash
python experiments/silver_mapping_benchmark.py \
  --labels annotation_work/codex_astra/e9c_annotator_A.csv \
  --output results/e10a_silver_metrics.json

python experiments/e10b_prepare_local.py --data ./data \
  --out annotation_work/e10b_sessions.json.gz \
  --bank-out annotation_work/e10b_question_bank.csv

python experiments/e10b_astra_silver_from_csv.py \
  --astra annotation_work/codex_astra/e9c_annotator_A.csv \
  --out annotation_work/e10b_astra_silver.json

python experiments/e10b_studentbench_predict.py \
  --sessions annotation_work/e10b_sessions.json.gz \
  --bank annotation_work/e10b_question_bank.csv \
  --silver annotation_work/e10b_astra_silver.json \
  --output results/e10b_dev_metrics.json
```

**The 131-session holdout in the remote exploratory E10b was reserved, not used for model selection or scoring.** A fresh frozen official data revision is required before claiming exact repetition. Avoid opening holdout or changing the data-split seed to search for favorable numbers.

E10 cannot prove learning gains or psychological mastery. Real-data E10b uses no participant-identifying predictors but the reduced JSON includes session identifiers for splitting; keep it local.
