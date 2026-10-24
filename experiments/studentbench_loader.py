"""Load public StudentBench GRE Quant sessions for diagnostic experiments.

This loader reads an *already downloaded* public dataset from disk and never
uploads raw tutoring dialogue to GitHub. It does not process heldout outcomes
other than loading records; experimental scripts must split sessions before fitting.
"""
from pathlib import Path
import csv
import json
import random


def _csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_sessions(root, per_tutor=62):
    root = Path(root)
    base = root / "1_main_leaderboard_data" / "gre_quant"
    if not base.exists():
        raise FileNotFoundError(f"Missing GRE Quant data directory: {base}")
    if per_tutor is not None and per_tutor < 1:
        raise ValueError("per_tutor must be >= 1 or None")

    sessions = []
    for arm in sorted(base.glob("ai_arm_*")):
        taskdirs = sorted(arm.glob("task_id_*"))
        # Same algorithm as remote 2026-10-24 semantic pilot.
        relative = "1_main_leaderboard_data/gre_quant/" + arm.name
        random.Random("semantic:" + relative).shuffle(taskdirs)
        chosen = taskdirs if per_tutor is None else taskdirs[:per_tutor]
        for task in chosen:
            profile_path = task / "student_data" / "student.json"
            pre_path = task / "student_data" / "pretest_responses.csv"
            post_path = task / "student_data" / "posttest_responses.csv"
            traj_path = task / "ai_tutoring_data" / "student_ai_tutor_interaction_trajectory.csv"
            if not all(p.exists() for p in (profile_path, pre_path, post_path, traj_path)):
                continue
            try:
                profile = json.loads(profile_path.read_text(encoding="utf-8"))
                pre, post, events = _csv(pre_path), _csv(post_path), _csv(traj_path)
                events.sort(key=lambda e: int(e["trajectory_position"]))
                student_text = " ".join(e["content"] for e in events
                                        if e["event_type"] == "student_message" and e["content"].strip())[:10000]
                tutor_text = " ".join(e["content"] for e in events
                                      if e["event_type"] == "ai_tutor_message" and e["content"].strip())[:12000]
                symbols = []
                for e in events:
                    typ = e["event_type"]
                    if typ == "student_message":
                        symbols.append("S")
                    elif typ == "ai_tutor_message":
                        symbols.append("A")
                    elif typ == "practice_problem_shown":
                        symbols.append("P")
                    elif typ == "practice_answer_submitted":
                        correctness = e["is_correct"].strip().lower()
                        symbols.append("C" if correctness in ("true", "1")
                                       else "W" if correctness in ("false", "0") else "U")
                sessions.append({
                    "profile": profile, "pre": pre, "post": post,
                    "student_text": student_text, "tutor_text": tutor_text,
                    "events": symbols,
                })
            except (OSError, ValueError, KeyError):
                continue
    return sessions


def load_question_bank(root):
    path = Path(root) / "question_bank_quant.csv"
    return {r["question_id"]: r for r in _csv(path)}
