"""Synthetic-only source-provenance tests; NOT ND2 empirical results."""
import csv
import tempfile
from pathlib import Path
from nd2_pipeline import load_nd1_sessions, source_revision_audit, SOURCE_REVISION

def expect_valueerror(fn,part):
    try:fn()
    except ValueError as e:
        assert part.lower() in str(e).lower(),repr(e)
        return
    raise AssertionError('Expected ValueError: '+part)

def write_rows(path,rows):
    with path.open('w',encoding='utf8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['episode_id','session_key'])
        writer.writeheader();writer.writerows(rows)

def test_provenance_guards():
    with tempfile.TemporaryDirectory() as td:
        folder=Path(td);mapping=folder/'map.csv'
        nd1=[{'episode_id':f'ND1-{i}'} for i in range(40)]
        good=[{'episode_id':f'ND1-{i}','session_key':format(i,'020x')} for i in range(40)]
        write_rows(mapping,good)
        assert len(load_nd1_sessions(mapping,nd1))==40
        write_rows(mapping,good[:-1])
        expect_valueerror(lambda:load_nd1_sessions(mapping,nd1),'exactly all')
        write_rows(mapping,good[:-1]+[good[0]])
        expect_valueerror(lambda:load_nd1_sessions(mapping,nd1),'exactly all')
        corrupted=[dict(row) for row in good];corrupted[0]['session_key']='not-validated'
        write_rows(mapping,corrupted)
        expect_valueerror(lambda:load_nd1_sessions(mapping,nd1),'20-character')
        assert not source_revision_audit(folder)['revision_record_matches_expected']
        (folder/'.studentbench_revision').write_text('other',encoding='utf-8')
        expect_valueerror(lambda:source_revision_audit(folder),'Invalid source')
        (folder/'.studentbench_revision').write_text('0'*40,encoding='utf-8')
        expect_valueerror(lambda:source_revision_audit(folder),'differs')
        (folder/'.studentbench_revision').write_text(SOURCE_REVISION,encoding='utf-8')
        assert source_revision_audit(folder)['revision_record_matches_expected']
    print('PASS: source-provenance guard tests (synthetic only).')

if __name__=='__main__':test_provenance_guards()
