#!/usr/bin/env python3
"""Validate complete StudentBench download against official upstream snapshot.

Input manifest: https://github.com/Handshake-AI-Research/studentbench/blob/main/verification/data_snapshot.json
Digest is SHA256 of sorted: relative_path TAB file_sha256 NEWLINE.
No student text, scores, identifiers or contents are written to the report.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

DIGEST_METHOD = "SHA256 of sorted relative_path TAB file_sha256 NEWLINE records"

def sha256_file(path):
    digest=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024*1024),b""):
            digest.update(block)
    return digest.hexdigest()

def verify(root,manifest):
    root=Path(root)
    if manifest.get("method") != DIGEST_METHOD:
        raise ValueError("unknown official dataset hash method")
    files=[]
    missing=[]
    for rel in manifest["data_roots"]:
        path=root/rel
        if not path.exists():
            missing.append(rel)
        elif path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(p for p in path.rglob("*") if p.is_file())
        else:
            missing.append(rel)
    pairs=sorted((p.relative_to(root).as_posix(),p) for p in files)
    digest=hashlib.sha256()
    for name,path in pairs:
        digest.update(f"{name}\t{sha256_file(path)}\n".encode("utf-8"))
    actual=digest.hexdigest()
    ok=(not missing and len(pairs)==int(manifest["file_count"])
        and actual==manifest["sha256"])
    return {
        "status":"VERIFIED" if ok else "MISMATCH",
        "huggingface_revision":manifest.get("huggingface_revision"),
        "expected_files":manifest["file_count"],
        "observed_files":len(pairs),
        "expected_digest":manifest["sha256"],
        "observed_digest":actual,
        "missing_source_roots":missing,
    }

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data",type=Path,required=True)
    ap.add_argument("--official-manifest",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    manifest=json.loads(args.official_manifest.read_text(encoding="utf-8"))
    result=verify(args.data,manifest)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
    if result["status"] != "VERIFIED":
        raise SystemExit(2)

if __name__ == "__main__":
    main()
