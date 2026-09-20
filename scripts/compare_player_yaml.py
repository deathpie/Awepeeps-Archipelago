"""Compare two player YAMLs while optionally ignoring metadata fields."""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path
from typing import Any


class CompareError(RuntimeError):
    """A user-actionable comparison error."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare parsed player YAML settings. By default, name and description "
            "are treated as organizational metadata."
        )
    )
    parser.add_argument("before", type=Path, help="Original player YAML.")
    parser.add_argument("after", type=Path, help="Candidate player YAML.")
    parser.add_argument(
        "--ignore",
        action="append",
        default=["name", "description"],
        metavar="KEY",
        help="Top-level YAML key to ignore; repeat as needed. Defaults to name and description.",
    )
    return parser.parse_args()


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise CompareError(
            "PyYAML is required. Run `python -m pip install -r requirements-dev.txt`."
        ) from exc

    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise CompareError(f"could not read YAML {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CompareError(f"YAML file must contain a mapping: {path}")
    return value


def comparable(data: dict[str, Any], ignored: set[str]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if key not in ignored}


def format_data(data: dict[str, Any]) -> list[str]:
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True).splitlines()


def main() -> int:
    args = parse_args()
    try:
        before = load_yaml(args.before.expanduser().resolve())
        after = load_yaml(args.after.expanduser().resolve())
        ignored = set(args.ignore)
        before_settings = comparable(before, ignored)
        after_settings = comparable(after, ignored)
        if before_settings == after_settings:
            print("YAML settings match.")
            print(f"Ignored top-level keys: {', '.join(sorted(ignored))}")
            return 0

        diff = difflib.unified_diff(
            format_data(before_settings),
            format_data(after_settings),
            fromfile=str(args.before),
            tofile=str(args.after),
            lineterm="",
        )
        print("YAML settings differ:")
        print("\n".join(diff))
        return 1
    except CompareError as exc:
        print(f"Comparison failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())