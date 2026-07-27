"""
BattleSystem – manages combat state, turn order, grid positions, terrain.
The TacticalAI (engine/ai.py) computes what NPCs should do.
Includes BattleStatisticsTracker, DMAdvisor, and WinProbabilityCalculator.
"""
import json
import math
import os
import copy
import random
from typing import List, Optional, Callable
from engine.entities import Entity
from engine.ai import TacticalAI, TurnPlan, ActionStep
from engine.terrain import TerrainObject, get_elevation_at, check_los_blocked, calculate_fall_damage
from engine.dice import roll_dice
from engine.battle_stats import BattleStatisticsTracker
from engine.dm_advisor import DMAdvisor
from engine.win_probability import WinProbabilityCalculator
from data.models import CreatureStats


# Terrain that bites while you walk through it rather than at the start
# of a turn (PHB: "for every 5 feet it moves through the area").
_PER_5FT_TERRAIN = {"spike_growth", "wall_thorns", "wall_fire"}
# Terrain that bites the moment you set foot in it, and again each turn.
_ON_ENTER_TERRAIN = {"black_tentacles", "web", "entangle", "sleet_storm",
                     "moonbeam"}
# Terrain that only harms creatures other than its caster.
_SPARES_CASTER = {"spirit_guardians", "moonbeam"}


def _spell_terrain_rules(spell, caster) -> dict:
    """Carry a spell's saving throw, condition and timing onto its tiles.

    ``spawn_spell_terrain`` used to keep only the colour and the damage
    dice, so every area spell landed as a flat damage carpet with no
    save and no condition: Web restrained nobody and Cloudkill allowed
    no Constitution save.
    """
    terrain_type = getattr(spell, "creates_terrain", "") or ""
    if terrain_type in _PER_5FT_TERRAIN:
        trigger = "per_5ft"
    elif terrain_type in _ON_ENTER_TERRAIN:
        trigger = "enter"
    else:
        trigger = "turn_start"
    exempt = []
    if terrain_type in _SPARES_CASTER and caster is not None:
        exempt.append(caster.name)
    dc = 0
    if getattr(spell, "save_ability", ""):
        dc = getattr(spell, "save_dc_fixed", 0) or 0
        if not dc and caster is not None:
            dc = getattr(caster.stats, "spell_save_dc", 0) or 0
    return {
        "save_dc": int(dc),
        "save_ability": getattr(spell, "save_ability", "") or "",
        "applies_condition": getattr(spell, "applies_condition", "") or "",
        "half_on_save": bool(getattr(spell, "half_on_save", True)),
        "trigger": trigger,
        "exempt": exempt,
    }


