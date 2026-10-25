#!/usr/bin/env python3
"""Synthetic safety regression checks for E13. No actual student data."""
from e13_features import event_features,features,assemble
import json,random
import pandas as pd

def ev(pos,typ,pid="",correct="",time=0):
    return dict(trajectory_position=str(pos),event_type=typ,
        practice_problem_id=pid,is_correct=correct,
        timestamp_elapsed_seconds=str(time),actor="system")
EVENTS=[
 ev(1,"practice_problem_shown","p1",time=0),
 ev(2,"practice_answer_submitted","p1","False",10),
 ev(3,"ai_tutor_message","p1",time=12),
 ev(4,"student_message","p1",time=18),
 ev(5,"practice_answer_submitted","p1","True",35),
 ev(6,"practice_problem_shown","p2",time=40),
 ev(7,"practice_answer_submitted","p2","True",55),
]
def main():
    p,c,s=event_features(EVENTS)
    assert p["prov_n_attempted"]==2,p
    assert p["prov_correction_count"]==1,p
    assert p["prov_first_correct_rate"]==.5,p
    assert p["prov_last_correct_rate"]==1.,p
    assert p["prov_repeated_fraction"]==.5,p
    assert c["count_event_A"]==3
    assert s["seq_tutor_between_attempt_fraction"]==1.
    assert s["seq_student_between_attempt_fraction"]==1.
    assert s["seq_n_valid_resubmit_times"]==1
    assert s["seq_median_resubmit_seconds"]==25
    for seed in range(1,24):
        x,c2,y=event_features(EVENTS,seed)
        assert x==p,("Provenance changed after temporal shuffle",seed)
        assert c2==c,("Event counts changed after temporal shuffle",seed)
        assert y["seq_first_sequence_support"]==2
        assert len([k for k in y if k.startswith("seq_ev_")])==14
    # The only legitimate null permutations alter order, never posttest
    # outcomes, first/final correctness or number of practice submissions.
    print("PASS: synthetic provenance invariance, no posttest-leakage input, 23 temporal shuffles")
if __name__=="__main__":main()
