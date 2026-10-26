#!/usr/bin/env python3
"""Create ONE common 40-episode blind input for Codex Astra and Gemini Web.

Run AFTER nd1_extract_feedback_episodes.py generated the current private
nd1_pilot_180_PRIVATE.csv. Do NOT transmit or commit user/student dialogue.
Only formats and samples the SAME 40 records for both annotators.
"""
import argparse,csv,hashlib,json,re,shutil
from pathlib import Path
FIELDS=["episode_id","previous_student_excerpt","tutor_context","student_turn",
        "primary_act","feedback_uptake","annotation_rationale","confidence"]
TEXT=FIELDS[:4]
LABELS=FIELDS[4:]
def read(path):
    with path.open("r",encoding="utf-8-sig",newline="") as fp:
        rdr=csv.DictReader(fp)
        if rdr.fieldnames!=FIELDS:raise ValueError("Expected exactly eight ND1 fields")
        return list(rdr)
def write(path,records):
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader()
        w.writerows(records)
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,default=Path("annotation_work/new_direction/nd1_pilot_180_PRIVATE.csv"))
    parser.add_argument("--out-dir",type=Path,default=Path("annotation_work/new_direction"))
    parser.add_argument("--count",type=int,default=40)
    args=parser.parse_args()
    if args.count!=40:raise ValueError("ND1 phase-1 codebook expects exactly 40 cases")
    r=read(args.source)
    if len(r)!=180:raise ValueError(f"Expected full 180-row sample; got {len(r)}")
    if len(set(x["episode_id"] for x in r))!=180:raise ValueError("Duplicate ID in source")
    if any(any(x[k].strip() for k in LABELS) for x in r):
        raise ValueError("Source is NOT blind: it already contains annotations")
    rows=r[:40]
    args.out_dir.mkdir(parents=True,exist_ok=True)
    common=args.out_dir/"ND1_pilot_40_blind.csv"
    a=args.out_dir/"ND1_Astra_A_40_BLANK.csv"
    b=args.out_dir/"ND1_Gemini4Argon_B_40_UPLOAD.csv"
    for p in (common,a,b):write(p,rows)
    # Verify identical inputs; Gemini web should be given only the source CSV.
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (common,a,b)}
    assert len(set(hashes.values()))==1
    check=read(common)
    assert len(check)==40 and len({r["episode_id"] for r in check})==40
    # Pattern review is a warning, NOT an anonymization guarantee.
    combined=" ".join(x[k] for x in check for k in TEXT[1:])
    pii={
      "email_matches":len(re.findall(r"[\w.+-]+@[\w.-]+\.[a-z]{2,}",combined,re.I)),
      "urls":len(re.findall(r"https?://\S+",combined,re.I)),
      "possible_phone_numbers":len(re.findall(r"(?<!\d)\+?\d[\d .()-]{9,}\d(?!\d)",combined))
    }
    out={
      "status":"BLIND_40_READY_FOR_INDEPENDENT_ANNOTATION",
      "ids":40,"source_total":180,
      "first_id":check[0]["episode_id"],"last_id":check[-1]["episode_id"],
      "identical_input_sha256":next(iter(hashes.values())),
      "files":[p.name for p in (common,a,b)],
      "pii_pattern_screen":pii,
      "human_manual_privacy_review_required":True,
      "annotation_label_count":0
    }
    (args.out_dir/"ND1_40_input_manifest.json").write_text(json.dumps(out,indent=2),encoding="utf8")
    print(json.dumps(out,indent=2))
if __name__=="__main__":main()
