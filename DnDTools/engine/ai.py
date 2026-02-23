"""
D&D 5e 2014 Tactical AI for NPCs.
Computes an optimal TurnPlan for a given entity.
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
    step_type: str             # "attack","spell","bonus_attack","bonus_spell","move","wait","legendary"
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


@dataclass
class TurnPlan:
    entity: Optional["Entity"] = None
    steps: List[ActionStep] = field(default_factory=list)
    skipped: bool = False
    skip_reason: str = ""


class TacticalAI:
    """Full D&D 5e 2014 tactical AI."""

    def calculate_turn(self, entity: "Entity", battle: "BattleSystem") -> TurnPlan:
        plan = TurnPlan(entity=entity)

        if entity.is_lair:
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
            
            # AoE Lair Action
            if action.aoe_radius > 0:
                clusters = self._best_aoe_cluster(owner, enemies, battle, action.aoe_radius)
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

            # Single Target Lair Action
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

        if entity.is_incapacitated():
            plan.skipped = True
            conds = ", ".join(entity.conditions & {"Incapacitated","Paralyzed","Stunned","Unconscious","Petrified"})
            plan.skip_reason = f"Incapacitated ({conds})"
            return plan

        enemies = battle.get_enemies_of(entity)
        allies  = battle.get_allies_of(entity)

        if not enemies:
            plan.skipped = True
            plan.skip_reason = "No valid targets"
            return plan

        # ----- 1. MOVEMENT -----
        move_step = self._decide_movement(entity, enemies, allies, battle)
        if move_step:
            plan.steps.append(move_step)

        # ----- 1.5. AOE ACTION (Breath Weapon etc) -----
        aoe_action_step = self._try_aoe_action(entity, enemies, battle)
        if aoe_action_step:
            plan.steps.append(aoe_action_step)
            entity.action_used = True

        # ----- 2. MAIN ACTION -----
        action_steps = self._decide_action(entity, enemies, allies, battle)
        if action_steps:
            plan.steps.extend(action_steps)

        # ----- 3. BONUS ACTION -----
        if not entity.bonus_action_used:
            bonus_step = self._decide_bonus_action(entity, enemies, allies, battle)
            if bonus_step:
                plan.steps.append(bonus_step)

        if not plan.steps:
            plan.skipped = True
            plan.skip_reason = "Nothing to do"

        return plan

    # ------------------------------------------------------------------ #
    # Movement                                                             #
    # ------------------------------------------------------------------ #

    def _decide_movement(self, entity, enemies, allies, battle):
        if not entity.can_move() or entity.movement_left <= 0:
            return None

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
        has_ranged = any(a.range > 10 for a in actions)
        has_melee  = any(a.range <= 5  for a in actions)
        spells     = entity.stats.spells_known or []
        has_aoe    = any(s.aoe_radius > 0 for s in spells)

        # If we want melee and not adjacent, move closer
        if has_melee and dist > 1.5:
            return self._move_toward(entity, target, allies, battle)

        # If we want ranged/spells and enemy is too close, step away
        if has_ranged and not has_melee and dist <= 1.5:
            return self._move_away(entity, target, battle)

        # AoE caster: position for best cluster
        if has_aoe and not has_melee:
            cluster = self._best_aoe_cluster(entity, enemies, battle, 20)
            if cluster and len(cluster) >= 2:
                cx, cy = self._cluster_center(cluster)
                # Move to optimum cast position (20 ft from center)
                return self._move_toward_point(entity, cx, cy, battle)

        return None

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
            # Chebyshev distance (diagonals count as 1 step in 5e)
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
            
            if current in visited: continue
            visited.add(current)

            cx, cy = current
            # Check all 8 neighbors
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0: continue
                    nx, ny = cx + dx, cy + dy
                    neighbor = (nx, ny)

                    if not self._is_safe_passable(battle, nx, ny, entity):
                        continue

                    # Movement cost (1.0 normal, 2.0 difficult)
                    move_cost = battle.get_terrain_movement_cost(nx, ny)
                    tentative_g = g_score[current] + move_cost

                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        f = tentative_g + heuristic(neighbor, end)
                        heapq.heappush(open_set, (f, neighbor))
        return None

    def _move_toward(self, entity, target, allies, battle):
        """Move toward target, trying flanking position. Respects terrain."""
        flank = self._flanking_position(entity, target, allies, battle)
        dest_x = flank[0] if flank else target.grid_x
        dest_y = flank[1] if flank else target.grid_y

        # If destination is occupied (e.g. target is there), find closest free spot
        if not battle.is_passable(dest_x, dest_y, exclude=entity):
            valid_adj = []
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0: continue
                    nx, ny = int(dest_x + dx), int(dest_y + dy)
                    if self._is_safe_passable(battle, nx, ny, entity):
                        valid_adj.append((nx, ny))
            
            if valid_adj:
                # Pick neighbor closest to entity
                dest_x, dest_y = min(valid_adj, key=lambda p: math.hypot(p[0]-entity.grid_x, p[1]-entity.grid_y))
            else:
                # No valid spot near target?
                return None

        start_x, start_y = entity.grid_x, entity.grid_y
        start_movement = entity.movement_left

        # Calculate Path
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
                
                # Stop if adjacent to target (so we can attack)
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

    def _move_toward_point(self, entity, tx, ty, battle):
        start_x, start_y = entity.grid_x, entity.grid_y
        start_movement = entity.movement_left

        # If target point is blocked, find closest free spot
        dest_x, dest_y = tx, ty
        if not battle.is_passable(dest_x, dest_y, exclude=entity):
            valid_adj = []
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0: continue
                    nx, ny = int(dest_x + dx), int(dest_y + dy)
                    if self._is_safe_passable(battle, nx, ny, entity):
                        valid_adj.append((nx, ny))
            if valid_adj:
                dest_x, dest_y = min(valid_adj, key=lambda p: math.hypot(p[0]-entity.grid_x, p[1]-entity.grid_y))

        path = self._find_path((int(entity.grid_x), int(entity.grid_y)), (int(dest_x), int(dest_y)), battle, entity)

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
            
        return ActionStep(step_type="move",
                          description=f"{entity.name} repositions {moved_cost:.0f} ft.",
                          attacker=entity, new_x=entity.grid_x, new_y=entity.grid_y,
                          movement_ft=moved_cost, old_x=start_x, old_y=start_y)

    def _move_away(self, entity, threat, battle):
        start_x, start_y = entity.grid_x, entity.grid_y
        start_movement = entity.movement_left

        while entity.movement_left >= 5.0:
            dx = entity.grid_x - threat.grid_x
            dy = entity.grid_y - threat.grid_y
            
            # Move away logic
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
            
        return ActionStep(step_type="move",
                          description=f"{entity.name} disengages and moves {moved_cost:.0f} ft.",
                          attacker=entity, new_x=entity.grid_x, new_y=entity.grid_y,
                          movement_ft=moved_cost, old_x=start_x, old_y=start_y)

    # ------------------------------------------------------------------ #
    # Main Action                                                          #
    # ------------------------------------------------------------------ #

    def _decide_action(self, entity, enemies, allies, battle) -> List[ActionStep]:
        if entity.action_used:
            return []

        # Self-heal if critical and has healing ability
        if entity.max_hp > 0 and (entity.hp / entity.max_hp < 0.25):
            heal_step = self._try_heal_action(entity)
            if heal_step:
                entity.action_used = True
                return [heal_step]

        # Disengage if critical and threatened
        if entity.max_hp > 0 and (entity.hp / entity.max_hp < 0.3):
            disengage_step = self._try_disengage_action(entity, enemies, battle)
            if disengage_step:
                entity.action_used = True
                return [disengage_step]

        # AoE spell if 3+ enemies grouped
        if entity.has_spell_slot(1) or entity.stats.cantrips:
            aoe_step = self._try_aoe_spell(entity, enemies, battle)
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

        # Multiattack
        multi = next((a for a in entity.stats.actions if a.is_multiattack), None)
        if multi:
            steps = self._execute_multiattack(entity, multi, enemies, battle)
            entity.action_used = True
            return steps

        # Single best attack - Iterate targets by priority to find one we can actually hit
        alive_enemies = [e for e in enemies if e.hp > 0]
        sorted_enemies = sorted(alive_enemies, key=lambda e: self._score_target(entity, e), reverse=True)

        for target in sorted_enemies:
            # --- TACTICAL MANEUVERS (Shove/Grapple) ---
            if battle.is_adjacent(entity, target):
                # Check if we have allies engaging this target (Pack Tactics / Mob mentality)
                engaging_allies = [a for a in allies if battle.is_adjacent(a, target)]
                str_score = entity.stats.abilities.strength
                
                # 1. SHOVE (Prone) - Great if allies are ready to beat them up
                # Attempt if we have allies nearby OR we are strong enough
                if not target.has_condition("Prone") and (len(engaging_allies) >= 1 or str_score >= 14):
                    # 30% chance to try Shove to set up allies
                    if random.random() < 0.3:
                        shove_step = self._try_shove_action(entity, target)
                        if shove_step:
                            entity.action_used = True
                            return [shove_step]

                # 2. GRAPPLE - Lock them down
                # Relaxed constraint: STR >= 12 OR (STR >= 10 AND allies present)
                if not target.has_condition("Grappled"):
                    can_grapple = str_score >= 12 or (str_score >= 10 and len(engaging_allies) >= 1)
                    if can_grapple and random.random() < 0.2:
                        grapple_step = self._try_grapple_action(entity, target)
                        if grapple_step:
                            entity.action_used = True
                            return [grapple_step]
            # ------------------------------------------

            best_action = self._best_melee_or_ranged(entity, target, battle)
            if best_action:
                step = self._execute_attack(entity, best_action, target, battle)
                entity.action_used = True
                return [step]

        # If no attacks possible, try to Dash to get closer
        return self._try_dash_action(entity, enemies, allies, battle)

    def _try_aoe_action(self, entity, enemies, battle):
        """Try to use a non-spell AoE action (like Breath Weapon)."""
        if entity.action_used:
            return None
        
        # Find AoE actions
        aoe_actions = [a for a in entity.stats.actions if a.aoe_radius > 0 and a.damage_dice]
        if not aoe_actions:
            return None
            
        # Sort by damage
        aoe_actions.sort(key=lambda a: average_damage(a.damage_dice), reverse=True)
        
        for action in aoe_actions:
            # For cones, we need a cluster relative to self
            # For spheres (if any actions are spheres), we need a cluster anywhere in range
            # Simplified: use same cluster logic
            clusters = self._best_aoe_cluster(entity, enemies, battle, action.aoe_radius)
            if not clusters or len(clusters) < 2:
                continue
            
            cx, cy = self._cluster_center(clusters)
            raw_dmg = roll_dice(action.damage_dice)
            
            return ActionStep(
                step_type="attack", # or "action"
                description=f"{entity.name} uses {action.name} (DC {action.condition_dc or '??'} {action.condition_save})",
                attacker=entity, targets=clusters, action=action, damage=raw_dmg, damage_type=action.damage_type,
                action_name=action.name, aoe_center=(cx, cy),
                save_dc=action.condition_dc, save_ability=action.condition_save
            )
        return None

    def _try_heal_action(self, entity):
        """Try to use a healing spell or potion."""
        # Check healing spells
        for spell in entity.stats.spells_known:
            if spell.heals and spell.targets == "self":
                slot = entity.get_slot_for_level(spell.level) if spell.level > 0 else 0
                if spell.level == 0 or entity.use_spell_slot(spell.level):
                    healed = roll_dice(spell.heals)
                    return ActionStep(
                        step_type="spell",
                        description=f"{entity.name} casts {spell.name} on self, healing {healed} HP.",
                        attacker=entity, target=entity, spell=spell,
                        slot_used=slot, action_name=spell.name,
                    )
        # Check potions
        for item in entity.items:
            if item.heals and item.uses > 0:
                item.uses -= 1
                healed = roll_dice(item.heals)
                return ActionStep(
                    step_type="bonus_attack",
                    description=f"{entity.name} uses {item.name}, healing {healed} HP.",
                    attacker=entity, target=entity, action_name=item.name,
                )
        return None

    def _try_disengage_action(self, entity, enemies, battle):
        """If threatened, use Disengage and move away."""
        # Check if adjacent to any enemy
        threats = [e for e in enemies if battle.is_adjacent(entity, e)]
        if not threats:
            return None
        
        # Calculate retreat move
        threat = threats[0]
        entity.movement_left += entity.stats.speed # Assume we use movement for this
        move_step = self._move_away(entity, threat, battle)
        
        if move_step:
            move_step.description = f"{entity.name} Disengages (Action) and retreats."
            move_step.step_type = "move"
            return move_step
        return None

    def _try_dash_action(self, entity, enemies, allies, battle):
        """Use Action to Dash if out of range."""
        target = self._pick_target(entity, enemies)
        if not target:
            return []
        
        # Grant extra movement
        entity.movement_left += entity.stats.speed
        step = self._move_toward(entity, target, allies, battle)
        
        if step:
            step.description = f"{entity.name} Dashes (Action): " + step.description
            entity.action_used = True
            return [step]
        return []

    def _try_grapple_action(self, entity, target):
        """Perform a grapple check (simulated as an attack for now)."""
        # DC = 8 + STR mod + Prof (Passive Athletics approximation)
        prof = entity.stats.proficiency_bonus
        dc = 8 + entity.get_modifier("Strength") + prof
        desc = f"{entity.name} attempts to Grapple {target.name} (DC {dc} STR/DEX check)"
        return ActionStep(
            step_type="attack", description=desc,
            attacker=entity, target=target, action_name="Grapple",
            applies_condition="Grappled", condition_dc=dc, save_ability="Strength"
        )

    def _try_shove_action(self, entity, target):
        """Attempt to Shove target Prone (Action)."""
        prof = entity.stats.proficiency_bonus
        dc = 8 + entity.get_modifier("Strength") + prof
        desc = f"{entity.name} attempts to Shove {target.name} Prone (DC {dc} STR/DEX check)"
        return ActionStep(
            step_type="attack", description=desc,
            attacker=entity, target=target, action_name="Shove",
            applies_condition="Prone", condition_dc=dc, save_ability="Strength"
        )

    def _try_aoe_spell(self, entity, enemies, battle):
        """Cast best AoE spell if cluster >= 3 enemies (or 2 if high damage)."""
        aoe_spells = [s for s in entity.stats.spells_known if s.aoe_radius > 0 and s.damage_dice]
        if not aoe_spells:
            return None

        # Sort by value (highest slot * highest damage)
        aoe_spells.sort(key=lambda s: average_damage(s.damage_dice), reverse=True)

        for spell in aoe_spells:
            if spell.level == 0:
                continue  # cantrips rarely AoE in this context
            threshold = 3 if average_damage(spell.damage_dice) < 20 else 2
            clusters = self._best_aoe_cluster(entity, enemies, battle, spell.aoe_radius)
            if not clusters or len(clusters) < threshold:
                continue
            if entity.use_spell_slot(spell.level):
                slot = spell.level
                cx, cy = self._cluster_center(clusters)
                # Roll saves and compute damage for each target
                dc = spell.save_dc_fixed if spell.save_dc_fixed else \
                     (entity.stats.spell_save_dc or 8 + entity.stats.proficiency_bonus
                      + entity.get_modifier(entity.stats.spellcasting_ability))
                
                raw_dmg = roll_dice(spell.damage_dice)
                
                return ActionStep(
                    step_type="spell",
                    description=f"{entity.name} casts {spell.name} (DC {dc} {spell.save_ability})",
                    attacker=entity, targets=clusters, spell=spell, slot_used=slot, damage=raw_dmg, damage_type=spell.damage_type,
                    action_name=spell.name, aoe_center=(cx, cy),
                    save_dc=dc if dc else 0,
                    save_ability=spell.save_ability,
                )
        return None

    def _try_debuff_spell(self, entity, enemies, battle):
        """Cast a debuff/control spell on highest-priority target."""
        debuff_spells = [s for s in entity.stats.spells_known
                         if s.applies_condition and not s.damage_dice
                         and s.targets == "single"]
        if not debuff_spells:
            return None
        debuff_spells.sort(key=lambda s: s.level, reverse=True)
        for spell in debuff_spells:
            if not entity.has_spell_slot(spell.level):
                continue
            # Target: highest HP enemy without the condition already
            candidates = [e for e in enemies
                          if not e.has_condition(spell.applies_condition) and e.hp > 0]
            if not candidates:
                continue
            target = max(candidates, key=lambda e: e.hp)
            dist = battle.get_distance(entity, target) * 5
            if dist > spell.range:
                continue
            entity.use_spell_slot(spell.level)
            slot = spell.level
            dc = spell.save_dc_fixed if spell.save_dc_fixed else \
                 (entity.stats.spell_save_dc or 8 + entity.stats.proficiency_bonus
                  + entity.get_modifier(entity.stats.spellcasting_ability))
            
            desc = f"{entity.name} casts {spell.name} on {target.name} (DC {dc} {spell.save_ability})"
            return ActionStep(
                step_type="spell", description=desc,
                attacker=entity, target=target, spell=spell, slot_used=slot,
                action_name=spell.name, save_dc=dc, save_ability=spell.save_ability,
                applies_condition=spell.applies_condition,
            )
        return None

    def _try_damage_spell(self, entity, enemies, battle):
        """Cast best available damage spell (or cantrip)."""
        all_spells = entity.stats.spells_known + entity.stats.cantrips
        damage_spells = [s for s in all_spells if s.damage_dice and s.targets == "single"]
        if not damage_spells:
            return None

        # Prefer highest-level spell with available slot
        def spell_value(s):
            if s.level == 0:
                return average_damage(s.damage_dice)
            slot = entity.get_slot_for_level(s.level)
            if slot == 0:
                return -1
            return average_damage(s.damage_dice) * slot

        damage_spells.sort(key=spell_value, reverse=True)
        target = self._pick_target(entity, enemies)

        for spell in damage_spells:
            dist = battle.get_distance(entity, target) * 5
            if dist > spell.range:
                continue
            if spell.level > 0 and not entity.use_spell_slot(spell.level):
                continue
            slot = spell.level
            if spell.concentration:
                entity.start_concentration(spell)
            dc = spell.save_dc_fixed if spell.save_dc_fixed else \
                 (entity.stats.spell_save_dc or 8 + entity.stats.proficiency_bonus
                  + entity.get_modifier(entity.stats.spellcasting_ability))
            atk_bonus = (spell.attack_bonus_fixed or
                         (entity.stats.spell_attack_bonus or
                          entity.stats.proficiency_bonus + entity.get_modifier(entity.stats.spellcasting_ability)))
            if spell.save_ability:
                # Save-based damage spell
                dmg = roll_dice(spell.damage_dice)
                desc = f"{entity.name} casts {spell.name} on {target.name} (DC {dc} {spell.save_ability})"
                return ActionStep(
                    step_type="spell", description=desc,
                    attacker=entity, target=target, spell=spell, slot_used=slot,
                    action_name=spell.name, damage=dmg,
                    damage_type=spell.damage_type, save_dc=dc,
                    save_ability=spell.save_ability,
                )
            else:
                # Attack roll
                adv = entity.has_attack_advantage(target, is_ranged=True)
                dis = entity.has_attack_disadvantage(target, is_ranged=True)
                total, nat, is_crit, is_fumble, roll_str = roll_attack(atk_bonus, adv, dis)
                is_hit = total >= target.stats.armor_class and not is_fumble
                dmg = roll_dice_critical(spell.damage_dice) if is_crit else roll_dice(spell.damage_dice)
                
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

    def _execute_multiattack(self, entity, multi_action, enemies, battle) -> List[ActionStep]:
        """Execute all attacks in a multiattack action."""
        steps = []
        primary_action_names = multi_action.multiattack_targets or []
        sub_actions = []
        for name in primary_action_names:
            found = next((a for a in entity.stats.actions if a.name == name and not a.is_multiattack), None)
            if found:
                sub_actions.append(found)

        if not sub_actions:
            # Fallback: use all non-multiattack actions multi_action.multiattack_count times
            non_multi = [a for a in entity.stats.actions if not a.is_multiattack]
            if non_multi:
                sub_actions = [non_multi[0]] * multi_action.multiattack_count

        for sub in sub_actions:
            t = self._pick_target(entity, [e for e in enemies if e.hp > 0])
            if not t:
                break
            dist = battle.get_distance(entity, t)
            if sub.range // 5 < dist - 0.5:
                continue
            
            step = self._execute_attack(entity, sub, t, battle)
            steps.append(step)

        return steps

    def _execute_attack(self, entity, action: Action, target: "Entity", battle) -> ActionStep:
        dist = battle.get_distance(entity, target)
        is_ranged = action.range > 10
        adv = entity.has_attack_advantage(target, is_ranged)
        dis = entity.has_attack_disadvantage(target, is_ranged)
        allies_adj = [a for a in battle.get_allies_of(entity) if battle.is_adjacent(a, target)]
        if allies_adj and not is_ranged:
            adv = True

        total, nat, is_crit, is_fumble, roll_str = roll_attack(action.attack_bonus, adv, dis)
        crit_auto = (target.has_condition("Paralyzed") or target.has_condition("Unconscious")) and dist <= 1.5
        if crit_auto:
            is_crit, is_hit = True, True
        else:
            is_hit = total >= target.stats.armor_class and not is_fumble

        dmg_str = f"{action.damage_dice}+{action.damage_bonus}" if action.damage_bonus else action.damage_dice
        dmg = roll_dice_critical(dmg_str) if is_crit else roll_dice(dmg_str)

        hit_str = "CRIT! " if is_crit else "Hit? "
        desc = (f"{entity.name} {action.name} ({roll_str}+{action.attack_bonus}={total} "
                f"vs AC {target.stats.armor_class}) {hit_str}→ {target.name}")
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

    def _decide_bonus_action(self, entity, enemies, allies, battle):
        if entity.bonus_action_used:
            return None

        # Check bonus action attacks
        for ba in entity.stats.bonus_actions:
            # Skip actions that have no damage dice (likely utility/heal actions)
            if not ba.damage_dice:
                continue
            target = self._pick_target(entity, enemies)
            if not target:
                continue
            dist = battle.get_distance(entity, target)
            if ba.range // 5 >= dist - 0.5:
                step = self._execute_attack(entity, ba, target, battle)
                step.step_type = "bonus_attack"
                entity.bonus_action_used = True
                return step

        # Bonus Action Spells (Heals, Buffs, Utility)
        for spell in entity.stats.spells_known:
            if spell.action_type != "bonus":
                continue
            if spell.level > 0 and not entity.has_spell_slot(spell.level):
                continue

            # 1. Healing (if hurt)
            if spell.heals and entity.hp < entity.max_hp * 0.7:
                if spell.level == 0 or entity.use_spell_slot(spell.level):
                    healed = roll_dice(spell.heals)
                    entity.bonus_action_used = True
                    return ActionStep(
                        step_type="bonus_attack",
                        description=f"{entity.name} uses bonus {spell.name}, heals {healed} HP.",
                        attacker=entity, target=entity, spell=spell, slot_used=spell.level, damage=healed,
                        action_name=spell.name,
                    )
            
            # 2. Buffs / Damage Boosts (Concentration)
            # E.g. Hunter's Mark, Divine Favor, Shield of Faith
            if spell.concentration and not entity.concentrating_on:
                # Simple logic: cast if we have a target
                target = self._pick_target(entity, enemies)
                if target and (spell.level == 0 or entity.use_spell_slot(spell.level)):
                    entity.start_concentration(spell)
                    entity.bonus_action_used = True
                    return ActionStep(
                        step_type="bonus_attack",
                        description=f"{entity.name} casts bonus {spell.name} (Concentration).",
                        attacker=entity, target=entity, spell=spell, slot_used=spell.level,
                        action_name=spell.name,
                    )
        return None

    # ------------------------------------------------------------------ #
    # Legendary Actions                                                    #
    # ------------------------------------------------------------------ #

    def calculate_legendary_action(self, entity, battle) -> Optional[ActionStep]:
        if entity.legendary_actions_left <= 0:
            return None
        enemies = battle.get_enemies_of(entity)
        if not enemies:
            return None

        # Prefer cost-1 legendary attack
        leg_feats = [f for f in entity.stats.features if f.feature_type == "legendary"]
        leg_feats.sort(key=lambda f: f.legendary_cost)
        for feat in leg_feats:
            if feat.legendary_cost <= entity.legendary_actions_left:
                # Check if there's a matching action
                leg_action = next((a for a in entity.stats.actions if a.name == feat.name
                                   and a.action_type == "legendary"), None)
                if leg_action:
                    target = self._pick_target(entity, enemies)
                    dist = battle.get_distance(entity, target)
                    if leg_action.range // 5 >= dist - 0.5:
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
        """Score enemies: low HP % + proximity + low AC."""
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
        return s

    def _best_melee_or_ranged(self, entity, target, battle):
        if not target:
            return None
        dist = battle.get_distance(entity, target)
        actions = [a for a in entity.stats.actions if not a.is_multiattack]
        in_range = [a for a in actions if a.range // 5 >= dist - 0.5]
        if not in_range:
            return None
        return max(in_range, key=lambda a: average_damage(
            f"{a.damage_dice}+{a.damage_bonus}" if a.damage_bonus else a.damage_dice))

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

    def _best_aoe_cluster(self, entity, enemies, battle, radius_ft):
        """Returns the list of enemies within aoe_radius of the best center point."""
        alive = [e for e in enemies if e.hp > 0]
        if not alive:
            return []
        best_cluster = []
        for candidate in alive:
            cluster = [e for e in alive
                       if math.hypot(candidate.grid_x - e.grid_x, candidate.grid_y - e.grid_y) <= radius_ft/5]
            if len(cluster) > len(best_cluster):
                best_cluster = cluster
        return best_cluster

    def _cluster_center(self, cluster):
        if not cluster:
            return 0.0, 0.0
        cx = sum(e.grid_x for e in cluster) / len(cluster)
        cy = sum(e.grid_y for e in cluster) / len(cluster)
        return cx, cy
