---
name: archipelago-session-workflow
description: "Use when creating or importing an Awepeeps Archipelago season, normalizing player YAMLs, validating APWorlds, generating a seed, or publishing seed/spoiler artifacts. Prefer the repository scripts and dry runs described in docs/session-workflow.md."
---

# Archipelago Session Workflow

Use this skill for session lifecycle work in this repository. The scripts are the executable source of truth; do not recreate their copy, move, or validation logic manually.

## Route

- New season or bulk input import: `python scripts/scaffold_session.py --dry-run`
- Prove a YAML rename is cosmetic: `python scripts/compare_player_yaml.py <before> <after>`
- Generate from one season: `python scripts/generate_session.py --dry-run`
- Publish staged artifacts: `python scripts/publish_session_artifacts.py --dry-run`
- Final gate: `python scripts/validate_repo.py`

Read [docs/session-workflow.md](../../../docs/session-workflow.md) for arguments, layout, and the private/revealed boundary. Read [docs/agent-workflows.md](../../../docs/agent-workflows.md) for repository-specific safety rules.

## Required behavior

1. Read the selected season README and check `git status` before editing.
2. Use a literal player alias for an active season. Keep a `game: TBD` placeholder out of generation, but do not silently delete it from the season.
3. Treat `YAML/.host.yaml` as host configuration. Never place it in `Players/` or import it as a player.
4. Preserve player settings when changing only organization. Run the comparison helper and report any non-metadata diff.
5. Verify APWorld archives before installation or synchronization. Do not execute an unreviewed archive.
6. Keep generation work under `.secrets/hidden/`. Publish only intentionally shareable artifacts under `.secrets/revealed/`.
7. Run a dry run before each mutating lifecycle command. Do not overwrite an existing run or revealed artifact without an explicit user decision and the command's overwrite option.
8. Run the repository validator after edits. If it fails, fix the underlying issue or report it; never weaken the validator.

Do not invent room links, ports, seed identities, game settings, or release provenance. Unknown values belong in the season README as `TBD` until verified.
