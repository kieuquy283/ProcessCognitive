import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from e1_context_pilot import prepare_e1


def fake_inputs(tmp_path, n_sessions=40, turns_per_session=24):
    sessions, turns = [], []
    for i in range(n_sessions):
        section = "gre_quant" if i % 2 == 0 else "gre_verbal"
        sid = f"FICTIONAL_{section}_{i}"
        sessions.append({"session_id": sid, "section": section,
                         "audit_pass": True, "pre_score": 12, "post_score": 16})
        for j in range(turns_per_session):
            turns.append({
                "session_id": sid,
                "turn_key": f"{sid}|{j*3+2}",
                "trajectory_position": j*3+2,
                "current_utterance": "why?" if j % 2 == 0 else
                                     "please check my carefully written detailed solution to this question",
                "last_ai_response": "FICTIONAL previous tutor reply",
                "prior_dialogue_json": json.dumps([] if j == 0 else [
                    {"role": "ai_tutor", "content": "FICTIONAL",
                     "trajectory_position": j*3+1}]),
                "concept_id": "c1", "practice_problem_id": "p1",
            })
    a = tmp_path / "sessions.csv"
    b = tmp_path / "turns.csv"
    pd.DataFrame(sessions).to_csv(a, index=False)
    pd.DataFrame(turns).to_csv(b, index=False)
    return a, b


def test_deterministic_section_split_and_blinded_labels(tmp_path):
    s, t = fake_inputs(tmp_path)
    a = prepare_e1(s, t, tmp_path / "a")
    b = prepare_e1(s, t, tmp_path / "b")
    assert a["n_total"] == 280
    assert a["n_development"] == 200
    assert a["n_locked_holdout"] == 80
    assert a["selected_keys_sha256"] == b["selected_keys_sha256"]
    x = pd.read_csv(tmp_path / "a" / "e1_annotator_A_UNLABELED.csv",
                    keep_default_na=False)
    assert len(x) == 280 and x.turn_key.is_unique and set(x.label) == {""}
    assert "pre_score" not in x.columns and "post_score" not in x.columns
    dev = set(x.loc[x.split == "development", "session_id"])
    hold = set(x.loc[x.split == "locked_holdout", "session_id"])
    assert not dev & hold
    assert x.groupby(["section", "split"]).size().to_dict() == {
        ("gre_quant", "development"): 100,
        ("gre_quant", "locked_holdout"): 40,
        ("gre_verbal", "development"): 100,
        ("gre_verbal", "locked_holdout"): 40,
    }


def test_refuse_insufficient_real_turns(tmp_path):
    s, t = fake_inputs(tmp_path, 4, 24)
    with pytest.raises(RuntimeError, match="only 96 eligible turns"):
        prepare_e1(s, t, tmp_path / "out", min_sessions_per_section=2)


def test_refuse_outcome_leakage_and_future_history(tmp_path):
    s, t = fake_inputs(tmp_path)
    df = pd.read_csv(t)
    df["posttest_score_points"] = 21
    df.to_csv(t, index=False)
    with pytest.raises(RuntimeError, match="score/outcome"):
        prepare_e1(s, t, tmp_path / "out")
    df = df.drop(columns=["posttest_score_points"])
    df.loc[0, "prior_dialogue_json"] = json.dumps([
        {"role": "ai_tutor", "content": "FICTIONAL future",
         "trajectory_position": 999}])
    df.to_csv(t, index=False)
    with pytest.raises(RuntimeError, match="future context"):
        prepare_e1(s, t, tmp_path / "out")
