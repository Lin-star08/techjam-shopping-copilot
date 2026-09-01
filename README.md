# Conversational E-Commerce Search

## Project overview

This project implements a deterministic conversational shopping agent for the TechJam Conversational E-Commerce Search Challenge. Given an anonymized preference profile and a customer message, the agent can ask one clarification question and return up to 10 ranked product `parent_asin` values on each turn. Evaluation uses exact ASIN matching over at most 10 turns.

The current V3.3 implementation does not call an LLM or any external API. It reports zero prompt and completion tokens and uses only the Python standard library.

### How the solution works

1. **State and constraints:** `starter/state.py` and `starter/constraints.py` retain confirmed category, material, color, size, brand, budget, feature, style, and use-case signals across turns. Neutral answers clear the affected preference, while overrides invalidate superseded values.
2. **Intent and clarification:** `starter/intent.py` recognizes Buying, Browsing, Intent Override, and Boundary behavior from the current message. `starter/dialogue_policy.py` selects a non-repeated clarification question and asks at most three attributes.
3. **Retrieval:** `starter/retrieval.py` builds in-memory SQLite FTS5 indexes over the 50,000-product catalog. It retrieves through message, state, title, category, attribute, requirement, profile, popularity, relaxed, and fallback routes.
4. **Exact catalog signatures:** Product features and details are normalized into signature indexes. When the conversation exposes exact catalog-supported requirements, the agent intersects those observations to narrow the candidate set.
5. **Filtering and ranking:** Hard constraints filter candidates before `starter/ranking.py` combines route ranks with weighted Reciprocal Rank Fusion and a bounded evidence boost.
6. **Confidence-gated output:** `starter/agent.py` returns Top 1 under weak evidence, up to Top 3 for a small exact-signature group after one concrete answer, and up to Top 10 after stronger evidence or a declined Boundary question.
7. **Evaluation:** `evaluator/local_evaluator.py` simulates the customer dialogue and reports Hit@10, MRR, MTTC, token usage, scenario metrics, and the recommended Technical score.

### Data

The repository contains:

- `data/catalog.jsonl`: 50,000 products from the Amazon Reviews 2023 `Clothing_Shoes_and_Jewelry` category.
- `data/public_set.jsonl`: 200 labeled public sessions: 80 Buying, 80 Browsing, 30 Intent Override, and 10 Boundary.
- `artifacts/lexicon.json` and `artifacts/category_playbook.md`: generated vocabulary and clarification assets used by the rule-based pipeline.

See `DATA_ATTRIBUTION.md` for dataset attribution and permitted-use guidance.

### Result progression

| Version | Main improvement | Hit@10 | MRR | MTTC | Technical score |
|---|---|---:|---:|---:|---:|
| V0 baseline | Initial retrieval baseline | 0.125000 | 0.068034 | 9.810000 | 0.106710 |
| V1 state | Persistent session state and structured constraint tracking | 0.130000 | 0.068942 | 9.760000 | 0.110483 |
| V1.1 RRF | Multi-route Reciprocal Rank Fusion and removal of premature candidate truncation | 0.190000 | 0.093456 | 9.180000 | 0.159437 |
| V2 dialogue | Intent-aware clarification with neutral and override handling | 0.410000 | 0.219788 | 7.430000 | 0.342336 |
| V2.1 evidence | Field-aware retrieval routes and evidence-aware ranking | 0.515000 | 0.246766 | 6.450000 | 0.422530 |
| **V3.3 final** | Exact signature matching, catalog-driven clarification, and confidence-gated output | **1.000000** | **0.969583** | **2.140000** | **0.968075** |

The archived V3.3 result is `results/v3.3-final.json`. It contains all 200 per-session records. All targets are found by turn 4: 46 on turn 1, 101 on turn 2, 32 on turn 3, and 21 on turn 4. The final target ranks are 189 at rank 1, eight at rank 2, two at rank 3, and one at rank 4.

## Setup and installation instructions

### Requirements

- Python 3.10 or later
- A Python build with SQLite FTS5 enabled
- Git

No third-party Python packages, model downloads, API keys, or network services are required at runtime.

### Installation

Clone the final `main` branch and enter the repository:

```bash
git clone --branch main --single-branch https://github.com/Lin-star08/techjam-shopping-copilot.git
cd techjam-shopping-copilot
```

Confirm the Python version, input files, and SQLite FTS5 support:

```bash
python3 --version
wc -l data/catalog.jsonl data/public_set.jsonl
python3 -c "import sqlite3; db = sqlite3.connect(':memory:'); db.execute('CREATE VIRTUAL TABLE check_fts USING fts5(text)'); print('SQLite FTS5 available')"
```

