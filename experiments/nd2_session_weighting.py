#!/usr/bin/env python3
"""Compare session- and turn-weighted 950-character context exposure.

Requires aggregate rows per session, NEVER participant-level transcripts.
The result is descriptive for a convenience sample, not population inference.
"""
import argparse
import json
import numpy as np
import pandas as pd

REQUIRED={'domain','arm','task_id','student_turns','long_context_turns'}

def summarize(df,rng,bootstrap=10000):
    n=df['student_turns'].to_numpy(dtype=float)
    long=df['long_context_turns'].to_numpy(dtype=float)
    if (n<1).any() or (long<0).any() or (long>n).any():
        raise ValueError('Invalid session counts')
    per_session=long/n
    turn_rate=long.sum()/n.sum()
    session_rate=per_session.mean()
    draws=rng.integers(0,len(n),size=(bootstrap,len(n)))
    long_b=long[draws];n_b=n[draws]
    diff_b=(long_b/n_b).mean(axis=1)-long_b.sum(axis=1)/n_b.sum(axis=1)
    return {
        'sessions':len(n),'student_turns':int(n.sum()),
        'turn_weighted_rate':float(turn_rate),
        'session_weighted_rate':float(session_rate),
        'difference_percentage_points':float(100*(session_rate-turn_rate)),
        'descriptive_session_bootstrap_diff_95pct_pp':np.percentile(100*diff_b,[2.5,97.5]).tolist(),
        'turns_min':int(n.min()),'turns_max':int(n.max()),
        'turn_weight_kish_effective_sessions':float(n.sum()**2/(n*n).sum()),
    }

def run(input_path,bootstrap=10000,seed=20261028):
    df=pd.read_csv(input_path)
    if not REQUIRED.issubset(df.columns):
        raise ValueError('Required columns missing: '+repr(REQUIRED-set(df.columns)))
    if df.duplicated(subset=['domain','arm','task_id']).any():
        raise ValueError('Duplicate session rows')
    rng=np.random.default_rng(seed)
    result={'warning':'Convenience sample audit; not representative ND2 model performance.',
            'seed':seed,'iterations':bootstrap}
    for domain,group in [('all',df),('quant',df[df.domain=='quant']),('verbal',df[df.domain=='verbal'])]:
        result[domain]=summarize(group,rng,bootstrap)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('aggregate_csv')
    p.add_argument('--iterations',type=int,default=10000)
    p.add_argument('--seed',type=int,default=20261028)
    a=p.parse_args()
    if a.iterations<100:p.error('--iterations must be >= 100')
    print(json.dumps(run(a.aggregate_csv,a.iterations,a.seed),indent=2))
