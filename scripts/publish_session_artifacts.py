"""Publish a generated seed and spoiler into a season's revealed archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAFE_FOLDER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
ARTIFACT_NAMES = {
    "seed": re.compile(r"^(\d{4}-\d{2}-\d{2})_seed\.zip$"),
    "spoiler": re.compile(r"^(\d{4}-\d{2}-\d{2})_spoiler\.txt$"),
}
ROM_EXTENSIONS = {
    ".3ds",
    ".a26",
    ".a52",
    ".a78",
    ".bin",
    ".cdi",
    ".chd",
    ".cia",
    ".col",
    ".cue",
    ".gb",
    ".gba",
    ".gbc",
    ".gcm",
    ".gcz",
    ".gdi",
    ".gen",
    ".gg",
    ".img",
    ".int",
    ".iso",
    ".j64",
    ".n64",
    ".nds",
    ".neo",
    ".nes",
    ".ng",
    ".nsp",
    ".pce",
    ".pbp",
    ".rom",
    ".rvz",
    ".sfc",
    ".smc",
    ".smd",
    ".sg",
    ".sms",
    ".v64",
    ".wad",
    ".wbfs",
    ".wud",
    ".wux",
    ".xci",
    ".z64",
}
HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class PublishError(RuntimeError):
    """A user-actionable publishing error."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Copy a generated seed and spoiler into a season's revealed folder. "
            "The default source is a run under .secrets/hidden."
        )
    )
    parser.add_argument("--season", required=True, help="Season directory relative to the repository root.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--run", type=Path, help="Run directory name or path under .secrets/hidden.")
    source.add_argument("--seed", type=Path, help="Staged seed file to publish.")
    parser.add_argument("--spoiler", type=Path, help="Staged spoiler file when --seed is used.")
    parser.add_argument(
        "--destination",
        help="Revealed folder name; defaults to the run directory name when --run is used.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing destination artifacts explicitly.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs and print the copy plan without writing files.",
    )
    return parser.parse_args()


def resolve_path(path: Path, base: Path = ROOT) -> Path:
    return path.expanduser().resolve() if path.is_absolute() else (base / path).resolve()


def resolve_season(raw_path: str) -> Path:
    season = resolve_path(Path(raw_path))
    if not season.is_dir():
        raise PublishError(f"season directory not found: {season}")
    if not (season / ".secrets" / "revealed").is_dir():
        raise PublishError(f"season is missing .secrets/revealed/: {season}")
    return season


def require_file(path: Path, description: str) -> Path:
    if not path.is_file():
        raise PublishError(f"{description} does not exist or is not a file: {path}")
    return path


