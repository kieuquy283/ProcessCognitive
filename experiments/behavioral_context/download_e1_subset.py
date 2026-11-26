#!/usr/bin/env python3
"""Selective pinned public source download for BOTH GRE AI arms. No full SHA digest."""
import argparse,json
from pathlib import Path
from huggingface_hub import snapshot_download
DATASET="handshake-ai-research/studentbench"
REVISION="304c8d63c726e72b60510bba3a44454fc0726721"
PATTERNS=["studentbench_overall_parameters.json"]
for section in ("gre_quant","gre_verbal"):
    for suffix in ("student_data/student.json","student_data/pretest_responses.csv",
                   "student_data/posttest_responses.csv",
                   "ai_tutoring_data/student_ai_tutor_interaction_trajectory.csv"):
        PATTERNS.append(f"1_main_leaderboard_data/{section}/ai_arm_*/task_id_*/{suffix}")
def download(out,max_workers=12):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    snapshot_download(DATASET,repo_type="dataset",revision=REVISION,
                      allow_patterns=PATTERNS,local_dir=str(out),max_workers=max_workers)
    counts={s:len(list((out/"1_main_leaderboard_data"/s).glob(
        "ai_arm_*/task_id_*/student_data/student.json")))
        for s in ("gre_quant","gre_verbal")}
    if sum(counts.values())!=2139:raise RuntimeError(f"E0 BLOCKED: expected 2139, found {counts}")
    if not (out/"studentbench_overall_parameters.json").is_file():
        raise RuntimeError("E0 BLOCKED: missing root marker")
    print(json.dumps({"dataset":DATASET,"requested_revision":REVISION,
      "selective_download":True,"full_snapshot_hash_verified":False,
      "profiles_by_section":counts},indent=2))
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    p.add_argument("--max-workers",type=int,default=12)
    a=p.parse_args();download(a.out,a.max_workers)
