#!/usr/bin/env python3
"""Pure synthetic regression tests of E14's locked internal-test controls."""
import numpy as np
import pandas as pd
from e14_locked_holdout import null_shuffle_dev_by_task,contrast,logloss_individual

def main():
    frame=pd.DataFrame({
        "group":["a","a","b","b","c","c","d","d"],
        "sid":[0,0,1,1,2,2,3,3],
        "y":[0,1,1,0,0,1,1,0],
        "prov_repeated_fraction":[.1,.1,.2,.2,.3,.3,.4,.4],
        "prov_avg_attempts":[1,1,2,2,3,3,4,4],
        "prov_max_attempts":[1,1,2,2,3,3,4,4],
        "prov_n_attempted":[6,6,7,7,8,8,9,9],
        "pre_total":[11]*8
    })
    cols=["prov_repeated_fraction","prov_avg_attempts","prov_max_attempts","prov_n_attempted"]
    shuffle=null_shuffle_dev_by_task(frame,cols,seed=20261026)
    assert (shuffle["y"]==frame["y"]).all()
    assert (shuffle["pre_total"]==frame["pre_total"]).all()
    original=sorted(tuple(row) for row in frame.drop_duplicates("group")[cols].to_numpy())
    randomized=sorted(tuple(row) for row in shuffle.drop_duplicates("group")[cols].to_numpy())
    assert original==randomized,"Shuffle must conserve entire source-vector multiset"
    assert shuffle.groupby("group")[cols[0]].nunique().max()==1
    p=np.asarray([.2,.8,.7,.3,.1,.9,.65,.35])
    delta=contrast(p,p,frame.y.to_numpy(),frame.group.to_numpy(),np.random.default_rng(0),boot=300)
    assert delta["positive_means_candidate_better"]==0
    assert delta["ci95_task_bootstrap"]==[0,0]
    print("PASS E14: shuffle preserves joint task-level vectors, original labels and fixed zero-delta bootstrap")

if __name__=="__main__":main()
