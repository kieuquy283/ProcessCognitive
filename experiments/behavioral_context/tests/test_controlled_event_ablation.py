"""Synthetic-only tests: never report fictional outcomes as StudentBench results."""
import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from controlled_event_ablation import (
    SYMBOLS, BAGS, EDGES, event_features, deterministic_shuffle,
    assemble, assign_original_e8_folds, score_development,
)

def fake_sessions(n=120, temporal=False):
    rng=np.random.default_rng(123)
    out=[]
    for i in range(n):
        typ=int(rng.integers(0,2))
        seq=([("S" if j%2==0 else "A") for j in range(120)]
             if temporal and typ else
             (["S"]*60+["A"]*60 if temporal else
              rng.choice(SYMBOLS,size=120).tolist()))
        profile={
            "student_id":f"FICTIONAL_{i}",
            "ai_model_preset_id":f"FICTIONAL_TUTOR_{i%2}",
            "assessment_form_order":"QP" if i%2 else "PQ",
            "pretest_score_points":10+i%7,"pretest_irt_theta":0.0,
            "practice_problems_answered_count":8,
            "practice_problems_final_correct_count":4,
            "practice_answer_submissions_count":10,
            "student_messages_sent_to_tutor":seq.count("S"),
            "ai_tutor_messages_sent_to_student":seq.count("A"),
            "posttest_score_points":float(9+9*typ if temporal else 13+rng.normal(0,2)),
        }
        out.append({"profile":profile,"events":seq})
    return out

def test_features_keep_counts_invariant_when_order_is_shuffled():
    seq=["S","A","S","A","C","W"]
    a=event_features(seq)
    b=event_features(deterministic_shuffle(seq,"FICTIONAL"))
    assert all(a[k]==b[k] for k in BAGS)
    assert a["edge_S_A"] == pytest.approx(2/5)
    assert sum(a[k] for k in EDGES)==pytest.approx(1)

def test_source_holdout_never_enters_training_table():
    sessions=fake_sessions()
    folds,hold=assign_original_e8_folds(sessions)
    assert not set(folds)&hold
    table=assemble(sessions,sorted(folds))
    assert len(table)==len(folds)
    assert "posttest_score_points" not in table
    assert "student_id" not in table
    assert len(table)>=80

def test_nested_model_synthetic_integration():
    sessions=fake_sessions(160,temporal=True)
    folds,_=assign_original_e8_folds(sessions)
    table=assemble(sessions,sorted(folds))
    r=score_development(table,[folds[i] for i in sorted(folds)],n_boot=80)
    assert r["models"]["M2_static_bag_ordered"]["MAE_score_points"] < (
        r["models"]["M1_static_bag"]["MAE_score_points"])
    assert set(r["paired_MAE_contrasts"])=={
        "bag_vs_static","order_vs_bag","order_vs_shuffle"}

def test_small_samples_blocked():
    sessions=fake_sessions(20)
    folds,_=assign_original_e8_folds(sessions)
    with pytest.raises(ValueError,match=">=80"):
        score_development(assemble(sessions,sorted(folds)),
                          [folds[i] for i in sorted(folds)],n_boot=80)
