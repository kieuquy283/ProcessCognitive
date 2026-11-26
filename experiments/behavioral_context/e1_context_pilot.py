#!/usr/bin/env python3
"""Prepare blinded, score-free E1 behavioral annotation candidates.

Requires E0 turn-level outputs from a local official StudentBench snapshot.
Generated sheets contain released student text and MUST stay in ignored
annotation_work/. This script does not annotate or validate a codebook.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
import numpy as np
import pandas as pd

SENSITIVE = re.compile(
    r"(pretest|posttest|pre_score|post_score|gain|lift|correctness|grade|outcome|is_correct)",
    re.I)
REQUIRED = {
    "session_id", "turn_key", "trajectory_position", "current_utterance",
    "prior_dialogue_json", "last_ai_response"
}


def prepare_e1(sessions_path, turns_path, out_dir, seed=20261126,
               n_total=280, n_holdout=80, min_sessions_per_section=40,
               max_turns_per_session=5):
    if n_total != 280 or n_holdout != 80:
        raise ValueError("Frozen E1 design requires 280 turns: 200 development + 80 locked holdout")
    sessions = pd.read_csv(sessions_path, keep_default_na=False)
    turns = pd.read_csv(turns_path, keep_default_na=False)
    if not REQUIRED.issubset(turns.columns):
        raise RuntimeError(
            f"E1 BLOCKED: missing columns {sorted(REQUIRED - set(turns.columns))}")
    if any(SENSITIVE.search(c) for c in turns.columns):
        raise RuntimeError("E1 BLOCKED: score/outcome column in annotation input")
    if turns.empty or turns.turn_key.duplicated().any():
        raise RuntimeError("E1 BLOCKED: empty or duplicate turn keys")
    if not {"session_id", "section", "audit_pass"}.issubset(sessions.columns):
        raise RuntimeError("E1 BLOCKED: invalid E0 session audit")
    if sessions.session_id.duplicated().any():
        raise RuntimeError("E1 BLOCKED: duplicated session keys")
    valid = sessions[
        sessions.audit_pass.astype(str).str.lower() == "true"
    ][["session_id", "section"]]
    merged = turns.merge(valid, on="session_id",
                         how="inner", validate="many_to_one")
    if merged.empty:
        raise RuntimeError("E1 BLOCKED: zero eligible real turns")
    merged = merged.loc[
        merged.current_utterance.astype(str).str.strip().ne("")
    ].copy()
    merged["short"] = merged.current_utterance.astype(str).str.split().map(len).le(7)
    for record in merged.itertuples(index=False):
        try:
            history = json.loads(record.prior_dialogue_json)
        except (TypeError, json.JSONDecodeError):
            raise RuntimeError("E1 BLOCKED: invalid JSON history") from None
        if not isinstance(history, list):
            raise RuntimeError("E1 BLOCKED: history must be a list")
        if any(int(x["trajectory_position"]) >= int(record.trajectory_position)
               for x in history):
            raise RuntimeError("E1 BLOCKED: future context leaked into annotation")
        last_ai = next((x.get("content","") for x in reversed(history)
                        if x.get("role") == "ai_tutor"), "")
        if str(record.last_ai_response) != str(last_ai):
            raise RuntimeError("E1 BLOCKED: last_ai_response inconsistent with prior history")
    if len(merged) < n_total:
        raise RuntimeError(
            f"E1 BLOCKED: only {len(merged)} eligible turns; require {n_total}")
    rng = np.random.default_rng(seed)
    items = []
    strata = []
    for section in ("gre_quant", "gre_verbal"):
        subset = merged[merged.section == section]
        ids = sorted(subset.session_id.unique())
        if len(ids) < min_sessions_per_section:
            raise RuntimeError(
                f"E1 BLOCKED: {section} has only {len(ids)} sessions; "
                f"require {min_sessions_per_section}")
        rng.shuffle(ids)
        hold = set(ids[:max(2, round(len(ids) * .30))])
        dev = set(ids) - hold
        for split, keys, wanted in (
            ("development", dev, 100),
            ("locked_holdout", hold, 40),
        ):
            pool = subset[subset.session_id.isin(keys)]
            if len(pool) < wanted:
                raise RuntimeError(
                    f"E1 BLOCKED: {section}/{split} only {len(pool)} turns; "
                    f"need {wanted}")
            # Limit correlated turns per session before length-stratified selection.
            capped=[]
            for sid, group in pool.groupby('session_id', sort=True):
                n_take=min(max_turns_per_session,len(group))
                indices=rng.choice(len(group),n_take,replace=False)
                capped.append(group.iloc[indices])
            pool=pd.concat(capped,ignore_index=True)
            short = pool[pool.short]
            long = pool[~pool.short]
            n_short = min(len(short), wanted // 2)
            n_long = min(len(long), wanted - n_short)
            if n_short + n_long < wanted:
                n_short = min(len(short), wanted - n_long)
            if n_short + n_long < wanted:
                raise RuntimeError("E1 BLOCKED: session-cap/length-stratified quota impossible")
            chosen = pd.concat([
                short.iloc[rng.choice(len(short), n_short, replace=False)],
                long.iloc[rng.choice(len(long), n_long, replace=False)],
            ]).copy()
            chosen["split"] = split
            min_selected=20 if split=="development" else 8
            if chosen.session_id.nunique() < min_selected:
                raise RuntimeError("E1 BLOCKED: too few independent sessions after sampling")
            items.append(chosen)
            strata.append({
                "section": section, "split": split,
                "n_turns": len(chosen),
                "n_sessions": int(chosen.session_id.nunique()),
                "n_short": int(chosen.short.sum()),
            })
    selected = pd.concat(items, ignore_index=True)
    if selected.turn_key.nunique() != n_total:
        raise RuntimeError("E1 BLOCKED: duplicate sampling after session split")
    dev_ids = set(selected.loc[
        selected.split == "development", "session_id"])
    hold_ids = set(selected.loc[
        selected.split == "locked_holdout", "session_id"])
    if dev_ids & hold_ids:
        raise RuntimeError(
            "E1 BLOCKED: session appears in development and holdout")
    selected = selected.iloc[
        rng.permutation(len(selected))
    ].copy().reset_index(drop=True)
    selected["pilot_id"] = [
        "E1-%03d" % (i + 1) for i in range(len(selected))]
    selected["label"] = ""
    selected["rationale"] = ""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    selected[["pilot_id","turn_key","session_id","split"]].to_csv(
        out / "E1_split_manifest_PRIVATE.csv",index=False)
    columns = [
        "pilot_id", "turn_key", "session_id", "trajectory_position",
        "section", "current_utterance", "last_ai_response",
        "prior_dialogue_json", "concept_id", "practice_problem_id",
        "label", "rationale"
    ]
    columns = [c for c in columns if c in selected]
    for who in ("A", "B"):
        sheet=selected[columns].copy()
        sheet["annotator_id"]=who
        sheet.to_csv(out / f"e1_annotator_{who}_UNLABELED.csv", index=False)
    digest = hashlib.sha256(
        "\n".join(sorted(selected.turn_key)).encode()
    ).hexdigest()
    report = {
        "experiment": "E1_context_pilot",
        "status": "SAMPLE_PREPARED_NOT_ANNOTATED",
        "n_total": len(selected),
        "n_development": int(
            (selected.split == "development").sum()),
        "n_locked_holdout": int(
            (selected.split == "locked_holdout").sum()),
        "selected_keys_sha256": digest,
        "seed": seed, "max_turns_per_session":max_turns_per_session, "strata": strata,
        "warning": "Length-enriched pilot; not a population-prevalence "
                   "estimator. Human annotations are not supplied.",
    }
    (out / "E1_sampling_summary.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sessions", required=True)
    parser.add_argument("--turns", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--seed", type=int, default=20261126)
    args = parser.parse_args()
    print(json.dumps(prepare_e1(
        args.sessions, args.turns, args.out, args.seed), indent=2))


if __name__ == "__main__":
    main()
