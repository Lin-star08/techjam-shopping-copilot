# Failure Taxonomy v3

This is the required Member 1 delivery artifact. It records only aggregate,
evidence-backed v1.1 failures. It must not be used to encode public target
answers, target ASINs, or session-specific lookup rules.

## v1.1 result context

- Evaluated commit: `5e4e8ae`; comparison version: V1 commit `c8b4812`.
- Full public set (200 cases): HitRate@10 `0.190000`, MRR `0.093456`, MTTC `9.180000`.
- Change from V1: HitRate@10 `+0.060000`, MRR `+0.024514`, MTTC `-0.580000`.
- V1.1 gained 13 hits and lost 1 hit, for a net gain of 12.
- All 1,674 legal responses returned `ask_attribute = null`.
- Formal metrics come from `results/v1.1-rrf.json`. Candidate-funnel counts came from a temporary runtime hook and are diagnostic evidence, not fields in the formal result file.

## Allowed failure classes

- `retrieval_miss`: the target was absent from the post-filter candidate pool on every valid turn.
- `hard_filter_error`: an uncertain or incorrectly parsed condition removed a valid candidate on a turn.
- `rerank_error`: the target was retrieved but ranked below Top 10, or a previously successful target was demoted.
- `state_error`: a current valid preference was lost, or an invalidated preference resurfaced.
- `override_underweighting`: evidence from the latest explicit intent did not receive enough ranking weight.
- `missing_clarification`: the system had an informative question available but returned no question.
- `interaction_gap`: a scenario metric improved without exercising the interaction behavior the scenario is intended to test.
- `evidence_overbreadth`: a term matches so many unrelated leaf categories that its boost has little separating power.
- `evidence_attribute_collision`: the same term is configured for multiple attributes and route precedence assigns the wrong meaning.
- `context_free_alias`: an alias such as `Sets` is used without the parent category needed to identify the product type.
- `attribute_fallback_mislabel`: a recognized value has no dedicated classifier and falls through to the generic `feature` label.

## Confirmed v1.1 records

### F101 - Clarification was absent in every scenario

- Scenario: Buying / Browsing / Intent Override / Boundary
- Evidence source: full public v1.1 trace
- Observed behavior: All 1,674 legal responses returned `ask_attribute = null`; Browsing had 666 fixed retry turns and Buying had 504 fixed retry turns without a question.
- Failure class: `missing_clarification`
- Generalizable rule: When the live candidate set is broad and an unasked, non-neutral attribute has at least two meaningful values, ask exactly one question from the category question order.
- Owning module: clarification / state
- Expected metric impact: HitRate@10 / MTTC
- Regression risk: Asking a low-coverage or already-neutral attribute can add turns without narrowing candidates.
- Validation test: Verify one-question maximum, `asked_attributes`, no-preference skip, and `ask_attribute = null` after the useful order is exhausted.
- Status: accepted

### F102 - Targets were missing from post-filter candidates

- Scenario: Buying / Browsing / Intent Override / Boundary
- Evidence source: full public v1.1 diagnostic candidate funnel
- Observed behavior: Targets were absent from the post-filter pool in 19/80 Buying, 37/80 Browsing, 10/30 Intent Override, and 2/10 Boundary cases.
- Failure class: `retrieval_miss`
- Generalizable rule: Treat uncertain material, feature, style, size, and use-case matches as soft evidence; hard-filter only explicit, high-confidence constraints.
- Owning module: constraints / retrieval
- Expected metric impact: HitRate@10 / MRR
- Regression risk: Making every condition soft can enlarge candidate pools and reduce precision.
- Validation test: Audit target presence before and after each filter on development and internal holdout, grouped by attribute.
- Status: accepted

### F103 - Recalled candidates remained below Top 10

- Scenario: Buying / Browsing / Intent Override / Boundary
- Evidence source: full public v1.1 diagnostic candidate funnel
- Observed behavior: Recalled targets still missed Top 10 in 37 Buying, 37 Browsing, 15 Intent Override, and 5 Boundary cases.
- Failure class: `rerank_error`
- Generalizable rule: Distinguish strong current-message evidence from repeated generic route evidence; route agreement alone must not dominate explicit need match.
- Owning module: ranking
- Expected metric impact: HitRate@10 / MRR / MTTC
- Regression risk: Increasing one route globally may improve one scenario while demoting strong shared hits in another.
- Validation test: Log per-route rank contribution and compare Top 10, Top 50, and reciprocal rank by scenario.
- Status: accepted

