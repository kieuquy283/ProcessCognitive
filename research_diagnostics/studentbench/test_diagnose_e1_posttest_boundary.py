import csv,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from diagnose_e1_posttest_boundary import diagnose

def fixture(root):
    root.mkdir()
    patterns=[
        [("student_message", 10),("ai_tutor_message",20)], # safe
        [("student_message", 10),("ai_tutor_message",52)], # nonstudent after
        [("student_message", 10),("ai_tutor_message",52),("student_message",53)], # student after
        [("ai_tutor_message",60),("student_message",40)], # clock recrossing
    ]
    for i,events in enumerate(patterns):
        base=root/"1_main_leaderboard_data"/("gre_quant" if i<2 else "gre_verbal")/"ai_arm_FIXTURE"/f"task_id_{i:04d}"
        student=base/"student_data";student.mkdir(parents=True)
        tutor=base/"ai_tutoring_data";tutor.mkdir()
        (student/"student.json").write_text(json.dumps({
          "instrument_id":"gre_quant" if i<2 else "gre_verbal",
          "posttest_started_elapsed_seconds":50}))
        with (tutor/"student_ai_tutor_interaction_trajectory.csv").open("w",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=[
                "trajectory_position","event_type","timestamp_elapsed_seconds","content"])
            writer.writeheader()
            for pos,(kind,time) in enumerate(events,1):
                writer.writerow({"trajectory_position":pos,"event_type":kind,
                                 "timestamp_elapsed_seconds":time,
                                 "content":"FICTIONAL PRIVATE TEXT"})
    return root

def test_classify_old_exclusion_and_reversals_without_text(tmp_path):
    result=diagnose(fixture(tmp_path/"synthetic"),expect=4)
    t=result["totals"]
    assert t["sessions_old_E1_excludes"]==3
    assert t["sessions_with_no_beyond"]==1
    assert t["excluded_sessions_with_student_after"]==1
    assert t["excluded_sessions_with_only_nonstudent_after"]==2
    assert t["excluded_sessions_with_timestamp_recrossing"]==1
    assert t["excluded_sessions_first_cross_after_last_student"]==1
    assert t["student_messages_before_boundary_in_excluded_sessions"]==3
    assert "FICTIONAL" not in json.dumps(result)

def test_reject_incomplete_source(tmp_path):
    root=fixture(tmp_path/"synthetic")
    try: diagnose(root,expect=2139)
    except RuntimeError as error:
        assert "expected 2139" in str(error)
    else:
        assert False