class BattleSystem:
    def __init__(self, log_callback: Callable[[str], None], initial_entities: List[Entity] = None):
        self.grid_size = 60             # pixels per square
        self.entities: List[Entity] = initial_entities or []
        self.turn_index = 0
        self.current_plane = "Material Plane"
        self.log = log_callback
        self.round = 1
        self.combat_started = False
        self.ai = TacticalAI()
        self.terrain: List[TerrainObject] = []
        self.weather = "Clear"  # Clear, Rain, Fog, Ash

        # Optional JPG/PNG background image painted beneath the terrain
        # (so imported real-world battle maps can provide art while the
        # DM still paints walls/hazards on top for the AI to read).
        self.background_image_path: str = ""
        self.background_alpha: int = 200            # 0-255
        self.background_world_cells_w: int = 40     # image width in grid cells
        self.background_world_cells_h: int = 40     # image height in grid cells
        self.background_offset_x: int = 0           # world px offset
        self.background_offset_y: int = 0           # world px offset

        # Procedural floor style painted under the grid when there is no
        # background image. Premade maps set this so a dungeon reads as
        # flagstone and a forest reads as grass instead of every map
        # sharing the same flat dark fill. See states/battle_floor.py.
        self.floor_style: str = "stone"

        # Global ceiling (feet). 0 = outdoor (no ceiling); a positive
        # value caps how high flying creatures may go. Used to model
        # indoor encounters (10ft corridor, 15ft cave, etc.).
        self.ceiling_ft: int = 0

        # Pending OA reactions: list of (reactor, mover)
        self.pending_reactions: List[tuple] = []

        # Legendary action queue: entities that may still act this round
        self.legendary_queue: List[Entity] = []

        # Lair activation: set True from encounter setup if combat takes place in a lair
        # Lair actions only happen when this is True (PHB/MM: lair actions are NOT available
        # outside the creature's lair)
        self.lair_enabled: bool = False

        # Battle analytics
        self.stats_tracker = BattleStatisticsTracker()
        self.dm_advisor = DMAdvisor()
        self.win_calculator = WinProbabilityCalculator()

        # Track last damage source for kill attribution
        self._last_damage_source: str = ""

        if not self.entities:
            self._init_demo_entities()

    # ------------------------------------------------------------------ #
    # Setup                                                                #
    # ------------------------------------------------------------------ #

    def start_combat(self, surprise_side: str = ""):
        """Start combat. surprise_side: 'players' if players surprise enemies,
        'enemies' if enemies surprise players, '' for no surprise."""
        self.combat_started = True

        # Nobody starts the fight standing inside somebody else or in a
        # wall. Spawn points on the premade maps are one square apart,
        # which is fine for Medium creatures and immediately overlaps for
        # anything Large or bigger — an ogre needs 2x2 and a dragon 3x3.
        self.resolve_overlaps()

        # Register entities with stats tracker
        for entity in self.entities:
            if not entity.is_lair:
                self.stats_tracker.register_entity(entity)

        # Check for Lair Actions (only if lair is enabled from encounter setup)
        # PHB/MM: Lair actions only occur when fighting in the creature's lair
        lair_owners = []
        if self.lair_enabled:
            from engine.special_actions import has_lair_actions
            lair_owners = [e for e in self.entities
                           if has_lair_actions(e.stats)]
        for owner in lair_owners:
            from data.models import CreatureStats
            lair_stats = CreatureStats(name="Lair Action", hit_points=1, speed=0, challenge_rating=0)
            lair_ent = Entity(lair_stats, -100, -100)
            lair_ent.initiative = 20
            lair_ent.is_lair = True
            lair_ent.lair_owner = owner
            self.entities.append(lair_ent)

        for entity in self.entities:
            if entity.is_lair:
                continue
            # A value the DM typed in during deployment is a decision,
            # not a leftover — rolling over it threw away the order they
            # had just set up by hand.
            if getattr(entity, "initiative_locked", False):
                continue
            entity.roll_initiative()
        self.entities.sort(key=lambda e: e.initiative, reverse=True)

        # PHB p.189: Surprise — surprised creatures can't move or act in round 1
        if surprise_side:
            for entity in self.entities:
                if entity.is_lair:
                    continue
                # Alert feat: can't be surprised
                if entity.has_feature("alert"):
                    continue
                if surprise_side == "players" and not entity.is_player:
                    entity.is_surprised = True
                    self.log(f"  [SURPRISE] {entity.name} is surprised!")
                elif surprise_side == "enemies" and entity.is_player:
                    entity.is_surprised = True
                    self.log(f"  [SURPRISE] {entity.name} is surprised!")

        self.log("=== COMBAT STARTED ===")
        self.log("Initiative order: " + " > ".join(e.name for e in self.entities))
        curr = self.get_current_entity()
        curr.reset_turn()
        self.log(f"--- Round {self.round}: {curr.name}'s turn ---")
        self._build_legendary_queue()

        # Initial win probability
        self.win_calculator.calculate(self)

    def _init_demo_entities(self):
        from data.models import AbilityScores, Action
        from data.library import library
        paladin = CreatureStats(
            name="Hero Paladin", hit_points=80, armor_class=18, speed=30,
            abilities=AbilityScores(strength=18, constitution=16, charisma=14),
            actions=[Action("Longsword", attack_bonus=7, damage_dice="1d8",
                            damage_bonus=4, damage_type="slashing")]
        )
        self.entities.append(Entity(paladin, 5, 5, is_player=True))
        bugbear = library.get_monster("Bugbear")
        self.entities.append(Entity(bugbear, 10, 5, is_player=False))

    # ------------------------------------------------------------------ #
    # Turn Management                                                      #
    # ------------------------------------------------------------------ #

    def get_current_entity(self) -> Entity:
        if not self.entities:
            raise ValueError("No entities in battle!")
        if self.turn_index >= len(self.entities):
            self.turn_index = 0
        return self.entities[self.turn_index]

    def spawn_summon(self, owner: Entity, name: str, x: float, y: float,
                     hp: int = 0, ac: int = 10, atk_bonus: int = 0,
                     damage_dice: str = "", damage_type: str = "force",
                     duration: int = 10, spell_name: str = "") -> Entity:
        """Spawn a summoned token (e.g. Spiritual Weapon) on the battlefield."""
        from data.models import CreatureStats, Action, AbilityScores

        spell_mod = owner.get_modifier(owner.stats.spellcasting_ability) if owner.stats.spellcasting_ability else 0
        actual_atk = atk_bonus or owner.stats.spell_attack_bonus or (
            owner.stats.proficiency_bonus + spell_mod)
        actual_dmg_bonus = spell_mod

        summon_stats = CreatureStats(
            name=f"{name} ({owner.name})",
            hit_points=max(hp, 1),
            armor_class=ac,
            speed=20,
            actions=[
                Action(name, description=f"Summon attack",
                       attack_bonus=actual_atk, damage_dice=damage_dice or "1d8",
                       damage_bonus=actual_dmg_bonus, damage_type=damage_type,
                       range=5)
            ],
        )
        ent = Entity(summon_stats, x, y, is_player=owner.is_player)
        ent.is_summon = True
        # A summon used to materialise straight on top of whoever was
        # standing there. Slide it to the nearest square it actually
        # fits in; if the whole area is packed, drop it next to its
        # summoner rather than inside somebody.
        spot = self.find_free_cell(ent, x, y)
        if spot is None:
            spot = self.find_free_cell(ent, owner.grid_x, owner.grid_y, 6)
        if spot is not None:
            ent.grid_x, ent.grid_y = float(spot[0]), float(spot[1])
        ent.summon_owner = owner
        ent.summon_rounds_left = duration
        ent.summon_spell_name = spell_name
        ent.hp = max(hp, 1)
        ent.max_hp = max(hp, 1)
        # Summon acts right after the owner in initiative
        ent.initiative = owner.initiative - 0.5
        if "Spiritual Weapon" in name:
            ent.acts_on_initiative = False

        self.entities.append(ent)
        # Re-sort to maintain initiative order
        current = self.get_current_entity()
        self.entities.sort(key=lambda e: e.initiative, reverse=True)
        self.turn_index = self.entities.index(current)

        # If the summoning spell requires concentration, tie the creature
        # to it so losing concentration makes the summon vanish (PHB).
        conc = owner.concentrating_on
        if conc is not None and spell_name and conc.name == spell_name:
            owner.register_concentration_effect(ent, "summon", spell_name)

        self.log(f"[SUMMON] {name} appears at ({int(x)},{int(y)})!")
        return ent

    def remove_expired_summons(self) -> bool:
        """Clear away summons that are finished. True if the current one went.

        Finished means the duration ran out OR the thing was destroyed.
        A summon is a spell effect, not a creature: it does not fall
        unconscious and it does not roll death saves. Leaving the wreck
        on the field meant a Spiritual Weapon on -1 hp kept taking a
        turn and kept swinging, because a player-side summon satisfied
        the "dying player still gets a turn" rule in next_turn.
        """
        current = self.get_current_entity() if self.entities else None
        expired = [e for e in self.entities
                   if e.is_summon and (e.summon_rounds_left <= 0
                                       or e.hp <= 0)]
        current_removed = False
        for e in expired:
            verb = "is destroyed" if e.hp <= 0 else "disappears"
            self.log(f"[SUMMON] {e.name} {verb}.")
            if e == current:
                current_removed = True

        self.entities = [e for e in self.entities if e not in expired]
        
        if current and current in self.entities:
            self.turn_index = self.entities.index(current)
        elif self.entities:
            self.turn_index = min(self.turn_index, len(self.entities) - 1)
            
        return current_removed

    def next_turn(self, skip_saves: bool = False) -> Optional[Entity]:
        if not self.entities:
            return None

        # Safety check for turn_index
        if self.turn_index >= len(self.entities):
            self.turn_index = 0

        # Clean up any spell terrain from concentration that was dropped
        # since the last turn advance (e.g. caster took damage from an
        # attack and failed the concentration save, caster fell unconscious).
        self._auto_cleanup_dropped_terrain()

        # --- END OF TURN LOGIC (Previous Entity) ---
        prev_ent = self.entities[self.turn_index]
        if prev_ent.hp > 0 and not skip_saves:
            self.handle_end_of_turn_saves(prev_ent)

        # Check Banishment status (returns, permanent banishment, etc.)
        self._update_banishment_status()

        # Validate grapples (break if out of range)
        self.validate_grapples()

        # Check Barbarian Rage end-of-turn
        if prev_ent.rage_active:
            if prev_ent.check_rage_end():
                self.log(f"[RAGE] {prev_ent.name}'s rage ends! (No attack/damage this turn)")

        # Clean up expired summons
        current_removed = self.remove_expired_summons()

        # Check if entities still exist
        if not self.entities:
            return None

        # If current entity was removed, the next entity shifted into its index.
        # So we decrement index so that the increment below lands on the correct next entity.
        if current_removed:
            self.turn_index -= 1

        # Advance turn — use a flag to ensure round increments exactly once per wrap
        self.turn_index += 1
        new_round = False
        if self.turn_index >= len(self.entities):
            self.turn_index = 0
            new_round = True

        # Find next valid entity (Alive OR Dying Player OR Lair)
        start_index = self.turn_index
        while True:
            ent = self.entities[self.turn_index]
            is_alive = ent.hp > 0
            # Players roll death saves, so they get a turn even if 0 HP
            # (unless dead-dead or stable). A summon is not a player
            # even when it fights on the party's side — it is a spell
            # effect, and a destroyed one has no death saves to roll.
            is_dying_player = (ent.is_player and not ent.is_summon
                               and ent.hp <= 0
                               and ent.death_save_failures < 3
                               and not ent.is_stable)

            should_act = ent.acts_on_initiative
            if (is_alive or is_dying_player or ent.is_lair) and should_act:
                break

            self.turn_index = (self.turn_index + 1) % len(self.entities)
            if self.turn_index == 0:
                new_round = True

            if self.turn_index == start_index:
                break # Everyone dead/skipped

        if new_round:
            self.round += 1
            self.log(f"=== ROUND {self.round} ===")

        current = self.get_current_entity()

        # PHB p.189: Surprised creatures skip their first turn,
        # then surprise ends (they can use reactions afterwards)
        if current.is_surprised:
            current.is_surprised = False
            self.log(f"  [SURPRISE] {current.name} is surprised and loses this turn.")
            # Still reset turn economy so reaction becomes available after this point
            current.reset_turn()
            current.action_used = True
            current.bonus_action_used = True
            current.movement_left = 0
            return current

        # 5e Rule: Legendary Actions reset at start of creature's turn
        current.reset_legendary_actions()
        current.reset_turn()

        # Handle Effects Duration (decrement at start of turn)
        expired = []
        for eff, duration in list(current.active_effects.items()):
            current.active_effects[eff] -= 1
            if current.active_effects[eff] <= 0:
                expired.append(eff)
        for eff in expired:
            del current.active_effects[eff]
            self.log(f"  [EFFECT] '{eff}' expired.")
            # Auto-remove condition if it matches effect name (e.g. Guiding Bolt)
            if current.has_condition(eff):
                current.remove_condition(eff)
            # PHB p.250: when Haste ends, the target loses a turn to
            # lethargy — also on natural expiry, not just when the
            # caster's concentration breaks.
            if eff == "Haste":
                current.apply_haste_lethargy()
                self.log(f"  [HASTE] {current.name} is overcome by lethargy!")

        # Regeneration at start of turn (Vampire, Troll, Phoenix, etc.)
        if current.hp > 0:
            self._handle_regeneration(current)

        # Champion Fighter: Survivor feature (regen if below half HP)
        if current.hp > 0 and current.has_feature("survivor"):
            if current.hp <= current.max_hp // 2:
                regen_amount = 5 + current.get_modifier("Constitution")
                old_hp = current.hp
                current.heal(regen_amount)
                actual = current.hp - old_hp
                if actual > 0:
                    self.log(f"  [SURVIVOR] {current.name} regenerates {actual} HP (below half)")

        # Concentration duration tracking: decrement rounds remaining
        if current.concentrating_on:
            self._tick_concentration_duration(current)

        # Check phase triggers (behavior change at HP thresholds)
        if current.hp > 0:
            self._check_phase_triggers(current)

        # Check hazard terrain at start of turn
        if current.hp > 0:
            self._check_hazard_damage(current)

        # Decrement Summon Duration
        if current.is_summon:
            current.summon_rounds_left -= 1
            if current.summon_rounds_left <= 0:
                self.log(f"  [SUMMON] {current.name} duration expired.")

        # Recharge Rolls (only if alive)
        if current.hp > 0:
            recharges = current.recharge_features()
            for r in recharges:
                self.log(f"  [RECHARGE] {r}")

        # Death Saves
        if current.hp <= 0 and not current.is_stable and not current.is_lair:
            res = current.roll_death_save()
            if res:
                self.log(f"  [DEATH] {res}")

        # Nobody starts a turn standing inside somebody else. This runs
        # after the death save above on purpose: a natural 20 puts a
        # downed creature back on 1 HP, and the body it was lying under
        # had been walked over while it counted for nothing.
        self.separate_overlapping()

        # Add to legendary queue if this creature has legendary actions
        self._build_legendary_queue()

        self.log(f"--- {current.name}'s turn (Round {self.round}, Initiative {current.initiative}) ---")
        if current.conditions:
            for cond in current.conditions:
                self.log(f"  [STATUS] {cond}")
        if current.concentrating_on:
            self.log(f"  [CONCENTRATION] {current.concentrating_on.name}")
        return current

    def _update_banishment_status(self):
        """Check all banished entities for return conditions."""
        # Iterate a copy since we might remove entities
        for ent in list(self.entities):
            if "Banished" not in ent.conditions:
                continue

            caster = ent.condition_sources.get("Banished")
            should_return = False
            permanent_banish = False

            # 1. Check Concentration: If caster lost it, target returns immediately
            if not caster or not caster.concentrating_on or caster.concentrating_on.name != "Banishment":
                should_return = True
                self.log(f"[BANISHMENT] Concentration broken/ended. {ent.name} returns.")
            
            # 2. Check Duration: If time runs out (active_effects <= 0)
            elif ent.active_effects.get("Banishment", 0) <= 0:
                # Duration expired naturally (1 minute passed)
                # Check planes
                native = ent.stats.native_plane
                current = self.current_plane
                
                if native and current and native.lower() != current.lower():
                    permanent_banish = True
                else:
                    should_return = True
                    self.log(f"[BANISHMENT] Duration expired. {ent.name} returns.")

            if permanent_banish:
                self.log(f"[BANISHMENT] {ent.name} is permanently banished to {ent.stats.native_plane}!")
                ent.remove_condition("Banished")
                self.entities.remove(ent)
                # Adjust turn index if needed
                if self.turn_index >= len(self.entities):
                    self.turn_index = 0

            elif should_return:
                ent.remove_condition("Banished")
                # Find return spot
                rx, ry = ent.banished_from if ent.banished_from else (ent.grid_x, ent.grid_y)
                if self.is_occupied(rx, ry, exclude=ent):
                    # Find nearest free space
                    # Spiral search
                    found = False
                    for r in range(1, 6): # Search up to 30ft away
                        for dx in range(-r, r+1):
                            for dy in range(-r, r+1):
                                nx, ny = rx + dx, ry + dy
                                if self.is_passable(nx, ny, exclude=ent):
                                    rx, ry = nx, ny
                                    found = True
                                    break
                            if found: break
                        if found: break
                
                ent.grid_x, ent.grid_y = rx, ry
                self.log(f"[BANISHMENT] {ent.name} reappears at ({int(rx)}, {int(ry)}).")

    # Everything planning spends. calculate_turn already rewinds where a
    # creature stood; these are the rest of the books it writes in.
    _PREVIEW_SCALARS = (
        "action_used", "bonus_action_used", "reaction_used", "movement_left",
        "reckless_attack_active", "rage_active", "rages_left",
        "potion_used_this_turn", "sneak_attack_used", "elevation",
        "is_flying", "is_climbing", "legendary_actions_left",
        "legendary_resistances_left", "concentrating_on",
        "concentration_rounds_left", "marked_target", "temp_hp", "hp",
    )
    _PREVIEW_DICTS = ("spell_slots", "feature_uses")

    def ai_bounds(self):
        """The rectangle creatures are allowed to move inside.

        The engine has no map edge, so a creature that decides to back
        away can back away forever: a ranger being chased by something
        she could not see retreated in a straight line to x = -429,
        eight squares a round for sixty rounds, off the DM's screen and
        out of the fight without either side ever landing a blow.

        The board is the terrain if there is any, otherwise where the
        creatures actually are, plus a wide margin so genuine
        manoeuvring is never cramped. Cached — terrain rarely moves.
        """
        cached = getattr(self, "_ai_bounds_cache", None)
        stamp = (len(self.terrain), len(self.entities))
        if cached is not None and cached[0] == stamp:
            return cached[1]
        xs, ys = [], []
        for t in self.terrain:
            xs += [t.grid_x, t.grid_x + max(1, t.width)]
            ys += [t.grid_y, t.grid_y + max(1, t.height)]
        for e in self.entities:
            xs.append(e.grid_x)
            ys.append(e.grid_y)
        if not xs:
            box = (0.0, 0.0, 200.0, 200.0)
        else:
            MARGIN = 40.0          # 200 ft of room beyond the action
            box = (min(0.0, min(xs)) - MARGIN, min(0.0, min(ys)) - MARGIN,
                   max(xs) + MARGIN, max(ys) + MARGIN)
        self._ai_bounds_cache = (stamp, box)
        return box

    def in_ai_bounds(self, x, y) -> bool:
        x0, y0, x1, y1 = self.ai_bounds()
        return x0 <= x <= x1 and y0 <= y <= y1

    def preview_ai_turn(self, entity: Entity):
        """Plan a turn WITHOUT spending anything.

        The stat panel shows "what would the AI do with this character",
        and it got that answer by running the real planner — which marks
        the action used, burns the bonus action, spends a spell slot,
        lights Reckless Attack and eats a rage. Merely selecting a
        character therefore consumed their turn, and on a hero the DM
        had not touched yet that is indistinguishable from the tool
        being broken.
        """
        snap = {k: getattr(entity, k, None) for k in self._PREVIEW_SCALARS}
        snap_d = {k: dict(getattr(entity, k, {}) or {})
                  for k in self._PREVIEW_DICTS}
        links = list(getattr(entity, "concentration_links", []) or [])
        try:
            return self.compute_ai_turn(entity)
        finally:
            self._restore_preview(entity, snap, snap_d, links)

    @staticmethod
    def _restore_preview(entity, snap, snap_d, links):
        """Put back everything a preview plan spent."""
        for k, v in snap.items():
            try:
                setattr(entity, k, v)
            except Exception:
                pass
        for k, v in snap_d.items():
            cur = getattr(entity, k, None)
            if isinstance(cur, dict):
                cur.clear()
                cur.update(v)
        cur_links = getattr(entity, "concentration_links", None)
        if isinstance(cur_links, list):
            cur_links[:] = links

    def apply_planned_move(self, mover: Entity, new_x, new_y,
                           elevation=None, flying=None, teleport=False,
                           dragged=None):
        """Walk a creature to where an approved step says it goes.

        Planning no longer moves anything — it only records intent — so
        this is what actually relocates a token, whether the DM pressed
        approve or the simulation is running itself. Anything the mover
        has grappled comes along (PHB p.195).

        ``elevation``/``flying`` restore the altitude the planner meant
        the creature to be at. A route that only exists in the air —
        over a statue, a wall, a chasm — is illegal on the ground, so
        the height has to land together with the position, not after it.

        ``teleport`` marks a blink rather than a walk: it drags nobody
        and ends every grapple the mover is part of, in both directions.

        ``dragged`` is where the planner actually left each grappled
        creature, as [(entity, x, y)]. Prefer it: the planner walks the
        route square by square and the victim trails one step behind,
        whereas re-deriving the spot from a single jump to the
        destination drops them back at the origin.
        """
        if mover is None:
            return
        if teleport:
            mover.break_all_grapples()
        if flying is not None:
            mover.is_flying = bool(flying)
        if elevation is not None:
            mover.elevation = elevation
        old_x, old_y = mover.grid_x, mover.grid_y
        mover.grid_x, mover.grid_y = float(new_x), float(new_y)
        # The planner's list, when it gave one, is the whole truth about
        # who comes along. A grapple made LATER in the same turn is
        # already on the creature by the time the move is approved —
        # planning applies it immediately — and dragging that victim
        # would move somebody the plan's own ordering had not grabbed
        # yet, out of reach of the attack the move was made for.
        want = None if dragged is None else {id(e) for e, _x, _y in dragged}
        spots = {id(e): (x, y) for e, x, y in (dragged or ())}
        for held in list(mover.grappling or ()):
            if held is None or held.hp <= 0:
                continue
            if want is not None and id(held) not in want:
                continue
            hx, hy = spots.get(id(held), (None, None))
            if hx is not None and self.is_passable(hx, hy, exclude=held):
                held.grid_x, held.grid_y = float(hx), float(hy)
                continue
            # A hold only drags what it can still reach. Teleports break
            # grapples the engine has no other chance to notice — an
            # Archmage that Misty Stepped out of a rogue's grip was
            # yanked twenty-eight feet back across the map the next time
            # the rogue took a step, and then stabbed from out of reach.
            reach = mover.get_max_melee_reach() / 5.0
            ms, hs = mover.size_in_squares, held.size_in_squares
            gx = max(0.0, held.grid_x - (old_x + ms),
                     old_x - (held.grid_x + hs))
            gy = max(0.0, held.grid_y - (old_y + ms),
                     old_y - (held.grid_y + hs))
            if math.hypot(gx, gy) > reach + 0.1:
                mover.release_grapple(held)
                self.log(f"[GRAPPLE] {held.name} is no longer within "
                         f"{mover.name}'s reach; the hold breaks.")
                continue
            # Dumping the victim in the square the mover left is only
            # right for a single step. An approved plan can cover thirty
            # feet at once, and a paladin who walked fifteen feet with an
            # ogre in tow left it three squares behind — then swung at it
            # from out of reach. Use the vacated square only when it is
            # still next to where the mover ended up.
            # Measure the VICTIM standing on the vacated square against
            # the mover's new footprint — not the mover's old anchor
            # against its new one, which for a Huge creature reads as
            # zero however far it walked.
            ox2 = max(0.0, old_x - (float(new_x) + ms),
                      float(new_x) - (old_x + hs))
            oy2 = max(0.0, old_y - (float(new_y) + ms),
                      float(new_y) - (old_y + hs))
            vacated_still_close = math.hypot(ox2, oy2) <= reach + 0.1
            if vacated_still_close and self.is_passable(old_x, old_y,
                                                        exclude=held):
                held.grid_x, held.grid_y = old_x, old_y
                continue
            spot = self.find_free_cell(held, mover.grid_x, mover.grid_y,
                                       max_radius=2)
            if spot is not None:
                held.grid_x, held.grid_y = spot
            else:
                mover.release_grapple(held)

    def apply_plan_movement(self, plan) -> int:
        """Run every movement a plan intends, in order.

        For callers that want the end state without stepping through
        the DM's approvals — the simulation, and tests that ask "where
        would this turn leave the creature".
        """
        moved = 0
        for step in getattr(plan, "steps", ()) or ():
            if step.attacker is None:
                continue
            if step.step_type == "move":
                self.apply_planned_move(step.attacker, step.new_x, step.new_y,
                                        step.new_elevation, step.new_flying,
                                        dragged=step.dragged)
                moved += 1
            elif (step.step_type == "spell"
                    and (step.old_x or step.old_y)
                    and (step.old_x, step.old_y) != (step.new_x, step.new_y)):
                self.apply_planned_move(step.attacker, step.new_x, step.new_y,
                                        teleport=True)
                moved += 1
        return moved

    def validate_grapples(self):
        """Break any grapple that is no longer real.

        Two directions, and only the first used to be checked. Sweeping
        the grapplers finds holds that have gone out of reach; sweeping
        the VICTIMS finds the far nastier case — a Grappled condition
        with nobody on the other end of it.

        That one deadlocks the fight outright. Grappled sets speed to 0,
        speed 0 means you cannot stand up from Prone, and a creature
        that is both can never act again: no movement, no escape, no
        end of combat. A whole party sat at full hit points for fifteen
        rounds logging nothing but "[STATUS] Prone / [STATUS] Grappled"
        because their grapplers had left the board and the condition
        outlived them.
        """
        for victim in self.entities:
            if not victim.has_condition("Grappled"):
                continue
            holder = victim.grappled_by
            still_held = (holder is not None
                          and holder in self.entities
                          and holder.hp > 0
                          and victim in holder.grappling)
            if not still_held:
                victim.grappled_by = None
                if holder is not None and victim in holder.grappling:
                    holder.grappling.remove(victim)
                victim.remove_condition("Grappled")
                self.log(f"[GRAPPLE] {victim.name} is free — nothing is "
                         f"holding them any more.")

        for grappler in self.entities:
            # Check targets this entity is grappling
            for target in list(grappler.grappling):
                # 1. Check if grappler incapacitated
                if grappler.is_incapacitated():
                    grappler.release_grapple(target)
                    self.log(f"[GRAPPLE] {grappler.name} incapacitated; releases {target.name}.")
                    continue
                
                # 2. Check range
                dist = self.get_distance(grappler, target)
                # Reach is usually 5ft (1 square). Large creatures might have more?
                # Standard grapple reach is 5ft unless specified.
                # We'll use max_melee_reach of grappler.
                reach = grappler.get_max_melee_reach() / 5.0
                
                if dist > reach + 0.1:
                    grappler.release_grapple(target)
                    self.log(f"[GRAPPLE] {target.name} broke free from {grappler.name} (out of reach).")

    def get_total_save_bonus(self, entity: Entity, ability: str) -> int:
        """Get save bonus including auras (e.g. Paladin).
        PHB p.85: Aura of Protection applies to the paladin AND allies within range."""
        bonus = entity.get_save_bonus(ability)
        # Paladin Aura of Protection: check self AND allies
        # The paladin benefits from their own aura (PHB p.85)
        aura_sources = [entity] + self.get_allies_of(entity)
        for source in aura_sources:
            if source.hp > 0 and not source.is_incapacitated():
                aura = source.get_feature("aura_of_protection")
                if aura:
                    if source == entity or self.get_distance(entity, source) * 5 <= (aura.aura_radius or 10):
                        bonus += max(1, source.get_modifier("Charisma"))
                        break  # Bonuses don't stack from multiple paladins
        return bonus

    def handle_end_of_turn_saves(self, entity: Entity):
        """Check if entity can shake off any conditions at end of turn."""
        from engine.rules import make_saving_throw

        # Check if Frightened source is dead -> remove Frightened
        if entity.has_condition("Frightened"):
            fear_source = entity.get_condition_source("Frightened")
            if fear_source and fear_source.hp <= 0:
                entity.remove_condition("Frightened")
                self.log(f"[STATUS] {entity.name} is no longer Frightened (source defeated)")

        # PHB p.290: Charmed ends if charmer is dead/incapacitated
        if entity.has_condition("Charmed"):
            charm_source = entity.get_condition_source("Charmed")
            if charm_source and (charm_source.hp <= 0 or charm_source.is_incapacitated()):
                entity.remove_condition("Charmed")
                self.log(f"[STATUS] {entity.name} is no longer Charmed (source defeated)")

        # Check if grappler is incapacitated or dead -> remove Grappled
        if entity.has_condition("Grappled") and entity.grappled_by:
            grappler = entity.grappled_by
            if grappler.hp <= 0 or grappler.is_incapacitated():
                grappler.release_grapple(entity)
                self.log(f"[STATUS] {entity.name} escapes grapple ({grappler.name} incapacitated)")

        # Iterate a copy since we might modify the dict
        for cond, meta in list(entity.condition_metadata.items()):
            if cond not in entity.conditions:
                continue  # Already removed above
            ability = meta.get("save")
            dc = meta.get("dc")
            if ability and dc:
                success, total, msg = make_saving_throw(entity, ability, dc, self,
                                                        applies_condition=cond)
                if success:
                    entity.remove_condition(cond)
                    self.log(f"[SAVE] {msg} -> no longer {cond}!")
                else:
                    self.log(f"[SAVE] {msg} -> remains {cond}.")

        # Timed conditions tick down at the end of the entity's turn and
        # expire at 0 (e.g. Blinding Powder "until end of next turn").
        for cond in list(getattr(entity, "condition_durations", {}).keys()):
            if cond not in entity.conditions:
                entity.condition_durations.pop(cond, None)
                continue
            entity.condition_durations[cond] -= 1
            if entity.condition_durations[cond] <= 0:
                entity.remove_condition(cond)
                self.log(f"[STATUS] {entity.name}: {cond} expired.")

    def _check_hazard_damage(self, entity: Entity):
        """Apply hazard terrain damage at the start of an entity's turn.
        Flying creatures above ground-level hazards are safe."""
        if entity.is_flying:
            return  # Flying above hazards
        t = self.get_terrain_at(int(entity.grid_x), int(entity.grid_y))
        if t is None:
            return
        # Per-5-ft terrain (Spike Growth, Wall of Thorns) only bites while
        # a creature moves through it — standing still in brambles is not
        # a fresh 2d4 every round.
        if t.is_spell_terrain and t.trigger == "per_5ft":
            return
        self.apply_terrain_effect(entity, t, reason="turn start")

    def apply_terrain_effect(self, entity: Entity, t, *, reason: str = "") -> int:
        """Resolve one tile's damage, saving throw and condition.

        Returns the damage actually dealt. Honours ``exempt`` (a cleric
        is untouched by their own Spirit Guardians), rolls the spell's
        saving throw when the tile carries one, halves on a success when
        the spell says so, and applies the condition on a failure.
        """
        if t is None or entity.hp <= 0:
            return 0
        if entity.name in (getattr(t, "exempt", None) or ()):
            return 0
        dc = getattr(t, "save_dc", 0) or 0
        ability = getattr(t, "save_ability", "") or ""
        condition = getattr(t, "applies_condition", "") or ""
        if not t.is_hazard and not condition:
            return 0

        saved = False
        if dc > 0 and ability:
            try:
                from engine.rules import make_saving_throw
                saved, _roll, _msg = make_saving_throw(
                    entity, ability, dc, battle=self)
            except Exception:
                bonus = entity.get_save_bonus(ability)
                saved = (random.randint(1, 20) + bonus) >= dc

        dealt = 0
        if t.is_hazard:
            dmg = roll_dice(t.hazard_damage)
            if saved:
                dmg = dmg // 2 if getattr(t, "half_on_save", True) else 0
            if dmg > 0:
                dealt, _broke = entity.take_damage(dmg, t.hazard_damage_type)
                where = f" ({reason})" if reason else ""
                self.log(f"  [HAZARD] {entity.name} takes {dealt} "
                         f"{t.hazard_damage_type} from {t.label}{where}"
                         f"{' — saved for half' if saved else ''}!")

        if condition and not saved and not entity.has_condition(condition):
            if condition in (entity.stats.condition_immunities or []):
                self.log(f"  [TERRAIN] {entity.name} is immune to "
                         f"{condition}.")
            else:
                entity.add_condition(condition, save_ability=ability,
                                     save_dc=dc)
                self.log(f"  [TERRAIN] {entity.name} is {condition} "
                         f"({t.label})!")
        return dealt

    def is_silenced(self, entity: Entity) -> bool:
        """Is this creature inside a Silence zone?

        PHB: no sound can be created within or pass through the area, so
        a creature inside cannot cast a spell with a verbal component.
        The spell library does not record components for most entries,
        and virtually every spell has V, so the rule here is "silenced =
        cannot cast" unless the creature has a feature that removes the
        requirement (Subtle Spell and the like).
        """
        if entity is None:
            return False
        t = self.get_terrain_at(int(entity.grid_x), int(entity.grid_y))
        if t is None or t.terrain_type != "silence":
            return False
        for feat in (entity.stats.features or []):
            blob = f"{feat.name} {feat.description}".lower()
            if "subtle" in blob or "without verbal" in blob \
                    or "no v/s" in blob:
                return False
        return True

    def can_cast_here(self, entity: Entity, spell=None) -> bool:
        """False when a Silence zone gags the caster."""
        if not self.is_silenced(entity):
            return True
        if spell is not None:
            comps = (getattr(spell, "components", "") or "").upper()
            # Only a spell explicitly recorded as having no verbal
            # component still works.
            if comps and "V" not in comps:
                return True
        return False

    def wind_wall_between(self, a: Entity, b: Entity) -> bool:
        """Does a Wind Wall stand between these two?

        PHB: the wall stops ordinary ranged weapon attacks (arrows,
        bolts, thrown weapons) and gases. It does not block sight, so
        the LOS check never noticed it.
        """
        if a is None or b is None or not self.terrain:
            return False
        walls = [t for t in self.terrain
                 if t.terrain_type == "wall_wind"]
        if not walls:
            return False
        x1, y1 = int(a.grid_x), int(a.grid_y)
        x2, y2 = int(b.grid_x), int(b.grid_y)
        steps = max(abs(x2 - x1), abs(y2 - y1))
        if steps <= 0:
            return False
        for i in range(1, steps):
            cx = x1 + round((x2 - x1) * i / steps)
            cy = y1 + round((y2 - y1) * i / steps)
            for w in walls:
                if w.occupies(cx, cy):
                    return True
        return False

    def apply_movement_terrain(self, entity: Entity, gx: int, gy: int,
                               *, entering: bool) -> int:
        """Terrain that triggers from movement rather than the clock.

        ``entering`` distinguishes the first step into a tile (Web,
        Black Tentacles) from continuing through it (Spike Growth, which
        bites for every 5 ft moved).
        """
        if entity.is_flying or entity.hp <= 0:
            return 0
        t = self.get_terrain_at(int(gx), int(gy))
        if t is None or not t.is_spell_terrain:
            return 0
        trigger = getattr(t, "trigger", "turn_start")
        if trigger == "per_5ft":
            return self.apply_terrain_effect(entity, t, reason="moving through")
        if trigger == "enter" and entering:
            return self.apply_terrain_effect(entity, t, reason="entering")
        return 0

    def _handle_regeneration(self, entity: Entity):
        """Handle start-of-turn regeneration for creatures with the Regeneration feature.
        Vampire: 20 HP, Troll: 10 HP, Phoenix: 10 HP, etc.
        Uses the 'regeneration' mechanic key and mechanic_value for HP amount."""
        regen_feat = entity.get_feature("regeneration")
        if not regen_feat:
            return
        try:
            regen_amount = int(regen_feat.mechanic_value) if regen_feat.mechanic_value else 10
        except ValueError:
            regen_amount = 10
        if entity.hp >= entity.max_hp:
            return
        old_hp = entity.hp
        entity.heal(regen_amount)
        actual = entity.hp - old_hp
        if actual > 0:
            self.log(f"  [REGEN] {entity.name} regenerates {actual} HP")

    def _check_phase_triggers(self, entity: Entity):
        """Check if any phase mechanics should trigger based on HP thresholds."""
        if entity.max_hp <= 0:
            return
        hp_pct = entity.hp / entity.max_hp
        for feat in entity.stats.features:
            if feat.phase_trigger_hp_pct > 0 and feat.name not in entity.active_phases:
                if hp_pct <= feat.phase_trigger_hp_pct:
                    entity.active_phases.add(feat.name)
                    self.log(f"  [PHASE] {entity.name}: {feat.name} triggered! {feat.phase_description}")

    # Duration constants: spell duration -> rounds (1 round = 6 sec)
    _DURATION_ROUNDS = {
        "1 round": 1, "1 minute": 10, "10 minutes": 100,
        "1 hour": 600, "8 hours": 4800, "24 hours": 14400,
    }

    def _tick_concentration_duration(self, entity: Entity):
        """Track concentration spell duration. Auto-drop when expired.
        Uses the entity's concentration_rounds_left counter."""
        spell = entity.concentrating_on
        if not spell or not spell.duration:
            return
        # Initialize counter if not set
        if not hasattr(entity, 'concentration_rounds_left') or entity.concentration_rounds_left is None:
            rounds = self._DURATION_ROUNDS.get(spell.duration, 0)
            if rounds <= 0:
                return  # Unknown or permanent duration - don't auto-expire
            entity.concentration_rounds_left = rounds
        # Decrement
        entity.concentration_rounds_left -= 1
        remaining = entity.concentration_rounds_left
        # Log warning at key thresholds
        if remaining == 1:
            self.log(f"  [CONCENTRATION] {spell.name} expires next round!")
        elif remaining <= 0:
            self.log(f"  [CONCENTRATION] {spell.name} duration expired!")
            self.remove_spell_terrain(entity.name, spell.name)
            entity.drop_concentration()
            entity.concentration_rounds_left = None

    def _build_legendary_queue(self):
        """After each turn, legendary creatures can use their legendary actions."""
        self.legendary_queue = [
            e for e in self.entities
            if e.legendary_actions_left > 0 and e.hp > 0 and e != self.get_current_entity()
        ]

    def get_pending_legendary_action(self) -> tuple[Optional[Entity], Optional[ActionStep]]:
        """Pop the next legendary action from the queue, if any."""
        while self.legendary_queue:
            leg_entity = self.legendary_queue[0]
            # Verify still valid
            if leg_entity.legendary_actions_left <= 0 or leg_entity.hp <= 0:
                self.legendary_queue.pop(0)
                continue
            
            step = self.ai.calculate_legendary_action(leg_entity, self)
            if step:
                # Don't pop yet; wait for UI to confirm/execute
                return leg_entity, step
            else:
                # No valid action found for this entity
                self.legendary_queue.pop(0)
        return None, None

    def commit_legendary_action(self, entity: Entity):
        """Call this after the UI has executed the legendary action."""
        if self.legendary_queue and self.legendary_queue[0] == entity:
            self.legendary_queue.pop(0)

    # ------------------------------------------------------------------ #
    # AI                                                                   #
    # ------------------------------------------------------------------ #

    def compute_ai_turn(self, entity: Entity) -> TurnPlan:
        """Calculate full turn plan for an NPC. Does NOT apply changes yet."""
        return self.ai.calculate_turn(entity, self)

    def check_opportunity_attacks(self, mover: Entity, old_x: float,
                                  old_y: float, new_x=None, new_y=None):
        """Who gets a swing as ``mover`` leaves their reach?

        Both ends of the move have to be passed in now. This used to
        read the mover's live position as the "after" end, which worked
        only because planning had already walked the token there. Now
        that a move lands when it is approved rather than when it is
        planned, the creature is still standing at ``old_x, old_y`` when
        this is asked — so without the destination every move looked
        like standing still and nobody ever got an attack.
        """
        if new_x is None:
            new_x = mover.grid_x
        if new_y is None:
            new_y = mover.grid_y
        # Forced movement (e.g. Grappled/dragged, Shoved) does not provoke OAs
        # If speed is 0 (Grappled), they can't move voluntarily, so it must be forced.
        if mover.has_condition("Grappled") or mover.has_condition("Restrained") or mover.has_condition("Stunned"):
            return []

        oas = []
        for e in self.entities:
            if e == mover or e.hp <= 0 or e.reaction_used:
                continue
            # A surprised or incapacitated watcher can't take the OA
            # reaction (PHB p.189 / Incapacitated).
            if getattr(e, "is_surprised", False) or e.is_incapacitated():
                continue
            if e.is_player == mover.is_player:
                continue  # same team
            # Disengage prevents OAs — except against a Sentinel-feat
            # watcher (creatures ignore Disengage for Sentinel's OA).
            if mover.is_disengaging and not e.has_feature("sentinel"):
                continue
            
            # Calculate reach in squares (1 square = 5 ft)
            reach_squares = e.get_max_melee_reach() / 5.0
            
            # Calculate distance BEFORE move (using old coordinates)
            dist_old = self._calculate_distance_coords(
                e.grid_x, e.grid_y, e.size_in_squares,
                old_x, old_y, mover.size_in_squares
            )
            
            # Calculate distance AFTER move (the destination)
            dist_new = self._calculate_distance_coords(
                e.grid_x, e.grid_y, e.size_in_squares,
                new_x, new_y, mover.size_in_squares
            )
            
            # Trigger OA if target was within reach AND is now outside reach
            # Add small tolerance for floating point comparisons
            if dist_old <= reach_squares + 0.01 and dist_new > reach_squares + 0.01:
                oas.append(e)
        return oas

    def check_counterspell_reaction(self, caster: Entity, spell_level: int) -> List[Entity]:
        """Who could counterspell this, by the book?

        PHB p.228: the trigger is "a creature within 60 feet of you that
        you can see casting a spell". Both halves of that matter and
        only the range half was being checked, so counterspells came
        through solid stone walls and blinded mages countered spells
        they could not possibly have seen being cast.
        """
        potential = []
        for enemy in self.get_enemies_of(caster):
            if enemy.reaction_used or enemy.is_incapacitated():
                continue

            # Check if has Counterspell known
            has_cs = False
            for s in enemy.stats.spells_known:
                if s.name == "Counterspell":
                    has_cs = True
                    break
            if not has_cs:
                continue

            if not enemy.has_spell_slot(3):
                continue
            if self.get_distance(caster, enemy) * 5 > 60:
                continue
            if enemy.has_condition("Blinded"):
                continue
            if not self.has_line_of_sight(enemy, caster):
                continue
            potential.append(enemy)
        return potential

    def check_turn_start_auras(self, entity: Entity) -> List[dict]:
        """Check if entity is in aura of others at start of turn."""
        triggers = []
        for other in self.entities:
            if other == entity or other.hp <= 0:
                continue
            # Check features
            for feat in other.stats.features:
                if feat.aura_radius > 0:
                    # Filter out passive auras (like Paladin Aura of Protection)
                    # Only trigger if it requires a save, deals damage, or applies a condition
                    if not (feat.save_ability or feat.damage_dice or feat.applies_condition):
                        continue

                    # Team safety check: Harmful auras don't affect allies
                    if other.is_player == entity.is_player:
                        continue

                    dist_ft = self.get_distance(entity, other) * 5
                    if dist_ft <= feat.aura_radius:
                        triggers.append({
                            "source": other,
                            "target": entity,
                            "feature": feat
                        })
        return triggers

    # ------------------------------------------------------------------ #
    # Grid / Geometry                                                      #
    # ------------------------------------------------------------------ #

    def _calculate_distance_coords(self, x1, y1, s1, x2, y2, s2) -> float:
        """Calculate distance between two entities given their coordinates and sizes."""
        # Distance in X (0 if ranges overlap)
        dx = max(0, x2 - (x1 + s1), x1 - (x2 + s2))
        # Distance in Y (0 if ranges overlap)
        dy = max(0, y2 - (y1 + s1), y1 - (y2 + s2))
        return math.hypot(dx, dy)

    def get_distance(self, e1: Entity, e2: Entity) -> float:
        """Calculate distance between entities in grid squares, accounting for elevation.
        Elevation difference adds to 3D distance (1 square = 5ft)."""
        s1 = e1.size_in_squares
        s2 = e2.size_in_squares

        # Distance in X (0 if ranges overlap)
        dx = max(0, e2.grid_x - (e1.grid_x + s1), e1.grid_x - (e2.grid_x + s2))

        # Distance in Y (0 if ranges overlap)
        dy = max(0, e2.grid_y - (e1.grid_y + s1), e1.grid_y - (e2.grid_y + s2))

        # Elevation difference in squares (5ft per square)
        dz = abs(e1.elevation - e2.elevation) / 5.0

        return math.sqrt(dx*dx + dy*dy + dz*dz)

    def is_adjacent(self, e1: Entity, e2: Entity) -> bool:
        return self.get_distance(e1, e2) < 0.5

    def resolve_overlaps(self) -> int:
        """Slide any creature that does not legally fit to the nearest
        square that it does. Returns how many were moved.

        Bigger creatures are placed first, because a Huge dragon has far
        fewer legal squares than a goblin and should get first pick.
        """
        moved = 0
        order = sorted(
            [e for e in self.entities if not e.is_lair and e.hp > 0],
            key=lambda e: -e.size_in_squares)
        for ent in order:
            if self.is_passable(ent.grid_x, ent.grid_y, exclude=ent):
                continue
            spot = self.find_free_cell(ent, ent.grid_x, ent.grid_y,
                                       max_radius=6)
            if spot is None:
                continue
            self.log(f"  [PLACEMENT] {ent.name} shifted from "
                     f"({int(ent.grid_x)},{int(ent.grid_y)}) to "
                     f"({int(spot[0])},{int(spot[1])}) — no room there.")
            ent.grid_x, ent.grid_y = float(spot[0]), float(spot[1])
            moved += 1
        return moved

    def separate_overlapping(self) -> int:
        """Break up creatures that are sharing squares. Returns how many
        were moved.

        A creature at 0 HP does not block anybody, so allies and enemies
        walk right over the body — and then it is healed, or rolls a
        natural 20 on its death save, and stands up inside whatever is
        now on top of it. Rather than police every heal, every turn
        begins by sliding anyone sharing a square out to the nearest
        free one.

        Smallest first, the opposite of :meth:`resolve_overlaps`: there
        the question is "who gets first pick of a crowded map", here it
        is "who squeezes out from underneath", and the goblin should be
        the one to shuffle aside, not the dragon standing on it.
        Terrain is only consulted for the destination — a creature
        inside a Forcecage is meant to stay stuck in it.
        """
        moved = 0
        order = sorted([e for e in self.entities
                        if not e.is_lair and e.hp > 0],
                       key=lambda e: e.size_in_squares)
        for ent in order:
            if not self.footprint_occupied(ent, ent.grid_x, ent.grid_y):
                continue
            spot = self.find_free_cell(ent, ent.grid_x, ent.grid_y,
                                       max_radius=6)
            if spot is None:
                continue
            self.log(f"  [PLACEMENT] {ent.name} squeezes out from "
                     f"({int(ent.grid_x)},{int(ent.grid_y)}) to "
                     f"({int(spot[0])},{int(spot[1])}) — that square was "
                     f"already taken.")
            ent.grid_x, ent.grid_y = float(spot[0]), float(spot[1])
            moved += 1
        return moved

    def find_free_cell(self, entity: Entity, x: float, y: float,
                       max_radius: int = 4):
        """Nearest square where ``entity`` legally fits, searching outward.

        Returns (x, y) or None. Used wherever something is placed rather
        than walked — a summon arriving, a token dropped by the DM — so
        nothing ever lands on top of another creature or inside a wall.
        """
        if self.is_passable(x, y, exclude=entity):
            return (x, y)
        for r in range(1, max(1, int(max_radius)) + 1):
            ring = []
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if max(abs(dx), abs(dy)) != r:
                        continue
                    ring.append((int(x) + dx, int(y) + dy))
            ring.sort(key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)
            for nx, ny in ring:
                if self.is_passable(nx, ny, exclude=entity):
                    return (float(nx), float(ny))
        return None

    def is_occupied(self, x: float, y: float, exclude: Entity = None) -> bool:
        for e in self.entities:
            if e == exclude or e.hp <= 0:
                continue
            # Check if point (x,y) is inside e's footprint
            s = e.size_in_squares
            if e.grid_x <= x < e.grid_x + s and e.grid_y <= y < e.grid_y + s:
                return True
        return False

    def get_cover_bonus(self, attacker: Entity, target: Entity) -> int:
        """
        Calculate AC bonus from cover (0, 2, or 5).
        5e cover: Half (+2 AC), Three-quarters (+5 AC), Total (can't target).
        Also considers elevation advantage (higher ground negates some cover).
        """
        best_bonus = 0

        # Elevation advantage: attacker above target reduces cover effectiveness
        elev_diff = attacker.elevation - target.elevation

        for t in self.terrain:
            if not t.provides_cover:
                continue

            # Is terrain adjacent to target?
            dist = math.hypot(t.grid_x - target.grid_x, t.grid_y - target.grid_y)
            if dist < 1.5:
                # Is terrain between attacker and target?
                v_ta_x = attacker.grid_x - target.grid_x
                v_ta_y = attacker.grid_y - target.grid_y
                v_tt_x = t.grid_x - target.grid_x
                v_tt_y = t.grid_y - target.grid_y

                if (v_ta_x * v_tt_x + v_ta_y * v_tt_y) > 0:
                    cb = t.cover_bonus
                    # If attacker is significantly above, reduce cover
                    if elev_diff >= 10 and cb <= 2:
                        cb = 0  # High ground negates half cover
                    elif elev_diff >= 20 and cb <= 5:
                        cb = 2  # Very high ground reduces 3/4 to half
                    best_bonus = max(best_bonus, cb)

        # Check LOS blocking terrain between attacker and target
        if best_bonus == 0:
            ax, ay = int(attacker.grid_x), int(attacker.grid_y)
            tx, ty = int(target.grid_x), int(target.grid_y)
            # 3D LOS — use eye-level ≈ top of the model (elevation + 5 ft)
            az = float(attacker.elevation) + 5.0
            tz = float(target.elevation) + 5.0
            if check_los_blocked(self.terrain, ax, ay, tx, ty, az, tz):
                best_bonus = max(best_bonus, 2)  # At minimum half cover if LOS obstructed

        return best_bonus

    def has_line_of_sight(self, e1: Entity, e2: Entity) -> bool:
        """Check if e1 can see e2. Considers terrain LOS blocking, darkness, invisibility.

        5e 2014 rules:
        - Heavily obscured (darkness, heavy fog): can't see → no LOS
        - Darkvision: treats darkness as dim light (lightly obscured) within range
        - Devil's Sight / Truesight: see normally in magical darkness
        - Blindsight: see without relying on sight at all
        """
        # Blindsight always works within range (ignore visibility entirely)
        bs_range = e1.get_blindsight_range()
        if bs_range > 0:
            dist_ft = self.get_distance(e1, e2) * 5
            if dist_ft <= bs_range:
                # Blindsight ignores invisible, darkness, everything
                # Still blocked by full cover (terrain LOS blocking)
                x1, y1 = int(e1.grid_x), int(e1.grid_y)
                x2, y2 = int(e2.grid_x), int(e2.grid_y)
                z1 = float(e1.elevation) + 5.0
                z2 = float(e2.elevation) + 5.0
                if check_los_blocked(self.terrain, x1, y1, x2, y2, z1, z2):
                    return False
                return True

        # Invisible target: can't see unless truesight
        if e2.has_condition("Invisible") and not e1.has_feature("truesight"):
            return False

        x1, y1 = int(e1.grid_x), int(e1.grid_y)
        x2, y2 = int(e2.grid_x), int(e2.grid_y)
        z1 = float(e1.elevation) + 5.0
        z2 = float(e2.elevation) + 5.0

        # Check terrain LOS blocking (walls, full cover)
        if check_los_blocked(self.terrain, x1, y1, x2, y2, z1, z2):
            return False

        # Darkness check: target in darkness terrain (heavily obscured)
        t_at_target = self.get_terrain_at(x2, y2)
        if t_at_target and t_at_target.terrain_type == "darkness":
            # Devil's Sight / Truesight see through magical darkness
            if e1.has_feature("devil_sight") or e1.has_feature("truesight"):
                return True
            # Darkvision: treats darkness as dim light within range → can see (with disadvantage)
            dv_range = e1.get_darkvision_range()
            if dv_range > 0:
                dist_ft = self.get_distance(e1, e2) * 5
                if dist_ft <= dv_range:
                    return True  # Can see but effectively lightly obscured → disadvantage applied elsewhere
            return False  # No special sight: heavily obscured = can't see

        # Heavy fog also blocks LOS (already handled via blocks_los in terrain)

        return True

    def get_target_obscurement(self, attacker: Entity, target: Entity) -> str:
        """Determine visibility obscurement level from attacker to target.

        Returns:
          "none"    - clear vision, no penalty
          "light"   - lightly obscured (dim light, light fog) → disadvantage on Perception
                      In 5e 2014 this gives disadvantage on attack rolls (effectively Blinded)
          "heavy"   - heavily obscured → can't see (handled by LOS check, shouldn't reach here)
        """
        x2, y2 = int(target.grid_x), int(target.grid_y)
        t = self.get_terrain_at(x2, y2)

        # Devil's Sight / Truesight: see normally in all darkness
        if attacker.has_feature("devil_sight") or attacker.has_feature("truesight"):
            return "none"

        # Blindsight: no visual penalties
        bs_range = attacker.get_blindsight_range()
        if bs_range > 0:
            dist_ft = self.get_distance(attacker, target) * 5
            if dist_ft <= bs_range:
                return "none"

        if t:
            # Darkness: if darkvision can reach, treated as dim light (lightly obscured)
            if t.terrain_type == "darkness":
                dv_range = attacker.get_darkvision_range()
                dist_ft = self.get_distance(attacker, target) * 5
                if dv_range > 0 and dist_ft <= dv_range:
                    return "light"  # Darkvision treats darkness as dim light
                return "heavy"  # Shouldn't get here if LOS blocks, but safety

            # Dim light: lightly obscured (disadvantage on Perception-based sight)
            if t.terrain_type == "dim_light":
                dv_range = attacker.get_darkvision_range()
                dist_ft = self.get_distance(attacker, target) * 5
                if dv_range > 0 and dist_ft <= dv_range:
                    return "none"  # Darkvision: dim light → normal light
                return "light"

            # Light fog: lightly obscured
            if t.terrain_type == "fog_light":
                return "light"

        return "none"

    def footprint_occupied(self, entity: Entity, x: float, y: float) -> bool:
        """Does another creature stand in any square ``entity`` would cover?

        ``is_occupied`` only ever tests one square, which quietly let a
        Large or Huge creature settle half on top of somebody else.
        """
        size = entity.size_in_squares if entity is not None else 1
        for dx in range(size):
            for dy in range(size):
                if self.is_occupied(x + dx, y + dy, exclude=entity):
                    return True
        return False

    def flyer_clears(self, entity: Entity, t) -> bool:
        """Can a flying ``entity`` pass over the impassable tile ``t``?

        Flight is not phasing. A creature only crosses an obstruction
        when it is actually above it, so a dragon at 15 ft sails over a
        10 ft wall while a portcullis, a pillar or a forcecage — none of
        which declare a height, so ``los_top_ft`` falls back to 100 ft —
        stops it dead. Chasms are the one thing flight always beats.
        """
        if t is None or t.passable:
            return True
        if t.is_gap:
            return True
        return float(entity.elevation) >= t.los_top_ft

    def is_passable(self, x: float, y: float, exclude: Entity = None) -> bool:
        """Is this cell free of creatures and terrain for ``exclude``?

        Checks the mover's whole footprint, not just its anchor square.
        Flying ignores ground obstacles only where the creature is high
        enough to be over them (see :meth:`flyer_clears`) — never other
        creatures, which occupy the air above their square too.
        """
        size = exclude.size_in_squares if exclude else 1
        is_flyer = exclude.is_flying if exclude else False
        for dx in range(size):
            for dy in range(size):
                check_x, check_y = x + dx, y + dy
                if self.is_occupied(check_x, check_y, exclude=exclude):
                    return False
                t = self.get_terrain_at(int(check_x), int(check_y))
                if t is None or t.passable:
                    continue
                if not is_flyer or not self.flyer_clears(exclude, t):
                    return False
        return True

    def is_passable_or_jumpable(self, x: float, y: float, entity: Entity = None) -> bool:
        """Like is_passable but also allows gaps that the entity can jump/fly across.
        Used by AI pathfinding to consider jump routes."""
        if self.is_passable(x, y, exclude=entity):
            return True
        # Check if it's a jumpable gap
        t = self.get_terrain_at(int(x), int(y))
        if t and t.is_gap and entity:
            gap_ft = t.gap_width_ft
            if entity.is_flying or entity.can_jump_gap(gap_ft,
                                                       running_start=True):
                return not self.footprint_occupied(entity, x, y)
        return False

    def get_gap_at(self, x: int, y: int):
        """Get gap terrain at position, or None."""
        t = self.get_terrain_at(x, y)
        if t and t.is_gap:
            return t
        return None

    def get_terrain_movement_cost(self, x: float, y: float, entity: Entity = None) -> float:
        """Returns movement multiplier: 1.0 normal, 2.0 difficult, 2.0 climbing.
        Flying entities ignore difficult terrain. Aquatic entities (swim
        speed / amphibious / water_breathing) ignore the water penalty."""
        if entity and entity.is_flying:
            return 1.0
        # PHB p.191: moving while prone = crawling, every foot costs one
        # extra foot (doubles again in difficult terrain via the stack
        # below). Prone no longer halves speed itself.
        crawl_mult = 2.0 if (entity and entity.has_condition("Prone")) else 1.0
        t = self.get_terrain_at(int(x), int(y))
        if t:
            # Water: aquatic creatures move at full speed; everyone else
            # pays the PHB p.182 swim penalty (half speed).
            if t.terrain_type in ("water", "deep_water"):
                if entity and entity.is_aquatic:
                    return crawl_mult
                return 2.0 * crawl_mult
            if t.is_difficult:
                return 2.0 * crawl_mult
            if t.is_climbable and entity and entity.is_climbing:
                # Climbing without climb speed = half speed (2x cost)
                if entity.stats.climb_speed <= 0:
                    return 2.0 * crawl_mult
        return crawl_mult

    def get_entity_at(self, x: float, y: float) -> Optional[Entity]:
        for e in self.entities:
            s = e.size_in_squares
            if e.grid_x <= x < e.grid_x + s and e.grid_y <= y < e.grid_y + s:
                return e
        return None

    def get_enemies_of(self, entity: Entity) -> List[Entity]:
        return [e for e in self.entities if e.is_player != entity.is_player and e.hp > 0 and "Banished" not in e.conditions]

    def get_allies_of(self, entity: Entity) -> List[Entity]:
        return [e for e in self.entities if e.is_player == entity.is_player and e.hp > 0 and e != entity and "Banished" not in e.conditions]

    # ------------------------------------------------------------------ #
    # Terrain                                                              #
    # ------------------------------------------------------------------ #

    def get_terrain_at(self, gx: int, gy: int) -> Optional[TerrainObject]:
        """The tile at this square, or None.

        Indexed rather than scanned. This is the single hottest call in
        the engine — every passability test hits it once per square of
        the mover's footprint, and pathfinding does that thousands of
        times per turn — so a linear walk of the terrain list made the
        cost of a turn scale with the size of the map. On a city
        district of two thousand tiles that was two thousand
        comparisons per lookup, and the combat audit measured turns
        thirty times slower there than on a small dungeon.

        The index is rebuilt whenever the terrain list is replaced or
        changes length, which covers every path that adds or removes a
        tile. Mutating a tile in place (opening a door) does not move
        it, so the index stays valid.
        """
        key = (id(self.terrain), len(self.terrain))
        if getattr(self, "_terrain_index_key", None) != key:
            index = {}
            for t in self.terrain:
                for dx in range(max(1, t.width)):
                    for dy in range(max(1, t.height)):
                        index.setdefault((t.grid_x + dx, t.grid_y + dy), t)
            self._terrain_index = index
            self._terrain_index_key = key
        return self._terrain_index.get((int(gx), int(gy)))

    def add_terrain(self, terrain: TerrainObject):
        # Remove any existing terrain at the same cell first
        self.terrain = [t for t in self.terrain if not t.occupies(terrain.grid_x, terrain.grid_y)]
        self.terrain.append(terrain)

    def remove_terrain_at(self, gx: int, gy: int):
        self.terrain = [t for t in self.terrain if not t.occupies(gx, gy)]

    def targets_in_aoe(self, caster, center_x, center_y,
                        radius_ft, shape="sphere", *,
                        exclude_caster=False):
        """Phase 29 — shared AoE target resolver used by the GM-click
        manual cast path and (going forward) anything else that needs
        to apply an AoE.

        ``caster`` is the entity who cast the spell (origin for cone
        and line). ``center_x/center_y`` is where they clicked.

        Shape rules (PHB pp. 204-205):

          * ``sphere`` / ``cylinder`` — every creature within
            ``radius_ft`` of the clicked point.
          * ``cube`` — every creature within ``radius_ft / 2`` on each
            axis from the centre (treated as edge-length = radius).
          * ``cone`` — origin = caster, opens toward the clicked
            point, half-angle 30° (60° total spread).
          * ``line`` — origin = caster, runs toward the clicked
            point, 5 ft wide.

        ``exclude_caster=True`` filters the caster out (used for
        cones/lines where the caster is the *origin* and shouldn't be
        damaged by their own spell).
        """
        import math as _math
        targets = []
        caster_cx = (caster.grid_x + caster.size_in_squares / 2.0
                       if caster else 0.0)
        caster_cy = (caster.grid_y + caster.size_in_squares / 2.0
                       if caster else 0.0)
        radius_sq = radius_ft / 5.0
        # Cone/line direction = caster → click; pre-compute axis.
        if shape in ("cone", "line"):
            dx = center_x - caster_cx
            dy = center_y - caster_cy
            length = _math.hypot(dx, dy)
            if length == 0:
                # User clicked on themselves — pick an arbitrary axis
                # so we still hit something rather than nothing.
                dx, dy, length = 1.0, 0.0, 1.0
            ax, ay = dx / length, dy / length
        else:
            ax = ay = 0.0
        for ent in self.entities:
            if ent.hp <= 0:
                continue
            if exclude_caster and ent is caster:
                continue
            tx = ent.grid_x + ent.size_in_squares / 2.0
            ty = ent.grid_y + ent.size_in_squares / 2.0
            if shape == "cube":
                half = radius_sq  # treat radius as half-edge
                if abs(tx - center_x) <= half and abs(ty - center_y) <= half:
                    targets.append(ent)
            elif shape == "cone":
                ex = tx - caster_cx
                ey = ty - caster_cy
                dist = _math.hypot(ex, ey)
                if dist > radius_sq or dist == 0:
                    if dist == 0 and not exclude_caster:
                        targets.append(ent)
                    continue
                # Project onto axis; require >0 (in front) and within
                # 30° half-angle (cos(30°) ~= 0.866 of length).
                proj = (ex * ax + ey * ay) / dist
                if proj >= _math.cos(_math.radians(30)):
                    targets.append(ent)
            elif shape == "line":
                ex = tx - caster_cx
                ey = ty - caster_cy
                # Along-axis distance (parallel)
                along = ex * ax + ey * ay
                if along < 0 or along > radius_sq:
                    continue
                # Perpendicular distance (1-square wide line = ±0.5)
                perp = abs(ex * (-ay) + ey * ax)
                if perp <= 0.6:  # half-square + small fudge
                    targets.append(ent)
            else:
                # Default: sphere / cylinder
                if _math.hypot(tx - center_x, ty - center_y) <= radius_sq:
                    targets.append(ent)
        return targets

    def spawn_spell_terrain(self, spell, caster, center_x, center_y):
        """Create persistent terrain tiles for a spell's area of effect."""
        import math
        terrain_type = spell.creates_terrain
        if not terrain_type:
            return
        radius_sq = spell.aoe_radius / 5.0  # convert feet to grid squares
        # For line/wall spells: wall length = aoe_radius (e.g. Wall of Fire 60ft).
        # Wall extends half on each side of center → half-length in squares.
        wall_half = max(1, int(round(radius_sq / 2)))
        # Determine wall orientation from caster→center direction.
        # Wall runs perpendicular to the cast direction (blocks the path).
        vertical_wall = True  # default
        if caster is not None:
            cdx = center_x - caster.grid_x
            cdy = center_y - caster.grid_y
            # If caster is mostly north/south of center, wall runs east-west
            vertical_wall = abs(cdy) < abs(cdx)
        tiles_created = 0
        for dx in range(int(-radius_sq), int(radius_sq) + 1):
            for dy in range(int(-radius_sq), int(radius_sq) + 1):
                gx = int(center_x) + dx
                gy = int(center_y) + dy
                # Shape filtering
                if spell.aoe_shape in ("sphere", "cylinder"):
                    if math.hypot(dx, dy) > radius_sq:
                        continue
                elif spell.aoe_shape == "cube":
                    if abs(dx) > radius_sq or abs(dy) > radius_sq:
                        continue
                elif spell.aoe_shape == "line":
                    # 5e Wall: a single straight line, 1 square thick, not a cross.
                    if vertical_wall:
                        if dx != 0 or abs(dy) > wall_half:
                            continue
                    else:
                        if dy != 0 or abs(dx) > wall_half:
                            continue
                # Don't overwrite non-spell terrain (walls, doors, etc.)
                existing = self.get_terrain_at(gx, gy)
                if existing and not existing.is_spell_terrain:
                    continue
                t = TerrainObject(
                    terrain_type=terrain_type,
                    grid_x=gx, grid_y=gy,
                    spell_owner=caster.name,
                    spell_name=spell.name,
                    is_spell_terrain=True,
                    **_spell_terrain_rules(spell, caster),
                )
                self.add_terrain(t)
                tiles_created += 1
        if tiles_created > 0:
            self.log(f"  [TERRAIN] {caster.name}'s {spell.name} creates {tiles_created} tiles of {terrain_type}.")

    def remove_spell_terrain(self, caster_name: str, spell_name: str):
        """Remove all terrain tiles created by a specific spell from a specific caster."""
        before = len(self.terrain)
        self.terrain = [t for t in self.terrain
                        if not (t.is_spell_terrain and t.spell_owner == caster_name and t.spell_name == spell_name)]
        removed = before - len(self.terrain)
        if removed > 0:
            self.log(f"  [TERRAIN] {spell_name} terrain fades ({removed} tiles removed).")

    def _auto_cleanup_dropped_terrain(self):
        """Scan all entities for concentration-spell terrain that should be cleaned up.

        Triggers:
          - Entity's drop_concentration() set `_dropped_spell_terrain` (damage broke
            concentration, caster was incapacitated, etc.)
          - Entity is dead/unconscious AND still listed as concentrating on a
            terrain-creating spell (fallback in case drop_concentration was skipped).
        """
        for ent in self.entities:
            info = getattr(ent, '_dropped_spell_terrain', None)
            if info:
                caster_name, spell_name = info
                self.remove_spell_terrain(caster_name, spell_name)
                ent._dropped_spell_terrain = None
            # Fallback: dead caster still concentrating on terrain spell
            if ent.hp <= 0 and ent.concentrating_on and getattr(ent.concentrating_on, 'creates_terrain', ''):
                spell = ent.concentrating_on
                self.remove_spell_terrain(ent.name, spell.name)
                ent.drop_concentration()
                ent._dropped_spell_terrain = None

    def toggle_door_at(self, gx: int, gy: int) -> bool:
        """Toggle a door at the given position. Returns True if toggled."""
        t = self.get_terrain_at(gx, gy)
        if t and t.is_door:
            if t.toggle_door():
                state = "opens" if t.door_open else "closes"
                self.log(f"  [DOOR] Door at ({gx},{gy}) {state}.")
                return True
            else:
                self.log(f"  [DOOR] Door at ({gx},{gy}) is locked!")
                return False
        return False

    def unlock_door_at(self, gx: int, gy: int) -> bool:
        """Unlock a locked door at the given position."""
        t = self.get_terrain_at(gx, gy)
        if t and t.is_door and t.is_locked:
            t.unlock()
            self.log(f"  [DOOR] Door at ({gx},{gy}) unlocked!")
            return True
        return False

    def get_elevation_at(self, gx: int, gy: int) -> int:
        """Get ground elevation in feet at grid position."""
        return get_elevation_at(self.terrain, gx, gy)

    def apply_fall_damage(self, entity: Entity, fall_height_ft: int):
        """Apply falling damage to an entity. 1d6 per 10ft, max 20d6. Lands prone."""
        if fall_height_ft <= 0:
            return
        dmg = calculate_fall_damage(fall_height_ft)
        if dmg > 0:
            dealt, _ = entity.take_damage(dmg, "bludgeoning")
            self.log(f"  [FALL] {entity.name} falls {fall_height_ft}ft and takes {dealt} bludgeoning damage!")
            # Falling creatures land prone (PHB p.183)
            if entity.hp > 0 and not entity.has_condition("Prone"):
                entity.add_condition("Prone")
                self.log(f"  [FALL] {entity.name} lands prone.")
        entity.is_flying = False
        entity.is_climbing = False

    def move_entity_with_elevation(self, entity: Entity, new_x: float, new_y: float,
                                    is_jumping: bool = False):
        """Move entity and handle elevation changes, fall damage, climbing costs.
        is_jumping: entity is mid-jump (won't fall into gaps)."""
        old_elev = entity.elevation
        new_ground = self.get_elevation_at(int(new_x), int(new_y))

        # Check for gap/chasm at destination
        t_at_new = self.get_terrain_at(int(new_x), int(new_y))
        if t_at_new and t_at_new.is_gap and not entity.is_flying and not is_jumping:
            # Entity walks into a chasm without jumping - they fall!
            fall_dist = abs(t_at_new.elevation) + old_elev
            entity.grid_x = float(new_x)
            entity.grid_y = float(new_y)
            entity.elevation = t_at_new.elevation
            if t_at_new.is_hazard:
                # Lava/acid chasm: hazard damage on top of fall
                from engine.dice import roll_dice
                hdmg = roll_dice(t_at_new.hazard_damage)
                dealt, _ = entity.take_damage(hdmg, t_at_new.hazard_damage_type)
                self.log(f"  [HAZARD] {entity.name} falls into {t_at_new.name}! {dealt} {t_at_new.hazard_damage_type} damage!")
            self.apply_fall_damage(entity, fall_dist)
            self.log(f"  [CHASM] {entity.name} falls into {t_at_new.name}!")
            return

        if entity.is_flying:
            # Flying entity: stays at current elevation or terrain elevation, whichever is higher
            entity.elevation = max(entity.elevation, new_ground)
            # Indoor ceiling cap (Phase 4c): enforce max altitude
            if self.ceiling_ft > 0:
                cap = self.ceiling_ft - 5
                if entity.elevation > cap:
                    entity.elevation = max(new_ground, cap)
        elif entity.is_climbing:
            # Climbing: entity reaches the terrain's elevation
            entity.elevation = new_ground
        else:
            # Walking: if terrain is lower, check for fall
            if new_ground < old_elev:
                fall_dist = old_elev - new_ground
                t_at_new = self.get_terrain_at(int(new_x), int(new_y))
                # Stairs/ladders/bridges are safe transitions
                if t_at_new and t_at_new.terrain_type in ("stairs_up", "stairs_down", "ladder", "bridge"):
                    entity.elevation = new_ground
                elif fall_dist >= 10:
                    # Fall damage
                    entity.elevation = new_ground
                    self.apply_fall_damage(entity, fall_dist)
                else:
                    # Small drop (< 10ft), no damage
                    entity.elevation = new_ground
            else:
                # Going up: need stairs/ladder/climb, or it's same level
                if new_ground > old_elev:
                    t_at_new = self.get_terrain_at(int(new_x), int(new_y))
                    if t_at_new and t_at_new.terrain_type in ("stairs_up", "stairs_down", "ladder"):
                        entity.elevation = new_ground
                    elif t_at_new and t_at_new.is_climbable:
                        entity.elevation = new_ground
                        entity.is_climbing = True
                    else:
                        entity.elevation = new_ground
                else:
                    entity.elevation = new_ground

        entity.grid_x = float(new_x)
        entity.grid_y = float(new_y)

    # ------------------------------------------------------------------ #
    # Forced movement (shove / telekinesis / thunderwave etc.)
    # ------------------------------------------------------------------ #
    def push_entity(self, target: Entity, from_x: float, from_y: float,
                     distance: int = 5) -> dict:
        """Push ``target`` ``distance`` feet straight away from (from_x, from_y).

        Handles:
          * Destination occupied or blocked by an impassable (non-gap) wall:
            stops at the last free cell along the push line.
          * Destination is a gap/chasm: the target falls in (unless flying)
            and takes gap hazard + fall damage via move_entity_with_elevation.
          * Destination is a ground hazard (lava / spikes / fire / acid):
            full hazard damage applied, one-shot (simulates being thrown
            into it rather than walking through).
          * Destination is a lower tile (platform edge): fall damage applies
            if drop is >= 10 ft.

        Returns a summary dict with ``moved_cells``, ``final_cell``,
        ``fell_into_gap``, ``fell_from``, ``hazard_damage``,
        ``destination_type`` — the AI uses it for scoring.
        """
        result = {
            "moved_cells": 0,
            "final_cell": (int(target.grid_x), int(target.grid_y)),
            "fell_into_gap": False,
            "fell_from": 0,
            "hazard_damage": 0,
            "destination_type": "",
        }
        if target.hp <= 0 or distance <= 0:
            return result

        cells = max(1, int(round(distance / 5.0)))
        dx = target.grid_x - from_x
        dy = target.grid_y - from_y
        dist = (dx * dx + dy * dy) ** 0.5
        if dist <= 0:
            return result
        step_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
        step_y = 1 if dy > 0 else (-1 if dy < 0 else 0)
        # Snap to nearest cardinal if diagonal dominance is not clear
        if abs(dx) > abs(dy) * 1.2:
            step_y = 0
        elif abs(dy) > abs(dx) * 1.2:
            step_x = 0

        last_x, last_y = target.grid_x, target.grid_y
        cur_x, cur_y = last_x, last_y
        pushed = 0
        for _ in range(cells):
            nx = cur_x + step_x
            ny = cur_y + step_y
            t = self.get_terrain_at(int(nx), int(ny))
            # Gap / hazard stops the push AT the gap (target gets shoved in)
            if t is not None and t.is_gap:
                pushed += 1
                cur_x, cur_y = nx, ny
                break
            # Footprint-aware: the old single-cell test let a Large
            # creature be shoved through a one-square doorway it cannot
            # fit through, and past the corner of another creature.
            if not self.is_passable(nx, ny, exclude=target):
                break
            pushed += 1
            cur_x, cur_y = nx, ny
            # Ground hazard: continue past, but we mark it
            if t is not None and t.is_hazard:
                # Stop at first big hazard (lava-tier) — no walking through
                if t.terrain_type in ("lava", "fire", "acid", "lava_chasm"):
                    break

        if pushed == 0:
            return result

        # Apply destination effects via move_entity_with_elevation so the
        # existing fall / gap / hazard handling fires consistently.
        old_elev = target.elevation
        before_hp = target.hp
        self.move_entity_with_elevation(target, cur_x, cur_y)
        t_final = self.get_terrain_at(int(cur_x), int(cur_y))

        # Forced-movement ground hazard: a shove into lava/fire/acid/spikes
        # triggers hazard damage immediately (unlike walking, which only
        # charges on turn events).
        if (t_final is not None and t_final.is_hazard
                and not t_final.is_gap and target.hp > 0):
            from engine.dice import roll_dice
            hdmg = roll_dice(t_final.hazard_damage)
            dealt, _ = target.take_damage(hdmg, t_final.hazard_damage_type)
            self.log(
                f"  [SHOVE HAZARD] {target.name} pushed into {t_final.label}: "
                f"{dealt} {t_final.hazard_damage_type} damage!"
            )

        after_hp = target.hp
        # fell_from = how many feet the target actually descended due to
        # the push (platform edge → ground, or stayed on a gap).
        fell_from = max(0, old_elev - target.elevation)
        result.update({
            "moved_cells": pushed,
            "final_cell": (int(cur_x), int(cur_y)),
            "fell_into_gap": bool(t_final and t_final.is_gap),
            "fell_from": fell_from,
            "hazard_damage": max(0, before_hp - after_hp),
            "destination_type": t_final.terrain_type if t_final else "",
        })
        return result

    # ------------------------------------------------------------------ #
    # Ceiling (indoor flight cap)                                          #
    # ------------------------------------------------------------------ #
    def max_fly_altitude(self, ground_elev: int = 0) -> int:
        """Return the highest elevation (ft) a flying creature may reach
        above ``ground_elev``. If no ceiling is set, returns a very large
        number (effectively unlimited)."""
        if self.ceiling_ft <= 0:
            return 10_000
        # The ceiling is measured in ft above global zero, so even on a
        # platform the entity still can't go above ceiling_ft total.
        return max(ground_elev, self.ceiling_ft - 5)

    def clamp_fly_altitude(self, entity: Entity):
        """If entity is flying above the ceiling, pull it down to the cap."""
        if self.ceiling_ft <= 0 or not entity.is_flying:
            return
        cap = self.ceiling_ft - 5
        if entity.elevation > cap:
            entity.elevation = max(0, cap)
            self.log(f"  [CEILING] {entity.name} caps at {entity.elevation}ft "
                     f"(ceiling {self.ceiling_ft}ft).")

    # ------------------------------------------------------------------ #
    # Battle background image                                              #
    # ------------------------------------------------------------------ #
    def set_background_image(self, path: str, alpha: int = 200,
                              cells_w: int = 40, cells_h: int = 40,
                              offset_x: int = 0, offset_y: int = 0) -> bool:
        """Configure a JPG/PNG background image. path may be empty to clear.
        Returns True if accepted (path empty, or the file exists)."""
        if not path:
            self.background_image_path = ""
            return True
        import os as _os
        abs_path = path
        if not _os.path.isabs(abs_path):
            base_dir = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
            abs_path = _os.path.join(base_dir, path)
        if not _os.path.isfile(abs_path):
            return False
        self.background_image_path = path
        self.background_alpha = max(0, min(255, int(alpha)))
        self.background_world_cells_w = max(1, int(cells_w))
        self.background_world_cells_h = max(1, int(cells_h))
        self.background_offset_x = int(offset_x)
        self.background_offset_y = int(offset_y)
        return True

    # ------------------------------------------------------------------ #
    # Manual DM operations                                                 #
    # ------------------------------------------------------------------ #

    def update_initiative(self, entity: Entity, delta: int):
        entity.initiative += delta
        # Typed by hand: start_combat must not roll over it.
        entity.initiative_locked = True
        if not self.combat_started:
            self.entities.sort(key=lambda e: e.initiative, reverse=True)
            return
        current = self.get_current_entity()
        self.entities.sort(key=lambda e: e.initiative, reverse=True)
        self.turn_index = self.entities.index(current)

    def move_in_initiative(self, entity: Entity, direction: int):
        """DM turn-order edit: move ``entity`` one slot earlier
        (direction=-1) or later (direction=+1) by swapping initiative
        values with its neighbour. Keeps the current turn pointer on the
        same creature."""
        order = self.entities
        if entity not in order:
            return
        idx = order.index(entity)
        other_idx = idx + direction
        if other_idx < 0 or other_idx >= len(order):
            return
        current = self.get_current_entity()
        other = order[other_idx]
        entity.initiative, other.initiative = other.initiative, entity.initiative
        # Equal initiatives would make the swap a no-op after sorting —
        # nudge so the intended order holds.
        if entity.initiative == other.initiative:
            entity.initiative += -direction
        self.entities.sort(key=lambda e: e.initiative, reverse=True)
        self.turn_index = self.entities.index(current)
        self.log(f"[INIT] {entity.name} moved "
                 f"{'earlier' if direction < 0 else 'later'} in turn order.")

    def check_battle_over(self) -> Optional[str]:
        players_alive = any(e.is_player and e.hp > 0 for e in self.entities)
        enemies_alive = any(not e.is_player and e.hp > 0 and not e.is_lair and not e.is_summon for e in self.entities)
        if not players_alive:
            return "enemies"
        if not enemies_alive:
            return "players"
        return None

    def finalize_battle(self, winner: str):
        """Finalize battle statistics and generate report."""
        self.stats_tracker.finalize(self.entities, self.round, winner)

    def get_win_probability(self) -> dict:
        """Get current win probability for players."""
        return self.win_calculator.calculate(self)

    def get_encounter_danger(self) -> dict:
        """Get pre-combat encounter danger assessment."""
        from engine.win_probability import assess_encounter_danger
        players = [e for e in self.entities if e.is_player]
        enemies = [e for e in self.entities if not e.is_player and not e.is_lair]
        return assess_encounter_danger(players, enemies)

    def get_dm_suggestion(self, entity: Entity):
        """Get AI suggestion for a player's turn.

        Advisory only: the advisor plans with a copy of the battle but
        the real creature, so without this the act of asking spent the
        creature's action, bonus action and slots.
        """
        snap = {k: getattr(entity, k, None) for k in self._PREVIEW_SCALARS}
        snap_d = {k: dict(getattr(entity, k, {}) or {})
                  for k in self._PREVIEW_DICTS}
        links = list(getattr(entity, "concentration_links", []) or [])
        try:
            return self.dm_advisor.get_optimal_move(entity, self)
        finally:
            self._restore_preview(entity, snap, snap_d, links)

    def rate_player_action(self, entity: Entity, action_type: str,
                           target: Entity = None, damage_dealt: int = 0,
                           spell_name: str = "", moved_distance: float = 0):
        """Rate a player's action compared to AI optimal."""
        return self.dm_advisor.rate_player_action(
            entity, self, action_type, target, damage_dealt,
            spell_name, moved_distance)

    # ------------------------------------------------------------------ #
    # Save / Load  (delegated to engine.battle_serialization)              #
    # ------------------------------------------------------------------ #

    def get_state_dict(self) -> dict:
        """Serialize full combat state to a dictionary."""
        from engine.battle_serialization import get_state_dict
        return get_state_dict(self)

    def save_state(self, filepath: str):
        """Serialize full combat state to JSON file."""
        from engine.battle_serialization import save_state
        save_state(self, filepath)

    def restore_state(self, data: dict):
        """Restore state from dictionary."""
        from engine.battle_serialization import restore_state
        restore_state(self, data)

    @classmethod
    def from_save(cls, filepath: str, log_callback: Callable[[str], None]) -> "BattleSystem":
        """Reconstruct a BattleSystem from a saved JSON file."""
        from engine.battle_serialization import battle_from_save
        return battle_from_save(filepath, log_callback)
