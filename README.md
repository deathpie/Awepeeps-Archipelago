# Awepeeps Archipelago

This repository organizes Archipelago multiworld configurations, setup references, and session records for the Awepeeps community.

## Repository layout

- `2026/<number>. <Season>/`: one folder per session season.
- `README.md` in each season: game links, player assignments, session dates, and setup notes.
- `YAML/`: player configurations and the season's `.host.yaml` generation settings.
- `APWorld/`: APWorld archives kept with the session for reference and local installation.
- `.secrets/revealed/`: spoiler logs or other files intentionally shared with the repository.
- `.secrets/hidden/`: private local files; this path is ignored.
- `.roms/`: local ROM storage; this path is ignored and must stay local.
- [Archipelago resources](Archipelago.md): general setup and community links.

Spring and Summer 2026 are archived. Their historical YAMLs may retain `{player}` placeholders. New or active-season YAMLs use the literal in-game player name in `name:`.

## Preparing a session

1. Read the season README and the linked game setup guides.
2. Install each required APWorld manually into the Archipelago installation's `custom_worlds` directory. Review the source or release before installing an archive; this repository does not automatically install or trust third-party code.
3. Obtain any required game files lawfully. ROMs are never stored or linked here. Keep local copies under the season's `.roms/` directory or another local-only location.
4. Copy the player YAMLs from the season's `YAML/` directory into the Archipelago installation's `Players/` directory, or provide them through Archipelago's normal generation workflow. Do not copy `.host.yaml` as a player file.
5. Use the season's `YAML/.host.yaml` for host settings when generating. Its `player_files_path: "Players"` and `output_path: "output"` are relative to the Archipelago installation, not this repository.
6. Keep generated private spoilers, logs, and credentials in `.secrets/hidden/` or another ignored local directory. Move a file to `.secrets/revealed/` only when it is intentionally shareable.

For the complete create, generate, publish, and archive workflow, see [Session workflow](docs/session-workflow.md). AI agents should also follow [Agent workflows](docs/agent-workflows.md).

### Reproducible session generation

Use `scripts/generate_session.py` to generate a seed from one season's checked-in player YAMLs, host settings, and APWorld archives. The command skips player files whose `game` is `TBD`, checks the installed Archipelago version and APWorld hashes, and writes each run to the season's ignored `.secrets/hidden/<run-id>/` directory. A run without `--run-id` uses the current date, such as `2026-09-20`.

From PowerShell, run a preflight first:

```powershell
python scripts/generate_session.py `
	--season "2026/3. Fall" `
	--archipelago "C:\ProgramData\Archipelago" `
	--dry-run
```

After reviewing the reported players and command, omit `--dry-run` to generate. Add `--seed <number>` to select a known numeric seed, `--run-id <name>` for a memorable private output directory, and `--sync-apworlds` only after reviewing any APWorld archive that the tool reports as missing or different. Each completed run contains a `generation-manifest.json` with input hashes, the generator executable hash, and the command, plus `YYYY-MM-DD_seed.zip` and `YYYY-MM-DD_spoiler.txt` directly in the private run folder. Use `scripts/publish_session_artifacts.py --season <season> --run <run-id> --dry-run`, then rerun without `--dry-run`, to publish those two files into the matching `.secrets/revealed/<run-id>/` folder. Treat the numeric seed as part of the run identity, not as a guarantee of byte-identical output across different Archipelago, APWorld, or runtime states.

Do not copy generated output into `.secrets/revealed/` unless the spoiler or seed is deliberately being shared with the group.

Game-specific caveats belong in the season README. For example, Fall 2026 documents the SM64 decompilation workflow and the local Crystal ROM filename expected by its host configuration.

## Validation

Install the development dependency once, then run the repository validator from the repository root:

```powershell
python -m pip install -r requirements-dev.txt
python scripts/validate_repo.py
```

The validator checks season structure, YAML parsing, active player names, duplicate names, APWorld ZIP integrity, local Markdown links, ignore rules, and tracked or non-ignored files with common ROM extensions. GitHub Actions runs the same check on every push and pull request.

## Contribution rules

- Keep changes scoped to the relevant season and preserve archived session history unless a maintainer explicitly requests an archive correction.
- Use `player_game_vN.yaml` filenames and literal player aliases for active sessions.
- Never commit ROMs, ROM download links, private secrets, generated credentials, or unreviewed generated output.
- Run the validator before asking for review. The pull-request template records the remaining manual checks.
- Read [AGENTS.md](AGENTS.md) before making repository changes with an AI coding agent.
