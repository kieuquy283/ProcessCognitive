#!/usr/bin/env python3
"""Reproduce ND1 agreement against frozen Astra reference labels.

Run locally only. Inputs contain StudentBench dialogue, and row-level outputs
contain episode identifiers: never commit these files to GitHub.
"""
import argparse
import json
from pathlib import Path
from scipy.stats import binomtest
import pandas as pd
from sklearn.metrics import cohen_kappa_score, confusion_matrix, f1_score, precision_recall_fscore_support

SOURCE = ['episode_id','previous_student_excerpt','tutor_context','student_turn']
SCHEMA = SOURCE + ['primary_act','feedback_uptake','annotation_rationale','confidence']
LABELS = {'primary_act':['AK','AN','CQ','HR','OT','RE','VE'],
          'feedback_uptake':['AC','AP','NO','NR','UN']}
CONFIDENCE = {'high','medium','low'}

def load(path):
    frame = pd.read_csv(path, dtype=str, keep_default_na=False, encoding='utf-8-sig')
    if list(frame.columns) != SCHEMA or len(frame) != 40:
        raise ValueError(f'{path}: expected exactly 40 rows and the 8 ND1 fields in order')
    if frame.episode_id.eq('').any() or frame.episode_id.duplicated().any():
        raise ValueError(f'{path}: empty or duplicate episode_id')
    if frame.annotation_rationale.str.strip().eq('').any():
        raise ValueError(f'{path}: missing annotation rationale')
    for field, allowed in {**LABELS, 'confidence':list(CONFIDENCE)}.items():
        if not frame[field].isin(allowed).all():
            raise ValueError(f'{path}: unexpected {field} value')
    return frame

def holm(pvals):
    adjusted = [0.0] * len(pvals)
    previous = 0.0
    for i, idx in enumerate(sorted(range(len(pvals)), key=lambda j: pvals[j])):
        previous = max(previous, (len(pvals)-i)*pvals[idx])
        adjusted[idx] = min(1.0, previous)
    return adjusted

def exact_p(left, right):
    left_only = int((left & ~right).sum())
    right_only = int((~left & right).sum())
    discordant = left_only+right_only
    p = binomtest(min(left_only,right_only),discordant,0.5).pvalue if discordant else 1.0
    return {'claude_only_correct':left_only,'gemini_only_correct':right_only,'exact_p':float(p)}

def evaluate(a,b,field):
    names=LABELS[field]
    supported=[x for x in names if x in set(a[field])]
    precision,recall,f1,support=precision_recall_fscore_support(a[field],b[field],labels=names,zero_division=0)
    counts=pd.DataFrame({'label':names,'support_astra':support,
                         'n_predicted':[int((b[field]==x).sum()) for x in names],
                         'precision':precision,'recall':recall,'f1':f1})
    score={'accuracy':float((a[field]==b[field]).mean()),
           'macro_f1_supported':float(f1_score(a[field],b[field],labels=supported,average='macro',zero_division=0)),
           'cohens_kappa':float(cohen_kappa_score(a[field],b[field]))}
    return score,counts

def main():
    cli=argparse.ArgumentParser(description=__doc__)
    root=Path('annotation_work/nd1')  # gitignored in this repository
    cli.add_argument('--astra',type=Path,default=root/'ND1_Astra_A_40.csv')
    cli.add_argument('--claude',type=Path,default=root/'ND1_ClaudeOpus55_B_40.csv')
    cli.add_argument('--gemini',type=Path,default=root/'ND1_Gemini4Argon_B_40.csv')
    cli.add_argument('--outdir',type=Path,default=Path('results/nd1'))  # gitignored
    args=cli.parse_args()
    a,c,g=load(args.astra),load(args.claude),load(args.gemini)
    for who,other in [('Claude',c),('Gemini',g)]:
        for field in SOURCE:
            if not a[field].equals(other[field]):
                raise ValueError(f'{who}: mismatch in {field}; cannot compare aligned rows')

    args.outdir.mkdir(parents=True,exist_ok=True)
    metrics={}; per_class=[]
    for who,pred in [('Claude',c),('Gemini',g)]:
        metrics[who]={}
        for field in LABELS:
            score,table=evaluate(a,pred,field)
            metrics[who][field]=score
            table.insert(0,'annotator',who)
            table.insert(1,'dimension',field)
            per_class.append(table)
        joint=(a.primary_act==pred.primary_act)&(a.feedback_uptake==pred.feedback_uptake)
        metrics[who]['joint_exact_accuracy']=float(joint.mean())
        metrics[who]['joint_correct']=int(joint.sum())
    pd.concat(per_class,ignore_index=True).to_csv(args.outdir/'per_class.csv',index=False)
    for field,names in LABELS.items():
        matrix=confusion_matrix(a[field],c[field],labels=names)
        pd.DataFrame(matrix,index=names,columns=names).rename_axis(index='Astra',columns='Claude').to_csv(args.outdir/f'{field}_confusion.csv')

    c_joint=(a.primary_act==c.primary_act)&(a.feedback_uptake==c.feedback_uptake)
    g_joint=(a.primary_act==g.primary_act)&(a.feedback_uptake==g.feedback_uptake)
    keys=['primary_act','feedback_uptake','joint']
    pairs=[exact_p(a[k]==c[k],a[k]==g[k]) for k in LABELS]
    pairs.append(exact_p(c_joint,g_joint))
    for entry,p in zip(pairs,holm([x['exact_p'] for x in pairs])):
        entry['holm_adjusted_p']=p
    metrics['paired_tests']=dict(zip(keys,pairs))

    rows=[]
    for i in range(len(a)):
        if not c_joint.iloc[i]:
            rows.append({'row_no':i+1,'episode_id':a.at[i,'episode_id'],
                         'astra_primary':a.at[i,'primary_act'],'claude_primary':c.at[i,'primary_act'],
                         'astra_uptake':a.at[i,'feedback_uptake'],'claude_uptake':c.at[i,'feedback_uptake']})
    # This output has episode identifiers. It belongs under ignored results/, not GitHub.
    pd.DataFrame(rows,columns=['row_no','episode_id','astra_primary','claude_primary','astra_uptake','claude_uptake']).to_csv(args.outdir/'errors_local_only.csv',index=False)

    metrics['claude_confidence']={}
    for level in ['high','medium','low']:
        mask=c.confidence==level
        n=int(mask.sum()); correct=int((mask&c_joint).sum())
        metrics['claude_confidence'][level]={'n':n,'joint_correct':correct,'joint_accuracy':correct/n if n else None}
    metrics['source_audit']={'n_rows':len(a),
                             'missing_previous_student_excerpt':int(a.previous_student_excerpt.eq('').sum()),
                             'tutor_context_exactly_950_chars':int(a.tutor_context.str.len().eq(950).sum())}
    (args.outdir/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(metrics,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
