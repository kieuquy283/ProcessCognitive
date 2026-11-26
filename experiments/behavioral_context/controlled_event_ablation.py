#!/usr/bin/env python3
"""E8R: nested event-order ablation, GRE Quant development sessions only.

Not semantic behavior labels; not a held-out or causal educational study.
Keep static data and full-session event histograms fixed when adding order.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SYMBOLS = ("S", "A", "P", "C", "W", "U")
SEED = 20261024
NUMERIC = ("pretest_score_points", "pretest_irt_theta",
           "practice_problems_answered_count",
           "practice_problems_final_correct_count",
           "practice_answer_submissions_count",
           "student_messages_sent_to_tutor", "ai_tutor_messages_sent_to_student",
           "all_event_count")
CAT = ("ai_model_preset_id", "assessment_form_order")
BAGS = tuple(f"bag_{s}" for s in SYMBOLS)
EDGES = tuple(f"edge_{a}_{b}" for a in SYMBOLS for b in SYMBOLS)


def deterministic_shuffle(seq, session_id, seed=SEED):
    digest = hashlib.sha256(f"{seed}|{session_id}".encode()).digest()
    rng = np.random.default_rng(int.from_bytes(digest[:8], "big"))
    arr = np.array(seq, dtype=object)
    rng.shuffle(arr)
    return arr.tolist()


def event_features(sequence):
    seq = list(sequence)
    if any(x not in SYMBOLS for x in seq):
        raise ValueError("unexpected event symbol")
    n = len(seq)
    counts = Counter(seq)
    transitions = Counter(zip(seq, seq[1:]))
    return {
        **{f"bag_{s}": counts[s] / max(1, n) for s in SYMBOLS},
        **{f"edge_{a}_{b}": transitions[(a, b)] / max(1, n - 1)
           for a in SYMBOLS for b in SYMBOLS},
    }


def assign_original_e8_folds(sessions):
    """Replicate existing E7/E8 tutor/form-grouped development partition."""
    groups = defaultdict(list)
    for i, s in enumerate(sessions):
        p = s["profile"]
        groups[(p["ai_model_preset_id"], p["assessment_form_order"])].append(i)
    folds, holdout = {}, set()
    for key, ids in sorted(groups.items()):
        ids.sort(key=lambda i: sessions[i]["profile"]["student_id"])
        random.Random("embedding" + str(key) + ":20261024").shuffle(ids)
        for j, i in enumerate(ids):
            if j % 5 == 0:
                holdout.add(i)
            else:
                folds[i] = j % 5 - 1
    if set(folds) & holdout or len(folds) + len(holdout) != len(sessions):
        raise RuntimeError("session partition is invalid")
    return folds, holdout


def assemble(sessions, dev_ids):
    """Posttest is target y only, never a feature or a splitting variable."""
    records, shuffled = [], []
    for i in dev_ids:
        s = sessions[i]
        p = s["profile"]
        seq = list(s["events"])
        if len(seq) < 2:
            raise ValueError("need >=2 events per session")
        row = {k: p.get(k) for k in NUMERIC if k != "all_event_count"}
        row.update({k: p.get(k) for k in CAT})
        row["all_event_count"] = len(seq)
        row.update(event_features(seq))
        row["y"] = p["posttest_score_points"]
        records.append(row)
        shuf = event_features(deterministic_shuffle(seq, p["student_id"]))
        shuffled.append({f"null_{c}": shuf[c] for c in EDGES})
    return pd.concat([pd.DataFrame(records), pd.DataFrame(shuffled)], axis=1)


def ridge_pipeline(columns):
    numeric = [c for c in columns if c not in CAT]
    categorical = [c for c in columns if c in CAT]
    return Pipeline([
        ("pre", ColumnTransformer([
            ("numeric", Pipeline([
                ("fill", SimpleImputer(strategy="median")),
                ("scale", StandardScaler())]), numeric),
            ("categorical", Pipeline([
                ("fill", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore"))]), categorical),
        ])),
        ("model", Ridge()),
    ])


def score_development(df, fold_values, seed=SEED, n_boot=2000):
    if len(df) < 80 or len(df) != len(fold_values):
        raise ValueError("E8R BLOCKED: require >=80 development sessions with matched folds")
    required = set(NUMERIC) | set(CAT) | set(BAGS) | set(EDGES) | {"y"} | {
        f"null_{c}" for c in EDGES}
    if required - set(df.columns):
        raise ValueError(f"missing required columns {sorted(required-set(df.columns))}")
    if any(k in df for k in ("posttest_score_points", "score_lift_points", "student_id")):
        raise ValueError("forbidden outcome/identifier feature")
    y = df.y.to_numpy(dtype=float)
    folds = np.asarray(fold_values)
    if not np.isfinite(y).all() or y.min() < 0 or y.max() > 27:
        raise ValueError("invalid posttest target")
    if set(folds) != {0, 1, 2, 3} or any((folds == f).sum() < 5 for f in range(4)):
        raise ValueError("four development folds with >=5 sessions per fold required")
    static = list(NUMERIC) + list(CAT)
    configs = {
        "M0_static": static,
        "M1_static_bag": static + list(BAGS),
        "M2_static_bag_ordered": static + list(BAGS) + list(EDGES),
        "M2_null_static_bag_shuffled": static + list(BAGS) + [
            f"null_{c}" for c in EDGES],
    }
    pred = {name: np.full(len(df), np.nan) for name in configs}
    for f in range(4):
        train = np.flatnonzero(folds != f)
        test = np.flatnonzero(folds == f)
        inner = KFold(n_splits=3, shuffle=True, random_state=seed + f)
        for name, cols in configs.items():
            model = GridSearchCV(
                ridge_pipeline(cols), {"model__alpha": [1., 10., 100.]},
                cv=inner, scoring="neg_mean_absolute_error")
            model.fit(df.iloc[train][cols], y[train])
            pred[name][test] = model.predict(df.iloc[test][cols])
    if any(not np.isfinite(values).all() for values in pred.values()):
        raise RuntimeError("missing OOF predictions")
    metrics = {
        name: {
            "MAE_score_points": float(mean_absolute_error(y, values)),
            "RMSE_score_points": float(np.sqrt(mean_squared_error(y, values))),
            "R2": float(r2_score(y, values)),
        } for name, values in pred.items()
    }
    contrasts = {}
    rng = np.random.default_rng(seed)
    for label, a, b in [
        ("bag_vs_static", "M0_static", "M1_static_bag"),
        ("order_vs_bag", "M1_static_bag", "M2_static_bag_ordered"),
        ("order_vs_shuffle", "M2_null_static_bag_shuffled", "M2_static_bag_ordered"),
    ]:
        gain = np.abs(y - pred[a]) - np.abs(y - pred[b])
        idx = rng.integers(0, len(y), size=(n_boot, len(y)))
        contrasts[label] = {
            "mean_MAE_reduction_points": float(gain.mean()),
            "percentile_CI95": np.quantile(gain[idx].mean(axis=1),
                                          [.025, .975]).tolist(),
        }
    return {
        "status": "DEVELOPMENT_EXPLORATORY_ONLY",
        "n_development_sessions": len(df), "n_folds": 4,
        "models": metrics, "paired_MAE_contrasts": contrasts,
        "interpretation": "These are system-event features, not validated student "
                          "behavioral states. Paired bootstrap is conditional "
                          "on development OOF model selection; no causal inference.",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data", required=True, type=Path)
    p.add_argument("--output", type=Path,
                   default=Path("results/e8r_controlled_event_ablation.json"))
    p.add_argument("--per-tutor", type=int, default=62)
    p.add_argument("--allow-full-count", action="store_true")
    args = p.parse_args()
    if not (args.data / "studentbench_overall_parameters.json").exists():
        raise SystemExit("E8R BLOCKED: official dataset root missing")
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from studentbench_loader import load_sessions
    sessions = load_sessions(args.data, per_tutor=None if args.allow_full_count
                             else args.per_tutor)
    fold_map, holdout = assign_original_e8_folds(sessions)
    dev_ids = sorted(fold_map)
    report = score_development(assemble(sessions, dev_ids),
                               [fold_map[i] for i in dev_ids])
    report.update({
        "n_loaded": len(sessions), "n_holdout_unopened": len(holdout),
        "upstream_revision_not_verified": True,
        "source": "https://github.com/Handshake-AI-Research/studentbench",
        "input_scope": "Full-session bag/edges for all comparisons; no 256-event truncation",
    })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
