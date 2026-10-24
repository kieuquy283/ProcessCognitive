#!/usr/bin/env python3
"""E11: compare TWO independently completed annotation files.

Never call model-model agreement "human ground truth". Audit sheet for 160
blind human-review pairs is deterministic and does not contain model labels,
confidence, stratum or earlier rationales.
"""
import argparse,collections,csv,json,random
from pathlib import Path
import numpy as np

CLASSES=("D","S","N","U")
FIELDS=("pair_id","gre_skill","gre_subskill","tutoring_concept_title","label","rationale")

def read(path):
    with Path(path).open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def kappa(x,y):
    n=len(x)
    po=sum(a==b for a,b in zip(x,y))/n
    pa=collections.Counter(x);pb=collections.Counter(y)
    pe=sum(pa[l]*pb[l] for l in (set(x)|set(y)))/n**2
    return None if pe>=1 else (po-pe)/(1-pe)

def info(x,y):
    return {"n":len(x),"agreement":sum(a==b for a,b in zip(x,y))/len(x),
            "cohen_kappa":kappa(x,y),"count_A":dict(collections.Counter(x)),
            "count_B":dict(collections.Counter(y))}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--model-a",type=Path,required=True)
    p.add_argument("--model-b",type=Path,required=True)
    p.add_argument("--sidecar",type=Path,required=True,help="Private analyst-only E11 sampling strata file")
    p.add_argument("--out",type=Path,default=Path("annotation_work/e11/agreement.json"))
    p.add_argument("--audit-out",type=Path,default=Path("annotation_work/e11/e11_human_blinded_160.csv"))
    args=p.parse_args()
    source=read(args.source);A=read(args.model_a);B=read(args.model_b);side=read(args.sidecar)
    if not (len(source)==len(A)==len(B)==len(side)==400):
        raise ValueError("All inputs must have 400 records")
    if len({r["pair_id"] for r in source})!=400:raise ValueError("Duplicate source pairs")
    bystrata={r["pair_id"]:r["sample_stratum"] for r in side}
    if set(bystrata)!={r["pair_id"] for r in source}:raise ValueError("Analyst sidecar has mismatched pair IDs")
    for idx,(s,a,b) in enumerate(zip(source,A,B)):
        for col in FIELDS[:4]:
            if not(s[col]==a[col]==b[col]):raise ValueError(f"Mismatch in original data, row {idx}, column {col}")
        for r in (a,b):
            if r["label"] not in CLASSES:raise ValueError("Invalid or missing model label")
            if not (1<=len(r["rationale"].strip().split())<=25):raise ValueError("Missing/too long rationale")
    aa=[r["label"] for r in A];bb=[r["label"] for r in B]
    matrix={i:{j:sum(a==i and b==j for a,b in zip(aa,bb)) for j in CLASSES} for i in CLASSES}
    summary={
        "status":"TWO_MODEL_LABELS_NOT_HUMAN_GROUND_TRUTH",
        "overall":info(aa,bb),
        "D_versus_non_D":info([("D" if a=="D" else "other") for a in aa],
                              [("D" if b=="D" else "other") for b in bb]),
        "confusion_rows_A_columns_B":matrix,"by_sample_stratum":{},
        "critical_caution":"Population label proportions MAY be estimated ONLY from the 200 uniform unique-pair panel with an independently valid reference; not from all 400 intentionally enriched pairs."
    }
    for name in ("uniform_unique_pair","high_similarity_enriched","generic_strategy_stress"):
        idx=[i for i,s in enumerate(source) if bystrata[s["pair_id"]]==name]
        if not idx:raise ValueError("Missing expected panel "+name)
        summary["by_sample_stratum"][name]=info([aa[i] for i in idx],[bb[i] for i in idx])
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(summary,indent=2),encoding="utf-8")
    quotas={"uniform_unique_pair":80,"high_similarity_enriched":60,"generic_strategy_stress":20}
    rng=random.Random(20261024)
    indices=[]
    for name,q in quotas.items():
        candidates=[i for i,r in enumerate(source) if bystrata[r["pair_id"]]==name]
        indices+=rng.sample(candidates,q)
    rng.shuffle(indices)
    with args.audit_out.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(FIELDS))
        w.writeheader()
        for i in indices:
            s=source[i];w.writerow({k:s[k] for k in FIELDS})
    print(json.dumps(summary,indent=2))
    print("BLINDED HUMAN REVIEW SAMPLE:",str(args.audit_out),"rows",len(indices))
if __name__=="__main__":main()
