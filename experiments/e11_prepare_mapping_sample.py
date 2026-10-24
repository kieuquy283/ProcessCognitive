#!/usr/bin/env python3
"""E11: 400 blinded GRE concept↔subskill candidates with two clearly separate panels.

Population: UNIQUE observed pairs of GRE Quant subskill and active lesson concept
title within DEVELOPMENT sessions. 200 pairs uniformly sampled without
replacement from that finite pair universe estimate class prevalence for
UNIQUE pairs; 150 similarity-enriched probable-direct-coverage candidates; 50
generic-strategy stress cases. The latter 200 are NOT population-representative.

No true labels, test outcomes or transcript content enter sample construction.
Exact E9c 120 pairs are excluded to reduce reuse/contamination.
Outputs should be inspected for unexpected sensitive text before publishing.
"""
import argparse,csv,hashlib,json,random,re,urllib.request,urllib.error,time,collections,io
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import numpy as np
from fastembed import TextEmbedding

SEED=20261024
DATA_REVISION="304c8d63c726e72b60510bba3a44454fc0726721"
BASE="https://huggingface.co/datasets/handshake-ai-research/studentbench/resolve/"+DATA_REVISION+"/"
API="https://huggingface.co/api/datasets/handshake-ai-research/studentbench"
GENERIC=re.compile(r"\b(?:QC|strategy|strategies|test[- ]taking|exam technique|edge cases|time management|guessing|approach|problem[- ]solving)\b",re.I)
PII=re.compile(r"[\w.\-+]+@[\w.\-]+\.[a-z]{2,}|https?://|(?:phone|student.id|email|address)\s*[:=]|[\r\n]|(?:\+?\d[\d\- ]{8,}\d)",re.I)
STOP={"an","a","the","vs","of","and","to","for","with","using","in","on","or","by","a","is","gre","quantitative","mathematics","math","method","methods","problem","problems"}

def tokens(x):
    return set(t for t in re.findall(r"[a-z]+",x.lower()) if t not in STOP)
def normalize(t):
    return " ".join(t.strip().split())

def read_csv(path):
    with Path(path).open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def request(url):
    for i in range(4):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"StudentBench E11 reproducibility"})
            with urllib.request.urlopen(req,timeout=27) as f:return f.read().decode("utf-8-sig")
        except urllib.error.HTTPError as e:
            if e.code==404:return None
            time.sleep(1+2*i if e.code==429 else 1)
        except Exception:time.sleep(1)
    return None

def remote_sessions(per_arm):
    root=json.loads(request(API+"/tree/"+DATA_REVISION+"/1_main_leaderboard_data/gre_quant"))
    arms=sorted(x["path"] for x in root if x["path"].split("/")[-1].startswith("ai_arm_"))
    tasks=[]
    for arm in arms:
        raw=request(API+"/tree/"+DATA_REVISION+"/"+arm)
        if not raw:continue
        cases=sorted(x["path"] for x in json.loads(raw) if x["type"]=="directory")
        random.Random("E9:"+arm).shuffle(cases)
        tasks.extend(cases[:per_arm])
    print("REMOTE selected",len(tasks),"arms",len(arms),flush=True)
    def download(path):
        fs=["student_data/student.json",
            "ai_lesson_plan_data/lesson_plan_including_practice_problems.json",
            "ai_tutoring_data/student_ai_tutor_interaction_trajectory.csv"]
        res=[request(BASE+path+"/"+p) for p in fs]
        if any(x is None for x in res):return None
        try:
            p=json.loads(res[0]);plan=json.loads(res[1])
            events=list(csv.DictReader(io.StringIO(res[2])))
            active=collections.Counter(x["concept_id"] for x in events
                if x["event_type"]=="student_message" and x.get("content","").strip())
            titles=sorted({normalize(c["name"]) for c in plan.get("concepts",[])
                if c.get("name","") and active[c["concept_id"]]>0})
            return dict(id=p["student_id"],tutor=p["ai_model_preset_id"],
                        form=p["assessment_form_order"],titles=titles)
        except (ValueError,KeyError):return None
    rows=[]
    with ThreadPoolExecutor(max_workers=14) as pool:
        for j,f in enumerate(as_completed([pool.submit(download,p) for p in tasks]),1):
            x=f.result()
            if x:rows.append(x)
            if j%175==0:print("REMOTE fetched",j,"complete",len(rows),flush=True)
    metadata=json.loads(request(API))
    return rows,dict(huggingface_revision_pinned=DATA_REVISION,main_revision_observed=metadata.get("sha"),selected=len(tasks),downloaded=len(rows),arms=len(arms))

