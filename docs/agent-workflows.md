# Agent Workflows

This repository has a small always-on policy in [AGENTS.md](../AGENTS.md). Use these routing rules to keep session work predictable and avoid rediscovering the same filesystem conventions.

For branch synchronization or GitHub account problems, use [Git workflow](git-workflow.md). Branch tracking and authentication are separate concerns.

## Route the task

| Task | First action | Required follow-up |
|------|--------------|--------------------|
| Create a season | Run `scripts/scaffold_session.py --dry-run` | Review the input mapping, scaffold, then validate |
| Import player YAMLs or APWorlds | Use the scaffold command or copy into the selected season only | Preserve YAML settings and validate archive integrity |
| Compare a renamed or normalized YAML | Run `scripts/compare_player_yaml.py` | Treat any non-metadata diff as a settings change |
| Generate a seed | Run `scripts/generate_session.py --dry-run` | Review players, version, APWorld drift, and command before generation |
| Share seed/spoiler artifacts | Run `scripts/publish_session_artifacts.py --dry-run` | Publish only after ZIP, date, and destination checks pass |
| Validate or prepare a pull request | Run `scripts/validate_repo.py` | Run `git diff --check` and inspect the final status |

## Before editing

1. Read the target season README and determine whether it is active or archived.
2. Inspect the current Git status and preserve unrelated user changes.
3. Keep player YAMLs, host settings, APWorlds, local ROMs, private runs, and revealed artifacts in their documented directories.
4. For a supplied YAML, compare the parsed settings before and after any name, description, filename, or version normalization. Do not claim a change is cosmetic without checking it.

## During editing

- Prefer the repository scripts over manual copy, rename, or move sequences.
- Use literal player aliases for active seasons. Skip `game: TBD` players during generation, but keep the placeholder YAML in the season until the game is chosen.
- Treat APWorld archives as code. Verify ZIP integrity and inspect the source or release before recommending installation or synchronization.
- Never read, print, or publish private generated spoilers, credentials, or local ROM content unless the user explicitly requests a review of a specific file and it is safe to do so.
- Do not invent room URLs, ports, seed identifiers, game settings, or release provenance. Mark unknown values as TBD and point to the owning README.

## After editing

Run the repository gate:

```powershell
python scripts/validate_repo.py
git diff --check
```

If validation fails, fix the source issue or stop and report it. Never relax the validator to make a new file pass. Do not use Git staging, commit, push, reset, clean, checkout, or revert commands unless the maintainer explicitly asks for that operation.
