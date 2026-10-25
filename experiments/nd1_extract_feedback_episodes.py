#!/usr/bin/env python3
"""Pilot V1: reproducibly sample BLINDED student dialogue episodes from real StudentBench.

Annotation unit: ONE student_message with immediately relevant preceding tutor
turn and optional previous student turn; no posttest, downstream practice
outcomes, model predictions or previous pseudo-labels in blind input.

Remote acquisition is pinned to official StudentBench SHA. Pilot corpus
and sidecars contain learner free text and must remain in gitignored
annotation_work/, NEVER a public repo. Exports only aggregate metadata as JSON.
"""
import argparse,csv,io,json,random,re,hashlib,time,urllib.request,urllib.error,collections
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
SHA="304c8d63c726e72b60510bba3a44454fc0726721"
ROOT="1_main_leaderboard_data/gre_quant/"
API="https://huggingface.co/api/datasets/handshake-ai-research/studentbench/tree/"+SHA+"/"
RAW="https://huggingface.co/datasets/handshake-ai-research/studentbench/resolve/"+SHA+"/"
POSITIVE=re.compile(r"\b(?:because|therefore|so that|i (?:think|got|used|calculated)|if .* then|multiply|divide|fraction|equation|subtract|add |ratio|percent)\b",re.I)
FOLLOWUP=re.compile(r"\b(?:but|sorry|actually|instead|i see|oh |you mean|now i|not sure|why|still|confus|wait)\b",re.I)
SHORT=re.compile(r"^(?:yes|no|ok|okay|sure|thanks|thank you|idk|got it|next|continue|\\d+(?:\\.\\d+)?%?)\\W*$",re.I)
MAIL=re.compile(r"[\w.+'-]+@[\w.-]+\.[A-Za-z]{2,}")
URL=re.compile(r"https?://\S+",re.I)
PHONE=re.compile(r"(?<!\d)(?:\+?\d[\s().-]*){10,15}(?!\d)")
def sanitize(t,limit):
    s=(t or "").strip()
    s=MAIL.sub("[EMAIL]",s);s=URL.sub("[LINK]",s)
    # Avoid overly aggressive PHONE regex in quantitative mathematics:
    # phone masking left for a trained human privacy review.
    return " ".join(s.split())[:limit]
def request(url):
    for retry in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"ProcessCognitive-Pilot-V1"}),timeout=26) as r:return r.read().decode("utf-8-sig")
        except urllib.error.HTTPError as e:
            if e.code==404:return None
        except Exception:pass
        time.sleep(.6+retry*1.2)
    return None
def candidate(session_path,rows):
    rows=sorted(rows,key=lambda r:int(r["trajectory_position"]) if r.get("trajectory_position","").isdigit() else 10**9)
    out=[];active_tutor=None;last_student=None
    for idx,e in enumerate(rows):
        kind=e.get("event_type")
        if kind=="ai_tutor_message" and e.get("content","").strip():
            active_tutor=(idx,e)
        if kind=="student_message" and e.get("content","").strip():
            if active_tutor is not None:
                ix,prior=active_tutor
                # Anchor to tutor context within 9 events; prefer matching problem
                # when populated; otherwise treat as discourse context only.
                dist=idx-ix
                same=(not e.get("practice_problem_id") or not prior.get("practice_problem_id")
                      or prior["practice_problem_id"]==e["practice_problem_id"])
                if 0<dist<=9 and same:
                    student=sanitize(e.get("content"),700)
                    tutor=sanitize(prior.get("content"),950)
                    preceding=sanitize(last_student.get("content"),260) if last_student else ""
                    evidence=(
                      "reasoning_candidate" if POSITIVE.search(student) and len(student)>38
                      else "feedback_followup_candidate" if FOLLOWUP.search(student)
                      else "short_response_candidate" if len(student)<22 or SHORT.match(student)
                      else "unrestricted_other"
                    )
                    key=session_path+"|"+str(e.get("trajectory_position"))
                    eid="NV1-"+hashlib.sha256(key.encode()).hexdigest()[:12].upper()
                    out.append({
                       "episode_id":eid,
                       "previous_student_excerpt":preceding,
                       "tutor_context":tutor,
                       "student_turn":student,
                       "primary_act":"","feedback_uptake":"","annotation_rationale":"","confidence":"",
                       "_stratum":evidence,
                       "_session_key":hashlib.sha256(session_path.encode()).hexdigest()[:12],
                       "_arm":session_path.split("/")[-2],
                       "_anchor_position":e.get("trajectory_position"),
                       "_window_event_distance":dist,
                       "_raw_text_truncated":len(e.get("content",""))>700 or len(prior.get("content",""))>950,
                       "_practice_problem_aligned":bool(e.get("practice_problem_id") and prior.get("practice_problem_id"))
                    })
            last_student=e
    return out
