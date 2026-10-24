#!/usr/bin/env python3
"""Validate one finished E9c Codex or Antigravity annotation CSV."""
import argparse,csv,json
from pathlib import Path

COLUMNS=["pair_id","gre_skill","gre_subskill","tutoring_concept_title","label","rationale"]
LABELS={"D","S","N","U"}

def load(path):
 with Path(path).open("r",encoding="utf-8-sig",newline="") as f:
  reader=csv.DictReader(f)
  if reader.fieldnames!=COLUMNS:
   raise ValueError(f"Columns must match EXACTLY: {COLUMNS}")
  return list(reader)

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument("--file",type=Path,required=True)
 parser.add_argument("--source",type=Path,required=True)
 args=parser.parse_args()
 original=load(args.source);assigned=load(args.file)
 if len(original)!=120 or len(assigned)!=120:
  raise ValueError(f"Expected 120 original/annotated records, got {len(original)}/{len(assigned)}")
 seen=set();counts={key:0 for key in sorted(LABELS)}
 for line,(orig,row) in enumerate(zip(original,assigned),start=2):
  for key in COLUMNS[:4]:
   if row[key]!=orig[key]:
    raise ValueError(f"Row {line} field {key} differs from input")
  if row["pair_id"] in seen:raise ValueError(f"Duplicate ID at line {line}")
  seen.add(row["pair_id"])
  label=row["label"].strip().upper()
  if label not in LABELS:raise ValueError(f"Invalid label on row {line}")
  if row["label"]!=label:raise ValueError(f"Noncanonical label at row {line}")
  rationale=row["rationale"].strip()
  if not rationale or len(rationale.split())>25:raise ValueError(f"Rationale must be 1–25 words at row {line}")
  if any(term in rationale.lower() for term in ("cosine similarity","model confidence","another annotator","student score")):
   raise ValueError(f"Potential forbidden rationale content at row {line}")
  counts[label]+=1
 print(json.dumps({"status":"PASS","records":len(assigned),"label_counts":counts,"file":str(args.file)},indent=2))
if __name__=="__main__":main()
