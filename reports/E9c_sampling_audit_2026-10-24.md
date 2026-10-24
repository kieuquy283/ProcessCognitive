# E9c — Human-annotation sampling audit and reproducibility

**Recorded:** 2026-10-24  
**Status:** Real-data candidate-sampling experiment completed. Independent human annotations **not yet obtained**. No inter-annotator agreement or mapping accuracy can be reported.

## Objective

E9 previously found that a nearest/soft-match between an AI-generated lesson-plan concept title and a GRE Quantitative `subskill` did not consistently outperform a content-shuffled negative control. E9c evaluates the **construct validity** of this mapping before building another skill-conditioned ML model.

## Real dataset extraction and sampling

Original public dataset: [StudentBench](https://huggingface.co/datasets/handshake-ai-research/studentbench). This extraction (sampling metadata only) retrieved **624/624 selected GRE Quantitative AI sessions** from **13 AI tutor arms**, selected as the first 48 per arm in a fixed shuffled directory order, seed embedded in `e9c_sample_pairs.py`.

All sampled session profiles, lesson-plan concept titles and event trajectories were used only in the private research execution environment. Session split (tutor × assessment form, seed 20261024) kept **489 development sessions** and **135 held-out sessions**. The annotation candidate pool was generated solely from development.

**Activity filter:** A concept was included only if at least one `student_message` in the trajectory referred to its `concept_id`. Only lesson-plan **titles**, not message bodies, entered the annotation sample.

### Source counts

| Quantity | Measured |
|---|---:|
| Selected sessions / sessions successfully retrieved | 624 / 624 |
| Development sessions | 489 |
| Holdout sessions not used in the candidate sample | 135 |
| Unique safe lesson concept titles in development | 1,999 |
| GRE quantitative subskills | 27 |
| Distinct candidate (subskill, concept title) pairings encountered in development | 53,973 |
| Candidate pairings with generic strategy indicator | 2,511 |
| (Session, GRE subskill) nearest-concept queries evaluated | 13,203 |
| Generic strategy title selected as closest concept | 879 |
| Fraction of nearest matches with generic strategy title | **6.66%** |

**Meaning of 53,973:** The pool is a cross-product of 27 subskills and the active tutoring concept titles observed in each development session, deduplicated. It is **not** a count of proven pedagogical relationships or paired human labels.

**Meaning of 6.66%:** The generic-title rate is based on a simple keyword detector and a frozen sentence encoder nearest match. It measures frequency of a **potential ambiguity**, not false-match frequency or true mapping error. Broad GRE strategies can be relevant to several items; a content-coverage codebook must separate generic strategy from direct mathematical overlap.

## Model and sample selection

- Frozen encoder: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions).
- Query template: `GRE Quantitative mathematics subskill: {subskill}`.
- Concept title template: `GRE mathematics concept: {concept name}`.
- Cosine similarity on normalized embeddings. No post-test scores, pre-test answer correctness, or grade outcomes enter sample selection.
- Similarity tercile cutpoints for non-generic candidates: **0.358769**, **0.440320**. These are ranking thresholds only, not probabilities that concepts match.
- Selected 120 *distinct* concept-title/subskill pairs with a reproducible random seed:
  - 30 non-generic low similarity,
  - 30 non-generic medium similarity,
  - 30 non-generic high similarity,
  - 30 generic strategy titles.
- All **27 GRE subskills** and **114 unique concept titles** are represented.
- Two sheets use identical randomized order and identical pair IDs; **all labels deliberately blank**. The analyst-only similarity sidecar is not sent to annotators.

### Blinding & governance

Public sample [`annotations/templates/e9c_pairs_blinded.csv`](../annotations/templates/e9c_pairs_blinded.csv) contains only pair ID, public GRE skill/subskill and selected lesson-plan concept title, with blank `label` and `rationale`. No raw participant-level transcripts, session identifiers, test results, embedding values or match scores are included.

The analyst-only sidecar with similarity and sampling stratum is created *locally* under ignored `annotation_work/`. It must be kept inaccessible to annotators until labels are locked.

## Execution

```bash
pip install -r requirements.txt -r requirements-research.txt

python experiments/e9c_sample_pairs.py \
  --data ./data \
  --out-dir ./annotation_work

# Two independent annotators each fill label (D/S/N/U) and rationale.
# No agreement is computed until the labels actually exist.
python experiments/e9c_agreement.py \
  --annotator-a ./annotation_work/e9c_annotator_A.csv \
  --annotator-b ./annotation_work/e9c_annotator_B.csv \
  --output ./annotation_work/e9c_agreement.json
```

The remote study used a temporary **metadata-only** cache and the same sampling code. Rerunning on a pinned full download may vary if the directory inventory changes. For byte-identical pair lists, use the committed blinded sample linked above.

### Code tests performed

- `e9c_sample_pairs.py` **compiled** and successfully generated 120 blinded rows from the real metadata extraction; 27 subskills and 114 distinct titles.
- `e9c_agreement.py` compiled; verified it **refuses to score blank labels**.
- For a technical test only, generated fictional independent 120-label files, verified it calculates confusion matrix, raw agreement, 4-class Cohen's kappa, strict/broad binary kappas, and identifies **24 planted disagreements**. The fictional outcomes are **not** StudentBench annotation results.
- Real annotation agreement is **pending**.

## Scientific decision rule

Class definitions from [the annotation protocol](../docs/E9c_annotation_protocol_v0.1.md): D = direct content coverage, S = general strategy, N = no relation, U = indeterminate.

Report both overall four-class agreement and explicit D-vs-not-D agreement, not just a single kappa. Inspect disagreement types and generic strategy false-direct classifications. Assess cosine rank's calibration *after* collecting independent blinded labels.

If the mapping lacks reliable human agreement, reject the current construct and revise the ontology or lesson-plan evidence source before developing a new representation. If agreement is reliable, train and evaluate **the same-data-budget** skill-conditioned method against correctly pooled and permuted evidence, with locked holdout only after development is complete.

**Limitations:** The selection is deliberately balanced across similarity strata and generic strategy pairs; it cannot estimate prevalence of incorrect matches among all tutoring interactions without sampling weights. Titles may be vague; the labels measure topical correspondence, **not correctness of a student's reasoning or mastery**. Two annotators have not yet completed this study.
