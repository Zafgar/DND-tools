"""
D&D 5e 2014 Tactical AI for NPCs and Auto-Battle Heroes.
Computes an optimal TurnPlan for a given entity.
Understands class mechanics: Rage, Sneak Attack, Divine Smite, Hunter's Mark,
Stunning Strike, Flurry of Blows, Spiritual Weapon summons, etc.
"""
import math
import random
import heapq
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING
from data.models import Action, SpellInfo
from engine.dice import roll_attack, roll_dice, roll_dice_critical, average_damage

if TYPE_CHECKING:
    from engine.entities import Entity
    from engine.battle import BattleSystem


@dataclass
class ActionStep:
    """One step inside a full turn plan."""
    step_type: str             # "attack","spell","bonus_attack","bonus_spell","move","wait","legendary","summon"
    description: str = ""
    attacker: Optional["Entity"] = None
    target: Optional["Entity"] = None
    targets: List["Entity"] = field(default_factory=list)
    action_name: str = ""
    action: Optional[Action] = None
    spell: Optional[SpellInfo] = None
    slot_used: int = 0
    attack_roll: int = 0
    attack_roll_str: str = ""
    nat_roll: int = 0
    is_crit: bool = False
    is_hit: bool = False
    damage: int = 0
    damage_type: str = ""
    save_dc: int = 0
    save_ability: str = ""
    applies_condition: str = ""
    condition_dc: int = 0
    new_x: float = 0.0
    new_y: float = 0.0
    movement_ft: float = 0.0
    old_x: float = 0.0
    old_y: float = 0.0
    aoe_center: tuple = field(default_factory=tuple)
    # Class mechanic extras
    bonus_damage: int = 0            # Extra damage from Sneak Attack, Smite, etc.
    bonus_damage_desc: str = ""      # "Sneak Attack 5d6", "Divine Smite 2d8", etc.
    rage_bonus: int = 0              # Rage damage bonus applied
    # Summon spawn info
    summon_name: str = ""
    summon_x: float = 0.0
    summon_y: float = 0.0
    summon_hp: int = 0
    summon_ac: int = 10
    summon_owner: Optional["Entity"] = None
    summon_duration: int = 10
    summon_spell: str = ""
    summon_immediate_attack: bool = False  # If True, attacks immediately after spawn


@dataclass
class TurnPlan:
    entity: Optional["Entity"] = None
    steps: List[ActionStep] = field(default_factory=list)
    skipped: bool = False
    skip_reason: str = ""


