#!/usr/bin/env python3
"""E9b: low-dimensional skill-coverage diagnostic; development folds only."""
import argparse, collections, csv, json, random
from pathlib import Path
import numpy as np
import pandas as pd
from fastembed import TextEmbedding
from scipy.special import softmax
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from skill_conditioned_e9 import load_data, make_split, normalize

BASE = ["pre_total","theta","matched_pre","pre_skill","pre_subskill",
        "practice_n","practice_good","practice_submissions","student_msgs","tutor_msgs"]
CATS = ["question","arm","form","skill","subskill","difficulty"]
SPECS = {
    "baseline":BASE,
    "curriculum_size":BASE+["active_concepts","plan_concepts"],
    "coverage_relevance":BASE+["active_concepts","plan_concepts","max_plan","max_touched"],
    "aligned_activity":BASE+["active_concepts","plan_concepts","max_plan","max_touched","weighted_student_msgs","weighted_tutor_msgs"],
    "wrong_activity":BASE+["active_concepts","plan_concepts","max_plan","max_touched","wrong_student_msgs","weighted_tutor_msgs"],
}

def build_items(sessions, bank, folds, model, cache):
    ids=sorted(folds)
    subs=sorted(set(q["subskill"] for q in bank.values()))
    labels=["GRE Quantitative mathematics subskill: "+s for s in subs]
    concepts=[(i,c) for i in ids for c in sessions[i]["concepts"]]
    labels+=["GRE mathematics concept: "+c["name"] for i,c in concepts]
    enc=TextEmbedding(model_name=model,cache_dir=str(cache),threads=2)
    X=normalize(np.asarray(list(enc.embed(labels,batch_size=64)),dtype=np.float32))
    queries=X[:len(subs)]; concept_vectors=X[len(subs):]
    query_index={s:i for i,s in enumerate(subs)}
    by_session=collections.defaultdict(list)
    for j,(i,c) in enumerate(concepts):by_session[i].append(j)
    records=[]
    for sid,i in enumerate(ids):
        s=sessions[i];p=s["profile"]
        all_concepts=by_session[i]
        active=[j for j in all_concepts if concepts[j][1]["student_messages"]>0]
        matched={}
        pre_skill,pre_sub=collections.defaultdict(list),collections.defaultdict(list)
        for row in s["pre"]:
            question=bank.get(row["question_id"])
            if question and row["is_correct"] in ("0","1"):
                correct=int(row["is_correct"])
                matched[question["pair"]]=correct
                pre_skill[question["skill"]].append(correct)
                pre_sub[question["subskill"]].append(correct)
        for row in s["post"]:
            question=bank.get(row["question_id"])
            if not question or row["is_correct"] not in ("0","1"):continue
            q=queries[query_index[question["subskill"]]]
            allsim=concept_vectors[all_concepts]@q if all_concepts else np.zeros(0)
            scores=concept_vectors[active]@q if active else np.zeros(0)
            if active:
                weight=softmax(scores/.1)
                stu=np.asarray([concepts[j][1]["student_messages"] for j in active])
                tut=np.asarray([concepts[j][1]["tutor_messages"] for j in active])
                wrong=stu.copy()
                random.Random("wrong-"+p["student_id"]).shuffle(wrong)
                weighted_stu=float(np.log1p(weight@stu))
                weighted_tut=float(np.log1p(weight@tut))
                weighted_wrong=float(np.log1p(weight@wrong))
            else:weighted_stu=weighted_tut=weighted_wrong=0.0
            sk=pre_skill[question["skill"]];sub=pre_sub[question["subskill"]]
            records.append(dict(sid=sid,fold=folds[i],y=int(row["is_correct"]),
                question=question["question_id"],skill=question["skill"],
                subskill=question["subskill"],difficulty=question["difficulty"],
                arm=p["ai_model_preset_id"],form=p["assessment_form_order"],
                pre_total=p["pretest_score_points"],theta=p.get("pretest_irt_theta"),
                matched_pre=matched.get(question["pair"],np.nan),
                pre_skill=float(np.mean(sk)) if sk else np.nan,
                pre_subskill=float(np.mean(sub)) if sub else np.nan,
                practice_n=p["practice_problems_answered_count"],
                practice_good=p["practice_problems_final_correct_count"],
                practice_submissions=p["practice_answer_submissions_count"],
                student_msgs=p["student_messages_sent_to_tutor"],
                tutor_msgs=p["ai_tutor_messages_sent_to_student"],
                active_concepts=len(active),plan_concepts=len(all_concepts),
                max_plan=float(allsim.max()) if len(allsim) else 0.,
                max_touched=float(scores.max()) if len(scores) else 0.,
                weighted_student_msgs=weighted_stu,weighted_tutor_msgs=weighted_tut,
                wrong_student_msgs=weighted_wrong))
    return pd.DataFrame(records)

