#!/usr/bin/env python3
"""Audit pinned official StudentBench GRE AI-tutor session frame (aggregates ONLY).

No raw text, row-level metadata, labels or participant IDs are emitted. Does
not annotate ND2 or establish independence from the ND1 pilot.
"""
import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

REV='304c8d63c726e72b60510bba3a44454fc0726721'
PATTERNS={
 'coordination':r'\b(next|start|stop|skip|continue|step|explain|again|move on)\b',
 'reason_verify':r'\b(because|why|reason|check|verify|correct|right|prove)\b',
 'help_clarify':r'\b(help|hint|confused|what|how|clarify|understand)\b',
 'feedback':r'\b(ok|got it|thanks|actually|but|no|yes|understood|wrong)\b',
}
REGEX={k:re.compile(v,re.I) for k,v in PATTERNS.items()}

def audit_one(path):
    with path.open(encoding='utf-8-sig',newline='') as f:
        r=csv.DictReader(f)
        if not {'event_type','trajectory_position','content'}.issubset(r.fieldnames or []):
            raise ValueError('Missing event columns')
        events=list(r)
    positions=[int(e['trajectory_position']) for e in events]
    if len(set(positions))!=len(positions):raise ValueError('Duplicate trajectory positions')
    events.sort(key=lambda e:int(e['trajectory_position']))
    counts=Counter({'files':1,'events':len(events)})
    prior=[];turns=long=practice=0
    found={k:False for k in REGEX}
    for e in events:
        typ=e['event_type'];s=(e['content'] or '').strip()
        if typ=='student_message' and s:
            turns+=1
            long+=int(len('\n\n'.join(prior))>950)
            for k,regex in REGEX.items():
                if regex.search(s):found[k]=True
            prior=[]
        elif typ=='ai_tutor_message' and s:
            prior.append(s)
        elif typ=='practice_answer_submitted':
            practice+=1
    counts.update({'student_turns':turns,'long_context_turns':long,
                   'practice_answer_submissions':practice})
    if turns:
        counts['eligible_sessions']+=1
        for k,yes in found.items():
            if yes:counts['session_keyword_'+k]+=1
    else:counts['zero_student_turn_sessions']+=1
    return counts

def run(root):
    root=Path(root);stamp=root/'.studentbench_revision'
    if not stamp.is_file() or stamp.read_text(encoding='utf-8').strip()!=REV:
        raise ValueError('Pinned release stamp required. Use the verified downloader.')
    base=root/'1_main_leaderboard_data';by_group=defaultdict(Counter);directory_count=Counter()
    for domain in ('gre_quant','gre_verbal'):
        for folder in (base/domain).glob('ai_arm_*/task_id_*'):
            if folder.is_dir():directory_count[domain]+=1
        for file in (base/domain).glob('ai_arm_*/task_id_*/ai_tutoring_data/student_ai_tutor_interaction_trajectory.csv'):
            arm=file.parents[2].name
            try:by_group[(domain,arm)].update(audit_one(file))
            except (ValueError,KeyError,csv.Error):
                by_group[(domain,arm)]['bad_file_sessions']+=1
    overall=Counter()
    groups=[]
    for (domain,arm),c in sorted(by_group.items()):
        overall.update(c)
        groups.append({'domain':domain,'arm':arm,**dict(c)})
    n=overall['files'];turns=overall['student_turns']
    return {
        'source':'handshake-ai-research/studentbench','pinned_revision':REV,
        'directory_count_by_domain':dict(directory_count),
        'overall_counts':dict(overall),'by_domain_and_tutor_arm':groups,
        'audit':{
            'source_directories':sum(directory_count.values()),
            'readable_source_sessions':n,
            'incomplete_or_unreadable_sessions':sum(directory_count.values())-n,
            'eligible_sessions_with_student_chat':overall['eligible_sessions'],
            'eligible_280_sessions_available':overall['eligible_sessions']>=280,
            'turn_weighted_context_gt950':overall['long_context_turns']/turns if turns else None},
        'interpretation':'Eligibility and lexical challenge capacity, not behavioral labels or ND2 performance',
        'cautions':['No verified ND1 session mapping','Keyword groups are not labeled classes',
                    'No new Astra/Claude annotations','No raw participant data emitted']
    }

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',default='data/studentbench')
    p.add_argument('--out',default='results/nd2_full_frame_aggregate.json')
    a=p.parse_args()
    result=run(a.data)
    output=Path(a.out);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
