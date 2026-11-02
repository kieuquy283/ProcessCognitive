#!/usr/bin/env python3
"""Pinned StudentBench 200+80 session-sampling feasibility audit, aggregate only.

This does NOT exclude the 40 private ND1 source sessions and therefore does
NOT create a certified ND2 external test set. No individual-level output.
"""
import argparse
import json
import random
import re
from collections import Counter,defaultdict
from pathlib import Path
from nd2_pipeline import build,source_revision_audit,SEED
BUCKETS=[
 ('coordination',r'\b(next|start|stop|skip|continue|step|explain|again|move on)\b'),
 ('reason_verify',r'\b(because|why|reason|check|verify|correct|right|prove)\b'),
 ('help_clarify',r'\b(help|hint|confused|what|how|clarify|understand)\b'),
 ('feedback',r'\b(ok|got it|thanks|actually|but|no|yes|understood|wrong)\b')]

def preflight(root,seed=SEED):
    if not source_revision_audit(root)['revision_record_matches_expected']:
        raise ValueError('Pinned source revision stamp required')
    episodes=build(root,[])
    by_session=defaultdict(list)
    for episode in episodes:by_session[episode['session_key']].append(episode)
    rnd=random.Random(seed)
    pool=[rnd.choice(v) for _,v in sorted(by_session.items())]
    rnd.shuffle(pool)
    if len(pool)<280:raise ValueError('Fewer than 280 eligible sessions')
    natural=pool[:200]
    remaining={x['episode_id']:x for x in pool[200:]}
    challenge=[];buckets=[]
    for name,pattern in BUCKETS:
        matches=[x for x in remaining.values() if re.search(pattern,x['student_turn'],re.I)]
        rnd.shuffle(matches)
        if len(matches)<20:raise ValueError(f'Bucket {name} contains only {len(matches)} candidates')
        for x in matches[:20]:
            challenge.append(x)
            remaining.pop(x['episode_id'])
        buckets.append({'bucket':name,'available_after_prior_buckets':len(matches),'chosen':20})
    assert len({x['session_key'] for x in natural+challenge})==280
    return {
        'eligible_sessions':len(by_session),
        'eligible_chat_turns':len(episodes),
        'seed':seed,'random_n':len(natural),'challenge_n':len(challenge),
        'random_by_domain':dict(Counter(x['section'] for x in natural)),
        'challenge_by_domain':dict(Counter(x['section'] for x in challenge)),
        'random_by_tutor_arm':dict(Counter(x['tutor_configuration'] for x in natural)),
        'challenge_keyword_buckets':buckets,
        'within_preflight_session_overlap':0,
        'nd1_session_overlap_certified':False,
        'annotation_status':'NONE: Astra/Claude not invoked',
        'interpretation':'Sampling feasibility only; no ND1-source mapping or ND2 labels. Aggregate output only.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',default='data/studentbench')
    p.add_argument('--out',default='results/nd2_sampling_preflight_aggregate.json')
    a=p.parse_args()
    result=preflight(a.data)
    path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
