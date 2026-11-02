"""Synthetic-only ND2 evaluator validation tests, NOT empirical model evaluation."""
import tempfile
from pathlib import Path
import pandas as pd
from nd2_pipeline import COLUMNS, INPUT, check, wilson

def expect_fail(fn,msg):
    try:fn()
    except ValueError as e:
        assert msg.lower() in str(e).lower(),(msg,e)
        return
    raise AssertionError('Expected ValueError: '+msg)

def test_guards():
    assert wilson(0,0)==[None,None]
    lo,hi=wilson(32,40)
    assert 0.65<lo<0.66 and 0.89<hi<0.90
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)
        d={c:['']*280 for c in COLUMNS}
        d['episode_id']=[f'PRIVATE-SYNTH-{i}' for i in range(280)]
        d['student_turn']=['Synthetic student test message']*280
        d['primary_act']=['AK']*280;d['feedback_uptake']=['AP']*280
        d['annotation_rationale']=['synthetic reason']*280;d['confidence']=['high']*280
        a=pd.DataFrame(d)
        a.to_csv(p/'a.csv',index=False);a.to_csv(p/'b.csv',index=False)
        a[INPUT].to_csv(p/'s.csv',index=False)
        check(p/'a.csv',p/'b.csv',p/'s.csv')
        b=a.copy();b.at[0,'student_turn']='MISMATCH';b.to_csv(p/'b.csv',index=False)
        expect_fail(lambda:check(p/'a.csv',p/'b.csv',p/'s.csv'),'Immutable input mismatch')
        b=a.copy();b.at[0,'primary_act']='INVALID';b.to_csv(p/'b.csv',index=False)
        expect_fail(lambda:check(p/'a.csv',p/'b.csv',p/'s.csv'),'Invalid/missing')
        b=a.copy();b.at[0,'confidence']='';b.to_csv(p/'b.csv',index=False)
        expect_fail(lambda:check(p/'a.csv',p/'b.csv',p/'s.csv'),'Invalid/missing')
        b=a.copy();b.loc[1,'episode_id']=b.loc[0,'episode_id'];b.to_csv(p/'b.csv',index=False)
        expect_fail(lambda:check(p/'a.csv',p/'b.csv',p/'s.csv'),'Duplicate')
    print('PASS: immutable fields, invalid labels, duplicate IDs and Wilson CI (synthetic only).')

if __name__=='__main__':test_guards()
