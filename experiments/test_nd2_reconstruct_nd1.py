"""Synthetic-only ND1 session reconstruction guard tests."""
import csv
import tempfile
from pathlib import Path
from nd2_reconstruct_nd1 import match

def make_source(folder):
    folder.mkdir(parents=True,exist_ok=True)
    p=folder/'student_ai_tutor_interaction_trajectory.csv'
    with p.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['event_type','trajectory_position','content'])
        writer.writeheader()
        writer.writerows([
            {'event_type':'ai_tutor_message','trajectory_position':1,'content':'Correct reasoning: now find the missing value after the prior step.'},
            {'event_type':'student_message','trajectory_position':2,'content':'Let me try 17.'}])

def test_reconstruction():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        base=root/'data'/'1_main_leaderboard_data'/'gre_quant'/'ai_arm_X'
        make_source(base/'task_id_0001'/'ai_tutoring_data')
        nd1=root/'nd1.csv'
        with nd1.open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=['episode_id','student_turn','tutor_context','previous_student_excerpt'])
            writer.writeheader()
            writer.writerow({'episode_id':'ND1-ONE','student_turn':'Let me try 17.',
               'tutor_context':'Correct reasoning: now find the missing value after the prior step.',
               'previous_student_excerpt':''})
        result=match(root/'data',nd1,root/'diag.csv')
        assert result['resolved']==1 and result['private_mapping_written']
        make_source(base/'task_id_0002'/'ai_tutoring_data')
        result=match(root/'data',nd1,root/'diag.csv')
        assert result['resolved']==0 and result['ambiguous']==1 and not result['private_mapping_written']
    print('PASS: synthetic unique-vs-ambiguous source match.')

if __name__=='__main__':test_reconstruction()