def local_sessions(root,per_arm):
    base=Path(root)/"1_main_leaderboard_data"/"gre_quant"
    rows=[];n=0
    for arm in sorted(base.glob("ai_arm_*")):
        cases=sorted(arm.glob("task_id_*"))
        random.Random("E9:1_main_leaderboard_data/gre_quant/"+arm.name).shuffle(cases)
        for task in cases[:per_arm]:
            n+=1
            pp=task/"student_data"/"student.json"
            pl=task/"ai_lesson_plan_data"/"lesson_plan_including_practice_problems.json"
            tr=task/"ai_tutoring_data"/"student_ai_tutor_interaction_trajectory.csv"
            if not all(p.is_file() for p in (pp,pl,tr)):continue
            try:
                profile=json.loads(pp.read_text(encoding="utf8"))
                lesson=json.loads(pl.read_text(encoding="utf8"))
                events=read_csv(tr)
                active=collections.Counter(x["concept_id"] for x in events
                    if x["event_type"]=="student_message" and x.get("content","").strip())
                titles=sorted({normalize(x["name"]) for x in lesson.get("concepts",[])
                    if x.get("name") and active[x["concept_id"]]>0})
                rows.append(dict(id=profile["student_id"],tutor=profile["ai_model_preset_id"],
                                 form=profile["assessment_form_order"],titles=titles))
            except (OSError,KeyError,ValueError):continue
    return rows,dict(huggingface_revision="RECORD_MANUALLY_FROM_PINNED_DOWNLOAD",selected=n,downloaded=len(rows))

def split_by_group(rows):
    grouped=collections.defaultdict(list)
    for i,r in enumerate(rows):grouped[(r["tutor"],r["form"])].append(i)
    dev=[];held=[]
    for key,inds in sorted(grouped.items()):
        inds.sort(key=lambda i:rows[i]["id"])
        random.Random("E9"+str(key)+":20261024").shuffle(inds)
        for k,i in enumerate(inds):
            (held if k%5==0 else dev).append(i)
    return sorted(dev),sorted(held)

def write_csv(path,rows,fieldnames):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fieldnames);w.writeheader()
        w.writerows([{k:r[k] for k in fieldnames} for r in rows])

def choose_top(pool,n,picked,seed):
    rng=random.Random(seed)
    candidates=list(pool)
    # Priority by cosine & lexical overlap with tiny random jitter to break ties,
    # diversity bounds in first pass, then relax for samples that require it.
    candidates.sort(key=lambda r:-(r["score"]+rng.random()*.0001))
    out=[]
    used={(r["gre_subskill"],r["tutoring_concept_title"]) for r in picked}
    subcnt=collections.Counter(r["gre_subskill"] for r in picked)
    titlecnt=collections.Counter(r["tutoring_concept_title"] for r in picked)
    for submax,titlemax in ((12,2),(16,3),(10000,10000)):
        for r in candidates:
            k=(r["gre_subskill"],r["tutoring_concept_title"])
            if k in used or subcnt[r["gre_subskill"]]>=submax or titlecnt[r["tutoring_concept_title"]]>=titlemax:continue
            out.append(r);used.add(k);subcnt[r["gre_subskill"]]+=1;titlecnt[r["tutoring_concept_title"]]+=1
            if len(out)==n:return out
    return out

