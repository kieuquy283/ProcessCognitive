#!/usr/bin/env python3
"""Recover pseudonymous ND1 session mapping from official StudentBench locally.

Matches require contextual corroboration, not just repeated short chat text.
Diagnostics and mapping are PRIVATE; never commit participant/session records.
"""
import argparse
import csv
import hashlib
import json
import unicodedata
from collections import defaultdict
from pathlib import Path

def norm(text):
    return ' '.join(unicodedata.normalize('NFKC',text or '').split())

def session_key(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()[:20]

def rows(path):
    with open(path,encoding='utf-8-sig',newline='') as stream:
        return list(csv.DictReader(stream))

def supporting_evidence(ref,candidate):
    original=norm(ref.get('tutor_context',''))
    tutor=norm(candidate['tutor'])
    previous=norm(ref.get('previous_student_excerpt',''))
    source_prev=norm(candidate['previous'])
    context=bool(len(original)>=40 and
                 (original[:min(80,len(original))] in tutor or
                  tutor[:min(80,len(tutor))] in original))
    prev=bool(previous and len(previous)>=8 and
              (previous==source_prev or previous[:min(60,len(previous))] in source_prev))
    return context,prev

def match(data,nd1_path,out_file):
    reference=rows(nd1_path)
    if not reference or len({r['episode_id'] for r in reference})!=len(reference):
        raise ValueError('Empty or duplicate ND1 episode IDs')
    wanted=defaultdict(list)
    for record in reference:
        wanted[norm(record['student_turn'])].append(record)
    matching=defaultdict(list)
    root=Path(data)/'1_main_leaderboard_data'
    paths=sorted(root.glob('gre_*/ai_arm_*/task_id_*/ai_tutoring_data/student_ai_tutor_interaction_trajectory.csv'))
    if not paths:raise FileNotFoundError('No official StudentBench trajectory files found')
    for path in paths:
        section=path.parents[3].name; arm=path.parents[2].name; task=path.parents[1].name
        key=session_key(f'{section}/{arm}/{task}')
        events=sorted(rows(path),key=lambda event:int(event['trajectory_position']))
        previous='';tutor=[]
        for event in events:
            kind=event['event_type'];text=(event.get('content') or '').strip()
            if kind=='student_message' and text:
                exact=norm(text)
                if exact in wanted:
                    candidate={'session_key':key,'position':event['trajectory_position'],
                               'previous':previous,'tutor':'\n\n'.join(tutor)}
                    for ref in wanted[exact]:
                        c,p=supporting_evidence(ref,candidate)
                        matching[ref['episode_id']].append(
                            {'session_key':key,'context_matched':c,'previous_matched':p})
                previous=text;tutor=[]
            elif kind=='ai_tutor_message' and text:tutor.append(text)
    diagnostics=[];confirmed=[]
    for row in reference:
        eid=row['episode_id'];candidates=matching[eid]
        strong=[c for c in candidates if c['context_matched'] or c['previous_matched']]
        status='resolved' if len(strong)==1 else ('ambiguous' if len(strong)>1 else 'unresolved')
        diagnostics.append({'episode_id':eid,'candidate_count':len(candidates),
                            'strong_count':len(strong),'status':status})
        if status=='resolved':confirmed.append({'episode_id':eid,'session_key':strong[0]['session_key']})
    out=Path(out_file);out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=['episode_id','candidate_count','strong_count','status'])
        writer.writeheader();writer.writerows(diagnostics)
    mapping=out.with_name('ND1_sessions_private.csv')
    if len(confirmed)==len(reference):
        with mapping.open('w',newline='',encoding='utf-8') as stream:
            writer=csv.DictWriter(stream,fieldnames=['episode_id','session_key'])
            writer.writeheader();writer.writerows(confirmed)
    else:
        mapping.unlink(missing_ok=True)
    return {'scanned_sessions':len(paths),'nd1_rows':len(reference),
            'resolved':len(confirmed),
            'ambiguous':sum(x['status']=='ambiguous' for x in diagnostics),
            'unresolved':sum(x['status']=='unresolved' for x in diagnostics),
            'private_mapping_written':mapping.is_file(),
            'limitation':'Automated matches require independent provenance review before external-test claims.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',default='data/studentbench')
    parser.add_argument('--nd1',required=True)
    parser.add_argument('--out',default='annotation_work/nd2/ND1_source_match_audit_private.csv')
    options=parser.parse_args()
    print(json.dumps(match(options.data,options.nd1,options.out),indent=2))
