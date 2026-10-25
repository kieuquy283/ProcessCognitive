#!/usr/bin/env python3
"""E13: outcome-blind practice provenance + sequence extraction.

Excludes transcript text and AI-generated lesson titles. All features are
generated before independent posttest outcomes; only the final item assembler
attaches targets. Negative controls keep first/final problem correctness and
counts unchanged while randomizing sequence features and event ordering.
"""
import argparse,collections,gzip,json,math,random,statistics
from pathlib import Path
import numpy as np
import pandas as pd

EVENT_TYPES={
 "practice_problem_shown":"P","practice_answer_submitted":"A",
 "student_message":"S","ai_tutor_message":"T",
 "practice_problem_created_during_tutoring":"C"
}
EVENT_BIGRAMS=("PA","AT","TS","ST","TA","AA","PS","SA","AP","TP","PT","AS","CT","CS")
def as_correct(x):
    v=str(x).lower().strip()
    return 1 if v in ("1","true","yes") else 0 if v in ("0","false","no") else None
def as_number(x):
    try:
        out=float(x)
        return out if math.isfinite(out) else None
    except (ValueError,TypeError):return None
def mean(vals):
    return float(np.mean(vals)) if vals else np.nan

def event_features(events,shuffle_seed=None):
    events=sorted(events,key=lambda e:as_number(e.get("trajectory_position")) if
                  as_number(e.get("trajectory_position")) is not None else 1e10)
    typ=[EVENT_TYPES.get(e.get("event_type"),"X") for e in events]
    ix={id(e):j for j,e in enumerate(events)}
    attempts=collections.defaultdict(list)
    all_answers=[]
    for j,e in enumerate(events):
        if typ[j]!="A":continue
        v=as_correct(e.get("is_correct"))
        key=e.get("practice_problem_id")
        if v is not None and key:
            attempts[key].append((j,v,as_number(e.get("timestamp_elapsed_seconds"))))
            all_answers.append((j,v))
    attempts={k:v for k,v in attempts.items() if v}
    ordered=sorted(attempts.values(),key=lambda v:v[0][0])
    first=[x[0][1] for x in ordered]
    last=[x[-1][1] for x in ordered]
    repeats=[len(x) for x in ordered]
    corrections=sum(x[0][1]==0 and x[-1][1]==1 for x in ordered)
    regressions=sum(x[0][1]==1 and x[-1][1]==0 for x in ordered)
    changed=sum(x[0][1]!=x[-1][1] for x in ordered)
    n=len(ordered)
    # Original within-problem first/final correctness is invariant to negative controls.
    provenance={
        "prov_n_attempted":n,
        "prov_first_correct_rate":mean(first),
        "prov_last_correct_rate":mean(last),
        "prov_first_wrong_count":first.count(0),
        "prov_repeated_fraction":mean([len(v)>1 for v in ordered]),
        "prov_avg_attempts":mean(repeats),
        "prov_max_attempts":max(repeats,default=0),
        "prov_correction_count":corrections,
        "prov_correction_per_first_wrong":corrections/max(first.count(0),1),
        "prov_regression_count":regressions,
        "prov_changed_count":changed,
        "prov_answered_missing":int(n==0)
    }
    # Negative-control seed acts only on temporal features, NEVER on provenance.
    types=typ[:]
    first_seq=first[:]
    outcomes=[v for _,v in all_answers]
    if shuffle_seed is not None:
        rnd=random.Random(int(shuffle_seed))
        rnd.shuffle(types)                 # same event counts, broken ordering
        rnd.shuffle(first_seq)             # same first-correct count, broken improvement slope
        rnd.shuffle(outcomes)              # same answer correctness totals
    half=len(first_seq)//2
    early=first_seq[:half]
    late=first_seq[half:]
    first_delta=mean(late)-mean(early) if early and late else np.nan
    corrtrans=[(a,b) for a,b in zip(outcomes,outcomes[1:])]
    # Feedback windows use TRUE practice-submission boundaries. Shuffle tutor vs
    # student identities within message slots to destroy response-to-feedback
    # placement without changing message count or attempt correctness.
    message_typ=types[:]
    if shuffle_seed is not None:
        message_typ=typ[:]
        positions=[j for j,t in enumerate(typ) if t in ("S","T")]
        actors=[typ[j] for j in positions]
        random.Random(int(shuffle_seed)+9812).shuffle(actors)
        for j,new_actor in zip(positions,actors):message_typ[j]=new_actor
    eligible=0;tutor_between=0;student_between=0;fix_with_tutor=0
    gaps=[];correction_gaps=[]
    for v in ordered:
        for (prev,correct0,t0),(cur,correct1,t1) in zip(v,v[1:]):
            eligible+=1
            has_tutor="T" in message_typ[prev+1:cur]
            has_student="S" in message_typ[prev+1:cur]
            tutor_between+=int(has_tutor)
            student_between+=int(has_student)
            fix_with_tutor+=int(correct0==0 and correct1==1 and has_tutor)
            if t0 is not None and t1 is not None and t1>=t0:
                gaps.append(min(t1-t0,3600))
                if correct0==0 and correct1==1:correction_gaps.append(min(t1-t0,3600))
    seq={
        "seq_early_first_correct":mean(early),
        "seq_late_first_correct":mean(late),
        "seq_first_correct_delta":first_delta,
        "seq_first_sequence_support":len(first_seq),
        "seq_ww_first":sum(a==0 and b==0 for a,b in zip(first_seq,first_seq[1:])),
        "seq_wc_first":sum(a==0 and b==1 for a,b in zip(first_seq,first_seq[1:])),
        "seq_cw_first":sum(a==1 and b==0 for a,b in zip(first_seq,first_seq[1:])),
        "seq_cc_first":sum(a==1 and b==1 for a,b in zip(first_seq,first_seq[1:])),
        "seq_wc_all":sum(a==0 and b==1 for a,b in corrtrans)/max(len(corrtrans),1),
        "seq_cw_all":sum(a==1 and b==0 for a,b in corrtrans)/max(len(corrtrans),1),
        "seq_tutor_between_attempt_fraction":tutor_between/max(eligible,1),
        "seq_student_between_attempt_fraction":student_between/max(eligible,1),
        "seq_correction_with_tutor_fraction":fix_with_tutor/max(eligible,1),
        "seq_n_resubmissions":eligible,
        "seq_median_resubmit_seconds":float(np.median(gaps)) if gaps else np.nan,
        "seq_median_correction_seconds":float(np.median(correction_gaps)) if correction_gaps else np.nan,
        "seq_n_valid_resubmit_times":len(gaps),
    }
    for pair in EVENT_BIGRAMS:
        seq["seq_ev_"+pair]=sum(a+b==pair for a,b in zip(types,types[1:]))/max(len(types)-1,1)
    counts=collections.Counter(typ)
    counts_out={"count_trajectory_events":len(events)}
    for k in ("P","A","S","T","C"):
        counts_out["count_event_"+k]=counts[k]
    # These can be predictive but have no event-sequence order.
    return provenance,counts_out,seq

