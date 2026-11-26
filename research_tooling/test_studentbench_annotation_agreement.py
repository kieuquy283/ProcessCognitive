import hashlib,json,sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from studentbench_annotation_agreement import run

def fixture(tmp_path,approved=True):
    manifest=pd.DataFrame([{
        "pilot_id":f"E1-{i+1:03d}",
        "turn_key":f"FICTIONAL_SESSION_{i}|{i}",
        "session_id":f"FICTIONAL_SESSION_{i}",
        "split":"development" if i<200 else "locked_holdout",
    } for i in range(280)])
    manifest.to_csv(tmp_path/"manifest.csv",index=False)
    digest=hashlib.sha256("\n".join(sorted(manifest.turn_key)).encode()).hexdigest()
    (tmp_path/"summary.json").write_text(json.dumps({"selected_keys_sha256":digest}))
    (tmp_path/"codebook.json").write_text(json.dumps({
        "approved":approved,"frozen":True,"version":"FICTIONAL_TEST",
        "labels":["A","B"]}))
    for name in ("a","b"):
        df=manifest[["pilot_id","turn_key"]].copy()
        df["label"]=["A" if i%2==0 else "B" for i in range(280)]
        df["annotator_source"]="human"
        df.to_csv(tmp_path/f"{name}.csv",index=False)
    return [tmp_path/f"{name}" for name in
            ("a.csv","b.csv","manifest.csv","summary.json","codebook.json","result.json")]

def test_exact_human_agreement_only_reports_aggregates(tmp_path):
    files=fixture(tmp_path)
    result=run(*files)
    assert result["n_units"]==200 and result["n_distinct_sessions"]==200
    assert result["cohen_kappa"]==pytest.approx(1)
    assert result["evidence_tier"]=="human_reference"
    assert "FICTIONAL_SESSION" not in (tmp_path/"result.json").read_text()

def test_refuse_unapproved_codebook(tmp_path):
    files=fixture(tmp_path,False)
    with pytest.raises(RuntimeError,match="NOT APPROVED"):
        run(*files)

def test_refuse_fake_human_annotations(tmp_path):
    files=fixture(tmp_path)
    d=pd.read_csv(tmp_path/"b.csv")
    d["annotator_source"]="llm"
    d.to_csv(tmp_path/"b.csv",index=False)
    with pytest.raises(RuntimeError,match="two human"):
        run(*files)

def test_holdout_is_separate_and_rejects_incomplete_phase(tmp_path):
    files=fixture(tmp_path)
    x=run(*files,phase="locked_holdout")
    assert x["n_units"]==80
    a=pd.read_csv(tmp_path/"a.csv",keep_default_na=False)
    a.loc[200,"label"]=""
    a.to_csv(tmp_path/"a.csv",index=False)
    with pytest.raises(RuntimeError,match="missing independent"):
        run(*files,phase="locked_holdout")
