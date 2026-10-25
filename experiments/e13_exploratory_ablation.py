import numpy as np,pandas as pd,json,argparse
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('--input',default='annotation_work/e13_features_private.pkl')
parser.add_argument('--output',default='results/E13_exploratory_ablation.json')
args=parser.parse_args()
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss,roc_auc_score,brier_score_loss
df=pd.read_pickle(args.input);Y=df.y.to_numpy();G=df.group.to_numpy()
base=['pre_total','pre_theta','pre_matched','pre_skill','pre_sub','practice_n','practice_good','practice_submissions','student_msgs','tutor_msgs']
cat=['question','skill','subskill','difficulty','arm','form']
count=[c for c in df if c.startswith('count_')]
prov=[c for c in df if c.startswith('prov_')]
seq=[c for c in df if c.startswith('seq_')]
first=['prov_first_correct_rate','prov_first_wrong_count','prov_answered_missing']
retry=['prov_repeated_fraction','prov_avg_attempts','prov_max_attempts','prov_n_attempted']
fix=['prov_correction_count','prov_correction_per_first_wrong','prov_regression_count','prov_changed_count']
temporal_first=[c for c in seq if c.startswith('seq_early') or c.startswith('seq_late') or c.startswith('seq_first') or c.startswith('seq_w') or c.startswith('seq_c')]
feedback=[c for c in seq if 'tutor_between' in c or 'student_between' in c or 'correction_with_tutor' in c or 'n_resubmissions' in c]
event=[c for c in seq if c.startswith('seq_ev_')]
timing=[c for c in seq if 'seconds' in c or 'valid_resubmit_times' in c]
spec={
'B0':base,'N2_count':base+count,
'P_first':base+count+first,'P_attempts':base+count+retry,
'P_revision':base+count+fix,
'P_first_revision':base+count+first+retry+fix,
'B1_all_provenance':base+count+prov,
'T_early_late':base+count+prov+temporal_first,
'T_event_bigrams':base+count+prov+event,
'T_feedback_trajectory':base+count+prov+feedback,
'T_timing':base+count+prov+timing,
}
folds=list(GroupKFold(4).split(df,Y,groups=G))
res={};contrasts={}
for C in (.03,.3):
 pred={}
 for name,cols in spec.items():
  oof=np.full(len(df),np.nan)
  for tr,va in folds:
   pre=ColumnTransformer([('num',Pipeline([('impute',SimpleImputer(strategy='median',add_indicator=True,keep_empty_features=True)),('scale',StandardScaler())]),cols),
                           ('cat',OneHotEncoder(handle_unknown='ignore'),cat)],sparse_threshold=1)
   X=pre.fit_transform(df.iloc[tr][cols+cat]);Z=pre.transform(df.iloc[va][cols+cat])
   lr=LogisticRegression(C=C,solver='liblinear',max_iter=250)
   lr.fit(X,Y[tr]);oof[va]=lr.predict_proba(Z)[:,1]
  pred[name]=oof
  res[f'C{C}/{name}']={'logloss':float(log_loss(Y,oof)),'auc':float(roc_auc_score(Y,oof)),'brier':float(brier_score_loss(Y,oof))}
  print('ABLATION',C,name,round(res[f'C{C}/{name}']['logloss'],6),flush=True)
 loss=lambda p:-(Y*np.log(np.clip(p,1e-8,1-1e-8))+(1-Y)*np.log(np.clip(1-p,1e-8,1-1e-8)))
 for name in spec:
  if name=='B0':continue
  diff=loss(pred['B0'])-loss(pred[name])
  arr=pd.DataFrame({'group':df.group,'d':diff}).groupby('group').d.mean().to_numpy()
  bs=np.random.default_rng(20261025).choice(arr,size=(2500,len(arr)),replace=True).mean(axis=1)
  contrasts[f'C{C}/B0_to_{name}']={'gain':float(arr.mean()),'CI95':np.quantile(bs,[.025,.975]).tolist()}
Path(args.output).parent.mkdir(parents=True,exist_ok=True)
json.dump({'status':'EXPLORATORY_POST_HOC_FEATURE_ABLATION','metrics':res,'contrasts':contrasts},open(args.output,'w'),indent=2)
print('DONE',len(df),flush=True)
