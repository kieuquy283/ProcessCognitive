#!/usr/bin/env python3
"""Validate ND1 behavioral move / feedback-uptake annotation CSVs.

Input private episode CSV, output independent annotation CSV.
This validator checks STRUCTURE, not cognitive or pedagogical correctness.
"""
import argparse,csv,collections,json
from pathlib import Path
SOURCE=("episode_id","previous_student_excerpt","tutor_context","student_turn")
OUTPUT=SOURCE+("primary_act","feedback_uptake","annotation_rationale","confidence")
ACT={"RE","VE","CQ","HR","AN","AK","OT"}
UPTAKE={"NO","NR","AC","AP","RV","UN"}
CONF={"low","medium","high"}
def rows(path):
    with Path(path).open("r",encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        if tuple(rd.fieldnames)!=OUTPUT:raise ValueError("Unexpected CSV columns or column order")
        return list(rd)
def validate(source,output,n_expected=180,allow_partial=False):
    a=rows(source);b=rows(output)
    if len(a)!=n_expected or len(b)!=n_expected:
        raise ValueError(f"Expected {n_expected} source and output rows")
    if len({r["episode_id"] for r in a})!=n_expected:raise ValueError("Duplicate pilot episode IDs")
    labels=collections.Counter();uptakes=collections.Counter();completed=0
    for i,(x,y) in enumerate(zip(a,b),start=2):
        if any(x[k]!=y[k] for k in SOURCE):raise ValueError(f"Source text/ID changed on row {i}")
        if any(x[k].strip() for k in OUTPUT[4:]):raise ValueError("Source file already contains annotations")
        if not any(y[k].strip() for k in OUTPUT[4:]):
            if allow_partial:continue
            raise ValueError(f"Row {i} unlabelled")
        if y["primary_act"] not in ACT:raise ValueError(f"Invalid move on row {i}")
        if y["feedback_uptake"] not in UPTAKE:raise ValueError(f"Invalid uptake on row {i}")
        if y["confidence"] not in CONF:raise ValueError(f"Invalid confidence on row {i}")
        rationale=y["annotation_rationale"].strip()
        if len(rationale.split())<8 or len(rationale.split())>35:
            raise ValueError(f"Rationale must have 8–35 words on row {i}")
        completed+=1;labels[y["primary_act"]]+=1;uptakes[y["feedback_uptake"]]+=1
    return {"status":"VALID_FORMAT_NOT_HUMAN_LABEL_ACCURACY",
            "cases":n_expected,"completed":completed,
            "primary_act_distribution":dict(labels),
            "feedback_uptake_distribution":dict(uptakes)}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--file",type=Path,required=True)
    p.add_argument("--n",type=int,default=180)
    p.add_argument("--allow-partial",action="store_true")
    a=p.parse_args()
    print(json.dumps(validate(a.source,a.file,a.n,a.allow_partial),indent=2))
if __name__=="__main__":main()
