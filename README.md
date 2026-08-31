# TechJam Conversational E-Commerce Search Challenge

Build an AI shopping agent that asks useful follow-up questions and recommends the customer's hidden target product within at most 10 turns.

## Final Submission: V3.2

Public repository: **https://github.com/Lin-star08/techjam-shopping-copilot**

Submission document: [`docs/submission/TechJam_V3.2_Written_Project_Description.docx`](docs/submission/TechJam_V3.2_Written_Project_Description.docx)

V3.2 is a deterministic, zero-API-cost conversational shopping agent. It combines session-state tracking, four-way intent recognition, catalog-driven clarification, conservative constraint handling, SQLite FTS5 recall, structured product-signature matching, evidence-aware reciprocal-rank fusion, and confidence-gated candidate expansion. The agent asks only questions that can change retrieval, carries confirmed constraints across turns, invalidates superseded preferences, and expands from Top 1 to Top 3 or Top 10 only when the accumulated evidence supports it.

On the frozen 200-session public evaluator, the final implementation achieves:

| Metric | Target | V3.2 result |
|---|---:|---:|
| Hit Rate@10 | > 0.98 | **1.000000** |
| MRR | > 0.95 | **0.969583** |
| MTTC | < 2.16 | **2.140000** |
| TechnicalScore | — | **0.968075** |

All 200 targets are found by turn 4. Rank 1/2/3/4 hit counts are `189/8/2/1`; first-hit turn 1/2/3/4 counts are `46/101/32/21`.

## Solution Architecture

1. **Session and constraint state** (`starter/state.py`, `starter/constraints.py`) records category, material, color, feature, budget, neutral answers, and overrides without exposing user identity.
2. **Intent and dialogue policy** (`starter/intent.py`, `starter/dialogue_policy.py`) distinguishes Buying, Browsing, Intent Override, and Boundary sessions, then asks a catalog-supported, high-information clarification question.
3. **Multi-route retrieval** (`starter/retrieval.py`) combines current-message, state, category, requirement, profile, and popularity routes through SQLite FTS5. A structured signature index provides exact intersections over normalized product attributes.
4. **Evidence-aware ranking** (`starter/ranking.py`) fuses routes using reciprocal-rank fusion and stable popularity tie-breaking. It does not use public sample IDs, target ASINs, or evaluator internals.
5. **Confidence gate** (`starter/agent.py`) emits Top 1 with weak evidence, up to Top 3 for a small exact-signature candidate group after one concrete answer, and Top 10 only after stronger evidence or a declined Boundary question.
6. **Reproducible evaluation** (`tools/run_goal_workflow.py`) runs tests, a fixed development/holdout split, label-leakage checks, the unchanged evaluator, strict metric gates, and result provenance hashes.

The progression from the weak starter to V3.2 was deliberate: state tracking improved consistency; RRF increased recall; intent-aware dialogue reduced wasted turns; evidence ranking improved early precision; `public_set1.jsonl` supplied catalog vocabulary and clarification rules; exact product signatures closed remaining recall gaps; and the final confidence gate reduced MTTC while preserving MRR.

## Development Environment, APIs, and Libraries

- **Tools:** VS Code, macOS Terminal, Git, and Python 3.11.1. The code supports Python 3.10 or later.
- **APIs/models:** none at runtime. V3.2 makes no OpenAI, Google, hosted-model, or network API calls and reports zero prompt/completion tokens.
- **Libraries/frameworks:** Python standard library only, including `sqlite3`/FTS5, `json`, `re`, `dataclasses`, `pathlib`, `collections`, `statistics`, `unittest`, and `argparse`. PyTorch, Transformers, scikit-learn, and pandas are not required.
- **Datasets/assets:** the frozen 50,000-item Amazon Reviews 2023 `Clothing_Shoes_and_Jewelry` catalog; 200 labeled public dialogue sessions; `public_set1.jsonl` with 3,021 catalog-shaped product rows for vocabulary and product-knowledge development; and generated `lexicon.json` / `category_playbook.md` assets. See `DATA_ATTRIBUTION.md` for source and redistribution notes.

## Setup and Installation

1. Clone the public repository and enter it:

   ```bash
   git clone https://github.com/Lin-star08/techjam-shopping-copilot.git
   cd techjam-shopping-copilot
   ```

2. Use Python 3.10+; no third-party package installation is required.

3. Download `catalog.jsonl.gz` from the repository release, verify it against `SHA256SUMS`, and unpack it:

   ```bash
   gzip -dk catalog.jsonl.gz
   mv catalog.jsonl data/catalog.jsonl
   ```

4. Confirm that `data/public_set.jsonl` is present, then run the test suite:

   ```bash
   python3 -m unittest discover -s tests -q
   ```

## Reproduce the V3.2 Results

Run the frozen workflow for the development split, full public set, and internal holdout:

```bash
python3 -m tools.run_goal_workflow \
  --split development \
  --output results/v3.2-confidence-development.json

python3 -m tools.run_goal_workflow \
  --split full \
  --open-holdout \
  --output results/v3.2-confidence-full.json \
  --skip-tests

python3 -m tools.run_goal_workflow \
  --split holdout \
  --open-holdout \
  --output results/v3.2-confidence-holdout.json \
  --skip-tests
```

The detailed result narrative is in `docs/reports/v3.2/README.md`; metric provenance, data/result hashes, test counts, and audit status are in `results/v3.2-confidence-evidence.json`.

## Limitations and Future Improvements

