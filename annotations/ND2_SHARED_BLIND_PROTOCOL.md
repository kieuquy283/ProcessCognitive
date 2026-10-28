# ND2 — Common blind annotation rules for BOTH annotators

**This document is procedural, NOT the semantic codebook.** Before starting, the research coordinator MUST find and freeze the authoritative ND1 codebook with complete definitions, worked examples and precedence rules for the seven `primary_act` categories and five `feedback_uptake` categories. A list of abbreviations or past labels is NOT a codebook. If no full codebook is available, STOP, do not guess.

Source: official StudentBench pinned revision `304c8d63c726e72b60510bba3a44454fc0726721`. Sample: exactly **200 naturally sampled + 80 lexical challenge** student turns from 280 separate GRE tutoring sessions, after manual verification that none overlap the 40 ND1 source sessions. The previous 200+80 result was a *sampling preflight*, NOT the finalized ND2 sample.

Unit of decision: current student turn, using only prior student excerpt and AI tutor messages preceding it. The source inputs MUST be identical for both annotators, and should retain the full source context. Do NOT use future tutor/student events, pre/post assessment scores, other model labels, ND1 adjudications or research metrics.

Allowed categorical values:
- `primary_act`: AK, AN, CQ, HR, OT, RE, VE.
- `feedback_uptake`: AC, AP, NO, NR, UN.
- `confidence`: high, medium, low. Confidence is ordinal and not calibrated.

Follow exactly the frozen codebook semantics and precedence rules; don't implement shallow keyword matching or infer private psychological states. Each output has exactly one act, one uptake code, a brief English evidence-based rationale, and confidence. If the input context is technically missing/truncated, request corrected input rather than pretending an `UN` annotation means unread data.

Both CSVs must preserve this eight-column schema, original order and immutable first four fields:
```csv
episode_id,previous_student_excerpt,tutor_context,student_turn,primary_act,feedback_uptake,annotation_rationale,confidence
```
The 40 ND1 labels, Gemini/Claude historical outputs, current ND2 annotation results and any agreement reports are **off-limits** to both annotators. Each annotator works in an isolated environment and may use code for I/O and validation only, not automatic decisions. Record *verified* model name/ID, codebook SHA-256, data SHA-256, prompt SHA-256, interface, parameters, run date and any truncation.

**No individual chat, session mapping, raw annotation CSV or student-level outputs belong in GitHub or GitHub Actions artifacts.** Use ignored local folders `data/`, `annotation_work/`. Validate both outputs and model metadata first; only then compare Astra conventional-reference vs Claude, reporting 200 random and 80 challenge separately. Inter-LLM agreement does NOT establish human construct validity.