### F104 - Equal-weight fusion lost one prior Buying hit

- Scenario: Buying
- Evidence source: full public v1.1 comparison and diagnostic trace
- Observed behavior: V1.1 gained 5 Buying hits but lost 1 prior hit; the lost target remained a candidate and its best RRF rank was 13.
- Failure class: `rerank_error`
- Generalizable rule: Preserve strong single-route, explicit-current-message matches when several weaker routes agree on alternatives.
- Owning module: ranking
- Expected metric impact: HitRate@10 / MRR
- Regression risk: A preservation bonus that is too large can defeat useful multi-route fusion.
- Validation test: Add a regression test that checks rank churn for shared hits and reports gained, lost, promoted, and demoted cases.
- Status: accepted

### F105 - Intent Override gained a hit but lost MRR

- Scenario: Intent Override
- Evidence source: full public v1.1 result and diagnostic candidate funnel
- Observed behavior: HitRate@10 rose by `0.033334`, but MRR fell from `0.111111` to `0.097778`; all 5 hits occurred on turn 4, and 15 recalled targets were below Top 10.
- Failure class: `override_underweighting`
- Generalizable rule: The latest explicit intent and its normalized synonyms should outrank stale or generic evidence after an override.
- Owning module: state / constraints / ranking
- Expected metric impact: MRR / HitRate@10
- Regression risk: Over-aggressive override handling can erase valid constraints that the user did not replace.
- Validation test: Test same-attribute replacement separately from cross-attribute intent changes, and compare final-turn ranks.
- Status: accepted

### F106 - Boundary gains did not validate no-preference handling

- Scenario: Boundary
- Evidence source: full public v1.1 trace
- Observed behavior: Boundary HitRate@10 improved from `0.000000` to `0.300000`, but all Boundary responses still had `ask_attribute = null` and the no-preference branch was never triggered.
- Failure class: `interaction_gap`
- Generalizable rule: Do not treat a ranking-only gain as evidence that clarification, neutral-state recording, or asked-attribute handling works.
- Owning module: clarification / state / evaluation
- Expected metric impact: MTTC / HitRate@10
- Regression risk: Aggregate score gains can hide an entirely untested interaction path.
- Validation test: Add multi-turn tests in which the agent asks a real attribute, the user says no preference, state records it as neutral, and the next question changes.
- Status: accepted

## V2.1 catalog/code evidence audit

- Evaluated retrieval source: `starter/retrieval.py` from V2.1 commit `0eb12aa`; the exact source SHA-256 is recorded in `lexicon.json`.
- Audit source: all 50,000 products in `data/catalog.jsonl`, using title, categories, features, details, description, and store fields only.
- Public targets, target ASINs, hidden intents, and public answers were not read.
- The audit found 202 configured evidence terms: 36 have only the `accurate` flag, 165 have the `broad` flag, and 13 have the `ambiguous` flag. Flags overlap, so these counts must not be added together.
- `broad` is a catalog diagnostic, not a relevance label: coverage is at least 1% and no single leaf category contains more than 35% of matched products.
- The current retrieval module does not load `artifacts/lexicon.json`; Members 3 and 4 must explicitly consume these recommendations before they affect runtime behavior.

### F201 - Generic root categories create saturated category evidence

- Evidence source: reproducible catalog-field audit against the V2.1 retrieval term variants.
- Observed behavior: `shoe`, `shoes`, and `jewelry` each match the `categories` field for 50,000/50,000 products because every full path contains the root `Clothing, Shoes & Jewelry`.
- Failure class: `evidence_overbreadth`
- Generalizable rule: Exclude generic root path components from product-level matched evidence; retain informative descendants such as `Fashion Sneakers`, `Boots`, or `Necklaces`.
- Owning module: retrieval; Member 1 supplies the audit and Member 3 implements it.
- Expected metric impact: MRR / HitRate@10
- Regression risk: Removing all parent categories would also discard useful mid-level context; exclude only audited generic roots.
- Validation test: Root-only terms must not increment product evidence, while a matching informative leaf still does.
- Status: accepted

