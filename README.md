# WORKY — Burger Economy Simulator 🍔

A 2D pixel idle game where you manage a burger production business, hire workers, upgrade systems, and earn coins.

## How to Run

### 1. Install Python 3.10+

Make sure Python is installed and available in your PATH.

### 2. Install dependencies

```bash
cd workygame
pip install -r requirements.txt
```

### 3. Launch the game

```bash
python main.py
```

## Controls

| Action          | How                          |
|-----------------|------------------------------|
| Hire Worker     | Click **Hire Worker** button  |
| Upgrade Worker  | Click **Up** next to a worker |
| Buy Upgrade     | Switch to **Upgrades** tab    |
| Prestige        | Click **PRESTIGE** at bottom  |
| Quit            | Close the window              |

## Game Mechanics

- **Workers** generate income based on speed × efficiency
- **Upgrades** boost production, sales, or reduce costs
- **Super Burgers** are random events that temporarily multiply income (Rare ×5, Epic ×20, Legendary ×100)
- **Prestige** resets progress but gives a permanent income multiplier

## Architecture

```
main.py          — Game loop & system orchestration
player.py        — Player state (coins, workers, prestige)
worker.py        — Worker entity, hiring, rarity system
economy.py       — Production engine, event system
upgrades.py      — Upgrade definitions & effects
ui.py            — Pygame rendering & input handling
save_system.py   — JSON save/load with auto-save
```

## Save System

- Auto-saves every 10 seconds
- Saves on exit
- Save file: `worky_save.json`
- Delete the save file to start fresh

## Future Integration Points

- **Seasonal Events**: `economy.py` event system is extensible
- **Leaderboard**: `player.total_income` and `prestige_level` are tracked
- **Token Economy**: `player.coins` can map to token balances
