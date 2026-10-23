# StudentBench diagnostic experiments

This feature branch contains a **minimal reproducible session-level baseline**. It does not yet include the previously drafted item-level or E7/E8 scripts, nor does it reproduce the pilot numbers in previous chat messages.

## Run

1. Download the official StudentBench data and extract it under `./data` following https://github.com/Handshake-AI-Research/studentbench.
2. Install: `pip install -r requirements.txt`.
3. Run: `python experiments/session_baseline.py --data ./data --output ./results`.

The script evaluates pretest only, pretest + practice counts, and pretest + practice + interaction counts with fourfold session-grouped cross-validation on an approximately 80% development split. The remaining sessions are **not evaluated**. Results are written to `results/session_baseline.json`.

**Limitations:** outcome is posttest total percentage, not item-level correctness. No deep semantic encoder or GRU is included. Results do not support causal conclusions about learning. Check the exact dataset revision and sample inclusion before comparing pilot numbers.

Never commit raw transcripts, participant-level records, API keys, or full downloaded datasets.
