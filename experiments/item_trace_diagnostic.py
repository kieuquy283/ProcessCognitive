import csv,io,gzip,json,random,collections,hashlib,time,os,argparse
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss,brier_score_loss,roc_auc_score
def load_dataset(directory, per_tutor=55):
    root=Path(directory)
    base=root/'1_main_leaderboard_data'/'gre_quant'
    if not base.is_dir():
        raise FileNotFoundError(f'Missing StudentBench data: {base}')
    cases=[]
    for arm in sorted(base.glob('ai_arm_*')):
        taskdirs=sorted(arm.glob('task_id_*'))
        # Reproduce the exploratory tutor-balanced selection order.
        key='shuffle'+'1_main_leaderboard_data/gre_quant/'+arm.name
        random.Random(key).shuffle(taskdirs)
        for task in taskdirs[:min(per_tutor,len(taskdirs))]:
            pp=task/'student_data'/'student.json'
            pre=task/'student_data'/'pretest_responses.csv'
            post=task/'student_data'/'posttest_responses.csv'
            traj=task/'ai_tutoring_data'/'student_ai_tutor_interaction_trajectory.csv'
            if not all(p.exists() for p in (pp,pre,post,traj)):
                continue
            try:
                p=json.loads(pp.read_text(encoding='utf-8'))
                def csvrows(path):
                    with path.open('r',encoding='utf-8-sig',newline='') as f:
                        return list(csv.DictReader(f))
                ev=csvrows(traj)
                ev.sort(key=lambda e:int(e['trajectory_position']))
                st=' '.join(e['content'] for e in ev if e['event_type']=='student_message' and e['content'].strip())[:9000]
                tt=' '.join(e['content'] for e in ev if e['event_type']=='ai_tutor_message' and e['content'].strip())[:12000]
                sym=[]
                for e in ev:
                    typ=e['event_type']
                    if typ=='student_message':sym.append('S')
                    elif typ=='ai_tutor_message':sym.append('A')
                    elif typ=='practice_problem_shown':sym.append('P')
                    elif typ=='practice_answer_submitted':
                        c=e['is_correct'].strip().lower()
                        sym.append('C' if c in ('1','true') else 'W' if c in ('0','false') else 'U')
                cases.append({'profile':p,'pre':csvrows(pre),'post':csvrows(post),
                              'student_text':st,'tutor_text':tt,'event_symbols':sym})
            except (ValueError,KeyError):
                continue
    with (root/'question_bank_quant.csv').open(encoding='utf-8-sig',newline='') as f:
        questionbank=list(csv.DictReader(f))
    return cases,questionbank

parser=argparse.ArgumentParser(description='StudentBench GRE Quant item-level diagnostic; exploratory')
parser.add_argument('--data',type=Path,help='Official extracted StudentBench data root')
parser.add_argument('--output',type=Path,default=Path('results/item_trace_pilot.json'))
parser.add_argument('--per-tutor',type=int,default=55)
args=parser.parse_args()
if args.data is not None:
    raw,questionbank=load_dataset(args.data,args.per_tutor)
else:
    # Remote analysis workspace cache; never committed to repository
    raw=json.load(gzip.open('/tmp/processcognitive_sample.json.gz','rt'))
    questionbank=json.load(open('/tmp/processcognitive_questionbank.json'))
bank={r['question_id']:r for r in questionbank}
alphabet=['S','A','P','C','W','U'];pairs=[a+b for a in alphabet for b in alphabet]
def eventvals(seq,variant):
 seq=list(seq)
 if variant=='shuffle':
  random.Random(20261024+len(seq)).shuffle(seq)
 n=max(1,len(seq))
 counts=collections.Counter(seq)
 paircts=collections.Counter(a+b for a,b in zip(seq[:-1],seq[1:]))
 out={}
 for k in alphabet:out['event_'+k]=counts[k]/n
 if variant!='bag':
  for k in pairs:out['transition_'+k]=paircts[k]/max(1,len(seq)-1)
 return out
records=[];info=[]
for s in raw:
 p=s['profile']; sid=p['student_id'];seq=s['event_symbols']
 pre_correct={};by_skill=collections.defaultdict(list);by_subskill=collections.defaultdict(list)
 for r in s['pre']:
  b=bank.get(r['question_id'])
  if b and r['is_correct'] in ('0','1'):
   y=int(r['is_correct']);pre_correct[b['pair']]=y
   by_skill[b['skill']].append(y)
   by_subskill[b['subskill']].append(y)
 if len(pre_correct)<25:continue
 base={
  'sid':sid,'arm':p['ai_model_preset_id'],'form':p['assessment_form_order'],
  'pre_total':p['pretest_score_points'],'pre_theta':p.get('pretest_irt_theta',np.nan),
  'practice_n':p['practice_problems_answered_count'],'practice_correct':p['practice_problems_final_correct_count'],
  'practice_submissions':p['practice_answer_submissions_count'],
  'student_msgs':p['student_messages_sent_to_tutor'],'ai_msgs':p['ai_tutor_messages_sent_to_student'],
  'student_text':s['student_text'],'tutor_text':s['tutor_text'],
 }
 base.update(eventvals(seq,'ordered'))
 shuf=eventvals(seq,'shuffle')
 for k in pairs:base['shuffle_'+k]=shuf['transition_'+k]
 for r in s['post']:
  b=bank.get(r['question_id'])
  if b is None or r['is_correct'] not in ('0','1'):continue
  skill=by_skill.get(b['skill'],[])
  sub=by_subskill.get(b['subskill'],[])
  vals=dict(base)
  vals.update({'y':int(r['is_correct']),'question':b['question_id'],'pair':b['pair'],'skill':b['skill'],
    'difficulty':b['difficulty'],'format':b['format_code'],
    'matched_pre':pre_correct.get(b['pair'],np.nan),
    'pre_skill':np.mean(skill) if skill else np.nan,
    'pre_skill_n':len(skill),
    'pre_subskill':np.mean(sub) if sub else np.nan,
    'pre_subskill_n':len(sub)})
  records.append(vals)
