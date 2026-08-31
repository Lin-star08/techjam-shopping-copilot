# Competition Data

## `public_set.jsonl`

Contains 200 labeled development sessions: 80 Buying, 80 Browsing, 30 Intent Override, and 10 Boundary sessions.

Each session contains a safe aggregate `user_profile` and public labels for local development. Direct user identifiers, timestamps, free-text reviews, raw purchase history, hidden intent cards, and simulator-policy internals are not shipped in this participant file.

## `catalog.jsonl`

Download `catalog.jsonl.gz` from the GitHub Release and decompress it as `catalog.jsonl` in this directory. Expected row count: 50,000.

Never place API keys, private evaluation data, or participant outputs in this directory.

## `public_set1.jsonl`

Contains 3,021 unique product records used by the V2.2 product-knowledge ablation. It is a catalog-shaped knowledge source, not an evaluator session dataset: it has no `sample_id`, `scenario_type`, `user_profile`, or `ground_truth` fields. Its ASINs are all present in `catalog.jsonl` and do not overlap the 200 public target ASINs.
