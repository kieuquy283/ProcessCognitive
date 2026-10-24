#!/usr/bin/env python3
"""Session-level event sequence: neural baseline vs event bag vs GRU vs shuffle.

Exploratory 4-fold grouped evaluation. The holdout stays unopened.
Requires official locally downloaded StudentBench data. Only aggregate metrics exported.
"""
import argparse
import collections
import copy
import json
import random
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler
from torch import nn
from torch.nn.utils.rnn import pack_padded_sequence

from studentbench_loader import load_sessions
from semantic_baseline import assign_folds

SYMBOLS = ["S", "A", "P", "C", "W", "U"]
SEED = 20261024


class Predictor(nn.Module):
    def __init__(self, static_width, kind):
        super().__init__()
        self.kind = kind
        if kind == "gru":
            self.embed = nn.Embedding(7, 8, padding_idx=0)
            self.gru = nn.GRU(8, 16, batch_first=True)
            feature_width = static_width + 16
        elif kind == "bag":
            feature_width = static_width + 6
        else:
            feature_width = static_width
        self.head = nn.Sequential(nn.Linear(feature_width, 24), nn.ReLU(),
                                  nn.Dropout(0.2), nn.Linear(24, 1))

    def forward(self, static, counts, events, lengths):
        if self.kind == "gru":
            packed = pack_padded_sequence(self.embed(events), lengths.cpu(),
                                          batch_first=True, enforce_sorted=False)
            _, state = self.gru(packed)
            x = torch.cat([static, state[-1]], dim=-1)
        elif self.kind == "bag":
            x = torch.cat([static, counts], dim=-1)
        else:
            x = static
        return self.head(x).squeeze(-1).sigmoid()


def make_features(sessions, dev_ids):
    tutors = sorted({s["profile"]["ai_model_preset_id"] for s in sessions})
    matrix, counts, sequences, shuffled, targets = [], [], [], [], []
    for i in dev_ids:
        p = sessions[i]["profile"]
        feature = [float(p["pretest_score_points"]), float(p.get("pretest_irt_theta") or 0),
                   float(p["practice_problems_answered_count"]),
                   float(p["practice_problems_final_correct_count"]),
                   float(p["practice_answer_submissions_count"]),
                   float(p["student_messages_sent_to_tutor"]),
                   float(p["ai_tutor_messages_sent_to_student"])]
        feature.extend(float(p["ai_model_preset_id"] == t) for t in tutors)
        feature.append(float(p["assessment_form_order"] == "QP"))
        symbols = list(sessions[i]["events"])
        cnt = np.array([symbols.count(x) for x in SYMBOLS], dtype=np.float32)
        cnt /= max(1, len(symbols))
        if len(symbols) > 256:
            symbols = symbols[:128] + symbols[-128:]
        ints = [SYMBOLS.index(x) + 1 for x in symbols]
        if not ints:
            ints = [1]
        swapped = ints.copy()
        random.Random("shuffle-" + p["student_id"]).shuffle(swapped)
        matrix.append(feature)
        counts.append(cnt)
        sequences.append(ints)
        shuffled.append(swapped)
        targets.append(float(p["posttest_score_points"]) / 27.0)

    def pad(all_sequences):
        arr = np.zeros((len(all_sequences), 256), dtype=np.int64)
        lengths = np.zeros(len(all_sequences), dtype=np.int64)
        for j, seq in enumerate(all_sequences):
            arr[j, :len(seq)] = seq
            lengths[j] = len(seq)
        return torch.tensor(arr), torch.tensor(lengths)

    return (np.asarray(matrix, dtype=np.float32),
            torch.tensor(np.asarray(counts, dtype=np.float32)),
            pad(sequences), pad(shuffled),
            torch.tensor(np.asarray(targets, dtype=np.float32)))


