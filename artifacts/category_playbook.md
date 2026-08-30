# Category Question Playbook v1

This file is generated from `data/catalog.jsonl` by `artifacts/build_lexicon.py`.
It does not use public ground truth. The machine-readable source of truth is
`artifacts/lexicon.json`.

## Usage contract for member 2

1. Consider questions in the listed order, but skip attributes already in `asked`, `neutral`, or current slots.
2. Ask at most one attribute, and only if it is expected to narrow the current candidates; otherwise return `ask_attribute = null`.
3. Treat catalog-derived priorities as a weak policy prior, not as hard constraints.
4. A later explicit preference replaces the earlier value. Invalidated values must never re-enter current-state retrieval.
5. Some frozen catalog leaf labels are noisy (for example, `Westlake`). Do not hard-filter on a category inferred only from a noisy leaf label.

## Catalog summary

- Products scanned: 50000
- Products with usable prices: 10410 (20.82%)
- Priority formula: attribute coverage x normalized value entropy x explainable policy prior.

## Top category priorities

### T-Shirts (2807 products)

Priority: `style` (coverage 66.4%), `brand` (coverage 100.0%), `material` (coverage 84.7%).

### Shoes (1299 products)

Priority: `color` (coverage 62.1%), `brand` (coverage 99.2%), `material` (coverage 61.1%).

### Westlake (1136 products)

Priority: `color` (coverage 64.9%), `style` (coverage 60.4%), `brand` (coverage 98.2%).

### Casual (1099 products)

Priority: `style` (coverage 86.5%), `material` (coverage 81.0%), `brand` (coverage 100.0%).

### Wrist Watches (1034 products)

Priority: `color` (coverage 85.8%), `material` (coverage 86.7%), `brand` (coverage 99.8%).

### Fashion Sneakers (1017 products)

Priority: `material` (coverage 87.3%), `brand` (coverage 99.9%), `feature` (coverage 41.5%).

### Flats (927 products)

Priority: `material` (coverage 74.7%), `brand` (coverage 100.0%), `feature` (coverage 42.9%).

### Blouses & Button-Down Shirts (691 products)

Priority: `style` (coverage 85.8%), `material` (coverage 77.4%), `use_case` (coverage 61.2%).

### Loafers & Slip-Ons (665 products)

Priority: `material` (coverage 91.7%), `brand` (coverage 100.0%), `feature` (coverage 50.1%).

### Dresses (656 products)

Priority: `style` (coverage 96.3%), `use_case` (coverage 77.1%), `material` (coverage 79.0%).

### Pumps (630 products)

Priority: `material` (coverage 74.4%), `brand` (coverage 100.0%), `style` (coverage 54.0%).

### Sets (610 products)

Priority: `material` (coverage 73.6%), `feature` (coverage 62.0%), `style` (coverage 59.2%).

### Sandals (586 products)

Priority: `brand` (coverage 100.0%), `feature` (coverage 50.3%), `material` (coverage 67.2%).

### Platforms & Wedges (545 products)

Priority: `material` (coverage 69.2%), `brand` (coverage 100.0%), `feature` (coverage 40.4%).

### Sunglasses (540 products)

Priority: `feature` (coverage 72.8%), `color` (coverage 60.0%), `brand` (coverage 99.4%).

### Slippers (538 products)

Priority: `material` (coverage 79.4%), `feature` (coverage 63.4%), `use_case` (coverage 69.0%).

### Pendant Necklaces (531 products)

Priority: `color` (coverage 86.2%), `material` (coverage 81.4%), `brand` (coverage 99.2%).

### Road Running (522 products)

Priority: `material` (coverage 82.0%), `feature` (coverage 46.9%), `use_case` (coverage 82.2%).

### Tunics (521 products)

Priority: `style` (coverage 87.1%), `use_case` (coverage 60.8%), `material` (coverage 78.1%).

### Drop & Dangle (503 products)

Priority: `color` (coverage 79.7%), `material` (coverage 75.1%), `use_case` (coverage 72.6%).

### Tanks & Camis (499 products)

Priority: `material` (coverage 79.8%), `style` (coverage 71.9%), `use_case` (coverage 58.5%).

### Fashion Hoodies & Sweatshirts (489 products)

Priority: `style` (coverage 76.9%), `material` (coverage 74.9%), `brand` (coverage 100.0%).

### Costumes (470 products)

Priority: `use_case` (coverage 90.4%), `material` (coverage 69.8%), `brand` (coverage 99.2%).

### Jeans (467 products)

Priority: `material` (coverage 89.1%), `style` (coverage 58.0%), `brand` (coverage 99.8%).

### Clothing (423 products)

Priority: `material` (coverage 63.6%), `style` (coverage 53.0%), `brand` (coverage 77.3%).

### Baseball Caps (385 products)

Priority: `material` (coverage 83.6%), `brand` (coverage 99.7%), `feature` (coverage 65.7%).

### Leggings (383 products)

Priority: `material` (coverage 80.4%), `feature` (coverage 65.5%), `use_case` (coverage 59.3%).

### Ankle & Bootie (382 products)

Priority: `material` (coverage 85.1%), `brand` (coverage 100.0%), `feature` (coverage 35.3%).

### Pullovers (379 products)

Priority: `style` (coverage 80.0%), `material` (coverage 74.9%), `brand` (coverage 100.0%).

### Socks (376 products)

Priority: `material` (coverage 90.2%), `feature` (coverage 55.0%), `brand` (coverage 100.0%).

