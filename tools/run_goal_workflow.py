from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "hit_rate_at_10": (">", 0.98),
    "mrr": (">", 0.95),
    "mttc": ("<", 2.16),
}


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def select_samples(dataset: Path, split_path: Path, split_name: str) -> list[dict]:
    rows = load_jsonl(dataset)
    if split_name == "full":
        return rows
    split = json.loads(split_path.read_text(encoding="utf-8"))
    key = "development_sample_ids" if split_name == "development" else "holdout_sample_ids"
    selected = set(split[key])
    return [row for row in rows if row["sample_id"] in selected]


def target_status(result: dict) -> dict[str, dict[str, object]]:
    status: dict[str, dict[str, object]] = {}
    for metric, (operator, threshold) in TARGETS.items():
        value = float(result[metric])
        passed = value > threshold if operator == ">" else value < threshold
        status[metric] = {
            "value": value,
            "operator": operator,
            "threshold": threshold,
            "passed": passed,
        }
    return status


def audit_no_public_label_literals(source_root: Path, dataset: Path) -> list[str]:
    rows = load_jsonl(dataset)
    forbidden = {
        str(row["sample_id"])
        for row in rows
    } | {
        str(row["ground_truth"]["parent_asin"])
        for row in rows
    }
    findings: list[str] = []
    for path in sorted(source_root.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        try:
            display_path = path.relative_to(ROOT)
        except ValueError:
            display_path = path
        for literal in forbidden:
            if literal in text:
                findings.append(f"{display_path} contains forbidden literal {literal}")
    return findings


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the gated conversational-search optimization workflow.")
    parser.add_argument("--split", choices=("development", "holdout", "full"), default="development")
    parser.add_argument("--open-holdout", action="store_true", help="Required for holdout or full evaluation.")
    parser.add_argument("--dataset", type=Path, default=Path("data/public_set.jsonl"))
    parser.add_argument("--catalog", type=Path, default=Path("data/catalog.jsonl"))
    parser.add_argument("--split-file", type=Path, default=Path("docs/internal_split.json"))
    parser.add_argument("--output", type=Path, default=Path("results/goal-development.json"))
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()

    if args.split != "development" and not args.open_holdout:
        parser.error("--open-holdout is required for holdout or full evaluation")

    dataset = ROOT / args.dataset
    findings = audit_no_public_label_literals(ROOT / "starter", dataset)
    if findings:
        raise SystemExit("public-label leakage audit failed:\n" + "\n".join(findings))

    if not args.skip_tests:
        run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"])

    selected = select_samples(dataset, ROOT / args.split_file, args.split)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", encoding="utf-8") as handle:
        for row in selected:
            handle.write(json.dumps(row, separators=(",", ":")) + "\n")
        handle.flush()
        run([
            sys.executable,
            "-m",
            "evaluator.local_evaluator",
            "--catalog",
            str(args.catalog),
            "--dataset",
            handle.name,
            "--output",
            str(args.output),
        ])

    result = json.loads((ROOT / args.output).read_text(encoding="utf-8"))
    checks = target_status(result)
    print(json.dumps({
        "split": args.split,
        "sample_count": len(selected),
        "leakage_audit": "passed",
        "targets": checks,
        "all_targets_passed": all(item["passed"] for item in checks.values()),
        "output": str(args.output),
    }, indent=2))


if __name__ == "__main__":
    main()
