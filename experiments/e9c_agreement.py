#!/usr/bin/env python3
"""E9c: inter-annotator reliability and disagreement audit.

Use only after two independent people have annotated E9c pairs.
No raw titles, learner data, transcript or individual labels are written to Git.
"""
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

LABELS = ("D", "S", "N", "U")


def records(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"Empty annotation file: {path}")
    required = {"pair_id", "gre_subskill", "tutoring_concept_title", "label"}
    if not required.issubset(rows[0]):
        raise ValueError("Required columns missing: " + ", ".join(sorted(required - set(rows[0]))))
    data = {}
    for row in rows:
        key = row["pair_id"].strip()
        if not key or key in data:
            raise ValueError("Missing or duplicated pair_id")
        label = row["label"].strip().upper()
        if label not in LABELS:
            raise ValueError(f"{path}: pair {key} has missing/invalid label. Allowed: {LABELS}")
        data[key] = row
    return data


def nominal_agreement(a, b, labels=LABELS):
    n = len(a)
    if not n:
        raise ValueError("No paired labels")
    matching = sum(x == y for x, y in zip(a, b))
    p_observed = matching / n
    pa = Counter(a)
    pb = Counter(b)
    p_expected = sum(pa[t] * pb[t] for t in labels) / (n * n)
    kappa = ((p_observed - p_expected) / (1.0 - p_expected)
             if p_expected < 1 else None)
    return {
        "n": n, "raw_agreement": p_observed,
        "expected_chance_agreement": p_expected,
        "cohen_kappa": kappa,
    }


def ordinal_binary(labels, positive):
    return ["positive" if x in positive else "other" for x in labels]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotator-a", type=Path, required=True)
    parser.add_argument("--annotator-b", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("annotation_work/e9c_agreement.json"))
    parser.add_argument("--disagreements", type=Path,
                        default=Path("annotation_work/e9c_disagreements_private.csv"))
    args = parser.parse_args()

    A = records(args.annotator_a)
    B = records(args.annotator_b)
    if set(A) != set(B):
        raise ValueError("Annotation files contain different pair IDs")
    keys = sorted(A)
    for k in keys:
        if (A[k]["gre_subskill"], A[k]["tutoring_concept_title"]) != (
                B[k]["gre_subskill"], B[k]["tutoring_concept_title"]):
            raise ValueError(f"Pair content differs for ID {k}")
    labels_a = [A[k]["label"].strip().upper() for k in keys]
    labels_b = [B[k]["label"].strip().upper() for k in keys]

    confusion = {x: {y: 0 for y in LABELS} for x in LABELS}
    for a, b in zip(labels_a, labels_b):
        confusion[a][b] += 1

    strict_a = ordinal_binary(labels_a, {"D"})
    strict_b = ordinal_binary(labels_b, {"D"})
    broad_a = ordinal_binary(labels_a, {"D", "S"})
    broad_b = ordinal_binary(labels_b, {"D", "S"})

    agreement = nominal_agreement(labels_a, labels_b)
    stats = {
        "status": "HUMAN_ANNOTATION_COMPLETED",
        "label_definitions": {
            "D": "Direct mathematical concept coverage",
            "S": "General problem-solving strategy",
            "N": "No meaningful relation",
            "U": "Indeterminate from titles alone",
        },
        "four_class": agreement,
        "strict_D_vs_non_D": nominal_agreement(
            strict_a, strict_b, labels=("positive", "other")),
        "broad_D_or_S_vs_N_or_U": nominal_agreement(
            broad_a, broad_b, labels=("positive", "other")),
        "label_counts_annotator_A": dict(Counter(labels_a)),
        "label_counts_annotator_B": dict(Counter(labels_b)),
        "confusion_rows_A_columns_B": confusion,
        "disagreement_count": sum(a != b for a, b in zip(labels_a, labels_b)),
        "caution": ("Kappa is affected by prevalence and sampling. This stratified "
                    "120-pair audit does not estimate population prevalence without weighting."),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(stats, indent=2), encoding="utf-8")

    args.disagreements.parent.mkdir(parents=True, exist_ok=True)
    with args.disagreements.open("w", encoding="utf-8", newline="") as f:
        cols = ["pair_id", "gre_subskill", "tutoring_concept_title",
                "annotator_A", "annotator_B", "rationale_A", "rationale_B"]
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        for k in keys:
            if A[k]["label"] != B[k]["label"]:
                writer.writerow({
                    "pair_id": k,
                    "gre_subskill": A[k]["gre_subskill"],
                    "tutoring_concept_title": A[k]["tutoring_concept_title"],
                    "annotator_A": A[k]["label"],
                    "annotator_B": B[k]["label"],
                    "rationale_A": A[k].get("rationale", ""),
                    "rationale_B": B[k].get("rationale", ""),
                })
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
