# V3.3 Demo Video Script

## Recording goal

Create a 4.5–5 minute backend/NLP walkthrough that demonstrates the solution end to end, explains the most important engineering decisions, runs all four dialogue scenarios, and summarizes the full public-set result.

Use only the team's source code, terminal output, plain text, and generic catalog identifiers. Do not show product images, product titles, brand names, logos, private information, credentials, or unlicensed music.

## Timeline

| Time | Screen | Narration focus |
|---|---|---|
| 0:00–0:20 | Title and final metrics | Problem and one-sentence solution |
| 0:20–0:45 | README project overview | Dataset, four scenarios, deterministic local execution |
| 0:45–1:25 | Repository structure | Responsibilities of the important directories and files |
| 1:25–2:05 | Core source code | Agent orchestration, retrieval, ranking, and confidence gate |
| 2:05–3:30 | Four live inference traces | Buying, Browsing, Intent Override, and Boundary |
| 3:30–4:00 | Full V3.3 evaluation result | Aggregate metrics and scenario coverage |
| 4:00–4:25 | Version progression | How each iteration addressed a concrete failure mode |
| 4:25–4:50 | Limitations and future work | Honest technical boundaries |
| 4:50–5:00 | Closing title | Reproducibility and final message |

## 1. Opening

### Screen

Show a plain title:

```text
Conversational E-Commerce Search — V3.3

Hit@10: 1.000000
MRR: 0.969583
MTTC: 2.140000
Technical score: 0.968075
```

### Narration

> Shopping search often fails because users reveal their intent gradually, change their minds, or cannot provide a precise preference. We built a conversational search agent that handles these situations and recommends the correct catalog item as early as possible.
>
> The solution is deterministic, runs locally, and uses no LLM or external API. It searches 50,000 products and is evaluated on 200 public sessions covering Buying, Browsing, Intent Override, and Boundary behavior.

## 2. Project structure

### Screen

Expand only the important project paths:

```text
data/
  catalog.jsonl
  public_set.jsonl

artifacts/
  lexicon.json
  category_playbook.md

starter/
  agent.py
  constraints.py
  state.py
  intent.py
  dialogue_policy.py
  retrieval.py
  ranking.py

evaluator/
  local_evaluator.py
  debug_trace.py

results/
  README.md
  v3.3-final.json

tests/
```

### Narration

> Before running the demo, here is the project structure.
>
> The data directory contains the 50,000-product catalog and 200 public evaluation sessions.
>
> The artifacts directory contains the generated vocabulary and category clarification playbook.
>
> The starter package contains the production agent. Constraints parses user requirements. State maintains preferences across turns. Intent recognizes the four dialogue scenarios, and dialogue policy selects useful clarification questions.
>
> Retrieval implements multi-route SQLite FTS5 search and exact product-signature indexes. Ranking performs evidence-aware Reciprocal Rank Fusion.
>
> Agent connects these components into the end-to-end response pipeline.
>
> The evaluator package simulates customer conversations and calculates the metrics, while results contains the archived output for each version.

## 3. Core code walkthrough

### 3.1 `starter/agent.py`

Show these symbols:

- `signature_recommendation_limit()`
- `Agent.reset()`
- `Agent.respond()`
- constraint parsing, intent recognition, and state update
- retrieval, hard filtering, and reranking
- exact signature candidates and confidence-gated output

### Narration

> Agent.py is the orchestration layer. On every turn, it parses new constraints, recognizes the current intent, updates session state, retrieves candidates, applies hard filters, reranks the remaining products, and decides whether to return Top 1, Top 3, or Top 10.
>
> A key insight is that returning ten ambiguous products too early can end the conversation with a poor reciprocal rank. The confidence gate initially returns only the strongest candidate and expands the list only when the evidence supports it.

### 3.2 `starter/retrieval.py`

Show these symbols:

- `CatalogRetriever`
- `_build_index()`
- `retrieve_signature_candidates()`
- `_route_lists_for_turn()`
- `retrieve_route_candidates()`

### Narration

> Retrieval.py builds in-memory SQLite FTS5 indexes over titles, categories, attributes, stores, and descriptions. Different dialogue intents activate different retrieval routes.
>
> The exact-signature route normalizes catalog-supported requirements disclosed during the conversation and intersects their candidate sets.

### 3.3 `starter/ranking.py`

Show these symbols:

- `RANKING_CONFIGS`
- `evidence_boost_breakdown()`
- `reciprocal_rank_fusion_contributions()`
- `rerank_candidates()`

### Narration

