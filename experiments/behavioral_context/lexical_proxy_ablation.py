#!/usr/bin/env python3
"""E8L: real GRE Quant lexical-proxy ablation, NOT semantic human labels.

Uses existing StudentBench development folds and baseline feature set. Source
student_text is the first <=10,000 characters of chronological utterances
assembled by the original loader. Only aggregate CV metrics may be uploaded.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV,KFold
from controlled_event_ablation import (
    NUMERIC,CAT,BAGS,assemble,assign_original_e8_folds,ridge_pipeline
)

KEYWORDS={
  "why_how":r"\b(why|how)\b",
  "explain":r"\b(explain|explanation|understand|confused|clarify)\b",
  "verify":r"\b(check|verify|correct|right|wrong)\b",
  "reason":r"\b(because|therefore|think|suppose|assume)\b",
  "answer":r"\b(answer|solution|solve|tell me)\b"
}
FEATURES=("lex_log_words","lex_question_mark_per_100",
          "lex_unique_ratio","lex_mean_word_chars") + tuple(
          "lex_"+k+"_per_100" for k in KEYWORDS)

def lexical_features(text):
    txt=(text or "").lower()
    words=re.findall(r"[a-z]+(?:'[a-z]+)?",txt)
    n=max(1,len(words))
    result={
      "lex_log_words":float(np.log1p(len(words))),
      "lex_question_mark_per_100":100*txt.count("?")/n,
      "lex_unique_ratio":len(set(words))/n,
      "lex_mean_word_chars":sum(len(w) for w in words)/n,
    }
    for name,pattern in KEYWORDS.items():
        result["lex_"+name+"_per_100"]=100*len(re.findall(pattern,txt))/n
    return result

def build_frame(sessions,dev_ids,seed=20261126):
    df=assemble(sessions,dev_ids)
    features=pd.DataFrame([
        lexical_features(sessions[i]["student_text"]) for i in dev_ids])
    if features.isna().any().any() or not set(FEATURES)==set(features.columns):
        raise ValueError("lexical extraction failed")
    # Fixed group-wise permutation preserves tutor/form marginal distributions.
    rng=np.random.default_rng(seed)
    shuf=features.copy()
    groups={}
    for n,i in enumerate(dev_ids):
        p=sessions[i]["profile"]
        key=(p["ai_model_preset_id"],p["assessment_form_order"])
        groups.setdefault(key,[]).append(n)
    for positions in groups.values():
        if len(positions)>1:
            shuffled=rng.permutation(positions)
            shuf.iloc[positions]=features.iloc[shuffled].to_numpy()
    for k in FEATURES:
        df[k]=features[k].to_numpy()
        df["null_"+k]=shuf[k].to_numpy()
    return df

def evaluate(df,folds,seed=20261126,n_boot=1000):
    folds=np.asarray(folds)
    if len(df)<80 or set(folds.tolist())!={0,1,2,3}:
        raise ValueError("E8L BLOCKED: insufficient development sessions/folds")
    if len(folds)!=len(df):
        raise ValueError("E8L BLOCKED: rows and fold assignments do not match")
    forbidden={"student_id","posttest_score_points","score_lift_points"}
    if forbidden.intersection(df.columns):
        raise ValueError("E8L BLOCKED: outcome or session identifier leaked into features")
    base=list(NUMERIC)+list(CAT)+list(BAGS)
    arms={
      "B0_event_bag":base,
      "B1_event_bag_plus_lexical":base+list(FEATURES),
      "B2_event_bag_plus_shuffled_lexical":base+["null_"+x for x in FEATURES],
    }
    required=set().union(*(set(x) for x in arms.values()))|{"y"}
    if required-set(df.columns):
        raise ValueError("E8L BLOCKED: missing required features")
    y=df.y.to_numpy(dtype=float)
    if not np.isfinite(y).all() or (y<0).any() or (y>27).any():
        raise ValueError("E8L BLOCKED: invalid outcome values")
    pred={name:np.full(len(df),np.nan) for name in arms}
    for fold in range(4):
        train=np.flatnonzero(folds!=fold)
        test=np.flatnonzero(folds==fold)
        inner=KFold(n_splits=3,shuffle=True,random_state=seed+fold)
        for name,cols in arms.items():
            estimator=GridSearchCV(ridge_pipeline(cols),
                {"model__alpha":[1.,10.,100.]},
                cv=inner,scoring="neg_mean_absolute_error")
            estimator.fit(df.iloc[train][cols],y[train])
            pred[name][test]=estimator.predict(df.iloc[test][cols])
    rng=np.random.default_rng(seed)
    ix=rng.integers(0,len(y),size=(n_boot,len(y)))
    report={"status":"DEVELOPMENT_EXPLORATORY_LEXICAL_PROXY_NOT_BEHAVIOR_LABELS",
            "n_development_sessions":len(df),"n_folds":4,
            "features":list(FEATURES),
            "metrics":{}, "comparisons":{},
            "caution":"Text of STUDENT messages from source loader capped at "
                      "10,000 chars per session. No human-labeled behaviors, "
                      "no holdout and no causal interpretation."}
    for name,z in pred.items():
        report["metrics"][name]={
          "MAE":float(mean_absolute_error(y,z)),
          "RMSE":float(np.sqrt(mean_squared_error(y,z))),
          "R2":float(r2_score(y,z)),
        }
    for key,first,second in (
        ("lexical_vs_bag","B0_event_bag","B1_event_bag_plus_lexical"),
        ("lexical_vs_shuffled","B2_event_bag_plus_shuffled_lexical",
            "B1_event_bag_plus_lexical")):
        effect=np.abs(y-pred[first])-np.abs(y-pred[second])
        report["comparisons"][key]={
          "MAE_reduction":float(effect.mean()),
          "bootstrap_CI95":np.quantile(effect[ix].mean(axis=1),[.025,.975]).tolist(),
        }
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--per-tutor",type=int,default=62)
    args=parser.parse_args()
    if not (args.data/"studentbench_overall_parameters.json").exists():
        raise SystemExit("E8L BLOCKED: official source root missing")
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
    from studentbench_loader import load_sessions
    sessions=load_sessions(args.data,per_tutor=args.per_tutor)
    folds,holdout=assign_original_e8_folds(sessions)
    dev_ids=sorted(folds)
    report=evaluate(build_frame(sessions,dev_ids),
                    [folds[i] for i in dev_ids])
    report["n_loaded_sessions"]=len(sessions)
    report["n_holdout_unopened"]=len(holdout)
    report["selective_revision_not_full_snapshot_hash_verified"]=True
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))

if __name__=="__main__":main()
