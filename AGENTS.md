# Repository Guidelines

This is a documentation and configuration repository for Archipelago community sessions. The root [README.md](README.md) describes the human workflow; this file records the rules an AI coding agent must apply while editing it. Use [docs/agent-workflows.md](docs/agent-workflows.md) for task routing and [docs/session-workflow.md](docs/session-workflow.md) for the detailed session lifecycle.

## Source of truth

- Read the relevant season README before changing a season.
- For a new season, input import, generation, or artifact publication, use the repository scripts documented in [docs/session-workflow.md](docs/session-workflow.md) instead of recreating the workflow manually.
- Keep player YAMLs in that season's `YAML/` directory and APWorld archives in `APWorld/`.
- Use `YAML/.host.yaml` for host settings. The filename is intentionally dot-prefixed.
- Run `python scripts/validate_repo.py` after repository changes. If the validator fails, do not proceed. Report the failing checks to the maintainer and either fix the underlying issue or revert the change; never weaken the validator to make it pass. Update the validator when a deliberate repository convention changes instead of weakening checks to make a change pass.

## Session conventions

- Active-season player YAMLs use a literal in-game alias in top-level `name:`. Do not generate `{player}`, `{PLAYER}`, `{number}`, or `{NUMBER}` placeholders for active sessions.
- Historical archived seasons may retain their original placeholders. Preserve them unless a maintainer explicitly requests a historical correction.
- Name player files `player_game_vN.yaml`; use the game name in lowercase with spaces replaced by hyphens and all other punctuation removed (e.g. "Super Mario World" -> `super-mario-world`), and increment the version when replacing a configuration.
- A `TBD` player YAML must set `game: TBD` as the placeholder until the player's game is chosen.
- Season host paths such as `Players` and `output` are relative to the Archipelago installation, not the repository or season folder.

## ROMs, secrets, and APWorlds

- Never add ROM content or ROM download links. Keep local ROMs in an ignored `.roms/` directory or outside the repository.
- The validator and CI reject common ROM extensions, including cartridge images, disc images, and compressed console images. Do not bypass the ignore rules with forced staging.
- Never track private spoilers, credentials, generated secrets, or files under `.secrets/hidden/` or `.generated-secrets-hidden/`. Only intentionally shareable material belongs in `.secrets/revealed/`.
- `.apworld` files are ZIP archives. Validate their integrity and inspect their source or release before recommending manual installation into Archipelago's `custom_worlds` directory. Do not execute or install untrusted archives automatically. If an `.apworld` archive fails integrity checks or its source cannot be verified, do not recommend installation; flag it as untrusted and report the specific failure to the maintainer.
- Do not place generated output, player copies, server logs, or local credentials in the repository just because the host config refers to relative paths.

## Editing and Git safety

- Preserve unrelated user changes and archived session history.
- Read-only Git inspection is allowed: `git status`, `git diff`, `git log`, `git ls-files`, and `git check-ignore` are useful for validation.
- Do not run `git add`, `git commit`, `git push`, `git reset`, `git clean`, or checkout/revert commands. Leave staging, history, and destructive operations to the human maintainer.
- Do not broaden a documentation change into a season rewrite. Keep README tables faithful to the season's existing columns and links.
- Do not create an agent skill merely to duplicate this file or the validator. Add a skill only when a repeatable, on-demand workflow needs guidance beyond these repository-wide rules.

## Validation

From the repository root:

```powershell
python -m pip install -r requirements-dev.txt
python scripts/validate_repo.py
```

The GitHub workflow runs the same validator on pushes and pull requests. A passing check does not replace human review of game settings, ROM compatibility, APWorld provenance, or generated spoiler handling.
