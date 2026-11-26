#!/usr/bin/env python3
"""Extract causally available StudentBench student turns for local E1 annotation.

The produced turn-level CSV contains raw public dialogue. NEVER commit it;
store under ignored annotation_work/. No pre/post scores are emitted.
"""
from __future__ import annotations
import argparse
import csv
import json
from collections import Counter, deque
from pathlib import Path

def read_csv(p):
    with Path(p).open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def extract(root,out,history_turns=6,min_sessions=80):
    root,out=Path(root),Path(out)
    if not (root/"studentbench_overall_parameters.json").is_file():
        raise RuntimeError("E1 BLOCKED: official root marker missing")
    if history_turns < 1:
        raise ValueError("history_turns must be >= 1")
    profiles=sorted(root.glob(
        "1_main_leaderboard_data/gre_*/ai_arm_*/task_id_*/student_data/student.json"))
    if len(profiles) < min_sessions:
        raise RuntimeError(f"E1 BLOCKED: only {len(profiles)} real AI session profiles; require {min_sessions}")
    out.mkdir(parents=True,exist_ok=True)
    sessions_path=out/"sessions_E0_INTERNAL.csv"
    turns_path=out/"turns_E1_PRIVATE_UNLABELED.csv"
    fields=["session_id","turn_key","trajectory_position","current_utterance",
            "prior_dialogue_json","last_ai_response","concept_id",
            "practice_problem_id","task_context_text"]
    counters=Counter()
    with sessions_path.open("w",encoding="utf-8",newline="") as fs, \
         turns_path.open("w",encoding="utf-8",newline="") as ft:
        sessions=csv.DictWriter(fs,fieldnames=["session_id","section","audit_pass"])
        turns=csv.DictWriter(ft,fieldnames=fields)
        sessions.writeheader();turns.writeheader()
        seen_sessions=set()
        for p in profiles:
            profile=json.loads(p.read_text(encoding="utf-8"))
            sid=profile.get("student_id")
            section=profile.get("instrument_id")
            if not sid or sid in seen_sessions or section not in ("gre_quant","gre_verbal"):
                raise RuntimeError("E1 BLOCKED: invalid or duplicated source session identifiers")
            seen_sessions.add(sid)
            base=p.parent.parent
            traj=base/"ai_tutoring_data/student_ai_tutor_interaction_trajectory.csv"
            counters["sessions_seen"]+=1
            if profile.get("tutoring_arm")!="ai" or not traj.is_file():
                sessions.writerow({"session_id":sid,"section":section,"audit_pass":False})
                counters["session_fail"]+=1
                continue
            events=read_csv(traj)
            positions=[int(e["trajectory_position"]) for e in events]
            if positions!=list(range(1,len(events)+1)):
                sessions.writerow({"session_id":sid,"section":section,"audit_pass":False})
                counters["position_failure"]+=1
                continue
            student=[e for e in events if e["event_type"]=="student_message" and e.get("content","").strip()]
            ai=[e for e in events if e["event_type"]=="ai_tutor_message" and e.get("content","").strip()]
            if (len(student)!=profile.get("student_messages_sent_to_tutor")
                or len(ai)!=profile.get("ai_tutor_messages_sent_to_student")):
                sessions.writerow({"session_id":sid,"section":section,"audit_pass":False})
                counters["message_count_failure"]+=1
                continue
            stop=profile.get("posttest_started_elapsed_seconds")
            if stop is None:
                sessions.writerow({"session_id":sid,"section":section,"audit_pass":False})
                counters["missing_posttest_start"]+=1
                continue
            stop=float(stop)
            # A posttest-timed *suffix* appearing strictly after the last
            # student utterance cannot enter any pre-existing student context.
            # Do not assume timestamps are monotonic: censor by the earliest
            # boundary-crossing trajectory position, not by timestamp sort.
            first_cross=next((int(e["trajectory_position"]) for e in events
                if e.get("timestamp_elapsed_seconds","")!=""
                and float(e["timestamp_elapsed_seconds"])>=stop),None)
            last_student_pos=max((int(e["trajectory_position"]) for e in student),default=0)
            if first_cross is not None and first_cross <= last_student_pos:
                sessions.writerow({"session_id":sid,"section":section,"audit_pass":False})
                counters["posttest_leakage_failure"]+=1
                counters["posttest_boundary_ambiguous_sessions"]+=1
                continue
            if first_cross is not None:
                # Retain only the strictly pre-crossing event prefix.
                # Source student/AI event counts were validated on the full
                # original trajectory above; the suffix is intentionally
                # excluded from labeling input and future context.
                counters["safe_posttest_suffix_sessions"]+=1
                counters["suffix_events_discarded"]+=len(events)-first_cross+1
                counters["student_turns_recovered_from_suffix_sessions"]+=len(student)
                events=events[:first_cross-1]
            sessions.writerow({"session_id":sid,"section":section,"audit_pass":True})
            counters["sessions_pass"]+=1
            history=deque(maxlen=history_turns)
            task_lookup={}
            for e in events:
                ty=e["event_type"]
                text=e.get("content","").strip()
                pos=int(e["trajectory_position"])
                pid=e.get("practice_problem_id","")
                if ty=="practice_problem_shown" and pid and text:
                    task_lookup[pid]=(pos,text)
                if ty=="student_message" and text:
                    past=list(history)
                    recent_ai=next((x["content"] for x in reversed(past)
                                    if x["role"]=="ai_tutor"),"")
                    problem=task_lookup.get(pid)
                    # Task text is only available if it was shown earlier.
                    task_text=problem[1] if problem and problem[0]<pos else ""
                    turns.writerow({
                        "session_id":sid,
                        "turn_key":f"{sid}|{pos}",
                        "trajectory_position":pos,
                        "current_utterance":text,
                        "prior_dialogue_json":json.dumps(past,ensure_ascii=False),
                        "last_ai_response":recent_ai,
                        "concept_id":e.get("concept_id",""),
                        "practice_problem_id":pid,
                        "task_context_text":task_text,
                    })
                    counters["student_turns_written"]+=1
                if ty in ("student_message","ai_tutor_message") and text:
                    history.append({"role":"student" if ty=="student_message" else "ai_tutor",
                                    "content":text,"trajectory_position":pos})
    # Aggregate-only summary. Actual rows must remain in private ignored directory.
    summary={"status":"EXTRACTED_UNLABELED","source_sessions":dict(counters),
             "history_turns":history_turns,
             "outcome_fields_in_turns":False,
             "integrity_verified_against_official_snapshot":False,
             "warning":"Source CSVs include raw student text; do not publish or commit."}
    (out/"E1_extraction_aggregate.json").write_text(
        json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data",required=True)
    ap.add_argument("--out",required=True)
    ap.add_argument("--history-turns",type=int,default=6)
    ap.add_argument("--min-sessions",type=int,default=80)
    args=ap.parse_args()
    print(json.dumps(extract(args.data,args.out,args.history_turns,args.min_sessions),indent=2))

if __name__=="__main__":
    main()
