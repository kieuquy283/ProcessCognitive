# ND1 — Quy trình bắt đầu hướng mới (student behavioral moves & feedback uptake)

**Tình trạng:** extraction thực trên StudentBench đã PASS; 180 episode chưa có nhãn. Các kết quả của hướng ND1 chưa phải kết quả model.

## Source and privacy

Đọc [codebook v0.1](../docs/ND1_behavioral_moves_feedback_uptake_codebook_v0.1.md) và [báo cáo tái thiết kế](../reports/ProcessCognitive_E7-E14_review_ND1_research_redesign_2026-10-25.md) trước khi gán nhãn.

Dataset là StudentBench GRE Quant, revision `304c8d63c726e72b60510bba3a44454fc0726721`; script lấy 6 phiên/tutor arm, tổng 78 phiên, tối đa 4 student-turn episode/phiên và 180 episode không trùng ID.

Tạo **private local** CSV bằng cách chạy từ repository root:

```bash
python experiments/nd1_extract_feedback_episodes.py \
  --out annotation_work/new_direction/nd1_pilot_180_PRIVATE.csv \
  --n 180 --per-arm 6 --workers 14
```

Expected output fields:
`episode_id,previous_student_excerpt,tutor_context,student_turn,primary_act,feedback_uptake,annotation_rationale,confidence`.
Tất cả ô nhãn **để trống**. Script tạo thêm `_B.csv` cho người gán nhãn độc lập, `pilot_sampling_sidecar_PRIVATE.csv`, và `pilot_sampling_aggregate.json`. Các files private chỉ nên tồn tại dưới `annotation_work/` (đã gitignore).

Do NOT commit dialogues, sidecar or hand-annotated files. Review PII manually. Current masking addresses email/URL but is **not an exhaustive anonymizer**. Some tutor messages are truncated at 950 chars, student at 700 chars; human reviewer may mark `UN` where context insufficient.

## Pilot annotation

1. Freeze codebook v0.1; have independent human annotators examine **the same 40 episodes** (e.g. 40 first rows chosen by frozen pseudorandom shuffle) and mark each axis. Do NOT expose sampling sidecar or later practice/posttest correctness.
2. Annotator A writes `annotation_work/new_direction/pilot_A_reviewed.csv`; annotator B writes `pilot_B_reviewed.csv`. Use exact source columns/order and fill only the last 4 columns. `annotation_rationale` 8–35 English or Vietnamese words; `confidence` low/medium/high.
3. For 40-case trial, first create a **matched 40-row blank source**, e.g.:

```python
import csv
from pathlib import Path
p=Path("annotation_work/new_direction/nd1_pilot_180_PRIVATE.csv")
with p.open(encoding="utf-8", newline="") as f:r=list(csv.DictReader(f))
out=p.with_name("nd1_pilot_40_BLIND_PRIVATE.csv")
with out.open("w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(r[0]));w.writeheader();w.writerows(r[:40])
```

4. Validate each independently:

```bash
python experiments/nd1_validate_annotations.py --source annotation_work/new_direction/nd1_pilot_40_BLIND_PRIVATE.csv --file annotation_work/new_direction/pilot_A_reviewed.csv --n 40
python experiments/nd1_validate_annotations.py --source annotation_work/new_direction/nd1_pilot_40_BLIND_PRIVATE.csv --file annotation_work/new_direction/pilot_B_reviewed.csv --n 40
```

5. In a third analyst workspace (after both finished):

```bash
python experiments/nd1_agreement.py \
  --source annotation_work/new_direction/nd1_pilot_40_BLIND_PRIVATE.csv \
  --a annotation_work/new_direction/pilot_A_reviewed.csv \
  --b annotation_work/new_direction/pilot_B_reviewed.csv \
  --n 40 --out annotation_work/new_direction/nd1_pilot_agreement.json
```

Interpret accuracy/κ on 40 as **reliability feasibility**, not final population quality. Inspect every disagreement, especially `AC/AP/RV` and `NO/UN`. One human annotator is a reviewed reference, not IAA. Two AI annotators imply **model-model** agreement only.

## Decision gate before classification

- Assess coverage of context, interleaved practice IDs, PII and truncated messages.
- Fix ambiguity and freeze a **new** codebook v0.2, keeping version v0.1 auditable.
- Start a fresh 140-case pilot batch with two independent raters on ≥60 cases if resources permit.
- Only if the ontology is consistently applied, train majority vs student-only TF-IDF vs tutor-context TF-IDF and a shuffled-tutor-context control on **session-disjoint folds**.
- Never use future answer correctness or posttest score in annotation inputs.

## AI annotators, if used

Codex/Astra and Gemini/Antigravity may serve as two **silver-labeling agents**, but do not present those outputs as human adjudication. Each needs a new chat and separate local checkout; prompts must point to the SAME frozen codebook. Human audit still required before substantive claims.

## What has actually been completed

- Successful extraction of **180 real unlabeled episodes** from **78/78** downloaded sessions; **1,795** eligible student turns in sampled sessions, **68 distinct sessions** in pilot, 13 tutor arms.
- Script, codebook, CSV validator and κ comparison method committed.
- NOT done: human annotation, agreement metrics from real human labels, trained classifiers, verified behavioral correlation or causal evidence.

Reference metadata: [ND1 extraction aggregate audit](../reports/ND1_real_pilot_extraction_audit_2026-10-25.json).
