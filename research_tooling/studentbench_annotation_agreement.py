#!/usr/bin/env python3
"""E1 A/B agreement on a frozen, score-blinded annotation pilot.

Consumes PRIVATE local annotation files and manifest. Writes ONLY aggregate
agreement, confusion matrix, and reliability diagnostics; never raw texts,
participant IDs, per-turn labels or per-session outcomes.

Do NOT call a silver-LLM comparison "human ground truth."
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score, confusion_matrix

DISPOSITIONS=("UNCLEAR","OUT_OF_SCOPE")

def run(a_path,b_path,manifest_path,summary_path,codebook_path,
        out_path,phase="development",tier="human_reference"):
    if phase not in ("development","locked_holdout"):
        raise ValueError("unknown phase")
    if tier not in ("human_reference","silver_llm"):
        raise ValueError("unknown annotation tier")
    codebook=json.loads(Path(codebook_path).read_text(encoding="utf-8"))
    if codebook.get("approved") is not True:
        raise RuntimeError("E1 BLOCKED: codebook NOT APPROVED")
    if phase=="locked_holdout" and not codebook.get("frozen"):
        raise RuntimeError("E1 BLOCKED: codebook must be frozen for locked holdout")
    labels=list(codebook.get("labels",[]))+list(DISPOSITIONS)
    if not labels or len(labels)!=len(set(labels)):
        raise RuntimeError("invalid approved codebook")
    manifest=pd.read_csv(manifest_path,keep_default_na=False)
    if len(manifest)!=280 or manifest.pilot_id.duplicated().any():
        raise RuntimeError("E1 BLOCKED: manifest must contain 280 unique items")
    if not {"pilot_id","turn_key","split","session_id"}.issubset(manifest.columns):
        raise RuntimeError("E1 BLOCKED: private manifest missing required columns")
    digest=hashlib.sha256("\n".join(sorted(manifest.turn_key)).encode()).hexdigest()
    summary=json.loads(Path(summary_path).read_text(encoding="utf-8"))
    if digest!=summary.get("selected_keys_sha256"):
        raise RuntimeError("E1 BLOCKED: selected-set hash mismatch")
    a=pd.read_csv(a_path,keep_default_na=False)
    b=pd.read_csv(b_path,keep_default_na=False)
    required={"pilot_id","turn_key","label","annotator_source"}
    for who,df in (("A",a),("B",b)):
        if not required.issubset(df.columns):
            raise RuntimeError(f"E1 BLOCKED: annotator {who} missing columns")
        if len(df)!=280 or df.pilot_id.duplicated().any() or df.turn_key.duplicated().any():
            raise RuntimeError(f"E1 BLOCKED: annotator {who} incomplete or duplicated")
        if set(df.pilot_id)!=set(manifest.pilot_id):
            raise RuntimeError(f"E1 BLOCKED: annotator {who} has unexpected pilot IDs")
        check=df.merge(manifest[["pilot_id","turn_key"]],on="pilot_id",
                       suffixes=("","_expected"),validate="one_to_one")
        if not (check.turn_key==check.turn_key_expected).all():
            raise RuntimeError(f"E1 BLOCKED: annotator {who} has inconsistent turn keys")
    matched=manifest[["pilot_id","split","session_id"]].merge(
        a[["pilot_id","label","annotator_source"]].rename(
            columns={"label":"label_a","annotator_source":"source_a"}),
        on="pilot_id",validate="one_to_one").merge(
        b[["pilot_id","label","annotator_source"]].rename(
            columns={"label":"label_b","annotator_source":"source_b"}),
        on="pilot_id",validate="one_to_one")
    selected=matched[matched.split==phase]
    expected=200 if phase=="development" else 80
    if len(selected)!=expected:
        raise RuntimeError(f"E1 BLOCKED: expected {expected} items in phase")
    if selected[["label_a","label_b"]].eq("").any().any():
        raise RuntimeError("E1 BLOCKED: missing independent labels for selected phase")
    if not set(selected.label_a).issubset(labels) or not set(selected.label_b).issubset(labels):
        raise RuntimeError("E1 BLOCKED: label outside approved codebook")
    if tier=="human_reference" and (not selected.source_a.eq("human").all()
                                    or not selected.source_b.eq("human").all()):
        raise RuntimeError("E1 BLOCKED: human reference requires two human sources")
    if tier=="silver_llm" and (not selected.source_a.eq("llm").all()
                               or not selected.source_b.eq("llm").all()):
        raise RuntimeError("E1 BLOCKED: silver LLM requires two llm sources")
    if selected.session_id.nunique()<28:
        raise RuntimeError("E1 BLOCKED: too few independent sessions")
    la=selected.label_a.tolist()
    lb=selected.label_b.tolist()
    kappa=float(cohen_kappa_score(la,lb,labels=labels))
    agreement=float(np.mean(np.array(la)==np.array(lb)))
    report={
        "status":"AGREEMENT_ONLY_NOT_MODEL_F1",
        "phase":phase,
        "evidence_tier":tier,
        "sample_hash":digest,
        "codebook_version":codebook.get("version",""),
        "n_units":len(selected),
        "n_distinct_sessions":int(selected.session_id.nunique()),
        "raw_agreement":agreement,
        "cohen_kappa":kappa if np.isfinite(kappa) else None,
        "labels":labels,
        "confusion_a_rows_b_columns":confusion_matrix(la,lb,labels=labels).tolist(),
        "warning":"Agreement alone does not establish construct validity; "
                  "LLM silver labels are not human gold. No educational outcome claim.",
    }
    out=Path(out_path);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for key in ("a","b","manifest","summary","codebook","out"):
        p.add_argument("--"+key,required=True)
    p.add_argument("--phase",choices=("development","locked_holdout"),
                   default="development")
    p.add_argument("--tier",choices=("human_reference","silver_llm"),
                   default="human_reference")
    args=p.parse_args()
    result=run(args.a,args.b,args.manifest,args.summary,args.codebook,
               args.out,args.phase,args.tier)
    print(json.dumps(result,indent=2))
