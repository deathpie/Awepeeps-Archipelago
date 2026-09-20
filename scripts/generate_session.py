"""Generate an Archipelago session from one season's checked-in inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SAFE_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True)
class PlayerInput:
    source: Path
    name: str
    game: str


class GenerationError(RuntimeError):
    """A user-actionable preflight or generation error."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare and generate one Awepeeps Archipelago season. "
            "Use --dry-run to preflight without generating."
        )
    )
    parser.add_argument(
        "--season",
        required=True,
        help="Season directory, relative to the repository root or an absolute path.",
    )
    parser.add_argument(
        "--archipelago",
        required=True,
        type=Path,
        help="Archipelago installation containing ArchipelagoGenerate.exe and custom_worlds/.",
    )
    parser.add_argument(
        "--run-id",
        help="Output workspace name. Defaults to the current local date.",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        help="Override the output root; defaults to the season's .secrets/hidden directory.",
    )
    parser.add_argument(
        "--generator",
        type=Path,
        help="Override the Archipelago generator executable path.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Optional numeric seed passed to ArchipelagoGenerate.",
    )
    parser.add_argument(
        "--spoiler",
        type=int,
        choices=range(4),
        metavar="0-3",
        help="Override host.yaml spoiler level; omitted means Archipelago uses the copied host configuration.",
    )
    parser.add_argument(
        "--sync-apworlds",
        action="store_true",
        help="Copy the season's validated APWorld archives into custom_worlds/ when needed.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run preflight and print the command without creating files or generating output.",
    )
    return parser.parse_args()


