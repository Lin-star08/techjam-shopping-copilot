# Category Question Playbook v1.2

This file is generated from `data/catalog.jsonl` by `knowledge/build_lexicon.py`.
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

| Leaf label | Products | Issue | Parent paths | Required handling |
| --- | ---: | --- | ---: | --- |
| Westlake | 1136 | noisy_leaf | 1 | The leaf does not describe a stable product type; infer from the full path and title. |
| Shoes | 1299 | broad_leaf | 12 | The leaf is valid but too broad; identify footwear purpose before details. |
| Clothing | 423 | broad_leaf | 11 | The leaf is valid but too broad; identify garment type before details. |
| Casual | 1099 | ambiguous_leaf | 7 | The same leaf appears under dresses, pants, skirts, and shorts; retain its parent path. |
| Sets | 610 | ambiguous_leaf | 18 | The same leaf appears under sleepwear, swimwear, activewear, and underwear; retain its parent path. |
| Women | 294 | broad_leaf | 15 | Audience is not a product type; infer the requested item before attributes. |
| Men | 185 | broad_leaf | 13 | Audience is not a product type; infer the requested item before attributes. |
| Fun World Costumes | 2 | brand_like_leaf | 1 | The leaf equals the store name; do not use it as a reliable product-type hard filter. |
| California Costumes | 2 | brand_like_leaf | 1 | The leaf equals the store name; do not use it as a reliable product-type hard filter. |

## Question order table

The percentages show how often the vocabulary found usable catalog evidence. Size coverage is conservative because numeric sizes are parsed separately by member 2.

