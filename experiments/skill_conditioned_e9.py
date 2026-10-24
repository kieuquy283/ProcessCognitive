#!/usr/bin/env python3
"""E9: skill-conditioned learning evidence for independent GRE post-test correctness.

Experimental, not a confirmatory or causal estimator.
No raw student text or per-student predictions are written to disk.

Usage:
  pip install -r requirements.txt -r requirements-research.txt
  python experiments/skill_conditioned_e9.py --data ./data --output ./results/e9.json
"""
import argparse
import collections
import csv
import json
import random
from pathlib import Path

import numpy as np
import pandas as pd
from fastembed import TextEmbedding
from scipy.special import softmax
from scipy.sparse import csr_matrix, hstack
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SEED = 20261024
NUM = ["pre_total", "pre_theta", "matched_pre", "pre_skill", "pre_subskill",
       "practice_n", "practice_correct", "practice_attempts", "student_msgs", "tutor_msgs"]
CAT = ["question", "skill", "subskill", "difficulty", "arm", "form"]
OPTIONS = {
    "baseline": None,
    "pooled_student": "pooled_student",
    "skill_student": "skill_student",
    "permuted_skill": "permuted_skill",
    "pooled_tutor": "pooled_tutor",
    "skill_tutor": "skill_tutor",
}


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_data(root, per_arm=48):
    base = Path(root) / "1_main_leaderboard_data" / "gre_quant"
    if not base.is_dir():
        raise FileNotFoundError(f"GRE Quant directory missing: {base}")
    if per_arm < 1:
        raise ValueError("per_arm must be positive")
    sessions = []
    for arm in sorted(base.glob("ai_arm_*")):
        selected = sorted(arm.glob("task_id_*"))
        random.Random("E9:1_main_leaderboard_data/gre_quant/" + arm.name).shuffle(selected)
        for task in selected[:per_arm]:
            files = [task / "student_data" / "student.json",
                     task / "student_data" / "pretest_responses.csv",
                     task / "student_data" / "posttest_responses.csv",
                     task / "ai_tutoring_data" / "student_ai_tutor_interaction_trajectory.csv",
                     task / "ai_lesson_plan_data" / "lesson_plan_including_practice_problems.json"]
            if not all(f.is_file() for f in files):
                continue
            try:
                profile = json.loads(files[0].read_text("utf8"))
                pre, post, events = read_csv(files[1]), read_csv(files[2]), read_csv(files[3])
                plan = json.loads(files[4].read_text("utf8"))
                events.sort(key=lambda e: int(e["trajectory_position"]))
                concepts = {c["concept_id"]: {"name": c.get("name", ""), "student": [],
                                              "tutor": [], "n_events": 0}
                            for c in plan.get("concepts", [])}
                for event in events:
                    cid = event["concept_id"]
                    if not cid:
                        continue
                    c = concepts.setdefault(cid, {"name": "", "student": [], "tutor": [], "n_events": 0})
                    c["n_events"] += 1
                    if event["event_type"] == "student_message" and event["content"].strip():
                        c["student"].append(event["content"])
                    if event["event_type"] == "ai_tutor_message" and event["content"].strip():
                        c["tutor"].append(event["content"])
                details = [
                    {"name": c["name"], "student_text": " ".join(c["student"])[:5000],
                     "tutor_text": " ".join(c["tutor"])[:9000],
                     "student_messages": len(c["student"]), "tutor_messages": len(c["tutor"])}
                    for c in concepts.values() if c["n_events"] > 0
                ]
                sessions.append({"profile": profile, "pre": pre, "post": post, "concepts": details})
            except (ValueError, KeyError, OSError):
                continue
    qbank = {q["question_id"]: q for q in read_csv(Path(root) / "question_bank_quant.csv")}
    return sessions, qbank


def make_split(sessions):
    grouped = collections.defaultdict(list)
    for i, s in enumerate(sessions):
        p = s["profile"]
        grouped[(p["ai_model_preset_id"], p["assessment_form_order"])].append(i)
    fold_of, heldout = {}, set()
    for key, ids in sorted(grouped.items()):
        ids.sort(key=lambda i: sessions[i]["profile"]["student_id"])
        random.Random("E9" + str(key) + ":20261024").shuffle(ids)
        for j, idx in enumerate(ids):
            if j % 5 == 0:
                heldout.add(idx)
            else:
                fold_of[idx] = j % 5 - 1
    return fold_of, heldout


def normalize(array):
    return array / np.maximum(1e-7, np.linalg.norm(array, axis=-1, keepdims=True))


