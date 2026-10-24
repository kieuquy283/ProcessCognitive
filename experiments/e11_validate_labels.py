#!/usr/bin/env python3
"""Validate one E11 annotator's filled 400-row file against frozen blind source."""
import argparse,csv,json
from pathlib import Path
COLS=["pair_id","gre_skill","gre_subskill","tutoring_concept_title","label","rationale"]
LABELS={"D","S","N","U"}

def read(path):
    with Path(path).open("r",encoding="utf-8-sig",newline="") as f:
        rdr=csv.DictReader(f)
        if rdr.fieldnames!=COLS:raise ValueError("Expected exact six E11 columns: "+str(COLS))
        return list(rdr)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--file",type=Path,required=True)
    args=p.parse_args()
    source=read(args.source);result=read(args.file)
    if len(source)!=400 or len(result)!=400:
        raise ValueError(f"Expected 400 rows in BOTH input and output; got {len(source)} and {len(result)}")
    seen=set();counts={s:0 for s in sorted(LABELS)}
    for i,(a,b) in enumerate(zip(source,result),2):
        for k in COLS[:4]:
            if a[k]!=b[k]:raise ValueError(f"Row {i}: original data changed: {k}")
        if b["pair_id"] in seen:raise ValueError(f"Duplicate pair ID at row {i}")
        seen.add(b["pair_id"])
        if a["label"].strip() or a["rationale"].strip():raise ValueError("Source already annotated (must be blinded)")
        lab=b["label"].strip()
        rationale=b["rationale"].strip()
        if lab not in LABELS:raise ValueError(f"Row {i}: invalid or missing label")
        if not (1<=len(rationale.split())<=25):raise ValueError(f"Row {i}: rationale 1–25 words required")
        counts[lab]+=1
    print(json.dumps({"status":"PASS_FORMAT_ONLY_NOT_LABEL_ACCURACY",
                      "n":len(result),"labels":counts,"file":str(args.file)},indent=2))

if __name__=="__main__":main()