| Category | Products | Ask 1 | Ask 2 | Ask 3 | Ask 4 |
| --- | ---: | --- | --- | --- | --- |
| T-Shirts | 2807 | `use_case`: What will you mainly use it for? (45.4%) | `size`: What size or fit do you need? (6.5%) | `style`: What style or fit do you prefer? (70.2%) | `material`: Do you have a material preference? (85.1%) |
| Shoes | 1299 | `use_case`: What will you mainly use it for? (41.9%) | `size`: What size or fit do you need? (1.3%) | `feature`: Which feature matters most to you? (32.6%) | `style`: What style or fit do you prefer? (25.1%) |
| Westlake | 1136 | `category`: What kind of item are you looking for? (0.0%) | `use_case`: What will you mainly use it for? (31.7%) | `size`: What size or fit do you need? (9.5%) | `style`: What style or fit do you prefer? (64.2%) |
| Casual | 1099 | `category`: What kind of item are you looking for? (0.0%) | `use_case`: What will you mainly use it for? (58.1%) | `size`: What size or fit do you need? (16.0%) | `style`: What style or fit do you prefer? (87.4%) |
| Wrist Watches | 1034 | `use_case`: What will you mainly use it for? (47.3%) | `feature`: Which feature matters most to you? (67.4%) | `style`: What style or fit do you prefer? (44.3%) | `material`: Do you have a material preference? (87.2%) |
| Fashion Sneakers | 1017 | `use_case`: What will you mainly use it for? (34.1%) | `size`: What size or fit do you need? (0.9%) | `feature`: Which feature matters most to you? (44.2%) | `style`: What style or fit do you prefer? (41.7%) |
| Flats | 927 | `use_case`: What will you mainly use it for? (37.4%) | `size`: What size or fit do you need? (3.7%) | `feature`: Which feature matters most to you? (46.4%) | `style`: What style or fit do you prefer? (41.9%) |
| Blouses & Button-Down Shirts | 691 | `use_case`: What will you mainly use it for? (63.8%) | `size`: What size or fit do you need? (17.4%) | `style`: What style or fit do you prefer? (88.1%) | `material`: Do you have a material preference? (83.7%) |
| Loafers & Slip-Ons | 665 | `use_case`: What will you mainly use it for? (42.4%) | `size`: What size or fit do you need? (2.1%) | `feature`: Which feature matters most to you? (53.7%) | `style`: What style or fit do you prefer? (54.6%) |
| Dresses | 656 | `use_case`: What will you mainly use it for? (79.1%) | `size`: What size or fit do you need? (16.8%) | `style`: What style or fit do you prefer? (96.7%) | `material`: Do you have a material preference? (84.2%) |
| Pumps | 630 | `use_case`: What will you mainly use it for? (37.5%) | `size`: What size or fit do you need? (2.1%) | `feature`: Which feature matters most to you? (39.5%) | `style`: What style or fit do you prefer? (54.0%) |
| Sets | 610 | `category`: What kind of item are you looking for? (0.0%) | `use_case`: What will you mainly use it for? (60.8%) | `size`: What size or fit do you need? (10.8%) | `style`: What style or fit do you prefer? (63.9%) |
| Sandals | 586 | `use_case`: What will you mainly use it for? (47.6%) | `size`: What size or fit do you need? (1.2%) | `feature`: Which feature matters most to you? (55.8%) | `style`: What style or fit do you prefer? (40.4%) |
| Platforms & Wedges | 545 | `use_case`: What will you mainly use it for? (34.5%) | `size`: What size or fit do you need? (1.3%) | `feature`: Which feature matters most to you? (43.9%) | `style`: What style or fit do you prefer? (33.6%) |
| Sunglasses | 540 | `use_case`: What will you mainly use it for? (35.4%) | `feature`: Which feature matters most to you? (73.0%) | `style`: What style or fit do you prefer? (37.8%) | `color`: What color would you prefer? (60.0%) |
| Slippers | 538 | `use_case`: What will you mainly use it for? (69.9%) | `size`: What size or fit do you need? (5.6%) | `feature`: Which feature matters most to you? (66.0%) | `style`: What style or fit do you prefer? (19.0%) |
| Pendant Necklaces | 531 | `use_case`: What will you mainly use it for? (73.6%) | `style`: What style or fit do you prefer? (20.7%) | `material`: Do you have a material preference? (82.3%) | `feature`: Which feature matters most to you? (28.6%) |
| Road Running | 522 | `use_case`: What will you mainly use it for? (86.4%) | `size`: What size or fit do you need? (0.8%) | `feature`: Which feature matters most to you? (48.9%) | `style`: What style or fit do you prefer? (26.8%) |
| Tunics | 521 | `use_case`: What will you mainly use it for? (61.6%) | `size`: What size or fit do you need? (24.8%) | `style`: What style or fit do you prefer? (97.7%) | `material`: Do you have a material preference? (79.1%) |
| Drop & Dangle | 503 | `use_case`: What will you mainly use it for? (73.4%) | `style`: What style or fit do you prefer? (34.4%) | `material`: Do you have a material preference? (75.5%) | `feature`: Which feature matters most to you? (33.8%) |
| Tanks & Camis | 499 | `use_case`: What will you mainly use it for? (60.9%) | `size`: What size or fit do you need? (11.8%) | `style`: What style or fit do you prefer? (77.6%) | `material`: Do you have a material preference? (81.8%) |
| Fashion Hoodies & Sweatshirts | 489 | `use_case`: What will you mainly use it for? (54.4%) | `size`: What size or fit do you need? (11.7%) | `style`: What style or fit do you prefer? (91.0%) | `material`: Do you have a material preference? (75.0%) |
| Costumes | 470 | `use_case`: What will you mainly use it for? (90.6%) | `size`: What size or fit do you need? (12.8%) | `style`: What style or fit do you prefer? (61.1%) | `budget`: What budget would you like to stay within? (39.4%) |
| Jeans | 467 | `use_case`: What will you mainly use it for? (23.3%) | `size`: What size or fit do you need? (13.7%) | `style`: What style or fit do you prefer? (66.2%) | `material`: Do you have a material preference? (89.3%) |
| Clothing | 423 | `category`: What kind of item are you looking for? (0.0%) | `use_case`: What will you mainly use it for? (42.8%) | `size`: What size or fit do you need? (15.4%) | `style`: What style or fit do you prefer? (62.9%) |
| Baseball Caps | 385 | `use_case`: What will you mainly use it for? (41.3%) | `size`: What size or fit do you need? (33.0%) | `style`: What style or fit do you prefer? (34.5%) | `material`: Do you have a material preference? (83.6%) |
| Leggings | 383 | `use_case`: What will you mainly use it for? (66.1%) | `size`: What size or fit do you need? (17.0%) | `style`: What style or fit do you prefer? (56.9%) | `material`: Do you have a material preference? (81.2%) |
| Ankle & Bootie | 382 | `use_case`: What will you mainly use it for? (32.5%) | `size`: What size or fit do you need? (1.1%) | `feature`: Which feature matters most to you? (38.7%) | `style`: What style or fit do you prefer? (36.9%) |
| Pullovers | 379 | `use_case`: What will you mainly use it for? (53.8%) | `size`: What size or fit do you need? (11.1%) | `style`: What style or fit do you prefer? (86.8%) | `material`: Do you have a material preference? (76.5%) |
| Socks | 376 | `size`: What size or fit do you need? (20.7%) | `material`: Do you have a material preference? (90.4%) | `feature`: Which feature matters most to you? (59.6%) | `use_case`: What will you mainly use it for? (50.8%) |
| Rings | 373 | `use_case`: What will you mainly use it for? (59.2%) | `style`: What style or fit do you prefer? (24.1%) | `material`: Do you have a material preference? (89.5%) | `feature`: Which feature matters most to you? (39.4%) |
| Wallets | 370 | `use_case`: What will you mainly use it for? (46.2%) | `size`: What size or fit do you need? (5.1%) | `feature`: Which feature matters most to you? (43.5%) | `style`: What style or fit do you prefer? (30.8%) |
| Stud | 358 | `use_case`: What will you mainly use it for? (69.0%) | `style`: What style or fit do you prefer? (29.9%) | `material`: Do you have a material preference? (87.7%) | `feature`: Which feature matters most to you? (37.1%) |
| Walking | 342 | `use_case`: What will you mainly use it for? (86.0%) | `size`: What size or fit do you need? (2.9%) | `feature`: Which feature matters most to you? (76.6%) | `style`: What style or fit do you prefer? (57.6%) |
| Sneakers | 341 | `use_case`: What will you mainly use it for? (39.3%) | `size`: What size or fit do you need? (0.0%) | `feature`: Which feature matters most to you? (55.4%) | `style`: What style or fit do you prefer? (43.4%) |
| Necklaces | 329 | `use_case`: What will you mainly use it for? (62.3%) | `style`: What style or fit do you prefer? (22.2%) | `material`: Do you have a material preference? (82.7%) | `feature`: Which feature matters most to you? (34.9%) |
| Heeled Sandals | 325 | `use_case`: What will you mainly use it for? (38.5%) | `size`: What size or fit do you need? (2.1%) | `feature`: Which feature matters most to you? (43.7%) | `style`: What style or fit do you prefer? (55.4%) |
| Cardigans | 315 | `use_case`: What will you mainly use it for? (50.5%) | `size`: What size or fit do you need? (17.5%) | `style`: What style or fit do you prefer? (82.5%) | `material`: Do you have a material preference? (75.2%) |
| Pants | 297 | `use_case`: What will you mainly use it for? (64.6%) | `size`: What size or fit do you need? (12.8%) | `style`: What style or fit do you prefer? (56.9%) | `material`: Do you have a material preference? (83.5%) |
| Active Shorts | 294 | `use_case`: What will you mainly use it for? (77.5%) | `size`: What size or fit do you need? (6.8%) | `style`: What style or fit do you prefer? (61.9%) | `material`: Do you have a material preference? (80.3%) |
| Women | 294 | `category`: What kind of item are you looking for? (0.0%) | `use_case`: What will you mainly use it for? (54.4%) | `size`: What size or fit do you need? (19.7%) | `style`: What style or fit do you prefer? (52.4%) |
| Casual Button-Down Shirts | 288 | `use_case`: What will you mainly use it for? (48.3%) | `size`: What size or fit do you need? (9.0%) | `style`: What style or fit do you prefer? (87.2%) | `material`: Do you have a material preference? (92.4%) |
| Mules & Clogs | 283 | `use_case`: What will you mainly use it for? (42.0%) | `size`: What size or fit do you need? (3.2%) | `feature`: Which feature matters most to you? (62.5%) | `style`: What style or fit do you prefer? (35.7%) |
| Oxfords | 283 | `use_case`: What will you mainly use it for? (45.6%) | `size`: What size or fit do you need? (0.4%) | `feature`: Which feature matters most to you? (45.9%) | `style`: What style or fit do you prefer? (62.9%) |
| Athletic Socks | 276 | `size`: What size or fit do you need? (6.5%) | `material`: Do you have a material preference? (88.4%) | `feature`: Which feature matters most to you? (78.3%) | `use_case`: What will you mainly use it for? (67.8%) |
| Crossbody Bags | 271 | `use_case`: What will you mainly use it for? (39.5%) | `size`: What size or fit do you need? (10.3%) | `feature`: Which feature matters most to you? (72.3%) | `style`: What style or fit do you prefer? (22.5%) |
| Boots | 268 | `use_case`: What will you mainly use it for? (43.7%) | `size`: What size or fit do you need? (0.4%) | `feature`: Which feature matters most to you? (47.0%) | `style`: What style or fit do you prefer? (29.1%) |
| Active Shirts & Tees | 263 | `use_case`: What will you mainly use it for? (55.5%) | `size`: What size or fit do you need? (6.1%) | `style`: What style or fit do you prefer? (71.9%) | `material`: Do you have a material preference? (75.3%) |
| Belts | 260 | `use_case`: What will you mainly use it for? (53.8%) | `size`: What size or fit do you need? (14.2%) | `style`: What style or fit do you prefer? (62.3%) | `material`: Do you have a material preference? (88.5%) |
| One-Pieces | 259 | `use_case`: What will you mainly use it for? (51.7%) | `size`: What size or fit do you need? (17.4%) | `style`: What style or fit do you prefer? (46.7%) | `material`: Do you have a material preference? (69.1%) |
| Shoulder Bags | 257 | `use_case`: What will you mainly use it for? (37.4%) | `size`: What size or fit do you need? (3.5%) | `feature`: Which feature matters most to you? (64.6%) | `style`: What style or fit do you prefer? (27.2%) |
| Hoodies | 252 | `use_case`: What will you mainly use it for? (49.2%) | `size`: What size or fit do you need? (1.6%) | `style`: What style or fit do you prefer? (86.1%) | `material`: Do you have a material preference? (75.8%) |
| Statement | 249 | `use_case`: What will you mainly use it for? (67.1%) | `size`: What size or fit do you need? (1.6%) | `style`: What style or fit do you prefer? (24.1%) | `material`: Do you have a material preference? (91.2%) |
| Flip-Flops | 245 | `use_case`: What will you mainly use it for? (49.8%) | `size`: What size or fit do you need? (1.6%) | `feature`: Which feature matters most to you? (46.5%) | `style`: What style or fit do you prefer? (36.7%) |
| Running | 238 | `use_case`: What will you mainly use it for? (85.7%) | `size`: What size or fit do you need? (0.4%) | `feature`: Which feature matters most to you? (52.1%) | `style`: What style or fit do you prefer? (39.1%) |
| Snow & Cold Weather | 232 | `use_case`: What will you mainly use it for? (77.6%) | `size`: What size or fit do you need? (4.3%) | `style`: What style or fit do you prefer? (24.6%) | `material`: Do you have a material preference? (85.8%) |
| Everyday Bras | 230 | `size`: What size or fit do you need? (16.1%) | `material`: Do you have a material preference? (85.7%) | `feature`: Which feature matters most to you? (76.1%) | `use_case`: What will you mainly use it for? (36.1%) |
| Polos | 219 | `use_case`: What will you mainly use it for? (46.1%) | `size`: What size or fit do you need? (8.7%) | `style`: What style or fit do you prefer? (73.5%) | `material`: Do you have a material preference? (90.0%) |
| Pant Sets | 203 | `use_case`: What will you mainly use it for? (54.7%) | `size`: What size or fit do you need? (1.5%) | `style`: What style or fit do you prefer? (71.4%) | `material`: Do you have a material preference? (90.6%) |
| Skirts | 202 | `use_case`: What will you mainly use it for? (62.4%) | `size`: What size or fit do you need? (20.3%) | `style`: What style or fit do you prefer? (73.3%) | `material`: Do you have a material preference? (86.1%) |

## No-preference flow

For every row: record the current attribute as `neutral`, move to the next column, and never ask the neutral attribute again. If all four are answered, neutral, already asked, or unable to narrow live candidates, use `ask_attribute = null`.

## Evidence boundary

All counts, vocabulary, aliases, category families, and classification findings come from participant-visible fields in `data/catalog.jsonl`. Public ground truth, target ASINs, and session-specific answer rules were not used.
