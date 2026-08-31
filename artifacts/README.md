# Artifacts

This directory contains the shared knowledge assets and supporting notes used by the team. Ownership and delivery rules follow the [team delivery contract](<../team_delivery_contract(1).md>).

## Member 1 Deliverables

| File | Purpose | Consumers | Acceptance check |
| --- | --- | --- | --- |
| `lexicon.json` | Machine-readable vocabulary, aliases, category rules, coverage statistics, and question order | Members 2, 3, and 4 | Loads with Python `json.load()`; terms and statistics come from the catalog |
| `category_playbook.md` | Human-readable category findings, follow-up order, and handoff notes | Whole team | Matches the `category_playbook` section in `lexicon.json` |
| `failure_taxonomy.md` | Confirmed failure patterns, handling rules, owners, and regression checks | Members 2, 3, 4, and 5 | Every finding is evidence-backed and contains no public-answer special case |

`build_lexicon.py` rebuilds `lexicon.json` and `category_playbook.md`. Keep the generator in sync with both generated files so a later rebuild does not overwrite a valid change.

## Current Version

- Asset version: V3
- Schema version: `1.3`
- Catalog: `data/catalog.jsonl`
- Products scanned: 50,000
- Evidence terms: 202
- Category aliases: 171
- Quality flags: 36 accurate, 165 broad, 13 ambiguous, and 0 noise; flags may overlap
- Public ground truth: not used to build vocabulary, aliases, or category rules

## Downstream Use

- Member 2 reads the attribute vocabulary and `category_playbook[*].question_order`. Attributes already answered, asked, or marked neutral should be skipped.
- Member 3 uses aliases, field coverage, and unreliable-category rules. Ambiguous terms remain soft evidence; an alias or broad leaf alone must never trigger a hard filter.
- Member 4 may use stronger evidence for explicit, accurate matches. Broad evidence should be capped or downweighted, while ambiguous evidence needs route context.
- Member 5 runs the full evaluation after integration and updates the failure review and experiment log when new issues appear.

## Unreliable Category Rules

- `Casual`: use the parent as the product type and keep `casual` as the style.
- `Sets`: combine it with the nearest informative parent, such as `Sleepwear Sets` or `Bikini Sets`.
- `Women` and `Men`: treat them as audience labels, not product types.
- `Westlake` and `Clothing`: do not use the leaf itself as a product type. A title may provide soft evidence; ask for the category when the title is unclear.
- Keep the original catalog path for audit whenever a derived category is used.

## Rebuild and Validate

Run these commands from the repository root:

```bash
python artifacts/build_lexicon.py
python -m unittest discover -s tests -p "test_lexicon.py" -v
```

To check the JSON independently:

```bash
python -c "import json; json.load(open('artifacts/lexicon.json', encoding='utf-8')); print('lexicon ok')"
```

Before delivery, confirm that:

1. `lexicon.json` loads successfully and its `version` and `updated_at` fields are current.
2. `category_playbook.md` matches the generator output.
3. The change does not modify `evaluator/`, `data/public_set.jsonl`, `data/catalog.jsonl`, or the official evaluation configuration.
4. No API keys, private data, public target ASINs, or session-specific lookup rules are included.
5. Members 2, 3, and 4 are notified before any shared field or schema changes.
