#!/usr/bin/env python3
"""ND2: strict provenance/annotation schema checks. No model calls or row-level logs."""
import argparse,csv,hashlib,json,re,sys
from collections import Counter
from pathlib import Path
REVISION='304c8d63c726e72b60510bba3a44454fc0726721'
INPUT=['episode_id','previous_student_excerpt','tutor_context','student_turn']
COLS=INPUT+['primary_act','feedback_uptake','annotation_rationale','confidence']
ACT={'AK','AN','CQ','HR','OT','RE','VE'};UPTAKE={'AC','AP','NO','NR','UN'};CONF={'high','medium','low'}
def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()
def load(path):
    with open(path,encoding='utf-8-sig',newline='') as f:
        x=csv.DictReader(f)
        if x.fieldnames is None:raise ValueError('Empty CSV: '+str(path))
        header=x.fieldnames;rows=list(x)
        if any(None in r or any(v is None for v in r.values()) for r in rows):
            raise ValueError('Malformed CSV: '+str(path))
        return header,rows
def must(condition,msg):
    if not condition:raise ValueError(msg)
def source_gate(args):
    h,nd1=load(args.nd1)
    must('episode_id' in h and len(nd1)==40,'ND1 must have exactly 40 episodes')
    ids=[r['episode_id'] for r in nd1]
    must(len(set(ids))==40 and all(ids),'Duplicate/blank ND1 episode IDs')
    h,mapping=load(args.nd1_mapping)
    must({'episode_id','session_key'}.issubset(h) and len(mapping)==40,'ND1 mapping incomplete')
    must(Counter(r['episode_id'] for r in mapping)==Counter(ids),'ND1 source mapping must exactly cover all 40 IDs')
    must(all(re.fullmatch('[0-9a-f]{20}',r['session_key'].strip()) for r in mapping),'Bad session_key format')
    must(Path(args.codebook).is_file() and Path(args.codebook).stat().st_size>200,
         'Missing full codebook (file size is NOT evidence of correct semantic definitions)')
    stamp=Path(args.data)/'.studentbench_revision'
    must(stamp.is_file() and stamp.read_text(encoding='utf-8').strip()==REVISION,
         'Source release revision stamp mismatch')
    attested=False
    if args.provenance:
        p=json.loads(Path(args.provenance).read_text(encoding='utf-8'))
        must(p.get('nd1_sha256')==sha(args.nd1),'ND1 provenance SHA mismatch')
        must(p.get('mapping_sha256')==sha(args.nd1_mapping),'Mapping provenance SHA mismatch')
        must(bool(p.get('reviewed_by') and p.get('reviewed_at')),'Provenance reviewer/time absent')
        must(p.get('source_revision')==REVISION,'Wrong provenance source revision')
        attested=True
    return {'status':'STRUCTURAL SOURCE GATE PASSED','nd1_records':len(nd1),
            'codebook_sha256':sha(args.codebook),
            'nd1_sha256':sha(args.nd1),'mapping_sha256':sha(args.nd1_mapping),
            'provenance_attested':attested,
            'warning':'A file attestation does not independently prove that 40 matches are true. Review original evidence manually.'}
def annotation_gate(args):
    source_h,source=load(args.source)
    must(all(k in source_h for k in INPUT) and len(source)==280,
         'Source must have 280 records and original input fields')
    ids=[r['episode_id'] for r in source]
    must(len(set(ids))==280 and all(ids),'Bad source IDs')
    files={}
    for name,path in [('Astra',args.astra),('Claude',args.claude)]:
        head,rows=load(path)
        must(head==COLS and len(rows)==280,name+' output schema/row count')
        must([r['episode_id'] for r in rows]==ids,name+' IDs/order changed')
        must(all(all(r[col]==s[col] for col in INPUT) for r,s in zip(rows,source)),
             name+' immutable source text changed')
        must(all(r['primary_act'] in ACT and r['feedback_uptake'] in UPTAKE and
                 r['confidence'] in CONF and r['annotation_rationale'].strip() for r in rows),
             name+' contains invalid/missing labels or rationale')
        files[name]=rows
    m_h,m=load(args.manifest)
    must({'episode_id','session_key','split'}.issubset(m_h),'Manifest schema')
    must([r['episode_id'] for r in m]==ids,'Manifest episode order mismatch')
    must(len({r['session_key'] for r in m})==280,'ND2 session collision')
    must(Counter(r['split'] for r in m)==Counter({'random':200,'challenge':80}),
         'Need exactly 200 random and 80 challenge cases')
    must(Path(args.codebook).is_file() and Path(args.codebook).stat().st_size>200,
         'Frozen semantic codebook missing')
    hashes={'source_sha256':sha(args.source),'codebook_sha256':sha(args.codebook)}
    model_meta_verified=False
    if args.astra_meta and args.claude_meta:
        for name,p in [('Astra',args.astra_meta),('Claude',args.claude_meta)]:
            meta=json.loads(Path(p).read_text(encoding='utf-8'))
            must(meta.get('annotator')==name,name+' metadata annotator mismatch')
            must(bool(meta.get('verified_model_id') and meta.get('interface_or_api') and meta.get('run_date')),
                 name+' model metadata missing')
            must(all(meta.get(k)==v for k,v in hashes.items()),name+' codebook/source SHA mismatch')
        model_meta_verified=True
    output={'status':'ANNOTATION SCHEMA VALIDATED — not a scientific PASS','rows':280,
            'model_metadata_structurally_verified':model_meta_verified,
            'label_counts':{name:{col:dict(Counter(r[col] for r in rr)) for col in
                                 ['primary_act','feedback_uptake','confidence']}
                            for name,rr in files.items()},
            'file_sha256':{'Astra':sha(args.astra),'Claude':sha(args.claude),**hashes}}
    if args.sampling_audit:
        audit=json.loads(Path(args.sampling_audit).read_text(encoding='utf-8'))
        output['holdout_status']='NOT scientifically certified by this structural validator'
        output['pinned_data_stamp_in_sampling_audit']=bool(audit.get('source_revision_audit',{}).get('revision_record_matches_expected'))
    return output
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    a=sub.add_parser('source-gate')
    for name in ('nd1','nd1-mapping','codebook','data'):a.add_argument('--'+name,required=True)
    a.add_argument('--provenance')
    b=sub.add_parser('annotations')
    for name in ('source','manifest','astra','claude','codebook'):b.add_argument('--'+name,required=True)
    for name in ('astra-meta','claude-meta','sampling-audit'):b.add_argument('--'+name)
    args=parser.parse_args()
    try:
        obj=source_gate(args) if args.command=='source-gate' else annotation_gate(args)
        print(json.dumps(obj,ensure_ascii=False,indent=2))
    except (ValueError,FileNotFoundError,KeyError,UnicodeError,json.JSONDecodeError) as exc:
        print('VALIDATION FAILED:',exc,file=sys.stderr)
        sys.exit(2)
if __name__=='__main__':main()
