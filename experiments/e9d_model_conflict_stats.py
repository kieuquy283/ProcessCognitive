#!/usr/bin/env python3
"""E9d reproducible model-model disagreement and rubric sensitivity audit.

Reads private original E9c annotator CSVs; writes ONLY aggregate metrics.
The generic-keyword pattern reproduces the 30/90 sampling-strata split for
the supplied 120-pair pilot; use with caution on other samples.
"""
import argparse
import collections
import csv
import json
import re
from pathlib import Path

import numpy as np
from scipy.stats import fisher_exact, binomtest

GENERIC = re.compile(
    r"\b(?:QC|strategy|strategies|test[- ]taking|exam technique|edge cases|"
    r"time management|guessing|approach|problem[- ]solving)\b", re.I
)
LABELS = ("D", "S", "N", "U")


def load(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    ids = [r["pair_id"] for r in rows]
    if len(rows) != 120 or len(set(ids)) != 120:
        raise ValueError(f"{path}: expected 120 distinct pairs")
    if any(r["label"] not in LABELS for r in rows):
        raise ValueError(f"{path}: invalid label(s)")
    return rows


def cohens_kappa(a, b):
    obs = np.mean(a == b)
    chance = sum(np.mean(a == v) * np.mean(b == v) for v in set(a) | set(b))
    return (obs - chance) / (1 - chance) if chance < 1 else None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model-a", type=Path, required=True)
    p.add_argument("--model-b", type=Path, required=True)
    p.add_argument("--out", type=Path, default=Path("annotation_work/e9d_conflict_stats.json"))
    p.add_argument("--bootstrap", type=int, default=15000)
    args = p.parse_args()
    A, B = load(args.model_a), load(args.model_b)
    for a, b in zip(A, B):
        if any(a[k] != b[k] for k in (
            "pair_id", "gre_skill", "gre_subskill", "tutoring_concept_title")):
            raise ValueError("Models' CSV content or order is different")

    labels_a = np.asarray([r["label"] for r in A])
    labels_b = np.asarray([r["label"] for r in B])
    disagree = labels_a != labels_b
    generic = np.asarray([bool(GENERIC.search(r["tutoring_concept_title"])) for r in A])
    g = disagree[generic]
    other = disagree[~generic]

    subskills = sorted({r["gre_subskill"] for r in A})
    cluster = {
        name: np.array([i for i, r in enumerate(A) if r["gre_subskill"] == name])
        for name in subskills
    }
    rng = np.random.default_rng(20261024)
    risk_differences = []
    for _ in range(args.bootstrap):
        sample = np.concatenate(
            [cluster[subskills[j]] for j in rng.integers(0, len(subskills), len(subskills))]
        )
        sample_generic = generic[sample]
        sample_disagree = disagree[sample]
        if sample_generic.any() and (~sample_generic).any():
            risk_differences.append(
                float(sample_disagree[sample_generic].mean() -
                      sample_disagree[~sample_generic].mean())
            )

    merged = {"D": "D", "S": "R", "N": "R", "U": "U"}
    mapped_a = np.asarray([merged[v] for v in labels_a])
    mapped_b = np.asarray([merged[v] for v in labels_b])
    a_s_b_n = int(np.sum((labels_a == "S") & (labels_b == "N")))
    a_n_b_s = int(np.sum((labels_a == "N") & (labels_b == "S")))
    matrix = {x: {y: int(np.sum((labels_a == x) & (labels_b == y)))
                  for y in LABELS} for x in LABELS}
    stats = {
        "n_pairs": len(A), "model_model_agreement": float(np.mean(~disagree)),
        "nominal_kappa_4_class": float(cohens_kappa(labels_a, labels_b)),
        "confusion_A_rows_B_columns": matrix,
        "generic_title_count": int(generic.sum()),
        "generic_disagreement": int(g.sum()),
        "other_disagreement": int(other.sum()),
        "generic_disagreement_rate": float(g.mean()),
        "other_disagreement_rate": float(other.mean()),
        "generic_minus_other_disagreement_pp": float((g.mean() - other.mean()) * 100),
        "fisher_independent_pairs_exploratory": {
            "odds_ratio": float(fisher_exact([[g.sum(), len(g) - g.sum()],
                                              [other.sum(), len(other) - other.sum()]]).statistic),
            "p_value": float(fisher_exact([[g.sum(), len(g) - g.sum()],
                                           [other.sum(), len(other) - other.sum()]]).pvalue),
            "warning": "Independent-pair assumption is imperfect; 120 stratified pairs share subskills.",
        },
        "risk_difference_subskill_cluster_bootstrap_95ci":
            np.quantile(risk_differences, [0.025, 0.975]).tolist(),
        "SN_directional": {
            "A_S_B_N": a_s_b_n, "A_N_B_S": a_n_b_s,
            "exact_symmetry_p_exploratory": binomtest(
                min(a_s_b_n, a_n_b_s), a_s_b_n + a_n_b_s, 0.5
            ).pvalue if a_s_b_n + a_n_b_s else None,
        },
        "collapsed_S_N_model_agreement": float(np.mean(mapped_a == mapped_b)),
        "collapsed_S_N_kappa": float(cohens_kappa(mapped_a, mapped_b)),
        "note": "No human labels; no population accuracy/validity or predictive gain established.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
