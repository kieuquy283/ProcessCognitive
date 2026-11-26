"""Synthetic only: validate lexical features and the nested control."""
import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lexical_proxy_ablation import (
  lexical_features,build_frame,evaluate,FEATURES
)
from controlled_event_ablation import assign_original_e8_folds
from test_controlled_event_ablation import fake_sessions

def test_lexical_feature_names_and_signals():
    a=lexical_features("Why? Please check my answer because I think it is wrong.")
    assert set(a)==set(FEATURES)
    assert a["lex_question_mark_per_100"]>0
    assert a["lex_why_how_per_100"]>0
    assert a["lex_verify_per_100"]>0
    assert a["lex_reason_per_100"]>0
    assert a["lex_answer_per_100"]>0
    assert set(lexical_features("").values())=={0.0}

def test_lexical_control_uses_same_rows_and_folds():
    sessions=fake_sessions(n=160,temporal=False)
    for i,s in enumerate(sessions):
        s["student_text"]=(
          "why explain why why why how how" if i%2 else
          "the answer is this because I think so")
    folds,hold=assign_original_e8_folds(sessions)
    dev_ids=sorted(folds)
    frame=build_frame(sessions,dev_ids)
    assert len(frame)==len(dev_ids)
    assert frame[list(FEATURES)].notna().all().all()
    assert len(hold)+len(dev_ids)==len(sessions)
    assert "posttest_score_points" not in frame
    result=evaluate(frame,[folds[i] for i in dev_ids],n_boot=32)
    assert result["n_development_sessions"]==len(dev_ids)
    assert set(result["metrics"])=={
        "B0_event_bag","B1_event_bag_plus_lexical",
        "B2_event_bag_plus_shuffled_lexical"}

def test_reject_small_development_and_outcome_leakage():
    sessions=fake_sessions(n=20)
    for s in sessions:s["student_text"]="hello"
    folds,_=assign_original_e8_folds(sessions)
    ids=sorted(folds)
    frame=build_frame(sessions,ids)
    with pytest.raises(ValueError,match="insufficient"):
        evaluate(frame,[folds[i] for i in ids],n_boot=10)
    frame["score_lift_points"]=8
    with pytest.raises(ValueError,match="insufficient"):
        evaluate(frame,[folds[i] for i in ids],n_boot=10)
