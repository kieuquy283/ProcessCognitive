#!/usr/bin/env python3
"""E14: LOCKED internal holdout of minimal StudentBench practice evidence.

Source contract: docs/E14_locked_internal_holdout_protocol_v0.1.md,
committed BEFORE E14 holdout scoring. Previously reserved 125 E13 task IDs
are scored only after development parity assertion.

Run:
  python experiments/e14_locked_holdout.py \
    --input annotation_work/e13_private_trajectories.json.gz \
    --output results/E14_locked_holdout_aggregate.json
Requires e13_features.py in the same source directory.

No raw event text, learner IDs, per-item predictions or answer data are exported.
"""
import argparse,collections,gzip,json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss,roc_auc_score,brier_score_loss
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder,StandardScaler

from e13_features import assemble

SEED=20261025
C=0.3
BASE=["pre_total","pre_theta","pre_matched","pre_skill","pre_sub",
      "practice_n","practice_good","practice_submissions",
      "student_msgs","tutor_msgs"]
CATEGORICAL=["question","skill","subskill","difficulty","arm","form"]
ATTEMPTS=["prov_repeated_fraction","prov_avg_attempts",
          "prov_max_attempts","prov_n_attempted"]
FIRST=["prov_first_correct_rate","prov_first_wrong_count","prov_answered_missing"]
EXPECTED_E13_CV={"B0":0.5243614134736273,"P_attempts":0.523262}
# Exact E13 exploratory ablation originally printed 0.523262 (6 decimals).
# For P_attempts, allow 2e-6 tolerance; baseline has complete precision.
def logloss_individual(y,p):
    p=np.clip(p,1e-8,1-1e-8)
    return -(y*np.log(p)+(1-y)*np.log(1-p))

def make_pipeline(numeric):
    prep=ColumnTransformer([
       ("num",Pipeline([
           ("impute",SimpleImputer(strategy="median",add_indicator=True,keep_empty_features=True)),
           ("scale",StandardScaler())]),numeric),
       ("categorical",OneHotEncoder(handle_unknown="ignore"),CATEGORICAL)],
       sparse_threshold=1)
    return Pipeline([("preprocess",prep),
                     ("model",LogisticRegression(solver="liblinear",C=C,max_iter=250))])

def grouped_oof(frame,nums):
    yy=frame.y.to_numpy(dtype=int)
    gg=frame.group.astype(str).to_numpy()
    pred=np.full(len(frame),np.nan)
    for tr,va in GroupKFold(n_splits=4).split(frame,yy,gg):
        if set(gg[tr])&set(gg[va]):
            raise AssertionError("Task ID leakage in development CV")
        pipe=make_pipeline(nums)
        pipe.fit(frame.iloc[tr][nums+CATEGORICAL],yy[tr])
        pred[va]=pipe.predict_proba(frame.iloc[va][nums+CATEGORICAL])[:,1]
    if not np.isfinite(pred).all():
        raise AssertionError("Missing OOF prediction")
    return float(log_loss(yy,pred))

def score(y,p):
    return {"LogLoss":float(log_loss(y,p)),
            "Brier":float(brier_score_loss(y,p)),
            "AUC":float(roc_auc_score(y,p)) if len(set(y))>1 else None}

def train_predict(dev,hold,numeric):
    yy=dev.y.to_numpy(dtype=int)
    pipe=make_pipeline(numeric)
    pipe.fit(dev[numeric+CATEGORICAL],yy)
    return pipe.predict_proba(hold[numeric+CATEGORICAL])[:,1]

def contrast(reference,challenger,yy,groups,rng,boot):
    losses=logloss_individual(yy,reference)-logloss_individual(yy,challenger)
    grouped=pd.DataFrame({"group":groups,"loss_improvement":losses}).groupby(
        "group",sort=True).loss_improvement.mean().to_numpy()
    take=rng.integers(0,len(grouped),size=(boot,len(grouped)))
    draws=grouped[take].mean(axis=1)
    ci=np.quantile(draws,[.025,.975])
    return {
        "positive_means_candidate_better":float(grouped.mean()),
        "ci95_task_bootstrap":[float(ci[0]),float(ci[1])],
        "point_item_weighted":float(losses.mean()),
        "n_task_groups":len(grouped),
        "ci_contains_zero":bool(ci[0]<=0<=ci[1])}

