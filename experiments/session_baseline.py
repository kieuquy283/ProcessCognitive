#!/usr/bin/env python3
"""StudentBench Quantitative session-level benchmark; exploratory, no held-out test evaluation."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def load_sessions(folder):
    rows = []
    for path in sorted((folder / "1_main_leaderboard_data" / "gre_quant").glob("ai_arm_*/task_id_*/student_data/student.json")):
        p = json.loads(path.read_text(encoding="utf-8"))
        keys = ("pretest_score_points", "posttest_score_points", "practice_problems_answered_count",
                "practice_answer_submissions_count", "practice_problems_final_correct_count",
                "student_messages_sent_to_tutor", "ai_tutor_messages_sent_to_student")
        if any(p.get(k) is None for k in keys):
            continue
        rows.append(dict(session=p["student_id"],
                         form=p["assessment_form_order"], tutor=p["ai_model_preset_id"],
                         pre=p["pretest_score_points"], pre_theta=p.get("pretest_irt_theta"),
                         practice_count=p["practice_problems_answered_count"],
                         practice_submissions=p["practice_answer_submissions_count"],
                         practice_correct=p["practice_problems_final_correct_count"],
                         student_msgs=p["student_messages_sent_to_tutor"],
                         tutor_msgs=p["ai_tutor_messages_sent_to_student"],
                         post=p["posttest_score_points"] / 27.0))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, type=Path)
    ap.add_argument("--output", default="results", type=Path)
    args = ap.parse_args()
    df = load_sessions(args.data)
    if df.empty or df["session"].nunique() < 10:
        raise ValueError("Not enough valid GRE Quantitative sessions found")
    # Deterministic partition by session, not by individual posttest item.
    ids = sorted(df.session.unique())
    rng = np.random.default_rng(20261023)
    rng.shuffle(ids)
    reserve = set(ids[:max(1, int(len(ids) * .2))])
    dev = df[~df.session.isin(reserve)].copy()
    cats = ["form", "tutor"]
    base = ["pre", "pre_theta"]
    configs = {"pretest": base,
               "practice": base + ["practice_count", "practice_submissions", "practice_correct"],
               "interaction_counts": base + ["practice_count", "practice_submissions",
                                             "practice_correct", "student_msgs", "tutor_msgs"]}
    fold = GroupKFold(n_splits=4)
    report = {"sessions_total": len(df), "development_sessions": len(dev),
              "heldout_sessions_unopened": len(reserve), "metrics": {}}
    for name, cols in configs.items():
        oof = np.full(len(dev), np.nan)
        for tr, va in fold.split(dev, groups=dev.session):
            features = ColumnTransformer([
                ("num", Pipeline([("impute", SimpleImputer(strategy="median")),
                                  ("scale", StandardScaler())]), cols),
                ("cat", OneHotEncoder(handle_unknown="ignore"), cats)])
            model = Pipeline([("features", features), ("ridge", Ridge(alpha=10.0, solver="lsqr"))])
            model.fit(dev.iloc[tr][cols + cats], dev.iloc[tr].post)
            oof[va] = np.clip(model.predict(dev.iloc[va][cols + cats]), 0, 1)
        rmse = float(27 * np.sqrt(mean_squared_error(dev.post, oof)))
        report["metrics"][name] = {"oof_rmse_score_points": rmse}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "session_baseline.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
