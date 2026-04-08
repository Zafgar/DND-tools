# D&D 5e AI Encounter Manager

A comprehensive D&D 5e (2014) tactical combat simulator and campaign management tool built with Pygame.

## Features

- **AI-Driven Combat** -- Monte Carlo simulation-based tactical AI that handles targeting, positioning, spell selection, and class-specific mechanics (Rage, Sneak Attack, Divine Smite, etc.)
- **Full D&D 5e Rules Engine** -- Grapple, shove, cover, advantage/disadvantage, concentration, legendary resistance, exhaustion, death saves, and more
- **Tactical Grid Map** -- 60+ terrain types with line-of-sight, elevation, cover, and difficult terrain calculations. A* pathfinding for AI movement
- **Hero Creator** -- Point buy, 12 classes, 7+ races, spell and equipment selection
- **Campaign Manager** -- Long-term campaign tracking with party management, NPCs, areas, encounters, shops, and inns
- **Combat Roster** -- Quick multi-team encounter setup with drag-and-drop
- **Battle Reports** -- Post-combat analysis with MVP, damage/healing stats, resource usage
- **DM Advisor** -- AI evaluates player actions and suggests optimal moves
- **TaleSpire Integration** -- REST API (Flask) for syncing miniature positions with TaleSpire

## Requirements

- Python 3.10+
- Pygame 2.5+
- Flask 3.0+

## Installation

```bash
git clone https://github.com/zafgar/dnd-tools.git
cd dnd-tools
pip install -r requirements.txt
```

## Usage

```bash
python DnDTools/main.py
```

The application opens a 1920x1080 Pygame window. From the main menu you can:

1. **New Encounter** -- Set up a battle with heroes and monsters
2. **Hero Creator** -- Build custom D&D 5e characters
3. **Combat Roster** -- Quick team-based encounter setup
4. **Campaign** -- Manage long-running campaigns

### TaleSpire Integration

The app starts a Flask server on port 5000. Send miniature position updates via:

```bash
curl -X POST http://localhost:5000/update_minis \
  -H "Content-Type: application/json" \
  -d '{"minis": [{"name": "Goblin", "x": 5, "y": 3}]}'
```

## Project Structure

```
DnDTools/
  main.py              # Entry point, GameManager, Flask server
  settings.py          # Screen config, color palette, constants
  engine/              # Core game logic
    ai/                # Tactical AI (targeting, movement, spells, attacks)
    battle/            # Combat system (turns, conditions, terrain, saves)
    dice.py            # Dice rolling and parsing
    entities.py        # Entity state (HP, conditions, resources)
    rules.py           # D&D 5e rules reference
    terrain.py         # Terrain types and line-of-sight
    win_probability.py # Encounter difficulty estimation
    battle_report.py   # Post-combat report generation
    battle_stats.py    # Combat event tracking
    dm_advisor.py      # DM suggestion engine
    campaign_bridge.py # Battle-to-campaign sync
  data/                # Game data and models
    models.py          # Data structures (CreatureStats, SpellInfo, etc.)
    heroes.py          # Pre-built level 10 heroes
    monsters/          # Monster library by CR
    spells.py          # Spell definitions
    equipment.py       # Weapons, armor, magic items
    class_features.py  # Class feature definitions
    conditions.py      # D&D 5e conditions
    feats.py           # Feat definitions
    racial_traits.py   # Racial trait definitions
    campaign.py        # Campaign data structures
    world.py           # World building (NPCs, locations, shops)
    encounters.py      # Encounter difficulty tables
    library.py         # Monster library loader
  states/              # UI states (screens)
    menu_state.py      # Main menu
    encounter_setup.py # Encounter setup screen
    battle_state.py    # Battle UI with drag-and-drop
    battle_renderer.py # Grid and token rendering
    battle_events.py   # Battle event handling
    hero_creator.py    # Character creation screen
    combat_roster.py   # Team-based roster setup
    campaign_manager.py# Campaign management screen
  ui/                  # Reusable UI components
    components.py      # Button, Panel, HPBar, TabBar, Tooltip
  tests/               # Unit tests
```

## License

This project is for personal use.
