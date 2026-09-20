"""Validate the structure and safety rules for Awepeeps Archipelago."""

from __future__ import annotations

import re
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
SEASONS_ROOT = ROOT / "2026"
SEASON_NAME_PATTERN = re.compile(r"^\d+\.\s+.+$")
PLACEHOLDER_PATTERN = re.compile(r"\{(?:player|PLAYER|number|NUMBER)\}")
PLAYER_FILENAME_PATTERN = re.compile(
    r"^[^_]+_[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*_v\d+\.yaml$"
)
MARKDOWN_LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]*)\)")
ROM_EXTENSIONS = {
    ".a26",
    ".a52",
    ".a78",
    ".3ds",
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
    ".wbfs",
    ".wad",
    ".wud",
    ".wux",
    ".xci",
    ".z64",
}
PRIVATE_PATH_PARTS = {".roms", ".generated-secrets-hidden"}


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def repository_files(errors: list[str]) -> list[Path]:
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(ROOT),
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
            ],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        errors.append(f"could not inspect repository files with git ls-files: {exc}")
        return []

    return [ROOT / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def validate_ignore_rules(errors: list[str]) -> None:
    ignore_path = ROOT / ".gitignore"
    if not ignore_path.is_file():
        errors.append("missing .gitignore")
        return

    ignore_text = read_text(ignore_path)
    required_patterns = (
        "**/.secrets/hidden/",
        "**/.generated-secrets-hidden/",
        "**/.roms/",
    ) + tuple(f"*{extension}" for extension in sorted(ROM_EXTENSIONS))
    for pattern in required_patterns:
        if pattern not in ignore_text:
            errors.append(f".gitignore is missing required pattern: {pattern}")


def validate_tracked_safety(files: list[Path], errors: list[str]) -> None:
    for path in files:
        parts = {part.lower() for part in path.relative_to(ROOT).parts}
        if ".secrets" in parts and "hidden" in parts:
            errors.append(f"private secret is tracked: {relative(path)}")
        if parts & PRIVATE_PATH_PARTS:
            errors.append(f"local-only path is tracked: {relative(path)}")
        if path.suffix.lower() in ROM_EXTENSIONS:
            errors.append(f"ROM-like file is tracked or not ignored: {relative(path)}")


def validate_seasons(errors: list[str], yaml_module: object) -> None:
    if not SEASONS_ROOT.is_dir():
        errors.append("missing 2026 season directory")
        return

    season_dirs = sorted(
        path
        for path in SEASONS_ROOT.iterdir()
        if path.is_dir() and SEASON_NAME_PATTERN.match(path.name)
    )
    if not season_dirs:
        errors.append("no season directories found under 2026")
        return

    for season in season_dirs:
        for required in ("README.md", "APWorld", "YAML", ".secrets/revealed"):
            required_path = season / required
            if not required_path.exists():
                errors.append(f"{relative(season)} is missing {required}/")

        host_path = season / "YAML" / ".host.yaml"
        if not host_path.is_file():
            errors.append(f"{relative(season)} is missing YAML/.host.yaml")

        yaml_dir = season / "YAML"
        if not yaml_dir.is_dir():
            continue

        yaml_files = sorted(yaml_dir.glob("*.yaml"))
        player_files = [path for path in yaml_files if path.name != ".host.yaml"]
        names: dict[str, Path] = {}
        readme_path = season / "README.md"
        readme_text = read_text(readme_path) if readme_path.is_file() else ""
        archived = bool(
            re.search(r"\*\*Status:\*\*\s*Inactive\b", readme_text[:1500], re.IGNORECASE)
        )

        for yaml_path in yaml_files:
            try:
                data = yaml_module.safe_load(read_text(yaml_path))
            except Exception as exc:  # PyYAML exposes several parser exception types.
                errors.append(f"invalid YAML in {relative(yaml_path)}: {exc}")
                continue

            if not isinstance(data, dict):
                errors.append(f"{relative(yaml_path)} must contain a YAML mapping")
                continue

            if yaml_path.name == ".host.yaml":
                continue

            if not PLAYER_FILENAME_PATTERN.fullmatch(yaml_path.name):
                errors.append(
                    f"{relative(yaml_path)} must use player_game_vN.yaml format "
                    "with hyphens between game words"
                )

            name = data.get("name")
            game = data.get("game")
            if not isinstance(name, str) or not name.strip():
                errors.append(f"{relative(yaml_path)} is missing a non-empty name")
            elif not archived and PLACEHOLDER_PATTERN.search(name):
                errors.append(
                    f"active season uses a slot placeholder in {relative(yaml_path)}: {name}"
                )
            elif name.casefold() in names:
                errors.append(
                    f"duplicate player name in {relative(season)}: "
                    f"{names[name.casefold()].name} and {yaml_path.name}"
                )
            else:
                names[name.casefold()] = yaml_path

            if not isinstance(game, str) or not game.strip():
                errors.append(f"{relative(yaml_path)} is missing a non-empty game")

        apworld_dir = season / "APWorld"
        if apworld_dir.is_dir():
            for apworld_path in sorted(apworld_dir.glob("*.apworld")):
                try:
                    with zipfile.ZipFile(apworld_path) as archive:
                        broken_file = archive.testzip()
                except (OSError, zipfile.BadZipFile) as exc:
                    errors.append(f"invalid APWorld archive {relative(apworld_path)}: {exc}")
                    continue
                if broken_file is not None:
                    errors.append(
                        f"corrupt file in APWorld archive {relative(apworld_path)}: {broken_file}"
                    )


def validate_markdown_links(errors: list[str]) -> None:
    markdown_files = sorted(
        path
        for path in ROOT.rglob("*.md")
        if ".git" not in path.parts and ".secrets" not in path.parts
    )
    for markdown_path in markdown_files:
        try:
            text = read_text(markdown_path)
        except UnicodeDecodeError as exc:
            errors.append(f"could not read {relative(markdown_path)} as UTF-8: {exc}")
            continue

        for raw_target in MARKDOWN_LINK_PATTERN.findall(text):
            target = raw_target.strip()
            if target.startswith("<") and ">" in target:
                target = target[1 : target.index(">")]
            else:
                target = target.split(maxsplit=1)[0] if target else ""

            if (
                not target
                or target in {"link", "path"}
                or target.startswith(("#", "http://", "https://", "mailto:", "ftp://"))
            ):
                continue

            target = unquote(target.split("#", maxsplit=1)[0].split("?", maxsplit=1)[0])
            candidate = (markdown_path.parent / target).resolve()
            try:
                candidate.relative_to(ROOT)
            except ValueError:
                errors.append(f"local link escapes repository: {relative(markdown_path)} -> {target}")
                continue
            if not candidate.exists():
                errors.append(f"broken local link: {relative(markdown_path)} -> {target}")


def main() -> int:
    try:
        import yaml
    except ImportError:
        print(
            "PyYAML is required. Install development dependencies with "
            "python -m pip install -r requirements-dev.txt.",
            file=sys.stderr,
        )
        return 2

    errors: list[str] = []
    files = repository_files(errors)
    validate_ignore_rules(errors)
    validate_tracked_safety(files, errors)
    validate_seasons(errors, yaml)
    validate_markdown_links(errors)

    if errors:
        print("Repository validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Repository validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())