def inside(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
    except ValueError:
        return False
    return True


def validate_artifact_name(path: Path, kind: str) -> str:
    match = ARTIFACT_NAMES[kind].fullmatch(path.name)
    if match is None:
        raise PublishError(
            f"{kind} must be named YYYY-MM-DD_{kind}.{'zip' if kind == 'seed' else 'txt'}: {path.name}"
        )
    return match.group(1)


def validate_seed(path: Path) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            broken_file = archive.testzip()
            if broken_file is not None:
                raise PublishError(f"seed archive is corrupt: {path} ({broken_file})")
            unsafe_entries = sorted(
                entry.filename
                for entry in archive.infolist()
                if Path(entry.filename).suffix.lower() in ROM_EXTENSIONS
            )
    except (OSError, zipfile.BadZipFile) as exc:
        raise PublishError(f"seed is not a readable ZIP archive: {path}: {exc}") from exc
    if unsafe_entries:
        listed = ", ".join(unsafe_entries[:5])
        suffix = "..." if len(unsafe_entries) > 5 else ""
        raise PublishError(f"seed archive contains ROM-like entries: {listed}{suffix}")


def validate_spoiler(path: Path) -> None:
    try:
        if not path.read_text(encoding="utf-8").strip():
            raise PublishError(f"spoiler file is empty: {path}")
    except UnicodeDecodeError as exc:
        raise PublishError(f"spoiler is not UTF-8 text: {path}: {exc}") from exc
    except OSError as exc:
        raise PublishError(f"could not read spoiler: {path}: {exc}") from exc


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_hash(value: object, description: str) -> str:
    if not isinstance(value, str) or HASH_PATTERN.fullmatch(value) is None:
        raise PublishError(f"generation manifest has an invalid {description} SHA-256 hash")
    return value


def manifest_file(value: object, description: str) -> str:
    if not isinstance(value, str) or not value or Path(value).name != value:
        raise PublishError(f"generation manifest has an invalid {description} filename")
    return value


def validate_generation_manifest(run: Path, season: Path) -> None:
    manifest_path = require_file(run / "generation-manifest.json", "generation manifest")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PublishError(f"could not read generation manifest: {manifest_path}: {exc}") from exc
    if not isinstance(manifest, dict):
        raise PublishError(f"generation manifest must contain an object: {manifest_path}")

    try:
        expected_season = season.relative_to(ROOT).as_posix()
    except ValueError:
        expected_season = None
    if expected_season is not None and manifest.get("season") != expected_season:
        raise PublishError(
            f"generation manifest season does not match the selected season: {manifest.get('season')}"
        )

    host_hash = manifest_hash(manifest.get("host_sha256"), "host")
    source_host = require_file(season / "YAML" / ".host.yaml", "season host configuration")
    require_file(run / "host.yaml", "generated host configuration")
    if file_hash(source_host) != host_hash:
        raise PublishError(f"generation manifest host hash does not match: {source_host}")

    players = manifest.get("players")
    if not isinstance(players, list) or not players:
        raise PublishError("generation manifest must contain at least one player")
    for index, entry in enumerate(players, start=1):
        if not isinstance(entry, dict):
            raise PublishError(f"generation manifest player entry {index} is not an object")
        filename = manifest_file(entry.get("file"), f"player {index}")
        if not filename.endswith(".yaml"):
            raise PublishError(f"generation manifest player {index} is not a YAML file: {filename}")
        player_path = require_file(run / "Players" / filename, f"manifest player {index}")
        expected_hash = manifest_hash(entry.get("sha256"), f"player {index}")
        if file_hash(player_path) != expected_hash:
            raise PublishError(f"generation manifest player hash does not match: {filename}")

    apworlds = manifest.get("apworlds")
    if not isinstance(apworlds, list):
        raise PublishError("generation manifest APWorlds must be a list")
    for index, entry in enumerate(apworlds, start=1):
        if not isinstance(entry, dict):
            raise PublishError(f"generation manifest APWorld entry {index} is not an object")
        filename = manifest_file(entry.get("file"), f"APWorld {index}")
        if not filename.endswith(".apworld"):
            raise PublishError(f"generation manifest APWorld {index} is not an archive: {filename}")
        apworld_path = require_file(season / "APWorld" / filename, f"manifest APWorld {index}")
        expected_hash = manifest_hash(entry.get("sha256"), f"APWorld {index}")
        if file_hash(apworld_path) != expected_hash:
            raise PublishError(f"generation manifest APWorld hash does not match: {filename}")


def resolve_sources(args: argparse.Namespace, season: Path) -> tuple[Path, Path, str]:
    hidden = (season / ".secrets" / "hidden").resolve()
    if args.run is not None:
        if not hidden.is_dir():
            raise PublishError(f"season is missing .secrets/hidden/: {season}")
        run = resolve_path(args.run, hidden)
        if not inside(run, hidden):
            raise PublishError(f"run must be inside the season's hidden directory: {run}")
        run = require_file(run / "generation-manifest.json", "generation manifest").parent
        validate_generation_manifest(run, season)
        seed_files = sorted(run.glob("*_seed.zip"))
        spoiler_files = sorted(run.glob("*_spoiler.txt"))
        if len(seed_files) != 1 or len(spoiler_files) != 1:
            raise PublishError(
                f"run must contain exactly one staged seed and spoiler: {run} "
                f"(found {len(seed_files)} seeds and {len(spoiler_files)} spoilers)"
            )
        seed = seed_files[0]
        spoiler = spoiler_files[0]
        destination = args.destination or run.name
    else:
        if args.spoiler is None:
            raise PublishError("--spoiler is required when using --seed")
        seed = resolve_path(args.seed)
        spoiler = resolve_path(args.spoiler)
        if not args.destination:
            raise PublishError("--destination is required when using --seed and --spoiler")
        destination = args.destination

    if not SAFE_FOLDER.fullmatch(destination):
        raise PublishError("--destination may contain only letters, numbers, dots, underscores, and hyphens")
    return require_file(seed, "staged seed"), require_file(spoiler, "staged spoiler"), destination


def main() -> int:
    args = parse_args()
    try:
        season = resolve_season(args.season)
        seed, spoiler, destination = resolve_sources(args, season)
        seed_date = validate_artifact_name(seed, "seed")
        spoiler_date = validate_artifact_name(spoiler, "spoiler")
        if seed_date != spoiler_date:
            raise PublishError(f"seed and spoiler dates do not match: {seed_date} vs {spoiler_date}")
        validate_seed(seed)
        validate_spoiler(spoiler)

        destination_dir = season / ".secrets" / "revealed" / destination
        target_seed = destination_dir / seed.name
        target_spoiler = destination_dir / spoiler.name
        targets = (target_seed, target_spoiler)
        if not args.overwrite:
            existing = [str(path) for path in targets if path.exists()]
            if existing:
                raise PublishError(
                    "destination already contains an artifact; use --overwrite explicitly: "
                    + ", ".join(existing)
                )

        print(f"Seed: {seed}")
        print(f"Spoiler: {spoiler}")
        print(f"Destination: {destination_dir}")
        if args.dry_run:
            print("Dry run complete; no files were created.")
            return 0

        destination_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(seed, target_seed)
        shutil.copy2(spoiler, target_spoiler)
        print("Published seed and spoiler.")
        return 0
    except PublishError as exc:
        print(f"Publishing failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())