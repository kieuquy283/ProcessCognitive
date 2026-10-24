#!/usr/bin/env python3
"""E9d: compare a completed blinded expert review with two frozen GPT label files.

Not for unannotated sheets; not a ground-truth claim. The 41 reviewed items
deliberately oversample the 21 model disagreements.
Usage:
 python experiments/e9d_analyze_expert_review.py \
   --expert-csv annotation_work/e9d_review_filled.csv \
   --model-a annotation_work/codex_astra/e9c_annotator_A.csv \
   --model-b annotation_work/antigravity_gemini/e9c_annotator_B.csv \
   --out annotation_work/e9d_expert_comparison.json

From the blinded XLSX, export just the Audit_41 worksheet as UTF-8 CSV.
All outputs are local, aggregated, and should remain gitignored.
"""
import argparse
import collections
import csv
import json
from pathlib import Path

LABELS = ("D", "S", "N", "U")


def load_csv(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def kappa(x, y):
    if len(x) != len(y) or not x:
        raise ValueError("Equal non-empty paired labels required")
    observed = sum(a == b for a, b in zip(x, y)) / len(x)
    expected = sum(x.count(k) * y.count(k) for k in LABELS) / (len(x)**2)
    return None if expected >= 1 else (observed - expected) / (1 - expected)


def load_model(path):
    rows = load_csv(path)
    if len(rows) != 120:
        raise ValueError(f"{path}: expected exactly 120 labels")
    index = {}
    for r in rows:
        pair = r["pair_id"]
        if pair in index or r["label"] not in LABELS:
            raise ValueError(f"{path}: duplicate ID or invalid label {pair}")
        index[pair] = r
    return index


def read_expert(path):
    rows = load_csv(path)
    if len(rows) != 41:
        raise ValueError(f"{path}: expected 41 blinded expert review rows")
    index = {}
    for r in rows:
        key = r.get("Pair ID", r.get("pair_id"))
        label = r.get("Final label (D/S/N/U)", r.get("Human label", r.get("label")))
        math_axis = r.get("Math content relationship", "")
        strategy_axis = r.get("General strategy present?", "")
        rationale = r.get("Rationale (1–25 words)", r.get("Human rationale", r.get("rationale", "")))
        concept = r.get("Tutoring concept title", r.get("tutoring_concept_title"))
        subskill = r.get("GRE subskill", r.get("gre_subskill"))
        if not key or key in index:
            raise ValueError(f"Duplicate/missing pair ID: {key}")
        if not label or label.strip() not in LABELS:
            raise ValueError(f"Missing or invalid expert label: {key}")
        if not rationale or len(rationale.split()) > 25:
            raise ValueError(f"Invalid/missing expert rationale: {key}")
        if math_axis and math_axis not in ("Specific match", "Different topic", "Unclear or partial"):
            raise ValueError(f"Invalid mathematical axis: {key}")
        if strategy_axis and strategy_axis not in (
            "Explicit general strategy", "No explicit strategy", "Unclear"
        ):
            raise ValueError(f"Invalid strategy axis: {key}")
        index[key] = {
            "label": label.strip(), "math_axis": math_axis,
            "strategy_axis": strategy_axis,
            "subskill": subskill, "concept": concept
        }
    return index


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--expert-csv", required=True, type=Path)
    p.add_argument("--model-a", required=True, type=Path)
    p.add_argument("--model-b", required=True, type=Path)
    p.add_argument("--out", default=Path("annotation_work/e9d_expert_comparison.json"), type=Path)
    args = p.parse_args()
    A, B = load_model(args.model_a), load_model(args.model_b)
    E = read_expert(args.expert_csv)
    if len(set(A) & set(B)) != 120 or any(k not in A or k not in B for k in E):
        raise ValueError("Review IDs do not align to both original 120-item annotation sets")
    for key, r in E.items():
        for m in (A[key], B[key]):
            if (r["subskill"], r["concept"]) != (
                m["gre_subskill"], m["tutoring_concept_title"]
            ):
                raise ValueError(f"Content changed between model and human review for {key}")
    conflicts = [k for k in E if A[k]["label"] != B[k]["label"]]
    agrees = [k for k in E if A[k]["label"] == B[k]["label"]]
    if len(conflicts) != 21 or len(agrees) != 20:
        raise ValueError(f"Unexpected sampling protocol: conflicts={len(conflicts)}, controls={len(agrees)}")

    def summarize(keys):
        human = [E[k]["label"] for k in keys]
        one = [A[k]["label"] for k in keys]
        two = [B[k]["label"] for k in keys]
        return {
            "n": len(keys), "expert_label_distribution": dict(collections.Counter(human)),
            "A_equals_expert": sum(x == h for x, h in zip(one, human)),
            "B_equals_expert": sum(x == h for x, h in zip(two, human)),
            "A_vs_expert_kappa": kappa(one, human),
            "B_vs_expert_kappa": kappa(two, human),
        }

    favor = {"A": 0, "B": 0, "neither": 0}
    for key in conflicts:
        human = E[key]["label"]
        if human == A[key]["label"]: favor["A"] += 1
        elif human == B[key]["label"]: favor["B"] += 1
        else: favor["neither"] += 1

    controls = collections.Counter(
        ("expert_matches_both" if E[k]["label"] == A[k]["label"] else "expert_disagrees_both")
        for k in agrees
    )
    axes = collections.Counter(
        (r["math_axis"], r["strategy_axis"], r["label"]) for r in E.values()
        if r["math_axis"] and r["strategy_axis"]
    )
    flags = {
        "D_without_specific_match": sum(
            r["label"] == "D" and r["math_axis"] and r["math_axis"] != "Specific match"
            for r in E.values()
        ),
        "S_without_explicit_strategy": sum(
            r["label"] == "S" and r["strategy_axis"] and r["strategy_axis"] != "Explicit general strategy"
            for r in E.values()
        ),
    }

    summary = {
        "status": "EXPERT_REVIEW_COMPARISON",
        "n_total": 41, "n_conflicts": 21, "n_controls": 20,
        "whole_enriched_sample": summarize(list(E)),
        "conflict_group": summarize(conflicts), "concordant_controls": summarize(agrees),
        "conflict_expert_preference": favor,
        "concordant_control_expert_verdicts": dict(controls),
        "two_axis_counts": [
            {"math_content": m, "general_strategy": s, "final_label": lab, "n": n}
            for (m, s, lab), n in sorted(axes.items())
        ],
        "quality_flags_to_review": flags,
        "warnings": [
            "Expert reference is not definitive ground truth or causal evidence.",
            "The 41-case set enriches for GPT disagreements; no unweighted population accuracy.",
            "No predictive-model performance can be inferred from this adjudication.",
            "This script did not modify original Astra or Gemini labels.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
