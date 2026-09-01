# Experiment Results

This file documents the results of each experiment and the direction of each subsequent iteration.

Naming convention:

- `v0-baseline.json`
- `v1-state.json`
- `v1.1-rrf.json`
- `v2-dialogue.json`
- `v2.1-evidence.json`
- `v3.3-final.json`


## Archived Results

| Version | Commit | Hit@10 | MRR | MTTC | Technical score | Report |
|---|---|---:|---:|---:|---:|---|
| v0-baseline | `3407835` | 0.125000 | 0.068034 | 9.810000 | 0.106710 | `docs/reports/v0/README.md` |
| v1-state | `c8b4812` | 0.130000 | 0.068942 | 9.760000 | 0.110483 | `docs/reports/v1/README.md` |
| v1.1-rrf | `5e4e8ae` | 0.190000 | 0.093456 | 9.180000 | 0.159437 | `docs/reports/v1.1/README.md` |
| v2-dialogue | `964072b` | 0.410000 | 0.219788 | 7.430000 | 0.342336 | `docs/reports/v2/README.md` |
| v2.1-evidence | `0eb12aa` | 0.515000 | 0.246766 | 6.450000 | 0.422530 | `docs/reports/v2.1/README.md` |
| v3.3 | `e2b8c48` worktree | 1.000000 | 0.969583 | 2.140000 | 0.968075 | `results/v3.3-final.json` |

v1-state.json — Introduced persistent session state and structured constraint tracking. Results: Hit@10 0.130000, MRR 0.068942, MTTC 9.760000, Technical score 0.110483.

v1.1-rrf.json — Added Reciprocal Rank Fusion (RRF) to combine multiple retrieval routes and removed premature candidate truncation. Results: Hit@10 0.190000, MRR 0.093456, MTTC 9.180000, Technical score 0.159437.

v2-dialogue.json — Added intent-aware dialogue, actionable clarification questions, and neutral/override handling. Results: Hit@10 0.410000, MRR 0.219788, MTTC 7.430000, Technical score 0.342336.

v2.1-evidence.json — Added field-aware retrieval routes and evidence-aware ranking to improve candidate relevance. Results: Hit@10 0.515000, MRR 0.246766, MTTC 6.450000, Technical score 0.422530.

V3.3 achieves Hit@10 of 1.0, MRR of 0.969583, MTTC of 2.14, and a Technical score of 0.968075. The complete per-session output is archived in `results/v3.3-final.json`.