def main():
    p=argparse.ArgumentParser()
    src=p.add_mutually_exclusive_group(required=True)
    src.add_argument("--data",type=Path)
    src.add_argument("--remote",action="store_true")
    p.add_argument("--bank",type=Path)
    p.add_argument("--exclude-e9c",type=Path)
    p.add_argument("--out-dir",type=Path,default=Path("annotation_work/e11"))
    p.add_argument("--cache-dir",default=".cache/fastembed")
    p.add_argument("--per-arm",type=int,default=48)
    p.add_argument("--metadata-cache",type=Path,help="Store/reuse metadata after remote fetch; never commit this file")
    args=p.parse_args()
    if args.metadata_cache and args.metadata_cache.is_file():
        cache=json.loads(args.metadata_cache.read_text(encoding="utf8"))
        rows,metadata=cache["rows"],cache["metadata"]
        print("USING CACHED METADATA",len(rows),flush=True)
    else:
        rows,metadata=remote_sessions(args.per_arm) if args.remote else local_sessions(args.data,args.per_arm)
        if args.metadata_cache:
            args.metadata_cache.parent.mkdir(parents=True,exist_ok=True)
            args.metadata_cache.write_text(json.dumps({"rows":rows,"metadata":metadata}),encoding="utf8")
    if args.remote:
        raw=request(BASE+"question_bank_quant.csv")
        if not raw:raise RuntimeError("Question bank download failed")
        bank=list(csv.DictReader(io.StringIO(raw)))
    else:
        bank=read_csv(args.bank or args.data/"question_bank_quant.csv")
    if len(rows)<200:raise ValueError("Less than 200 sessions; sample quality poor")
    dev,held=split_by_group(rows)
    subskills=sorted(set(r["subskill"] for r in bank))
    skill_by_sub={r["subskill"]:r["skill"] for r in bank}
    titles=sorted({t for i in dev for t in rows[i]["titles"] if 3<=len(t)<=130 and not PII.search(t)})
    banned=set()
    if args.exclude_e9c:
        old=read_csv(args.exclude_e9c)
        banned={(r["gre_subskill"],normalize(r["tutoring_concept_title"])) for r in old}
    elif args.remote:
        # Public blank E9c sample; use only pair definitions, never annotations.
        u="https://raw.githubusercontent.com/kieuquy283/ProcessCognitive/research/studentbench-diagnostics/annotations/templates/e9c_pairs_blinded.csv"
        raw=request(u)
        if raw:
            banned={(r["gre_subskill"],normalize(r["tutoring_concept_title"])) for r in csv.DictReader(io.StringIO(raw))}
    universe=[]
    for sub in subskills:
        for title in titles:
            if (sub,title) not in banned:
                universe.append({"gre_subskill":sub,"gre_skill":skill_by_sub[sub],
                                 "tutoring_concept_title":title})
    if len(universe)<1000:raise ValueError("Insufficient unique pairs")
    rng=random.Random(SEED)
    # First random sample: each unique pair has equal inclusion probability.
    random_panel=rng.sample(universe,200)
    encoder=TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2",
                          cache_dir=args.cache_dir,threads=2)
    desc=["GRE Quantitative mathematics subskill: "+x for x in subskills]
    concepts=["GRE mathematics concept: "+x for x in titles]
    E=np.asarray(list(encoder.embed(desc+concepts,batch_size=64)),dtype=np.float32)
    E/=np.maximum(np.linalg.norm(E,axis=1,keepdims=True),1e-7)
    cosine=E[:len(subskills)]@E[len(subskills):].T
    subix={s:i for i,s in enumerate(subskills)};tix={t:i for i,t in enumerate(titles)}
    score=[]
    for r in universe:
        sub,title=r["gre_subskill"],r["tutoring_concept_title"]
        word=tokens(sub);name=tokens(title)
        recall=len(word&name)/max(1,len(word))
        sim=float(cosine[subix[sub],tix[title]])
        score.append({**r,"cosine":sim,"overlap":recall,
            "score":.65*sim+.35*recall,"generic":bool(GENERIC.search(title))})
    sampled={(r["gre_subskill"],r["tutoring_concept_title"]) for r in random_panel}
    enriched=choose_top((r for r in score if not r["generic"] and
             (r["gre_subskill"],r["tutoring_concept_title"]) not in sampled),
             150,random_panel,SEED+1)
    stress=choose_top((r for r in score if r["generic"] and
            (r["gre_subskill"],r["tutoring_concept_title"]) not in sampled),
            50,random_panel+enriched,SEED+2)
    if len(enriched)!=150 or len(stress)!=50:
        raise RuntimeError(f"Insufficient candidates: enriched={len(enriched)}, strategy={len(stress)}")
    score_index={(r["gre_subskill"],r["tutoring_concept_title"]):r for r in score}
    selected=[]
    for stratum,records in [("uniform_unique_pair",random_panel),
                            ("high_similarity_enriched",enriched),
                            ("generic_strategy_stress",stress)]:
        for raw_r in records:
            r=score_index[(raw_r["gre_subskill"],raw_r["tutoring_concept_title"])]
            tag=r["gre_subskill"]+"\0"+r["tutoring_concept_title"]
            uid="E11-"+hashlib.sha256(tag.encode("utf8")).hexdigest()[:12].upper()
            selected.append({**r,"sample_stratum":stratum,"pair_id":uid})
    rng.shuffle(selected)
    if len(selected)!=400 or len({r["pair_id"] for r in selected})!=400:
        raise ValueError("Invalid sample: expected exactly 400 unique pairs")
    args.out_dir.mkdir(parents=True,exist_ok=True)
    fields=["pair_id","gre_skill","gre_subskill","tutoring_concept_title","label","rationale"]
    blank=[{**{k:r[k] for k in fields[:4]},"label":"","rationale":""} for r in selected]
    for name in ("e11_blinded_400.csv","e11_annotator_A.csv","e11_annotator_B.csv"):
        write_csv(args.out_dir/name,blank,fields)
    analyst_fields=["pair_id","sample_stratum","cosine","overlap","score","generic"]
    write_csv(args.out_dir/"e11_analyst_sidecar_PRIVATE.csv",selected,analyst_fields)
    audit={
        **metadata,"status":"UNANNOTATED","model":"sentence-transformers/all-MiniLM-L6-v2",
        "development_sessions":len(dev),"holdout_session_count_not_used":len(held),
        "observed_development_safe_titles":len(titles),
        "subskills":len(subskills),"unique_pair_population_excluding_pilot":len(universe),
        "excluded_prior_E9c_pairs":len(banned),"sample_size":len(selected),
        "sample_strata":dict(collections.Counter(r["sample_stratum"] for r in selected)),
        "distinct_subskills":len({r["gre_subskill"] for r in selected}),
        "distinct_titles":len({r["tutoring_concept_title"] for r in selected}),
        "high_similarity_cosine_range":[min(r["cosine"] for r in enriched),max(r["cosine"] for r in enriched)],
        "uniform_sample_estimand":"prevalence over unique observed concept-title/subskill pairs, NOT usage exposures or learners",
        "warnings":["No labels generated; high-similarity is NOT ground truth D",
            "Do not infer prevalence from 150+50 deliberately enriched items",
            "Sample only from development titles; holdout sessions not used",
            "Potential title-based PII filtering incomplete; manual audit before public sharing",
            "A remote available-case sample differs from a pinned full release."],
    }
    (args.out_dir/"e11_sampling_audit.json").write_text(json.dumps(audit,indent=2),encoding="utf8")
    print(json.dumps(audit,indent=2),flush=True)

if __name__=="__main__":main()
