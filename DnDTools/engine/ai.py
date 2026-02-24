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

        # ----- 1. MOVEMENT -----
        move_step = self._decide_movement(entity, enemies, allies, battle)
        if move_step:
            plan.steps.append(move_step)

        # ----- 1.5. AOE ACTION (Breath Weapon etc) -----
        aoe_action_step = self._try_aoe_action(entity, enemies, allies, battle)
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
                                               radius_ft=action.aoe_radius)
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

        # Decrement duration
        entity.summon_rounds_left -= 1
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
        has_melee = any(a.range <= 5 for a in actions)
        spells = entity.stats.spells_known or []
        has_aoe = any(s.aoe_radius > 0 for s in spells)

        # If we want melee and not adjacent, move closer
        if has_melee and dist > 1.5:
            return self._move_toward(entity, target, allies, battle)

        # If we want ranged/spells and enemy is too close, step away
        if has_ranged and not has_melee and dist <= 1.5:
            return self._move_away(entity, target, battle)

        # AoE caster: position for best cluster
        if has_aoe and not has_melee:
            cluster = self._best_aoe_cluster(entity, enemies, allies, battle, 20)
            if cluster and len(cluster) >= 2:
                cx, cy = self._cluster_center(cluster)
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

    def _move_toward(self, entity, target, allies, battle):
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

        # Self-heal if critical and has healing ability
        if entity.max_hp > 0 and (entity.hp / entity.max_hp < 0.25):
            heal_step = self._try_heal_action(entity)
            if heal_step:
                entity.action_used = True
                return [heal_step]

        # Second Wind (Fighter) if hurt
        if entity.max_hp > 0 and (entity.hp / entity.max_hp < 0.5):
            sw_step = self._try_second_wind(entity)
            if sw_step:
                # Second Wind is a bonus action, don't use main action
                pass

        # Disengage if critical and threatened (only for non-melee or squishy characters)
        is_squishy = entity.stats.character_class in ("Wizard", "Sorcerer", "Bard", "Warlock")
        if entity.max_hp > 0 and (entity.hp / entity.max_hp < 0.3) and is_squishy:
            disengage_step = self._try_disengage_action(entity, enemies, battle)
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
                step = self._execute_attack(entity, best_action, target, battle)
                # Apply class bonuses to single attacks too
                self._apply_class_attack_bonuses(entity, step, target, allies, battle)
                entity.action_used = True
                return [step]

        return self._try_dash_action(entity, enemies, allies, battle)

    def _try_aoe_action(self, entity, enemies, allies, battle):
        """Try to use a non-spell AoE action (like Breath Weapon)."""
        if entity.action_used:
            return None

        aoe_actions = [a for a in entity.stats.actions if a.aoe_radius > 0 and a.damage_dice]
        if not aoe_actions:
            return None

        aoe_actions.sort(key=lambda a: average_damage(a.damage_dice), reverse=True)

        for action in aoe_actions:
            clusters = self._best_aoe_cluster(entity, enemies, allies, battle, action.aoe_radius)
            if not clusters or len(clusters) < 2:
                continue

            cx, cy = self._cluster_center(clusters)
            raw_dmg = roll_dice(action.damage_dice)

            return ActionStep(
                step_type="attack",
                description=f"{entity.name} uses {action.name} (DC {action.condition_dc or '??'} {action.condition_save})",
                attacker=entity, targets=clusters, action=action, damage=raw_dmg,
                damage_type=action.damage_type, action_name=action.name, aoe_center=(cx, cy),
                save_dc=action.condition_dc, save_ability=action.condition_save
            )
        return None

    def _try_heal_action(self, entity):
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
            damage=healed,  # Repurpose damage field for heal amount
        )

    def _try_disengage_action(self, entity, enemies, battle):
        threats = [e for e in enemies if battle.is_adjacent(entity, e)]
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

        aoe_spells.sort(key=lambda s: average_damage(s.damage_dice), reverse=True)

        # Can this caster sculpt spells? (Evocation Wizard)
        can_sculpt = entity.has_feature("sculpt_spells")

        for spell in aoe_spells:
            if spell.level == 0:
                continue
            threshold = 3 if average_damage(spell.damage_dice) < 20 else 2
            clusters = self._best_aoe_cluster(entity, enemies, allies, battle,
                                               spell.aoe_radius,
                                               avoid_allies=not can_sculpt)
            if not clusters or len(clusters) < threshold:
                continue
            if entity.use_spell_slot(spell.level):
                slot = spell.level
                cx, cy = self._cluster_center(clusters)
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

            # Agonizing Blast: add CHA to Eldritch Blast
            extra_spell_dmg = 0
            if spell.name == "Eldritch Blast" and entity.has_feature("agonizing_blast"):
                extra_spell_dmg = entity.get_modifier("charisma")

            # Empowered Evocation: add INT to evocation damage
            if entity.has_feature("empowered_evocation"):
                extra_spell_dmg += entity.get_modifier("intelligence")

            if spell.save_ability:
                dmg = roll_dice(spell.damage_dice) + extra_spell_dmg
                desc = f"{entity.name} casts {spell.name} on {target.name} (DC {dc} {spell.save_ability})"
                return ActionStep(
                    step_type="spell", description=desc,
                    attacker=entity, target=target, spell=spell, slot_used=slot,
                    action_name=spell.name, damage=dmg,
                    damage_type=spell.damage_type, save_dc=dc,
                    save_ability=spell.save_ability,
                )
            else:
                adv = entity.has_attack_advantage(target, is_ranged=True)
                dis = entity.has_attack_disadvantage(target, is_ranged=True)
                total, nat, is_crit, is_fumble, roll_str = roll_attack(atk_bonus, adv, dis)
                is_hit = total >= target.stats.armor_class and not is_fumble
                dmg = roll_dice_critical(spell.damage_dice) if is_crit else roll_dice(spell.damage_dice)
                dmg += extra_spell_dmg

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
            t = self._pick_target(entity, alive_enemies)
            if not t:
                break
            dist = battle.get_distance(entity, t)
            if sub.range // 5 < dist - 0.5:
                continue

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
        adv = entity.has_attack_advantage(target, is_ranged)
        dis = entity.has_attack_disadvantage(target, is_ranged)
        allies_adj = [a for a in battle.get_allies_of(entity) if battle.is_adjacent(a, target)]
        if allies_adj and not is_ranged:
            adv = True

        # Improved/Superior Critical (Fighter Champion)
        crit_range = 20
        if entity.has_feature("superior_critical"):
            crit_range = 18
        elif entity.has_feature("improved_critical"):
            crit_range = 19

        total, nat, is_crit, is_fumble, roll_str = roll_attack(action.attack_bonus, adv, dis)
        # Override crit check with expanded range
        is_crit = nat >= crit_range
        crit_auto = (target.has_condition("Paralyzed") or target.has_condition("Unconscious")) and dist <= 1.5
        if crit_auto:
            is_crit, is_hit = True, True
        else:
            is_hit = total >= target.stats.armor_class and not is_fumble

        dmg_str = f"{action.damage_dice}+{action.damage_bonus}" if action.damage_bonus else action.damage_dice
        dmg = roll_dice_critical(dmg_str) if is_crit else roll_dice(dmg_str)

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
            if ba.range // 5 >= dist - 0.5:
                step = self._execute_attack(entity, ba, target, battle)
                step.step_type = "bonus_attack"
                entity.bonus_action_used = True
                return step

        # --- Hunter's Mark (Ranger) ---
        hm_step = self._try_hunters_mark(entity, enemies, battle)
        if hm_step:
            return hm_step

        # --- Hex (Warlock) ---
        hex_step = self._try_hex(entity, enemies, battle)
        if hex_step:
            return hex_step

        # --- Spiritual Weapon summon ---
        sw_step = self._try_summon_spiritual_weapon(entity, enemies, battle)
        if sw_step:
            return sw_step

        # Bonus Action Spells (Heals, Buffs, Utility)
        for spell in entity.stats.spells_known:
            if spell.action_type != "bonus":
                continue
            if spell.level > 0 and not entity.has_spell_slot(spell.level):
                continue

            # Healing (if hurt)
            if spell.heals and entity.hp < entity.max_hp * 0.7:
                if spell.level == 0 or entity.use_spell_slot(spell.level):
                    healed = roll_dice(spell.heals)
                    entity.bonus_action_used = True
                    return ActionStep(
                        step_type="bonus_attack",
                        description=f"{entity.name} uses bonus {spell.name}, heals {healed} HP.",
                        attacker=entity, target=entity, spell=spell,
                        slot_used=spell.level, damage=healed,
                        action_name=spell.name,
                    )

            # Buffs / Damage Boosts (Concentration)
            if spell.concentration and not entity.concentrating_on:
                target = self._pick_target(entity, enemies)
                if target and (spell.level == 0 or entity.use_spell_slot(spell.level)):
                    entity.start_concentration(spell)
                    entity.bonus_action_used = True
                    return ActionStep(
                        step_type="bonus_attack",
                        description=f"{entity.name} casts bonus {spell.name} (Concentration).",
                        attacker=entity, target=entity, spell=spell,
                        slot_used=spell.level, action_name=spell.name,
                    )
        return None

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

        return ActionStep(
            step_type="bonus_attack",
            description=desc, attacker=entity, target=target,
            action_name="Flurry of Blows", damage=total_dmg,
            damage_type="bludgeoning",
            is_hit=total_dmg > 0,
            # If stunning strike was used, add condition
            applies_condition="Stunned" if any("Stunning Strike" in p for p in desc_parts) else "",
            condition_dc=8 + entity.stats.proficiency_bonus + entity.get_modifier("wisdom"),
            save_ability="Constitution",
        )

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

    def _best_aoe_cluster(self, entity, enemies, allies, battle, radius_ft,
                          avoid_allies=True):
        """Returns the list of enemies within aoe_radius of the best center point.
        If avoid_allies is True, penalizes clusters that would hit allies."""
        alive = [e for e in enemies if e.hp > 0]
        if not alive:
            return []

        best_cluster = []
        best_score = -999

        for candidate in alive:
            cluster = [e for e in alive
                       if math.hypot(candidate.grid_x - e.grid_x,
                                     candidate.grid_y - e.grid_y) <= radius_ft / 5]
            score = len(cluster)

            # Penalize hitting allies
            if avoid_allies and allies:
                allies_hit = [a for a in allies if a.hp > 0 and
                              math.hypot(candidate.grid_x - a.grid_x,
                                         candidate.grid_y - a.grid_y) <= radius_ft / 5]
                score -= len(allies_hit) * 3  # Heavy penalty for hitting allies

            if score > best_score:
                best_score = score
                best_cluster = cluster

        # Don't use AoE if we'd hit more allies than enemies
        if best_score <= 0:
            return []

        return best_cluster

    def _cluster_center(self, cluster):
        if not cluster:
            return 0.0, 0.0
        cx = sum(e.grid_x for e in cluster) / len(cluster)
        cy = sum(e.grid_y for e in cluster) / len(cluster)
        return cx, cy
