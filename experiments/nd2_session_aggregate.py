#!/usr/bin/env python3
"""Produce a LOCAL-ONLY session aggregate CSV for the ND2 weighting experiment.

Session rows may be participant-level metadata; NEVER commit the output CSV.
"""
import argparse
import csv
from pathlib import Path

ARMS=('gpt-5.5-high','opus-5-high','gemini-3.1-pro-high')
DOMAINS=('gre_quant','gre_verbal')
FIELDS=('domain','arm','task_id','events','student_turns','long_context_turns','practice_submissions')

def audit_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream)
        if not {'event_type','trajectory_position','content'}.issubset(reader.fieldnames or []):
            raise ValueError(f'Missing trajectory fields in {path}')
        events=sorted(reader,key=lambda x:int(x['trajectory_position']))
    positions=[int(e['trajectory_position']) for e in events]
    if len(positions)!=len(set(positions)):
        raise ValueError(f'Duplicate trajectory positions in {path}')
    pending=[]
    turns=long=practice=0
    for event in events:
        kind=event['event_type']
        text=(event['content'] or '').strip()
        if kind=='ai_tutor_message' and text:
            pending.append(text)
        elif kind=='student_message' and text:
            turns+=1
            long+=int(len('\n\n'.join(pending))>950)
            pending=[]
        elif kind=='practice_answer_submitted':
            practice+=1
    return {'events':len(events),'student_turns':turns,
            'long_context_turns':long,'practice_submissions':practice}

def run(data,per_arm=4):
    base=Path(data)/'1_main_leaderboard_data'
    records=[]
    for domain in DOMAINS:
        for arm in ARMS:
            pattern=f'{domain}/ai_arm_{arm}/task_id_*/ai_tutoring_data/student_ai_tutor_interaction_trajectory.csv'
            paths=sorted(base.glob(pattern))[:per_arm]
            if len(paths)<per_arm:
                raise FileNotFoundError(f'{domain}/{arm}: need {per_arm}, got {len(paths)}')
            for path in paths:
                records.append({'domain':domain.split('_')[-1], 'arm':arm,
                    'task_id':path.parent.parent.name.removeprefix('task_id_'),
                    **audit_csv(path)})
    return records

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',default='data/studentbench')
    p.add_argument('--per-arm',type=int,default=4)
    p.add_argument('--out',default='annotation_work/nd2/context_session_aggregate_private.csv')
    a=p.parse_args()
    if a.per_arm<1:p.error('--per-arm must be >= 1')
    records=run(a.data,a.per_arm)
    target=Path(a.out);target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS)
        writer.writeheader();writer.writerows(records)
    print(f'Created local-only aggregate: {target}; sessions={len(records)}; turns={sum(row["student_turns"] for row in records)}')
