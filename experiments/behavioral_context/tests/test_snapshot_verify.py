import hashlib
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from verify_studentbench_snapshot import verify,sha256_file

def fake(tmp_path):
    (tmp_path/"folder").mkdir()
    (tmp_path/"folder"/"file.csv").write_text("abc\n")
    (tmp_path/"other.json").write_text("{}")
    d=hashlib.sha256()
    for name in ["folder/file.csv","other.json"]:
        d.update(f"{name}\t{sha256_file(tmp_path/name)}\n".encode())
    return {
        "method":"SHA256 of sorted relative_path TAB file_sha256 NEWLINE records",
        "data_roots":["folder","other.json"],
        "huggingface_revision":"FICTIONAL_FIXTURE","file_count":2,
        "sha256":d.hexdigest(),
    }

def test_clean_fixture_passes_and_outside_files_ignored(tmp_path):
    m=fake(tmp_path)
    assert verify(tmp_path,m)["status"]=="VERIFIED"
    (tmp_path/"unrelated_private.txt").write_text("not part of source")
    assert verify(tmp_path,m)["status"]=="VERIFIED"

def test_mutation_and_missing_input_detected(tmp_path):
    m=fake(tmp_path)
    (tmp_path/"folder"/"file.csv").write_text("changed\n")
    assert verify(tmp_path,m)["status"]=="MISMATCH"
    (tmp_path/"other.json").unlink()
    assert verify(tmp_path,m)["missing_source_roots"] == ["other.json"]
