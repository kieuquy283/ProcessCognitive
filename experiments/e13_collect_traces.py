#!/usr/bin/env python3
"""E13 StudentBench Quant retrieval: confidential reduced event traces, zero raw text.

Select 48 deterministic sessions from each of 13 GRE Quant tutor arms. A pinned
upstream Hugging Face revision prevents silent updates. Output is PRIVATE
because it retains posttest targets and session identifiers. Do not commit it.
"""
from __future__ import annotations
import argparse,csv,io,json,gzip,random,time,collections,urllib.request,urllib.error
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path

SHA="304c8d63c726e72b60510bba3a44454fc0726721"
API="https://huggingface.co/api/datasets/handshake-ai-research/studentbench/tree/"+SHA+"/"
RAW="https://huggingface.co/datasets/handshake-ai-research/studentbench/resolve/"+SHA+"/"
FILES=("student_data/student.json","student_data/pretest_responses.csv",
       "student_data/posttest_responses.csv",
       "ai_tutoring_data/student_ai_tutor_interaction_trajectory.csv")
KEEP_EVENT=("trajectory_position","timestamp_elapsed_seconds","recorded_elapsed_seconds",
            "event_type","actor","concept_id","practice_problem_id","problem_origin",
            "is_correct","answer_attempt_number")
PROFILE=("student_id","ai_model_preset_id","assessment_form_order",
         "pretest_score_points","pretest_irt_theta",
         "practice_problems_answered_count","practice_problems_final_correct_count",
         "practice_answer_submissions_count",
         "student_messages_sent_to_tutor","ai_tutor_messages_sent_to_student")
def request(url,tries=3):
    for k in range(tries):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"ProcessCognitive-E13-research/1.0"})
            with urllib.request.urlopen(req,timeout=19) as f:
                return f.read().decode("utf-8-sig")
        except urllib.error.HTTPError as e:
            if e.code==404:return None
            time.sleep(0.6+1.5*k)
        except Exception:time.sleep(0.6+1.1*k)
    return None

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="annotation_work/e13_private_trajectories.json.gz")
    p.add_argument("--workers",type=int,default=20)
    p.add_argument("--per-arm",type=int,default=48)
    a=p.parse_args()
    arms_raw=request(API+"1_main_leaderboard_data/gre_quant")
    if not arms_raw:raise RuntimeError("Failed to enumerate tutor arms")
    arms=sorted(x["path"] for x in json.loads(arms_raw)
                if x["path"].split("/")[-1].startswith("ai_arm_"))
    if len(arms)!=13:raise RuntimeError(f"Expected 13 GRE Quant tutor arms, found {len(arms)}")
    tasks=[]
    for arm in arms:
        raw=request(API+arm)
        if not raw:raise RuntimeError(f"Cannot list tutor arm {arm}")
        choices=sorted(x["path"] for x in json.loads(raw) if x["type"]=="directory")
        random.Random("E9:"+arm).shuffle(choices)
        tasks.extend(choices[:a.per_arm])
    print("E13 TARGET",len(tasks),"ARMS",len(arms),flush=True)
    def fetch(path):
        raw=[request(RAW+path+"/"+part) for part in FILES]
        if any(v is None for v in raw):return path,None
        try:
            full=json.loads(raw[0])
            pre=list(csv.DictReader(io.StringIO(raw[1])))
            post=list(csv.DictReader(io.StringIO(raw[2])))
            trace=list(csv.DictReader(io.StringIO(raw[3])))
            reduced={
                "profile":{k:full.get(k) for k in PROFILE},
                "pre":[{k:r.get(k) for k in ("question_id","is_correct")}
                       for r in pre],
                "post":[{k:r.get(k) for k in ("question_id","is_correct")}
                        for r in post],
                "events":[{k:r.get(k) for k in KEEP_EVENT} for r in trace],
            }
            return path,reduced
        except (KeyError,ValueError,TypeError):return path,None
    results={};failed=[];start=time.time()
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futures={ex.submit(fetch,t):t for t in tasks}
        for j,future in enumerate(as_completed(futures),1):
            path,res=future.result()
            if res is not None:results[path]=res
            else:failed.append(path)
            if j%104==0:
                print("FETCH",j,"OK",len(results),"FAIL",len(failed),
                      "sec",round(time.time()-start),flush=True)
    banktext=request(RAW+"question_bank_quant.csv")
    if not banktext:raise RuntimeError("Unable to download question bank")
    bank=list(csv.DictReader(io.StringIO(banktext)))
    obj={
        "revision":SHA,"selected":len(tasks),"successful":len(results),"fail_count":len(failed),
        "failed_task_paths":failed,"bank":bank,
        "sessions":[results[t] for t in tasks if t in results]
    }
    output=Path(a.output);output.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(output,"wt",encoding="utf8") as f:json.dump(obj,f)
    audits=collections.Counter(x["event_type"] for s in obj["sessions"] for x in s["events"])
    print("E13 COMPLETE",len(results),"/",len(tasks),
          "EVENT COUNTS",json.dumps(audits),"BANK",len(bank),
          "OUTPUT",output,"sec",round(time.time()-start),flush=True)

if __name__=="__main__":main()
