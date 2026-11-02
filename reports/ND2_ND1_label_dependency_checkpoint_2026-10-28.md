# ND2 scientific checkpoint: ND1 label dependency (2026-10-28)

**Genuine research data:** two aligned, privately stored 40-episode ND1 CSVs (Astra reference and Claude annotations). This is an **ND1 reanalysis**, not an actual 280-episode ND2 accuracy experiment. No participant-level rows or dialogue were committed.

## Empirical results

| Metric (Claude vs Astra) | Primary act | Feedback uptake |
|---|---:|---:|
| Accuracy | 32/40 = 0.800 | 38/40 = 0.950 |
| Macro-F1 on Astra-observed classes | 0.754 (7/7) | 0.860 (4/5) |
| Macro-F1 on all fixed classes, assigning F1=0 for absent classes | 0.754 | **0.688** |
| In-sample majority-prevalence diagnostic | 0.250 (AN) | 0.475 (AP) |

Astra `feedback_uptake` support: AC=18, AP=19, NO=0, NR=1, UN=2. **Zero-support NO is not evidence that Claude failed to classify NO examples**; the fixed-5-class score is reported *only* as a denominator/coverage sensitivity, not the preferred performance estimate. Majority labels are selected from the test sample itself and do not constitute an independent predictive benchmark.

### Are the two label dimensions redundant?
- Astra `primary_act` ↔ `feedback_uptake` mutual information **0.6455 nats**. Permutation-label test using 10,000 shuffles, seed 20261028: empirical **p≈0.0001**, exploratory.
- **Oracle-primary-act conditional baseline:** train a lookup from 39 Astra primary+uptake label pairs and, on the held-out episode, use its *Astra primary* label to predict uptake. Leave-one-out accuracy: **34/40 = 85%**.
- Claude's uptake labels: **38/40 = 95%** versus oracle-primary conditional diagnostic **34/40 = 85%**, exact paired McNemar p=**0.289** (unadjusted). A more operational leave-one-out baseline instead feeds **Claude-predicted primary act** to the 39-case Astra-trained mapping: **31/40 = 77.5%** uptake accuracy; Claude direct uptake remains 38/40, paired McNemar **p=0.015625** unadjusted. All contrasts remain developmental and exploratory.
- Paired correctness: both dimensions correct 32, primary only 0, uptake only 6, both wrong 2; Fisher's exact p≈**0.0359** (exploratory, only 2 uptake errors).

**Interpretation:** `feedback_uptake` is **strongly associated with** `primary_act` within this pilot. This may result from the definitions of the codebook, selected episode composition, shared annotator conventions, or a meaningful behavioral relationship. **Association does not establish that the second dimension is redundant or that it measures actual practice behavior.** The diagnostic lookup had oracle access to the correct primary label and is not a deployable text classifier.

## Scientific implications for preregistering ND2
1. Keep the ontology frozen during ND2. Explicitly examine *incremental information* of uptake beyond primary act.
2. Report all five uptake support counts, and both observed-class and fixed-class Macro-F1 variants with correct caveats.
3. Report performance separately for 200 session-sampled random episodes and 80 challenge episodes. Session provenance, frozen prompt/codebook and independently verified model IDs remain mandatory.
4. The uptake-vs-primary diagnostic should include **both an oracle baseline and an operational non-oracle baseline** so it cannot exaggerate usefulness.
5. Evaluate event-aware uptake using actual tutor/chat/practice sequences and blinded human review before making construct-validity claims.

## Reproduce

```bash
python -m pip install pandas numpy scipy scikit-learn
python experiments/nd1_label_dependency_audit.py \
  --astra annotation_work/ND1_Astra_A_40.csv \
  --claude annotation_work/ND1_ClaudeOpus55_B_40.csv
```

These 40 samples are a developmental pilot: the p-values are exploratory, not confirmatory, and should not be extrapolated to the full StudentBench population. **ND2 formal performance remains PENDING.**
