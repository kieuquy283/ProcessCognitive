#!/usr/bin/env python3
"""Diagnose E1 timestamp-vs-posttest boundary exclusions.

This is an aggregate-only audit. It NEVER returns raw text, session IDs,
participant-level scores, utterances, or per-session records.
The comparison is intentionally identical to the original strict E1 rule:
any event with timestamp_elapsed_seconds >= posttest_started_elapsed_seconds.
"""
from __future__ import annotations
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

def csv_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def diagnose(root, expect=2139):
    root=Path(root)
    profiles=sorted(root.glob(
        "1_main_leaderboard_data/gre_*/ai_arm_*/task_id_*/student_data/student.json"))
    if len(profiles)!=expect:
        raise RuntimeError(f"E1 time diagnostic BLOCKED: expected {expect} profiles, got {len(profiles)}")
    totals=Counter()
    sections={}
    types=Counter()
    for path in profiles:
        p=json.loads(path.read_text(encoding="utf-8"))
        section=p.get("instrument_id")
        if section not in ("gre_quant","gre_verbal"):
            raise RuntimeError("unrecognized section")
        stat=sections.setdefault(section, Counter())
        events=csv_rows(path.parent.parent/"ai_tutoring_data"/
                        "student_ai_tutor_interaction_trajectory.csv")
        stop=p.get("posttest_started_elapsed_seconds")
        if stop is None:
            totals["sessions_no_posttest_boundary"]+=1
            stat["sessions_no_posttest_boundary"]+=1
            continue
        boundary=float(stop)
        parsed=[]
        for event in events:
            raw=event.get("timestamp_elapsed_seconds","")
            if raw == "":
                totals["events_missing_timestamp"]+=1
                continue
            value=float(raw)
            is_beyond=value>=boundary
            parsed.append((int(event["trajectory_position"]),event["event_type"],is_beyond))
        invalid=[x for x in parsed if x[2]]
        totals["sessions_analyzed"]+=1
        stat["sessions_analyzed"]+=1
        if not invalid:
            totals["sessions_with_no_beyond"]+=1
            stat["sessions_with_no_beyond"]+=1
            continue
        totals["sessions_old_E1_excludes"]+=1
        stat["sessions_old_E1_excludes"]+=1
        student_after=sum(k=="student_message" for _,k,_ in invalid)
        ai_after=sum(k=="ai_tutor_message" for _,k,_ in invalid)
        nonchat_after=len(invalid)-student_after-ai_after
        for _,kind,_ in invalid:
            types[kind]+=1
        totals["events_beyond"]+=len(invalid)
        totals["student_messages_beyond"]+=student_after
        totals["ai_messages_beyond"]+=ai_after
        totals["nonchat_events_beyond"]+=nonchat_after
        if student_after:
            totals["excluded_sessions_with_student_after"]+=1
            stat["excluded_sessions_with_student_after"]+=1
        else:
            totals["excluded_sessions_with_only_nonstudent_after"]+=1
            stat["excluded_sessions_with_only_nonstudent_after"]+=1
        first_cross=min(pos for pos,_,_ in invalid)
        if any(pos>first_cross and not beyond for pos,_,beyond in parsed):
            totals["excluded_sessions_with_timestamp_recrossing"]+=1
            stat["excluded_sessions_with_timestamp_recrossing"]+=1
        last_student=max((pos for pos,k,_ in parsed if k=="student_message"),default=-1)
        if first_cross>last_student:
            totals["excluded_sessions_first_cross_after_last_student"]+=1
        totals["student_messages_before_boundary_in_excluded_sessions"]+=sum(
            kind=="student_message" and not beyond for _,kind,beyond in parsed)
    return {
        "status":"DIAGNOSTIC_ONLY_NOT_AN_E1_GATE_CHANGE",
        "n_source_profiles":len(profiles),
        "totals":dict(totals),
        "by_section":{k:dict(v) for k,v in sorted(sections.items())},
        "beyond_boundary_event_types":dict(sorted(types.items())),
        "privacy":"aggregate-only; no session IDs, scores, or dialogue text",
        "interpretation":"Timestamp beyond test start is suspicious but does not "
            "independently prove dialogue leaked posttest information. "
            "Do not relax E1 exclusions based on these counts alone.",
    }

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--expect",type=int,default=2139)
    args=ap.parse_args()
    r=diagnose(args.data,args.expect)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(r,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(r,indent=2))

if __name__=="__main__":
    main()
