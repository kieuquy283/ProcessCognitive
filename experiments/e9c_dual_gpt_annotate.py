#!/usr/bin/env python3
"""Run two distinct GPT models as independent E9c concept/subskill annotators.

- Each model receives the SAME rubric and SAME 120-item dataset.
- Every batch is a new stateless Responses API call: no shared history, prior
  labels, similarity scores, learning outcomes or cross-model answers.
- Saves one CSV per model, retaining original pair IDs and order.
- Does not run without OPENAI_API_KEY and --execute (billed API usage).
- Never commits outputs or credentials. Files reside in ignored annotation_work/.
"""
import argparse
import csv
import hashlib
import json
import os
import random
import sys
import time
from pathlib import Path

from openai import (OpenAI, APIConnectionError, APITimeoutError,
                    InternalServerError, RateLimitError)

ALLOWED = {"D", "S", "N", "U"}
DEFAULT_PAIR_FILE = Path("annotations/templates/e9c_pairs_blinded.csv")
DEFAULT_PROMPT_FILE = Path("annotations/E9c_shared_gpt_prompt_v1.md")
DEFAULT_OUTPUT = Path("annotation_work/gpt_independent_e9c")
DEFAULT_MODELS = ("gpt-6-luna", "gpt-5.6-terra")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_pairs(filename: Path):
    with filename.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    required = {"pair_id", "gre_skill", "gre_subskill",
                "tutoring_concept_title", "label", "rationale"}
    if len(rows) != 120:
        raise ValueError(f"Expected 120 E9c pairs; found {len(rows)}")
    if not rows or not required.issubset(rows[0]):
        raise ValueError("Incomplete E9c CSV columns")
    identifiers = set()
    clean = []
    for row in rows:
        pair_id = row["pair_id"].strip()
        if not pair_id or pair_id in identifiers:
            raise ValueError("Duplicate/missing pair ID")
        identifiers.add(pair_id)
        if row["label"].strip() or row["rationale"].strip():
            raise ValueError("Only BLIND UNLABELLED files are allowed as input")
        clean.append({
            "pair_id": pair_id,
            "gre_skill": row["gre_skill"].strip(),
            "gre_subskill": row["gre_subskill"].strip(),
            "tutoring_concept_title": row["tutoring_concept_title"].strip(),
        })
    if len({(x["gre_subskill"], x["tutoring_concept_title"]) for x in clean}) != len(clean):
        raise ValueError("Duplicate concept/subskill pair")
    return clean


def batch_schema():
    return {
        "type": "object",
        "properties": {
            "annotations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "pair_id": {"type": "string"},
                        "label": {"type": "string", "enum": ["D", "S", "N", "U"]},
                        "rationale": {"type": "string"},
                    },
                    "required": ["pair_id", "label", "rationale"],
                    "additionalProperties": False,
                }
            }
        },
        "required": ["annotations"],
        "additionalProperties": False,
    }


def get_batch_labels(client, model, rubric, batch, attempts=4):
    payload = json.dumps(batch, ensure_ascii=False, separators=(",", ":"))
    common_input = (
        "Apply the shared E9c codebook to this exact JSON array. "
        "Return one answer for every input pair and no other content:\n" + payload
    )
    response = None
    for retry in range(attempts):
        try:
            # No previous_response_id, no assistant messages, no conversation state.
            response = client.responses.create(
                model=model,
                instructions=rubric,
                input=common_input,
                text={"format": {
                    "type": "json_schema",
                    "name": "e9c_annotation_batch",
                    "schema": batch_schema(),
                    "strict": True,
                }},
                reasoning={"effort": "low"},
                max_output_tokens=3500,
                store=False,
            )
            break
        except (RateLimitError, APIConnectionError, APITimeoutError,
                InternalServerError):
            if retry == attempts - 1:
                raise
            time.sleep(min(2 ** retry, 8))
    if response is None or response.status != "completed":
        raise RuntimeError(
            f"Model {model} did not complete: "
            f"{getattr(response, 'status', None)}")
    raw_text = response.output_text
    if not raw_text:
        raise ValueError(f"Model {model} returned empty structured output")
    parsed = json.loads(raw_text)["annotations"]
    expected_ids = [r["pair_id"] for r in batch]
    received_ids = [r["pair_id"] for r in parsed]
    if received_ids != expected_ids:
        raise ValueError(f"Model {model}: missing, extra or reordered pair IDs")
    for record in parsed:
        if record["label"] not in ALLOWED:
            raise ValueError("Invalid categorical label")
        if len(record["rationale"].split()) > 25:
            raise ValueError("Rationale exceeded 25 words; inspect before rerun")
    usage = None
    if getattr(response, "usage", None) is not None:
        usage = {
            "input_tokens": getattr(response.usage, "input_tokens", None),
            "output_tokens": getattr(response.usage, "output_tokens", None),
            "total_tokens": getattr(response.usage, "total_tokens", None),
        }
    return parsed, {"response_id": response.id, "usage": usage}


