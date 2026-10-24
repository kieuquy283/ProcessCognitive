#!/usr/bin/env python3
"""Frozen sentence embedding diagnostic, GRE Quant independent item correctness.

Usage: pip install -r requirements.txt -r requirements-research.txt
       python experiments/semantic_baseline.py --data ./data --output ./results/semantic.json
No raw dialogue, per-person predictions, or embeddings are exported.
"""
import argparse
import collections
import json
import random
from pathlib import Path

import numpy as np
import pandas as pd
from fastembed import TextEmbedding
from scipy.sparse import csr_matrix, hstack
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from studentbench_loader import load_question_bank, load_sessions

SEED = 20261024
NUMERIC = ["pre", "theta", "matched_pre", "pre_skill", "pre_subskill",
           "practice_n", "practice_correct", "practice_submissions"]
CATEGORY = ["question", "arm", "form", "skill", "subskill", "difficulty"]


def assign_folds(sessions):
    groups = collections.defaultdict(list)
    for i, s in enumerate(sessions):
        p = s["profile"]
        groups[(p["ai_model_preset_id"], p["assessment_form_order"])].append(i)
    fold_of, heldout = {}, set()
    for key, ids in sorted(groups.items()):
        ids.sort(key=lambda i: sessions[i]["profile"]["student_id"])
        random.Random("embedding" + str(key) + ":20261024").shuffle(ids)
        for j, i in enumerate(ids):
            if j % 5 == 0:
                heldout.add(i)
            else:
                fold_of[i] = j % 5 - 1
    return fold_of, heldout


def make_items(sessions, bank, dev_ids, fold_of):
    rows = []
    for session_number, i in enumerate(dev_ids):
        s = sessions[i]
        p = s["profile"]
        matching, skill, subskill = {}, collections.defaultdict(list), collections.defaultdict(list)
        for q in s["pre"]:
            b = bank.get(q["question_id"])
            if b and q["is_correct"] in ("0", "1"):
                value = int(q["is_correct"])
                matching[b["pair"]] = value
                skill[b["skill"]].append(value)
                subskill[b["subskill"]].append(value)
        for q in s["post"]:
            b = bank.get(q["question_id"])
            if b is None or q["is_correct"] not in ("0", "1"):
                continue
            rows.append({
                "sid": session_number, "fold": fold_of[i], "y": int(q["is_correct"]),
                "question": b["question_id"], "arm": p["ai_model_preset_id"],
                "form": p["assessment_form_order"], "skill": b["skill"],
                "subskill": b["subskill"], "difficulty": b["difficulty"],
                "pre": p["pretest_score_points"], "theta": p.get("pretest_irt_theta"),
                "matched_pre": matching.get(b["pair"], np.nan),
                "pre_skill": np.mean(skill[b["skill"]]) if skill[b["skill"]] else np.nan,
                "pre_subskill": np.mean(subskill[b["subskill"]]) if subskill[b["subskill"]] else np.nan,
                "practice_n": p["practice_problems_answered_count"],
                "practice_correct": p["practice_problems_final_correct_count"],
                "practice_submissions": p["practice_answer_submissions_count"],
            })
    return pd.DataFrame(rows)


def text_windows(text):
    if len(text) < 2200:
        return [text, text]
    return [text[:2200], text[-2200:]]


def pooled_embeddings(sessions, dev_ids, model_name, cache_dir):
    messages = []
    for i in dev_ids:
        s = sessions[i]
        messages.extend(text_windows(s["student_text"]))
        messages.extend(text_windows(s["tutor_text"]))
    encoder = TextEmbedding(model_name=model_name, cache_dir=cache_dir, threads=2)
    encoded = np.asarray(list(encoder.embed(messages, batch_size=64)), dtype=np.float32)
    chunks = encoded.reshape(len(dev_ids), 4, -1)
    def normalize(x):
        return x / np.maximum(np.linalg.norm(x, axis=1, keepdims=True), 1e-7)
    student = normalize((chunks[:, 0] + chunks[:, 1]) * 0.5)
    tutor = normalize((chunks[:, 2] + chunks[:, 3]) * 0.5)
    delta = normalize(chunks[:, 1] - chunks[:, 0])
    permutation = np.arange(len(dev_ids))
    groups = collections.defaultdict(list)
    for j, i in enumerate(dev_ids):
        p = sessions[i]["profile"]
        groups[(p["ai_model_preset_id"], p["assessment_form_order"])].append(j)
    rng = np.random.default_rng(1024)
    for group in groups.values():
        if len(group) > 1:
            permutation[group] = rng.permutation(group)
    return {"student": student, "tutor": tutor,
            "delta": delta, "permuted_student": student[permutation]}


