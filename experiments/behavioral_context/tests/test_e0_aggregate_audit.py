import csv
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from e0_aggregate_audit import audit


def fixture(root, n=4):
    root.mkdir(parents=True)
    (root / "studentbench_overall_parameters.json").write_text("{}")
    for k in range(n):
        section = "gre_quant" if k % 2 == 0 else "gre_verbal"
        base = (root / "1_main_leaderboard_data" / section /
                "ai_arm_test_fixture" / f"task_id_{k:04d}")
        student = base / "student_data"
        tutor = base / "ai_tutoring_data"
        student.mkdir(parents=True)
        tutor.mkdir()
        profile = {
            "instrument_id": section, "tutoring_arm": "ai",
            "pretest_score_points": 10, "posttest_score_points": 12,
            "score_lift_points": 2, "student_messages_sent_to_tutor": 1,
            "ai_tutor_messages_sent_to_student": 1,
        }
        (student / "student.json").write_text(json.dumps(profile))
        for name, score in (("pretest_responses.csv", 10),
                            ("posttest_responses.csv", 12)):
            with (student / name).open("w", newline="") as f:
                wr = csv.DictWriter(f, fieldnames=["question_id", "is_correct"])
                wr.writeheader()
                for i in range(27):
                    wr.writerow({"question_id": f"q{i}", "is_correct": int(i < score)})
        path = tutor / "student_ai_tutor_interaction_trajectory.csv"
        with path.open("w", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=[
                "trajectory_position", "timestamp_elapsed_seconds",
                "event_type", "content"])
            wr.writeheader()
            wr.writerow({"trajectory_position": 1, "timestamp_elapsed_seconds": 12,
                         "event_type": "ai_tutor_message", "content": "FICTIONAL AI"})
            wr.writerow({"trajectory_position": 2, "timestamp_elapsed_seconds": 11,
                         "event_type": "student_message", "content": "FICTIONAL student"})
    return root


def test_aggregate_counts_only(tmp_path):
    data = fixture(tmp_path / "fake_data")
    result = audit(data, tmp_path / "qa.json", expect=None)
    assert result["status"] == "PASS_AUDIT_ONLY"
    assert result["totals"]["sessions"] == 4
    assert result["totals"]["student_messages"] == 4
    assert result["totals"]["timestamp_inversions"] == 4
    assert result["snapshot_revision_verified"] is False
    assert "FICTIONAL student" not in (tmp_path / "qa.json").read_text()


def test_strict_profile_count_and_input_marker(tmp_path):
    data = fixture(tmp_path / "fake_data")
    with pytest.raises(RuntimeError, match="expected 2139"):
        audit(data, tmp_path / "qa.json")
    (data / "studentbench_overall_parameters.json").unlink()
    with pytest.raises(RuntimeError, match="marker missing"):
        audit(data, tmp_path / "qa.json", expect=None)
