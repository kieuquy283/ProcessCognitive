"""Synthetic fixtures only; no real participant text in tests."""
import csv
import json
import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from extract_e1_candidates import extract

def make_fixture(tmp_path):
    root=tmp_path/"dataset"
    root.mkdir()
    (root/"studentbench_overall_parameters.json").write_text("{}")
    base=root/"1_main_leaderboard_data"/"gre_quant"/"ai_arm_FAKE"/"task_id_0001"
    (base/"student_data").mkdir(parents=True)
    (base/"ai_tutoring_data").mkdir(parents=True)
    profile={
        "student_id":"FICTIONAL","instrument_id":"gre_quant","tutoring_arm":"ai",
        "posttest_started_elapsed_seconds":50,
        "pretest_score_points":10,"posttest_score_points":13,
        "student_messages_sent_to_tutor":3,"ai_tutor_messages_sent_to_student":2
    }
    (base/"student_data"/"student.json").write_text(json.dumps(profile))
    e=[
        ("ai_tutor_message","FICTIONAL hello",""),
        ("student_message","why?","p1"),
        ("practice_problem_shown","FICTIONAL question text","p1"),
        ("student_message","how?","p1"),
        ("ai_tutor_message","FICTIONAL because","p1"),
        ("student_message","check please","p1"),
    ]
    with (base/"ai_tutoring_data"/"student_ai_tutor_interaction_trajectory.csv").open("w",newline="") as f:
        wr=csv.DictWriter(f,fieldnames=["trajectory_position","timestamp_elapsed_seconds",
                 "event_type","content","practice_problem_id","concept_id"])
        wr.writeheader()
        for i,(typ,text,pid) in enumerate(e,1):
            wr.writerow({"trajectory_position":i,"timestamp_elapsed_seconds":i,
                  "event_type":typ,"content":text,"practice_problem_id":pid,"concept_id":"c1"})
    return root

def test_causal_context_and_no_grade_fields(tmp_path):
    root=make_fixture(tmp_path)
    info=extract(root,tmp_path/"private",min_sessions=1)
    assert info["source_sessions"]["student_turns_written"]==3
    df=pd.read_csv(tmp_path/"private"/"turns_E1_PRIVATE_UNLABELED.csv",keep_default_na=False)
    assert len(df)==3 and df.turn_key.nunique()==3
    assert all("posttest" not in k and "pretest" not in k for k in df.columns)
    assert df.task_context_text.tolist()==["","FICTIONAL question text","FICTIONAL question text"]
    assert df.last_ai_response.tolist()==["FICTIONAL hello","FICTIONAL hello","FICTIONAL because"]
    assert all(all(x["trajectory_position"]<pos for x in json.loads(hist))
        for hist,pos in zip(df.prior_dialogue_json,df.trajectory_position))

def test_refuse_short_source_and_posttest_leak(tmp_path):
    root=make_fixture(tmp_path)
    with pytest.raises(RuntimeError,match="only 1"):
        extract(root,tmp_path/"fail",min_sessions=80)
    p=next(root.glob("**/student.json"))
    d=json.loads(p.read_text())
    d["posttest_started_elapsed_seconds"]=3
    p.write_text(json.dumps(d))
    x=extract(root,tmp_path/"blocked",min_sessions=1)
    assert x["source_sessions"]["posttest_leakage_failure"]==1
    assert x["source_sessions"].get("student_turns_written",0)==0
