# Category Question Playbook v3

This file is generated from `data/catalog.jsonl` by `artifacts/build_lexicon.py`.
It does not use public ground truth. The machine-readable source of truth is
`artifacts/lexicon.json`.

## Usage contract for member 2

1. Follow the question order for the category family, but skip attributes already in `asked`, `neutral`, or current slots.
2. Ask at most one natural question per turn, only when the live candidates contain at least two meaningful values for that attribute.
3. If the user says no preference, record that attribute as neutral and move to the next unasked attribute. Never repeat it.
4. Stop asking and return `ask_attribute = null` after the listed order is exhausted or when no question can narrow candidates.
5. A later explicit preference replaces the earlier value. Invalidated values must never re-enter current-state retrieval.
6. Use the full category path. Do not hard-filter on a noisy, broad, ambiguous, or brand-like leaf label alone.

## Catalog summary

- Products scanned: 50000
- Products with usable prices: 10410 (20.82%)
- Coverage is catalog-derived and is a safety signal, not the conversation order.

## Classification audit

- Products with no category path: 0
- The following leaf labels need fallback handling:

| Leaf label | Products | Issue | Parent paths | Auto-resolved | Ask category | Required handling |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| Westlake | 1136 | noisy_leaf | 1 | 582 | 554 | The leaf does not describe a stable product type; infer from the full path and title. |
| Shoes | 1299 | broad_leaf | 12 | N/A | N/A | The leaf is valid but too broad; identify footwear purpose before details. |
| Clothing | 423 | broad_leaf | 11 | 192 | 231 | The leaf is valid but too broad; identify garment type before details. |
| Casual | 1099 | ambiguous_leaf | 7 | 1099 | 0 | The same leaf appears under dresses, pants, skirts, and shorts; retain its parent path. |
| Sets | 610 | ambiguous_leaf | 18 | 610 | 0 | The same leaf appears under sleepwear, swimwear, activewear, and underwear; retain its parent path. |
| Women | 294 | broad_leaf | 15 | 120 | 174 | Audience is not a product type; infer the requested item before attributes. |
| Men | 185 | broad_leaf | 13 | 101 | 84 | Audience is not a product type; infer the requested item before attributes. |
| Fun World Costumes | 2 | brand_like_leaf | 1 | N/A | N/A | The leaf equals the store name; do not use it as a reliable product-type hard filter. |
| California Costumes | 2 | brand_like_leaf | 1 | N/A | N/A | The leaf equals the store name; do not use it as a reliable product-type hard filter. |

## Normalization rules for unreliable leaves

- `Casual`: use the parent (`Dresses`, `Pants`, `Skirts`, or `Shorts`) as `product_type`; keep `casual` as `style`.
- `Sets`: combine the nearest informative parent with `Sets`, such as `Sleepwear Sets`, `Bikini Sets`, or `Activewear Sets`.
- `Women` / `Men`: move the leaf to `audience`; it is never a product type.
- `Westlake` / `Clothing`: ignore the leaf as a product type. A unique title noun may be soft evidence; multiple or zero matches require a category question.
- Never hard-filter from an unreliable leaf or a title-derived category. Preserve the original catalog path for audit.

## Retrieval evidence audit

- Retrieval source: `starter/retrieval.py` (`sha256: 31b8c3fea97e1b4dffbdc341c9a1314a4ff28a77ada66389147fcf746f7b0a88`).
- Runtime currently references this lexicon: `false`. Member 3 must explicitly consume the metadata for it to affect retrieval.
- `frequency` counts field-product matches; `coverage` counts unique matched products. They are not relevance labels.
- Broad, ambiguous, and noisy terms are soft/downweighted/block candidates; no audit flag alone authorizes a hard filter.
- Quality flag counts: accurate=36, ambiguous=13, broad=165, noise=0

