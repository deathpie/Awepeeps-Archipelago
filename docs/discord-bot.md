# Discord Tracking Bot

A session may run a self-hosted Discord bot so the group can follow check,
DeathLink, and hint activity in a channel. The supported bot is
[bridgeipelago](https://github.com/Quasky/bridgeipelago) (v3.0.1 or newer),
which connects to the room as a **spectator slot**. This document is the
reusable procedure; the season README records the specific bot slot for that
session.

## Spectator slot model

- The bot input uses `game: Archipelago`. That game maps to Archipelago's hidden
  GenericWorld, whose `generate_early` marks the player `SlotType.spectator`.
  The slot holds no items or locations and cannot affect the multiworld.
- The YAML `name` must equal the bot's `ArchipelagoBotSlot` in `config.json`.
- A dedicated spectator slot is preferred. Pointing the bot at a real player's
  slot works but makes it consume that player's item stream, so avoid it.

## Bot input

Add one file to the season's `YAML/` directory, named
`<BotName>_Archipelago_vN.yaml` so it satisfies the repository's
`player_game_vN.yaml` rule. For example:

```yaml
name: Bridgeipelago
game: Archipelago
description: Bridgeipelago Discord tracking bot (spectator slot)
Archipelago: {}
```

The slot must exist in the generated multiworld, so add this input **before**
generation. It is a normal season input and is included by
`scripts/generate_session.py`; it is not a playable player, so do not add it to
the season's player table.

## Secrets and layout

- `config.json` contains the Discord bot token and the room password. Never
  commit it, the token, the password, or the bot's data folders.
- Keep the canonical clone beside the other repositories under
  `<workspace>/projects/repos/Awepeeps-bridgeipelago`, outside this repository.
  Do not clone into a Windows or WSL home directory. Keep the Linux virtual
  environment in `~/.local/share/bridgeipelago/venv`; it is runtime data, not
  another source checkout.
- A repo-local clone under the ignored `bridgeipelago/` path is recognized by
  [.worktreeinclude](../.worktreeinclude) so a worktree can run the bot without
  a re-clone. Only `bridgeipelago/config.json` is listed there; the clone's data
  folders and `.venv` are rebuildable and are deliberately not copied. If the
  clone must live in the repository, `bridgeipelago/` is the ignored path; do not
  use `.secrets/hidden/` for it, since that path is private generation workspace
  and is excluded from `.worktreeinclude`.
- The bot writes `logs/`, `RegistrationData/`, `ItemQueue/`, and `ArchData/`
  relative to its working directory, keyed by `UniqueID`. Run it from its own
  directory so those folders stay together.

## Host on WSL2

Native Windows is unsupported by bridgeipelago v3; use WSL2 (or Docker).

1. Install WSL2/Ubuntu if needed: `wsl --install -d Ubuntu` in an admin
   PowerShell, then reboot and set the Linux user.
2. Install prerequisites (skip any already present):
   `sudo apt update && sudo apt install -y git python3 python3-venv python3-pip`
3. Clone our fork; `main` contains the reviewed Awepeeps patches:
   ```bash
   # Set this to the workspace root mounted in WSL.
   workspace=/mnt/d/dev/deathpie
   git clone https://github.com/Awepeeps/Awepeeps-bridgeipelago.git "$workspace/projects/repos/Awepeeps-bridgeipelago"
   cd "$workspace/projects/repos/Awepeeps-bridgeipelago"
   python3 -m venv ~/.local/share/bridgeipelago/venv
   ~/.local/share/bridgeipelago/venv/bin/python -m pip install --upgrade pip
   ~/.local/share/bridgeipelago/venv/bin/python -m pip install -r requirements.txt
   ~/.local/share/bridgeipelago/venv/bin/python -m pip install "websockets<14"   # newer versions break the receive loop
   ```
4. Create `config.json` from the shipped template, apply the `LanguageFile`
   fix, and fill the values (see Configuration).
5. Run it interactively from the clone, or install it as a WSL service (below).
   The wrapper forces the `fork` start method, which the bot needs on Python
   3.14 (see Run as a WSL service):
   ```bash
   ~/.local/share/bridgeipelago/venv/bin/python -u -c "import multiprocessing as m, runpy; m.set_start_method('fork'); runpy.run_path('bridgeipelago.py', run_name='__main__')" config.json
   ```

The clone lives outside this repository, so `config.json` and the data folders
never enter Git. If a dependency will not build on the installed Python,
install Python 3.12 and recreate the venv with it.

Verified environment: WSL2 Ubuntu, Python 3.14.4, git 2.53, bridgeipelago
`awepeeps-patches` (based on `live-v3.0.1`, commit `91a24ff`), websockets
13.1, discord.py 2.7.1.

### Forks and local changes

- Upstream is
  [Quasky/bridgeipelago](https://github.com/Quasky/bridgeipelago). The org fork
  is
  [Awepeeps/Awepeeps-bridgeipelago](https://github.com/Awepeeps/Awepeeps-bridgeipelago),
  and the personal fork is
  [deathpie/Awepeeps-bridgeipelago](https://github.com/deathpie/Awepeeps-bridgeipelago),
  made from the org fork, so all three share one fork network.
- `main` contains the reviewed Awepeeps changes. Keep the long-lived
  `awepeeps-patches` branch for maintaining our deviations from the original
  release (`live-v3.0.1`, commit `91a24ff`). Merge reviewed updates into `main`
  and synchronize both owned forks; never publish changes to Quasky.
- The branch is pushed to both forks, so `Awepeeps/Awepeeps-bridgeipelago` and
  `deathpie/Awepeeps-bridgeipelago` stay identical. Push it to both after every
  change.
- To upgrade, merge the original release tag into `awepeeps-patches`, verify
  the result, and fast-forward `main` in both owned forks (see Upgrading).
- Current patches on `awepeeps-patches`:
  - The port-change announcement: `CheckArchHost()` already detects a new
    archipelago.gg room port, updates `config.json`, and reports it to the
    debug channel; our patch also announces the new address in the broadcast
    channel so players know where to reconnect.
  - Debounced host-status failures: the room-status request is validated and
    runs off Discord's event loop; the alert fires once after five consecutive
    failed checks, and the next valid check after it posts a recovery notice.
  - The `$help` command, which posts the player-command list in the channel.
  - Optional connection announcements: `DiscordConfig.AnnounceConnection`
    defaults to `false`, suppressing the repeated debug-channel startup message.
  - Hint result announcements: newly revealed hints are relayed to the
    broadcast channel with durable dedupe, restart-preserving pending
    deliveries, bounded retries, and a persisted deadletter list
    (see Hint result announcements and the fork's
    [hint result reference](https://github.com/Awepeeps/Awepeeps-bridgeipelago/blob/awepeeps-patches/docs/hint-notifications.md)).

The live clone's remotes follow this layout: `origin` for the personal fork,
`upstream` for the Awepeeps org fork, and `quasky` for the original
Quasky/bridgeipelago project. Fetch original release tags from `quasky` when
upgrading; publish our patches to `upstream` and `origin`.

### Upgrading

Maintain original-project upgrades on `awepeeps-patches`, then fast-forward
`main` after verification. Stop the service first so the bot does not run
against a tree that changes underneath it:

```bash
systemctl --user stop bridgeipelago
git fetch quasky --tags
git switch awepeeps-patches
git merge <new-upstream-tag>    # for example live-v3.0.2
~/.local/share/bridgeipelago/venv/bin/python -m pip install -r requirements.txt
~/.local/share/bridgeipelago/venv/bin/python -m unittest discover
git push upstream awepeeps-patches
git push origin awepeeps-patches
git switch main
git merge --ff-only awepeeps-patches
git push upstream main
git push origin main
systemctl --user start bridgeipelago
```

This preserves existing history and uses ordinary pushes to both owned forks.
Keep local `main` tracking `origin/main`; `quasky` is a read-only source.

`config.json` is unchanged from v3.0.0, so no migration is needed.

## Run as a WSL service

With systemd enabled in WSL, run the bot as a user service so it starts on boot
and restarts on failure.

Create `~/.config/systemd/user/bridgeipelago.service` (replace `<user>` with the
Linux username and `<workspace>` with `deathpie` or the owning workspace):

```ini
[Unit]
Description=Bridgeipelago Discord bot for Archipelago
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/mnt/d/dev/<workspace>/projects/repos/Awepeeps-bridgeipelago
ExecStart=/home/<user>/.local/share/bridgeipelago/venv/bin/python -u -c "import multiprocessing as m, runpy; m.set_start_method('fork'); runpy.run_path('bridgeipelago.py', run_name='__main__')" config.json
Restart=on-failure
RestartSec=10
StandardOutput=append:/mnt/d/dev/<workspace>/projects/repos/Awepeeps-bridgeipelago/bot.out
StandardError=append:/mnt/d/dev/<workspace>/projects/repos/Awepeeps-bridgeipelago/bot.out

[Install]
WantedBy=default.target
```

The wrapper exists because Python 3.14 defaults the Linux multiprocessing start
method to `forkserver` (previously `fork`); bridgeipelago relies on the Discord
child process inheriting a global lock, so under `forkserver` the bot's command
loop dies with `NameError: name 'ToggleLock' is not defined`. Forcing `fork`
avoids it without patching the bot.

Then:

```bash
systemctl --user daemon-reload
systemctl --user enable --now bridgeipelago
loginctl enable-linger "$USER"   # start on boot without an active login
systemctl --user status bridgeipelago
```

Logs go to `journalctl --user -u bridgeipelago -f` and the appended
`<workspace>/projects/repos/Awepeeps-bridgeipelago/bot.out`. Stop or restart with
`systemctl --user stop|restart bridgeipelago`.

## Docker alternative

Install Docker Desktop with WSL integration and run `docker compose up -d` from
the clone. `docker-compose.yaml` mounts the four data folders; if you change the
data paths in `AdvancedConfig`, update the mounts to match.

## Configuration

Start from this repository's
[bridgeipelago config template](bridgeipelago.config.template.json), which
pre-sets the recommended defaults, or from the `config.json.template` that ships
with the release you clone and apply the same values. The template and the code
have drifted historically, so do not hand-copy keys from the README.

Our session uses `ItemFilterConfig.BotItemFilterLevel` `2` (progression only
in the channel feed), saved in the ignored local `config.json` and provided
as the default in this repository's config template.
Other recommended defaults: `ItemFilterConfig.BotItemSpoilTraps` `false`,
`AdvancedConfig.SnoozeCompletedGames` `true` (suppress item posts to finished recipients),
and `MetaConfig.LanguageFile` `en`.

| Section | Keys to set |
|---------|-------------|
| `DiscordConfig` | `DiscordToken`, `DiscordBroadcastChannel`, `DiscordAlertUserID`, `DiscordDebugChannel` |
| `ArchipelagoConfig` | `ArchipelagoServer` (`wss://archipelago.gg`), `ArchipelagoPort`, `ArchipelagoPassword`, `ArchipelagoBotSlot` (must equal the YAML `name`), `ArchipelagoTrackerURL`, `ArchipelagoServerURL`, `UniqueID` |
| `ItemFilterConfig` | `BotItemSpoilTraps`, `BotItemFilterLevel` |
| `RelayConfig` | AP-to-Discord relay toggles; leave `SendOwnSlotMessages` off for a dedicated slot |
| `DrawbridgeConfig` | `DiscordBridgeEnabled` to relay Discord chat back to the room |
| `MetaConfig` | `FlavorDeathlink`, and `LanguageFile` (see gotcha) |
| `AdvancedConfig` | `QueueOverclock`, `SnoozeCompletedGames`, `SelfHostNoWeb`, and the four data directories |

**LanguageFile gotcha:** the v3.0.x `config.json.template` omits
`MetaConfig.LanguageFile`, but the code reads it, so some messages render as
`LANG_KEY_ERROR`. After copying the template, add the key:

```bash
python3 - <<'PY'
import json
from pathlib import Path
p = Path("config.json")
c = json.loads(p.read_text())
c.setdefault("MetaConfig", {})["LanguageFile"] = "en"
p.write_text(json.dumps(c, indent=4) + "\n")
PY
```

`ArchipelagoServerURL` and `ArchipelagoTrackerURL` must be the real room URLs;
the bot polls room status to follow port changes, and wrong URLs break that.

`DiscordAlertUserID` takes a **user ID**, or `&<role id>` to mention a role:
the bot builds `<@ID>` for users and `<@&ID>` for roles, so the `&` character
must come first for group IDs. Any other value is reported in the bot's error
log and produces no working mention.

## Discord application

1. Discord Developer Portal -> New Application (or reuse an existing bot).
2. Installation -> Installation Contexts: enable `Guild Install`. In
   Default Install Settings (Guild Install):
   - Scopes: `applications.commands` and `bot`
   - Permissions: `View Channels`, `Send Messages`, `Read Message History`,
     `Embed Links`, `Attach Files`
   Save. The `bot` scope is what makes Discord create the bot's managed role.
3. Bot tab: enable `Public Bot` and `Message Content Intent` (bridgeipelago
   reads `$` commands from message content); copy the token.
4. Invite the bot with the install link. Discord creates an
   integration-managed role named after the bot with the selected permissions
   and auto-applies it on every server the bot joins. A managed role cannot be
   edited or assigned manually; the server owner only positions it.
5. Choose a bot channel; enable Developer Mode and copy its channel ID and
   your own user ID. A separate debug channel is optional.

For Awepeeps, set both `DiscordBroadcastChannel` and `DiscordDebugChannel` to
`1561407458973319288` (`#archipelago-notifications`) in the local `config.json`.
All channel-based bot commands, AP notifications, and admin/debug alerts use
that channel; `#archipelago` is reserved for human conversation. Keep credentials
in the ignored local config; the tracked config template leaves channel IDs blank.

To give an already-added bot a managed role, add the `bot` scope to the default
install settings and re-add the bot (kick it, then invite it again). Re-adding
does not change the token.

**Channel permissions:** the bot's managed role needs `View Channel` and
`Send Messages` in every configured channel, plus `Attach Files` for charts.
A staff-only channel
that denies `Send Messages` makes the bot's `on_ready` fail with
`403 Missing Access`, so use a bot-friendly debug channel (for example a
`#bot-commands`) or add a channel overwrite for the managed role.

## Hint result announcements

Set `RelayConfig.HintMessages` to `true` in the bot's local `config.json` to
announce newly revealed hints in the configured broadcast channel, including
hints requested through game clients. Our community template enables this;
the generic bot template defaults to disabled. Restart after changing config.

This relays the actual result: whose item it is, the item name, its location,
whose world contains it, and its hint status. It does not request additional
hints or spend points. A player's `/hint` request through Discord still uses
the normal server hint cost; `/hints` only lists existing hints by DM.

The initial snapshot records existing hints silently, including any hint
revealed before that snapshot arrives. Announced hints are remembered durably
to suppress duplicates across reconnects, restarts, and overlapping
player hint lists. Hints are separate from progression-only item filtering and
finished-player item suppression.

Restarting the bot does not drop pending announcements. Unsent results are
persisted and reloaded on the first chat-loop pass after the Discord process
starts, even before the tracker reconnects. A crash after Discord accepts a
message but before its acknowledgement is saved can cause one repeated
announcement. If the state file cannot be written, the same result can be sent
on later passes until the write succeeds.

Delivery isolates each result, so a bad message cannot block later ones. A
failed send is retried on later passes with exponential backoff: five attempts
in total, waiting 2, 4, 8, and 16 seconds between them. A result that keeps
failing for about 30 seconds moves to a persisted deadletter list. Results
Discord permanently rejects (HTTP 400/403) move there at once. A deadlettered
result is not retried afterwards and does not come back on restart. These retry
limits are fixed in code, not read from `config.json`. Failures are logged as
short summaries without the message payload. Rendered result text is capped at
Discord's 2000-character message limit, literal `@` characters are escaped
before sending, and hint posts suppress Discord mentions: an announced result
never pings anyone.

`APClientHint` and `APClientHintLocation` only echo command text; they are not
needed for result announcements and remain disabled in our template.

`NotificationConfig.HintMessage` overrides the complete hint announcement,
including emojis. Supported placeholders are `{receiver}`, `{item}`,
`{location}`, `{finder}`, `{status}`, and `{entrance}`. The entrance placeholder
is empty when absent, otherwise it includes an ` Entrance: ` prefix. Missing or
blank overrides use a plain built-in message. See the fork's
[hint result reference](https://github.com/Awepeeps/Awepeeps-bridgeipelago/blob/awepeeps-patches/docs/hint-notifications.md)
for the startup baseline, persistence, and duplicate-handling details.

## Daily status reports

The `awepeeps-patches` bot can automatically post the same outputs as
`/checkcount`, then `/checkgraph`, then `/deathcount` in the configured broadcast
channel. Add this
top-level section to the ignored local `config.json` to enable midnight reports:

```json
"DailyPostConfig": {
    "Enabled": true,
    "Time": "00:00",
    "Timezone": "America/New_York"
}
```

Restart the bot after changing these settings. `Time` uses 24-hour `HH:MM`;
`Timezone` is an IANA timezone and follows daylight saving changes. The template
defaults to disabled. Startup waits for the next scheduled time rather than
posting missed reports. If the running computer is suspended across the scheduled
time, it may deliver that report once on resume. Failed reports are logged and
the next scheduled attempt is the following day. The bot records the last
successful report date under the session's
ignored log directory to prevent duplicate daily posts after reconnects or restarts.
The death tally includes observed DeathLink events; the graph uses the existing
web tracker and remains unavailable with `SelfHostNoWeb` enabled.

## Command availability

Our `awepeeps-patches` branch supports independent switches for message and
slash commands. Merge this section into the ignored local `config.json` and
restart the bot:

```json
"CommandConfig": {
    "PrefixCommandsEnabled": true,
    "SlashCommandsEnabled": true
}
```

Both default to `true`. Use JSON booleans, not strings. Setting
`PrefixCommandsEnabled` to `false` disables `$` commands, including message-only
admin commands. Keep it enabled if you need those commands. Setting
`SlashCommandsEnabled` to `false` disables player slash commands and removes
them from the configured server on the next successful command sync. The bot
continues relaying notifications with either or both command styles disabled.

## Opt-in item pings and watches

Our `awepeeps-patches` branch adds item watches and optional pings to the
existing registration and catch-up features. Merge
`"ItemMentionsEnabled": true` into the local `NotificationConfig` section and
restart to permit pings. The tracked templates default to `false`. A global
toggle alone never opts players in.

After registering for their slot, each player chooses one of:

- `/notify mode:all` or `$notify all`: ping for items sent to their registered
  slots, including self-found items when those are posted.
- `/notify mode:watched` or `$notify watched`: ping only for watched items.
- `/notify mode:off` or `$notify off`: stop pings.

Use `/watch slot:deathpie item:Mikiri Counter` or
`$watch deathpie | Mikiri Counter` to watch an item without spending hint
points or revealing its location. `/watches` (`$watches`) lists pending watches;
`/unwatch slot:deathpie item:Mikiri Counter`
(`$unwatch deathpie | Mikiri Counter`) removes one. Use the exact slot and item
names; matching ignores case. The item must exist in that slot's game, and
you must be registered for the slot. A Discord `/hint` or `$hint` request also
adds a watch for the canonical item returned by Archipelago in your registered slot. It does not opt
you into pings, and requesting the hint still has the normal hint cost.
The watch is added from the server's unresolved hint result, so a typo that
Archipelago resolves (such as `Mask Fragement: Left` becoming
`Mask Fragment: Left`) still watches the right item. Declined requests,
requests with no result, and already-found hint results do not add watches.
Automatic watching works with hint-result announcements disabled and only
affects the requester, who must still be registered for the receiving slot.
Hints requested in game clients do not create a personal watch; use `/watch`
for those.

Pending watches from registered players override the configured progression
filter: a watched filler item is posted even in a progression-only channel.
This also works for players with notifications off, but never opts them into
pings. Unwatched items retain the channel filter. Pure-trap spoiler settings
and finished-player suppression still apply; an arrival hidden by those
settings completes its watch without a post or ping. Pings attach to the
existing item post instead of creating a second notification.

Watches mean the next observed matching copy, not an item quantity or a search
of previously received items. Preferences persist per Discord user ID and
session `UniqueID`. Multiple registrants of one slot have independent choices.
Clearing registrations also removes consent and watches. Hint announcements
and chat relays continue to suppress mentions; item pings only allow the
specific consenting users and never enable role or everyone mentions.

See the fork's [item pings and watches reference](https://github.com/Awepeeps/Awepeeps-bridgeipelago/blob/awepeeps-patches/docs/item-watches.md)
for delivery and storage details.

## Registration and commands

Commands only work in the broadcast channel (`#archipelago-notifications` for
Awepeeps); the bot ignores messages everywhere else, including a separate debug
channel if one is configured. Commands are
case-sensitive and lowercase. `$register` links your Discord account to a slot; the other
player commands act on your registered slot(s). Upstream reference:
[bridgeipelago commands](https://github.com/Quasky/bridgeipelago#commands).

Registration is a subscription, not ownership: more than one Discord account
can register the same slot. Registrations are tracked per Discord account while
item notifications queue in one shared per-slot list. `$ketchmeup` keeps a
saved per-account position in that list (one cursor file per Discord account
in the bot's registration data), so catching up only sends each account the
items it has not received yet: one registrant's catch-up no longer consumes
another registrant's pending items, and repeated `$ketchmeup` requests only
send items added since that account's last catch-up. `$groupcheck` still shows
the slot's full stored queue regardless of any account's position.

For a slot with no saved position, the first catch-up after registering starts
at the queue's length when the account registered, so older history is not
replayed. Accounts registered before this change have no saved position, so
their first catch-up sends everything still in that slot's queue file.
`$clearreg` removes the registration list but keeps saved positions, so
registering the same slot again resumes where that account left off. Catch-up
does not delete queue files, so they keep growing, and `$groupcheck` sends the
whole file each time.

Two `` requests sent at the same moment by one account run one after
the other, so items are not sent twice. A bare `` (or `/register`
with a blank slot) replies with usage instead of registering anything. Slot
names with characters Windows does not allow in file names (such as `:`) or
device names such as `CON` now register normally; the bot stores their queue
under an encoded file name.

A Discord hint request now also gets a public acknowledgement in the broadcast
channel naming the requester, the slot, and the item (for example
`Player A requested a hint for Slot B: Item Name`), including for
`/hint`. Requests remain auditable next to their announced results, and
Discord mentions are suppressed in that acknowledgement. The slot and item
names are each limited to 100 characters. A hint spends the slot's own hint
points, so `$hint` and `/hint` only accept a slot the requester has
registered for with `$register`; server admins can request any slot. A bare
`$hint` replies with the usage.

The `awepeeps-patches` bot also registers the player commands as native Discord
slash commands in the server containing the configured broadcast channel. Type
`/` and select Shamiko-Bot to browse them. The existing `$` commands continue to
work. Slash commands enforce the same broadcast channel restriction; confirmations
and `/help` are private, catch-up and registration lists arrive by DM, and charts
and requested hints are posted in the broadcast channel.

Use `/register slot:<exact slot name>`, `/groupcheck slot:<exact slot name>`,
and `/hint slot:<exact slot name> item:<item name>` for commands with arguments.
`/ketchmeup` has an optional filter with Everything (default), Useful and
progression, and Progression only choices. The other player command names match
the `$` versions below. Admin and configuration commands remain message-only.

The bot determines the server ID from the broadcast channel and syncs its player
command list once after connecting. It requires application-command authorization
and members need permission to use application commands in that channel. No new
bot token, public web endpoint, or room generation is needed.

Player commands (`$` syntax; slash equivalents are available in Discord):

| Command | Effect |
|---------|--------|
| `$help` | Post this list of player commands in the channel |
| `$register <slot>` | Link your Discord account to an Archipelago slot |
| `$listreg` | DM the slots you are registered for |
| `$clearreg` | Remove all of your registrations |
| `$ketchmeup <2\|1\|0>` | DM checks you missed: `2` progression, `1` +useful, `0` +normal |
| `$groupcheck <slot>` | DM all queued checks for a slot (group games) |
| `$hints` | DM hinted items for your registered slots |
| `$hint <slot> \| <item>` | Request a hint for a slot you're registered to; the result is relayed to the channel |
| `$deathcount` | Post the current DeathLink tally |
| `$checkcount` | Post the current check counts |
| `$checkgraph` | Post a check-progress graph image |

Bot maintenance commands (these affect the bot, not the Archipelago room).
For room administration, see the [Admin guide](admin-guide.md). Upstream describes
these commands as admin-only. This Awepeeps bot enforces that as listed below:

| Command | Effect |
|---------|--------|
| `$hello`, `$iloveyou` | Trivial responses; not gated |
| `$reloadtracker`, `$reloaddiscord` | Reload the tracker or the Discord client (admin only) |
| `$setconfig <key> <value>` | Change a `config.json` value (`ArchipelagoPort`, `ArchipelagoPassword`, URLs, `UniqueID`). Admin only |
| `$archinfo` | Debug details (admin only, and only when `DebugMode` is on; secret-named values print as `<redacted>`) |

Admin means a server member with **Administrator** or **Manage Server**
permission. The bot reads that from Discord, not from the message text, and
other members get a refusal. `$setconfig` never echoes a password, token, or
secret back to the channel. If the room password was ever typed in the
channel, rotate it on the room. `UniqueID` values containing path separators or
control characters are rejected. Bot commands are only read in the broadcast
channel.

## Notifications

The `awepeeps-patches` bot suppresses the "Bot connected. Debug control - Online."
message by default, including when `DiscordConfig.AnnounceConnection` is absent.
Discord can fire `on_ready` again after reconnecting, which previously posted
the same message each time. Set `AnnounceConnection` to `true` only to restore
that behavior; this is an on/off setting, not a daily limit. Restart the bot
after changing it. Other debug messages, errors, and room-port alerts keep
their existing behavior.

A WebSocket disconnect does not prove the room is asleep. Brief reconnects stay
quiet. After a going-away close followed by at least 60 seconds of refused
reconnects, the bot posts one connection-unavailable notice and a matching
restored notice after reconnection. The room link stays wrapped in angle
brackets so Discord does not fetch a preview that could wake the room.

Both notices can be customized independently in the local `config.json`,
including their emojis:

```json
"NotificationConfig": {
    "ConnectionUnavailableMessage": "💤 The Archipelago room may be asleep. Open {room_url} to wake it up.",
    "ConnectionRestoredMessage": "☀️ The Archipelago room is reachable again at **{server_address}**.",
    "SleepWakeEditWindowMinutes": 15
}
```

If the room is reachable again within `SleepWakeEditWindowMinutes` (default
15) of the unavailable notice, the bot edits that notice into the restored
message instead of posting a second one. Set it to `0` to always post a new
message.

`{room_url}` inserts the current room link with preview-suppressing angle
brackets already included. `{server_address}` inserts the current host and port.
The bot's built-in fallback text is basic and has no emojis; missing, blank,
or invalid overrides use that fallback. Restart the bot after editing config.
The emoji prefixes in shipped templates are examples; the built-in fallbacks
are plain text without emojis.

The room-status poll behind the port-change announcements is also debounced.
The poll runs once per minute on a timer, and its HTTP request runs off
Discord's event loop with a 10-second timeout. Every response is validated:
the HTTP status is checked and `last_port` must be an integer from 1 to 65535.
A bad response never updates the port; it counts as a failed check. One
debug-channel alert goes out after 5 consecutive failed checks (with the alert
user mention from `DiscordAlertUserID`, when set); repeat failures stay quiet.
After an alert has gone out, the next valid check posts a recovery notice. Every
valid check clears the failure count.

Item flags and bot filter levels are different numbers. Server item flags are
`0` filler, `1` progression, `2` useful, and `4` trap; they can combine, such as
`3` for progression + useful. Our filter **level** `2` accepts items with the
progression bit set, not items whose flag equals `2`. Pure traps (`4`) are
disabled by our `BotItemSpoilTraps: false` setting. These preferences are saved
in the ignored local `config.json` and survive restarts; the community template
provides the same defaults. For combined flags, trap handling, and the Spirit
Light example, see the fork's
[item notification reference](https://github.com/Awepeeps/Awepeeps-bridgeipelago/blob/awepeeps-patches/docs/item-notifications.md).

There are two separate paths with separate filters:

- **Channel feed (not per-user, not opt-in).** Item events matching the configured
  filter, plus items explicitly watched by a registered player, are posted to
  the broadcast channel. The host sets the level in `config.json`
  with `ItemFilterConfig.BotItemFilterLevel`: `2` progression only, `1`
  progression + useful, `0` progression + useful + normal (traps only when
  `BotItemSpoilTraps` is true). `AdvancedConfig.SnoozeCompletedGames` skips
  posts to recipients who have already finished, regardless of the sender's
  completion status. Players cannot change this host setting.
- **Personal DMs (opt-in).** `$register <slot>` links a Discord account to a
  slot and starts queuing items **other players send to you**; your own finds
  are not queued (you see those in-game). Pull them with `$ketchmeup <2|1|0>`,
  which chooses the level per request. `$hints` DMs hinted items and
  `$groupcheck <slot>` DMs all queued items for a slot. There is no automatic
  push DM.
- **Room port changes.** When archipelago.gg restarts a paused room on a new
  port, the bot updates its own `config.json`, reports it in the debug channel,
  and (via the `awepeeps-patches` branch) posts the new address in the
  broadcast channel so players know where to reconnect.

The bot identifies players by slot, so a second game on the same account is
treated as someone else's items. Upstream: [bridgeipelago functionality](https://github.com/Quasky/bridgeipelago#functionality).

## DeathLink

DeathLink is a per-game Archipelago option. Only games with it enabled send and
receive deaths; the bot is a passive spectator that receives every DeathLink
broadcast (it never sends one).

When one arrives, and `RelayConfig.DeathlinkMessages` is true, the bot posts to
the broadcast channel:

> **Deathlink!** Received from **&lt;player&gt;**
> *Cause:* &lt;cause&gt;

`MetaConfig.FlavorDeathlink` replaces the "Received from" line with random flavor
from the project's `modules/DeathlinkFlavor.py`. Every received death is also
appended to `logs/<UniqueID>/DeathLog.txt`, which backs `$deathcount` and
`$deathgraph`. `DeathlinkLottery` is unused.

## Room or port changes

Use `$setconfig <key> <value>` (admin only) for `ArchipelagoPort`,
`ArchipelagoTrackerURL`, `ArchipelagoServerURL`, and `UniqueID`, then
`$reloadtracker` and `$reloaddiscord`. Bring the room up first so the bot can
connect during the reload.

## Verify

- `python scripts/validate_repo.py` passes with the bot input in place.
- `python scripts/generate_session.py --season <season> --archipelago <install> --dry-run`
  lists the bot slot among the players (preflight only).
- The bot connects and posts a real check to the broadcast channel.

## Troubleshooting

- **The bot connects and posts its startup message but never relays checks,
  chat, or DeathLink.** The unpinned `websockets` dependency resolved to 16+;
  bridgeipelago v3.0.0 calls `websockets.connect()` without a context manager,
  which newer versions no longer support. Install `websockets<14` in the venv
  (13.1 is verified) and restart.
- **The bot reconnects every ~12 s and never posts checks.** The log repeats
  `Unknown error in CheckDatapackage, returning False` and `DataPackage is
  invalid, requesting new one`, and `ErrorLog` shows
  `Error reading or validating datapackage: '<game>'`. v3.0.0 sends a bare
  `GetDataPackage`, which the current archipelago.gg server answers with an
  empty games dict, so `CheckDatapackage` fails and the bot loops. Upgrade to
  `live-v3.0.1`, which requests the room's game list explicitly.
- **`NameError: name 'ToggleLock' is not defined`.** Python 3.14 changed the
  Linux default multiprocessing start method to `forkserver`, so the Discord
  child process no longer inherits the global lock; the command loop dies the
  first time a port rescan is requested, which also breaks `$reloaddiscord`,
  `CycleDiscord`, and the port-change hand-off. Launch the bot with the `fork`
  wrapper (see Run as a WSL service), or build the venv with Python 3.12/3.13.

## Trust

bridgeipelago is a third-party application and has no license. Review the
release and source before running it, and never place its credentials in this
repository.
