#!/usr/bin/env python3
"""E9c: create a real, blinded concept-subskill annotation sample. No human labels created."""
import argparse,collections,csv,hashlib,json,random,re
from pathlib import Path
import numpy as np
from fastembed import TextEmbedding

SEED=20261024
GENERIC=re.compile(r"\b(?:QC|strategy|strategies|test[- ]taking|exam technique|edge cases|time management|guessing|approach|problem[- ]solving)\b",re.I)
SENSITIVE=re.compile(r"[\w.\-+]+@[\w.\-]+\.[A-Za-z]{2,}|https?://|\b(?:student id|account|phone|email|address)\s*[:=]\s*\S+",re.I)

def csvrows(path):
 with Path(path).open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def metadata_from_data(root,per_arm):
 base=Path(root)/"1_main_leaderboard_data"/"gre_quant"
 rows=[]
 for arm in sorted(base.glob("ai_arm_*")):
  cases=sorted(arm.glob("task_id_*"))
  random.Random("E9:1_main_leaderboard_data/gre_quant/"+arm.name).shuffle(cases)
  for task in cases[:per_arm]:
   paths=[task/"student_data"/"student.json",task/"ai_lesson_plan_data"/"lesson_plan_including_practice_problems.json",task/"ai_tutoring_data"/"student_ai_tutor_interaction_trajectory.csv"]
   if not all(p.is_file() for p in paths):continue
   try:
    p=json.loads(paths[0].read_text(encoding="utf-8"))
    plan=json.loads(paths[1].read_text(encoding="utf-8"))
    events=csvrows(paths[2])
    active=collections.Counter(e["concept_id"] for e in events if e["event_type"]=="student_message" and e.get("content","").strip())
    titles=sorted({c["name"].strip() for c in plan.get("concepts",[]) if c.get("name","").strip() and active[c["concept_id"]]>0})
    rows.append(dict(id=p["student_id"],tutor=p["ai_model_preset_id"],form=p["assessment_form_order"],titles=titles))
   except (OSError,KeyError,ValueError):continue
 return rows

def partition(data):
 groups=collections.defaultdict(list)
 for i,row in enumerate(data):groups[(row["tutor"],row["form"])].append(i)
 dev=[];hold=[]
 for key,idx in sorted(groups.items()):
  idx.sort(key=lambda i:data[i]["id"])
  random.Random("E9"+str(key)+":20261024").shuffle(idx)
  for k,i in enumerate(idx):
   (hold if k%5==0 else dev).append(i)
 return sorted(dev),sorted(hold)

def safe_title(title):
 return 3<=len(title)<=130 and not SENSITIVE.search(title)

def choose(pool,count,previous,rng):
 selected=[];sub=collections.Counter(x["subskill"] for x in previous);titles=collections.Counter(x["title"] for x in previous)
 used={(x["subskill"],x["title"]) for x in previous}
 candidates=list(pool);rng.shuffle(candidates)
 for max_sub,max_title in [(8,2),(12,3),(100000,100000)]:
  for r in candidates:
   key=(r["subskill"],r["title"])
   if key in used or sub[r["subskill"]]>=max_sub or titles[r["title"]]>=max_title:continue
   selected.append(r);used.add(key)
   sub[r["subskill"]]+=1;titles[r["title"]]+=1
   if len(selected)==count:return selected
 return selected

