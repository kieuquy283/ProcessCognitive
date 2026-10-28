#!/usr/bin/env python3
"""Fetch only official StudentBench AI tutoring trajectories needed for ND2.

Files are downloaded to a local ignored data/ folder. No participant-level
content, dialogue or row manifests should ever be committed.
"""
import argparse
from pathlib import Path

REPO = "handshake-ai-research/studentbench"
REVISION = "304c8d63c726e72b60510bba3a44454fc0726721"
PATTERNS = [
    "1_main_leaderboard_data/gre_quant/ai_arm_*/task_id_*/ai_tutoring_data/student_ai_tutor_interaction_trajectory.csv",
    "1_main_leaderboard_data/gre_verbal/ai_arm_*/task_id_*/ai_tutoring_data/student_ai_tutor_interaction_trajectory.csv",
]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", default="data/studentbench")
    p.add_argument("--revision", default=REVISION,
                   help="Pinned official dataset commit; record this value in reports")
    a = p.parse_args()
    dest = Path(a.data_dir)
    if ".git" in dest.parts:
        p.error("Cannot download the raw data inside .git")
    try:
        from huggingface_hub import snapshot_download
    except ImportError as e:
        raise SystemExit("Install with: python -m pip install huggingface_hub>=1.0") from e
    snapshot_download(repo_id=REPO, repo_type="dataset", revision=a.revision,
                      allow_patterns=PATTERNS, local_dir=str(dest))
    # This is local provenance metadata, not proof of upstream file integrity.
    (dest / '.studentbench_revision').write_text(a.revision + '\n', encoding='utf-8')
    paths = sorted(dest.glob("1_main_leaderboard_data/gre_*/ai_arm_*/task_id_*/ai_tutoring_data/student_ai_tutor_interaction_trajectory.csv"))
    print(f"Official StudentBench revision: {a.revision}")
    print(f"GRE AI trajectories downloaded: {len(paths)}")
    print(f"Local directory: {dest.resolve()}")
    if len(paths) < 280:
        raise SystemExit("Insufficient local AI sessions to sample 280 independent sessions; verify the dataset snapshot.")

if __name__ == "__main__":
    main()
