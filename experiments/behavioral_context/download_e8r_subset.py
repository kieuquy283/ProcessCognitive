#!/usr/bin/env python3
"""Download only E8R source inputs at the published HF revision.
Selective download is NOT the official 35,498-file integrity verification.
Downloaded source stays under ignored data/.
"""
import argparse
import json
from pathlib import Path

DATASET = "handshake-ai-research/studentbench"
REVISION = "304c8d63c726e72b60510bba3a44454fc0726721"
PATTERNS = [
    "studentbench_overall_parameters.json",
    "1_main_leaderboard_data/gre_quant/ai_arm_*/task_id_*/student_data/student.json",
    "1_main_leaderboard_data/gre_quant/ai_arm_*/task_id_*/student_data/pretest_responses.csv",
    "1_main_leaderboard_data/gre_quant/ai_arm_*/task_id_*/student_data/posttest_responses.csv",
    "1_main_leaderboard_data/gre_quant/ai_arm_*/task_id_*/ai_tutoring_data/student_ai_tutor_interaction_trajectory.csv",
]

def download(out, max_workers=12):
    from huggingface_hub import snapshot_download
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    snapshot_download(DATASET, repo_type="dataset", revision=REVISION,
                      allow_patterns=PATTERNS, local_dir=str(out),
                      max_workers=max_workers)
    count = len(list((out / "1_main_leaderboard_data" / "gre_quant").glob(
        "ai_arm_*/task_id_*/student_data/student.json")))
    if count < 80:
        raise RuntimeError(f"E8R BLOCKED: only {count} pinned Quant session profiles")
    if not (out / "studentbench_overall_parameters.json").is_file():
        raise RuntimeError("E8R BLOCKED: dataset root marker missing")
    result = {
        "dataset": DATASET, "requested_revision": REVISION,
        "selective_download": True, "full_snapshot_hash_verified": False,
        "quant_session_profiles_present": count,
    }
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--max-workers", type=int, default=12)
    args=p.parse_args()
    download(args.out,args.max_workers)