def features(sessions,seed=None):
    rows=[]
    for i,s in enumerate(sessions):
        provenance,counts,seq=event_features(s["events"],None if seed is None else (seed*1000003+i*7919))
        rows.append({**provenance,**counts,**seq})
    return pd.DataFrame(rows)

def assemble(raw,shuffles=20,subset="development"):
    bank={r["question_id"]:r for r in raw["bank"]}
    all_sessions=raw["sessions"]
    profiles=[s["profile"] for s in all_sessions]
    # ONE task ID occurs across distinct tutor arms. Split by task/student ID,
    # not merely by session: no duplicated virtual-student task across train/test.
    task_ids=sorted({p["student_id"] for p in profiles})
    shuffled=task_ids[:];random.Random(20261025).shuffle(shuffled)
    reserved_ids=set(shuffled[:round(.2*len(shuffled))])
    development=[i for i,p in enumerate(profiles) if p["student_id"] not in reserved_ids]
    reserved=[i for i,p in enumerate(profiles) if p["student_id"] in reserved_ids]
    if subset not in ("development","reserved"):
        raise ValueError("subset must be development or reserved")
    selected=development if subset=="development" else reserved
    D=[all_sessions[i] for i in selected]
    actual=features(D)
    control=[features(D,seed=j+1) for j in range(shuffles)]
    # session-feature extraction is pure; no post-test information enters it.
    rows=[]
    for sid,session in enumerate(D):
        p=session["profile"]
        pre_by_pair={};pre_by_skill=collections.defaultdict(list);pre_by_sub=collections.defaultdict(list)
        for ans in session["pre"]:
            q=bank.get(ans.get("question_id"))
            v=as_correct(ans.get("is_correct"))
            if q is None or v is None:continue
            pre_by_pair[q["pair"]]=v
            pre_by_skill[q["skill"]].append(v)
            pre_by_sub[q["subskill"]].append(v)
        for ans in session["post"]:
            q=bank.get(ans.get("question_id"))
            v=as_correct(ans.get("is_correct"))
            if q is None or v is None:continue
            row={
                "sid":sid,"group":p["student_id"],"y":v,
                "question":q["question_id"],"skill":q["skill"],
                "subskill":q["subskill"],"difficulty":q["difficulty"],
                "arm":p["ai_model_preset_id"],"form":p["assessment_form_order"],
                "pre_total":p.get("pretest_score_points"),
                "pre_theta":p.get("pretest_irt_theta"),
                "pre_matched":pre_by_pair.get(q["pair"],np.nan),
                "pre_skill":mean(pre_by_skill[q["skill"]]),
                "pre_sub":mean(pre_by_sub[q["subskill"]]),
                "practice_n":p.get("practice_problems_answered_count"),
                "practice_good":p.get("practice_problems_final_correct_count"),
                "practice_submissions":p.get("practice_answer_submissions_count"),
                "student_msgs":p.get("student_messages_sent_to_tutor"),
                "tutor_msgs":p.get("ai_tutor_messages_sent_to_student"),
            }
            row.update(actual.iloc[sid].to_dict())
            for j,control_df in enumerate(control):
                for k,vv in control_df.iloc[sid].items():
                    if k.startswith("seq_"):row["null%02d_"%j+k]=vv
            rows.append(row)
    df=pd.DataFrame(rows)
    audit={
        "revision":raw["revision"],"retrieval_selected":raw["selected"],
        "retrieval_successful":raw["successful"],"retrieval_failed":raw["fail_count"],
        "total_groups":len(task_ids),
        "n_reserved_task_groups":len(reserved_ids),
        "n_development_task_groups":len({profiles[i]["student_id"] for i in development}),
        "n_dev_sessions":len(development),"n_reserved_sessions_unscored":len(reserved),
        "n_dev_posttest_items":len(df),
        "n_shuffles":len(control),"all_event_counts":dict(collections.Counter(e["event_type"] for s in D for e in s["events"])),
        "provenance_coverage":{
            "sessions_with_scored_attempts":int((actual["prov_n_attempted"]>0).sum()),
            "sessions_with_repeat_attempts":int((actual["prov_max_attempts"]>1).sum()),
            "sessions_with_valid_time":int((actual["seq_n_valid_resubmit_times"]>0).sum()),
        },
        "baseline_counts_vs_trace":{
            "mean_abs_diff_practice_submissions":float(np.nanmean([
                abs(float(D[j]["profile"].get("practice_answer_submissions_count") or 0)-float(actual["count_event_A"].iloc[j]))
                for j in range(len(D))])),
            "mean_abs_diff_final_correct":float(np.nanmean([
                abs(float(D[j]["profile"].get("practice_problems_final_correct_count") or 0)-
                    float(actual["prov_last_correct_rate"].iloc[j])*float(actual["prov_n_attempted"].iloc[j]))
                for j in range(len(D)) if pd.notna(actual["prov_last_correct_rate"].iloc[j])]))
        }
    }
    return df,audit

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="annotation_work/e13_private_trajectories.json.gz")
    p.add_argument("--output",default="annotation_work/e13_features_private.pkl")
    p.add_argument("--audit",default="results/E13_feature_audit.json")
    p.add_argument("--shuffles",type=int,default=20)
    a=p.parse_args()
    with gzip.open(a.input,"rt",encoding="utf8") as f:raw=json.load(f)
    frame,audit=assemble(raw,shuffles=a.shuffles)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True);frame.to_pickle(a.output)
    Path(a.audit).parent.mkdir(parents=True,exist_ok=True)
    Path(a.audit).write_text(json.dumps(audit,indent=2),encoding="utf8")
    print(json.dumps(audit,indent=2))
if __name__=="__main__":main()
