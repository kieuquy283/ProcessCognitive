# StudentBench diagnostic experiments

Scripts in this folder are **exploratory research implementations**. They are not a finalized paper benchmark.

1. Download the original public dataset with the [official StudentBench instructions](https://github.com/Handshake-AI-Research/studentbench).
2. Install dependencies: `pip install -r requirements.txt`.
3. Run `python experiments/studentbench_diagnostic.py --data ./data --output ./results`.
4. Run `python experiments/studentbench_text_diagnostic.py --data ./data --output ./results_text`.

**Methodological warnings:** the pilot numbers in `reports/` were collected during exploratory development and may not be exactly reproducible after using a different full dataset snapshot or deterministic split. A final comparison requires a frozen data revision, session-level held-out evaluation, stronger item-level pretest baselines, semantic encoders and sequence controls. No improvement in predictive loss is evidence of a causal effect on learning.
