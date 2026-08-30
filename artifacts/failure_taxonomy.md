# Failure Taxonomy

This is the required Member 1 delivery artifact. Add only evidence-backed
failures observed during evaluation; do not encode public target answers or
session-specific ASIN lookup rules.

## Allowed failure classes

- `retrieval_miss`: the target was not present in the retrieved candidate pool.
- `state_error`: current valid preferences were lost, or invalidated preferences resurfaced.
- `hard_filter_error`: an uncertain or incorrectly parsed condition removed valid candidates.
- `rerank_error`: the target was retrieved but ranked too low.
- `low_value_question`: the clarification repeated, contradicted, or failed to narrow candidates.

## Record template

### FXXX - Short title

- Scenario: Buying / Browsing / Intent Override / Boundary
- Evidence source: development or internal holdout
- Observed behavior:
- Failure class:
- Generalizable rule:
- Owning module: state / constraints / retrieval / ranking / clarification
- Expected metric impact: HitRate@10 / MRR / MTTC
- Regression risk:
- Validation test:
- Status: proposed / accepted / rejected

## Confirmed records

No rule has been confirmed yet. Populate this section only after reviewing
evaluation failures and validating the rule without public-answer special cases.