def fit_fold(features, folds, fold, kind, permuted=False):
    X, bags, normal, shuffled, y = features
    events, lengths = shuffled if permuted else normal
    train = np.flatnonzero(folds != fold)
    test = np.flatnonzero(folds == fold)
    rng = np.random.default_rng(SEED + int(fold))
    train = rng.permutation(train)
    valid_count = max(30, len(train) // 7)
    validate, train = train[:valid_count], train[valid_count:]
    scaler = StandardScaler().fit(X[train])
    static = torch.tensor(scaler.transform(X).astype(np.float32))
    torch.manual_seed(SEED + int(fold) +
                      (10 if kind == "gru" else 20 if kind == "bag" else 30))
    predictor = Predictor(X.shape[1], kind)
    optimizer = torch.optim.AdamW(predictor.parameters(), lr=0.003, weight_decay=0.03)
    best_loss, best_weights, patience = float("inf"), None, 0
    for epoch in range(90):
        predictor.train()
        for batch in np.array_split(rng.permutation(train), max(1, (len(train) + 31) // 32)):
            optimizer.zero_grad()
            prediction = predictor(static[batch], bags[batch], events[batch], lengths[batch])
            loss = ((prediction - y[batch]) ** 2).mean()
            loss.backward()
            nn.utils.clip_grad_norm_(predictor.parameters(), 2.0)
            optimizer.step()
        predictor.eval()
        with torch.no_grad():
            guess = predictor(static[validate], bags[validate],
                              events[validate], lengths[validate])
            valid_loss = float(((guess - y[validate]) ** 2).mean())
        if valid_loss < best_loss - 0.00002:
            best_loss = valid_loss
            best_weights = copy.deepcopy(predictor.state_dict())
            patience = 0
        else:
            patience += 1
        if epoch >= 12 and patience >= 12:
            break
    predictor.load_state_dict(best_weights)
    predictor.eval()
    with torch.no_grad():
        output = predictor(static[test], bags[test], events[test], lengths[test])
    return test, output.numpy()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("results/event_gru.json"))
    parser.add_argument("--per-tutor", type=int, default=62)
    args = parser.parse_args()
    torch.set_num_threads(2)
    torch.manual_seed(SEED)
    sessions = load_sessions(args.data, per_tutor=args.per_tutor)
    fold_map, heldout = assign_folds(sessions)
    dev_ids = sorted(fold_map)
    if len(dev_ids) < 80:
        raise ValueError("Too few development sessions for fourfold training")
    fold_ids = np.array([fold_map[i] for i in dev_ids])
    data = make_features(sessions, dev_ids)
    outcome = data[-1].numpy()
    output = {}
    for name in ("static", "bag", "gru", "gru_shuffled"):
        predicted = np.empty(len(dev_ids), dtype=np.float32)
        for fold in sorted(set(fold_ids)):
            indices, values = fit_fold(data, fold_ids, fold,
                                       "gru" if name == "gru_shuffled" else name,
                                       name == "gru_shuffled")
            predicted[indices] = values
        output[name] = predicted

    rng = np.random.default_rng(20)
    differences = {}
    for a, b in [("static", "bag"), ("bag", "gru"),
                 ("gru_shuffled", "gru"), ("static", "gru")]:
        diff = (outcome - output[a])**2 - (outcome - output[b])**2
        sims = rng.choice(diff, size=(2000, len(diff)), replace=True).mean(axis=1)
        differences[f"{a}_to_{b}"] = {
            "delta_mse_fraction": float(diff.mean()),
            "bootstrap_ci95": np.quantile(sims, [.025, .975]).tolist()}
    metrics = {
        name: {"rmse_points": float(27 * np.sqrt(mean_squared_error(outcome, v))),
               "mae_points": float(27 * mean_absolute_error(outcome, v))}
        for name, v in output.items()
    }
    result = {"n_retrieved": len(sessions), "n_dev": len(dev_ids),
              "n_holdout_unopened": len(heldout), "target": "posttest total /27",
              "sequence": "6 event symbols, first and last 128 for >256 events",
              "models": metrics, "paired_bootstrap": differences,
              "note": "Exploratory development CV only; no heldout claims."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