class TacticalAI:
    """Full D&D 5e 2014 tactical AI with class mechanic awareness."""

    def calculate_turn(self, entity: "Entity", battle: "BattleSystem") -> TurnPlan:
        plan = TurnPlan(entity=entity)

        if entity.is_lair:
            return self._handle_lair_turn(entity, battle, plan)

        # Summons act on owner's turn with limited actions
        if entity.is_summon:
            return self._handle_summon_turn(entity, battle, plan)

        if entity.is_incapacitated():
            plan.skipped = True
            conds = ", ".join(entity.conditions & {"Incapacitated", "Paralyzed", "Stunned", "Unconscious", "Petrified"})
            plan.skip_reason = f"Incapacitated ({conds})"
            return plan

        # Death saves for dying players
        if entity.hp <= 0 and entity.is_player:
            plan.skipped = True
            plan.skip_reason = "Unconscious (dying)"
            return plan

        enemies = battle.get_enemies_of(entity)
        allies = battle.get_allies_of(entity)

        if not enemies:
            plan.skipped = True
            plan.skip_reason = "No valid targets"
            return plan

        # ----- 0. PRE-TURN: Barbarian Rage activation -----
        if not entity.bonus_action_used:
            rage_step = self._try_start_rage(entity, enemies, allies, battle)
            if rage_step:
                plan.steps.append(rage_step)
                entity.bonus_action_used = True

        # ----- 0.5. PRE-TURN: Rogue Cunning Action (Hide) -----
        if not entity.bonus_action_used and entity.has_feature("cunning_action"):
            hide_step = self._try_cunning_hide(entity, enemies, battle)
            if hide_step:
                plan.steps.append(hide_step)
                entity.bonus_action_used = True

        # ----- 1. MOVEMENT -----
        move_step = self._decide_movement(entity, enemies, allies, battle)
        if move_step:
            plan.steps.append(move_step)

        # ----- 1.5. REVIVE ALLY (Action) -----
        revive_step = self._try_revive_ally_spell(entity, allies, battle, action_type="action")
        if revive_step:
            plan.steps.append(revive_step)
            entity.action_used = True

        # ----- 1.5. AOE ACTION (Breath Weapon etc) -----
        aoe_action_step = self._try_aoe_action(entity, enemies, allies, battle)
        if aoe_action_step:
            plan.steps.append(aoe_action_step)
            entity.action_used = True

        # ----- 2. MAIN ACTION -----
        action_steps = self._decide_action(entity, enemies, allies, battle)
        if action_steps:
            plan.steps.extend(action_steps)

            # ----- 2.5. ACTION SURGE (Fighter) -----
            if entity.has_feature("action_surge") and entity.can_use_feature("Action Surge"):
                # Use if we took an offensive action and enemies are still present
                took_offense = any(s.step_type in ("attack", "spell", "multiattack") for s in action_steps)
                if took_offense:
                    entity.use_feature("Action Surge")
                    entity.action_used = False  # Reset action flag for the surge
                    surge_steps = self._decide_action(entity, enemies, allies, battle)
                    if surge_steps:
                        plan.steps.append(ActionStep(step_type="wait", description=f"{entity.name} uses Action Surge!", attacker=entity))
                        plan.steps.extend(surge_steps)

        # ----- 3. BONUS ACTION -----
        if not entity.bonus_action_used:
            bonus_steps = self._decide_bonus_action(entity, enemies, allies, battle, plan)
            if bonus_steps:
                plan.steps.extend(bonus_steps)

        if not plan.steps:
            plan.skipped = True
            plan.skip_reason = "Nothing to do"

        return plan

    # ------------------------------------------------------------------ #
    # Lair Actions                                                         #
    # ------------------------------------------------------------------ #

    def _handle_lair_turn(self, entity, battle, plan):
        owner = entity.lair_owner
        if not owner or owner.hp <= 0:
            plan.skipped = True
            plan.skip_reason = "Lair owner defeated"
            return plan

        lair_actions = [a for a in owner.stats.actions if a.action_type == "lair"]
        if not lair_actions:
            plan.skipped = True
            plan.skip_reason = "No lair actions found"
            return plan

        action = random.choice(lair_actions)
        enemies = battle.get_enemies_of(owner)

        if action.aoe_radius > 0:
            clusters = self._best_aoe_cluster(owner, enemies, allies=[], battle=battle,
                                               radius_ft=action.aoe_radius, shape=action.aoe_shape)
            if clusters:
                cx, cy = self._cluster_center(clusters)
                raw_dmg = roll_dice(action.damage_dice)
                step = ActionStep(
                    step_type="legendary",
                    description=f"[LAIR] {owner.name} uses {action.name}",
                    attacker=owner, targets=clusters, action=action, damage=raw_dmg,
                    damage_type=action.damage_type, action_name=action.name,
                    aoe_center=(cx, cy),
                    save_dc=action.condition_dc, save_ability=action.condition_save
                )
                plan.steps.append(step)
                return plan

        target = self._pick_target(owner, enemies)
        if target:
            step = self._execute_attack(owner, action, target, battle)
            step.step_type = "legendary"
            step.description = f"[LAIR] {step.description}"
            plan.steps.append(step)
            return plan

        plan.skipped = True
        plan.skip_reason = "No valid targets for Lair Action"
        return plan

    # ------------------------------------------------------------------ #
    # Summon Turn (Spiritual Weapon, etc.)                                 #
    # ------------------------------------------------------------------ #

    def _handle_summon_turn(self, entity, battle, plan):
        """Summons like Spiritual Weapon make a bonus-action attack each turn."""
        if not entity.summon_owner or entity.summon_owner.hp <= 0:
            plan.skipped = True
            plan.skip_reason = "Owner defeated"
            return plan

        # Check duration (decremented in battle.next_turn)
        if entity.summon_rounds_left <= 0:
            plan.skipped = True
            plan.skip_reason = f"{entity.name} expires"
            return plan

        enemies = battle.get_enemies_of(entity)
        target = self._pick_target(entity, enemies)
        if not target:
            plan.skipped = True
            plan.skip_reason = "No targets"
            return plan

        # Move summon adjacent to target
        if not battle.is_adjacent(entity, target):
            move_step = self._move_summon_to_target(entity, target, battle)
            if move_step:
                plan.steps.append(move_step)

        # Attack
        if battle.is_adjacent(entity, target) or entity.stats.actions:
            actions = entity.stats.actions
            if actions:
                step = self._execute_attack(entity, actions[0], target, battle)
                step.description = f"[SUMMON] {step.description}"
                plan.steps.append(step)

        if not plan.steps:
            plan.skipped = True
            plan.skip_reason = "Cannot reach target"

        return plan

    def _move_summon_to_target(self, entity, target, battle):
        """Simple movement for summons - teleport adjacent to target."""
        # Spiritual Weapon can move 20ft as part of its bonus action
        start_x, start_y = entity.grid_x, entity.grid_y
        # Find adjacent free spot to target
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = target.grid_x + dx, target.grid_y + dy
                if battle.is_passable(nx, ny, exclude=entity):
                    entity.grid_x, entity.grid_y = nx, ny
                    dist = math.hypot(nx - start_x, ny - start_y) * 5
                    return ActionStep(
                        step_type="move",
                        description=f"[SUMMON] {entity.name} moves to ({nx},{ny})",
                        attacker=entity, new_x=nx, new_y=ny,
                        movement_ft=dist, old_x=start_x, old_y=start_y,
                    )
        return None

    # ------------------------------------------------------------------ #
    # Barbarian Rage                                                       #
    # ------------------------------------------------------------------ #

    def _try_start_rage(self, entity, enemies, allies, battle):
        """Smart rage activation for Barbarians."""
        if not entity.has_feature("rage") or entity.rage_active:
            return None
        if entity.rages_left <= 0:
            return None

        # AI decision: when to rage?
        # 1. Always rage if enemies are close (melee is about to happen)
        # 2. Don't rage if no enemies within 60ft (waste)
        # 3. Rage if we're about to take damage (tanking)
        closest_enemy_dist = min(
            (battle.get_distance(entity, e) * 5 for e in enemies if e.hp > 0),
            default=999
        )

        # Don't rage if enemies are very far
        if closest_enemy_dist > 60:
            return None

        # Don't rage if we're very healthy and there's only 1 weak enemy
        if (entity.hp > entity.max_hp * 0.8 and
                len([e for e in enemies if e.hp > 0]) == 1 and
                enemies[0].hp < entity.hp * 0.3):
            return None

        # Rage!
        entity.start_rage()
        return ActionStep(
            step_type="bonus_attack",
            description=f"{entity.name} enters a RAGE! (Resistance to B/P/S, "
                        f"+{entity.get_rage_damage_bonus()} melee damage)",
            attacker=entity, action_name="Rage",
        )

    def _try_cunning_hide(self, entity, enemies, battle):
        """Rogue Cunning Action: Hide to gain advantage."""
        # 1. Can't hide if threatened (adjacent to enemy)
        if any(battle.is_adjacent(entity, e) for e in enemies if e.hp > 0):
            return None

        # 2. Pick intended target to see if we already have advantage
        target = self._pick_target(entity, enemies)
        if not target:
            return None

        # If we already have advantage, no need to hide
        if entity.has_attack_advantage(target, is_ranged=True):
            return None

        # 3. Attempt Hide (Stealth Check vs Passive Perception)
        stealth_roll = roll_dice("1d20") + entity.get_skill_bonus("Stealth") + entity.get_modifier("Dexterity")
        # Estimate Passive Perception (10 + bonus)
        pp = 10 + target.get_skill_bonus("Perception")

        if stealth_roll >= pp:
            # Success: Gain Invisible condition (simulates Hidden)
            entity.add_condition("Invisible")
            return ActionStep(
                step_type="bonus_attack",
                description=f"{entity.name} uses Cunning Action to Hide (Stealth {stealth_roll} vs PP {pp}).",
                attacker=entity,
                action_name="Hide"
            )
        return None

    # ------------------------------------------------------------------ #
    # Movement                                                             #
    # ------------------------------------------------------------------ #

    def _get_combat_preference(self, entity):
        """Determine if entity prefers Melee or Ranged combat."""
        stats = entity.stats
        
        # 1. Check stats (Mental vs Physical)
        phys = max(stats.abilities.strength, stats.abilities.dexterity)
        ment = max(stats.abilities.intelligence, stats.abilities.wisdom, stats.abilities.charisma)
        
        # 2. Check capabilities
        has_melee_action = any(a.range <= 5 for a in stats.actions)
        has_ranged_action = any(a.range > 10 for a in stats.actions)
        has_ranged_spells = any(s.range > 10 and s.damage_dice for s in stats.spells_known)
        
        if not has_melee_action: return "ranged"
        if not (has_ranged_action or has_ranged_spells): return "melee"
        
        # Hybrids: lean towards higher stat (e.g. Lich INT 20 > STR 11 -> Ranged)
        if ment > phys + 2: return "ranged"
        return "melee"

    def _decide_movement(self, entity, enemies, allies, battle):
        if not entity.can_move() or entity.movement_left <= 0:
            return None

        # 0. Emergency: Move to dying ally if we have touch healing
        dying_allies = [a for a in allies if a.hp <= 0 and not a.is_stable and not a.is_summon]
        if dying_allies:
            # Check if we have touch healing (Lay on Hands or Cure Wounds)
            if self._has_touch_healing(entity):
                closest_dying = min(dying_allies, key=lambda a: battle.get_distance(entity, a))
                if not battle.is_adjacent(entity, closest_dying):
                    return self._move_toward(entity, closest_dying, allies, battle)

        # Stand up from prone first
        if entity.has_condition("Prone"):
            entity.remove_condition("Prone")
            return ActionStep(
                step_type="wait",
                description=f"{entity.name} stands up (uses half speed).",
                attacker=entity,
            )

        target = self._pick_target(entity, enemies)
        dist = battle.get_distance(entity, target)
        actions = entity.stats.actions or []
        spells = entity.stats.spells_known or []
        has_aoe = any(s.aoe_radius > 0 for s in spells)
        
        preference = self._get_combat_preference(entity)

        # --- ESCAPE LOGIC (Teleport) ---
        # If stuck in melee and prefers ranged, try to Misty Step out
        if preference == "ranged" and dist <= 1.5 and not entity.bonus_action_used:
            misty = next((s for s in spells if s.name == "Misty Step"), None)
            if misty and entity.has_spell_slot(misty.level):
                # Teleport away
                tele_step = self._try_teleport_escape(entity, target, battle, misty)
                if tele_step:
                    entity.bonus_action_used = True
                    # We used movement logic to cast a spell, so we return it
                    return tele_step

        # If we want melee
        if preference == "melee":
            # Check for smart positioning (AoE avoidance)
            spread_dest = self._find_spread_out_destination(entity, target, allies, battle)
            
            if dist > 0.5:
                return self._move_toward(entity, target, allies, battle, spread_dest)
            elif spread_dest:
                # Already adjacent, but maybe in a bad spot (clumped)
                if int(entity.grid_x) != spread_dest[0] or int(entity.grid_y) != spread_dest[1]:
                    return self._move_toward(entity, target, allies, battle, spread_dest)

        # If we want ranged
        if preference == "ranged":
            # Too close? (within 15ft)
            if dist < 3.0:
                return self._move_away(entity, target, battle)
            # Too far? (over 60ft)
            elif dist > 12.0:
                return self._move_toward(entity, target, allies, battle)

        # AoE caster: position for best cluster
        if has_aoe and preference == "ranged":
            result = self._best_aoe_cluster(entity, enemies, allies, battle, 20)
            if result and len(result[0]) >= 2:
                cluster, (cx, cy) = result
                return self._move_toward_point(entity, cx, cy, battle)

        return None

    def _has_touch_healing(self, entity):
        """Check if entity has a way to heal adjacent allies."""
        if entity.lay_on_hands_left > 0:
            return True
        for spell in entity.stats.spells_known:
            if spell.heals and spell.range <= 5 and entity.has_spell_slot(spell.level):
                return True
        # Potions?
        return False

    def _is_safe_passable(self, battle, x, y, entity):
        if not battle.is_passable(x, y, exclude=entity):
            return False
        t = battle.get_terrain_at(int(x), int(y))
        if t and t.is_hazard:
            return False
        return True

    def _find_path(self, start, end, battle, entity):
        """A* Pathfinding to find optimal path around obstacles."""
        def heuristic(a, b):
            return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}

        if start == end:
            return []

        visited = set()

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == end:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                return path[::-1]

            if current in visited:
                continue
            visited.add(current)

            cx, cy = current
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = cx + dx, cy + dy
                    neighbor = (nx, ny)

                    if not self._is_safe_passable(battle, nx, ny, entity):
                        continue

                    move_cost = battle.get_terrain_movement_cost(nx, ny)
                    tentative_g = g_score[current] + move_cost

                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        f = tentative_g + heuristic(neighbor, end)
                        heapq.heappush(open_set, (f, neighbor))
        return None

    def _move_toward(self, entity, target, allies, battle, forced_dest=None):
        if forced_dest:
            dest_x, dest_y = forced_dest
        else:
            flank = self._flanking_position(entity, target, allies, battle)
            dest_x = flank[0] if flank else target.grid_x
            dest_y = flank[1] if flank else target.grid_y

        if not battle.is_passable(dest_x, dest_y, exclude=entity):
            valid_adj = []
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = int(dest_x + dx), int(dest_y + dy)
                    if self._is_safe_passable(battle, nx, ny, entity):
                        valid_adj.append((nx, ny))
            if valid_adj:
                dest_x, dest_y = min(valid_adj, key=lambda p: math.hypot(p[0] - entity.grid_x, p[1] - entity.grid_y))
            else:
                return None

        start_x, start_y = entity.grid_x, entity.grid_y
        start_movement = entity.movement_left

        start_node = (int(entity.grid_x), int(entity.grid_y))
        end_node = (int(dest_x), int(dest_y))
        path = self._find_path(start_node, end_node, battle, entity)

        if path:
            for (nx, ny) in path:
                cost = 5.0 * battle.get_terrain_movement_cost(nx, ny)
                if entity.movement_left < cost:
                    break
                entity.grid_x, entity.grid_y = nx, ny
                entity.movement_left -= cost
                if battle.is_adjacent(entity, target):
                    break

        moved_cost = start_movement - entity.movement_left
        dist_moved = math.hypot(entity.grid_x - start_x, entity.grid_y - start_y)

        if dist_moved < 0.1:
            return None

        return ActionStep(
            step_type="move",
            description=f"{entity.name} moves {moved_cost:.0f} ft.",
            attacker=entity,
            new_x=entity.grid_x, new_y=entity.grid_y,
            movement_ft=moved_cost, old_x=start_x, old_y=start_y,
        )

    def _try_teleport_escape(self, entity, threat, battle, spell):
        """Use Misty Step or similar to teleport away from threat."""
        # Find a spot 30ft away that is safe
        best_spot = None
        best_dist = 0
        
        # Check points in a circle around entity
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            tx = entity.grid_x + math.cos(rad) * 6  # 30ft = 6 squares
            ty = entity.grid_y + math.sin(rad) * 6
            if battle.is_passable(int(tx), int(ty)):
                d = math.hypot(tx - threat.grid_x, ty - threat.grid_y)
                if d > best_dist:
                    best_dist = d
                    best_spot = (int(tx), int(ty))
        
        if best_spot:
            entity.use_spell_slot(spell.level)
            entity.grid_x, entity.grid_y = best_spot
            return ActionStep(step_type="spell", description=f"{entity.name} casts {spell.name} to escape!", attacker=entity, spell=spell, slot_used=spell.level, action_name=spell.name)
        return None

    def _move_toward_point(self, entity, tx, ty, battle):
        start_x, start_y = entity.grid_x, entity.grid_y
        start_movement = entity.movement_left

        dest_x, dest_y = tx, ty
        if not battle.is_passable(dest_x, dest_y, exclude=entity):
            valid_adj = []
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = int(dest_x + dx), int(dest_y + dy)
                    if self._is_safe_passable(battle, nx, ny, entity):
                        valid_adj.append((nx, ny))
            if valid_adj:
                dest_x, dest_y = min(valid_adj, key=lambda p: math.hypot(p[0] - entity.grid_x, p[1] - entity.grid_y))

        path = self._find_path((int(entity.grid_x), int(entity.grid_y)),
                               (int(dest_x), int(dest_y)), battle, entity)

        if path:
            for (nx, ny) in path:
                cost = 5.0 * battle.get_terrain_movement_cost(nx, ny)
                if entity.movement_left < cost:
                    break
                entity.grid_x, entity.grid_y = nx, ny
                entity.movement_left -= cost

        moved_cost = start_movement - entity.movement_left
        dist_moved = math.hypot(entity.grid_x - start_x, entity.grid_y - start_y)

        if dist_moved < 0.1:
            return None

        return ActionStep(
            step_type="move",
            description=f"{entity.name} repositions {moved_cost:.0f} ft.",
            attacker=entity, new_x=entity.grid_x, new_y=entity.grid_y,
            movement_ft=moved_cost, old_x=start_x, old_y=start_y)

    def _move_away(self, entity, threat, battle):
        start_x, start_y = entity.grid_x, entity.grid_y
        start_movement = entity.movement_left

        while entity.movement_left >= 5.0:
            dx = entity.grid_x - threat.grid_x
            dy = entity.grid_y - threat.grid_y

            move_1 = (0, 0)
            move_2 = (0, 0)

            if abs(dx) >= abs(dy):
                move_1 = (1 if dx >= 0 else -1, 0)
                move_2 = (0, 1 if dy >= 0 else -1)
            else:
                move_1 = (0, 1 if dy >= 0 else -1)
                move_2 = (1 if dx >= 0 else -1, 0)

            nx, ny = entity.grid_x + move_1[0], entity.grid_y + move_1[1]
            chosen = None
            if self._is_safe_passable(battle, nx, ny, entity):
                chosen = (nx, ny)
            else:
                nx2, ny2 = entity.grid_x + move_2[0], entity.grid_y + move_2[1]
                if self._is_safe_passable(battle, nx2, ny2, entity):
                    chosen = (nx2, ny2)

            if chosen:
                cost = 5.0 * battle.get_terrain_movement_cost(chosen[0], chosen[1])
                if entity.movement_left >= cost:
                    entity.grid_x, entity.grid_y = chosen
                    entity.movement_left -= cost
                else:
                    break
            else:
                break

        moved_cost = start_movement - entity.movement_left
        dist_moved = math.hypot(entity.grid_x - start_x, entity.grid_y - start_y)

        if dist_moved < 0.1:
            return None

        return ActionStep(
            step_type="move",
            description=f"{entity.name} disengages and moves {moved_cost:.0f} ft.",
            attacker=entity, new_x=entity.grid_x, new_y=entity.grid_y,
            movement_ft=moved_cost, old_x=start_x, old_y=start_y)

    # ------------------------------------------------------------------ #
    # Main Action                                                          #
    # ------------------------------------------------------------------ #

    def _decide_action(self, entity, enemies, allies, battle) -> List[ActionStep]:
        if entity.action_used:
            return []

        # Paladin: Lay on Hands (Revive dying ally)
        if entity.lay_on_hands_left >= 1:
            loh_steps = self._try_lay_on_hands(entity, allies, battle)
            if loh_steps:
                entity.action_used = True
                return loh_steps

        # Cleric: Turn Undead
        if entity.has_feature("channel_divinity") and entity.channel_divinity_left > 0:
            tu_step = self._try_turn_undead(entity, enemies, battle)
            if tu_step:
                entity.action_used = True
                entity.channel_divinity_left -= 1
                return [tu_step]

        # Self-heal if critical and has healing ability
        if entity.max_hp > 0 and (entity.hp / entity.max_hp < 0.25):
            heal_step = self._try_heal_action(entity)
            if heal_step:
                entity.action_used = True
                return [heal_step]

        # Self-buff for defense (Mirror Image, etc.) if threatened
        buff_step = self._try_self_buff(entity, enemies, battle)
        if buff_step:
            entity.action_used = True
            return [buff_step]

        # Second Wind (Fighter) if hurt
        if entity.max_hp > 0 and (entity.hp / entity.max_hp < 0.5):
            sw_step = self._try_second_wind(entity)
            if sw_step:
                # Second Wind is a bonus action, don't use main action
                pass

        # Disengage if critical and threatened (only for non-melee or squishy characters)
        # Smart enemies (INT > 12) disengage earlier (50% HP) if they are ranged
        pref = self._get_combat_preference(entity)
        hp_threshold = 0.5 if (entity.stats.abilities.intelligence > 12 and pref == "ranged") else 0.25
        
        if entity.max_hp > 0 and (entity.hp / entity.max_hp < hp_threshold):
            disengage_step = self._try_disengage_action(entity, enemies, battle, pref)
            if disengage_step:
                entity.action_used = True
                return [disengage_step]

        # AoE spell if 3+ enemies grouped (but don't hit allies!)
        if entity.has_spell_slot(1) or entity.stats.cantrips:
            aoe_step = self._try_aoe_spell(entity, enemies, allies, battle)
            if aoe_step:
                entity.action_used = True
                return [aoe_step]

        # Debuff spell (high-value target)
        if entity.has_spell_slot(1):
            debuff_step = self._try_debuff_spell(entity, enemies, battle)
            if debuff_step:
                entity.action_used = True
                return [debuff_step]

        # Best damage spell / cantrip
        if entity.stats.spells_known or entity.stats.cantrips:
            spell_step = self._try_damage_spell(entity, enemies, battle)
            if spell_step:
                entity.action_used = True
                return [spell_step]

        # Multiattack (with class mechanic bonuses)
        multi = next((a for a in entity.stats.actions if a.is_multiattack), None)
        if multi:
            steps = self._execute_multiattack(entity, multi, enemies, allies, battle)
            entity.action_used = True
            return steps

        # Single best attack
        alive_enemies = [e for e in enemies if e.hp > 0]
        sorted_enemies = sorted(alive_enemies, key=lambda e: self._score_target(entity, e), reverse=True)

        for target in sorted_enemies:
            if battle.is_adjacent(entity, target):
                engaging_allies = [a for a in allies if battle.is_adjacent(a, target)]
                str_score = entity.stats.abilities.strength

                if not target.has_condition("Prone") and (len(engaging_allies) >= 1 or str_score >= 14):
                    if random.random() < 0.3:
                        shove_step = self._try_shove_action(entity, target)
                        if shove_step:
                            entity.action_used = True
                            return [shove_step]

                if not target.has_condition("Grappled"):
                    can_grapple = str_score >= 12 or (str_score >= 10 and len(engaging_allies) >= 1)
                    if can_grapple and random.random() < 0.2:
                        grapple_step = self._try_grapple_action(entity, target)
                        if grapple_step:
                            entity.action_used = True
                            return [grapple_step]

            best_action = self._best_melee_or_ranged(entity, target, battle)
            if best_action:
                # Consume usage if applicable
                if entity.get_feature_by_name(best_action.name):
                    entity.use_feature(best_action.name)

                step = self._execute_attack(entity, best_action, target, battle)
                # Apply class bonuses to single attacks too
                self._apply_class_attack_bonuses(entity, step, target, allies, battle)
                entity.action_used = True
                return [step]

        return self._try_dash_action(entity, enemies, allies, battle)

    def _try_self_buff(self, entity, enemies, battle):
        """Cast a defensive self-buff if enemies are nearby."""
        # Only buff if enemies are somewhat close (within 60ft)
        closest_dist = min((battle.get_distance(entity, e) * 5 for e in enemies if e.hp > 0), default=999)
        if closest_dist > 60:
            return None

        buffs = ["Mirror Image", "Blur", "Fire Shield", "Armor of Agathys", "Mage Armor", "Blink"]
        
        for spell in entity.stats.spells_known:
            if spell.name in buffs and spell.targets == "self":
                # Don't cast if already active
                if spell.name in entity.active_effects:
                    continue
                if spell.concentration and entity.concentrating_on:
                    continue
                
                if entity.use_spell_slot(spell.level):
                    if spell.concentration:
                        entity.start_concentration(spell)
                    return ActionStep(step_type="spell", description=f"{entity.name} casts {spell.name} on self.",
                                      attacker=entity, target=entity, spell=spell, slot_used=spell.level, action_name=spell.name)
        return None

    def _try_aoe_action(self, entity, enemies, allies, battle):
        """Try to use a non-spell AoE action (like Breath Weapon)."""
        if entity.action_used:
            return None

        aoe_actions = [a for a in entity.stats.actions if a.aoe_radius > 0 and a.damage_dice]
        if not aoe_actions:
            return None

        best_step = None
        best_total_dmg = 0.0

        for action in aoe_actions:
            # Check if this action is limited by a feature (e.g. Dragon Breath)
            if entity.get_feature_by_name(action.name):
                if not entity.can_use_feature(action.name):
                    continue

            result = self._best_aoe_cluster(entity, enemies, allies, battle, action.aoe_radius, shape=action.aoe_shape, damage_type=action.damage_type)
            if not result:
                continue
            clusters, (cx, cy) = result
            
            # Allow single target for powerful AoEs (Breath Weapons)
            min_targets = 2
            if average_damage(action.damage_dice) > 25:
                min_targets = 1

            if not clusters or len(clusters) < min_targets:
                continue

            # Calculate total expected damage considering vulnerabilities/saves
            total_dmg = 0.0
            for t in clusters:
                base = self._estimate_damage(action.damage_dice, action.damage_type, t)
                # Estimate save (simplified)
                if action.condition_save:
                    # Assume 50% chance to fail save for estimation
                    total_dmg += base * 0.75 # (1.0 + 0.5) / 2 roughly
                else:
                    total_dmg += base
            
            if total_dmg > best_total_dmg:
                best_total_dmg = total_dmg
                # Consume usage if applicable
                if entity.get_feature_by_name(action.name):
                    # We don't use it here, just mark we would
                    pass

                raw_dmg = roll_dice(action.damage_dice)
                best_step = ActionStep(
                    step_type="attack",
                    description=f"{entity.name} uses {action.name} (DC {action.condition_dc or '??'} {action.condition_save})",
                    attacker=entity, targets=clusters, action=action, damage=raw_dmg,
                    damage_type=action.damage_type, action_name=action.name, aoe_center=(cx, cy),
                    save_dc=action.condition_dc, save_ability=action.condition_save
                )

        if best_step:
            # Consume usage if applicable
            if entity.get_feature_by_name(best_step.action.name):
                entity.use_feature(best_step.action.name)
            return best_step
            
        return None

    def _try_revive_ally_spell(self, entity, allies, battle, action_type="action") -> Optional[ActionStep]:
        """Try to revive a dying ally with a healing spell."""
        # 1. Find dying allies
        dying_allies = [a for a in allies if a.hp <= 0 and not a.is_stable and not a.is_summon]
        if not dying_allies:
            return None

        # 2. Find healing spells of correct action type
        healing_spells = [s for s in entity.stats.spells_known 
                          if s.heals and s.action_type == action_type]
        
        if not healing_spells:
            return None

        # Sort by level (lowest first)
        healing_spells.sort(key=lambda s: s.level)

        for spell in healing_spells:
            # Check slots
            if spell.level > 0 and not entity.has_spell_slot(spell.level):
                continue
            
            # Find reachable target
            for target in dying_allies:
                dist_ft = battle.get_distance(entity, target) * 5
                if dist_ft > spell.range:
                    continue

                slot = spell.level
                if slot > 0:
                    entity.use_spell_slot(slot)
                
                healed = roll_dice(spell.heals)
                step_type = "spell" if action_type == "action" else "bonus_attack"
                
                return ActionStep(
                    step_type=step_type,
                    description=f"{entity.name} casts {spell.name} on dying {target.name}, healing {healed} HP!",
                    attacker=entity, target=target, spell=spell, slot_used=slot,
                    action_name=spell.name, damage=healed, damage_type="healing"
                )
        return None

    def _try_heal_action(self, entity):
        for spell in entity.stats.spells_known:
            if spell.heals and (spell.targets == "self" or spell.range == 0):
                slot = entity.get_slot_for_level(spell.level) if spell.level > 0 else 0
                if spell.level == 0 or entity.use_spell_slot(spell.level):
                    healed = roll_dice(spell.heals)
                    return ActionStep(
                        step_type="spell",
                        description=f"{entity.name} casts {spell.name} on self, healing {healed} HP.",
                        attacker=entity, target=entity, spell=spell,
                        slot_used=slot, action_name=spell.name,
                        damage=healed, damage_type="healing"
                    )
        for item in entity.items:
            if item.heals and item.uses > 0:
                item.uses -= 1
                healed = roll_dice(item.heals)
                return ActionStep(
                    step_type="bonus_attack",
                    description=f"{entity.name} uses {item.name}, healing {healed} HP.",
                    attacker=entity, target=entity, action_name=item.name,
                    damage=healed, damage_type="healing"
                )
        return None

    def _try_second_wind(self, entity):
        """Fighter's Second Wind: bonus action heal."""
        feat = entity.get_feature("second_wind")
        if not feat or not entity.can_use_feature("Second Wind"):
            return None
        if entity.bonus_action_used:
            return None
        # Only use if below 50% HP
        if entity.hp > entity.max_hp * 0.5:
            return None

        heal_dice = feat.mechanic_value or "1d10"
        level_bonus = entity.stats.character_level
        healed = roll_dice(heal_dice) + level_bonus
        entity.use_feature("Second Wind")
        entity.bonus_action_used = True
        return ActionStep(
            step_type="bonus_attack",
            description=f"{entity.name} uses Second Wind, healing {healed} HP.",
            attacker=entity, target=entity, action_name="Second Wind",
            damage=healed, damage_type="healing"
        )

    def _try_disengage_action(self, entity, enemies, battle, preference="melee"):
        threats = [e for e in enemies if battle.is_adjacent(entity, e)]
        # Melee fighters rarely disengage unless very critical, Ranged do it more often
        if preference == "melee" and entity.hp > entity.max_hp * 0.2:
            return None
        if not threats:
            return None

        threat = threats[0]
        entity.movement_left += entity.stats.speed
        move_step = self._move_away(entity, threat, battle)

        if move_step:
            move_step.description = f"{entity.name} Disengages (Action) and retreats."
            move_step.step_type = "move"
            return move_step
        return None

    def _try_dash_action(self, entity, enemies, allies, battle):
        target = self._pick_target(entity, enemies)
        if not target:
            return []
        entity.movement_left += entity.stats.speed
        step = self._move_toward(entity, target, allies, battle)
        if step:
            step.description = f"{entity.name} Dashes (Action): " + step.description
            entity.action_used = True
            return [step]
        return []

    def _try_grapple_action(self, entity, target):
        prof = entity.stats.proficiency_bonus
        dc = 8 + entity.get_modifier("Strength") + prof
        desc = f"{entity.name} attempts to Grapple {target.name} (DC {dc} STR/DEX check)"
        return ActionStep(
            step_type="attack", description=desc,
            attacker=entity, target=target, action_name="Grapple",
            applies_condition="Grappled", condition_dc=dc, save_ability="Strength"
        )

    def _try_shove_action(self, entity, target):
        prof = entity.stats.proficiency_bonus
        dc = 8 + entity.get_modifier("Strength") + prof
        desc = f"{entity.name} attempts to Shove {target.name} Prone (DC {dc} STR/DEX check)"
        return ActionStep(
            step_type="attack", description=desc,
            attacker=entity, target=target, action_name="Shove",
            applies_condition="Prone", condition_dc=dc, save_ability="Strength"
        )

    def _try_aoe_spell(self, entity, enemies, allies, battle):
        """Cast best AoE spell if cluster >= threshold enemies, avoiding allies."""
        aoe_spells = [s for s in entity.stats.spells_known if s.aoe_radius > 0 and s.damage_dice]
        if not aoe_spells:
            return None

        # Can this caster sculpt spells? (Evocation Wizard)
        can_sculpt = entity.has_feature("sculpt_spells")

        best_step = None
        best_total_dmg = 0.0

        for spell in aoe_spells:
            if spell.level == 0:
                continue
            threshold = 3 if average_damage(spell.damage_dice) < 20 else 2
            result = self._best_aoe_cluster(entity, enemies, allies, battle,
                                               spell.aoe_radius,
                                               shape=spell.aoe_shape,
                                               avoid_allies=not can_sculpt,
                                               damage_type=spell.damage_type)
            if not result:
                continue
            clusters, (cx, cy) = result
            if not clusters or len(clusters) < threshold:
                continue
            
            # Calculate total expected damage
            total_dmg = 0.0
            for t in clusters:
                base = self._estimate_damage(spell.damage_dice, spell.damage_type, t)
                # Adjust for save
                if spell.save_ability:
                    # Check target save bonus
                    save_bonus = t.get_save_bonus(spell.save_ability)
                    dc = spell.save_dc_fixed or (entity.stats.spell_save_dc or 13)
                    fail_chance = 1.0 - ((21 + save_bonus - dc) / 20.0)
                    fail_chance = max(0.05, min(0.95, fail_chance))
                    
                    if spell.half_on_save:
                        total_dmg += base * fail_chance + (base / 2.0) * (1.0 - fail_chance)
                    else:
                        total_dmg += base * fail_chance
            
            if total_dmg > best_total_dmg:
                best_total_dmg = total_dmg
                best_step = (spell, clusters, cx, cy)

        if best_step:
            spell, clusters, cx, cy = best_step
            if entity.use_spell_slot(spell.level):
                slot = spell.level
                dc = spell.save_dc_fixed if spell.save_dc_fixed else \
                     (entity.stats.spell_save_dc or 8 + entity.stats.proficiency_bonus
                      + entity.get_modifier(entity.stats.spellcasting_ability))

                raw_dmg = roll_dice(spell.damage_dice)

                # Empowered Evocation: add INT mod to evocation damage
                if entity.has_feature("empowered_evocation"):
                    raw_dmg += entity.get_modifier("intelligence")

                # Elemental Affinity (Sorcerer): add CHA mod to matching element
                if entity.has_feature("elemental_affinity"):
                    raw_dmg += entity.get_modifier("charisma")

                if spell.concentration:
                    entity.start_concentration(spell)

                return ActionStep(
                    step_type="spell",
                    description=f"{entity.name} casts {spell.name} (DC {dc} {spell.save_ability})",
                    attacker=entity, targets=clusters, spell=spell, slot_used=slot,
                    damage=raw_dmg, damage_type=spell.damage_type,
                    action_name=spell.name, aoe_center=(cx, cy),
                    save_dc=dc if dc else 0,
                    save_ability=spell.save_ability,
                )
        return None

    def _try_debuff_spell(self, entity, enemies, battle):
        debuff_spells = [s for s in entity.stats.spells_known
                         if s.applies_condition and not s.damage_dice
                         and s.targets == "single"]
        if not debuff_spells:
            return None
        debuff_spells.sort(key=lambda s: s.level, reverse=True)
        for spell in debuff_spells:
            if not entity.has_spell_slot(spell.level):
                continue
            candidates = [e for e in enemies
                          if not e.has_condition(spell.applies_condition) and e.hp > 0]
            # Filter out immune targets
            if spell.applies_condition:
                candidates = [e for e in candidates if spell.applies_condition not in e.stats.condition_immunities]
            if not candidates:
                continue
            # Pick target with lowest save bonus (highest chance to fail)
            # Tie-break with HP (prefer disabling high HP targets)
            target = min(candidates, key=lambda e: (e.get_save_bonus(spell.save_ability), -e.hp))
            
            dist = battle.get_distance(entity, target) * 5
            if dist > spell.range:
                continue
            entity.use_spell_slot(spell.level)
            slot = spell.level
            dc = spell.save_dc_fixed if spell.save_dc_fixed else \
                 (entity.stats.spell_save_dc or 8 + entity.stats.proficiency_bonus
                  + entity.get_modifier(entity.stats.spellcasting_ability))

            desc = f"{entity.name} casts {spell.name} on {target.name} (DC {dc} {spell.save_ability})"
            if spell.concentration:
                entity.start_concentration(spell)
            return ActionStep(
                step_type="spell", description=desc,
                attacker=entity, target=target, spell=spell, slot_used=slot,
                action_name=spell.name, save_dc=dc, save_ability=spell.save_ability,
                applies_condition=spell.applies_condition,
            )
        return None

    def _try_damage_spell(self, entity, enemies, battle):
        all_spells = entity.stats.spells_known + entity.stats.cantrips
        damage_spells = [s for s in all_spells if s.damage_dice and s.targets == "single"]
        if not damage_spells:
            return None

        best_step = None
        best_ev = -1.0

        for spell in damage_spells:
            if spell.level > 0 and not entity.has_spell_slot(spell.level):
                continue
            
            # Calculate spell DC and Attack Bonus once
            dc = spell.save_dc_fixed if spell.save_dc_fixed else \
                 (entity.stats.spell_save_dc or 8 + entity.stats.proficiency_bonus
                  + entity.get_modifier(entity.stats.spellcasting_ability))
            atk_bonus = (spell.attack_bonus_fixed or
                         (entity.stats.spell_attack_bonus or
                          entity.stats.proficiency_bonus + entity.get_modifier(entity.stats.spellcasting_ability)))

            # Bonuses
            extra = 0
            if spell.name == "Eldritch Blast" and entity.has_feature("agonizing_blast"):
                extra = entity.get_modifier("charisma")
            if entity.has_feature("empowered_evocation"):
                extra += entity.get_modifier("intelligence")

            # Find best target for this spell based on Expected Value (EV)
            for target in enemies:
                if target.hp <= 0: continue
                
                # Calculate damage against THIS target (vulnerability/resistance)
                base_dmg = self._estimate_damage(spell.damage_dice, spell.damage_type, target)
                if base_dmg <= 0: continue
                base_dmg += extra

                dist = battle.get_distance(entity, target) * 5
                if dist > spell.range: continue

                # Check if caster is threatened (enemy within 5ft) for ranged spells
                is_threatened = False
                if spell.action_type != "save": # Attack roll spells
                    enemies_adj = [e for e in enemies if battle.is_adjacent(e, entity)]
                    if enemies_adj: is_threatened = True

                ev = 0.0
                if spell.save_ability:
                    # Check target weakness (Save Bonus)
                    save_bonus = target.get_save_bonus(spell.save_ability)
                    # Chance to fail = 1 - (21 + bonus - DC)/20
                    fail_chance = 1.0 - ((21 + save_bonus - dc) / 20.0)
                    fail_chance = max(0.05, min(0.95, fail_chance))
                    
                    if spell.half_on_save:
                        ev = base_dmg * fail_chance + (base_dmg / 2.0) * (1.0 - fail_chance)
                    else:
                        ev = base_dmg * fail_chance
                else:
                    # Attack Roll
                    hit_chance = (21 + atk_bonus - target.stats.armor_class) / 20.0
                    adv = entity.has_attack_advantage(target, is_ranged=True)
                    dis = entity.has_attack_disadvantage(target, is_ranged=True, is_threatened=is_threatened)
                    if adv and not dis: hit_chance = 1 - (1-hit_chance)**2
                    if dis and not adv: hit_chance = hit_chance**2
                    hit_chance = max(0.05, min(0.95, hit_chance))
                    ev = base_dmg * hit_chance

                # Bonus for killing blow
                if base_dmg >= target.hp:
                    ev *= 1.2

                if ev > best_ev:
                    best_ev = ev
                    best_step = (spell, target, dc, atk_bonus, extra)

        if best_step:
            spell, target, dc, atk_bonus, extra = best_step
            slot = spell.level
            if spell.level > 0:
                entity.use_spell_slot(slot)
            
            if spell.concentration:
                entity.start_concentration(spell)

            if spell.save_ability:
                dmg = roll_dice(spell.damage_dice) + int(extra)
                desc = f"{entity.name} casts {spell.name} on {target.name} (DC {dc} {spell.save_ability})"
                return ActionStep(
                    step_type="spell", description=desc,
                    attacker=entity, target=target, spell=spell, slot_used=slot,
                    action_name=spell.name, damage=dmg,
                    damage_type=spell.damage_type, save_dc=dc,
                    save_ability=spell.save_ability,
                )
            else:
                # Check threatened for actual cast
                is_threatened = False
                enemies_adj = [e for e in enemies if battle.is_adjacent(e, entity)]
                if enemies_adj: is_threatened = True

                adv = entity.has_attack_advantage(target, is_ranged=True)
                dis = entity.has_attack_disadvantage(target, is_ranged=True, is_threatened=is_threatened)
                total, nat, is_crit, is_fumble, roll_str = roll_attack(atk_bonus, adv, dis)
                is_hit = total >= target.stats.armor_class and not is_fumble
                dmg = roll_dice_critical(spell.damage_dice) if is_crit else roll_dice(spell.damage_dice)
                dmg += int(extra)

                hit_str = "CRIT! " if is_crit else "Hit? "
                desc = (f"{entity.name} casts {spell.name} ({roll_str}+{atk_bonus}={total} "
                        f"vs AC {target.stats.armor_class}) {hit_str}→ {target.name}")
                return ActionStep(
                    step_type="spell", description=desc,
                    attacker=entity, target=target, spell=spell, slot_used=slot,
                    action_name=spell.name, attack_roll=total, attack_roll_str=roll_str,
                    nat_roll=nat, is_crit=is_crit, is_hit=is_hit,
                    damage=dmg, damage_type=spell.damage_type,
                )
        return None

    # ------------------------------------------------------------------ #
    # Multiattack with Class Mechanics                                     #
    # ------------------------------------------------------------------ #

    def _execute_multiattack(self, entity, multi_action, enemies, allies, battle) -> List[ActionStep]:
        steps = []
        primary_action_names = multi_action.multiattack_targets or []
        sub_actions = []
        for name in primary_action_names:
            found = next((a for a in entity.stats.actions if a.name == name and not a.is_multiattack), None)
            if found:
                sub_actions.append(found)

        if not sub_actions:
            non_multi = [a for a in entity.stats.actions if not a.is_multiattack]
            if non_multi:
                sub_actions = [non_multi[0]] * multi_action.multiattack_count

        first_attack = True
        for sub in sub_actions:
            alive_enemies = [e for e in enemies if e.hp > 0]
            
            # Filter targets by range of this specific attack
            # This prevents AI from picking a high-value target it can't reach (e.g. far away Wizard)
            # and then skipping the attack, when it could hit the adjacent Fighter.
            reachable_enemies = [e for e in alive_enemies if battle.get_distance(entity, e) * 5 <= sub.range]
            
            t = self._pick_target(entity, reachable_enemies)
            if not t:
                continue

            # Check usage limits for sub-action
            if entity.get_feature_by_name(sub.name):
                if not entity.can_use_feature(sub.name):
                    continue
                entity.use_feature(sub.name)

            step = self._execute_attack(entity, sub, t, battle)

            # Apply class bonuses to attack steps
            self._apply_class_attack_bonuses(entity, step, t, allies, battle,
                                             first_attack=first_attack)
            steps.append(step)
            first_attack = False

        return steps

    def _apply_class_attack_bonuses(self, entity, step, target, allies, battle,
                                    first_attack=True):
        """Apply class-specific combat bonuses to an attack step."""
        bonus_parts = []

        # --- BARBARIAN: Rage damage bonus ---
        if entity.rage_active and step.action and step.action.range <= 5:
            rage_bonus = entity.get_rage_damage_bonus()
            step.damage += rage_bonus
            step.rage_bonus = rage_bonus
            bonus_parts.append(f"Rage +{rage_bonus}")
            entity.rage_damage_dealt = True

        # --- ROGUE: Sneak Attack ---
        if (entity.has_feature("sneak_attack") and not entity.sneak_attack_used
                and step.is_hit):
            sa_dice = entity.get_sneak_attack_dice()
            if sa_dice:
                # Check conditions for Sneak Attack
                has_advantage = entity.has_attack_advantage(target,
                                                           is_ranged=(step.action and step.action.range > 10))
                ally_adjacent = any(battle.is_adjacent(a, target) for a in allies if a.hp > 0)
                if has_advantage or ally_adjacent:
                    sa_dmg = roll_dice_critical(sa_dice) if step.is_crit else roll_dice(sa_dice)
                    step.bonus_damage += sa_dmg
                    step.damage += sa_dmg
                    bonus_parts.append(f"Sneak Attack {sa_dice}={sa_dmg}")
                    entity.sneak_attack_used = True

        # --- PALADIN: Divine Smite (auto-use on crits, or vs tough enemies) ---
        if entity.has_feature("divine_smite") and step.is_hit:
            should_smite = False
            # Always smite on crits
            if step.is_crit:
                should_smite = True
            # Smite on first hit if target is tough or undead/fiend
            elif first_attack and entity.has_spell_slot(1):
                t_type = target.stats.creature_type.lower()
                if t_type in ("undead", "fiend"):
                    should_smite = True
                elif target.hp > 30:  # Smite against tough targets
                    should_smite = True

            if should_smite and entity.has_spell_slot(1):
                # Use highest slot for crits, lowest otherwise
                slot_level = entity.get_highest_slot() if step.is_crit else 1
                slot_key = entity._LEVEL_KEYS.get(slot_level, "1st")
                if entity.spell_slots.get(slot_key, 0) > 0:
                    entity.spell_slots[slot_key] -= 1
                    # 2d8 base + 1d8 per level above 1st
                    num_dice = 2 + (slot_level - 1)
                    # +1d8 vs undead/fiend
                    t_type = target.stats.creature_type.lower()
                    if t_type in ("undead", "fiend"):
                        num_dice += 1
                    num_dice = min(num_dice, 5)  # Max 5d8

                    smite_dice = f"{num_dice}d8"
                    smite_dmg = roll_dice_critical(smite_dice) if step.is_crit else roll_dice(smite_dice)
                    step.bonus_damage += smite_dmg
                    step.damage += smite_dmg
                    bonus_parts.append(f"Divine Smite ({slot_level}st slot) {smite_dice}={smite_dmg}")

        # --- PALADIN: Improved Divine Smite ---
        if entity.has_feature("improved_divine_smite") and step.is_hit:
            ids_dmg = roll_dice_critical("1d8") if step.is_crit else roll_dice("1d8")
            step.bonus_damage += ids_dmg
            step.damage += ids_dmg
            bonus_parts.append(f"Improved Smite +{ids_dmg}")

        # --- RANGER: Hunter's Mark bonus damage ---
        if (entity.concentrating_on and
                entity.concentrating_on.name == "Hunter's Mark" and
                entity.marked_target == target and step.is_hit):
            hm_dmg = roll_dice_critical("1d6") if step.is_crit else roll_dice("1d6")
            step.bonus_damage += hm_dmg
            step.damage += hm_dmg
            bonus_parts.append(f"Hunter's Mark +{hm_dmg}")

        # --- WARLOCK: Hex bonus damage ---
        if (entity.concentrating_on and
                entity.concentrating_on.name == "Hex" and
                entity.marked_target == target and step.is_hit):
            hex_dmg = roll_dice_critical("1d6") if step.is_crit else roll_dice("1d6")
            step.bonus_damage += hex_dmg
            step.damage += hex_dmg
            bonus_parts.append(f"Hex +{hex_dmg}")

        # --- RANGER: Colossus Slayer ---
        if (entity.has_feature("colossus_slayer") and step.is_hit and
                target.hp < target.max_hp and first_attack):
            cs_feat = entity.get_feature("colossus_slayer")
            cs_dice = cs_feat.mechanic_value if cs_feat else "1d8"
            cs_dmg = roll_dice_critical(cs_dice) if step.is_crit else roll_dice(cs_dice)
            step.bonus_damage += cs_dmg
            step.damage += cs_dmg
            bonus_parts.append(f"Colossus Slayer +{cs_dmg}")

        # --- CLERIC: Divine Strike ---
        if entity.has_feature("divine_strike") and step.is_hit and first_attack:
            ds_feat = entity.get_feature("divine_strike")
            ds_dice = ds_feat.mechanic_value if ds_feat else "1d8"
            ds_dmg = roll_dice_critical(ds_dice) if step.is_crit else roll_dice(ds_dice)
            step.bonus_damage += ds_dmg
            step.damage += ds_dmg
            bonus_parts.append(f"Divine Strike +{ds_dmg}")

        # Update description with bonus damage info
        if bonus_parts:
            step.bonus_damage_desc = " + ".join(bonus_parts)
            step.description += f" [{step.bonus_damage_desc}]"

    def _execute_attack(self, entity, action: Action, target: "Entity", battle) -> ActionStep:
        dist = battle.get_distance(entity, target)
        is_ranged = action.range > 10
        
        # Check if attacker is threatened (for ranged disadvantage)
        is_threatened = False
        if is_ranged:
            enemies_adj = [e for e in battle.get_enemies_of(entity) if battle.is_adjacent(e, entity)]
            if enemies_adj:
                is_threatened = True

        adv = entity.has_attack_advantage(target, is_ranged, dist)
        dis = entity.has_attack_disadvantage(target, is_ranged, is_threatened=is_threatened)
        allies_adj = [a for a in battle.get_allies_of(entity) if battle.is_adjacent(a, target)]
        if allies_adj:
            if entity.has_feature("pack_tactics"):
                adv = True

        # Improved/Superior Critical (Fighter Champion)
        crit_range = 20
        if entity.has_feature("superior_critical"):
            crit_range = 18
        elif entity.has_feature("improved_critical"):
            crit_range = 19

        # Calculate target effective AC (including Cover)
        cover_bonus = battle.get_cover_bonus(entity, target)
        effective_ac = target.armor_class + cover_bonus

        # --- Great Weapon Master / Sharpshooter Logic ---
        atk_mod = 0
        dmg_mod = 0
        use_power_attack = False

        # Heuristic: Use if hit chance > 40% even with penalty, or if we have Advantage
        # GWM (Heavy weapons: d10, d12, 2d6)
        is_heavy = any(d in action.damage_dice for d in ["d10", "d12", "2d6"])
        if entity.has_feature("great_weapon_master") and is_heavy and action.range <= 5:
            est_hit = (21 + action.attack_bonus - 5 - effective_ac) / 20.0
            if adv: est_hit = 1 - (1-est_hit)**2
            if est_hit > 0.40:
                use_power_attack = True

        # Sharpshooter (Ranged)
        elif entity.has_feature("sharpshooter") and is_ranged:
            est_hit = (21 + action.attack_bonus - 5 - effective_ac) / 20.0
            if adv: est_hit = 1 - (1-est_hit)**2
            if est_hit > 0.40:
                use_power_attack = True

        if use_power_attack:
            atk_mod = -5
            dmg_mod = 10

        total, nat, is_crit, is_fumble, roll_str = roll_attack(action.attack_bonus + atk_mod, adv, dis)
        
        # Add dynamic bonuses (Bless, etc.)
        effect_bonus = entity.get_attack_bonus_effects()
        total += effect_bonus
        if effect_bonus != 0:
            roll_str += f"{'+' if effect_bonus>0 else ''}{effect_bonus}(Eff)"

        # Override crit check with expanded range
        is_crit = nat >= crit_range
        crit_auto = (target.has_condition("Paralyzed") or target.has_condition("Unconscious")) and dist <= 0.5
        if crit_auto:
            is_crit, is_hit = True, True
        else:
            is_hit = total >= effective_ac and not is_fumble

        dmg_str = f"{action.damage_dice}+{action.damage_bonus}" if action.damage_bonus else action.damage_dice
        dmg = roll_dice_critical(dmg_str) if is_crit else roll_dice(dmg_str)
        dmg += dmg_mod

        # Brutal Critical (Barbarian): extra weapon dice on crit
        if is_crit and entity.has_feature("brutal_critical"):
            bc_feat = entity.get_feature("brutal_critical")
            extra_dice = int(bc_feat.mechanic_value) if bc_feat and bc_feat.mechanic_value else 1
            # Roll extra weapon dice
            import re
            match = re.match(r"(\d+)d(\d+)", action.damage_dice)
            if match:
                sides = int(match.group(2))
                for _ in range(extra_dice):
                    dmg += random.randint(1, sides)

        # Savage Attacks (Half-Orc): one extra weapon die on crit
        if is_crit and entity.has_feature("savage_attacks") and action.range <= 5:
            import re
            match = re.match(r"(\d+)d(\d+)", action.damage_dice)
            if match:
                sides = int(match.group(2))
                extra = random.randint(1, sides)
                dmg += extra
                roll_str += f" + {extra} (Savage)"

        hit_str = "CRIT! " if is_crit else "Hit? "
        desc = (f"{entity.name} {action.name} ({roll_str}+{action.attack_bonus}={total} "
                f"vs AC {effective_ac}) {hit_str}→ {target.name}")
        if cover_bonus > 0:
            desc += f" (Cover +{cover_bonus})"
        if use_power_attack:
            desc += " [Power Attack -5/+10]"
            
        # Break Invisibility / Hiding on attack (unless Greater Invisibility)
        if entity.has_condition("Invisible") and "Greater Invisibility" not in entity.active_effects:
            entity.remove_condition("Invisible")
            desc += " [Revealed]"

        return ActionStep(
            step_type="attack", description=desc,
            attacker=entity, target=target, action_name=action.name,
            attack_roll=total, attack_roll_str=roll_str, nat_roll=nat,
            is_crit=is_crit, is_hit=is_hit,
            damage=dmg, damage_type=action.damage_type, applies_condition=action.applies_condition,
            condition_dc=action.condition_dc, save_ability=action.condition_save
        )

    # ------------------------------------------------------------------ #
    # Bonus Action                                                         #
    # ------------------------------------------------------------------ #

    def _decide_bonus_action(self, entity, enemies, allies, battle, plan=None) -> List[ActionStep]:
        if entity.bonus_action_used:
            return []

        # Check if a leveled spell was cast with Action (prevents Bonus Action spells)
        leveled_spell_cast = False
        if plan:
            for s in plan.steps:
                if s.step_type == "spell" and s.slot_used > 0:
                    leveled_spell_cast = True
                    break

        # Monster: Aggressive (Orc) - Move towards enemy
        if entity.has_feature("aggressive"):
            target = self._pick_target(entity, enemies)
            if target:
                entity.movement_left += entity.stats.speed
                move_step = self._move_toward(entity, target, allies, battle)
                if move_step:
                    entity.bonus_action_used = True
                    move_step.description = f"{entity.name} uses Aggressive to move closer."
                    return [move_step]

        # Monster: Nimble Escape (Goblin) - Disengage or Hide
        if entity.has_feature("nimble_escape"):
            threats = [e for e in enemies if battle.is_adjacent(entity, e)]
            if threats:
                entity.movement_left += entity.stats.speed # Ensure movement logic works
                move_step = self._move_away(entity, threats[0], battle)
                if move_step:
                    entity.bonus_action_used = True
                    move_step.description = f"{entity.name} uses Nimble Escape to Disengage & Retreat."
                    return [move_step]

        # 1. Command Spiritual Weapon (if any)
        # Find my spiritual weapons that are summons
        my_weapons = [e for e in battle.entities 
                      if e.is_summon and e.summon_owner == entity and "Spiritual Weapon" in e.name]
        
        for weapon in my_weapons:
            # Pick target for weapon
            target = self._pick_target(weapon, enemies)
            if target:
                steps = []
                # Move if needed
                if not battle.is_adjacent(weapon, target):
                    move_step = self._move_summon_to_target(weapon, target, battle)
                    if move_step:
                        move_step.step_type = "bonus_attack"
                        move_step.description = f"{entity.name} moves Spiritual Weapon."
                        steps.append(move_step)
                
                if weapon.stats.actions:
                    atk_step = self._execute_attack(weapon, weapon.stats.actions[0], target, battle)
                    atk_step.step_type = "bonus_attack"
                    atk_step.description = f"{entity.name} attacks with Spiritual Weapon."
                    steps.append(atk_step)
                    entity.bonus_action_used = True
                    return steps

        # --- Monk: Flurry of Blows / Bonus Unarmed Strike ---
        if entity.has_feature("flurry_of_blows") and entity.ki_points_left > 0:
            target = self._pick_target(entity, enemies)
            if target and battle.is_adjacent(entity, target):
                return self._monk_flurry_of_blows(entity, target, allies, battle)

        # --- Monk: Stunning Strike (applied during attack, but tracked here) ---

        # Check bonus action attacks
        for ba in entity.stats.bonus_actions:
            if not ba.damage_dice:
                continue
            target = self._pick_target(entity, enemies)
            if not target:
                continue
            dist = battle.get_distance(entity, target)
            if ba.range / 5.0 >= dist:
                step = self._execute_attack(entity, ba, target, battle)
                step.step_type = "bonus_attack"
                entity.bonus_action_used = True
                return [step]

        # --- Hunter's Mark (Ranger) ---
        if not leveled_spell_cast:
            hm_step = self._try_hunters_mark(entity, enemies, battle)
            if hm_step:
                return [hm_step]

        # --- Hex (Warlock) ---
        if not leveled_spell_cast:
            hex_step = self._try_hex(entity, enemies, battle)
            if hex_step:
                return [hex_step]

        # --- Spiritual Weapon summon ---
        if not leveled_spell_cast:
            sw_step = self._try_summon_spiritual_weapon(entity, enemies, battle)
            if sw_step:
                return [sw_step]

    def _try_lay_on_hands(self, entity, allies, battle) -> List[ActionStep]:
        """Paladin: Heal dying or low HP ally."""
        # Prioritize dying allies
        dying = [a for a in allies if a.hp <= 0 and not a.is_stable and not a.is_summon]
        target = None
        amount = 0
        
        if dying:
            target = min(dying, key=lambda a: battle.get_distance(entity, a))
            amount = 1 # Just stabilize/revive
        else:
            # Heal very low allies if we have plenty of pool
            low = [a for a in allies if a.hp > 0 and a.hp < a.max_hp * 0.3 and not a.is_summon]
            if low and entity.lay_on_hands_left >= 10:
                target = min(low, key=lambda a: a.hp)
                amount = min(entity.lay_on_hands_left, target.max_hp - target.hp, 20)
        
        if not target:
            return []

        steps = []
        # Move to target (Touch)
        if not battle.is_adjacent(entity, target):
            move_step = self._move_toward(entity, target, allies, battle)
            if move_step:
                steps.append(move_step)
            
            # Check if we reached
            if not battle.is_adjacent(entity, target):
                return [] # Cannot reach

        entity.lay_on_hands_left -= amount
        steps.append(ActionStep(
            step_type="spell", # Treated as spell/action
            description=f"{entity.name} uses Lay on Hands on {target.name} for {amount} HP.",
            attacker=entity, target=target, action_name="Lay on Hands",
            damage=amount, damage_type="healing" # Heal
        ))
        return steps

    def _try_turn_undead(self, entity, enemies, battle) -> Optional[ActionStep]:
        """Cleric: Turn Undead if multiple undead nearby."""
        undead = [e for e in enemies if e.hp > 0 and e.stats.creature_type.lower() == "undead" 
                  and battle.get_distance(entity, e) * 5 <= 30]
        
        if len(undead) >= 2 or (len(undead) == 1 and undead[0].hp > 30):
            return ActionStep(
                step_type="spell",
                description=f"{entity.name} uses Turn Undead! (Undead within 30ft WIS Save)",
                attacker=entity, targets=undead, action_name="Turn Undead",
                save_dc=entity.stats.spell_save_dc, save_ability="Wisdom",
                applies_condition="Turned" # Custom condition logic handled by DM or engine
            )
        return None

        # --- Rogue: Cunning Action ---
        if entity.has_feature("cunning_action"):
            # Disengage if threatened
            threats = [e for e in enemies if battle.is_adjacent(entity, e)]
            if threats:
                # Bonus Disengage + Move away
                entity.movement_left += entity.stats.speed # Ensure we have movement logic available
                move_step = self._move_away(entity, threats[0], battle)
                if move_step:
                    entity.bonus_action_used = True
                    move_step.description = f"{entity.name} uses Cunning Action: Disengage & Retreat."
                    return [move_step]
            
            # Dash if target far
            target = self._pick_target(entity, enemies)
            if target:
                dist = battle.get_distance(entity, target) * 5
                if dist > entity.movement_left and dist > 30:
                     entity.movement_left += entity.stats.speed
                     # Generate movement step towards target
                     move_step = self._move_toward(entity, target, allies, battle)
                     if move_step:
                        entity.bonus_action_used = True
                        move_step.description = f"{entity.name} uses Cunning Action: Dash. " + move_step.description
                        return [move_step]

        # --- Bard: Bardic Inspiration ---
        if entity.has_feature("bardic_inspiration") and entity.bardic_inspiration_left > 0:
             # Find ally without inspiration, prioritize low HP
             candidates = [a for a in allies if a != entity and a.hp > 0]
             if candidates:
                 # Simple heuristic: inspire the one with lowest HP %
                 target = min(candidates, key=lambda a: a.hp / a.max_hp)
                 entity.bardic_inspiration_left -= 1
                 entity.bonus_action_used = True
                 return [ActionStep(step_type="bonus_attack", description=f"{entity.name} gives Bardic Inspiration to {target.name}.", attacker=entity, target=target, action_name="Bardic Inspiration")]

        # --- Revive Ally with Bonus Action (Healing Word) ---
        revive_step = self._try_revive_ally_spell(entity, allies, battle, action_type="bonus")
        if revive_step:
            entity.bonus_action_used = True
            return [revive_step]

        # Bonus Action Spells (Heals, Buffs, Utility)
        for spell in entity.stats.spells_known:
            if spell.action_type != "bonus":
                continue
            if spell.level > 0 and not entity.has_spell_slot(spell.level):
                continue
            if leveled_spell_cast and spell.level > 0:
                continue

            # Healing (if hurt)
            if spell.heals and entity.hp < entity.max_hp * 0.7:
                if spell.level == 0 or entity.use_spell_slot(spell.level):
                    healed = roll_dice(spell.heals)
                    entity.bonus_action_used = True
                    return [ActionStep(
                        step_type="bonus_attack",
                        description=f"{entity.name} uses bonus {spell.name}, heals {healed} HP.",
                        attacker=entity, target=entity, spell=spell,
                        slot_used=spell.level, damage=healed,
                        action_name=spell.name,
                    )]

            # Buffs / Damage Boosts (Concentration)
            if spell.concentration and not entity.concentrating_on:
                target = self._pick_target(entity, enemies)
                if target and (spell.level == 0 or entity.use_spell_slot(spell.level)):
                    entity.start_concentration(spell)
                    entity.bonus_action_used = True
                    return [ActionStep(
                        step_type="bonus_attack",
                        description=f"{entity.name} casts bonus {spell.name} (Concentration).",
                        attacker=entity, target=entity, spell=spell,
                        slot_used=spell.level, action_name=spell.name,
                    )]
        return []

    def _try_hunters_mark(self, entity, enemies, battle):
        """Cast Hunter's Mark on best target."""
        if entity.concentrating_on:
            return None  # Already concentrating
        hm = next((s for s in entity.stats.spells_known if s.name == "Hunter's Mark"), None)
        if not hm or not entity.has_spell_slot(1):
            return None

        target = self._pick_target(entity, enemies)
        if not target:
            return None

        dist = battle.get_distance(entity, target) * 5
        if dist > hm.range:
            return None

        entity.use_spell_slot(1)
        entity.start_concentration(hm)
        entity.marked_target = target
        entity.bonus_action_used = True

        return ActionStep(
            step_type="bonus_attack",
            description=f"{entity.name} casts Hunter's Mark on {target.name} "
                        f"(+1d6 on weapon hits, Concentration)",
            attacker=entity, target=target, spell=hm, slot_used=1,
            action_name="Hunter's Mark",
        )

    def _try_hex(self, entity, enemies, battle):
        """Cast Hex on best target (Warlock)."""
        if entity.concentrating_on:
            return None
        hex_spell = next((s for s in entity.stats.spells_known if s.name == "Hex"), None)
        if not hex_spell or not entity.has_spell_slot(1):
            return None

        target = self._pick_target(entity, enemies)
        if not target:
            return None

        dist = battle.get_distance(entity, target) * 5
        if dist > hex_spell.range:
            return None

        entity.use_spell_slot(hex_spell.level)
        entity.start_concentration(hex_spell)
        entity.marked_target = target
        entity.bonus_action_used = True

        return ActionStep(
            step_type="bonus_attack",
            description=f"{entity.name} casts Hex on {target.name} "
                        f"(+1d6 necrotic on hits, Concentration)",
            attacker=entity, target=target, spell=hex_spell, slot_used=hex_spell.level,
            action_name="Hex",
        )

    def _try_summon_spiritual_weapon(self, entity, enemies, battle):
        """Summon a Spiritual Weapon token near best target."""
        sw = next((s for s in entity.stats.spells_known if s.name == "Spiritual Weapon"), None)
        if not sw or not entity.has_spell_slot(2):
            return None

        # Don't summon if we already have one active
        existing = [e for e in battle.entities if e.is_summon and e.summon_owner == entity and "Spiritual Weapon" in e.name]
        if existing:
            return None

        target = self._pick_target(entity, enemies)
        if not target:
            return None

        # Find spawn position adjacent to target
        spawn_x, spawn_y = target.grid_x, target.grid_y
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = target.grid_x + dx, target.grid_y + dy
                if battle.is_passable(nx, ny, exclude=entity):
                    spawn_x, spawn_y = nx, ny
                    break

        entity.use_spell_slot(2)
        entity.bonus_action_used = True

        # Calculate attack bonus for spiritual weapon
        spell_atk = entity.stats.spell_attack_bonus or (
            entity.stats.proficiency_bonus +
            entity.get_modifier(entity.stats.spellcasting_ability))
        spell_mod = entity.get_modifier(entity.stats.spellcasting_ability)

        return ActionStep(
            step_type="summon",
            description=f"{entity.name} casts Spiritual Weapon near {target.name}!",
            attacker=entity, target=target, spell=sw, slot_used=2,
            action_name="Spiritual Weapon",
            summon_name="Spiritual Weapon",
            summon_x=spawn_x, summon_y=spawn_y,
            summon_hp=0, summon_ac=99,
            summon_owner=entity,
            summon_duration=10,
            summon_spell="Spiritual Weapon",
            summon_immediate_attack=True,
        )

    def _monk_flurry_of_blows(self, entity, target, allies, battle):
        """Monk: Flurry of Blows - spend 1 ki for 2 bonus unarmed strikes."""
        entity.ki_points_left -= 1
        entity.bonus_action_used = True

        # Get martial arts die
        ma_feat = entity.get_feature("martial_arts")
        ma_die = ma_feat.mechanic_value if ma_feat else "1d6"

        # Two unarmed strikes
        atk_bonus = entity.stats.proficiency_bonus + entity.get_modifier("dexterity")
        dex_mod = entity.get_modifier("dexterity")

        total_dmg = 0
        desc_parts = []
        for i in range(2):
            adv = entity.has_attack_advantage(target, is_ranged=False)
            dis = entity.has_attack_disadvantage(target, is_ranged=False)
            total, nat, is_crit, is_fumble, roll_str = roll_attack(atk_bonus, adv, dis)
            is_hit = total >= target.stats.armor_class and not is_fumble

            if is_hit:
                dmg = roll_dice_critical(ma_die) if is_crit else roll_dice(ma_die)
                dmg += dex_mod
                total_dmg += dmg
                desc_parts.append(f"Hit({total}): {dmg}")
            else:
                desc_parts.append(f"Miss({total})")

            # Stunning Strike: on hit, spend 1 ki to stun
            if (is_hit and entity.has_feature("stunning_strike") and
                    entity.ki_points_left > 0 and
                    not target.has_condition("Stunned")):
                entity.ki_points_left -= 1
                # Will be resolved as a condition in battle system
                desc_parts[-1] += " [Stunning Strike DC 16 CON]"

        desc = (f"{entity.name} Flurry of Blows (1 ki): " + ", ".join(desc_parts))

        return [ActionStep(
            step_type="bonus_attack",
            description=desc, attacker=entity, target=target,
            action_name="Flurry of Blows", damage=total_dmg,
            damage_type="bludgeoning",
            is_hit=total_dmg > 0,
            # If stunning strike was used, add condition
            applies_condition="Stunned" if any("Stunning Strike" in p for p in desc_parts) else "",
            condition_dc=8 + entity.stats.proficiency_bonus + entity.get_modifier("wisdom"),
            save_ability="Constitution",
        )]

    # ------------------------------------------------------------------ #
    # Legendary Actions                                                    #
    # ------------------------------------------------------------------ #

    def calculate_legendary_action(self, entity, battle) -> Optional[ActionStep]:
        if entity.legendary_actions_left <= 0:
            return None
        enemies = battle.get_enemies_of(entity)
        if not enemies:
            return None

        leg_feats = [f for f in entity.stats.features if f.feature_type == "legendary"]
        leg_feats.sort(key=lambda f: f.legendary_cost)
        for feat in leg_feats:
            if feat.legendary_cost <= entity.legendary_actions_left:
                leg_action = next((a for a in entity.stats.actions if a.name == feat.name
                                   and a.action_type == "legendary"), None)
                if leg_action:
                    target = self._pick_target(entity, enemies)
                    dist = battle.get_distance(entity, target)
                    if leg_action.range / 5.0 >= dist:
                        step = self._execute_attack(entity, leg_action, target, battle)
                        step.step_type = "legendary"
                        step.description = f"[LEGENDARY] " + step.description
                        entity.legendary_actions_left -= feat.legendary_cost
                        return step
        return None

    # ------------------------------------------------------------------ #
    # Opportunity Attack                                                   #
    # ------------------------------------------------------------------ #

    def calculate_opportunity_attack(self, entity, target, battle) -> Optional[ActionStep]:
        if entity.reaction_used or entity.is_incapacitated():
            return None
        actions = [a for a in entity.stats.actions if a.range <= 5 and not a.is_multiattack]
        if not actions:
            return None
        action = actions[0]
        step = self._execute_attack(entity, action, target, battle)
        step.step_type = "reaction"
        step.description = "[REACTION/OA] " + step.description
        entity.reaction_used = True
        return step

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _pick_target(self, entity, enemies) -> Optional["Entity"]:
        """Score enemies: low HP % + proximity + low AC + mark priority."""
        alive = [e for e in enemies if e.hp > 0]
        if not alive:
            return None
        return max(alive, key=lambda e: self._score_target(entity, e))

    def _score_target(self, entity, target):
        hp_pct = target.hp / target.max_hp
        dist = math.hypot(entity.grid_x - target.grid_x, entity.grid_y - target.grid_y)
        s = -dist * 2
        if hp_pct < 0.4:
            s += 20
        s -= (target.stats.armor_class - 12)
        # Prioritize marked targets (Hunter's Mark, Hex)
        if entity.marked_target == target:
            s += 30
        return s

    def _estimate_damage(self, dice_str, damage_type, target):
        """Calculate average damage against a target, accounting for weakness/resistance."""
        base = average_damage(dice_str)
        if not damage_type: return base
        dtype = damage_type.lower()
        if dtype in [x.lower() for x in target.stats.damage_immunities]:
            return 0.0
        if dtype in [x.lower() for x in target.stats.damage_vulnerabilities]:
            return base * 2.0
        if dtype in [x.lower() for x in target.stats.damage_resistances]:
            return base * 0.5
        return base

    def _best_melee_or_ranged(self, entity, target, battle):
        if not target:
            return None
        dist = battle.get_distance(entity, target)
        actions = [a for a in entity.stats.actions if not a.is_multiattack]
        
        valid_actions = []
        for a in actions:
            # Check range
            if a.range / 5.0 < dist:
                continue
            # Check usage limits
            if entity.get_feature_by_name(a.name):
                if not entity.can_use_feature(a.name):
                    continue
            valid_actions.append(a)

        if not valid_actions:
            return None
            
        # Score: Damage + Bonus for Conditions (prioritize control effects)
        # Use _estimate_damage to account for vulnerabilities
        def score_action(a):
            d_str = f"{a.damage_dice}+{a.damage_bonus}" if a.damage_bonus else a.damage_dice
            dmg = self._estimate_damage(d_str, a.damage_type, target)
            if dmg <= 0: return -1.0 # Avoid immune
            return dmg + (10 if a.applies_condition else 0)

        best = max(valid_actions, key=score_action)
        if score_action(best) < 0: return None # All actions ineffective
        return best

    def _flanking_position(self, entity, target, allies, battle):
        for ally in allies:
            if ally.hp <= 0:
                continue
            if battle.is_adjacent(ally, target):
                dx = target.grid_x - ally.grid_x
                dy = target.grid_y - ally.grid_y
                fx = target.grid_x + dx
                fy = target.grid_y + dy
                if battle.is_passable(fx, fy):
                    return (fx, fy)
        return None

    def _find_spread_out_destination(self, entity, target, allies, battle):
        """Find a melee spot adjacent to target that minimizes clumping with allies (vs AoE)."""
        # 1. Check if spreading is needed (AoE threat)
        enemies = battle.get_enemies_of(entity)
        has_aoe_threat = False
        for e in enemies:
            if e.hp <= 0: continue
            # Check actions
            for a in e.stats.actions:
                if a.aoe_radius > 0:
                    has_aoe_threat = True
                    break
            if has_aoe_threat: break
            # Check spells
            for s in e.stats.spells_known:
                if s.aoe_radius > 0:
                    has_aoe_threat = True
                    break
            if has_aoe_threat: break
        
        if not has_aoe_threat:
            return None

        # 2. Find all valid melee spots around target
        candidates = []
        t_size = target.size_in_squares
        
        for x in range(int(target.grid_x) - 1, int(target.grid_x) + t_size + 1):
            for y in range(int(target.grid_y) - 1, int(target.grid_y) + t_size + 1):
                if not battle.is_passable(x, y, exclude=entity): continue
                # Skip inside target
                if x >= target.grid_x and x < target.grid_x + t_size and \
                   y >= target.grid_y and y < target.grid_y + t_size:
                    continue
                candidates.append((x, y))

        if not candidates: return None

        # 3. Score candidates: -TravelDist - ClumpingPenalty
        best_score = -9999
        best_spot = None
        
        for (cx, cy) in candidates:
            travel = math.hypot(cx - entity.grid_x, cy - entity.grid_y)
            if travel * 5 > entity.movement_left: continue
            
            clumping = 0
            for ally in allies:
                if ally == entity or ally.hp <= 0: continue
                d = math.hypot(cx - ally.grid_x, cy - ally.grid_y)
                if d < 3.0: # Within 15ft
                    clumping += (3.0 - d) * 10
            
            score = -travel - clumping
            if score > best_score:
                best_score = score
                best_spot = (cx, cy)
        
        return best_spot

    def _best_aoe_cluster(self, entity, enemies, allies, battle, radius_ft,
                          shape="sphere", avoid_allies=True, damage_type=None):
        """Returns the list of enemies within aoe_radius of the best center point.
        If avoid_allies is True, penalizes clusters that would hit allies.
        Returns (best_cluster, (aim_x, aim_y)) or None."""
        alive = [e for e in enemies if e.hp > 0]
        if not alive:
            return None

        best_cluster = []
        best_score = -999
        best_aim_point = (0, 0)

        def get_center(e):
            s = e.size_in_squares
            return e.grid_x + s/2.0, e.grid_y + s/2.0

        ecx, ecy = get_center(entity)

        # CONE / LINE LOGIC (Origin = Entity)
        if shape in ("cone", "line"):
            # Cone angle ~60 degrees (half 30). Line is narrow.
            half_angle = math.radians(30) if shape == "cone" else math.radians(5)
            
            # Generate candidate angles: aim at every enemy, and midpoints between enemies
            candidate_angles = []
            
            # 1. Aim at every enemy center
            for e in alive:
                tcx, tcy = get_center(e)
                dx = tcx - ecx
                dy = tcy - ecy
                candidate_angles.append(math.atan2(dy, dx))

            # 2. Aim at midpoints between enemies (to catch multiple in cone)
            for i in range(len(alive)):
                for j in range(i + 1, len(alive)):
                    t1x, t1y = get_center(alive[i])
                    t2x, t2y = get_center(alive[j])
                    a1 = math.atan2(t1y - ecy, t1x - ecx)
                    a2 = math.atan2(t2y - ecy, t2x - ecx)
                    # Vector average for midpoint angle
                    vx = (math.cos(a1) + math.cos(a2)) / 2
                    vy = (math.sin(a1) + math.sin(a2)) / 2
                    candidate_angles.append(math.atan2(vy, vx))

            for aim_angle in candidate_angles:
                cluster = []
                for e in alive:
                    # Check immunity
                    if damage_type and damage_type.lower() in [x.lower() for x in e.stats.damage_immunities]:
                        continue

                    tcx, tcy = get_center(e)
                    # Check distance from attacker center
                    dist = math.hypot(tcx - ecx, tcy - ecy)
                    if dist * 5 > radius_ft: continue
                        
                    # Check angle
                    edx = tcx - ecx
                    edy = tcy - ecy
                    e_angle = math.atan2(edy, edx)
                    
                    diff = abs(e_angle - aim_angle)
                    while diff > math.pi: diff -= 2*math.pi
                    while diff < -math.pi: diff += 2*math.pi
                    
                    if abs(diff) <= half_angle:
                        cluster.append(e)
                
                score = len(cluster)
                if avoid_allies and allies:
                    for a in allies:
                        if a.hp <= 0: continue
                        acx, acy = get_center(a)
                        dist = math.hypot(acx - ecx, acy - ecy)
                        if dist * 5 > radius_ft: continue
                        adx = acx - ecx
                        ady = acy - ecy
                        a_angle = math.atan2(ady, adx)
                        diff = abs(a_angle - aim_angle)
                        while diff > math.pi: diff -= 2*math.pi
                        while diff < -math.pi: diff += 2*math.pi
                        if abs(diff) <= half_angle:
                            score -= 3
                
                if score > best_score:
                    best_score = score
                    best_cluster = cluster
                    # Aim point is just a point in the direction of the angle
                    best_aim_point = (ecx + math.cos(aim_angle)*5, ecy + math.sin(aim_angle)*5)
        else:
            # SPHERE / CUBE (Origin = Point in space)
            # Candidates: centers of enemies, and midpoints between enemies
            candidates = []
            for candidate in alive:
                candidates.append(get_center(candidate))
            
            for i in range(len(alive)):
                for j in range(i + 1, len(alive)):
                    t1x, t1y = get_center(alive[i])
                    t2x, t2y = get_center(alive[j])
                    candidates.append(((t1x + t2x)/2, (t1y + t2y)/2))

            for (ccx, ccy) in candidates:
                cluster = []
                for e in alive:
                    # Check immunity
                    if damage_type and damage_type.lower() in [x.lower() for x in e.stats.damage_immunities]:
                        continue

                    tcx, tcy = get_center(e)
                    if math.hypot(ccx - tcx, ccy - tcy) * 5 <= radius_ft:
                        cluster.append(e)

                score = len(cluster)
                if avoid_allies and allies:
                    for a in allies:
                        if a.hp <= 0: continue
                        acx, acy = get_center(a)
                        if math.hypot(ccx - acx, ccy - acy) * 5 <= radius_ft:
                            score -= 3

                if score > best_score:
                    best_score = score
                    best_cluster = cluster
                    best_aim_point = (ccx, ccy)

        # Don't use AoE if we'd hit more allies than enemies
        if best_score <= 0:
            return None

        return best_cluster, best_aim_point

    def _cluster_center(self, cluster):
        if not cluster:
            return 0.0, 0.0
        cx = sum(e.grid_x for e in cluster) / len(cluster)
        cy = sum(e.grid_y for e in cluster) / len(cluster)
        return cx, cy