def save_csv(path, pairs, annotations):
    index = {a["pair_id"]: a for a in annotations}
    fieldnames = ["pair_id", "gre_skill", "gre_subskill",
                  "tutoring_concept_title", "label", "rationale"]
    if set(index) != {p["pair_id"] for p in pairs}:
        raise ValueError("Incomplete annotations or duplicate IDs")
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for p in pairs:
            writer.writerow({**p, "label": index[p["pair_id"]]["label"],
                             "rationale": index[p["pair_id"]]["rationale"]})


def run_one_model(client, model, rubric, pairs, output, batch_size):
    # Each model's partial checkpoint has its own directory, preventing bleed.
    model_dir = output / model.replace("/", "_")
    model_dir.mkdir(parents=True, exist_ok=True)
    collected = []
    telemetry = []
    for start in range(0, len(pairs), batch_size):
        index = start // batch_size
        chunk = pairs[start:start + batch_size]
        result_path = model_dir / f"batch_{index:03d}.json"
        if result_path.exists():
            # A retry may resume from the same model's validated partial output.
            existing = json.loads(result_path.read_text(encoding="utf-8"))
            answered = existing["annotations"]
            meta = existing["metadata"]
            if meta["model"] != model:
                raise ValueError("Cross-model checkpoint reuse prohibited")
            if [a["pair_id"] for a in answered] != [p["pair_id"] for p in chunk]:
                raise ValueError("Checkpoint doesn't match current blind sample")
            if meta["rubric_sha256"] != sha256(rubric.encode("utf-8")):
                raise ValueError("Rubric changed; use a new output directory")
        else:
            answered, meta = get_batch_labels(client, model, rubric, chunk)
            meta["model"] = model
            meta["rubric_sha256"] = sha256(rubric.encode("utf-8"))
            meta["pair_batch_sha256"] = sha256(
                json.dumps(chunk, ensure_ascii=False, sort_keys=True).encode("utf-8"))
            result_path.write_text(
                json.dumps({"annotations": answered, "metadata": meta},
                           ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        collected.extend(answered)
        telemetry.append(meta)
        print(f"{model}: {min(start + batch_size, len(pairs))}/{len(pairs)} labels ready",
              flush=True)
    out_csv = output / f"{model.replace('/', '_')}_annotations.csv"
    save_csv(out_csv, pairs, collected)
    return out_csv, telemetry


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", type=Path, default=DEFAULT_PAIR_FILE)
    parser.add_argument("--rubric", type=Path, default=DEFAULT_PROMPT_FILE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--model-a", default=DEFAULT_MODELS[0])
    parser.add_argument("--model-b", default=DEFAULT_MODELS[1])
    parser.add_argument("--batch-size", type=int, default=12)
    parser.add_argument("--execute", action="store_true",
                        help="Explicitly authorize billed Responses API requests")
    args = parser.parse_args()

    if args.model_a == args.model_b:
        parser.error("Use two distinct model IDs for independent annotations")
    if args.batch_size < 1 or args.batch_size > 20:
        parser.error("--batch-size must be between 1 and 20")
    pairs = load_pairs(args.pairs)
    rubric = args.rubric.read_text(encoding="utf-8")
    if not rubric.strip():
        raise ValueError("Empty shared rubric")

    fingerprint = {
        "n_pairs": len(pairs),
        "models": [args.model_a, args.model_b],
        "batch_size": args.batch_size,
        "prompt_sha256": sha256(rubric.encode("utf-8")),
        "pairs_sha256": sha256(
            json.dumps(pairs, ensure_ascii=False, sort_keys=True).encode("utf-8")),
        "method": "Two stateless model IDs, same text rubric and same ordered blind pairs",
        "source": "GPT-GPT model judgments; NOT human double-annotation",
    }
    print(json.dumps(fingerprint, indent=2, ensure_ascii=False))
    if not args.execute:
        print("DRY RUN ONLY. No API calls made, no cost incurred. "
              "Add --execute after setting OPENAI_API_KEY.")
        return
    if not os.getenv("OPENAI_API_KEY"):
        parser.error("OPENAI_API_KEY is required with --execute")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.out_dir / "run_manifest.json"
    if manifest_path.exists():
        past = json.loads(manifest_path.read_text(encoding="utf-8"))
        for key in ("n_pairs", "models", "batch_size", "prompt_sha256", "pairs_sha256"):
            if past[key] != fingerprint[key]:
                raise ValueError(
                    "Cannot resume a run with different parameters; use a new output directory")
    else:
        manifest_path.write_text(json.dumps(fingerprint, indent=2), encoding="utf-8")

    client = OpenAI()
    outputs = {}
    # Running sequentially is independent here: every request is fresh/stateless
    # and no annotations from Model A enter the prompt for Model B.
    for model in (args.model_a, args.model_b):
        csv_path, telemetry = run_one_model(
            client, model, rubric, pairs, args.out_dir, args.batch_size)
        outputs[model] = {"csv": str(csv_path), "batches": telemetry}
    (args.out_dir / "completed_runs.json").write_text(
        json.dumps({"fingerprint": fingerprint, "models": outputs}, indent=2),
        encoding="utf-8",
    )
    print("Both independent model annotation files completed:")
    for model in (args.model_a, args.model_b):
        print(f"  {model}: {outputs[model]['csv']}")
    print("Model-model agreement is NOT a human inter-rater agreement estimate.")


if __name__ == "__main__":
    main()
