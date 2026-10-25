#!/usr/bin/env python3
"""Double-annotator agreement for ND1, no invented gold/reference labels."""
import argparse,csv,json,collections,random
from pathlib import Path
from sklearn.metrics import cohen_kappa_score,confusion_matrix
from nd1_validate_annotations import validate,rows
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--a",type=Path,required=True)
    p.add_argument("--b",type=Path,required=True)
    p.add_argument("--n",type=int,default=40)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    ia=validate(a.source,a.a,a.n);ib=validate(a.source,a.b,a.n)
    A=rows(a.a);B=rows(a.b)
    out={"status":"ANNOTATOR_AGREEMENT_NOT_GROUND_TRUTH","n":len(A),
         "axes":{},"completed_a":ia["completed"],"completed_b":ib["completed"]}
    for axis in ("primary_act","feedback_uptake"):
        xa=[r[axis] for r in A];xb=[r[axis] for r in B]
        labels=sorted(set(xa)|set(xb))
        out["axes"][axis]={
            "raw_agreement":sum(a==b for a,b in zip(xa,xb))/len(xa),
            "cohen_kappa_nominal":float(cohen_kappa_score(xa,xb,labels=labels)),
            "label_order":labels,"confusion_a_rows_b_cols":confusion_matrix(xa,xb,labels=labels).tolist(),
            "a_distribution":dict(collections.Counter(xa)),"b_distribution":dict(collections.Counter(xb)),
            "disagreements":[r["episode_id"] for r,z,w in zip(A,xa,xb) if z!=w]}
    a.out.parent.mkdir(exist_ok=True,parents=True)
    a.out.write_text(json.dumps(out,indent=2),encoding="utf8")
    print(json.dumps({k:v for k,v in out.items() if k!="axes"},indent=2))
    for k,v in out["axes"].items():
        print(k,"agreement",round(v["raw_agreement"],4),"kappa",round(v["cohen_kappa_nominal"],4),
              "discordant_cases",len(v["disagreements"]))
if __name__=="__main__":main()
