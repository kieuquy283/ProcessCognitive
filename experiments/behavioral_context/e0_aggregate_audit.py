#!/usr/bin/env python3
"""Aggregate-only audit of official StudentBench AI sessions.

No participant-level scores, identifiers or conversation text are written.
The official pinned dataset version must be verified separately.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
from collections import Counter

PIN = "304c8d63c726e72b60510bba3a44454fc0726721"


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def item_score(records):
    if len(records) != 27 or len({x["question_id"] for x in records}) != 27:
        raise ValueError("assessment_malformed")
    answers = [str(x["is_correct"]).lower() for x in records]
    if not set(answers) <= {"0", "1", "true", "false"}:
        raise ValueError("invalid_correctness")
    return sum(x in {"1", "true"} for x in answers)


def audit(root, out, expect=2139):
    root = Path(root)
    if not (root / "studentbench_overall_parameters.json").exists():
        raise RuntimeError("E0 BLOCKED: official dataset root marker missing")
    profiles = sorted(root.glob(
        "1_main_leaderboard_data/gre_*/ai_arm_*/task_id_*/student_data/student.json"))
    if not profiles:
        raise RuntimeError("E0 BLOCKED: zero real AI profiles")
    if expect is not None and len(profiles) != expect:
        raise RuntimeError(
            f"E0 BLOCKED: expected {expect} AI profiles; found {len(profiles)}")
    summary = Counter()
    fail = Counter()
    per_section = Counter()
    for path in profiles:
        summary["sessions"] += 1
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
            base = path.parent.parent
            pre = rows(path.parent / "pretest_responses.csv")
            post = rows(path.parent / "posttest_responses.csv")
            events = rows(base / "ai_tutoring_data" /
                          "student_ai_tutor_interaction_trajectory.csv")
            sec = str(obj.get("instrument_id", ""))
            per_section[sec] += 1
            if obj.get("tutoring_arm") != "ai":
                raise ValueError("unexpected_arm")
            if item_score(pre) != obj.get("pretest_score_points"):
                raise ValueError("pre_score_mismatch")
            if item_score(post) != obj.get("posttest_score_points"):
                raise ValueError("post_score_mismatch")
            if (obj["posttest_score_points"] -
                    obj["pretest_score_points"]) != obj.get("score_lift_points"):
                raise ValueError("gain_mismatch")
            positions = [int(x["trajectory_position"]) for x in events]
            if positions != list(range(1, len(events) + 1)):
                raise ValueError("sequence_position_mismatch")
            student = sum(x["event_type"] == "student_message" and
                          bool(x.get("content", "").strip()) for x in events)
            tutor = sum(x["event_type"] == "ai_tutor_message" and
                        bool(x.get("content", "").strip()) for x in events)
            if student != obj.get("student_messages_sent_to_tutor"):
                raise ValueError("student_message_mismatch")
            if tutor != obj.get("ai_tutor_messages_sent_to_student"):
                raise ValueError("ai_message_mismatch")
            times = [float(x["timestamp_elapsed_seconds"]) for x in events
                     if x.get("timestamp_elapsed_seconds")]
            inversions = sum(b < a for a, b in zip(times, times[1:]))
            summary["timestamp_inversions"] += inversions
            summary["sessions_with_timestamp_inversions"] += int(inversions > 0)
            summary["student_messages"] += student
            summary["ai_messages"] += tutor
            summary["events"] += len(events)
            summary["passed_sessions"] += 1
        except (ValueError, KeyError, TypeError, OSError, IndexError) as exc:
            fail[str(exc)[:80]] += 1
    result = {
        "phase": "E0",
        "dataset_revision_expected": PIN,
        "snapshot_revision_verified": False,
        "scope": "official local AI main cohort; aggregate counts only",
        "status": ("PASS_AUDIT_ONLY" if not fail and
                   summary["passed_sessions"] == len(profiles) else "FAIL"),
        "totals": dict(summary),
        "by_section": dict(per_section),
        "failure_reasons": dict(fail),
        "caution": "Dataset revision must be verified separately. The existence "
                   "of files does not prove matching release hashes.",
    }
    output = Path(out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--expect", type=int, default=2139)
    args = parser.parse_args()
    print(json.dumps(audit(args.data, args.out, args.expect), indent=2))


if __name__ == "__main__":
    main()