- The signature route relies on the competition generator's catalog-metadata normalization and disclosure order; distribution shifts require fresh validation.
- The 50-session internal holdout reaches MTTC `2.160000`, equal to rather than below the strict target, so the full-set MTTC margin is modest.
- Rule-based parsing is transparent and inexpensive but may be brittle for multilingual, misspelled, or highly implicit real-world requests.
- Popularity is a stable tie-breaker rather than a personalized preference model; richer privacy-safe preference learning could improve ambiguous cases.
- Given more time, we would add adversarial paraphrase tests, uncertainty calibration on unseen catalogs, multilingual normalization, latency/memory benchmarks, and a larger locked external holdout.

## Team Contributions

The contribution summary below is based on the repository's Git history; `TechJam2026` commits are upstream organizer changes rather than participant work.

- **sjie-z:** session state, four-way intent recognition, clarification policy, and dialogue-agent integration.
- **Li Cheng:** retrieval/search pipeline, recall improvements, evidence integration, and intent-flow integration.
- **Lin-star08:** reciprocal-rank fusion, reranking ablations, evidence-aware reranking, and branch/PR integration.
- **tangerineat1-cpu:** product-knowledge lexicon, category rules, and versioned knowledge artifacts.
- **Beijing Yuhui Drone Service:** baseline/final evaluation artifacts, dataset/result integration, and reported evidence.
- **linaka0517-create and yz4719:** search/evaluation branch integration and merge support recorded in Git history.

## What You Receive

- A frozen catalog of 50,000 products from the `Clothing_Shoes_and_Jewelry` category of Amazon Reviews 2023.
- 200 labeled public sessions for local development.
- A weak BM25 starter agent and deterministic local evaluator.
- The Agent API contract and scoring rules.

The organizer keeps 800 additional sessions private for final evaluation.

## Task

For each session, your agent receives an anonymized preference profile and a short customer message. Raw user IDs, review text, timestamps, and purchase history are never disclosed. On every turn the agent may:

- ask a natural clarification question in `message` and identify one requested field in `ask_attribute`;
- return a ranked list of up to 10 catalog `parent_asin` values;
- do both in the same response.

The session ends when the target product appears in the scored Top 10 or after turn 10. Sessions cover Buying, Browsing, Intent Override, and Boundary behavior.

## Download the Catalog

Download `catalog.jsonl.gz` from the GitHub Release attached to this repository, then run:

```bash
gzip -dk catalog.jsonl.gz
mv catalog.jsonl data/catalog.jsonl
```

Verify the downloaded file using the published `SHA256SUMS` file.

## Run the Starter

Python 3.10 or later is recommended. The starter uses only the Python standard library.

```bash
python3 -m evaluator.local_evaluator
```

Edit `starter/agent.py` to implement your system. Do not edit the evaluator or public labels when reporting your local score.
The command writes per-session results and aggregate metrics to `results.json`.

The included weak BM25 starter scores Hit Rate@10 `0.125`, MRR `0.068034`, and
MTTC `9.81` on the released public set. See `docs/baseline_results.json`.

## Agent Interface

```python
class Agent:
    def reset(self, session_id: str, user_profile: dict) -> None:
        ...

    def respond(self, session_id: str, user_message: str, turn: int, top_k: int) -> dict:
        return {
            "message": "Do you have a material preference?",
            "ask_attribute": "material",
            "recommendations": [
                {"parent_asin": "B000..."},
                {"parent_asin": "B001..."}
            ],
            "usage": {"prompt_tokens": 120, "completion_tokens": 30}
        }
```

`ask_attribute` is one of `category`, `material`, `color`, `size`, `style`, `brand`, `budget`, `feature`, `use_case`, `other`, or `null`. See `docs/agent_api_contract.json`.

## Technical Metrics

- **Hit Rate@10:** fraction of sessions that find the target within 10 turns.
- **MRR:** mean reciprocal rank of the target; a miss contributes zero.
- **MTTC:** mean first-hit turn; a miss is assigned turn 11.
- **Reported token usage:** prompt and completion tokens returned by the team's model client.

```text
TechnicalScore = 0.50 × HitRate@10 + 0.30 × MRR + 0.20 × Efficiency
Efficiency = clip((11 - MTTC) / 10, 0, 1)
```

`TechnicalScore` is an objective input to the `Technical Execution` assessment. It is not a separate judging criterion and does not represent the entire `Technical Execution` score.

Only exact `parent_asin` equality produces a hit. Core metrics are also reported by scenario.

## Model Choice and Cost

Teams may use any legally accessible LLM API or local model. Teams manage their own credentials and must never commit API keys. Model choice, estimated cost, token usage, and latency must be disclosed. Token usage is a feasibility metric, not part of the core technical score. The organizer does not provide or reimburse model API credits; teams are responsible for any costs incurred through optional external services.

## Files

```text
data/public_set.jsonl             200 labeled development sessions
docs/competition_specification.md participant rules and evaluation protocol
docs/agent_api_contract.json      machine-readable Agent contract
docs/evaluation_config.json       scoring configuration
docs/baseline_results.json        reproducible weak-starter reference score
starter/agent.py                  editable weak starter
evaluator/local_evaluator.py      public-set simulator and scorer
```

## Judging and Submission Policy

- Participant submission requirements: `docs/submission_rules.md`
- Organizer-only final judging controls: `organizer/JUDGING_RUNBOOK.md`
- Organizer private release checklist: `organizer/private_release_checklist.md`
- Judging day operations SOP: `organizer/JUDGING_DAY_SOP.md`

## Data Source

The catalog and sessions are derived from Amazon Reviews 2023 by McAuley Lab, UCSD. See `DATA_ATTRIBUTION.md` before using or redistributing the data.
Sessions are sampled deterministically from the official Clothing 5-core leave-last-out split and joined to the frozen catalog.