### F202 - Category precedence hides use-case meanings

- Evidence source: static retrieval classification plus catalog coverage audit.
- Observed behavior: 13 terms are ambiguous. `athletic`, `basketball`, `casual`, `club`, `cycling`, `everyday`, `lounge`, `rain`, `sleep`, `soccer`, and `sport` are configured as both category and use-case evidence; `set` and `sets` require category context. On default routes the current classifier assigns all 13 to `category`.
- Failure class: `evidence_attribute_collision`
- Generalizable rule: Use route and conversation slot context to choose the attribute; do not let membership in the category alias vocabulary always override an explicit use case.
- Owning module: retrieval / ranking; Member 1 supplies route-dependent metadata, Members 3 and 4 implement and weight it.
- Expected metric impact: MRR / HitRate@10
- Regression risk: Always forcing these terms to use-case would break genuine leaf-category queries.
- Validation test: Test the same term in a category request and a use-case sentence and require different matched attributes.
- Status: accepted

### F203 - `set` and `sets` are not self-contained product types

- Evidence source: catalog category paths.
- Observed behavior: all 610 `Sets` leaves can be resolved from an informative parent, including sleepwear, bikini, tankini, activewear, and thermal-underwear contexts; `Sets` alone is ambiguous.
- Failure class: `context_free_alias`
- Generalizable rule: Combine `Sets` with the nearest informative parent and never hard-filter from `set` or `sets` alone.
- Owning module: product knowledge / retrieval.
- Expected metric impact: candidate precision / HitRate@10
- Regression risk: Treating every occurrence of the ordinary word "set" as a product category can add unrelated candidates.
- Validation test: Verify parent-derived mappings and require clarification when no mapped parent exists.
- Status: accepted

### F204 - Size and style have no dedicated evidence classifier

- Evidence source: static V2.1 retrieval classification.
- Observed behavior: `size` and `style` do not have dedicated term sets in `_classify_matched_attributes`; an otherwise recognized match falls through to `feature` unless another earlier rule captures it.
- Failure class: `attribute_fallback_mislabel`
- Generalizable rule: Consume the lexicon's attribute metadata so size and style values retain their intended attribute instead of becoming generic features.
- Owning module: retrieval; Member 1 supplies vocabulary metadata and Member 3 consumes it.
- Expected metric impact: evidence accuracy / MRR
- Regression risk: Surface words such as "dress" can describe either a category or style; dedicated classification still needs route context.
- Validation test: Representative size/style aliases must be labeled correctly without changing explicit category matches.
- Status: accepted

### F205 - High coverage is not the same as high information value

- Evidence source: catalog-wide evidence and question statistics.
- Observed behavior: 165/202 configured evidence terms meet the reproducible `broad` heuristic. The question playbook also shows that attribute coverage and normalized information value can differ materially.
- Failure class: `evidence_overbreadth`
- Generalizable rule: Cap or downweight broad evidence and select questions by information value as well as coverage; do not promote a term merely because it appears frequently.
- Owning module: product knowledge / ranking / dialogue policy.
- Expected metric impact: MRR / MTTC
- Regression risk: The broad flag is not proof of irrelevance; globally blocking all broad terms would damage recall.
- Validation test: Compare capped/downweighted evidence on a frozen candidate set and require no holdout or Boundary regression.
- Status: diagnostic_only

## v2 ownership handoff

| Finding | Member 1 support | Primary implementation owner |
| --- | --- | --- |
| Missing clarification | `category_playbook.md` question order and no-preference fallback | Member 2 |
| Attribute/synonym recall gaps | `lexicon.json` catalog-derived vocabulary and aliases | Members 2 and 3 |
| Candidate recall misses | Attribute coverage and classification-quality warnings | Member 3 |
| RRF demotion / override underweighting | Strong-vs-generic evidence guidance | Member 4 |
| Metric and interaction verification | This taxonomy and reproducible validation criteria | Member 5 |

## Evidence boundary

The records above support general fixes only. They do not identify public target
products, prescribe target-specific vocabulary, or prove which individual
filter caused a retrieval miss. Filter attribution requires per-turn audit logs.