def resolve_path(path: Path, base: Path) -> Path:
    return path if path.is_absolute() else base / path


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise GenerationError(
            "PyYAML is required. Run `python -m pip install -r requirements-dev.txt`."
        ) from exc

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise GenerationError(f"could not read YAML {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise GenerationError(f"YAML file must contain a mapping: {path}")
    return data


def load_players(yaml_dir: Path) -> tuple[list[PlayerInput], set[str]]:
    players: list[PlayerInput] = []
    required_versions: set[str] = set()
    names: set[str] = set()

    for source in sorted(yaml_dir.glob("*.yaml")):
        if source.name == ".host.yaml":
            continue

        data = load_yaml(source)
        game = data.get("game")
        name = data.get("name")
        if game == "TBD":
            print(f"Skipping TBD player: {source.name}")
            continue
        if isinstance(game, str) and game.strip().casefold() == "tbd":
            raise GenerationError(f"{source} must use the exact placeholder game: TBD")
        if not isinstance(game, str) or not game.strip():
            raise GenerationError(f"{source} is missing a non-empty game")
        if not isinstance(name, str) or not name.strip():
            raise GenerationError(f"{source} is missing a non-empty name")
        normalized_name = name.strip().casefold()
        if normalized_name in names:
            raise GenerationError(f"duplicate player name in {yaml_dir}: {name.strip()}")
        names.add(normalized_name)

        requires = data.get("requires")
        if isinstance(requires, dict) and requires.get("version") is not None:
            required_versions.add(str(requires["version"]))
        players.append(PlayerInput(source=source, name=name, game=game))

    if not players:
        raise GenerationError(f"No playable player YAMLs found in {yaml_dir}")
    return players, required_versions


def validate_apworld(path: Path) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            broken_file = archive.testzip()
    except (OSError, zipfile.BadZipFile) as exc:
        raise GenerationError(f"invalid APWorld archive {path}: {exc}") from exc
    if broken_file is not None:
        raise GenerationError(f"corrupt file in APWorld archive {path}: {broken_file}")


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def version_tuple(value: str) -> tuple[int, ...]:
    try:
        parts = tuple(int(part) for part in value.split("."))
    except ValueError as exc:
        raise GenerationError(f"invalid Archipelago version: {value}") from exc
    if len(parts) != 3:
        raise GenerationError(f"invalid Archipelago version: {value}")
    return parts


def sync_apworlds(
    season: Path,
    archipelago: Path,
    allow_sync: bool,
    dry_run: bool,
) -> list[Path]:
    source_dir = season / "APWorld"
    destination_dir = archipelago / "custom_worlds"
    if not source_dir.is_dir():
        raise GenerationError(f"missing APWorld directory: {source_dir}")

    sources = sorted(source_dir.glob("*.apworld"))
    if not sources:
        print(f"No season APWorld archives found in {source_dir}; using installed core worlds.")
        return []
    if not destination_dir.is_dir():
        raise GenerationError(f"missing Archipelago custom_worlds directory: {destination_dir}")

    for source in sources:
        validate_apworld(source)
        destination = destination_dir / source.name
        if destination.is_file() and file_hash(source) == file_hash(destination):
            print(f"APWorld ready: {source.name}")
            continue
        if not allow_sync:
            raise GenerationError(
                f"installed APWorld is missing or differs: {destination}\n"
                "Re-run with --sync-apworlds after reviewing the archive source."
            )
        if dry_run:
            print(f"APWorld would be copied: {source.name}")
            continue
        shutil.copy2(source, destination)
        print(f"APWorld copied: {source.name}")
    return sources


def check_archipelago_version(archipelago: Path, required_versions: set[str]) -> str | None:
    if not required_versions:
        return None
    manifest_path = archipelago / "manifest.json"
    if not manifest_path.is_file():
        raise GenerationError(f"missing Archipelago manifest: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        installed_version = ".".join(str(part) for part in manifest["version"])
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise GenerationError(f"could not read Archipelago version from {manifest_path}: {exc}") from exc

    required_version = max(required_versions, key=version_tuple)
    if version_tuple(installed_version) < version_tuple(required_version):
        raise GenerationError(
            f"Archipelago {installed_version} is installed, but the player YAMLs require "
            f"{required_version}"
        )
    print(
        f"Archipelago version ready: {installed_version} "
        f"(highest YAML requirement: {required_version})"
    )
    return installed_version


def find_generator(archipelago: Path, override: Path | None) -> Path:
    if override is not None:
        generator = override.resolve()
    else:
        candidates = (archipelago / "ArchipelagoGenerate.exe", archipelago / "ArchipelagoGenerate")
        generator = next((candidate for candidate in candidates if candidate.is_file()), candidates[0])
    if not generator.is_file():
        raise GenerationError(f"Archipelago generator not found: {generator}")
    return generator


def safe_run_id(run_id: str | None) -> str:
    value = run_id or datetime.now().strftime("%Y-%m-%d")
    if not SAFE_RUN_ID.fullmatch(value):
        raise GenerationError("--run-id may contain only letters, numbers, dots, underscores, and hyphens")
    return value


def reject_default_run_id_collision(
    season: Path,
    run_id: str,
    explicit: bool,
    workspace_root: Path | None,
) -> None:
    if explicit:
        return
    hidden_root = (workspace_root or season / ".secrets" / "hidden").resolve()
    candidates = (hidden_root / run_id, season / ".secrets" / "revealed" / run_id)
    collisions = [path for path in candidates if path.exists()]
    if collisions:
        listed = ", ".join(str(path) for path in collisions)
        raise GenerationError(
            f"the default run ID already exists: {listed}\n"
            "Choose a new explicit --run-id before generating."
        )


def build_workspace(
    season: Path,
    players: list[PlayerInput],
    run_id: str,
    workspace_root: Path | None,
    dry_run: bool,
) -> tuple[Path, Path, Path]:
    root = (workspace_root or season / ".secrets" / "hidden").resolve()
    workspace = root / run_id
    players_dir = workspace / "Players"
    output_dir = workspace / "output"

    if dry_run:
        return workspace, players_dir, output_dir
    if workspace.exists():
        raise GenerationError(f"output workspace already exists: {workspace}")

    players_dir.mkdir(parents=True)
    output_dir.mkdir()
    shutil.copy2(season / "YAML" / ".host.yaml", workspace / "host.yaml")
    for player in players:
        shutil.copy2(player.source, players_dir / player.source.name)
    return workspace, players_dir, output_dir


def write_manifest(
    workspace: Path,
    season: Path,
    players: list[PlayerInput],
    apworlds: list[Path],
    archipelago_version: str | None,
    generator: Path,
    command: list[str],
) -> None:
    manifest = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "season": season.relative_to(ROOT).as_posix(),
        "archipelago_version": archipelago_version,
        "generator": {"path": str(generator), "sha256": file_hash(generator)},
        "players": [
            {"name": player.name, "game": player.game, "file": player.source.name, "sha256": file_hash(player.source)}
            for player in players
        ],
        "apworlds": [{"file": path.name, "sha256": file_hash(path)} for path in apworlds],
        "host_sha256": file_hash(season / "YAML" / ".host.yaml"),
        "command": command,
    }
    (workspace / "generation-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


def stage_revealed_files(workspace: Path, output_dir: Path) -> tuple[Path, Path]:
    archives = sorted(output_dir.glob("AP_*.zip"))
    if len(archives) != 1:
        raise GenerationError(
            f"expected exactly one generated AP archive in {output_dir}, found {len(archives)}"
        )

    archive_path = archives[0]
    spoiler_entries: list[str]
    with zipfile.ZipFile(archive_path) as archive:
        spoiler_entries = [
            entry.filename
            for entry in archive.infolist()
            if entry.filename.endswith("_Spoiler.txt")
        ]
        if len(spoiler_entries) != 1:
            raise GenerationError(
                f"expected exactly one spoiler file in {archive_path.name}, found {len(spoiler_entries)}"
            )
        spoiler_bytes = archive.read(spoiler_entries[0])

    date_prefix = datetime.now().strftime("%Y-%m-%d")
    seed_path = workspace / f"{date_prefix}_seed.zip"
    spoiler_path = workspace / f"{date_prefix}_spoiler.txt"
    shutil.copy2(archive_path, seed_path)
    spoiler_path.write_bytes(spoiler_bytes)
    return seed_path, spoiler_path


def build_command(
    generator: Path,
    players_dir: Path,
    output_dir: Path,
    seed: int | None,
    spoiler: int | None,
) -> list[str]:
    command = [
        str(generator),
        "--player_files_path",
        str(players_dir),
        "--outputpath",
        str(output_dir),
    ]
    if seed is not None:
        command.extend(("--seed", str(seed)))
    if spoiler is not None:
        command.extend(("--spoiler", str(spoiler)))
    return command


def main() -> int:
    args = parse_args()
    try:
        season = resolve_path(Path(args.season), ROOT).resolve()
        archipelago = args.archipelago.expanduser().resolve()
        if not season.is_dir():
            raise GenerationError(f"season directory not found: {season}")
        if not archipelago.is_dir():
            raise GenerationError(f"Archipelago directory not found: {archipelago}")

        yaml_dir = season / "YAML"
        host_path = yaml_dir / ".host.yaml"
        if not host_path.is_file():
            raise GenerationError(f"missing season host configuration: {host_path}")

        players, required_versions = load_players(yaml_dir)
        archipelago_version = check_archipelago_version(archipelago, required_versions)
        apworlds = sync_apworlds(season, archipelago, args.sync_apworlds, args.dry_run)
        generator = find_generator(archipelago, args.generator)
        run_id = safe_run_id(args.run_id)
        workspace_root = resolve_path(args.workspace_root, ROOT) if args.workspace_root is not None else None
        reject_default_run_id_collision(season, run_id, args.run_id is not None, workspace_root)
        workspace, players_dir, output_dir = build_workspace(
            season,
            players,
            run_id,
            workspace_root,
            args.dry_run,
        )
        command = build_command(generator, players_dir, output_dir, args.seed, args.spoiler)

        print(f"Players: {', '.join(player.name for player in players)}")
        print(f"Host configuration: {host_path}")
        print(f"Workspace: {workspace}")
        print("Command:")
        print("  " + subprocess.list2cmdline(command))
        if args.dry_run:
            print("Dry run complete; no files were created.")
            return 0

        result = subprocess.run(command, cwd=workspace, check=False)
        if result.returncode != 0:
            raise GenerationError(f"Archipelago generation failed with exit code {result.returncode}")
        seed_path, spoiler_path = stage_revealed_files(workspace, output_dir)
        write_manifest(workspace, season, players, apworlds, archipelago_version, generator, command)
        print(f"Generation complete. Inspect staged seed and spoiler files in: {workspace}")
        print(
            "Move these staged files into the appropriate date folder under "
            f"{season / '.secrets' / 'revealed'} when you are ready to reveal them:"
        )
        print(f"  Seed: {seed_path}")
        print(f"  Spoiler: {spoiler_path}")
        return 0
    except GenerationError as exc:
        print(f"Generation not started: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())