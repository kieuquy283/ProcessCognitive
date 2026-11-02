#!/usr/bin/env python3
"""Private-data-free synthetic smoke test for ND2 handoff and annotation validator."""
import csv,json,hashlib,subprocess,sys,tempfile
from pathlib import Path
SCRIPT=Path(__file__).with_name('validate_nd2_annotation.py')
REV='304c8d63c726e72b60510bba3a44454fc0726721'
INPUT=['episode_id','previous_student_excerpt','tutor_context','student_turn']
COLS=INPUT+['primary_act','feedback_uptake','annotation_rationale','confidence']
def write(path,cols,rows):
    with path.open('w',encoding='utf-8',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=cols);w.writeheader();w.writerows(rows)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def exec_check(command,should_pass):
    r=subprocess.run([sys.executable,str(SCRIPT)]+command,capture_output=True,text=True)
    assert (r.returncode==0)==should_pass,(r.stderr,r.stdout[:200])
def test():
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp);data=p/'data';data.mkdir()
        (data/'.studentbench_revision').write_text(REV,encoding='utf-8')
        nd1=p/'nd1.csv';mapping=p/'mapping.csv';book=p/'frozen_codebook.md'
        book.write_text('SYNTHETIC-ONLY CODEBOOK, NOT FOR REAL ANNOTATION.\n'+'A'*300,encoding='utf-8')
        write(nd1,['episode_id'],[{'episode_id':f'ND1-{i}'} for i in range(40)])
        write(mapping,['episode_id','session_key'],[{'episode_id':f'ND1-{i}','session_key':format(i,'020x')} for i in range(40)])
        att=p/'review.json'
        att.write_text(json.dumps({'reviewed_by':'Synthetic Reviewer','reviewed_at':'2026-10-28T00:00:00Z','source_revision':REV,'nd1_sha256':sha(nd1),'mapping_sha256':sha(mapping)}),encoding='utf-8')
        pre=['source-gate','--nd1',str(nd1),'--nd1-mapping',str(mapping),'--codebook',str(book),'--data',str(data),'--provenance',str(att)]
        exec_check(pre,True)
        write(mapping,['episode_id','session_key'],[{'episode_id':f'ND1-{i}','session_key':format(i,'020x')} for i in range(39)])
        exec_check(pre,False)
        rows=[{'episode_id':f'SYN-{i:03d}','previous_student_excerpt':'','tutor_context':'synthetic previous tutor','student_turn':'synthetic student question','primary_act':'AK','feedback_uptake':'AC','annotation_rationale':'Synthetic evidence','confidence':'medium'} for i in range(280)]
        for role in ['astra','claude']:write(p/f'{role}.csv',COLS,rows)
        write(p/'source.csv',INPUT,[{key:r[key] for key in INPUT} for r in rows])
        write(p/'manifest.csv',['episode_id','session_key','split'],[{'episode_id':r['episode_id'],'session_key':format(i,'020x'),'split':'random' if i<200 else 'challenge'} for i,r in enumerate(rows)])
        args=['annotations','--source',str(p/'source.csv'),'--manifest',str(p/'manifest.csv'),'--astra',str(p/'astra.csv'),'--claude',str(p/'claude.csv'),'--codebook',str(book)]
        exec_check(args,True)
        bad=[dict(r) for r in rows];bad[2]['student_turn']='corrupted'
        write(p/'claude.csv',COLS,bad);exec_check(args,False)
        bad=[dict(r) for r in rows];bad[2]['primary_act']='invalid'
        write(p/'claude.csv',COLS,bad);exec_check(args,False)
        print('PASS synthetic 40-mapping and 280-annotation validation (NO real model labels)')
if __name__=='__main__':test()