> Ranking.py aggregates candidates from all active routes. Weighted Reciprocal Rank Fusion combines their route positions, while a bounded evidence multiplier rewards products that match active constraints. Neutral and invalidated preferences are excluded from the boost.

## 4. Four-scenario inference demo

### Run all scenarios through one agent initialization

```bash
python3 -m evaluator.debug_trace \
  --sample-id public_0083 \
  --sample-id public_0011 \
  --sample-id public_0002 \
  --sample-id public_0187 \
  --output /tmp/techjam-four-scenario-demo.json
```

The command should report:

```json
{
  "sample_count": 4,
  "hits": 4
}
```

The initial index build can be shortened with a transparent jump cut and this caption:

```text
Building local FTS5 and signature indexes over 50,000 products
```

### Safe per-scenario display

Change `buying` to `browsing`, `intent_override`, and `boundary` for the remaining cases:

```bash
jq '.sessions[]
  | select(.scenario_type == "buying")
  | {
      scenario: .scenario_type,
      target_catalog_id: .target_parent_asin,
      hit,
      first_hit_turn,
      best_rank,
      turns: [
        .turns[] | {
          turn,
          customer: .user_message,
          agent: .agent_message,
          ask_attribute,
          recommended_catalog_ids: (.recommendations[:3]),
          target_rank
        }
      ]
    }' /tmp/techjam-four-scenario-demo.json
```

This filtered output avoids product titles and brand content.

### 4.1 Buying — `public_0083`

> In the Buying scenario, the customer starts with a product category and an explicit material requirement. The agent asks for additional discriminating details instead of returning a broad list. After receiving the closure requirement, the target becomes rank one on turn three.

Expected outcome:

```text
first_hit_turn: 3
best_rank: 1
```

### 4.2 Browsing — `public_0011`

> In the Browsing scenario, the customer is still exploring and provides no precise product at first. The agent asks broad but actionable clarification questions. Material and closure details progressively narrow the search, placing the target at rank one on turn three.

Expected outcome:

```text
first_hit_turn: 3
best_rank: 1
```

### 4.3 Intent Override — `public_0002`

> In the Intent Override scenario, the customer explicitly changes the active requirement. The agent recognizes the override, updates the session state, and prevents superseded preferences from influencing later retrieval and ranking. The final target is ranked first on turn four.

Expected outcome:

```text
first_hit_turn: 4
best_rank: 1
```

### 4.4 Boundary — `public_0187`

> In the Boundary scenario, the customer initially says they have no additional preference. The agent records this as a neutral answer rather than applying an incorrect negative filter. It switches to another useful attribute, collects material and feature evidence, and ranks the target first on turn four.

Expected outcome:

```text
first_hit_turn: 4
best_rank: 1
```

## 5. Full evaluation

### Screen

```bash
jq '{
  sample_count,
  hit_rate_at_10,
  mrr,
  mttc,
  recommended_technical_score,
  reported_token_usage,
  scenario_metrics
}' results/v3.3-final.json
```

### Narration

> Across all 200 public sessions, V3.3 achieves a Hit Rate at 10 of 1.0, an MRR of 0.969583, an MTTC of 2.14, and a Technical score of 0.968075.
>
> Every target is found by turn four. One hundred and eighty-nine of the 200 targets are ranked first, and the system reports zero prompt and completion tokens.

## 6. Version progression and impact

### Screen

Show the result-progression table in the root README.

### Narration

> Compared with the baseline, Hit Rate improves from 12.5 percent to 100 percent, while mean time to the correct recommendation falls from 9.81 turns to 2.14.
>
> The improvements were incremental: persistent state, multi-route fusion, intent-aware dialogue, evidence-aware ranking, exact signatures, and confidence-gated output.
>
> Because the system uses the Python standard library, local SQLite FTS5, and no hosted model, its runtime behavior is deterministic and does not require API credentials or model-serving costs.

## 7. Limitations and closing

### Narration

> The current result is limited to the public dataset. The parser is primarily English and rule-based, exact signatures depend on recognizable disclosure phrasing, and the indexes are rebuilt in memory.
>
> With more time, we would add a locked external holdout, multilingual and paraphrase evaluation, semantic retrieval, confidence calibration on unseen data, and persistent indexes.
>
> The complete architecture, setup, and reproduction steps are documented in the project README. Thank you for watching.

## Publishing checklist

- Use a plain text title and thumbnail without third-party logos.
- Do not display product images, product titles, brand names, private information, credentials, or unrelated browser tabs.
- Use no background music unless it is original or properly licensed.
- Upload the finished video to YouTube with visibility set to **Public**, not Unlisted.
- Verify the public link in a signed-out or private browser window.
- Add the public YouTube URL to the Devpost project description.
