#!/usr/bin/env python3
"""Count context-availability in private E1 inputs; never emit student dialogue."""
import argparse,csv,json
from collections import Counter
from pathlib import Path
def summarize(path):
    by_section={}
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            s=r["session_id"]
            section="gre_quant" if s.startswith("quant:") else (
                "gre_verbal" if s.startswith("verbal:") else None)
            if section is None:raise RuntimeError("E1 BLOCKED: unknown source section")
            d=by_section.setdefault(section,Counter())
            d["turns"]+=1
            d["has_recent_ai_response"]+=bool(r["last_ai_response"].strip())
            d["has_dialogue_history"]+=bool(json.loads(r["prior_dialogue_json"]))
            d["has_causally_available_task_text"]+=bool(r["task_context_text"].strip())
            d["short_7_words"]+=len(r["current_utterance"].split())<=7
    if sum(d["turns"] for d in by_section.values())<280:
        raise RuntimeError("E1 BLOCKED: insufficient actual student turns")
    return {"status":"REAL_DATA_CONTEXT_AVAILABILITY_ONLY",
            "counts":{k:dict(v) for k,v in sorted(by_section.items())},
            "warning":"No human labels or causal learning outcome inference."}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--turns",required=True)
    p.add_argument("--out",required=True);a=p.parse_args()
    r=summarize(a.turns);f=Path(a.out);f.parent.mkdir(parents=True,exist_ok=True)
    f.write_text(json.dumps(r,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(r,indent=2))