def evaluate(df, embeddings, regularization):
    y = df["y"].to_numpy()
    outputs = {}
    variants = {
        "baseline": [], "student_embedding": ["student"], "tutor_embedding": ["tutor"],
        "both_embeddings": ["student", "tutor"],
        "student_semantic_change": ["student", "delta"],
        "permuted_student_embedding": ["permuted_student"],
    }
    for name, keys in variants.items():
        pred = np.zeros(len(df))
        for fold in sorted(df.fold.unique()):
            tr = np.flatnonzero((df.fold != fold).to_numpy())
            va = np.flatnonzero((df.fold == fold).to_numpy())
            prep = ColumnTransformer([
                ("num", Pipeline([("impute", SimpleImputer(strategy="median")),
                                  ("scale", StandardScaler())]), NUMERIC),
                ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORY)
            ], sparse_threshold=1.0)
            xtr = prep.fit_transform(df.iloc[tr][NUMERIC + CATEGORY])
            xva = prep.transform(df.iloc[va][NUMERIC + CATEGORY])
            if keys:
                arr = np.concatenate([embeddings[k] for k in keys], axis=1) * 2.0
                xtr = hstack([xtr, csr_matrix(arr[df.iloc[tr].sid.to_numpy()])], format="csr")
                xva = hstack([xva, csr_matrix(arr[df.iloc[va].sid.to_numpy()])], format="csr")
            model = LogisticRegression(solver="liblinear", C=regularization, max_iter=250)
            model.fit(xtr, y[tr])
            pred[va] = model.predict_proba(xva)[:, 1]
        outputs[name] = pred
    metrics = {
        name: {"logloss": float(log_loss(y, p)),
               "brier": float(brier_score_loss(y, p)),
               "auc": float(roc_auc_score(y, p))}
        for name, p in outputs.items()
    }
    loss = lambda p: -(y * np.log(np.clip(p, 1e-7, 1-1e-7)) +
                       (1-y) * np.log(np.clip(1-p, 1e-7, 1-1e-7)))
    base = loss(outputs["baseline"])
    comparisons = {}
    for name, p in outputs.items():
        if name == "baseline":
            continue
        diff = base - loss(p)
        per_session = pd.DataFrame({"sid": df.sid, "diff": diff}).groupby("sid")["diff"].mean().to_numpy()
        sims = np.random.default_rng(2468).choice(
            per_session, size=(1600, len(per_session)), replace=True).mean(axis=1)
        comparisons[name] = {
            "delta_logloss": float(per_session.mean()),
            "bootstrap_ci95": np.quantile(sims, [.025, .975]).tolist()}
    return metrics, comparisons


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--output", type=Path, default=Path("results/semantic.json"))
    p.add_argument("--per-tutor", type=int, default=62)
    p.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    p.add_argument("--cache-dir", default=".cache/fastembed")
    args = p.parse_args()
    sessions = load_sessions(args.data, per_tutor=args.per_tutor)
    bank = load_question_bank(args.data)
    fold_of, heldout = assign_folds(sessions)
    dev_ids = sorted(fold_of)
    if len(dev_ids) < 80:
        raise ValueError("Insufficient sessions; use full official StudentBench data")
    df = make_items(sessions, bank, dev_ids, fold_of)
    representations = pooled_embeddings(sessions, dev_ids, args.model, args.cache_dir)
    result = {"n_total": len(sessions), "n_dev": len(dev_ids),
              "n_holdout_unopened": len(heldout), "n_dev_items": len(df),
              "encoder": args.model, "note": "Exploratory development CV only; holdout unopened.",
              "runs": {}}
    for c in (0.03, 0.3):
        metrics, comparisons = evaluate(df, representations, c)
        result["runs"][str(c)] = {"metrics": metrics, "comparisons": comparisons}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
