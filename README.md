# Awepeeps Archipelago

This repository organizes Archipelago multiworld game configurations, setups, and documentation for the Awepeeps community sessions.

## Repository Structure

- **Seasons**: Organized by year and season (e.g., `2026/1. Spring/`)
  - `README.md`: Alphabetical list of games with embedded links to info, setup guides, APWorld releases, and PopTracker packs
  - `YAML/`: Player-specific YAML configuration files (named as `playername_gamename_v1.yaml`)
  - `APWorld/`: Archipelago world files (if applicable)
  - Other session-related files

## Usage

- Refer to each season's README for game-specific setup instructions and links
- YAML files contain player configurations for Archipelago generations
- Follow the guidelines in `.instructions.md` for maintaining consistency

## Contributing

- Maintain season READMEs according to the process outlined in `.instructions.md`
- Do not commit `.admin` folders or `.generated-secrets-hidden` files (these are gitignored)
- All changes should be reviewed before committing

## Notes

- This repo is for community use and may contain spoilers or session-specific data
- Ensure YAML files are versioned appropriately (e.g., `_v1.yaml`)
