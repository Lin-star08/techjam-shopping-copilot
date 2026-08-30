from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


SEED = "techjam-20260829-v1"
HOLDOUT_COUNTS = {
    "buying": 20,
    "browsing": 20,
    "intent_override": 7,
    "boundary": 3,
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _split_key(sample_id: str, scenario: str, seed: str) -> str:
    value = f"{seed}\0{scenario}\0{sample_id}".encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def build_split(dataset_path: str | Path, seed: str = SEED) -> dict:
    source = Path(dataset_path)
    groups: dict[str, list[str]] = defaultdict(list)
    seen: set[str] = set()

    with source.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            sample = json.loads(line)
            sample_id = str(sample["sample_id"])
            scenario = str(sample["scenario_type"])
            if sample_id in seen:
                raise ValueError(f"duplicate sample_id at line {line_number}: {sample_id}")
            if scenario not in HOLDOUT_COUNTS:
                raise ValueError(f"unsupported scenario at line {line_number}: {scenario}")
            seen.add(sample_id)
            groups[scenario].append(sample_id)

    if set(groups) != set(HOLDOUT_COUNTS):
        raise ValueError(f"scenario mismatch: found {sorted(groups)}")

    development: list[str] = []
    holdout: list[str] = []
    development_counts: Counter[str] = Counter()
    holdout_counts: Counter[str] = Counter()

    for scenario in sorted(groups):
        ordered = sorted(groups[scenario], key=lambda value: _split_key(value, scenario, seed))
        holdout_count = HOLDOUT_COUNTS[scenario]
        if len(ordered) <= holdout_count:
            raise ValueError(f"not enough {scenario} rows for holdout={holdout_count}")
        scenario_holdout = ordered[:holdout_count]
        scenario_development = ordered[holdout_count:]
        holdout.extend(scenario_holdout)
        development.extend(scenario_development)
        holdout_counts[scenario] = len(scenario_holdout)
        development_counts[scenario] = len(scenario_development)

    development.sort()
    holdout.sort()
    return {
        "schema_version": 1,
        "source_dataset": source.as_posix(),
        "source_sha256": _sha256(source),
        "method": "scenario-stratified SHA-256 ordering of sample_id",
        "seed": seed,
        "selection_fields": ["sample_id", "scenario_type"],
        "uses_ground_truth_for_selection": False,
        "counts": {
            "total": len(development) + len(holdout),
            "development": len(development),
            "holdout": len(holdout),
            "development_by_scenario": dict(sorted(development_counts.items())),
            "holdout_by_scenario": dict(sorted(holdout_counts.items())),
        },
        "development_sample_ids": development,
        "holdout_sample_ids": holdout,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the fixed public development/holdout split")
    parser.add_argument("--dataset", default="data/public_set.jsonl")
    parser.add_argument("--output", default="docs/internal_split.json")
    parser.add_argument("--seed", default=SEED)
    args = parser.parse_args()

    payload = build_split(args.dataset, args.seed)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["counts"], indent=2))


if __name__ == "__main__":
    main()
