#!/usr/bin/env python3
"""Aggregate-only audit of ND1 label coupling. ND1 is NOT ND2 holdout evidence.

Requires local (ignored) ND1 Astra + Claude annotation CSVs. Does not emit episode rows.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import fisher_exact, binomtest
from sklearn.metrics import accuracy_score, f1_score, mutual_info_score

ACT=('AK','AN','CQ','HR','OT','RE','VE')
UPT=('AC','AP','NO','NR','UN')

def mcnemar(pa,pb):
    a=int(np.sum(pa & ~pb));b=int(np.sum(pb & ~pa))
    return {'first_only_correct':a,'second_only_correct':b,
            'p_exact_unadjusted':float(binomtest(min(a,b),a+b,p=.5).pvalue) if a+b else 1.0}

def loocv_reference_conditional(a):
    result=[]
    for i in range(len(a)):
        train=a.drop(index=i)
        matches=train.loc[train.primary_act==a.iloc[i].primary_act,'feedback_uptake']
        if matches.empty: matches=train.feedback_uptake
        counts=matches.value_counts()
        result.append(sorted(counts[counts==max(counts)].index)[0])
    return np.asarray(result)

def audit(astra,claude,permutations=10000,seed=20261028):
    a=pd.read_csv(astra,dtype=str,keep_default_na=False)
    c=pd.read_csv(claude,dtype=str,keep_default_na=False)
    if len(a)!=40 or len(c)!=40 or a.episode_id.tolist()!=c.episode_id.tolist():
        raise ValueError('ND1 requires 40 aligned episode IDs')
    result={'n':40,'reference':'Astra conventional reference; NOT independently validated human ground truth',
            'evidence':'real ND1 pilot reanalysis; not ND2 external sample'}
    for col,labels in [('primary_act',ACT),('feedback_uptake',UPT)]:
        if not a[col].isin(labels).all() or not c[col].isin(labels).all():
            raise ValueError('Invalid categorical label '+col)
        counts=a[col].value_counts().reindex(labels,fill_value=0)
        observed=[label for label in labels if counts[label]]
        majority=counts.idxmax()
        baseline=np.repeat(majority,len(a))
        true=a[col].to_numpy(); pred=c[col].to_numpy()
        result[col]={
            'support_by_label':counts.astype(int).to_dict(),
            'claude_accuracy':float(accuracy_score(true,pred)),
            'claude_macro_f1_observed':float(f1_score(true,pred,labels=observed,average='macro',zero_division=0)),
            'claude_macro_f1_fixed_all_classes_sensitivity':float(f1_score(true,pred,labels=labels,average='macro',zero_division=0)),
            'majority_label_from_test_distribution':majority,
            'descriptive_majority_accuracy_in_sample':float(accuracy_score(true,baseline)),
            'claude_vs_majority_exploratory':mcnemar(true==pred,true==baseline)}
    act=a.primary_act.to_numpy(); uptake=a.feedback_uptake.to_numpy()
    mi=float(mutual_info_score(act,uptake))
    rng=np.random.default_rng(seed)
    ge=sum(mutual_info_score(act,rng.permutation(uptake))>=mi for _ in range(permutations))
    oracle=loocv_reference_conditional(a)
    c_u=(c.feedback_uptake.to_numpy()==uptake);o_u=(oracle==uptake)
    p_correct=(c.primary_act.to_numpy()==act)
    result['relationship']={
        'astra_act_uptake_mutual_information_nats':mi,
        'permutation_p_exploratory':float((ge+1)/(permutations+1)),
        'permutations':permutations,'seed':seed,
        'loocv_uptake_from_astra_act_accuracy_oracle':float(o_u.mean()),
        'claude_uptake_vs_oracle_mcnemar':mcnemar(c_u,o_u),
        'caution':'Astra primary act is provided as an ORACLE to the conditional rule at test time, not a deployable model.'}
    cells=[int(np.sum(p_correct & c_u)),int(np.sum(p_correct & ~c_u)),
           int(np.sum(~p_correct & c_u)),int(np.sum(~p_correct & ~c_u))]
    result['cross_dimension_error_coupling']={
        'both_correct':cells[0],'only_primary_correct':cells[1],
        'only_uptake_correct':cells[2],'both_incorrect':cells[3],
        'fisher_exact_p_exploratory':float(fisher_exact([[cells[0],cells[1]],[cells[2],cells[3]]])[1])}
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--astra',required=True);p.add_argument('--claude',required=True)
    p.add_argument('--out',default='annotation_work/nd2/nd1_label_dependency_private.json')
    args=p.parse_args()
    data=audit(args.astra,args.claude)
    target=Path(args.out);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(data,indent=2),encoding='utf-8')
    print(json.dumps(data,indent=2))
