#!/usr/bin/env python3
"""Aggregate-only data audit for pinned StudentBench GRE trajectories.

Do not commit participant-level records, raw tutoring text, or individual outputs.
The default subset is a deterministic convenience sample, NOT representative.
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

ARMS = ('ai_arm_gpt-5.5-high','ai_arm_opus-5-high','ai_arm_gemini-3.1-pro-high')
DOMAINS = ('gre_quant','gre_verbal')
REVISION = '304c8d63c726e72b60510bba3a44454fc0726721'

def audit_one(path):
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if not {'event_type','trajectory_position','content'}.issubset(reader.fieldnames or []):
            raise ValueError(f'Missing fields in {path}')
        rows=list(reader)
    events=sorted(rows,key=lambda r:int(r['trajectory_position']))
    if len({int(r['trajectory_position']) for r in events})!=len(events):
        raise ValueError(f'Duplicate trajectory_position: {path}')
    counts=Counter(r['event_type'] for r in events)
    previous=''
    tutor=[]
    turns=long_context=first=no_context=maximum=0
    for e in events:
        kind=e['event_type']
        content=(e.get('content') or '').strip()
        if kind=='student_message' and content:
            turns+=1
            size=len('\n\n'.join(tutor))
            long_context+=int(size>950)
            first+=int(not previous)
            no_context+=int(size==0)
            maximum=max(maximum,size)
            previous=content
            tutor=[]
        elif kind=='ai_tutor_message' and content:
            tutor.append(content)
    return {'events':len(rows),'student_turns':turns,
            'practice_submissions':counts['practice_answer_submitted'],
            'long_context_turns':long_context,
            'missing_previous_turns':first,
            'no_tutor_context_turns':no_context,
            'max_context_chars':maximum}

def run(data,per_arm):
    out={}
    root=Path(data)/'1_main_leaderboard_data'
    for domain in DOMAINS:
        acc=Counter()
        by_arm={}
        for arm in ARMS:
            paths=sorted((root/domain/arm).glob(
                'task_id_*/ai_tutoring_data/student_ai_tutor_interaction_trajectory.csv'))[:per_arm]
            if len(paths)!=per_arm:
                raise FileNotFoundError(f'{domain}/{arm}: expected {per_arm} trajectories, got {len(paths)}')
            part=Counter()
            for path in paths:
                record=audit_one(path)
                part.update({k:v for k,v in record.items() if k!='max_context_chars'})
            part['sessions']=len(paths)
            by_arm[arm]=dict(part)
            acc.update(part)
        out[domain]=dict(acc)
        out[domain]['by_arm']=by_arm
        out[domain]['context_gt950_rate']=acc['long_context_turns']/acc['student_turns'] if acc['student_turns'] else None
    total=Counter()
    for domain in DOMAINS:
        total.update({k:v for k,v in out[domain].items() if isinstance(v,int)})
    out['overall']=dict(total)
    out['overall']['context_gt950_rate']=total['long_context_turns']/total['student_turns'] if total['student_turns'] else None
    out['metadata']={'source_revision':REVISION,'per_arm':per_arm,
                     'sampling':'first N sorted trajectories per 3 selected AI arms per GRE domain',
                     'limitation':'non-probability technical audit; no labels or model predictions'}
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',default='data/studentbench')
    p.add_argument('--per-arm',type=int,default=4)
    p.add_argument('--output',default='results/nd2_dataset_audit.json')
    a=p.parse_args()
    if a.per_arm<1:p.error('--per-arm must be positive')
    out=run(a.data,a.per_arm)
    path=Path(a.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps(out,indent=2))

if __name__=='__main__':
    main()
