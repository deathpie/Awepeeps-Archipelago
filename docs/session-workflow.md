# Session Workflow

This is the canonical operating procedure for creating, generating, and sharing an Awepeeps Archipelago session. Paths in commands are relative to the repository root unless they are absolute Windows paths.

## Layout

Each season follows this shape:

```text
2026/<number>. <Season>/
  README.md
  YAML/.host.yaml
  YAML/<player>_<game>_vN.yaml
  APWorld/<world>.apworld
  .roms/                         local only, ignored
  .secrets/hidden/<run-id>/      private generation workspace, ignored
  .secrets/revealed/<run-id>/    intentionally shared artifacts
```

`YAML/.host.yaml` is a host configuration, not a player file. Its `Players` and `output` paths are relative to the installed Archipelago directory. Do not copy it into a player folder or treat repository-relative paths as Archipelago paths.

## Create a season

Use `scripts/scaffold_session.py` when starting a new season or importing a group of local inputs. It refuses to overwrite an existing season, rejects duplicate player aliases, verifies APWorld ZIP integrity, and copies local ROMs into the ignored `.roms/` directory.

Start with a dry run:

```powershell
python scripts/scaffold_session.py `
    --season "2026/4. Winter" `
    --template-season "2026/3. Fall" `
    --player "C:\path\to\deathpie.yaml" `
    --player "C:\path\to\other-player.yaml" `
    --apworld "C:\path\to\world.apworld" `
    --rom "C:\path\to\local-rom.z64" `
    --dry-run
```

Use `--host-yaml` instead of `--template-season` when a specific host file is available. Repeat `--player`, `--apworld`, and `--rom` as needed. Review the printed mapping, then rerun the same command without `--dry-run`. The scaffold copies YAML bytes without changing game options, creates the standard folders, and writes a starter season README.

Active-season player YAMLs must already have literal names. A file with `name: "{player}"` or `name: "{number}"` is not ready for an active season; assign the real alias and verify the resulting file with [scripts/compare_player_yaml.py](../scripts/compare_player_yaml.py) when preserving settings matters.

Run the repository check immediately after scaffolding:

```powershell
python scripts/validate_repo.py
```

## Generate privately

Always preflight first. This reads only the selected season's YAML and APWorld inputs and skips `game: TBD` players:

```powershell
python scripts/generate_session.py `
    --season "2026/3. Fall" `
    --archipelago "C:\ProgramData\Archipelago" `
    --dry-run
```

After reviewing the player list and generator command, remove `--dry-run`. Use an explicit unique `--run-id` for named or repeated runs. If the date-only default already exists under either `.secrets/hidden/` or `.secrets/revealed/`, the generator requires an explicit new ID. Use `--seed <number>` only when a known numeric seed is required. Use `--sync-apworlds` only after reviewing the checked-in archive and its source; the default behavior stops on missing or different installed APWorlds.

The generator copies `YAML/.host.yaml` to the private workspace as `host.yaml` and runs `ArchipelagoGenerate` with that workspace as its current directory. Archipelago therefore loads omitted generator defaults, including spoiler level, from that copied file; a command-line option such as `--spoiler 1` overrides the corresponding host setting.

The completed run stays private under `.secrets/hidden/<run-id>/` and contains:

- `Players/` with the playable YAML copies
- `host.yaml` and `generation-manifest.json`
- `output/` with Archipelago's raw output
- `YYYY-MM-DD_seed.zip` and `YYYY-MM-DD_spoiler.txt` staged for publication

The manifest records input hashes, the installed Archipelago version, the generator hash, and the command. Keep it with the private run when reproducibility or debugging matters. Publishing with `--run` rechecks the manifest structure and the player, APWorld, and host input hashes before copying artifacts.

## Publish deliberately

For a retained private run, validate and publish both artifacts together:

```powershell
python scripts/publish_session_artifacts.py `
    --season "2026/3. Fall" `
    --run "2026-09-20_test" `
    --dry-run

python scripts/publish_session_artifacts.py `
    --season "2026/3. Fall" `
    --run "2026-09-20_test"
```

If the private run has already been removed, provide explicit staged files instead:

```powershell
python scripts/publish_session_artifacts.py `
    --season "2026/3. Fall" `
    --seed "C:\private\2026-09-20_seed.zip" `
    --spoiler "C:\private\2026-09-20_spoiler.txt" `
    --destination "2026-09-20_test" `
    --dry-run
```

The publisher requires matching `YYYY-MM-DD` names, a readable and intact seed ZIP, a non-empty UTF-8 spoiler, and no ROM-like entries inside the seed. It refuses to overwrite existing artifacts unless `--overwrite` is explicit. It copies into `.secrets/revealed/<destination>/`; it does not delete the private source.

Only publish a spoiler when the group intentionally wants it revealed. A hosted session normally needs the seed archive, while the spoiler remains a deliberate disclosure choice.

## Close or archive a season

Before marking a season inactive, publish any artifact that the group has chosen to share, remove only private local work from `.secrets/hidden/`, and update that season's README manually with its status and final room/session links. Do not rewrite historical YAML settings or archived README tables as part of cleanup.

Finish with:

```powershell
python scripts/validate_repo.py
```

The validator is the repository gate. If it fails, fix the underlying input or report the failure; do not weaken the check or force ignored/private files into Git.