def null_shuffle_dev_by_task(dev,cols,seed):
    # 499 unique task rows, each duplicated once per posttest item. Shuffle
    # four provenance covariates as a UNIT across tasks, not across item rows.
    # Do not alter labels, pretest controls, event counts or test-set covariates.
    rng=np.random.default_rng(seed)
    unique=dev.drop_duplicates("group").sort_values("group")
    vals=unique[cols].to_numpy().copy()
    perm=rng.permutation(len(vals))
    key={group:tuple(vals[j]) for group,j in zip(unique.group,perm)}
    out=dev.copy()
    mapped=out["group"].map(key).to_list()
    for j,c in enumerate(cols):
        out[c]=[v[j] for v in mapped]
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,default=Path("annotation_work/e13_private_trajectories.json.gz"))
    p.add_argument("--output",type=Path,default=Path("results/E14_locked_holdout_aggregate.json"))
    p.add_argument("--bootstrap",type=int,default=10000)
    p.add_argument("--null-seeds",type=int,default=20)
    args=p.parse_args()
    with gzip.open(args.input,"rt",encoding="utf8") as f:raw=json.load(f)
    if raw["revision"]!="304c8d63c726e72b60510bba3a44454fc0726721":
        raise ValueError("Dataset SHA changed from frozen E14 protocol")
    if raw["successful"]!=624 or raw["selected"]!=624:
        raise ValueError("Unpinned/incomplete cohort; this E14 internal test requires E13's same 624")
    # Derive both frames with unchanged outcome-blind E13 event_features().
    dev,dev_audit=assemble(raw,shuffles=0,subset="development")
    held,held_audit=assemble(raw,shuffles=0,subset="reserved")
    dev_groups=set(dev.group);test_groups=set(held.group)
    if dev_groups&test_groups:raise AssertionError("Task leakage into reserved group")
    if len(dev_groups)!=499 or len(test_groups)!=125 or len(dev)!=13473 or len(held)!=3375:
        raise ValueError(f"Unexpected E13 partition: dev={len(dev_groups)}/{len(dev)}, hold={len(test_groups)}/{len(held)}")
    if dev.y.isna().any() or held.y.isna().any():raise ValueError("Missing outcome")
    counts=sorted(k for k in dev if k.startswith("count_"))
    spec={
       "B0":BASE,
       "N2_event_counts":BASE+counts,
       "P_attempts_LOCKED":BASE+counts+ATTEMPTS,
       "P_first_secondary":BASE+counts+FIRST,
       "P_first_plus_attempts_secondary":BASE+counts+FIRST+ATTEMPTS,
    }
    if any(col not in dev or col not in held for cols in spec.values() for col in cols):
        raise KeyError("Required E13 predictors changed")
    # Do not expose, inspect, or score held-out outcomes until parity verified.
    oof_b0=grouped_oof(dev,spec["B0"])
    oof_att=grouped_oof(dev,spec["P_attempts_LOCKED"])
    if abs(oof_b0-EXPECTED_E13_CV["B0"])>1e-8:
        raise AssertionError(f"B0 not identical to published E13: {oof_b0}")
    if abs(oof_att-EXPECTED_E13_CV["P_attempts"])>2e-6:
        raise AssertionError(f"P_attempts deviates from published E13: {oof_att}")
    print("E14 DEV_PARITY_PASS B0",oof_b0,"P_attempts",oof_att,flush=True)
    # NOW apply predeclared models ONCE to reserved data.
    y=held.y.to_numpy(dtype=int)
    predictions={}
    scores={}
    for name,cols in spec.items():
        predictions[name]=train_predict(dev,held,cols)
        scores[name]=score(y,predictions[name])
        print("E14 HOLDOUT",name,scores[name],flush=True)
    groups=held.group.to_numpy()
    rng=np.random.default_rng(SEED)
    comparisons={}
    for ref,challenger in (
        ("B0","P_attempts_LOCKED"),
        ("N2_event_counts","P_attempts_LOCKED"),
        ("B0","N2_event_counts"),
        ("B0","P_first_secondary"),
        ("B0","P_first_plus_attempts_secondary"),
        ("P_first_secondary","P_attempts_LOCKED"),
    ):
        comparisons[ref+" -> "+challenger]=contrast(
            predictions[ref],predictions[challenger],y,groups,rng,args.bootstrap)
    null_metrics=[]
    for j in range(args.null_seeds):
        bad_dev=null_shuffle_dev_by_task(dev,ATTEMPTS,seed=SEED+j+1)
        predict=train_predict(bad_dev,held,spec["P_attempts_LOCKED"])
        null_metrics.append(score(y,predict)["LogLoss"])
    vals=np.asarray(null_metrics)
    null_summary={
        "n_null_shuffles":len(vals),
        "null_shuffle_rule":"permute entire attempt-provenance feature block across TRAINING TASK IDs only",
        "test_attempt_feature_values_unchanged":True,
        "null_loss_median":float(np.median(vals)),
        "null_loss_min":float(vals.min()),"null_loss_max":float(vals.max()),
        "true_attempt_loss":scores["P_attempts_LOCKED"]["LogLoss"],
        "null_losses_worse_than_true":int((vals>scores["P_attempts_LOCKED"]["LogLoss"]).sum()),
        "all_null_losses":[float(k) for k in vals]
    }
    # Descriptive subgroup, no fit/parameter selection. A minimum of 5
    # task IDs per arm prevents pseudo-precise subgroup reporting.
    subgroup={}
    for arm,sub in held.groupby("arm",sort=True):
        mask=(held.arm==arm).to_numpy()
        if sub.group.nunique()<5:continue
        yy=y[mask]
        subgroup[str(arm)]={
            "tasks":sub.group.nunique(),"items":int(mask.sum()),
            "B0_Loss":float(log_loss(yy,predictions["B0"][mask])),
            "Attempt_Loss":float(log_loss(yy,predictions["P_attempts_LOCKED"][mask]))}
        subgroup[str(arm)]["gain"]=subgroup[str(arm)]["B0_Loss"]-subgroup[str(arm)]["Attempt_Loss"]
    summary={
        "status":"ONE_INTERNAL_HOLDOUT_EVALUATION_LOCKED_E14",
        "protocol":"docs/E14_locked_internal_holdout_protocol_v0.1.md",
        "pre_holdout_frozen_protocol_commit":"1e868b4685c3012386c8d121ad0f393da4fdf14a",
        "revision":raw["revision"],
        "n_retrieved_sessions":raw["successful"],"n_dev_sessions":dev.sid.nunique(),
        "n_holdout_sessions":held.sid.nunique(),
        "n_dev_posttest_items":len(dev),"n_holdout_posttest_items":len(held),
        "n_dev_task_ids":len(dev_groups),"n_holdout_task_ids":len(test_groups),
        "hyperparameter_C":C,
        "dev_parity_check":{"B0_LogLoss":oof_b0,"Attempt_LogLoss":oof_att},
        "primary":"B0 -> P_attempts_LOCKED",
        "holdout_scores":scores,"paired_task_cluster_comparisons":comparisons,
        "holdout_attempt_shuffle_null":null_summary,
        "holdout_tutor_arm_descriptives":subgroup,
        "warnings":[
           "Holdout is INTERNAL: E13 chose the attempt feature family post hoc from same public dataset research program.",
           "Do not call this an independent external prospective replication.",
           "Bootstrap CI is conditional on frozen trained models and task sample; no multiple-testing adjustment.",
           "No causal claim about learning gain, corrective feedback or AI tutoring efficacy.",
           "No individual predictions, raw dialogue, student IDs or item outcomes exported.",
        ]}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf8")
    print("E14 DONE",len(held),"TEST ITEMS",len(test_groups),"TEST TASK IDS",flush=True)

if __name__=="__main__":
    main()