def main():
 p=argparse.ArgumentParser()
 src=p.add_mutually_exclusive_group(required=True)
 src.add_argument("--data",type=Path)
 src.add_argument("--metadata-json",type=Path)
 p.add_argument("--question-bank",type=Path)
 p.add_argument("--out-dir",type=Path,default=Path("annotation_work"))
 p.add_argument("--per-arm",type=int,default=48)
 p.add_argument("--per-stratum",type=int,default=30)
 p.add_argument("--model",default="sentence-transformers/all-MiniLM-L6-v2")
 p.add_argument("--cache-dir",default=".cache/fastembed")
 args=p.parse_args()
 if args.metadata_json:
  data=json.loads(args.metadata_json.read_text(encoding="utf8"))
  if args.question_bank is None:p.error("--question-bank required with --metadata-json")
 else:data=metadata_from_data(args.data,args.per_arm)
 bank=csvrows(args.question_bank or (args.data/"question_bank_quant.csv"))
 skillmap={}
 for item in bank:
  s=item["subskill"]
  if s in skillmap and skillmap[s]!=item["skill"]:raise ValueError("Conflicting GRE skills")
  skillmap[s]=item["skill"]
 subskills=sorted(skillmap)
 dev_ids,hold_ids=partition(data)
 dev=[data[i] for i in dev_ids]
 names=sorted({title for x in dev for title in x["titles"] if safe_title(title)})
 if len(names)<40:raise ValueError("Not enough concept titles")
 queries=["GRE Quantitative mathematics subskill: "+q for q in subskills]
 concepts=["GRE mathematics concept: "+s for s in names]
 emb=TextEmbedding(model_name=args.model,cache_dir=str(args.cache_dir),threads=2)
 vec=np.asarray(list(emb.embed(queries+concepts,batch_size=64)),dtype=np.float32)
 vec/=np.maximum(np.linalg.norm(vec,axis=1,keepdims=True),1e-7)
 sims=vec[:len(queries)]@vec[len(queries):].T
 nameidx={name:i for i,name in enumerate(names)}
 pairs=collections.Counter();top=collections.Counter()
 nquery=0;n_generic_top=0
 for x in dev:
  title_list=sorted(set(t for t in x["titles"] if t in nameidx))
  if not title_list:continue
  cols=[nameidx[t] for t in title_list]
  for j,subskill in enumerate(subskills):
   best=title_list[int(np.argmax(sims[j,cols]))]
   top[(subskill,best)]+=1;nquery+=1
   n_generic_top+=bool(GENERIC.search(best))
   for title in title_list:pairs[(subskill,title)]+=1
 records=[]
 qidx={name:i for i,name in enumerate(subskills)}
 for (skill,title),count in pairs.items():
  records.append(dict(subskill=skill,skill=skillmap[skill],title=title,
    cosine=float(sims[qidx[skill],nameidx[title]]),n_sessions=count,
    n_nearest=top[(skill,title)],generic=bool(GENERIC.search(title))))
 non=[x for x in records if not x["generic"]]
 gen=[x for x in records if x["generic"]]
 cut=np.quantile([x["cosine"] for x in non],[1/3,2/3])
 pools=dict(generic=gen,low=[x for x in non if x["cosine"]<=cut[0]],
            middle=[x for x in non if cut[0]<x["cosine"]<=cut[1]],
            high=[x for x in non if x["cosine"]>cut[1]])
 rng=random.Random(SEED)
 chosen=[]
 for stratum in ("generic","low","middle","high"):
  subset=choose(pools[stratum],args.per_stratum,chosen,rng)
  chosen.extend([{**x,"stratum":stratum} for x in subset])
 if len(chosen)!=args.per_stratum*4:
  raise RuntimeError(f"Not enough unique candidates; got {len(chosen)}")
 for x in chosen:
  x["pair_id"]="E9C-"+hashlib.sha256((x["subskill"]+"\x00"+x["title"]).encode("utf8")).hexdigest()[:12].upper()
 rng.shuffle(chosen)
 args.out_dir.mkdir(parents=True,exist_ok=True)
 fields=["pair_id","gre_skill","gre_subskill","tutoring_concept_title","label","rationale"]
 blind=[dict(pair_id=x["pair_id"],gre_skill=x["skill"],gre_subskill=x["subskill"],
             tutoring_concept_title=x["title"],label="",rationale="") for x in chosen]
 for filename in ("e9c_annotator_A.csv","e9c_annotator_B.csv"):
  with (args.out_dir/filename).open("w",encoding="utf8",newline="") as f:
   w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(blind)
 analyst_fields=["pair_id","stratum","cosine","n_sessions","n_nearest","generic"]
 with (args.out_dir/"e9c_analyst_audit.csv").open("w",encoding="utf8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=analyst_fields);w.writeheader()
  w.writerows([{k:r[k] for k in analyst_fields} for r in chosen])
 audit=dict(status="NOT_ANNOTATED",loaded_sessions=len(data),dev_sessions=len(dev),
            holdout_uninspected=len(hold_ids),unique_titles=len(names),
            n_subskills=len(subskills),candidate_pairs=len(records),
            generic_candidate_pairs=len(gen),nearest_queries=nquery,
            generic_nearest=n_generic_top,generic_nearest_rate=n_generic_top/nquery,
            cosine_terciles=cut.tolist(),sample_size=len(chosen),
            sample_strata=dict(collections.Counter(x["stratum"] for x in chosen)),
            sample_unique_subskills=len(set(x["subskill"] for x in chosen)),
            sample_unique_titles=len(set(x["title"] for x in chosen)),
            model=args.model,seed=SEED,
            warning="No human labels; deliberate stratified sample is not population-representative.")
 (args.out_dir/"e9c_sampling_audit.json").write_text(json.dumps(audit,indent=2),encoding="utf8")
 print(json.dumps(audit,indent=2))

if __name__=="__main__":main()