| Risk term | Configured role(s) | Default attribute | Products | Coverage | Matching fields | Flag(s) | Treatment |
| --- | --- | --- | ---: | ---: | --- | --- | --- |
| `jewelry` | category | category | 50000 | 100.00% | title:1589, categories:50000, features:2008, details:1492, description:1753, store:399 | broad | exclude_generic_root_path_from_evidence |
| `shoe` | category | category | 50000 | 100.00% | title:4451, categories:50000, features:2613, details:1327, description:3828, store:142 | broad | exclude_generic_root_path_from_evidence |
| `shoes` | category | category | 50000 | 100.00% | title:4451, categories:50000, features:2613, details:1327, description:3828, store:142 | broad | exclude_generic_root_path_from_evidence |
| `closure` | feature | feature | 19393 | 38.79% | title:104, features:18650, details:435, description:1293 | broad | cap_or_downweight |
| `wash` | feature | feature | 16134 | 32.27% | title:37, features:15734, details:130, description:1291, store:1 | broad | cap_or_downweight |
| `comfort` | feature_fallback | feature | 15539 | 31.08% | title:948, categories:6, features:11555, details:60, description:6472, store:51 | broad | cap_or_downweight |
| `comfortable` | feature_fallback | feature | 15531 | 31.06% | title:947, categories:6, features:11551, details:59, description:6468, store:50 | broad | cap_or_downweight |
| `soft` | feature_fallback | feature | 11225 | 22.45% | title:1101, features:8734, details:32, description:3678, store:13 | broad | cap_or_downweight |
| `polyester` | material | material | 10886 | 21.77% | title:51, features:10335, details:357, description:1624 | broad | cap_or_downweight |
| `tops` | category | category | 10741 | 21.48% | title:4584, categories:3975, features:5185, details:157, description:2858, store:53 | broad | cap_or_downweight |
| `quality` | feature_fallback | feature | 10525 | 21.05% | title:63, features:7139, details:8, description:4907, store:6 | broad | cap_or_downweight |
| `lightweight` | feature_fallback | feature | 10399 | 20.80% | title:1834, categories:95, features:7371, details:159, description:3228, store:3 | broad | cap_or_downweight |
| `casual` | category, use_case | category | 9972 | 19.94% | title:3871, categories:1631, features:5351, details:175, description:2541, store:7 | ambiguous, broad | route_dependent_soft_evidence |
| `hand` | feature | feature | 9933 | 19.87% | title:177, categories:1, features:8335, details:155, description:2435, store:13 | broad | cap_or_downweight |
| `cotton` | material | material | 9775 | 19.55% | title:1524, categories:28, features:9126, details:245, description:2322, store:9 | broad | cap_or_downweight |
| `fashion` | category | category | 9615 | 19.23% | title:1808, categories:2449, features:3592, details:201, description:3601, store:176 | broad | cap_or_downweight |
| `fabric` | material | material | 9264 | 18.53% | title:124, features:7556, details:244, description:2814, store:1 | broad | cap_or_downweight |
| `shirt` | category | category | 8590 | 17.18% | title:5832, categories:4771, features:3903, details:346, description:2283, store:270 | broad | cap_or_downweight |
| `shirts` | category | category | 8590 | 17.18% | title:5832, categories:4771, features:3903, details:346, description:2283, store:270 | broad | cap_or_downweight |
| `pull` | feature | feature | 8391 | 16.78% | title:148, features:7990, details:160, description:498, store:2 | broad | cap_or_downweight |
| `black` | color | color | 8229 | 16.46% | title:5000, features:2388, details:1102, description:1804, store:36 | broad | cap_or_downweight |
| `leather` | material | material | 7534 | 15.07% | title:2070, categories:95, features:6334, details:608, description:2573, store:55 | broad | cap_or_downweight |
| `accessories` | category | category | 7462 | 14.92% | title:333, categories:5531, features:1268, details:164, description:1605, store:60 | broad | cap_or_downweight |
| `accessory` | category | category | 7462 | 14.92% | title:332, categories:5531, features:1268, details:164, description:1605, store:60 | broad | cap_or_downweight |
| `rubber` | material | material | 6935 | 13.87% | title:234, features:6543, details:72, description:1199 | broad | cap_or_downweight |
| `short` | category | category | 6399 | 12.80% | title:3678, categories:849, features:3762, details:130, description:1601 | broad | cap_or_downweight |
| `shorts` | category | category | 6399 | 12.80% | title:3678, categories:849, features:3762, details:130, description:1601 | broad | cap_or_downweight |
| `dress` | category | category | 6268 | 12.54% | title:3762, categories:164, features:3385, details:60, description:2105, store:26 | broad | cap_or_downweight |
| `best` | feature_fallback | feature | 6204 | 12.41% | title:134, features:3250, details:1143, description:2418, store:13 | broad | cap_or_downweight |
| `out` | category | category | 6170 | 12.34% | title:264, categories:158, features:3734, details:13, description:2718, store:28 | broad | cap_or_downweight |