def evaluate(df,C):
    y=df.y.to_numpy();pred={}
    for name,nums in SPECS.items():
        oof=np.zeros(len(df))
        for fold in sorted(df.fold.unique()):
            train=np.flatnonzero((df.fold!=fold).to_numpy())
            val=np.flatnonzero((df.fold==fold).to_numpy())
            pre=ColumnTransformer([
                ("num",Pipeline([("impute",SimpleImputer(strategy="median")),("scale",StandardScaler())]),nums),
                ("cat",OneHotEncoder(handle_unknown="ignore"),CATS)],sparse_threshold=1.)
            x=pre.fit_transform(df.iloc[train][nums+CATS])
            xv=pre.transform(df.iloc[val][nums+CATS])
            mdl=LogisticRegression(C=C,solver="liblinear",max_iter=250)
            mdl.fit(x,y[train]);oof[val]=mdl.predict_proba(xv)[:,1]
        pred[name]=oof
    results={k:dict(logloss=float(log_loss(y,p)),brier=float(brier_score_loss(y,p)),
                    auc=float(roc_auc_score(y,p))) for k,p in pred.items()}
    ll=lambda p:-(y*np.log(np.clip(p,1e-8,1-1e-8))+(1-y)*np.log(np.clip(1-p,1e-8,1-1e-8)))
    pairs=[("baseline","curriculum_size"),("baseline","coverage_relevance"),
           ("coverage_relevance","aligned_activity"),("wrong_activity","aligned_activity"),
           ("baseline","aligned_activity")]
    comparison={}
    for a,b in pairs:
        d=ll(pred[a])-ll(pred[b])
        ses=pd.DataFrame(dict(sid=df.sid,d=d)).groupby("sid").d.mean().to_numpy()
        draws=np.random.default_rng(23).choice(ses,size=(1600,len(ses)),replace=True).mean(axis=1)
        comparison[a+"_to_"+b]=dict(delta=float(ses.mean()),
                                     ci95=np.quantile(draws,[.025,.975]).tolist())
    return dict(models=results,contrasts=comparison)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data",required=True,type=Path)
    p.add_argument("--output",default=Path("results/e9_coverage.json"),type=Path)
    p.add_argument("--per-arm",default=48,type=int)
    p.add_argument("--model",default="sentence-transformers/all-MiniLM-L6-v2")
    p.add_argument("--cache-dir",default=".cache/fastembed")
    a=p.parse_args()
    sessions,bank=load_data(a.data,a.per_arm)
    folds,held=make_split(sessions)
    if len(folds)<80:raise ValueError("Too few development sessions")
    df=build_items(sessions,bank,folds,a.model,a.cache_dir)
    result=dict(n_loaded=len(sessions),n_dev=len(folds),n_holdout_unopened=len(held),
                n_dev_items=len(df),note="Exploratory: concept-title relevance not human validated",
                regularization={str(C):evaluate(df,C) for C in (.03,.3)})
    a.output.parent.mkdir(exist_ok=True,parents=True)
    a.output.write_text(json.dumps(result,indent=2),encoding="utf8")
    print(json.dumps(result,indent=2))

if __name__=="__main__":main()