def sample(cases,n,per_arm):
    rng=random.Random(20261025)
    quotas={
      "reasoning_candidate":round(n*.30),
      "feedback_followup_candidate":round(n*.25),
      "short_response_candidate":round(n*.25)
    }
    quotas["unrestricted_other"]=n-sum(quotas.values())
    pool=collections.defaultdict(list)
    for r in cases:pool[r["_stratum"]].append(r)
    selected=[];ids=set();limit=4
    for label,k in quotas.items():
        options=pool[label][:]
        rng.shuffle(options)
        options.sort(key=lambda v:(v["_arm"],v["_session_key"],v["_anchor_position"]))
        rng.shuffle(options)
        for r in options:
            if len([x for x in selected if x["_stratum"]==label])>=k:break
            if r["episode_id"] in ids:continue
            if sum(x["_session_key"]==r["_session_key"] for x in selected)>=limit:continue
            selected.append(r);ids.add(r["episode_id"])
    if len(selected)<n:
        remaining=[r for r in cases if r["episode_id"] not in ids]
        rng.shuffle(remaining)
        for r in remaining:
            if len(selected)==n:break
            if sum(x["_session_key"]==r["_session_key"] for x in selected)>=limit:continue
            selected.append(r);ids.add(r["episode_id"])
    if len(selected)!=n:raise ValueError(f"insufficient eligible episodes {len(selected)} of requested {n}")
    rng.shuffle(selected)
    return selected,quotas
def main():
    pa=argparse.ArgumentParser()
    pa.add_argument("--out",type=Path,default=Path("annotation_work/new_direction/pilot_180_PRIVATE.csv"))
    pa.add_argument("--n",type=int,default=180)
    pa.add_argument("--per-arm",type=int,default=6)
    pa.add_argument("--workers",type=int,default=14)
    pa.add_argument("--local-manifest",type=Path,help="newline-delimited exact task paths for reproducibility; remote data still fetched")
    args=pa.parse_args()
    armtext=request(API+ROOT)
    if not armtext:raise RuntimeError("Could not reach official pinned dataset")
    arms=sorted(r["path"] for r in json.loads(armtext)
                if r["path"].split("/")[-1].startswith("ai_arm_"))
    tasks=[]
    if args.local_manifest:
        tasks=[x.strip() for x in args.local_manifest.read_text().splitlines() if x.strip()]
    else:
        for arm in arms:
            raw=request(API+arm)
            if not raw:raise RuntimeError(f"Missing tutor arm listing {arm}")
            ids=sorted(x["path"] for x in json.loads(raw) if x["type"]=="directory")
            random.Random("NV1:"+arm).shuffle(ids)
            tasks+=ids[:args.per_arm]
    def load(task):
        path=RAW+task+"/ai_tutoring_data/student_ai_tutor_interaction_trajectory.csv"
        response=request(path)
        if response is None:return task,None
        rows=list(csv.DictReader(io.StringIO(response)))
        return task,candidate(task,rows)
    allcases=[];complete=0;fail=[]
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for idx,f in enumerate(as_completed([ex.submit(load,t) for t in tasks]),1):
            task,res=f.result()
            if res is None:fail.append(task)
            else:
                allcases.extend(res);complete+=1
            if idx%25==0:print("DOWNLOAD",idx,"OK",complete,"CANDIDATES",len(allcases),flush=True)
    selected,quotas=sample(allcases,args.n,args.per_arm)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    public_cols=["episode_id","previous_student_excerpt","tutor_context","student_turn","primary_act","feedback_uptake","annotation_rationale","confidence"]
    with args.out.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=public_cols);w.writeheader()
        w.writerows([{k:r[k] for k in public_cols} for r in selected])
    # Another annotator gets same blank input but does not see first annotation.
    other=args.out.with_name(args.out.stem+"_B.csv")
    other.write_bytes(args.out.read_bytes())
    privatecols=["episode_id","_stratum","_session_key","_arm","_anchor_position","_window_event_distance",
                 "_raw_text_truncated","_practice_problem_aligned"]
    with args.out.with_name("pilot_sampling_sidecar_PRIVATE.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=privatecols);w.writeheader()
        w.writerows([{k:r[k] for k in privatecols} for r in selected])
    aggregate={
       "release_sha":SHA,"status":"REAL_SOURCE_EPISODES_NO_HUMAN_LABELS",
       "target_task_paths":len(tasks),"retrieved_sessions":complete,
       "failed_sessions":len(fail),"candidate_student_turns":len(allcases),
       "sample_size":len(selected),"distinct_session_keys":len({r["_session_key"] for r in selected}),
       "source_arms":len({r["_arm"] for r in selected}),
       "sample_strata_actual":dict(collections.Counter(r["_stratum"] for r in selected)),
       "max_episodes_per_session":max(collections.Counter(r["_session_key"] for r in selected).values()),
       "context_linked_exact_practice_fraction":sum(r["_practice_problem_aligned"] for r in selected)/len(selected),
       "text_truncated_count":sum(r["_raw_text_truncated"] for r in selected),
       "notes":["Labels are BLANK. Lexical sampling strata are heuristics, not classification.",
                "Private workbook contains real text; inspect for PII before distribution.",
                "Takes full tutor feedback context only up to first 950 chars; context may be incomplete.",
                "No outcomes, scores, next practice correctness or posttest data accessed.",
                "Pilot is deliberately enriched, not a prevalence estimator.",
                "Event ordering may interleave problems. No claim that nearest tutor turn is always feedback."]
    }
    args.out.with_name("pilot_sampling_aggregate.json").write_text(json.dumps(aggregate,indent=2),encoding="utf8")
    print("PILOT_FINISHED",json.dumps(aggregate),flush=True)
if __name__=="__main__":main()