### Category alias actions

- Kept as soft aliases: 35.
- Require parent context: `set`, `sets`.
- Route-dependent because of attribute collisions: `athletic`, `athletic shoes`, `basketball`, `casual button down shirts`, `casual button-down shirts`, `club and night out`, `club night out`, `cycling jerseys`, `everyday bra`, `everyday bras`, `rain`, `rain boots`, `sleep and lounge`, `sleep bottoms`, `sleep lounge`, `sleep lounge sets`, `sleep sets`, `soccer`, `soccer cleats`, `sport sandals`, `sport sandals and slides`, `sport sandals slides`.
- Not observed verbatim in catalog title/category fields: 0; keep only as soft query rewrites until validated.

## Question order table

Each cell shows `coverage` and `info`. Coverage is how many products expose the attribute; info is the weighted normalized-entropy score (0-1) estimating how much the answer can split candidates. High coverage does not automatically mean high information value. Size coverage is conservative because numeric sizes are parsed separately by member 2.

| Category | Products | Ask 1 | Ask 2 | Ask 3 | Ask 4 |
| --- | ---: | --- | --- | --- | --- |
| T-Shirts | 2807 | `use_case`: What will you mainly use it for? (coverage 45.4%; info 0.365) | `size`: What size or fit do you need? (coverage 6.5%; info 0.043) | `style`: What style or fit do you prefer? (coverage 70.2%; info 0.543) | `material`: Do you have a material preference? (coverage 85.1%; info 0.373) |
| Shoes | 1299 | `use_case`: What will you mainly use it for? (coverage 41.9%; info 0.340) | `size`: What size or fit do you need? (coverage 1.3%; info 0.008) | `feature`: Which feature matters most to you? (coverage 32.6%; info 0.252) | `style`: What style or fit do you prefer? (coverage 25.1%; info 0.182) |
| Westlake | 1136 | `category`: What kind of item are you looking for? (coverage 0.0%; info 0.000) | `use_case`: What will you mainly use it for? (coverage 31.7%; info 0.268) | `size`: What size or fit do you need? (coverage 9.5%; info 0.049) | `style`: What style or fit do you prefer? (coverage 64.2%; info 0.509) |
| Casual | 1099 | `use_case`: What will you mainly use it for? (coverage 58.1%; info 0.447) | `size`: What size or fit do you need? (coverage 16.0%; info 0.118) | `style`: What style or fit do you prefer? (coverage 87.4%; info 0.657) | `material`: Do you have a material preference? (coverage 84.9%; info 0.565) |
| Wrist Watches | 1034 | `use_case`: What will you mainly use it for? (coverage 47.3%; info 0.357) | `feature`: Which feature matters most to you? (coverage 67.4%; info 0.374) | `style`: What style or fit do you prefer? (coverage 44.3%; info 0.360) | `material`: Do you have a material preference? (coverage 87.2%; info 0.538) |
| Fashion Sneakers | 1017 | `use_case`: What will you mainly use it for? (coverage 34.1%; info 0.288) | `size`: What size or fit do you need? (coverage 0.9%; info 0.008) | `feature`: Which feature matters most to you? (coverage 44.2%; info 0.342) | `style`: What style or fit do you prefer? (coverage 41.7%; info 0.273) |
| Flats | 927 | `use_case`: What will you mainly use it for? (coverage 37.4%; info 0.313) | `size`: What size or fit do you need? (coverage 3.7%; info 0.025) | `feature`: Which feature matters most to you? (coverage 46.4%; info 0.357) | `style`: What style or fit do you prefer? (coverage 41.9%; info 0.298) |
| Blouses & Button-Down Shirts | 691 | `use_case`: What will you mainly use it for? (coverage 63.8%; info 0.479) | `size`: What size or fit do you need? (coverage 17.4%; info 0.115) | `style`: What style or fit do you prefer? (coverage 88.1%; info 0.710) | `material`: Do you have a material preference? (coverage 83.7%; info 0.601) |
| Loafers & Slip-Ons | 665 | `use_case`: What will you mainly use it for? (coverage 42.4%; info 0.331) | `size`: What size or fit do you need? (coverage 2.1%; info 0.019) | `feature`: Which feature matters most to you? (coverage 53.7%; info 0.408) | `style`: What style or fit do you prefer? (coverage 54.6%; info 0.370) |
| Dresses | 656 | `use_case`: What will you mainly use it for? (coverage 79.1%; info 0.605) | `size`: What size or fit do you need? (coverage 16.8%; info 0.122) | `style`: What style or fit do you prefer? (coverage 96.7%; info 0.732) | `material`: Do you have a material preference? (coverage 84.2%; info 0.577) |
| Pumps | 630 | `use_case`: What will you mainly use it for? (coverage 37.5%; info 0.273) | `size`: What size or fit do you need? (coverage 2.1%; info 0.019) | `feature`: Which feature matters most to you? (coverage 39.5%; info 0.277) | `style`: What style or fit do you prefer? (coverage 54.0%; info 0.340) |
| Sets | 610 | `use_case`: What will you mainly use it for? (coverage 60.8%; info 0.517) | `size`: What size or fit do you need? (coverage 10.8%; info 0.076) | `style`: What style or fit do you prefer? (coverage 63.9%; info 0.526) | `material`: Do you have a material preference? (coverage 74.4%; info 0.501) |
| Sandals | 586 | `use_case`: What will you mainly use it for? (coverage 47.6%; info 0.366) | `size`: What size or fit do you need? (coverage 1.2%; info 0.011) | `feature`: Which feature matters most to you? (coverage 55.8%; info 0.459) | `style`: What style or fit do you prefer? (coverage 40.4%; info 0.270) |
| Platforms & Wedges | 545 | `use_case`: What will you mainly use it for? (coverage 34.5%; info 0.282) | `size`: What size or fit do you need? (coverage 1.3%; info 0.009) | `feature`: Which feature matters most to you? (coverage 43.9%; info 0.341) | `style`: What style or fit do you prefer? (coverage 33.6%; info 0.222) |
| Sunglasses | 540 | `use_case`: What will you mainly use it for? (coverage 35.4%; info 0.290) | `feature`: Which feature matters most to you? (coverage 73.0%; info 0.463) | `style`: What style or fit do you prefer? (coverage 37.8%; info 0.288) | `color`: What color would you prefer? (coverage 60.0%; info 0.450) |
| Slippers | 538 | `use_case`: What will you mainly use it for? (coverage 69.9%; info 0.503) | `size`: What size or fit do you need? (coverage 5.6%; info 0.036) | `feature`: Which feature matters most to you? (coverage 66.0%; info 0.537) | `style`: What style or fit do you prefer? (coverage 19.0%; info 0.120) |
| Pendant Necklaces | 531 | `use_case`: What will you mainly use it for? (coverage 73.6%; info 0.420) | `style`: What style or fit do you prefer? (coverage 20.7%; info 0.167) | `material`: Do you have a material preference? (coverage 82.3%; info 0.501) | `feature`: Which feature matters most to you? (coverage 28.6%; info 0.217) |
| Road Running | 522 | `use_case`: What will you mainly use it for? (coverage 86.4%; info 0.477) | `size`: What size or fit do you need? (coverage 0.8%; info 0.008) | `feature`: Which feature matters most to you? (coverage 48.9%; info 0.373) | `style`: What style or fit do you prefer? (coverage 26.8%; info 0.171) |
| Tunics | 521 | `use_case`: What will you mainly use it for? (coverage 61.6%; info 0.484) | `size`: What size or fit do you need? (coverage 24.8%; info 0.098) | `style`: What style or fit do you prefer? (coverage 97.7%; info 0.752) | `material`: Do you have a material preference? (coverage 79.1%; info 0.487) |
| Drop & Dangle | 503 | `use_case`: What will you mainly use it for? (coverage 73.4%; info 0.470) | `style`: What style or fit do you prefer? (coverage 34.4%; info 0.302) | `material`: Do you have a material preference? (coverage 75.5%; info 0.473) | `feature`: Which feature matters most to you? (coverage 33.8%; info 0.271) |
| Tanks & Camis | 499 | `use_case`: What will you mainly use it for? (coverage 60.9%; info 0.495) | `size`: What size or fit do you need? (coverage 11.8%; info 0.073) | `style`: What style or fit do you prefer? (coverage 77.6%; info 0.599) | `material`: Do you have a material preference? (coverage 81.8%; info 0.530) |
| Fashion Hoodies & Sweatshirts | 489 | `use_case`: What will you mainly use it for? (coverage 54.4%; info 0.433) | `size`: What size or fit do you need? (coverage 11.7%; info 0.071) | `style`: What style or fit do you prefer? (coverage 91.0%; info 0.699) | `material`: Do you have a material preference? (coverage 75.0%; info 0.452) |
| Costumes | 470 | `use_case`: What will you mainly use it for? (coverage 90.6%; info 0.519) | `size`: What size or fit do you need? (coverage 12.8%; info 0.121) | `style`: What style or fit do you prefer? (coverage 61.1%; info 0.362) | `budget`: What budget would you like to stay within? (coverage 39.4%; info 0.262) |
| Jeans | 467 | `use_case`: What will you mainly use it for? (coverage 23.3%; info 0.186) | `size`: What size or fit do you need? (coverage 13.7%; info 0.108) | `style`: What style or fit do you prefer? (coverage 66.2%; info 0.539) | `material`: Do you have a material preference? (coverage 89.3%; info 0.516) |
| Clothing | 423 | `category`: What kind of item are you looking for? (coverage 0.0%; info 0.000) | `use_case`: What will you mainly use it for? (coverage 42.8%; info 0.382) | `size`: What size or fit do you need? (coverage 15.4%; info 0.107) | `style`: What style or fit do you prefer? (coverage 62.9%; info 0.545) |
| Baseball Caps | 385 | `use_case`: What will you mainly use it for? (coverage 41.3%; info 0.355) | `size`: What size or fit do you need? (coverage 33.0%; info 0.022) | `style`: What style or fit do you prefer? (coverage 34.5%; info 0.229) | `material`: Do you have a material preference? (coverage 83.6%; info 0.509) |
| Leggings | 383 | `use_case`: What will you mainly use it for? (coverage 66.1%; info 0.486) | `size`: What size or fit do you need? (coverage 17.0%; info 0.136) | `style`: What style or fit do you prefer? (coverage 56.9%; info 0.397) | `material`: Do you have a material preference? (coverage 81.2%; info 0.511) |
| Ankle & Bootie | 382 | `use_case`: What will you mainly use it for? (coverage 32.5%; info 0.275) | `size`: What size or fit do you need? (coverage 1.1%; info 0.010) | `feature`: Which feature matters most to you? (coverage 38.7%; info 0.324) | `style`: What style or fit do you prefer? (coverage 36.9%; info 0.283) |
| Pullovers | 379 | `use_case`: What will you mainly use it for? (coverage 53.8%; info 0.407) | `size`: What size or fit do you need? (coverage 11.1%; info 0.084) | `style`: What style or fit do you prefer? (coverage 86.8%; info 0.677) | `material`: Do you have a material preference? (coverage 76.5%; info 0.571) |
| Socks | 376 | `size`: What size or fit do you need? (coverage 20.7%; info 0.026) | `material`: Do you have a material preference? (coverage 90.4%; info 0.604) | `feature`: Which feature matters most to you? (coverage 59.6%; info 0.476) | `use_case`: What will you mainly use it for? (coverage 50.8%; info 0.446) |
| Rings | 373 | `use_case`: What will you mainly use it for? (coverage 59.2%; info 0.374) | `style`: What style or fit do you prefer? (coverage 24.1%; info 0.181) | `material`: Do you have a material preference? (coverage 89.5%; info 0.617) | `feature`: Which feature matters most to you? (coverage 39.4%; info 0.292) |
| Wallets | 370 | `use_case`: What will you mainly use it for? (coverage 46.2%; info 0.304) | `size`: What size or fit do you need? (coverage 5.1%; info 0.015) | `feature`: Which feature matters most to you? (coverage 43.5%; info 0.277) | `style`: What style or fit do you prefer? (coverage 30.8%; info 0.253) |
| Stud | 358 | `use_case`: What will you mainly use it for? (coverage 69.0%; info 0.451) | `style`: What style or fit do you prefer? (coverage 29.9%; info 0.252) | `material`: Do you have a material preference? (coverage 87.7%; info 0.523) | `feature`: Which feature matters most to you? (coverage 37.1%; info 0.285) |
| Walking | 342 | `use_case`: What will you mainly use it for? (coverage 86.0%; info 0.663) | `size`: What size or fit do you need? (coverage 2.9%; info 0.027) | `feature`: Which feature matters most to you? (coverage 76.6%; info 0.583) | `style`: What style or fit do you prefer? (coverage 57.6%; info 0.348) |
| Sneakers | 341 | `use_case`: What will you mainly use it for? (coverage 39.3%; info 0.337) | `size`: What size or fit do you need? (coverage 0.0%; info 0.000) | `feature`: Which feature matters most to you? (coverage 55.4%; info 0.425) | `style`: What style or fit do you prefer? (coverage 43.4%; info 0.330) |
| Necklaces | 329 | `use_case`: What will you mainly use it for? (coverage 62.3%; info 0.412) | `style`: What style or fit do you prefer? (coverage 22.2%; info 0.182) | `material`: Do you have a material preference? (coverage 82.7%; info 0.541) | `feature`: Which feature matters most to you? (coverage 34.9%; info 0.276) |
| Heeled Sandals | 325 | `use_case`: What will you mainly use it for? (coverage 38.5%; info 0.330) | `size`: What size or fit do you need? (coverage 2.1%; info 0.016) | `feature`: Which feature matters most to you? (coverage 43.7%; info 0.347) | `style`: What style or fit do you prefer? (coverage 55.4%; info 0.348) |
| Cardigans | 315 | `use_case`: What will you mainly use it for? (coverage 50.5%; info 0.409) | `size`: What size or fit do you need? (coverage 17.5%; info 0.099) | `style`: What style or fit do you prefer? (coverage 82.5%; info 0.662) | `material`: Do you have a material preference? (coverage 75.2%; info 0.603) |
| Pants | 297 | `use_case`: What will you mainly use it for? (coverage 64.6%; info 0.571) | `size`: What size or fit do you need? (coverage 12.8%; info 0.103) | `style`: What style or fit do you prefer? (coverage 56.9%; info 0.468) | `material`: Do you have a material preference? (coverage 83.5%; info 0.553) |
| Active Shorts | 294 | `use_case`: What will you mainly use it for? (coverage 77.5%; info 0.638) | `size`: What size or fit do you need? (coverage 6.8%; info 0.062) | `style`: What style or fit do you prefer? (coverage 61.9%; info 0.432) | `material`: Do you have a material preference? (coverage 80.3%; info 0.482) |
| Women | 294 | `category`: What kind of item are you looking for? (coverage 0.0%; info 0.000) | `use_case`: What will you mainly use it for? (coverage 54.4%; info 0.478) | `size`: What size or fit do you need? (coverage 19.7%; info 0.116) | `style`: What style or fit do you prefer? (coverage 52.4%; info 0.460) |
| Casual Button-Down Shirts | 288 | `use_case`: What will you mainly use it for? (coverage 48.3%; info 0.402) | `size`: What size or fit do you need? (coverage 9.0%; info 0.086) | `style`: What style or fit do you prefer? (coverage 87.2%; info 0.676) | `material`: Do you have a material preference? (coverage 92.4%; info 0.554) |
| Mules & Clogs | 283 | `use_case`: What will you mainly use it for? (coverage 42.0%; info 0.350) | `size`: What size or fit do you need? (coverage 3.2%; info 0.027) | `feature`: Which feature matters most to you? (coverage 62.5%; info 0.504) | `style`: What style or fit do you prefer? (coverage 35.7%; info 0.252) |
| Oxfords | 283 | `use_case`: What will you mainly use it for? (coverage 45.6%; info 0.356) | `size`: What size or fit do you need? (coverage 0.4%; info 0.000) | `feature`: Which feature matters most to you? (coverage 45.9%; info 0.370) | `style`: What style or fit do you prefer? (coverage 62.9%; info 0.438) |
| Athletic Socks | 276 | `size`: What size or fit do you need? (coverage 6.5%; info 0.025) | `material`: Do you have a material preference? (coverage 88.4%; info 0.606) | `feature`: Which feature matters most to you? (coverage 78.3%; info 0.640) | `use_case`: What will you mainly use it for? (coverage 67.8%; info 0.613) |
| Crossbody Bags | 271 | `use_case`: What will you mainly use it for? (coverage 39.5%; info 0.319) | `size`: What size or fit do you need? (coverage 10.3%; info 0.071) | `feature`: Which feature matters most to you? (coverage 72.3%; info 0.501) | `style`: What style or fit do you prefer? (coverage 22.5%; info 0.167) |
| Boots | 268 | `use_case`: What will you mainly use it for? (coverage 43.7%; info 0.344) | `size`: What size or fit do you need? (coverage 0.4%; info 0.000) | `feature`: Which feature matters most to you? (coverage 47.0%; info 0.383) | `style`: What style or fit do you prefer? (coverage 29.1%; info 0.235) |
| Active Shirts & Tees | 263 | `use_case`: What will you mainly use it for? (coverage 55.5%; info 0.473) | `size`: What size or fit do you need? (coverage 6.1%; info 0.041) | `style`: What style or fit do you prefer? (coverage 71.9%; info 0.599) | `material`: Do you have a material preference? (coverage 75.3%; info 0.478) |
| Belts | 260 | `use_case`: What will you mainly use it for? (coverage 53.8%; info 0.416) | `size`: What size or fit do you need? (coverage 14.2%; info 0.109) | `style`: What style or fit do you prefer? (coverage 62.3%; info 0.449) | `material`: Do you have a material preference? (coverage 88.5%; info 0.630) |
| One-Pieces | 259 | `use_case`: What will you mainly use it for? (coverage 51.7%; info 0.337) | `size`: What size or fit do you need? (coverage 17.4%; info 0.131) | `style`: What style or fit do you prefer? (coverage 46.7%; info 0.388) | `material`: Do you have a material preference? (coverage 69.1%; info 0.451) |
| Shoulder Bags | 257 | `use_case`: What will you mainly use it for? (coverage 37.4%; info 0.302) | `size`: What size or fit do you need? (coverage 3.5%; info 0.000) | `feature`: Which feature matters most to you? (coverage 64.6%; info 0.481) | `style`: What style or fit do you prefer? (coverage 27.2%; info 0.211) |
| Hoodies | 252 | `use_case`: What will you mainly use it for? (coverage 49.2%; info 0.416) | `size`: What size or fit do you need? (coverage 1.6%; info 0.013) | `style`: What style or fit do you prefer? (coverage 86.1%; info 0.528) | `material`: Do you have a material preference? (coverage 75.8%; info 0.420) |
| Statement | 249 | `use_case`: What will you mainly use it for? (coverage 67.1%; info 0.413) | `size`: What size or fit do you need? (coverage 1.6%; info 0.013) | `style`: What style or fit do you prefer? (coverage 24.1%; info 0.210) | `material`: Do you have a material preference? (coverage 91.2%; info 0.536) |
| Flip-Flops | 245 | `use_case`: What will you mainly use it for? (coverage 49.8%; info 0.399) | `size`: What size or fit do you need? (coverage 1.6%; info 0.016) | `feature`: Which feature matters most to you? (coverage 46.5%; info 0.371) | `style`: What style or fit do you prefer? (coverage 36.7%; info 0.255) |
| Running | 238 | `use_case`: What will you mainly use it for? (coverage 85.7%; info 0.669) | `size`: What size or fit do you need? (coverage 0.4%; info 0.000) | `feature`: Which feature matters most to you? (coverage 52.1%; info 0.410) | `style`: What style or fit do you prefer? (coverage 39.1%; info 0.222) |
| Snow & Cold Weather | 232 | `use_case`: What will you mainly use it for? (coverage 77.6%; info 0.542) | `size`: What size or fit do you need? (coverage 4.3%; info 0.034) | `style`: What style or fit do you prefer? (coverage 24.6%; info 0.177) | `material`: Do you have a material preference? (coverage 85.8%; info 0.627) |
| Everyday Bras | 230 | `size`: What size or fit do you need? (coverage 16.1%; info 0.097) | `material`: Do you have a material preference? (coverage 85.7%; info 0.577) | `feature`: Which feature matters most to you? (coverage 76.1%; info 0.561) | `use_case`: What will you mainly use it for? (coverage 36.1%; info 0.272) |
| Polos | 219 | `use_case`: What will you mainly use it for? (coverage 46.1%; info 0.393) | `size`: What size or fit do you need? (coverage 8.7%; info 0.074) | `style`: What style or fit do you prefer? (coverage 73.5%; info 0.591) | `material`: Do you have a material preference? (coverage 90.0%; info 0.510) |
| Pant Sets | 203 | `use_case`: What will you mainly use it for? (coverage 54.7%; info 0.431) | `size`: What size or fit do you need? (coverage 1.5%; info 0.000) | `style`: What style or fit do you prefer? (coverage 71.4%; info 0.533) | `material`: Do you have a material preference? (coverage 90.6%; info 0.498) |
| Skirts | 202 | `use_case`: What will you mainly use it for? (coverage 62.4%; info 0.517) | `size`: What size or fit do you need? (coverage 20.3%; info 0.170) | `style`: What style or fit do you prefer? (coverage 73.3%; info 0.556) | `material`: Do you have a material preference? (coverage 86.1%; info 0.647) |

## No-preference flow

For every row: record the current attribute as `neutral`, move to the next column, and never ask the neutral attribute again. If all four are answered, neutral, already asked, or unable to narrow live candidates, use `ask_attribute = null`.

## Team handoff

- Member 2: consume `category_playbook[*].question_order`; skip asked/neutral/current slots and use the normalization `next_action` as the fallback reason.
- Member 3: consume `evidence_audit.term_stats`, `safe_soft_aliases`, and unreliable-leaf policies. Do not label size/style terms as feature by default and do not hard-filter from aliases alone.
- Member 4: treat `accurate` explicit matches as candidates for stronger evidence; cap/downweight `broad`, keep `ambiguous` route-dependent, and block `noise` until catalog evidence exists.
- Member 5: rebuild with `python artifacts/build_lexicon.py`, run `python -m unittest discover -s tests -p test_lexicon.py -v`, and compare coverage/quality counts before accepting a change.

## Evidence boundary

All counts, vocabulary, aliases, category families, and classification findings come from participant-visible fields in `data/catalog.jsonl`. Public ground truth, target ASINs, and session-specific answer rules were not used.
