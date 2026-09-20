"""Create a new season from explicit local Archipelago inputs."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
SEASON_NAME_PATTERN = re.compile(r"^\d+\.\s+.+$")
PLACEHOLDER_PATTERN = re.compile(r"\{(?:player|PLAYER|number|NUMBER)\}")
VERSION_PATTERN = re.compile(r"_v(\d+)\.yaml$", re.IGNORECASE)


class ScaffoldError(RuntimeError):
    """A user-actionable scaffolding error."""


@dataclass(frozen=True)
class PlayerInput:
    source: Path
    target_name: str
    player_name: str
    game: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a new Awepeeps season without changing imported YAML settings. "
            "Use --dry-run to review the planned files first."
        )
    )
    parser.add_argument(
        "--season",
        required=True,
        help="New season path such as 2026/4. Winter, relative to the repository root.",
    )
    parser.add_argument(
        "--player",
        action="append",
        required=True,
        type=Path,
        help="Player YAML to import; repeat for each player.",
    )
    parser.add_argument(
        "--host-yaml",
        type=Path,
        help="Host YAML to copy as YAML/.host.yaml.",
    )
    parser.add_argument(
        "--template-season",
        type=Path,
        help="Existing season whose YAML/.host.yaml should be used when --host-yaml is omitted.",
    )
    parser.add_argument(
        "--apworld",
        action="append",
        type=Path,
        help="APWorld archive to import; repeat for each archive.",
    )
    parser.add_argument(
        "--rom",
        action="append",
        type=Path,
        help="Local ROM to copy into the ignored .roms/ directory; repeat as needed.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs and print the plan without creating files.",
    )
    return parser.parse_args()


def resolve_input(path: Path) -> Path:
    return path.expanduser().resolve()


def resolve_season(path: Path) -> Path:
    season = path.expanduser()
    if not season.is_absolute():
        season = ROOT / season
    season = season.resolve()
    if not SEASON_NAME_PATTERN.fullmatch(season.name):
        raise ScaffoldError(
            f"season must use '<number>. <name>' format, such as '4. Winter': {season.name}"
        )
    if not season.parent.name.isdigit():
        raise ScaffoldError(f"season must live under a numeric year directory: {season}")
    try:
        season.relative_to(ROOT)
    except ValueError as exc:
        raise ScaffoldError(f"season must be inside the repository: {season}") from exc
    if season.exists():
        raise ScaffoldError(f"season already exists; refusing to overwrite it: {season}")
    return season


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise ScaffoldError(
            "PyYAML is required. Run `python -m pip install -r requirements-dev.txt`."
        ) from exc

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ScaffoldError(f"could not read YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ScaffoldError(f"YAML file must contain a mapping: {path}")
    return data


def require_file(path: Path, description: str) -> Path:
    resolved = resolve_input(path)
    if not resolved.is_file():
        raise ScaffoldError(f"{description} does not exist or is not a file: {resolved}")
    return resolved


def normalize_component(value: str) -> str:
    value = value.replace("_", "-")
    value = re.sub(r"[^A-Za-z0-9 .-]+", "", value)
    value = re.sub(r"\s+", " ", value).strip(" .-")
    if not value:
        raise ScaffoldError(f"cannot create a filename component from: {value!r}")
    return value


def game_slug(game: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", game).strip("-").lower()
    if not slug:
        raise ScaffoldError(f"cannot create a filename game slug from: {game!r}")
    return slug


def player_target_name(source: Path, player_name: str, game: str) -> str:
    version_match = VERSION_PATTERN.search(source.name)
    version = version_match.group(1) if version_match else "0"
    game_component = "TBD" if game.strip() == "TBD" else game_slug(game)
    return f"{normalize_component(player_name)}_{game_component}_v{version}.yaml"


def prepare_players(paths: list[Path]) -> list[PlayerInput]:
    players: list[PlayerInput] = []
    target_names: set[str] = set()
    player_names: set[str] = set()
    for raw_path in paths:
        source = require_file(raw_path, "player YAML")
        data = load_yaml(source)
        player_name = data.get("name")
        game = data.get("game")
        if not isinstance(player_name, str) or not player_name.strip():
            raise ScaffoldError(f"player YAML is missing a non-empty name: {source}")
        if PLACEHOLDER_PATTERN.search(player_name):
            raise ScaffoldError(
                f"player YAML must use a literal in-game name for a new season: {source}"
            )
        normalized_player_name = player_name.strip().casefold()
        if normalized_player_name in player_names:
            raise ScaffoldError(f"duplicate player name: {player_name.strip()}")
        player_names.add(normalized_player_name)
        if not isinstance(game, str) or not game.strip():
            raise ScaffoldError(f"player YAML is missing a non-empty game: {source}")

        target_name = player_target_name(source, player_name.strip(), game.strip())
        normalized_target_name = target_name.casefold()
        if normalized_target_name in target_names:
            raise ScaffoldError(f"multiple player inputs map to {target_name}")
        target_names.add(normalized_target_name)
        players.append(
            PlayerInput(
                source=source,
                target_name=target_name,
                player_name=player_name.strip(),
                game=game.strip(),
            )
        )
    return players


def validate_apworld(path: Path) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            broken_file = archive.testzip()
    except (OSError, zipfile.BadZipFile) as exc:
        raise ScaffoldError(f"invalid APWorld archive {path}: {exc}") from exc
    if broken_file is not None:
        raise ScaffoldError(f"corrupt file in APWorld archive {path}: {broken_file}")


def prepare_apworlds(paths: list[Path]) -> list[Path]:
    archives: list[Path] = []
    names: set[str] = set()
    for raw_path in paths:
        archive = require_file(raw_path, "APWorld archive")
        if archive.suffix.lower() != ".apworld":
            raise ScaffoldError(f"APWorld input must use the .apworld extension: {archive}")
        validate_apworld(archive)
        if archive.name in names:
            raise ScaffoldError(f"duplicate APWorld filename: {archive.name}")
        names.add(archive.name)
        archives.append(archive)
    return archives


def prepare_host(host_yaml: Path | None, template_season: Path | None) -> Path:
    if host_yaml is not None and template_season is not None:
        raise ScaffoldError("use either --host-yaml or --template-season, not both")
    if template_season is not None:
        template = template_season.expanduser()
        if not template.is_absolute():
            template = ROOT / template
        host_yaml = template / "YAML" / ".host.yaml"
    if host_yaml is None:
        raise ScaffoldError("provide --host-yaml or --template-season")
    return require_file(host_yaml, "host YAML")


def prepare_roms(paths: list[Path]) -> list[Path]:
    roms: list[Path] = []
    names: set[str] = set()
    for raw_path in paths:
        rom = require_file(raw_path, "ROM input")
        if rom.name in names:
            raise ScaffoldError(f"duplicate ROM filename: {rom.name}")
        names.add(rom.name)
        roms.append(rom)
    return roms


def markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def render_readme(season: Path, players: list[PlayerInput], apworlds: list[Path]) -> str:
    year = season.parent.name
    season_label = season.name.split(".", 1)[1].strip()
    player_rows = "\n".join(
        f"| {markdown_cell(player.player_name)} | {markdown_cell(player.game)} | "
        f"[YAML](YAML/{quote(player.target_name)}) |"
        for player in players
    )
    apworld_links = ", ".join(
        f"[{archive.name}](APWorld/{quote(archive.name)})" for archive in apworlds
    ) or "None yet"
    return f"""# {season_label} {year} Games

