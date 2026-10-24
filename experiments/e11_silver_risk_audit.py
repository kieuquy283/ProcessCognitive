#!/usr/bin/env python3
"""E11: audit extrapolation of a weak Astra silver mapping classifier.

Inputs: PRIVATE Astra 120-label file, public E11 400-blinded candidates.
Outputs: aggregate diagnostics only, not per-pair pseudo-labels. This is a
SILVER-model transfer diagnostic; predictions are not true pedagogical labels.
"""
import argparse,csv,json,re,collections
from pathlib import Path
import numpy as np
from scipy.sparse import hstack,csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score,f1_score,confusion_matrix
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

GENERIC=re.compile(r"\b(?:QC|strategy|strategies|test[- ]taking|exam technique|edge cases|time management|guessing|approach|problem[- ]solving)\b",re.I)
STOP={"a","an","the","of","for","to","in","by","and","or","on","vs","using","with","is","gre","mathematics","math"}
LABELS=["D","S","N","U"]

def read(path):
 with Path(path).open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def tokens(t):return set(x for x in re.findall(r"[a-z]+",t.lower()) if x not in STOP)
def numerical(rows):
 a=[]
 for r in rows:
  sub,title=r["gre_subskill"],r["tutoring_concept_title"]
  st=tokens(sub);tt=tokens(title)
  a.append([int(bool(GENERIC.search(title))),len(st&tt)/max(len(st|tt),1),len(st&tt)/max(len(st),1),
    len(st&tt)/max(len(tt),1),np.log1p(len(sub)),np.log1p(len(title)),
    int("algebra" in title.lower()),int("geometry" in title.lower()),int("probability" in title.lower()),
    int("percent" in title.lower()),int("factor" in title.lower())])
 return np.asarray(a,dtype=np.float32)
class Features:
 def fit(self,rows):
  self.scalar=StandardScaler().fit(numerical(rows))
  self.vsub=TfidfVectorizer(analyzer="char",ngram_range=(2,4),max_features=1100,min_df=2,sublinear_tf=True).fit([r["gre_subskill"] for r in rows])
  self.vtitle=TfidfVectorizer(analyzer="char",ngram_range=(2,4),max_features=1100,min_df=2,sublinear_tf=True).fit([r["tutoring_concept_title"] for r in rows])
  return self
 def transform(self,rows):
  return hstack([csr_matrix(self.scalar.transform(numerical(rows))),
     self.vsub.transform([r["gre_subskill"] for r in rows]),
     self.vtitle.transform([r["tutoring_concept_title"] for r in rows])],format="csr")

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--astra",type=Path,required=True)
 p.add_argument("--pairs",type=Path,required=True)
 p.add_argument("--output",type=Path,default=Path("annotation_work/e11/silver_risk.json"))
 p.add_argument("--max-folds",type=int,default=5)
 args=p.parse_args()
 silver=read(args.astra);targets=read(args.pairs)
 if len(silver)!=120 or len(targets)!=400:raise ValueError("Expected 120 Astra labels and 400 E11 candidates")
 if any(x["label"] not in LABELS for x in silver):raise ValueError("Missing Astra labels")
 if any(x["label"].strip() for x in targets):raise ValueError("E11 target labels must remain blinded")
 overlap={(r["gre_subskill"],r["tutoring_concept_title"]) for r in silver}&{
     (r["gre_subskill"],r["tutoring_concept_title"]) for r in targets}
 if overlap:raise ValueError("E11 evaluation contains exact E9c training pairs")
 y=np.asarray([x["label"] for x in silver])
 metrics={}
 for group_type in ("gre_subskill","tutoring_concept_title"):
  groups=[r[group_type] for r in silver]
  splits=GroupKFold(n_splits=min(args.max_folds,len(set(groups))))
  pred=np.empty(len(y),dtype=object)
  for train,test in splits.split(np.arange(len(y)),y,groups=groups):
   tr=[silver[i] for i in train];te=[silver[i] for i in test]
   trf=Features().fit(tr)
   model=LogisticRegression(C=.35,max_iter=350,class_weight="balanced")
   model.fit(trf.transform(tr),y[train])
   pred[test]=model.predict(trf.transform(te))
  metrics[group_type]={
   "accuracy":float(accuracy_score(y,pred)),"macro_F1":float(f1_score(y,pred,labels=LABELS,average="macro",zero_division=0)),
   "F1_D":float(f1_score(y=="D",pred=="D",zero_division=0)),
   "true_D_count":int((y=="D").sum()),"predicted_D_count":int((pred=="D").sum()),
   "confusion_true_rows_pred_cols":confusion_matrix(y,pred,labels=LABELS).tolist(),
  }
 fit=Features().fit(silver)
 Xtrain=fit.transform(silver);X400=fit.transform(targets)
 predictions={};scores={}
 for c in (0.035,0.35,3.5):
  mdl=LogisticRegression(C=c,class_weight="balanced",max_iter=350)
  mdl.fit(Xtrain,y)
  pred=mdl.predict(X400); proba=mdl.predict_proba(X400)
  predictions[str(c)]=pred
  d=proba[:,list(mdl.classes_).index("D")]
  scores[str(c)]={"predicted_class_counts":dict(collections.Counter(pred.tolist())),
                  "D_posterior_quantiles_NOT_CALIBRATED":np.quantile(d,[0,.1,.5,.9,.99,1]).tolist(),
                  "count_argmax_D":int((pred=="D").sum()),"count_prob_D_ge_half":int((d>=.5).sum())}
 subgroups={
  "all_400":np.ones(400,dtype=bool),
  "title_generic":np.asarray([bool(GENERIC.search(r["tutoring_concept_title"])) for r in targets])}
 for name,mask in subgroups.items():
  scores["0.35"][name+"_argmax_label_counts"]=dict(collections.Counter(predictions["0.35"][mask].tolist()))
 lo,hi=predictions["0.035"],predictions["3.5"]
 out={
  "status":"SILVER_ONLY_NO_E11_LABELS",
  "Astra_original_label_counts":dict(collections.Counter(y.tolist())),
  "silver_oof_metrics":metrics,
  "E11_unlabelled_400_transfer":scores,
  "C_0.035_vs_3.5_prediction_disagreement":int(np.sum(lo!=hi)),
  "exact_prior_label_overlap":len(overlap),
  "warnings":["Predictions are NOT validated GRE knowledge labels",
              "P(D) is NOT calibrated to population prevalence",
              "Only 5 Astra D examples and 3 U examples",
              "E11 candidate mix is 200 probability-sampled + 200 enriched/stress; do not use mixed class rates as prevalence",
              "This file deliberately contains NO synthetic human judgments."],
 }
 args.output.parent.mkdir(parents=True,exist_ok=True)
 args.output.write_text(json.dumps(out,indent=2),encoding="utf8")
 print(json.dumps(out,indent=2))

if __name__=="__main__":main()
