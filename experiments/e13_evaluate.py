#!/usr/bin/env python3
"""E13 grouped pretest-controlled posttest benchmark with 20 sequence shuffles.

Fit imputation, scales, onehot and regularized LR INSIDE 4 task-grouped folds.
Only development items are present in feature pkl. 20 within-session ordered
shuffles are NEGATIVE CONTROLS (fixed seed), not alternative models to select.
All outputs are aggregate; do not upload the input frame.
"""
import argparse,json,collections
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss,roc_auc_score,brier_score_loss

BASE=["pre_total","pre_theta","pre_matched","pre_skill","pre_sub",
      "practice_n","practice_good","practice_submissions",
      "student_msgs","tutor_msgs"]
CATEGORICAL=["question","skill","subskill","difficulty","arm","form"]
def score(y,p):
    p=np.clip(p,1e-8,1-1e-8)
    return {
        "LogLoss":float(log_loss(y,p)),
        "Brier":float(brier_score_loss(y,p)),
        "AUC":float(roc_auc_score(y,p)) if len(np.unique(y))>1 else None
    }
def losses(y,p):
    p=np.clip(p,1e-8,1-1e-8)
    return -(y*np.log(p)+(1-y)*np.log(1-p))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",default="annotation_work/e13_features_private.pkl")
    parser.add_argument("--output",default="results/E13_dev_metrics.json")
    parser.add_argument("--boot",type=int,default=3000)
    args=parser.parse_args()
    df=pd.read_pickle(args.input)
    groups=np.asarray(df.group.astype(str));y=df.y.to_numpy(dtype=int)
    unique_groups=len(set(groups))
    if unique_groups<24:raise ValueError("Insufficient task-disjoint CV groups")
    provenance=[c for c in df if c.startswith("prov_")]
    counts=[c for c in df if c.startswith("count_")]
    temporal=[c for c in df if c.startswith("seq_")]
    if not provenance or not counts or not temporal:raise ValueError("Missing expected features")
    temporal_wo_timing=[c for c in temporal if c not in (
        "seq_median_resubmit_seconds","seq_median_correction_seconds",
        "seq_n_valid_resubmit_times")]
    specs={
        "B0_strong":BASE,
        "N2_event_counts":BASE+counts,
        "B1_practice_provenance":BASE+counts+provenance,
        "S1_sequence_no_timing":BASE+counts+provenance+temporal_wo_timing,
        "B2_full_sequence":BASE+counts+provenance+temporal,
    }
    null_list=sorted({int(k[:2]) for k in []}) # placeholder, no effect
    null_ids=sorted(set(int(c[4:6]) for c in df if c.startswith("null") and c[4:6].isdigit()))
    if len(null_ids)<5:raise ValueError("Expected multiple negative-control seeds")
    for idx in null_ids:
        null_cols=["null%02d_"%idx+c for c in temporal]
        if any(k not in df for k in null_cols):raise ValueError(f"Missing shuffle {idx}")
        specs["N1_shuffle_%02d"%idx]=BASE+counts+provenance+null_cols
    folds=list(GroupKFold(n_splits=4).split(df,y,groups))
    for tr,va in folds:
        if set(groups[tr]) & set(groups[va]):raise RuntimeError("GROUP LEAKAGE")
    all_metrics={};all_contrasts={}
    for C in (.03,.3):
        predicted={}
        for name,nums in specs.items():
            oof=np.full(len(df),np.nan)
            for tr,va in folds:
                pre=ColumnTransformer([
                    ("num",Pipeline([
                        ("imp",SimpleImputer(strategy="median",add_indicator=True,keep_empty_features=True)),
                        ("scale",StandardScaler())]),nums),
                    ("cat",OneHotEncoder(handle_unknown="ignore"),CATEGORICAL)],
                    sparse_threshold=1)
                Xtr=pre.fit_transform(df.iloc[tr][nums+CATEGORICAL])
                Xva=pre.transform(df.iloc[va][nums+CATEGORICAL])
                model=LogisticRegression(C=C,solver="liblinear",max_iter=250)
                model.fit(Xtr,y[tr])
                oof[va]=model.predict_proba(Xva)[:,1]
            assert np.isfinite(oof).all()
            predicted[name]=oof
            all_metrics[f"C{C}/{name}"]=score(y,oof)
            print("SCORE",C,name,round(all_metrics[f"C{C}/{name}"]["LogLoss"],6),flush=True)
        rng=np.random.default_rng(20261025)
        group_inverse=pd.factorize(groups,sort=True)[0]
        group_number=group_inverse.max()+1
        def contrast(a,b):
            # NOTE: equal session/group weight, not equal individual item weight.
            difference=losses(y,predicted[a])-losses(y,predicted[b])
            g_mean=np.array([np.mean(difference[group_inverse==i]) for i in range(group_number)])
            bootstrap=g_mean[rng.integers(0,group_number,size=(args.boot,group_number))].mean(axis=1)
            return {"improvement_positive_is_better":float(g_mean.mean()),
                    "CI95_task_cluster":[float(x) for x in np.quantile(bootstrap,[.025,.975])]}
        for a,b in [
            ("B0_strong","N2_event_counts"),
            ("B0_strong","B1_practice_provenance"),
            ("N2_event_counts","B1_practice_provenance"),
            ("B1_practice_provenance","S1_sequence_no_timing"),
            ("B1_practice_provenance","B2_full_sequence"),
            ("B0_strong","B2_full_sequence"),
        ]:
            all_contrasts[f"C{C}/{a} -> {b}"]=contrast(a,b)
        sh_loss=np.array([all_metrics[f"C{C}/N1_shuffle_{k:02d}"]["LogLoss"] for k in null_ids])
        actual=all_metrics[f"C{C}/B2_full_sequence"]["LogLoss"]
        b2_vs_null=[contrast("N1_shuffle_%02d"%k,"B2_full_sequence")["improvement_positive_is_better"]
                    for k in null_ids]
        all_contrasts[f"C{C}/B2_vs_{len(null_ids)}_shuffles"]={
            "actual_logloss":actual,"shuffle_median_logloss":float(np.median(sh_loss)),
            "shuffle_min_max_logloss":[float(sh_loss.min()),float(sh_loss.max())],
            "shuffles_worse_than_actual":int((sh_loss>actual).sum()),
            "task_cluster_gain_median":float(np.median(b2_vs_null)),
            "task_cluster_gain_range":[float(min(b2_vs_null)),float(max(b2_vs_null))],
            "warning":"Shuffles preserve event counts and first/final practice provenance; they do not always preserve physiologically possible event transition structure."
        }
        # Preplanned descriptive stratification matched pretest correct vs incorrect.
        for value in (0,1):
            mask=(df.pre_matched==value).to_numpy()
            if mask.sum()<50:continue
            all_contrasts[f"C{C}/B2_vs_B0_matched_pretest_{value}"]={
                "n_items":int(mask.sum()),
                "logloss_delta_item_mean":float(
                    (losses(y,predicted["B0_strong"])-losses(y,predicted["B2_full_sequence"]))[mask].mean())
            }
    summary={
        "status":"EXPLORATORY_DEVELOPMENT_ONLY",
        "primary_metric":"item-level LogLoss; paired task-ID-group bootstrap",
        "n_items":len(df),"n_groups":unique_groups,"n_sessions":df.sid.nunique(),
        "n_cv_folds":len(folds),
        "negative_controls":len(null_ids),
        "feature_dimensions":{"baseline_numeric":len(BASE),
         "practice_provenance":len(provenance),"event_counts":len(counts),
         "temporal":len(temporal)},
        "metrics":all_metrics,"comparisons":all_contrasts,
        "limitations":[
          "Post-test is not a causal learning-gain estimator",
          "The same task ID may occur across tutor arms; all CV folds grouped by task ID",
          "Missing remote files create available-case selection risk",
          "Multiple exploratory models/C; intervals are not selection-adjusted",
          "Reserved task IDs must not be scored during method development",
          "A shuffled event stream need not obey valid pedagogical temporal logic",
          "No direct transcript semantics or human-coded reasoning quality in this experiment"]
    }
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(summary,indent=2),encoding="utf8")
    print("SUMMARY",len(df),"ITEMS",unique_groups,"GROUPS","RESULT",str(out))
if __name__=="__main__":main()