def prepare_item_features(sessions, qbank, fold_of, model_name, cache_dir):
    dev_ids = sorted(fold_of)
    subskills = sorted({q["subskill"] for q in qbank.values()})
    query_index = {skill: j for j, skill in enumerate(subskills)}
    concepts = [(i, c) for i in dev_ids for c in sessions[i]["concepts"]]
    texts = (
        ["GRE Quantitative mathematics subskill: " + s for s in subskills] +
        ["GRE mathematics concept: " + c["name"] for i, c in concepts] +
        [c["student_text"][:1800] if c["student_text"].strip() else "No student explanation recorded"
         for i, c in concepts] +
        [c["tutor_text"][:1800] if c["tutor_text"].strip() else "No tutor explanation recorded"
         for i, c in concepts]
    )
    encoder = TextEmbedding(model_name=model_name, cache_dir=str(cache_dir), threads=2)
    embeddings = normalize(np.asarray(list(encoder.embed(texts, batch_size=64)), dtype=np.float32))
    nquery, nconcept = len(subskills), len(concepts)
    Q = embeddings[:nquery]
    label_vectors = embeddings[nquery:nquery+nconcept]
    student_vectors = embeddings[nquery+nconcept:nquery+2*nconcept]
    tutor_vectors = embeddings[nquery+2*nconcept:]
    lookup = collections.defaultdict(list)
    for j, (i, _) in enumerate(concepts):
        lookup[i].append(j)

    representations = collections.defaultdict(list)
    item_rows = []
    for session_number, i in enumerate(dev_ids):
        s = sessions[i]
        p = s["profile"]
        candidate = lookup.get(i, [])
        student_indices = [j for j in candidate if concepts[j][1]["student_messages"] > 0]
        tutor_indices = [j for j in candidate if concepts[j][1]["tutor_messages"] > 0]

        def pooled(indices, vectors, attr):
            if not indices:
                return np.zeros(embeddings.shape[1], dtype=np.float32)
            weight = np.asarray([concepts[j][1][attr] for j in indices], dtype=np.float32)
            weight /= weight.sum()
            return normalize((weight[:, None] * vectors[indices]).sum(axis=0))

        global_student = pooled(student_indices, student_vectors, "student_messages")
        global_tutor = pooled(tutor_indices, tutor_vectors, "tutor_messages")
        order = list(range(len(student_indices)))
        random.Random("E9wrong:" + p["student_id"]).shuffle(order)

        matched = {}
        by_skill, by_subskill = collections.defaultdict(list), collections.defaultdict(list)
        for q in s["pre"]:
            item = qbank.get(q["question_id"])
            if item and q["is_correct"] in ("0", "1"):
                value = int(q["is_correct"])
                matched[item["pair"]] = value
                by_skill[item["skill"]].append(value)
                by_subskill[item["subskill"]].append(value)
        for response in s["post"]:
            item = qbank.get(response["question_id"])
            if not item or response["is_correct"] not in ("0", "1"):
                continue
            query = Q[query_index[item["subskill"]]]
            if student_indices:
                cosine = label_vectors[student_indices] @ query
                attention = softmax(cosine / 0.1)
                skill_student = normalize((attention[:, None] *
                                           student_vectors[student_indices]).sum(axis=0))
                # Negative control: preserve labels and message content, permute their pairing.
                wrong_student = normalize((attention[:, None] *
                                           student_vectors[np.asarray(student_indices)[order]]).sum(axis=0))
                sim = float(cosine.max())
                volume = float(np.log1p(np.dot(
                    attention, [concepts[j][1]["student_messages"] for j in student_indices])))
                wrong_volume = float(np.log1p(np.dot(
                    attention, [concepts[student_indices[k]][1]["student_messages"] for k in order])))
            else:
                skill_student = wrong_student = np.zeros(embeddings.shape[1], dtype=np.float32)
                sim, volume, wrong_volume = 0.0, 0.0, 0.0
            if tutor_indices:
                cosine = label_vectors[tutor_indices] @ query
                attention = softmax(cosine / 0.1)
                skill_tutor = normalize((attention[:, None] *
                                         tutor_vectors[tutor_indices]).sum(axis=0))
            else:
                skill_tutor = np.zeros(embeddings.shape[1], dtype=np.float32)
            skill_values = by_skill[item["skill"]]
            subskill_values = by_subskill[item["subskill"]]
            item_rows.append({
                "sid": session_number, "fold": fold_of[i], "y": int(response["is_correct"]),
                "question": item["question_id"], "skill": item["skill"],
                "subskill": item["subskill"], "difficulty": item["difficulty"],
                "arm": p["ai_model_preset_id"], "form": p["assessment_form_order"],
                "pre_total": p["pretest_score_points"], "pre_theta": p.get("pretest_irt_theta"),
                "matched_pre": matched.get(item["pair"], np.nan),
                "pre_skill": np.mean(skill_values) if skill_values else np.nan,
                "pre_subskill": np.mean(subskill_values) if subskill_values else np.nan,
                "practice_n": p["practice_problems_answered_count"],
                "practice_correct": p["practice_problems_final_correct_count"],
                "practice_attempts": p["practice_answer_submissions_count"],
                "student_msgs": p["student_messages_sent_to_tutor"],
                "tutor_msgs": p["ai_tutor_messages_sent_to_student"],
                "active_concepts": len(student_indices), "total_concepts": len(candidate),
                "max_relevance": sim, "aligned_volume": volume, "wrong_volume": wrong_volume,
            })
            for name, value in [
                ("pooled_student", global_student), ("skill_student", skill_student),
                ("permuted_skill", wrong_student), ("pooled_tutor", global_tutor),
                ("skill_tutor", skill_tutor)
            ]:
                representations[name].append(value)
    df = pd.DataFrame(item_rows)
    arrays = {name: np.asarray(values, dtype=np.float32) for name, values in representations.items()}
    return df, arrays, len(concepts)


