# Fall 2026 Games

> See main Archipelago resources: [Archipelago Resources](../../Archipelago.md)

## Session Links

- **Google Sheet**: [https://docs.google.com/spreadsheets/d/1IlNYQDSLKqZUsS2J3TWNT6ruRYM5FtXTUhhjQ3Qtxc4/edit?usp=sharing](https://docs.google.com/spreadsheets/d/1IlNYQDSLKqZUsS2J3TWNT6ruRYM5FtXTUhhjQ3Qtxc4/edit?usp=sharing)
- **Archipelago Room**: [Link TBD](https://archipelago.gg/room/)
- **YAML Configurations**: [YAML/](YAML/)
- **APWorld Files**: [APWorld/](APWorld/) ([Sekiro](APWorld/sekiro.apworld), [Pokemon Crystal](APWorld/pokemon_crystal.apworld), [Ori WotW](APWorld/ori_wotw.apworld))
- **Secrets and Spoilers**: [.secrets/](.secrets/)

## Run Dates

- **Start:** October 17, 2026 — 7:00 PM Eastern

## Players & Games

| Player | Game |
|--------|------|
| deathpie | Sekiro: Shadows Die Twice |
| kriegsdorff | Pokemon Crystal |
| Jack Whitman | Super Mario 64 |
| propernoun | Ori and the Will of the Wisps |
| chickensalad | TBD |

| Game | Info | Setup Guide | YAML | Release | Software | PopTracker | Misc. |
|------|------|-------------|------|---------|----------|------------|-------|
| Sekiro: Shadows Die Twice | [Info](https://github.com/yenix4/ArchipelagoSekiro/blob/main/worlds/sekiro/docs/en_Sekiro%20Shadows%20Die%20Twice.md) | [Setup Guide](https://github.com/yenix4/ArchipelagoSekiro/blob/main/worlds/sekiro/docs/setup_en.md) | [YAML](YAML/deathpie_Sekiro_v1.yaml) | [Release](https://github.com/yenix4/ArchipelagoSekiro/releases) | [Sekiro AP Client](https://github.com/antonovanton000/SekiroArchipelagoClient/releases) | [PopTracker](https://github.com/vonTungsten/Sekiro-Poptracker/releases) (early/incomplete) | Enemy randomizer uses [thefifthmatt's Sekiro randomizer](https://www.nexusmods.com/sekiro/mods/543); consider disabling for large multiworlds |
| Pokemon Crystal | [Info](https://github.com/gerbiljames/Archipelago-Crystal/blob/pokecrystal/worlds/pokemon_crystal/docs/en_Pokemon%20Crystal.md) | [Setup Guide](https://multiworld.gg/tutorial/Pokemon%20Crystal/setup_en) | [YAML](YAML/kriegsdorff_Pokemon-Crystal_v1.yaml) | [Release](https://github.com/gerbiljames/Archipelago-Crystal/releases/latest) | [BizHawk 2.9/2.10](https://tasvideos.org/BizHawk/ReleaseHistory) or [mGBA 0.10.3+](https://mgba.io/) | [PopTracker Pack](https://github.com/palex00/crystal-ap-tracker/releases/latest) | [Web client](https://gerbiljames.github.io/crystal-ap-web/) (generate YAMLs / play in-browser) |
| Super Mario 64 | [Info](https://archipelago.gg/games/Super%20Mario%2064/info/en) | [Setup Guide](https://archipelago.gg/tutorial/Super%20Mario%2064/setup_en) | [YAML](YAML/Jack%20Whitman_Super-Mario-64_v0.yaml) | - | [SM64AP-Launcher](https://github.com/N00byKing/SM64AP-Launcher/releases) | - | Archipelago `sm64ex` decomp/PC build required |
| Ori and the Will of the Wisps | [Info](https://github.com/Satisha10/APwotw_release) | [Setup Guide](https://github.com/Satisha10/APwotw_release#setup-guide) | [YAML](YAML/propernoun_Ori-and-the-Will-of-the-Wisps_v1.yaml) | [Release](https://github.com/Satisha10/APwotw_release/releases) | [WotW Randomizer](https://wotw.orirando.com/) | - | [Wiki](https://wiki.orirando.com/) |
| TBD (ChickenSalad) | - | - | - | - | - | - | Game not yet chosen |

## Notes

- Fall session generation plans to use a new test session based on updated player-provided info before the official start date.
- Super Mario 64 uses the Archipelago `sm64ex` decomp/PC build, not an emulator. Build it with [SM64AP-Launcher](https://github.com/N00byKing/SM64AP-Launcher/releases) or the manual process in the [setup guide](https://archipelago.gg/tutorial/Super%20Mario%2064/setup_en). The YAML controls the generated multiworld; compile-time build options are configured separately before building. This YAML leaves move randomization disabled, so it does not require a special move-randomizer build.
- For online play, launch the built executable with `--sm64ap_name "Jack Whitman" --sm64ap_ip archipelago.gg:PORT`. A uniquely named build is normal for a custom configuration; an `.apsm64ex` patch file is for offline play and is not needed for the hosted-room flow.
- Super Mario 64's Archipelago integration is provided by the Archipelago `sm64ex` build, so no separate Fall APWorld file is needed for it.
- The Fall APWorld directory contains the supplied Sekiro, Pokemon Crystal, and Ori and the Will of the Wisps world archives used by the corresponding YAMLs.
- ROMs are not provided or linked in this repository; see [Archipelago.md](../../Archipelago.md) for policy.
