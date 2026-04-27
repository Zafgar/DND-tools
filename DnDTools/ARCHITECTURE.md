# DnDTools — Architecture overview

This document explains how the data layers fit together so the DM
can navigate the codebase. The biggest source of confusion is the
*two* map systems that historically lived side-by-side. They now
talk to each other through `data/campaign_map_sync.py`, but the
underlying split still exists.

```
┌──────────────────────────────────────────────────────────────────┐
│  Campaign  (data/campaign.py — Campaign dataclass)               │
│                                                                  │
│   ├─ party (PartyMember[])              ← active heroes          │
│   ├─ areas (CampaignArea[])             ← named lore locations   │
│   ├─ encounters (CampaignEncounter[])   ← pre-built fights       │
│   ├─ notes (CampaignNote[])             ← session journal        │
│   │                                                              │
│   ├─ world_data: dict                                            │
│   │    └─→ World (data/world.py)                                 │
│   │           ├─ locations: {id → Location}   ← OLD text DB:     │
│   │           ├─ npcs:      {id → NPC}        ←   cities, shops, │
│   │           ├─ quests:    {id → Quest}      ←   NPCs as data.  │
│   │           ├─ map_pins   (legacy)                             │
│   │           ├─ map_tokens (legacy)                             │
│   │           └─ map_image_path (legacy single-image map)        │
│   │                                                              │
│   └─ primary_world_map_id: str                                   │
│        └─→ WorldMap (data/map_engine.py — files in saves/maps/)  │
│              ├─ background_image  (full-resolution JPG)          │
│              ├─ scale_miles_per_pct                              │
│              ├─ travel_speed_miles_per_day                       │
│              ├─ layers (MapLayer[]):                             │
│              │    └─ objects (MapObject[])                       │
│              │         ├─ object_type (city/town/info_pin/…)     │
│              │         ├─ x, y in world %                        │
│              │         ├─ linked_location_id  ← BRIDGE TO World  │
│              │         ├─ actor_id           ← BRIDGE TO Actor   │
│              │         └─ passenger_actor_ids (vehicles)         │
│              └─ annotations (AnnotationPath[]) — roads / routes  │
│                   ├─ points (drawn polyline) OR                  │
│                   ├─ waypoint_object_ids — chain of MapObjects   │
│                   │   that the polyline auto-rebuilds through    │
│                   ├─ opacity (so a JPG road can show through)    │
│                   └─ path_type (route/road/sea_route/air_route)  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  ActorRegistry  (data/actors.py — saves/actors.json)             │
│                                                                  │
│   The shared identity layer. Heroes, NPCs, vehicles all live     │
│   here once. Map tokens (`MapObject.actor_id`) and battle        │
│   entities (`Entity.actor_id`) point at the same Actor so the    │
│   DM clicks any token in any view and gets the same name +       │
│   portrait + notes.                                              │
└──────────────────────────────────────────────────────────────────┘
```

## How the views talk to each other

| View                         | Source of truth                  |
|------------------------------|----------------------------------|
| Campaign manager (lists)     | `Campaign.world.locations` etc.  |
| Interactive world map        | `WorldMap` (`primary_world_map_id`) |
| Town view (drill-down)       | A child `WorldMap` referenced from a settlement MapObject |
| Tactical battle              | `BattleSystem` populated from a scenario or roster |
| Token identity in every view | `ActorRegistry` (singleton)      |

### The bridge (`data/campaign_map_sync.py`)

Use these helpers whenever you create or edit a settlement:

* `sync_location_to_map(world, world_map, location_id)` —
  *creates* a MapObject for a campaign Location if one isn't
  already on the world map. Updates the label/notes/tags but
  preserves the user's chosen position.
* `sync_map_object_to_location(world, world_map, obj_id)` —
  reverse direction: when the DM draws a town directly on the
  map, this materialises a campaign Location for it.
* `available_unplaced_locations(world, world_map)` — feeds the
  "drag onto map" palette so settlements created in the
  campaign manager appear there immediately.
* `unlink_location` and `remove_map_objects_for_location` —
  decouple or delete the token alongside a location.

### Path waypoints (`data/path_waypoints.py`)

Routes between settlements are built by listing
`waypoint_object_ids` rather than free-drawing every point:

* `make_path_between(world_map, "A", "B", "C")` — string
  settlements together; the polyline auto-fills with their
  positions.
* `add_waypoint(...)`, `insert_waypoint_between(...)` — extend
  an existing route through a new town. `insert_waypoint_between`
  picks the segment with the smallest detour automatically.
* `on_object_moved(world_map, obj_id)` — call from the editor
  after dragging a settlement to update every path that threads
  through it.
* `on_object_deleted(world_map, obj_id)` — auto-scrubs deleted
  settlements from paths and removes paths that lose a required
  endpoint.

## Travel pace + ship + flight (already wired)

* `data/travel_pace.py` — PHB pace tables, forced-march DC,
  long rest, exhaustion 0..6.
* `data/ships.py` — 7 hull types with passenger / cargo /
  fares, `cheapest_ship` / `fastest_ship` pickers,
  sea-route validator.
* `data/map_travel.py` — `flight_distance_miles`,
  `advance_followers_events` (per-token movement + waypoint
  pass-through detection + arrival flag).

## Combat

* `engine/battle.py` — BattleSystem owns terrain, entities,
  ceiling, weather, JPG background.
* `engine/ai/tactical_ai.py` — full turn planner. Currently
  knows: shove-to-hazard, 3D LOS, aquatic awareness, doors,
  cover, healing, summon plumbing (Spiritual Weapon, Find
  Familiar with Help action), Wild Shape (Moon + plain druid).
* `states/scenarios.py` ↔ user-saved scenario palette
  (`save_user_scenario`).
* `states/battle_vfx.py` + `states/character_art.py` +
  `states/terrain_art.py` — code-drawn art (no spritesheets).

## Save layout

```
saves/
  ├─ actors.json                       Shared ActorRegistry
  ├─ map_backgrounds/                  Imported JPG/PNG references
  ├─ maps/                             WorldMap files (one per JSON)
  └─ user_scenarios/                   Battle scenarios saved by DM
campaigns/
  └─ Novus Somnium.json                Default starter campaign
```

## What is NOT yet bridged (known follow-ups)

* The campaign manager UI doesn't yet show a "drag-onto-map"
  palette — the data helper exists
  (`available_unplaced_locations`) but hooking it into the
  pygame sidebar is a separate UI phase.
* `World.npcs` (campaign NPCs) ↔ `ActorRegistry` doesn't sync
  automatically. NPCs created in the campaign manager need a
  one-time `actor_id` link.
* Town view (`MapObject.linked_map_id`) drill-down works but
  has no template that mirrors a town's NPC list as tokens.