df=pd.DataFrame(records)
print('complete sessions',df.sid.nunique(),'items',len(df),'tutors',df.arm.nunique(),flush=True)
# stratified deterministic session-heldout, CV on development
groups=collections.defaultdict(list)
for sid, arm, form in df[['sid','arm','form']].drop_duplicates().itertuples(index=False,name=None):
 groups[(arm,form)].append(sid)
held=set();folds={}
for key,ids in sorted(groups.items()):
 ids.sort();random.Random(str(key)+':20261024').shuffle(ids)
 for j,sid in enumerate(ids):
  if j%5==0:held.add(sid)
  else:folds[sid]=(j%5)-1
dev=df[~df.sid.isin(held)].reset_index(drop=True).copy()
dev['fold']=dev.sid.map(folds)
print('development sessions',dev.sid.nunique(),'development items',len(dev),'holdout unopened',len(held),flush=True)
numerical_base=['pre_total','pre_theta','matched_pre','pre_skill','pre_skill_n','pre_subskill','pre_subskill_n']
practice=['practice_n','practice_correct','practice_submissions']
counts=['student_msgs','ai_msgs']
ev=[f'event_{x}' for x in alphabet]
trans=[f'transition_{x}' for x in pairs]
shuffle=[f'shuffle_{x}' for x in pairs]
cat=['question','arm','form','skill','difficulty','format']
configs={
 'B0_pretest':(numerical_base,[]),
 'B1_practice':(numerical_base+practice,[]),
 'B2_counts':(numerical_base+practice+counts,[]),
 'E8_event_bag':(numerical_base+practice+counts+ev,[]),
 'E8_ordered_transitions':(numerical_base+practice+counts+ev+trans,[]),
 'E8_shuffled_transitions':(numerical_base+practice+counts+ev+shuffle,[]),
 'E7_student_tfidf':(numerical_base+practice+counts,['student_text']),
 'E7_tutor_tfidf':(numerical_base+practice+counts,['tutor_text']),
 'E7_both_tfidf':(numerical_base+practice+counts,['student_text','tutor_text'])
}
y=dev.y.to_numpy();outs={}
start=time.time()
for name,(nums,texts) in configs.items():
 preds=np.zeros(len(dev))
 for fold in sorted(dev.fold.unique()):
  a=dev.fold!=fold;b=~a
  transforms=[
   ('numeric',Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler())]),nums),
   ('categorical',OneHotEncoder(handle_unknown='ignore'),cat)]
  for tc in texts:
   transforms.append(('text_'+tc,TfidfVectorizer(ngram_range=(1,2),min_df=5,max_features=1000,sublinear_tf=True,strip_accents='unicode'),tc))
  mdl=Pipeline([('features',ColumnTransformer(transforms,sparse_threshold=1.0)),
                ('classifier',LogisticRegression(solver='liblinear',C=.5,max_iter=200))])
  cols=nums+cat+texts
  mdl.fit(dev.loc[a,cols],dev.loc[a,'y'])
  preds[b.to_numpy()]=mdl.predict_proba(dev.loc[b,cols])[:,1]
 outs[name]=preds
 print(name,'logloss',round(log_loss(y,preds),6),'brier',round(brier_score_loss(y,preds),6),'auc',round(roc_auc_score(y,preds),5),'seconds',round(time.time()-start,1),flush=True)
rng=np.random.default_rng(20261024)
comp={}
for u,v in [('B0_pretest','B1_practice'),('B1_practice','B2_counts'),('B2_counts','E8_event_bag'),
 ('E8_event_bag','E8_ordered_transitions'),('E8_shuffled_transitions','E8_ordered_transitions'),
 ('B2_counts','E7_student_tfidf'),('B2_counts','E7_tutor_tfidf'),('B2_counts','E7_both_tfidf')]:
 a=np.clip(outs[u],1e-7,1-1e-7);b=np.clip(outs[v],1e-7,1-1e-7)
 d=(-(y*np.log(a)+(1-y)*np.log(1-a))+(y*np.log(b)+(1-y)*np.log(1-b)))
 per=pd.DataFrame({'sid':dev.sid,'diff':d}).groupby('sid')['diff'].mean().to_numpy()
 boot=rng.choice(per,size=(1700,len(per)),replace=True).mean(axis=1)
 comp[u+'_to_'+v]={'mean_logloss_reduction':float(per.mean()),'bootstrap_ci95':np.quantile(boot,[.025,.975]).tolist()}
 print('contrast',u,'=>',v,'delta',round(per.mean(),7),'ci',list(np.round(np.quantile(boot,[.025,.975]),7)),flush=True)
output={'n_downloaded':len(raw),'n_sessions':int(df.sid.nunique()),'n_dev_sessions':int(dev.sid.nunique()),'n_holdout_sessions':len(held),'n_dev_items':len(dev),'results':{},'comparisons':comp,'target':'posttest item correct','protocol':'4 fold grouped session out-of-fold, holdout not inspected','pretest':'item pair matched and skill/subskill performance','no_causal_claim':True}
for name,p in outs.items():output['results'][name]={'logloss':float(log_loss(y,p)),'brier':float(brier_score_loss(y,p)),'auc':float(roc_auc_score(y,p))}
args.output.parent.mkdir(parents=True,exist_ok=True)
json.dump(output,args.output.open('w',encoding='utf-8'),indent=2)
print('RESULT WRITTEN',str(args.output),'TIME',round(time.time()-start,1),flush=True)