> **Status:** Active

## Session Links

- **YAML Configurations:** [YAML/](YAML/)
- **APWorld Files:** [APWorld/](APWorld/)
- **Secrets and Spoilers:** [.secrets/](.secrets/)

## Players & Games

| Player | Game | YAML |
|--------|------|------|
{player_rows}

## APWorlds

{apworld_links}

## Notes

- Add the session date, room link, and game-specific setup notes before hosting.
- Review the host settings in `YAML/.host.yaml`; its paths are relative to the Archipelago installation.
- Run `python scripts/validate_repo.py` before sharing the season.
"""


def print_plan(
    season: Path,
    host: Path,
    players: list[PlayerInput],
    apworlds: list[Path],
    roms: list[Path],
) -> None:
    print(f"Season: {season}")
    print(f"Host: {host}")
    print("Players:")
    for player in players:
        print(f"  {player.target_name} ({player.player_name} - {player.game})")
    print("APWorlds:")
    for archive in apworlds:
        print(f"  {archive.name}")
    print("Local ROMs:")
    for rom in roms:
        print(f"  {rom.name} -> .roms/{rom.name}")


def create_season(
    season: Path,
    host: Path,
    players: list[PlayerInput],
    apworlds: list[Path],
    roms: list[Path],
) -> None:
    (season / "YAML").mkdir(parents=True)
    (season / "APWorld").mkdir()
    (season / ".secrets" / "revealed").mkdir(parents=True)
    (season / ".secrets" / "hidden").mkdir()
    (season / ".roms").mkdir()

    shutil.copy2(host, season / "YAML" / ".host.yaml")
    for player in players:
        shutil.copy2(player.source, season / "YAML" / player.target_name)
    for archive in apworlds:
        shutil.copy2(archive, season / "APWorld" / archive.name)
    for rom in roms:
        shutil.copy2(rom, season / ".roms" / rom.name)

    (season / "YAML" / ".gitkeep").touch()
    (season / "APWorld" / ".gitkeep").touch()
    (season / ".secrets" / "revealed" / ".gitkeep").touch()
    (season / "README.md").write_text(
        render_readme(season, players, apworlds), encoding="utf-8"
    )


def main() -> int:
    args = parse_args()
    try:
        season = resolve_season(Path(args.season))
        host = prepare_host(args.host_yaml, args.template_season)
        players = prepare_players(args.player)
        apworlds = prepare_apworlds(args.apworld or [])
        roms = prepare_roms(args.rom or [])
        print_plan(season, host, players, apworlds, roms)
        if args.dry_run:
            print("Dry run complete; no files were created.")
            return 0
        create_season(season, host, players, apworlds, roms)
        print(f"Season scaffold created: {season}")
        return 0
    except ScaffoldError as exc:
        print(f"Scaffolding failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())