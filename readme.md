# Tyrant Unleashed – Card Browser

A fan-made card browser for the mobile card game **Tyrant Unleashed**, built with Electron (desktop) and available as a web app via GitHub Pages.

## 🌐 Web Version

**[Open in Browser](https://isilrond.github.io/tucardbrowser/)**

No installation required. Works directly in your browser.

## 💾 Desktop Version (Portable)

A portable Windows `.exe` is available for download – no installation needed, just run it.

**[Download latest portable version](https://drive.google.com/file/d/1QHPu3qq1d2vBp-Qh2opm3bSZd8Eom_L4/view?usp=drive_link)**

Built with [Electron](https://www.electronjs.org/).

## Features

- Browse all **9,100+ cards** from the game
- Filter by **Faction**, **Rarity**, **Cost**, **Fusion level**, **Type**, **Set** and **Skills**
- Sort by **Name**, **ID**, **Faction**, **Rarity**, **Cost**, **Fusion** or **Type**
- Detailed card view with stats per level, skills, fusion info and summoned units
- Responsive grid layout

## Updating Card Data

Card data is stored in `tu_data.json`. To update it with the latest game data:

1. Run `update_data.py` (requires Python 3, no additional packages)
2. The script downloads all card XMLs from the game server into the `XMLS/` folder
3. A new `tu_data.json` is generated automatically
4. Replace the existing `tu_data.json` in the repository and push

```bash
python update_data.py
```

## Special Thanks

Special thanks to **MarshalKylen** – one of the original developers who, years after Synapse Games stopped actively maintaining the game, still stays in contact with the community. Your dedication means a lot.

## Disclaimer

This is an unofficial fan project. Tyrant Unleashed and all related assets are property of Kongregate and its developer studio Synapse Games.
