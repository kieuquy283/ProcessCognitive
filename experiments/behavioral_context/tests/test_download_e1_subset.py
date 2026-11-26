import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from download_e1_subset import PATTERNS, DATASET, REVISION
def test_two_section_pinned_patterns():
    assert DATASET=="handshake-ai-research/studentbench"
    assert len(REVISION)==40
    assert len(PATTERNS)==9
    assert sum("gre_quant" in p for p in PATTERNS)==4
    assert sum("gre_verbal" in p for p in PATTERNS)==4
