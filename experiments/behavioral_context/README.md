# StudentBench behavioral-context research (exploratory)

This workstream is independent of existing E7-E9c investigations in ProcessCognitive.
It studies context-aware student dialogue-act representation and the value of ordered behavioral traces for independent GRE posttest prediction.

**State on 2026-11-26:** E0 convenience audit performed on 8 public AI-tutored sessions; full-cohort audit not run; human behavior labels not available; no E2/E4/E5 empirical ML results.

## Files
- `e0_aggregate_audit.py`: reads a complete local official snapshot and writes aggregate QA only.
- `e1_context_pilot.py`: E1 sampler for 280 real unlabeled turns, with disjoint sessions and no scores.
- `tests/`: synthetic unit tests; not empirical study findings.
- `manifests/`: upstream revision marker and explicitly unapproved candidate labels.
- `docs/E1_PROTOCOL.md`: instructions and human-label gating.
- `../../reports/behavioral_context_E0_2026-11-26.md`: aggregate source-backed observations.

## Data policy
Do not commit raw student utterances, transcripts, `student.json`, per-session scores, completed annotator sheets, or model API responses containing student text.
Keep official downloaded data under ignored `data/`, and E1 sheets under ignored `annotation_work/`. Only source, synthetic tests, codebook drafts, and aggregate reports are committed.

## How to run (when a complete pinned local snapshot is available)
```bash
pip install -r experiments/behavioral_context/requirements-pilot.txt
python experiments/behavioral_context/e0_aggregate_audit.py --data ./data --out ./annotation_work/e0_summary.json
python experiments/behavioral_context/e1_context_pilot.py --sessions ./annotation_work/session_audit.csv --turns ./annotation_work/annotation_input_no_scores.csv --out ./annotation_work/e1
pytest -q experiments/behavioral_context/tests
```

**Important:** The E1 sampler requires turn-level E0 inputs. The aggregate-only E0 script intentionally does not emit participant rows; use the separate, consent-compliant local E0 pipeline supplied with the research pilot bundle to generate such inputs.

Official source: https://github.com/Handshake-AI-Research/studentbench. The pinned revision is documented, but the 8 remote micro-audit sessions were fetched from `main` and have not been hash-checked against that revision.

## 2026-11-26 methodological continuation

E1 has an increased session independence gate (40 input sessions per GRE section; <=5 sampled turns per session). The 24-session convenience E0 extension is insufficient for the *revised* gold annotation pilot despite having >280 utterances. See `reports/behavioral_context_E8R_E1_2026-11-26.md` for the E8 non-nested-model critique and controlled baseline requirements.
