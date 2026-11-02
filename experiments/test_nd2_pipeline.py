"""Synthetic fixture smoke test ONLY; never interpret as ND2 research evidence."""
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import pandas as pd

SCRIPT=Path(__file__).with_name('nd2_pipeline.py')

def test_pipeline():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);base=root/'data'/'1_main_leaderboard_data'/'gre_quant'/'ai_arm_1'
        types=['next step please','because this is the reason, check it','help me understand what','ok thanks but no']
        for i in range(480):
            p=base/f'task_id_{i}'/'ai_tutoring_data'/'student_ai_tutor_interaction_trajectory.csv'
            p.parent.mkdir(parents=True)
            with p.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=['event_type','trajectory_position','content']);w.writeheader()
                w.writerows([{'event_type':'ai_tutor_message','trajectory_position':1,'content':'Tutoring prompt.'},
                            {'event_type':'student_message','trajectory_position':2,'content':types[i%4]},
                            {'event_type':'ai_tutor_message','trajectory_position':3,'content':'Response.'}])
        old=root/'nd1.csv';pd.DataFrame({'episode_id':['ND1-SOME-OLD-ID']}).to_csv(old,index=False)
        out=root/'work'
        subprocess.run([sys.executable,str(SCRIPT),'sample','--data',str(root/'data'),'--nd1',str(old),'--outdir',str(out)],check=True,capture_output=True)
        mf=pd.read_csv(out/'ND2_manifest_private.csv')
        assert len(mf)==280 and mf.session_key.nunique()==280 and (mf.split=='random').sum()==200
        for annot in ['Astra','Claude']:
            f=out/f'ND2_{annot}_blinded_private.csv'
            df=pd.read_csv(f,keep_default_na=False)
            assert len(df)==280
            df['primary_act']='AK';df['feedback_uptake']='AP'
            df['annotation_rationale']='Synthetic smoke-test label only';df['confidence']='high'
            df.to_csv(f,index=False)
        subprocess.run([sys.executable,str(SCRIPT),'evaluate','--astra',str(out/'ND2_Astra_blinded_private.csv'),'--claude',str(out/'ND2_Claude_blinded_private.csv'),'--source',str(out/'ND2_input_private.csv'),'--manifest',str(out/'ND2_manifest_private.csv'),'--outdir',str(out)],check=True,capture_output=True)
        result=json.loads((out/'ND2_metrics_private.json').read_text())
        assert result['random']['n']==200 and result['challenge']['n']==80 and result['random']['joint_accuracy']==1
        assert json.loads((out/'ND2_sampling_audit_private.json').read_text())['nd1_session_overlap_verified'] is False
    print('PASS: synthetic smoke test only (no real ND2 observations or model annotations).')

if __name__=='__main__':test_pipeline()
