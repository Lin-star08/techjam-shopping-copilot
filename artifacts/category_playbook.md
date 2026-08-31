# Category Question Playbook v2

This file is generated from `data/public_set1.jsonl` by `artifacts/build_lexicon.py`.
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

- Products scanned: 3021
- Products with usable prices: 2168 (71.76%)
- Coverage is catalog-derived and is a safety signal, not the conversation order.

## Classification audit

- Products with no category path: 0
- The following leaf labels need fallback handling:

| Leaf label | Products | Issue | Parent paths | Required handling |
| --- | ---: | --- | ---: | --- |
| Westlake | 24 | noisy_leaf | 1 | The leaf does not describe a stable product type; infer from the full path and title. |
| Shoes | 21 | broad_leaf | 3 | The leaf is valid but too broad; identify footwear purpose before details. |
| Clothing | 15 | broad_leaf | 3 | The leaf is valid but too broad; identify garment type before details. |
| Casual | 46 | ambiguous_leaf | 5 | The same leaf appears under dresses, pants, skirts, and shorts; retain its parent path. |
| Sets | 26 | ambiguous_leaf | 8 | The same leaf appears under sleepwear, swimwear, activewear, and underwear; retain its parent path. |
| Women | 13 | broad_leaf | 3 | Audience is not a product type; infer the requested item before attributes. |
| Men | 7 | broad_leaf | 3 | Audience is not a product type; infer the requested item before attributes. |

## Question order table

The percentages show how often the vocabulary found usable catalog evidence. Size coverage is conservative because numeric sizes are parsed separately by member 2.

