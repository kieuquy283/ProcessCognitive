import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from download_e8r_subset import DATASET, REVISION, PATTERNS

def test_pinned_selective_source_patterns():
    assert DATASET=="handshake-ai-research/studentbench"
    assert len(REVISION)==40 and set(REVISION)<set("0123456789abcdef")
    assert len(PATTERNS)==5
    assert all("/gre_quant/" in p for p in PATTERNS[1:])