def cross_validate(df, arrays, C, features=None):
    y = df["y"].to_numpy()
    output = {}
    for name, rep in OPTIONS.items():
        if features is not None and name not in features:
            continue
        pred = np.zeros(len(df))
        for fold in sorted(df.fold.unique()):
            tr = np.flatnonzero((df.fold != fold).to_numpy())
            va = np.flatnonzero((df.fold == fold).to_numpy())
            preprocess = ColumnTransformer([
                ("numbers", Pipeline([("impute", SimpleImputer(strategy="median")),
                                      ("scale", StandardScaler())]), NUM),
                ("categories", OneHotEncoder(handle_unknown="ignore"), CAT)
            ], sparse_threshold=1.0)
            xtr = preprocess.fit_transform(df.iloc[tr][NUM + CAT])
            xva = preprocess.transform(df.iloc[va][NUM + CAT])
            if rep:
                xtr = hstack([xtr, csr_matrix(arrays[rep][tr] * 2)], format="csr")
                xva = hstack([xva, csr_matrix(arrays[rep][va] * 2)], format="csr")
            classifier = LogisticRegression(solver="liblinear", C=C, max_iter=260)
            classifier.fit(xtr, y[tr])
            pred[va] = classifier.predict_proba(xva)[:, 1]
        output[name] = pred
    return output


def score(df, predictions):
    y = df["y"].to_numpy()
    return {name: {"logloss": float(log_loss(y, p)),
                   "brier": float(brier_score_loss(y, p)),
                   "auc": float(roc_auc_score(y, p))}
            for name, p in predictions.items()}


def paired_bootstrap(df, preds):
    y = df["y"].to_numpy()
    loss = lambda p: -(y * np.log(np.clip(p, 1e-8, 1-1e-8)) +
                       (1-y) * np.log(np.clip(1-p, 1e-8, 1-1e-8)))
    contrasts = {}
    comparisons = [
        ("baseline", "pooled_student"), ("baseline", "skill_student"),
        ("pooled_student", "skill_student"), ("permuted_skill", "skill_student"),
        ("pooled_tutor", "skill_tutor")
    ]
    for before, after in comparisons:
        difference = loss(preds[before]) - loss(preds[after])
        per_session = pd.DataFrame({"sid": df.sid, "diff": difference}).groupby("sid")["diff"].mean().to_numpy()
        draws = np.random.default_rng(2026).choice(
            per_session, size=(1600, len(per_session)), replace=True).mean(axis=1)
        contrasts[f"{before}_to_{after}"] = {
            "delta_logloss": float(per_session.mean()),
            "ci95": np.quantile(draws, [0.025, 0.975]).tolist()
        }
    return contrasts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path("results/e9.json"))
    parser.add_argument("--per-arm", type=int, default=48)
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--cache-dir", default=".cache/fastembed")
    args = parser.parse_args()
    sessions, bank = load_data(args.data, per_arm=args.per_arm)
    folds, holdout = make_split(sessions)
    if len(folds) < 80:
        raise ValueError("Too few development sessions; download the complete official dataset.")
    df, arrays, nconcept = prepare_item_features(sessions, bank, folds, args.model, args.cache_dir)
    results = {
        "data": {"loaded_sessions": len(sessions), "development_sessions": len(folds),
                 "holdout_unopened": len(holdout), "development_items": len(df),
                 "development_concepts": nconcept},
        "protocol": "Development-only grouped session cross-validation; public GRE subskill to generated lesson concept similarity; no human validation of mapping.",
        "experiments": {}
    }
    for c in (0.03, 0.3):
        predictions = cross_validate(df, arrays, c)
        results["experiments"][str(c)] = {
            "metrics": score(df, predictions), "paired_session_bootstrap": paired_bootstrap(df, predictions)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2), encoding="utf8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