The expected row counts are 50,000 for `data/catalog.jsonl` and 200 for `data/public_set.jsonl`.

Run the verified core test suite:

```bash
python3 -m unittest -q \
  tests.test_agent_state \
  tests.test_constraints \
  tests.test_debug_trace \
  tests.test_dialogue_policy \
  tests.test_evaluation_assets \
  tests.test_evaluator \
  tests.test_intent \
  tests.test_lexicon \
  tests.test_ranking \
  tests.test_retrieval \
  tests.test_state
```

This command currently runs 142 tests.

## Steps to reproduce your results

1. Start from the repository root with the tracked catalog and public set in `data/`.
2. Clear any ranking override and run the local evaluator on all 200 public sessions:

   ```bash
   env -u RANKING_CONFIG_NAME python3 -m evaluator.local_evaluator \
     --catalog data/catalog.jsonl \
     --dataset data/public_set.jsonl \
     --output /tmp/v3.3-final.json
   ```

   The evaluator prints aggregate and scenario metrics to the terminal and writes the complete per-session result to `/tmp/v3.3-final.json`.

3. Verify the reproduced aggregate metrics:

   ```bash
   python3 -c "import json; r=json.load(open('/tmp/v3.3-final.json')); print({k:r[k] for k in ('sample_count','hit_rate_at_10','mrr','mttc','recommended_technical_score','reported_token_usage')})"
   ```

   Expected values:

   ```text
   sample_count: 200
   hit_rate_at_10: 1.0
   mrr: 0.969583
   mttc: 2.14
   recommended_technical_score: 0.968075
   reported_token_usage: 0 prompt tokens, 0 completion tokens
   ```

4. Compare the reproduced metrics with the archived result in `results/v3.3-final.json`. Historical version outputs are also stored under `results/`.

5. Record the exact submitted revision and result checksum so the evaluation can be audited after the final merge to `main`:

   ```bash
   git rev-parse HEAD
   shasum -a 256 data/catalog.jsonl data/public_set.jsonl results/v3.3-final.json
   ```

   The archived result must be regenerated from the same frozen `main` revision that is submitted for judging.

The evaluator uses exact `parent_asin` equality. A miss contributes turn 11 to MTTC, and the reported composite is:

```text
Efficiency = clip((11 - MTTC) / 10, 0, 1)
Technical score = 0.50 × Hit@10 + 0.30 × MRR + 0.20 × Efficiency
```

## Limitations and future improvements

The final public-set result is strong, but it should not be treated as evidence of general performance beyond this dataset.

- **Public-set validation only:** V3.3 is reported on the 200 tracked public sessions. The repository does not contain a locked external or private holdout result for this version. Given more time, we would freeze a larger unseen evaluation set before making further ranking or dialogue changes.
- **Simulator-sensitive exact matching:** The signature route recognizes a small set of disclosure phrases and intersects normalized catalog features. Different dialogue wording or product metadata may reduce its effectiveness. We would add paraphrase-heavy and out-of-distribution tests and make evidence extraction less dependent on fixed phrases.
- **Rule-based language coverage:** Intent and constraint parsing rely on English regular expressions and a generated vocabulary. Misspellings, multilingual input, implicit preferences, and unseen synonyms are not comprehensively handled. We would improve normalization and evaluate a local semantic retrieval model while preserving deterministic fallbacks.
- **In-memory indexing:** The complete catalog and multiple FTS5/signature indexes are rebuilt when an `Agent` is created. Startup time and peak memory are not reported. We would benchmark both and consider a persistent prebuilt index.
- **Fixed ranking and confidence rules:** Route weights, evidence boosts, and Top-K thresholds are hand-configured. We would calibrate them on a locked development set and validate them on unseen sessions.

## Team member contributions

- **evelynn yu — Product knowledge and taxonomy:** built the catalog-derived lexicon, category normalization rules, generated knowledge artifacts, and clarification playbook.
- **jie Zhao — Conversation intelligence:** implemented session-state tracking, constraint parsing, intent recognition, neutral and override handling, and the clarification policy.
- **naka li — Retrieval:** implemented the SQLite FTS5 search pipeline, multi-route retrieval, candidate evidence, fallback retrieval, and exact catalog-signature indexes.
- **JINGLIN WANG — Ranking and integration:** implemented candidate aggregation, weighted Reciprocal Rank Fusion, deterministic reranking, ranking ablations, and final branch integration.
- **Yiyong Zhang — Evaluation and delivery:** ran versioned evaluations, analyzed failure cases, archived final results, checked reproducibility, and prepared submission documentation.