| Category | Products | Ask 1 | Ask 2 | Ask 3 | Ask 4 |
| --- | ---: | --- | --- | --- | --- |
| T-Shirts | 111 | `use_case`: What will you mainly use it for? (64.0%) | `size`: What size or fit do you need? (8.1%) | `style`: What style or fit do you prefer? (77.5%) | `material`: Do you have a material preference? (95.5%) |
| Wrist Watches | 67 | `use_case`: What will you mainly use it for? (62.7%) | `feature`: Which feature matters most to you? (73.1%) | `style`: What style or fit do you prefer? (47.8%) | `material`: Do you have a material preference? (85.1%) |
| Costumes | 53 | `use_case`: What will you mainly use it for? (94.3%) | `size`: What size or fit do you need? (13.2%) | `style`: What style or fit do you prefer? (64.1%) | `budget`: What budget would you like to stay within? (81.1%) |
| Socks | 52 | `size`: What size or fit do you need? (34.6%) | `material`: Do you have a material preference? (100.0%) | `feature`: Which feature matters most to you? (71.2%) | `use_case`: What will you mainly use it for? (63.5%) |
| Slippers | 51 | `use_case`: What will you mainly use it for? (82.3%) | `size`: What size or fit do you need? (5.9%) | `feature`: Which feature matters most to you? (88.2%) | `style`: What style or fit do you prefer? (25.5%) |
| Athletic Socks | 49 | `size`: What size or fit do you need? (6.1%) | `material`: Do you have a material preference? (93.9%) | `feature`: Which feature matters most to you? (91.8%) | `use_case`: What will you mainly use it for? (69.4%) |
| Sunglasses | 48 | `use_case`: What will you mainly use it for? (62.5%) | `feature`: Which feature matters most to you? (89.6%) | `style`: What style or fit do you prefer? (52.1%) | `color`: What color would you prefer? (56.2%) |
| Casual | 46 | `category`: What kind of item are you looking for? (0.0%) | `use_case`: What will you mainly use it for? (73.9%) | `size`: What size or fit do you need? (19.6%) | `style`: What style or fit do you prefer? (93.5%) |
| Dresses | 44 | `use_case`: What will you mainly use it for? (88.6%) | `size`: What size or fit do you need? (27.3%) | `style`: What style or fit do you prefer? (97.7%) | `material`: Do you have a material preference? (97.7%) |
| Wallets | 42 | `use_case`: What will you mainly use it for? (66.7%) | `size`: What size or fit do you need? (2.4%) | `feature`: Which feature matters most to you? (45.2%) | `style`: What style or fit do you prefer? (52.4%) |
| Fashion Sneakers | 37 | `use_case`: What will you mainly use it for? (56.8%) | `size`: What size or fit do you need? (2.7%) | `feature`: Which feature matters most to you? (75.7%) | `style`: What style or fit do you prefer? (43.2%) |
| Loafers & Slip-Ons | 35 | `use_case`: What will you mainly use it for? (54.3%) | `size`: What size or fit do you need? (2.9%) | `feature`: Which feature matters most to you? (77.1%) | `style`: What style or fit do you prefer? (68.6%) |
| Jeans | 35 | `use_case`: What will you mainly use it for? (37.1%) | `size`: What size or fit do you need? (28.6%) | `style`: What style or fit do you prefer? (85.7%) | `material`: Do you have a material preference? (97.1%) |
| Stud | 34 | `use_case`: What will you mainly use it for? (85.3%) | `style`: What style or fit do you prefer? (38.2%) | `material`: Do you have a material preference? (85.3%) | `feature`: Which feature matters most to you? (52.9%) |
| Leggings | 34 | `use_case`: What will you mainly use it for? (64.7%) | `size`: What size or fit do you need? (14.7%) | `style`: What style or fit do you prefer? (55.9%) | `material`: Do you have a material preference? (91.2%) |
| Pants | 32 | `use_case`: What will you mainly use it for? (78.1%) | `size`: What size or fit do you need? (15.6%) | `style`: What style or fit do you prefer? (81.2%) | `material`: Do you have a material preference? (90.6%) |
| Hoop | 31 | `use_case`: What will you mainly use it for? (83.9%) | `style`: What style or fit do you prefer? (58.1%) | `material`: Do you have a material preference? (100.0%) | `feature`: Which feature matters most to you? (71.0%) |
| Blouses & Button-Down Shirts | 31 | `use_case`: What will you mainly use it for? (87.1%) | `size`: What size or fit do you need? (12.9%) | `style`: What style or fit do you prefer? (93.5%) | `material`: Do you have a material preference? (93.5%) |
| Crossbody Bags | 31 | `use_case`: What will you mainly use it for? (48.4%) | `size`: What size or fit do you need? (3.2%) | `feature`: Which feature matters most to you? (90.3%) | `style`: What style or fit do you prefer? (22.6%) |
| Fashion Hoodies & Sweatshirts | 30 | `use_case`: What will you mainly use it for? (73.3%) | `size`: What size or fit do you need? (13.3%) | `style`: What style or fit do you prefer? (100.0%) | `material`: Do you have a material preference? (93.3%) |
| Road Running | 30 | `use_case`: What will you mainly use it for? (100.0%) | `size`: What size or fit do you need? (0.0%) | `feature`: Which feature matters most to you? (73.3%) | `style`: What style or fit do you prefer? (13.3%) |
| Flats | 29 | `use_case`: What will you mainly use it for? (51.7%) | `size`: What size or fit do you need? (6.9%) | `feature`: Which feature matters most to you? (79.3%) | `style`: What style or fit do you prefer? (58.6%) |
| Drop & Dangle | 28 | `use_case`: What will you mainly use it for? (89.3%) | `style`: What style or fit do you prefer? (53.6%) | `material`: Do you have a material preference? (85.7%) | `feature`: Which feature matters most to you? (67.9%) |
| Belts | 26 | `use_case`: What will you mainly use it for? (73.1%) | `size`: What size or fit do you need? (11.5%) | `style`: What style or fit do you prefer? (88.5%) | `material`: Do you have a material preference? (96.2%) |
| Sets | 26 | `category`: What kind of item are you looking for? (0.0%) | `use_case`: What will you mainly use it for? (73.1%) | `size`: What size or fit do you need? (26.9%) | `style`: What style or fit do you prefer? (73.1%) |
| Tunics | 26 | `use_case`: What will you mainly use it for? (73.1%) | `size`: What size or fit do you need? (30.8%) | `style`: What style or fit do you prefer? (100.0%) | `material`: Do you have a material preference? (92.3%) |
| Necklaces | 25 | `use_case`: What will you mainly use it for? (84.0%) | `style`: What style or fit do you prefer? (24.0%) | `material`: Do you have a material preference? (76.0%) | `feature`: Which feature matters most to you? (60.0%) |
| Platforms & Wedges | 25 | `use_case`: What will you mainly use it for? (56.0%) | `size`: What size or fit do you need? (4.0%) | `feature`: Which feature matters most to you? (64.0%) | `style`: What style or fit do you prefer? (48.0%) |
| Pendant Necklaces | 24 | `use_case`: What will you mainly use it for? (87.5%) | `style`: What style or fit do you prefer? (20.8%) | `material`: Do you have a material preference? (87.5%) | `feature`: Which feature matters most to you? (41.7%) |
| Tanks & Camis | 24 | `use_case`: What will you mainly use it for? (83.3%) | `size`: What size or fit do you need? (20.8%) | `style`: What style or fit do you prefer? (87.5%) | `material`: Do you have a material preference? (83.3%) |
| Active Shorts | 24 | `use_case`: What will you mainly use it for? (83.3%) | `size`: What size or fit do you need? (0.0%) | `style`: What style or fit do you prefer? (58.3%) | `material`: Do you have a material preference? (91.7%) |
| Westlake | 24 | `category`: What kind of item are you looking for? (0.0%) | `use_case`: What will you mainly use it for? (50.0%) | `size`: What size or fit do you need? (12.5%) | `style`: What style or fit do you prefer? (50.0%) |
| Pullovers | 23 | `use_case`: What will you mainly use it for? (60.9%) | `size`: What size or fit do you need? (13.0%) | `style`: What style or fit do you prefer? (82.6%) | `material`: Do you have a material preference? (87.0%) |
| Skirts | 23 | `use_case`: What will you mainly use it for? (78.3%) | `size`: What size or fit do you need? (26.1%) | `style`: What style or fit do you prefer? (73.9%) | `material`: Do you have a material preference? (100.0%) |
| Casual Button-Down Shirts | 21 | `use_case`: What will you mainly use it for? (61.9%) | `size`: What size or fit do you need? (9.5%) | `style`: What style or fit do you prefer? (85.7%) | `material`: Do you have a material preference? (95.2%) |
| Shoes | 21 | `use_case`: What will you mainly use it for? (52.4%) | `size`: What size or fit do you need? (0.0%) | `feature`: Which feature matters most to you? (71.4%) | `style`: What style or fit do you prefer? (23.8%) |
| Baseball Caps | 19 | `use_case`: What will you mainly use it for? (57.9%) | `size`: What size or fit do you need? (31.6%) | `style`: What style or fit do you prefer? (47.4%) | `material`: Do you have a material preference? (89.5%) |
| Walking | 19 | `use_case`: What will you mainly use it for? (84.2%) | `size`: What size or fit do you need? (0.0%) | `feature`: Which feature matters most to you? (100.0%) | `style`: What style or fit do you prefer? (57.9%) |
| Cold Weather Gloves | 18 | `use_case`: What will you mainly use it for? (83.3%) | `size`: What size or fit do you need? (16.7%) | `style`: What style or fit do you prefer? (33.3%) | `material`: Do you have a material preference? (94.4%) |
| Totes | 18 | `use_case`: What will you mainly use it for? (88.9%) | `size`: What size or fit do you need? (0.0%) | `feature`: Which feature matters most to you? (83.3%) | `style`: What style or fit do you prefer? (50.0%) |
| Slides | 17 | `use_case`: What will you mainly use it for? (58.8%) | `size`: What size or fit do you need? (0.0%) | `feature`: Which feature matters most to you? (58.8%) | `style`: What style or fit do you prefer? (52.9%) |
| Cardigans | 17 | `use_case`: What will you mainly use it for? (64.7%) | `size`: What size or fit do you need? (23.5%) | `style`: What style or fit do you prefer? (82.3%) | `material`: Do you have a material preference? (82.3%) |
| Bottoms | 16 | `use_case`: What will you mainly use it for? (100.0%) | `size`: What size or fit do you need? (18.8%) | `style`: What style or fit do you prefer? (37.5%) | `material`: Do you have a material preference? (93.8%) |
| Sneakers | 16 | `use_case`: What will you mainly use it for? (75.0%) | `size`: What size or fit do you need? (0.0%) | `feature`: Which feature matters most to you? (81.2%) | `style`: What style or fit do you prefer? (56.2%) |
| Mules & Clogs | 16 | `use_case`: What will you mainly use it for? (43.8%) | `size`: What size or fit do you need? (0.0%) | `feature`: Which feature matters most to you? (87.5%) | `style`: What style or fit do you prefer? (56.2%) |
| Nightgowns & Sleepshirts | 16 | `size`: What size or fit do you need? (31.2%) | `material`: Do you have a material preference? (100.0%) | `feature`: Which feature matters most to you? (81.2%) | `use_case`: What will you mainly use it for? (81.2%) |
| Everyday Bras | 16 | `size`: What size or fit do you need? (0.0%) | `material`: Do you have a material preference? (93.8%) | `feature`: Which feature matters most to you? (87.5%) | `use_case`: What will you mainly use it for? (31.2%) |
| Ankle & Bootie | 16 | `use_case`: What will you mainly use it for? (31.2%) | `size`: What size or fit do you need? (0.0%) | `feature`: Which feature matters most to you? (43.8%) | `style`: What style or fit do you prefer? (50.0%) |
| Sandals | 16 | `use_case`: What will you mainly use it for? (81.2%) | `size`: What size or fit do you need? (0.0%) | `feature`: Which feature matters most to you? (87.5%) | `style`: What style or fit do you prefer? (56.2%) |
| Heeled Sandals | 16 | `use_case`: What will you mainly use it for? (50.0%) | `size`: What size or fit do you need? (0.0%) | `feature`: Which feature matters most to you? (62.5%) | `style`: What style or fit do you prefer? (68.8%) |
| Clothing | 15 | `category`: What kind of item are you looking for? (0.0%) | `use_case`: What will you mainly use it for? (73.3%) | `size`: What size or fit do you need? (26.7%) | `style`: What style or fit do you prefer? (66.7%) |
| Statement | 15 | `use_case`: What will you mainly use it for? (86.7%) | `size`: What size or fit do you need? (0.0%) | `style`: What style or fit do you prefer? (33.3%) | `material`: Do you have a material preference? (93.3%) |
| Polos | 14 | `use_case`: What will you mainly use it for? (64.3%) | `size`: What size or fit do you need? (7.1%) | `style`: What style or fit do you prefer? (71.4%) | `material`: Do you have a material preference? (100.0%) |
| Sweatpants | 14 | `use_case`: What will you mainly use it for? (71.4%) | `size`: What size or fit do you need? (35.7%) | `style`: What style or fit do you prefer? (85.7%) | `material`: Do you have a material preference? (100.0%) |
| Vests | 14 | `use_case`: What will you mainly use it for? (71.4%) | `size`: What size or fit do you need? (21.4%) | `style`: What style or fit do you prefer? (78.6%) | `material`: Do you have a material preference? (100.0%) |
| Snow & Cold Weather | 14 | `use_case`: What will you mainly use it for? (78.6%) | `size`: What size or fit do you need? (7.1%) | `style`: What style or fit do you prefer? (35.7%) | `material`: Do you have a material preference? (92.9%) |
| One-Pieces | 14 | `use_case`: What will you mainly use it for? (71.4%) | `size`: What size or fit do you need? (21.4%) | `style`: What style or fit do you prefer? (78.6%) | `material`: Do you have a material preference? (92.9%) |
| Hats & Caps | 14 | `use_case`: What will you mainly use it for? (64.3%) | `size`: What size or fit do you need? (28.6%) | `style`: What style or fit do you prefer? (21.4%) | `material`: Do you have a material preference? (78.6%) |
| Tops | 13 | `use_case`: What will you mainly use it for? (38.5%) | `size`: What size or fit do you need? (7.7%) | `style`: What style or fit do you prefer? (92.3%) | `material`: Do you have a material preference? (92.3%) |
| Flip-Flops | 13 | `use_case`: What will you mainly use it for? (84.6%) | `size`: What size or fit do you need? (15.4%) | `feature`: Which feature matters most to you? (84.6%) | `style`: What style or fit do you prefer? (76.9%) |

## No-preference flow

For every row: record the current attribute as `neutral`, move to the next column, and never ask the neutral attribute again. If all four are answered, neutral, already asked, or unable to narrow live candidates, use `ask_attribute = null`.

## Evidence boundary

All counts, vocabulary, aliases, category families, and classification findings come from participant-visible fields in `data/public_set1.jsonl`. Public ground truth, target ASINs, and session-specific answer rules were not used.
