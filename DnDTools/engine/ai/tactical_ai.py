"""TacticalAI – the main AI class that computes optimal turns for D&D 5e entities."""
import math
import random
import heapq
from typing import List, Optional, TYPE_CHECKING
from data.models import Action, SpellInfo, Item
from engine.dice import roll_attack, roll_dice, roll_dice_critical, average_damage, scale_cantrip_dice
from engine.ai.models import ActionStep, TurnPlan
from engine.ai.constants import (
    KILL_POTENTIAL_BONUS, FOCUS_FIRE_WEIGHT, THREAT_DPR_WEIGHT,
    SPELL_SLOT_THREAT, CONC_LEVEL_VALUE, CONC_AOE_BONUS,
    CONC_CONDITION_BONUS, CONC_SUMMON_BONUS, HEALER_PRIORITY_BONUS,
    DISTANCE_PENALTY_WEIGHT, AC_DIFFICULTY_WEIGHT, MARK_TARGET_BONUS,
    GRAPPLE_SHOVE_COMBO_VALUE, DODGE_HP_THRESHOLD, DODGE_CRITICAL_THRESHOLD,
    HEAL_MELEE_THRESHOLD, HEAL_RANGED_THRESHOLD, DISENGAGE_HP_LOW,
)
from engine.ai.utils import _get_effective_caster_level, _get_spell_damage_dice

if TYPE_CHECKING:
    from engine.entities import Entity
    from engine.battle import BattleSystem
    from data.models import CreatureStats


class TacticalAI:
    """Full D&D 5e 2014 tactical AI with class mechanic and environment awareness."""

    def _can_see_target(self, entity, target, battle) -> bool:
        """Check if entity has line of sight to target. Core check for all targeting."""
        return battle.has_line_of_sight(entity, target)

    def _get_visible_enemies(self, entity, enemies, battle) -> list:
        """Filter enemies to only those the entity can see.
        Also excludes charmer if entity is Charmed (PHB p.290)."""
        result = []
        for e in enemies:
            if e.hp <= 0:
                continue
            if not self._can_see_target(entity, e, battle):
                continue
            # PHB p.290: Charmed creature can't attack the charmer
            if entity.has_condition("Charmed"):
                charm_source = entity.condition_sources.get("Charmed")
                if charm_source is e:
                    continue
            result.append(e)
        return result

    def _can_ranged_attack(self, entity, target, battle, range_ft: float = 0) -> bool:
        """Check if a ranged attack/spell is valid: LOS + range."""
        if not self._can_see_target(entity, target, battle):
            return False
        if range_ft > 0:
            dist_ft = battle.get_distance(entity, target) * 5
            if dist_ft > range_ft:
                return False
        return True

    def _get_terrain_advantage_score(self, entity, battle, x, y) -> float:
        """Score a position for tactical terrain advantage."""
        score = 0.0
        t = battle.get_terrain_at(int(x), int(y))
        elev = battle.get_elevation_at(int(x), int(y))

        # Elevation advantage: +2 score per 5ft height
        if elev > 0:
            score += elev / 5.0 * 2.0

        # Cover bonus: good for ranged combatants
        if t and t.provides_cover:
            score += t.cover_bonus * 2.0

        # Adjacent cover check (better than being on cover, hide behind it)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                adj_t = battle.get_terrain_at(int(x) + dx, int(y) + dy)
                if adj_t and adj_t.provides_cover:
                    score += adj_t.cover_bonus * 0.5

        return score

    def calculate_turn(self, entity: "Entity", battle: "BattleSystem") -> TurnPlan:
        """Optimal turn planning with god-mode knowledge.

        Turn order optimized for maximum effectiveness:
        1. PRE-COMBAT BUFFS (bonus action): Rage, Hunter's Mark, Hex
           -> These MUST come before attacks to get bonus damage on first turn
        2. MOVEMENT: Position optimally (spread vs AoE, approach, kite)
        3. MAIN ACTION: Best available option (AoE, debuff, attack, grapple/shove)
        4. ACTION SURGE: Second action if Fighter
        5. POST-COMBAT BONUS: Flurry, Second Wind, Healing Word, Spiritual Weapon
        """
        plan = TurnPlan(entity=entity)

        if entity.is_lair:
            return self._handle_lair_turn(entity, battle, plan)

        if entity.is_summon:
            return self._handle_summon_turn(entity, battle, plan)

        if entity.is_incapacitated():
            plan.skipped = True
            conds = ", ".join(entity.conditions & {"Incapacitated", "Paralyzed", "Stunned", "Unconscious", "Petrified"})
            plan.skip_reason = f"Incapacitated ({conds})"
            return plan

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

        # ===== PHASE 0: PRE-COMBAT BONUS ACTIONS (buffs that boost subsequent attacks) =====
        if not entity.bonus_action_used:
            # Barbarian Rage FIRST - enables rage damage on all attacks this turn
            rage_step = self._try_start_rage(entity, enemies, allies, battle)
            if rage_step:
                plan.steps.append(rage_step)
                entity.bonus_action_used = True

        if not entity.bonus_action_used:
            # Hunter's Mark / Hex BEFORE attacks - adds 1d6 to ALL weapon hits this turn
            pre_buff_step = self._try_pre_combat_bonus(entity, enemies, allies, battle)
            if pre_buff_step:
                plan.steps.append(pre_buff_step)
                entity.bonus_action_used = True

        # Barbarian: Reckless Attack (PHB p.48) - decide before attacks
        # Gives advantage on melee STR attacks but enemies get advantage against you
        if entity.has_feature("reckless_attack") and not entity.reckless_attack_active:
            # Use reckless when: adjacent enemy and we benefit from advantage
            closest_enemy = min(enemies, key=lambda e: battle.get_distance(entity, e) if e.hp > 0 else 999)
            if closest_enemy.hp > 0 and battle.get_distance(entity, closest_enemy) * 5 <= entity.movement_left + 5:
                # Cost-benefit: advantage is worth it if we're a damage dealer or raging
                # Don't use if too many enemies are in melee (too costly)
                threats = [e for e in enemies if battle.is_adjacent(entity, e) and e.hp > 0]
                # Use reckless if: raging (resistance offsets cost), or fewer than 3 threats
                should_reckless = entity.rage_active or len(threats) <= 2
                if should_reckless:
                    entity.reckless_attack_active = True
                    plan.steps.append(ActionStep(
                        step_type="wait",
                        description=f"{entity.name} attacks recklessly! (Advantage on STR melee, enemies get advantage)",
                        attacker=entity, action_name="Reckless Attack",
                    ))

        if not entity.bonus_action_used and entity.has_feature("cunning_action"):
            # Rogue: Hide for advantage on first attack
            hide_step = self._try_cunning_hide(entity, enemies, battle)
            if hide_step:
                plan.steps.append(hide_step)
                entity.bonus_action_used = True

        # ===== PHASE 1: MOVEMENT (optimal positioning) =====
        move_step = self._decide_movement(entity, enemies, allies, battle)
        if move_step:
            plan.steps.append(move_step)

        # ===== PHASE 2: EMERGENCY REVIVE (highest priority action) =====
        if not entity.action_used:
            revive_step = self._try_revive_ally_spell(entity, allies, battle, action_type="action")
            if revive_step:
                plan.steps.append(revive_step)
                entity.action_used = True

        # ===== PHASE 3: AOE ACTION (Breath Weapon etc - before regular attacks) =====
        if not entity.action_used:
            aoe_action_step = self._try_aoe_action(entity, enemies, allies, battle)
            if aoe_action_step:
                plan.steps.append(aoe_action_step)
                entity.action_used = True

        # ===== PHASE 3.5: BUFF POTION (before attacks, if valuable) =====
        if not entity.action_used:
            buff_step = self._try_use_buff_potion(entity, enemies, battle)
            if buff_step:
                plan.steps.append(buff_step)

        # ===== PHASE 4: MAIN ACTION =====
        action_steps = self._decide_action(entity, enemies, allies, battle)
        if action_steps:
            plan.steps.extend(action_steps)

            # ===== PHASE 4.5: ACTION SURGE (Fighter) =====
            if entity.has_feature("action_surge") and entity.can_use_feature("Action Surge"):
                took_offense = any(s.step_type in ("attack", "spell", "multiattack") for s in action_steps)
                if took_offense:
                    entity.use_feature("Action Surge")
                    entity.action_used = False
                    surge_steps = self._decide_action(entity, enemies, allies, battle)
                    if surge_steps:
                        plan.steps.append(ActionStep(step_type="wait", description=f"{entity.name} uses Action Surge!", attacker=entity))
                        plan.steps.extend(surge_steps)

        # ===== PHASE 5: POST-COMBAT BONUS ACTION =====
        if not entity.bonus_action_used:
            bonus_steps = self._decide_bonus_action(entity, enemies, allies, battle, plan)
            if bonus_steps:
                plan.steps.extend(bonus_steps)

        # ===== PHASE 6: POST-ATTACK MOVEMENT (kite away after ranged attack) =====
        if entity.movement_left >= 5.0 and entity.can_move():
            post_move = self._try_post_attack_reposition(entity, enemies, allies, battle)
            if post_move:
                plan.steps.append(post_move)

        if not plan.steps:
            plan.skipped = True
            plan.skip_reason = "Nothing to do"

        return plan

    # ------------------------------------------------------------------ #
    # Lair Actions                                                         #
    # ------------------------------------------------------------------ #

    def _handle_lair_turn(self, entity, battle, plan):
        """Optimal lair action selection - score each option and pick best."""
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

        enemies = battle.get_enemies_of(owner)
        if not enemies:
            plan.skipped = True
            plan.skip_reason = "No valid targets for Lair Action"
            return plan

        allies = battle.get_allies_of(owner)
        best_step = None
        best_score = -1.0

        for action in lair_actions:
            # MM: Can't reuse the same lair action two rounds in a row
            if action.name == entity.last_lair_action and len(lair_actions) > 1:
                continue

            # Check if recharge needed
            if entity.get_feature_by_name(action.name):
                if not entity.can_use_feature(action.name):
                    continue

            if action.aoe_radius > 0:
                result = self._best_aoe_cluster(owner, enemies, allies=allies, battle=battle,
                                                   radius_ft=action.aoe_radius,
                                                   shape=action.aoe_shape or "sphere",
                                                   damage_type=action.damage_type)
                if result:
                    clusters, (cx, cy) = result
                    if clusters:
                        # Score: damage * targets * save factor
                        avg_dmg = average_damage(action.damage_dice) if action.damage_dice else 10
                        score = avg_dmg * len(clusters) * 0.6
                        # Condition value
                        if action.applies_condition:
                            score += len(clusters) * 8

                        if score > best_score:
                            best_score = score
                            raw_dmg = roll_dice(action.damage_dice) if action.damage_dice else 0
                            best_step = ActionStep(
                                step_type="legendary",
                                description=f"[LAIR] {owner.name} uses {action.name}",
                                attacker=owner, targets=clusters, action=action, damage=raw_dmg,
                                damage_type=action.damage_type, action_name=action.name,
                                aoe_center=(cx, cy),
                                save_dc=action.condition_dc, save_ability=action.condition_save
                            )
            else:
                # Single target lair action
                target = self._pick_target(owner, enemies, battle)
                if target:
                    dist = battle.get_distance(owner, target)
                    if action.range / 5.0 >= dist or action.range == 0:
                        avg_dmg = average_damage(action.damage_dice) if action.damage_dice else 10
                        score = avg_dmg * 0.65
                        if action.applies_condition:
                            score += 15

                        if score > best_score:
                            best_score = score
                            step = self._execute_attack(owner, action, target, battle)
                            step.step_type = "legendary"
                            step.description = f"[LAIR] {step.description}"
                            best_step = step

        if best_step:
            # Track which lair action was used (MM: can't repeat next round)
            entity.last_lair_action = best_step.action_name or (best_step.action.name if best_step.action else "")
            # Consume usage if applicable
            if best_step.action and entity.get_feature_by_name(best_step.action.name):
                entity.use_feature(best_step.action.name)
            plan.steps.append(best_step)
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
        target = self._pick_target(entity, enemies, battle)
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
        """Optimal rage activation.

        Always rage if:
        - Enemies within movement range (we'll be in melee this turn)
        - We're taking damage or about to
        - Resistance to BPS halves most enemy damage

        Don't rage if:
        - No enemies within 60ft
        - We're concentrating on a spell (rage breaks concentration)
        """
        if not entity.has_feature("rage") or entity.rage_active:
            return None
        if entity.rages_left <= 0:
            return None

        # PHB: Rage ends concentration - don't rage if concentrating on something valuable
        if entity.concentrating_on:
            return None

        closest_enemy_dist = min(
            (battle.get_distance(entity, e) * 5 for e in enemies if e.hp > 0),
            default=999
        )

        # Don't waste rage if enemies are far
        if closest_enemy_dist > 60:
            return None

        # Always rage if we can reach an enemy this turn
        if closest_enemy_dist <= entity.movement_left + 5:
            entity.start_rage()
            return ActionStep(
                step_type="bonus_attack",
                description=f"{entity.name} enters a RAGE! (Resistance to B/P/S, "
                            f"+{entity.get_rage_damage_bonus()} melee damage)",
                attacker=entity, action_name="Rage",
            )

        # Rage if enemies are approaching (within 40ft)
        if closest_enemy_dist <= 40:
            entity.start_rage()
            return ActionStep(
                step_type="bonus_attack",
                description=f"{entity.name} enters a RAGE! (Resistance to B/P/S, "
                            f"+{entity.get_rage_damage_bonus()} melee damage)",
                attacker=entity, action_name="Rage",
            )

        return None

    def _try_cunning_hide(self, entity, enemies, battle):
        """Rogue Cunning Action: Hide to gain advantage."""
        # 1. Can't hide if threatened (adjacent to enemy)
        if any(battle.is_adjacent(entity, e) for e in enemies if e.hp > 0):
            return None

        # 2. Pick intended target to see if we already have advantage
        target = self._pick_target(entity, enemies, battle)
        if not target:
            return None

        # If we already have advantage, no need to hide
        if entity.has_attack_advantage(target, is_ranged=True):
            return None

        # 3. Attempt Hide (Stealth Check vs Passive Perception)
        stealth_roll = roll_dice("1d20") + entity.get_skill_bonus("Stealth")
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
    # Pre-Combat Bonus & Post-Attack Reposition                            #
    # ------------------------------------------------------------------ #

    def _try_pre_combat_bonus(self, entity, enemies, allies, battle):
        """Cast concentration bonus spells BEFORE attacks for max damage.

        Hunter's Mark, Hex, Divine Favor, etc. add damage to ALL weapon hits,
        so they must be cast before the attack action for optimal DPR.
        """
        # Don't cast if we already have a good concentration going
        if entity.concentrating_on:
            return None

        target = self._pick_target(entity, enemies, battle)
        if not target:
            return None

        # Hunter's Mark (Ranger) - +1d6 on all weapon hits
        hm = next((s for s in entity.stats.spells_known if s.name == "Hunter's Mark"), None)
        if hm and entity.has_spell_slot(1):
            dist_ft = math.hypot(entity.grid_x - target.grid_x, entity.grid_y - target.grid_y) * 5
            if dist_ft <= hm.range and battle.has_line_of_sight(entity, target):
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

        # Hex (Warlock) - +1d6 necrotic on all hits
        hex_spell = next((s for s in entity.stats.spells_known if s.name == "Hex"), None)
        if hex_spell and entity.has_spell_slot(hex_spell.level):
            dist_ft = math.hypot(entity.grid_x - target.grid_x, entity.grid_y - target.grid_y) * 5
            if dist_ft <= hex_spell.range and battle.has_line_of_sight(entity, target):
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

        # Divine Favor (Paladin) - +1d4 radiant on all weapon hits
        df = next((s for s in entity.stats.spells_known if s.name == "Divine Favor"), None)
        if df and entity.has_spell_slot(1):
            entity.use_spell_slot(1)
            entity.start_concentration(df)
            entity.bonus_action_used = True
            return ActionStep(
                step_type="bonus_attack",
                description=f"{entity.name} casts Divine Favor (+1d4 radiant on weapon hits)",
                attacker=entity, target=entity, spell=df, slot_used=1,
                action_name="Divine Favor",
            )

        # Spirit Shroud (TCoE) - +1d8 on attacks within 10ft, prevents healing
        ss = next((s for s in entity.stats.spells_known if s.name == "Spirit Shroud"), None)
        if ss and entity.has_spell_slot(3):
            closest_dist = min(
                (battle.get_distance(entity, e) * 5 for e in enemies if e.hp > 0),
                default=999
            )
            # Only worthwhile if we'll be in melee range
            if closest_dist <= entity.movement_left + 10:
                entity.use_spell_slot(3)
                entity.start_concentration(ss)
                entity.bonus_action_used = True
                return ActionStep(
                    step_type="bonus_attack",
                    description=f"{entity.name} casts Spirit Shroud (+1d8 dmg within 10ft, prevents healing)",
                    attacker=entity, target=entity, spell=ss, slot_used=3,
                    action_name="Spirit Shroud",
                )

        # Zephyr Strike (XGtE) - no OA + advantage on one attack
        zs = next((s for s in entity.stats.spells_known if s.name == "Zephyr Strike"), None)
        if zs and entity.has_spell_slot(1):
            entity.use_spell_slot(1)
            entity.start_concentration(zs)
            entity.bonus_action_used = True
            return ActionStep(
                step_type="bonus_attack",
                description=f"{entity.name} casts Zephyr Strike (no OA, advantage on one attack + 1d8 force)",
                attacker=entity, target=entity, spell=zs, slot_used=1,
                action_name="Zephyr Strike",
            )

        return None

    def _try_post_attack_reposition(self, entity, enemies, allies, battle):
        """After attacking, use remaining movement to reposition.

        Ranged characters: move away from melee threats.
        Melee characters: spread out from allies to avoid AoE.
        """
        pref = self._get_combat_preference(entity)

        # Ranged: kite away if enemies are adjacent
        if pref == "ranged":
            threats = [e for e in enemies if battle.is_adjacent(entity, e) and e.hp > 0]
            if threats and entity.movement_left >= 5.0:
                # If we have Cunning Action or are disengaging, move away
                if entity.is_disengaging or entity.has_feature("cunning_action"):
                    return self._move_away(entity, threats[0], battle)

        # Both: spread from allies if AoE threat exists
        if entity.movement_left >= 5.0:
            aoe_threat = self._assess_aoe_threat(entity, enemies)
            if aoe_threat > 0:
                # Check if we're dangerously clumped
                nearby_allies = [a for a in allies if a.hp > 0 and a != entity
                                 and math.hypot(entity.grid_x - a.grid_x, entity.grid_y - a.grid_y) < 2.5]
                if len(nearby_allies) >= 2:
                    # We're clumped - try to spread
                    return self._spread_from_allies(entity, nearby_allies, enemies, battle)

        return None

    def _spread_from_allies(self, entity, nearby_allies, enemies, battle):
        """Move to reduce clumping while staying combat-effective."""
        start_x, start_y = entity.grid_x, entity.grid_y
        best_spot = None
        best_score = -999

        # Check spots within remaining movement
        max_squares = int(entity.movement_left / 5.0)
        for dx in range(-max_squares, max_squares + 1):
            for dy in range(-max_squares, max_squares + 1):
                nx, ny = int(entity.grid_x) + dx, int(entity.grid_y) + dy
                if not self._is_safe_passable(battle, nx, ny, entity):
                    continue
                travel = math.hypot(dx, dy) * 5
                if travel > entity.movement_left or travel < 5:
                    continue

                # Score: maximize distance from allies, minimize distance from nearest enemy
                min_ally_dist = min(math.hypot(nx - a.grid_x, ny - a.grid_y) for a in nearby_allies)
                nearest_enemy_dist = min(
                    (math.hypot(nx - e.grid_x, ny - e.grid_y) for e in enemies if e.hp > 0),
                    default=999)

                score = min_ally_dist * 5  # Spread bonus

                # Stay engaged if melee
                pref = self._get_combat_preference(entity)
                if pref == "melee":
                    if nearest_enemy_dist > 1.5:
                        score -= 20  # Don't run too far from enemies

                if score > best_score:
                    best_score = score
                    best_spot = (nx, ny)

        if best_spot and best_score > 5:
            old_x, old_y = entity.grid_x, entity.grid_y
            entity.grid_x, entity.grid_y = float(best_spot[0]), float(best_spot[1])
            move_cost = math.hypot(best_spot[0] - old_x, best_spot[1] - old_y) * 5
            entity.movement_left -= move_cost
            return ActionStep(
                step_type="move",
                description=f"{entity.name} spreads out to avoid AoE ({move_cost:.0f} ft).",
                attacker=entity, new_x=entity.grid_x, new_y=entity.grid_y,
                movement_ft=move_cost, old_x=old_x, old_y=old_y,
            )
        return None

    def _assess_aoe_threat(self, entity, enemies) -> float:
        """Assess how much AoE danger enemies pose. Returns threat score 0+."""
        threat = 0.0
        for e in enemies:
            if e.hp <= 0:
                continue
            # Check AoE actions (breath weapons)
            for a in e.stats.actions:
                if a.aoe_radius > 0 and a.damage_dice:
                    threat += average_damage(a.damage_dice) * 0.5
            # Check AoE spells
            for s in e.stats.spells_known:
                if s.aoe_radius > 0 and s.damage_dice and e.has_spell_slot(max(s.level, 1)):
                    threat += average_damage(s.damage_dice) * 0.3
        return threat

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
        """Optimal movement considering all factors including terrain awareness.

        Priority:
        0. Stand from prone / escape grapple
        0.5. Start flying if beneficial
        1. Emergency: reach dying ally for touch healing
        2. Frightened: flee from fear source
        3. Ranged: kite away from melee threats / Misty Step escape
        4. AoE threat: spread out from allies
        5. Melee: approach best target with anti-clump positioning
        6. Ranged: maintain optimal range + seek cover/elevation
        7. AoE caster: position for best cluster
        """
        if not entity.can_move() or entity.movement_left <= 0:
            return None

        # --- -1. FLYING: Start flying if we can and it's tactically useful ---
        if entity.can_fly and not entity.is_flying:
            pref = self._get_combat_preference(entity)
            # Ranged combatants should fly to gain elevation advantage and avoid ground threats
            if pref == "ranged":
                entity.start_flying()
                entity.elevation = max(entity.elevation, 15)  # Gain altitude
            else:
                # Melee flyers: fly if target is flying or if ground is hazardous
                for e in enemies:
                    if e.hp > 0 and e.is_flying:
                        entity.start_flying()
                        entity.elevation = max(entity.elevation, e.elevation)
                        break
                if not entity.is_flying:
                    t = battle.get_terrain_at(int(entity.grid_x), int(entity.grid_y))
                    if t and t.is_hazard:
                        entity.start_flying()
                        entity.elevation = max(entity.elevation + 10, 10)
                # Fly to cross gaps: if no path to target exists without flying
                fly_target = self._pick_target(entity, enemies, battle)
                if not entity.is_flying and fly_target:
                    normal_path = self._find_path(
                        (int(entity.grid_x), int(entity.grid_y)),
                        (int(fly_target.grid_x), int(fly_target.grid_y)),
                        battle, entity, allow_jump=False)
                    if normal_path is None:
                        # Can't walk there - fly if possible
                        entity.start_flying()
                        entity.elevation = max(entity.elevation, 15)

        # --- 0. PRONE: Stand up or escape grapple ---
        if entity.has_condition("Prone"):
            can_stand, reason = entity.can_stand_from_prone()
            if can_stand:
                from engine.rules import stand_from_prone_cost
                cost = stand_from_prone_cost(entity)
                entity.movement_left -= cost
                entity.remove_condition("Prone")
                return ActionStep(
                    step_type="wait",
                    description=f"{entity.name} stands up (costs {cost:.0f} ft movement).",
                    attacker=entity,
                )
            else:
                if entity.has_condition("Grappled") and entity.grappled_by:
                    from engine.rules import resolve_grapple_escape
                    success, msg = resolve_grapple_escape(entity, entity.grappled_by)
                    if success:
                        entity.grappled_by.release_grapple(entity)
                        return ActionStep(
                            step_type="wait",
                            description=msg,
                            attacker=entity, action_name="Escape Grapple"
                        )
                    else:
                        return ActionStep(
                            step_type="wait",
                            description=f"{msg} {entity.name} remains prone and grappled!",
                            attacker=entity, action_name="Escape Grapple (Failed)"
                        )

        # --- 0.5. GRAPPLED: Try to escape if we're being held ---
        if entity.has_condition("Grappled") and entity.grappled_by and not entity.has_condition("Prone"):
            # Escape grapple is worthwhile if we're ranged or need to reposition
            pref = self._get_combat_preference(entity)
            grappler = entity.grappled_by
            # Always try to escape if we're ranged (can't kite while grappled)
            # Or if grappler is setting up prone combo
            should_escape = (pref == "ranged") or (grappler.has_condition("Grappled") is False)
            if should_escape:
                from engine.rules import resolve_grapple_escape
                success, msg = resolve_grapple_escape(entity, grappler)
                if success:
                    grappler.release_grapple(entity)
                    return ActionStep(
                        step_type="wait", description=msg,
                        attacker=entity, action_name="Escape Grapple"
                    )

        # --- 1. EMERGENCY: Reach dying ally for touch healing ---
        dying_allies = [a for a in allies if a.hp <= 0 and not a.is_stable and not a.is_summon]
        if dying_allies and self._has_touch_healing(entity):
            closest_dying = min(dying_allies, key=lambda a: battle.get_distance(entity, a))
            if not battle.is_adjacent(entity, closest_dying):
                return self._move_toward(entity, closest_dying, allies, battle)

        # --- 2. FRIGHTENED: Flee from fear source ---
        if entity.has_condition("Frightened"):
            fear_source = entity.get_condition_source("Frightened")
            if fear_source and fear_source.hp > 0:
                fear_dist = battle.get_distance(entity, fear_source)
                if fear_dist < 6.0:
                    return self._move_away(entity, fear_source, battle)

        target = self._pick_target(entity, enemies, battle)
        if not target:
            return None
        dist = battle.get_distance(entity, target)
        spells = entity.stats.spells_known or []
        preference = self._get_combat_preference(entity)

        # --- 3. RANGED: Escape melee threats ---
        if preference == "ranged":
            threats_adjacent = [e for e in enemies if battle.is_adjacent(entity, e) and e.hp > 0]
            if threats_adjacent:
                # Misty Step escape (highest priority)
                if not entity.bonus_action_used:
                    misty = next((s for s in spells if s.name == "Misty Step"), None)
                    if misty and entity.has_spell_slot(misty.level):
                        tele_step = self._try_teleport_escape(entity, threats_adjacent[0], battle, misty)
                        if tele_step:
                            entity.bonus_action_used = True
                            return tele_step
                # Regular movement away
                return self._move_away(entity, threats_adjacent[0], battle)

        # --- 4. RANGED: Maintain optimal distance + seek cover/elevation ---
        if preference == "ranged":
            # Find our best ranged attack/spell range
            best_range = 60  # Default
            for s in spells:
                if s.damage_dice and s.range > best_range:
                    best_range = s.range
            for a in entity.stats.actions:
                if a.range > 10 and a.range > best_range:
                    best_range = a.range

            optimal_dist = best_range / 5.0 * 0.6  # 60% of max range in squares
            min_dist = 3.0  # At least 15ft away

            # If we can't see the target, try to move to get LOS
            if not self._can_see_target(entity, target, battle):
                los_move = self._move_to_get_los(entity, target, battle)
                if los_move:
                    return los_move
                # Fallback: move toward target (will eventually get around the wall)
                return self._move_toward(entity, target, allies, battle)

            if dist < min_dist:
                return self._move_away(entity, target, battle)
            elif dist > optimal_dist:
                return self._move_toward(entity, target, allies, battle)
            else:
                # In optimal range: seek cover or elevation advantage
                cover_move = self._seek_cover_position(entity, target, enemies, battle)
                if cover_move:
                    return cover_move

        # --- 5. MELEE: Approach target with smart positioning ---
        if preference == "melee":
            # If we can't see the target, move to get LOS first
            if not self._can_see_target(entity, target, battle):
                return self._move_toward(entity, target, allies, battle)

            # Calculate AoE threat level for anti-clustering
            aoe_threat = self._assess_aoe_threat(entity, enemies)
            spread_dest = None
            if aoe_threat > 10:
                spread_dest = self._find_spread_out_destination(entity, target, allies, battle)

            if dist > 0.5:
                return self._move_toward(entity, target, allies, battle, spread_dest)
            elif spread_dest:
                if int(entity.grid_x) != spread_dest[0] or int(entity.grid_y) != spread_dest[1]:
                    return self._move_toward(entity, target, allies, battle, spread_dest)

        # --- 6. AoE CASTER: Position for best cluster ---
        has_aoe = any(s.aoe_radius > 0 and s.damage_dice for s in spells)
        if has_aoe and preference == "ranged":
            result = self._best_aoe_cluster(entity, enemies, allies, battle, 20)
            if result:
                cluster, (cx, cy) = result
                if len(cluster) >= 2:
                    return self._move_toward_point(entity, cx, cy, battle)

        return None

    def _has_touch_healing(self, entity):
        """Check if entity has a way to heal adjacent allies."""
        if entity.lay_on_hands_left > 0:
            return True
        for spell in entity.stats.spells_known:
            if spell.heals and spell.range <= 5 and entity.has_spell_slot(spell.level):
                return True
        # Healing potions count as self-heal
        for item in entity.items:
            if item.item_type == "potion" and item.heals and (item.uses > 0 or item.uses == -1):
                return True
        return False

    def _seek_cover_position(self, entity, target, enemies, battle):
        """Find a nearby position with cover or elevation advantage that still has LOS to target.
        Returns a move ActionStep or None."""
        current_terrain_score = self._get_terrain_advantage_score(entity, battle, entity.grid_x, entity.grid_y)
        best_spot = None
        best_score = current_terrain_score

        max_squares = min(int(entity.movement_left / 5.0), 4)  # Don't wander too far

        for dx in range(-max_squares, max_squares + 1):
            for dy in range(-max_squares, max_squares + 1):
                nx, ny = int(entity.grid_x) + dx, int(entity.grid_y) + dy
                if dx == 0 and dy == 0:
                    continue
                if not self._is_safe_passable(battle, nx, ny, entity):
                    continue
                move_dist = math.hypot(dx, dy) * 5
                if move_dist > entity.movement_left:
                    continue

                # Must still have LOS to primary target
                from engine.terrain import check_los_blocked
                if check_los_blocked(battle.terrain, nx, ny, int(target.grid_x), int(target.grid_y)):
                    continue

                # Must still be in range
                new_dist = math.hypot(nx - target.grid_x, ny - target.grid_y) * 5
                if new_dist > 120:  # Max reasonable range
                    continue

                score = self._get_terrain_advantage_score(entity, battle, nx, ny)

                # Bonus for distance from nearest melee enemy
                min_enemy_dist = min(
                    (math.hypot(nx - e.grid_x, ny - e.grid_y) for e in enemies if e.hp > 0),
                    default=20)
                if min_enemy_dist > 2:
                    score += min(min_enemy_dist, 6) * 0.5

                if score > best_score + 2:  # Need meaningful improvement
                    best_score = score
                    best_spot = (nx, ny, move_dist)

        if best_spot:
            nx, ny, move_dist = best_spot
            old_x, old_y = entity.grid_x, entity.grid_y
            entity.grid_x, entity.grid_y = float(nx), float(ny)
            entity.movement_left -= move_dist
            reason = "seeks cover" if best_score > current_terrain_score + 3 else "repositions"
            return ActionStep(
                step_type="move",
                description=f"{entity.name} {reason} ({move_dist:.0f} ft).",
                attacker=entity, new_x=float(nx), new_y=float(ny),
                movement_ft=move_dist, old_x=old_x, old_y=old_y,
            )
        return None

    def _move_to_get_los(self, entity, target, battle):
        """Find a nearby position that has LOS to target. For ranged entities blocked by walls."""
        from engine.terrain import check_los_blocked
        best_spot = None
        best_dist_to_target = 999

        max_squares = min(int(entity.movement_left / 5.0), 6)

        for dx in range(-max_squares, max_squares + 1):
            for dy in range(-max_squares, max_squares + 1):
                nx, ny = int(entity.grid_x) + dx, int(entity.grid_y) + dy
                if dx == 0 and dy == 0:
                    continue
                if not self._is_safe_passable(battle, nx, ny, entity):
                    continue
                move_dist = math.hypot(dx, dy) * 5
                if move_dist > entity.movement_left:
                    continue
                # Check if this position has LOS to target
                if check_los_blocked(battle.terrain, nx, ny, int(target.grid_x), int(target.grid_y)):
                    continue
                # Prefer positions closest to target but still with decent range
                dist_to_target = math.hypot(nx - target.grid_x, ny - target.grid_y)
                if dist_to_target < best_dist_to_target:
                    best_dist_to_target = dist_to_target
                    best_spot = (nx, ny, move_dist)

        if best_spot:
            nx, ny, move_dist = best_spot
            old_x, old_y = entity.grid_x, entity.grid_y
            entity.grid_x, entity.grid_y = float(nx), float(ny)
            entity.movement_left -= move_dist
            return ActionStep(
                step_type="move",
                description=f"{entity.name} moves to get line of sight ({move_dist:.0f} ft).",
                attacker=entity, new_x=float(nx), new_y=float(ny),
                movement_ft=move_dist, old_x=old_x, old_y=old_y,
            )
        return None

    def _is_safe_passable(self, battle, x, y, entity, allow_jump=False):
        # First check standard passability
        if not battle.is_passable(x, y, exclude=entity):
            # Special case: closed (unlocked) door - AI can open it
            t = battle.get_terrain_at(int(x), int(y))
            if t and t.is_door and not t.door_open and not t.is_locked:
                # Door can be opened - treat as passable
                return True
            # Special case: gap/chasm - jumpable or flyable
            if t and t.is_gap:
                if entity.is_flying:
                    return not battle.is_occupied(x, y, exclude=entity)
                if allow_jump and entity.can_jump_gap(t.gap_width_ft, running_start=True):
                    return not battle.is_occupied(x, y, exclude=entity)
            return False
        # Flying entities ignore ground hazards
        if entity.is_flying:
            return True
        t = battle.get_terrain_at(int(x), int(y))
        if t and t.is_hazard:
            return False
        return True

    def _find_path(self, start, end, battle, entity, allow_jump=True):
        """A* Pathfinding to find optimal path around obstacles.
        allow_jump: if True, consider jumping across gaps/chasms."""
        def heuristic(a, b):
            return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        # Track which steps require jumping (for movement execution)
        self._path_jump_tiles = set()

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

                    if not self._is_safe_passable(battle, nx, ny, entity, allow_jump=allow_jump):
                        continue

                    move_cost = battle.get_terrain_movement_cost(nx, ny, entity)
                    # Doors cost extra (object interaction)
                    t = battle.get_terrain_at(int(nx), int(ny))
                    if t and t.is_door and not t.door_open:
                        move_cost += 0.5  # Small penalty so AI prefers open paths
                    # Gaps cost extra (jump cost = gap width in movement feet)
                    if t and t.is_gap and not entity.is_flying:
                        jump_cost = t.gap_width_ft / 5.0  # Convert to grid cost
                        move_cost += jump_cost
                        self._path_jump_tiles.add(neighbor)
                    # Climbing cost for going up to climbable terrain
                    if t and t.is_climbable and not entity.is_flying:
                        if entity.stats.climb_speed <= 0:
                            move_cost += 1.0  # Extra cost for climbing without climb speed

                    tentative_g = g_score[current] + move_cost

                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        f = tentative_g + heuristic(neighbor, end)
                        heapq.heappush(open_set, (f, neighbor))

        # No normal path found - try with jumping if not already
        if not allow_jump:
            return None

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

        jump_tiles = getattr(self, '_path_jump_tiles', set())
        jumped_over = False

        if path:
            from engine.rules import can_move_toward_fear_source
            fear_source = entity.get_condition_source("Frightened") if entity.has_condition("Frightened") else None

            for (nx, ny) in path:
                cost = 5.0 * battle.get_terrain_movement_cost(nx, ny, entity)
                is_jump = (nx, ny) in jump_tiles

                # Jump cost: gap width in feet of movement (PHB p.182)
                if is_jump:
                    t_gap = battle.get_terrain_at(int(nx), int(ny))
                    if t_gap and t_gap.is_gap:
                        jump_ft = t_gap.gap_width_ft
                        cost = entity.get_jump_cost(jump_ft)
                        # Need 10ft running start for full long jump
                        if entity.movement_left < cost:
                            break

                if entity.movement_left < cost:
                    break

                # Auto-open closed unlocked doors (free object interaction)
                t_at = battle.get_terrain_at(int(nx), int(ny))
                if t_at and t_at.is_door and not t_at.door_open and not t_at.is_locked:
                    battle.toggle_door_at(int(nx), int(ny))

                # PHB p.290: Frightened creatures can't move closer to fear source
                if fear_source:
                    allowed, _ = can_move_toward_fear_source(entity, nx, ny, fear_source)
                    if not allowed:
                        break

                old_x, old_y = entity.grid_x, entity.grid_y
                # If jumping over gap, use is_jumping=True to avoid falling
                if is_jump:
                    battle.move_entity_with_elevation(entity, nx, ny, is_jumping=True)
                    jumped_over = True
                else:
                    entity.grid_x, entity.grid_y = nx, ny
                entity.movement_left -= cost

                # PHB p.195: Drag grappled creatures along when moving
                for grappled_target in entity.grappling:
                    if grappled_target.hp > 0:
                        grappled_target.grid_x = old_x
                        grappled_target.grid_y = old_y

                if battle.is_adjacent(entity, target):
                    break

        moved_cost = start_movement - entity.movement_left
        dist_moved = math.hypot(entity.grid_x - start_x, entity.grid_y - start_y)

        if dist_moved < 0.1:
            return None

        drag_note = ""
        if entity.grappling:
            dragged_names = [g.name for g in entity.grappling if g.hp > 0]
            if dragged_names:
                drag_note = f" (dragging {', '.join(dragged_names)})"
        jump_note = " (jumps across gap!)" if jumped_over else ""

        return ActionStep(
            step_type="move",
            description=f"{entity.name} moves {moved_cost:.0f} ft.{jump_note}{drag_note}",
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
                    if self._is_safe_passable(battle, nx, ny, entity, allow_jump=True):
                        valid_adj.append((nx, ny))
            if valid_adj:
                dest_x, dest_y = min(valid_adj, key=lambda p: math.hypot(p[0] - entity.grid_x, p[1] - entity.grid_y))

        path = self._find_path((int(entity.grid_x), int(entity.grid_y)),
                               (int(dest_x), int(dest_y)), battle, entity)

        jump_tiles = getattr(self, '_path_jump_tiles', set())
        jumped = False
        if path:
            for (nx, ny) in path:
                is_jump = (nx, ny) in jump_tiles
                if is_jump:
                    t_gap = battle.get_terrain_at(int(nx), int(ny))
                    cost = entity.get_jump_cost(t_gap.gap_width_ft) if t_gap and t_gap.is_gap else 5.0
                else:
                    cost = 5.0 * battle.get_terrain_movement_cost(nx, ny, entity)
                if entity.movement_left < cost:
                    break
                if is_jump:
                    battle.move_entity_with_elevation(entity, nx, ny, is_jumping=True)
                    jumped = True
                else:
                    entity.grid_x, entity.grid_y = nx, ny
                entity.movement_left -= cost

        moved_cost = start_movement - entity.movement_left
        dist_moved = math.hypot(entity.grid_x - start_x, entity.grid_y - start_y)

        if dist_moved < 0.1:
            return None

        jump_note = " (jumps across gap!)" if jumped else ""
        return ActionStep(
            step_type="move",
            description=f"{entity.name} repositions {moved_cost:.0f} ft.{jump_note}",
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
                # Auto-open doors when fleeing
                t_at = battle.get_terrain_at(int(chosen[0]), int(chosen[1]))
                if t_at and t_at.is_door and not t_at.door_open and not t_at.is_locked:
                    battle.toggle_door_at(int(chosen[0]), int(chosen[1]))

                cost = 5.0 * battle.get_terrain_movement_cost(chosen[0], chosen[1], entity)
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
        """Optimal action selection with full knowledge of all options.

        Evaluates ALL possible actions and picks the highest EV (expected value) option.
        No randomness in decision-making - every choice is deterministic and optimal.
        """
        if entity.action_used:
            return []

        # === EMERGENCY: Paladin Lay on Hands for dying ally ===
        if entity.lay_on_hands_left >= 1:
            loh_steps = self._try_lay_on_hands(entity, allies, battle)
            if loh_steps:
                entity.action_used = True
                return loh_steps

        # === EMERGENCY: Stabilize dying ally (Medicine DC 10, no healing available) ===
        if not self._has_touch_healing(entity):
            dying_allies = [a for a in allies if a.hp <= 0 and not a.is_stable
                            and a.death_save_failures < 3 and not a.is_summon]
            for dying in dying_allies:
                if battle.is_adjacent(entity, dying):
                    # Medicine check: d20 + WIS mod (+ proficiency if proficient)
                    wis_mod = entity.stats.abilities.get_mod("wisdom")
                    med_bonus = entity.stats.skills.get("Medicine", wis_mod)
                    roll = random.randint(1, 20) + med_bonus
                    entity.action_used = True
                    if roll >= 10:
                        dying.is_stable = True
                        dying.death_save_successes = 3
                        return [ActionStep(
                            step_type="wait",
                            description=f"{entity.name} stabilizes {dying.name} (Medicine {roll} vs DC 10).",
                            attacker=entity, target=dying, action_name="Stabilize",
                        )]
                    else:
                        return [ActionStep(
                            step_type="wait",
                            description=f"{entity.name} fails to stabilize {dying.name} (Medicine {roll} vs DC 10).",
                            attacker=entity, target=dying, action_name="Stabilize",
                        )]

        # === EMERGENCY: Self-heal if critical ===
        pref = self._get_combat_preference(entity)
        heal_threshold = HEAL_MELEE_THRESHOLD if pref == "melee" else HEAL_RANGED_THRESHOLD
        if entity.max_hp > 0 and (entity.hp / entity.max_hp < heal_threshold):
            heal_step = self._try_heal_action(entity)
            if heal_step:
                entity.action_used = True
                return [heal_step]

        # === EVALUATE ALL OPTIONS AND PICK BEST ===
        # Build a list of (score, action_fn) and pick the highest
        candidates = []

        # --- Channel Divinity (Turn Undead etc.) ---
        if entity.has_feature("channel_divinity") and entity.channel_divinity_left > 0:
            tu_step = self._try_turn_undead(entity, enemies, battle)
            if tu_step:
                candidates.append((35.0, "turn_undead", [tu_step]))

        # --- Self-buff (Mirror Image, etc.) ---
        buff_step = self._try_self_buff(entity, enemies, battle)
        if buff_step:
            # Score based on how threatened we are
            threats = [e for e in enemies if battle.is_adjacent(entity, e) and e.hp > 0]
            buff_score = 15.0 + len(threats) * 5
            candidates.append((buff_score, "buff", [buff_step]))

        # --- Disengage (for ranged characters stuck in melee) ---
        hp_threshold = 0.5 if (entity.stats.abilities.intelligence > 12 and pref == "ranged") else 0.25
        if entity.max_hp > 0 and (entity.hp / entity.max_hp < hp_threshold):
            disengage_step = self._try_disengage_action(entity, enemies, battle, pref)
            if disengage_step:
                candidates.append((20.0, "disengage", [disengage_step]))

        # --- Dodge (defensive action when low HP and surrounded) ---
        dodge_step = self._try_dodge_action(entity, enemies, battle)
        if dodge_step:
            threats = [e for e in enemies if battle.is_adjacent(entity, e) and e.hp > 0]
            hp_pct = entity.hp / max(entity.max_hp, 1)
            # Higher score when low HP and many adjacent threats
            dodge_score = len(threats) * 10 * (1.0 - hp_pct)
            if dodge_score > 0:
                candidates.append((dodge_score, "dodge", [dodge_step]))

        # --- AoE spell ---
        if entity.has_spell_slot(1) or entity.stats.cantrips:
            aoe_step = self._try_aoe_spell(entity, enemies, allies, battle)
            if aoe_step:
                # Score AoE based on expected total damage
                aoe_score = aoe_step.damage * max(len(aoe_step.targets), 1) * 0.7
                candidates.append((aoe_score, "aoe_spell", [aoe_step]))

        # --- Debuff spell (high-value control) ---
        if entity.has_spell_slot(1):
            debuff_step = self._try_debuff_spell(entity, enemies, allies, battle)
            if debuff_step:
                # Score debuff based on condition value and target value
                debuff_score = self._score_debuff_value(debuff_step, entity, enemies)
                candidates.append((debuff_score, "debuff", [debuff_step]))

        # --- Terrain-creating spell (non-damage: Darkness, Fog Cloud, Silence) ---
        if entity.has_spell_slot(1):
            terrain_step = self._try_terrain_spell(entity, enemies, allies, battle)
            if terrain_step:
                candidates.append((terrain_step[0], "terrain_spell", terrain_step[1]))

        # --- Damage spell / cantrip ---
        if entity.stats.spells_known or entity.stats.cantrips:
            spell_step = self._try_damage_spell(entity, enemies, battle)
            if spell_step:
                spell_score = spell_step.damage * (0.65 if spell_step.is_hit or spell_step.save_ability else 0.3)
                candidates.append((spell_score, "damage_spell", [spell_step]))

        # --- Grapple/Shove tactics (evaluated deterministically) ---
        grapple_shove_steps = self._evaluate_grapple_shove(entity, enemies, allies, battle)
        if grapple_shove_steps:
            gs_score, gs_steps = grapple_shove_steps
            candidates.append((gs_score, "grapple_shove", gs_steps))

        # --- Multiattack ---
        multi = next((a for a in entity.stats.actions if a.is_multiattack), None)
        if multi:
            steps = self._execute_multiattack(entity, multi, enemies, allies, battle)
            if steps:
                total_dmg = sum(s.damage for s in steps if s.is_hit)
                multi_score = total_dmg * 0.8
                candidates.append((multi_score, "multiattack", steps))

        # --- Single best attack ---
        if not multi:
            single_steps = self._evaluate_best_single_attack(entity, enemies, allies, battle)
            if single_steps:
                sa_score, sa_steps = single_steps
                candidates.append((sa_score, "single_attack", sa_steps))

        # --- Heal wounded ally (not emergency - tactical healing) ---
        heal_ally_step = self._try_heal_wounded_ally(entity, allies, battle)
        if heal_ally_step:
            # Score based on ally HP deficit and danger
            candidates.append((heal_ally_step[0], "heal_ally", heal_ally_step[1]))

        # === PICK BEST OPTION ===
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            best_score, best_type, best_steps = candidates[0]

            # Apply side effects based on action type
            if best_type == "turn_undead":
                entity.channel_divinity_left -= 1
            elif best_type in ("aoe_spell", "damage_spell", "debuff"):
                pass  # Spell slot already consumed in try_ method
            elif best_type == "buff":
                pass  # Already handled
            elif best_type == "disengage":
                pass
            elif best_type in ("multiattack", "single_attack", "grapple_shove"):
                pass

            entity.action_used = True
            return best_steps

        # Fallback: Dash toward nearest enemy
        return self._try_dash_action(entity, enemies, allies, battle)

    def suggest_alternative(self, entity, battle, skipped_step) -> Optional[ActionStep]:
        """Suggest an alternative action after DM skips a step.

        Temporarily refunds resources consumed by the skipped step, then
        re-evaluates all options excluding the skipped action/spell.
        Returns a single ActionStep or None.
        """
        # Refund resources consumed by the skipped step
        if skipped_step.slot_used and skipped_step.slot_used > 0:
            entity.restore_spell_slot(skipped_step.slot_used)
        if skipped_step.step_type in ("attack", "multiattack", "spell") and skipped_step.attacker:
            entity.action_used = False

        excluded_name = skipped_step.action_name or (skipped_step.spell.name if skipped_step.spell else "")

        enemies = [e for e in battle.entities if e.hp > 0 and e.is_player != entity.is_player]
        allies  = [a for a in battle.entities if a.hp > 0 and a.is_player == entity.is_player and a != entity]

        # Re-run candidate evaluation (same as _decide_action but excluding the skipped action)
        pref = self._get_combat_preference(entity)
        candidates = []

        if entity.has_spell_slot(1) or entity.stats.cantrips:
            aoe_step = self._try_aoe_spell(entity, enemies, allies, battle)
            if aoe_step and aoe_step.action_name != excluded_name:
                aoe_score = aoe_step.damage * max(len(aoe_step.targets), 1) * 0.7
                candidates.append((aoe_score, aoe_step))

        if entity.has_spell_slot(1):
            debuff_step = self._try_debuff_spell(entity, enemies, allies, battle)
            if debuff_step and debuff_step.action_name != excluded_name:
                debuff_score = self._score_debuff_value(debuff_step, entity, enemies)
                candidates.append((debuff_score, debuff_step))

        if entity.stats.spells_known or entity.stats.cantrips:
            spell_step = self._try_damage_spell(entity, enemies, battle)
            if spell_step and spell_step.action_name != excluded_name:
                spell_score = spell_step.damage * 0.65
                candidates.append((spell_score, spell_step))

        multi = next((a for a in entity.stats.actions if a.is_multiattack), None)
        if multi and multi.name != excluded_name:
            steps = self._execute_multiattack(entity, multi, enemies, allies, battle)
            if steps:
                total_dmg = sum(s.damage for s in steps if s.is_hit)
                # Return first step of multiattack as alternative
                candidates.append((total_dmg * 0.8, steps[0]))

        if not multi:
            single = self._evaluate_best_single_attack(entity, enemies, allies, battle)
            if single:
                sa_score, sa_steps = single
                if sa_steps and sa_steps[0].action_name != excluded_name:
                    candidates.append((sa_score, sa_steps[0]))

        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1]
        return None

    def _evaluate_grapple_shove(self, entity, enemies, allies, battle):
        """Deterministic grapple/shove evaluation.

        Returns (score, steps) or None.
        No randomness - uses EV calculations to decide when to grapple/shove.
        """
        from engine.rules import can_shove, can_grapple as can_grapple_check

        alive_enemies = [e for e in enemies if e.hp > 0]
        best_score = 0
        best_steps = None

        for target in alive_enemies:
            if not battle.is_adjacent(entity, target):
                continue

            engaging_allies = [a for a in allies if battle.is_adjacent(a, target) and a.hp > 0]
            our_athletics = entity.get_skill_bonus("Athletics") + entity.get_modifier("Strength")

            # Target's best contested check
            target_athletics = target.get_skill_bonus("Athletics") + target.get_modifier("Strength")
            target_acrobatics = target.get_skill_bonus("Acrobatics") + target.get_modifier("Dexterity")
            target_best = max(target_athletics, target_acrobatics)

            # Estimate success chance: (our roll + bonus) vs (their roll + bonus)
            # Avg d20 = 10.5, so our expected total vs their expected total
            our_expected = 10.5 + our_athletics
            their_expected = 10.5 + target_best
            # Use advantage if we have it
            if entity.has_attack_advantage(target, is_ranged=False):
                our_expected = 13.8 + our_athletics  # Advantage avg ~13.8
            success_chance = max(0.1, min(0.95, 0.5 + (our_expected - their_expected) * 0.05))

            # --- COMBO: If target already grappled by us, SHOVE PRONE (devastating) ---
            if (target.has_condition("Grappled") and target.grappled_by == entity
                    and not target.has_condition("Prone")):
                shove_ok, _ = can_shove(entity, target)
                if shove_ok:
                    # This creates permanent advantage (target can't stand while grappled)
                    # Value = advantage bonus * remaining attacks from allies * expected combat length
                    combo_value = GRAPPLE_SHOVE_COMBO_VALUE * success_chance
                    combo_value += len(engaging_allies) * 10 * success_chance  # More allies = more value
                    shove_step = self._try_shove_action(entity, target)
                    if shove_step and combo_value > best_score:
                        best_score = combo_value
                        best_steps = [shove_step]

            # --- GRAPPLE: Start the grapple+prone combo ---
            if not target.has_condition("Grappled"):
                grapple_ok, _ = can_grapple_check(entity, target)
                if grapple_ok:
                    # Value depends on:
                    # 1. How many allies are adjacent (they all benefit from prone combo)
                    # 2. Is the target a high-value enemy? (worth locking down)
                    # 3. Can we follow up with shove next turn?
                    # 4. Is this a single powerful enemy? (lock-down is key strategy)
                    grapple_value = 0.0

                    # High value if outnumbering single enemy (lock them down!)
                    live_enemies = len([e for e in enemies if e.hp > 0])
                    live_allies = len([a for a in allies if a.hp > 0])
                    if live_enemies == 1 and live_allies >= 2:
                        grapple_value += 35 * success_chance  # Lock down the solo enemy
                    elif live_enemies <= 2 and live_allies >= 3:
                        grapple_value += 25 * success_chance

                    # Bonus for high-DPR targets (neutralize their threat)
                    target_dpr = self._estimate_entity_dpr(target)
                    if target_dpr > 15:
                        grapple_value += target_dpr * 0.5 * success_chance

                    # Bonus if we have allies to follow up with attacks
                    grapple_value += len(engaging_allies) * 5 * success_chance

                    # Bonus if target is a caster (grapple prevents escape)
                    if target.stats.spellcasting_ability and self._get_combat_preference(target) == "ranged":
                        grapple_value += 15 * success_chance

                    # Penalty: grapple uses our action, so compare vs just attacking
                    our_attack_dmg = self._estimate_entity_dpr(entity)
                    grapple_value -= our_attack_dmg * 0.3  # Opportunity cost

                    grapple_step = self._try_grapple_action(entity, target)
                    if grapple_step and grapple_value > best_score:
                        best_score = grapple_value
                        best_steps = [grapple_step]

            # --- SHOVE PRONE (standalone, without grapple) ---
            if not target.has_condition("Prone") and not target.has_condition("Grappled"):
                shove_ok, _ = can_shove(entity, target)
                if shove_ok and len(engaging_allies) >= 1:
                    # Value: allies get advantage on melee attacks this round
                    shove_value = len(engaging_allies) * 8 * success_chance
                    # Extra value if many melee allies
                    melee_allies = [a for a in engaging_allies
                                    if self._get_combat_preference(a) == "melee"]
                    shove_value += len(melee_allies) * 5 * success_chance

                    shove_step = self._try_shove_action(entity, target)
                    if shove_step and shove_value > best_score:
                        best_score = shove_value
                        best_steps = [shove_step]

            # --- SHOVE-TO-HAZARD (push into lava / off cliff / into pit) ---
            if not target.has_condition("Grappled"):
                hazard_score = self._score_shove_to_hazard(entity, target, battle)
                if hazard_score > 0:
                    hazard_score *= success_chance
                    if hazard_score > best_score:
                        shove_step = self._try_shove_action(
                            entity, target, prone=False, battle=battle
                        )
                        if shove_step:
                            best_score = hazard_score
                            best_steps = [shove_step]

        if best_steps and best_score > 0:
            return (best_score, best_steps)
        return None

    def _score_shove_to_hazard(self, entity, target, battle) -> float:
        """Estimate the damage value of shoving ``target`` 5 ft away from
        ``entity`` without actually moving anyone. Handles:
          * Lava / fire / acid / spikes ground hazards (full hazard damage)
          * Gaps / chasms (fall damage + gap hazard)
          * Cliff edges (drop of 10+ feet from platform)
        Returns 0 if the push would only land on ordinary ground.
        """
        from engine.terrain import calculate_fall_damage
        from engine.dice import average_damage

        dx = target.grid_x - entity.grid_x
        dy = target.grid_y - entity.grid_y
        step_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
        step_y = 1 if dy > 0 else (-1 if dy < 0 else 0)
        if abs(dx) > abs(dy) * 1.2:
            step_y = 0
        elif abs(dy) > abs(dx) * 1.2:
            step_x = 0
        if step_x == 0 and step_y == 0:
            return 0.0

        nx = int(target.grid_x + step_x)
        ny = int(target.grid_y + step_y)

        if battle.is_occupied(nx, ny, exclude=target):
            return 0.0
        t = battle.get_terrain_at(nx, ny)

        score = 0.0
        # Gap / chasm — huge score (fall + possible lava chasm)
        if t is not None and getattr(t, "is_gap", False) and not target.is_flying:
            fall_ft = abs(t.elevation) + target.elevation
            score += calculate_fall_damage(fall_ft) if fall_ft >= 10 else 0
            if t.is_hazard:
                score += average_damage(t.hazard_damage)
            # Flat bonus for a guaranteed "removed from the fight" outcome
            score += 20
            return score

        # Wall / impassable — no push possible
        if t is not None and not t.passable:
            return 0.0

        # Platform edge: pushed to a tile that drops >=10 ft
        dest_elev = battle.get_elevation_at(nx, ny)
        drop = target.elevation - dest_elev
        if drop >= 10 and not target.is_flying:
            score += calculate_fall_damage(drop)

        # Ground hazard at destination
        if t is not None and t.is_hazard:
            avg = average_damage(t.hazard_damage)
            # Lava-tier hazards are catastrophic (10d10 fire)
            if t.terrain_type in ("lava", "lava_chasm"):
                score += avg * 1.5  # effectively a kill
            else:
                score += avg

        return score

    def _evaluate_best_single_attack(self, entity, enemies, allies, battle):
        """Evaluate and return best single attack with EV scoring."""
        alive_enemies = [e for e in enemies if e.hp > 0]
        sorted_enemies = sorted(alive_enemies, key=lambda e: self._score_target(entity, e, battle), reverse=True)

        best_score = -1
        best_steps = None

        for target in sorted_enemies:
            best_action = self._best_melee_or_ranged(entity, target, battle)
            if best_action:
                # Calculate EV
                dist = battle.get_distance(entity, target)
                is_ranged = best_action.range > 10
                adv = entity.has_attack_advantage(target, is_ranged, dist)
                dis = entity.has_attack_disadvantage(target, is_ranged, battle=battle)

                dmg_str = f"{best_action.damage_dice}+{best_action.damage_bonus}" if best_action.damage_bonus else best_action.damage_dice
                base_dmg = average_damage(dmg_str)

                # Account for resistance/vulnerability
                base_dmg = self._estimate_damage(dmg_str, best_action.damage_type, target)

                hit_chance = (21 + best_action.attack_bonus - target.stats.armor_class) / 20.0
                if adv and not dis:
                    hit_chance = 1 - (1 - hit_chance) ** 2
                if dis and not adv:
                    hit_chance = hit_chance ** 2
                hit_chance = max(0.05, min(0.95, hit_chance))

                ev = base_dmg * hit_chance

                # Bonus damage from class features
                if entity.rage_active and best_action.range <= 5:
                    ev += entity.get_rage_damage_bonus() * hit_chance
                if entity.has_feature("sneak_attack") and not entity.sneak_attack_used:
                    sa_dice = entity.get_sneak_attack_dice()
                    if sa_dice:
                        ally_adj = any(battle.is_adjacent(a, target) for a in allies if a.hp > 0)
                        has_adv = entity.has_attack_advantage(target, is_ranged)
                        if ally_adj or has_adv:
                            ev += average_damage(sa_dice) * hit_chance

                # Kill bonus
                if base_dmg >= target.hp:
                    ev *= 1.3

                # Target priority bonus
                ev += self._score_target(entity, target) * 0.1

                if ev > best_score:
                    best_score = ev

                    # Actually execute the attack
                    if entity.get_feature_by_name(best_action.name):
                        entity.use_feature(best_action.name)

                    step = self._execute_attack(entity, best_action, target, battle)
                    self._apply_class_attack_bonuses(entity, step, target, allies, battle)
                    best_steps = [step]
                    break  # Take the best target (already sorted by _score_target)

        if best_steps:
            return (best_score, best_steps)
        return None

    def _score_debuff_value(self, debuff_step, entity, enemies):
        """Score the value of a debuff spell."""
        score = 15.0  # Base value for landing a debuff

        if debuff_step.spell:
            spell = debuff_step.spell
            # High-level spells are more valuable
            score += spell.level * 5

            # Hold Person/Monster on melee enemies = devastating (paralyzed = auto-crit)
            cond = spell.applies_condition
            if cond in ("Paralyzed", "Stunned"):
                score += 30
            elif cond in ("Restrained", "Blinded"):
                score += 20
            elif cond in ("Frightened", "Charmed"):
                score += 15

            # Target the enemy with worst save
            if debuff_step.target:
                save_bonus = debuff_step.target.get_save_bonus(spell.save_ability)
                dc = debuff_step.save_dc or entity.stats.spell_save_dc or 13
                fail_chance = 1.0 - ((21 + save_bonus - dc) / 20.0)
                fail_chance = max(0.05, min(0.95, fail_chance))
                score *= fail_chance

                # Extra value for high-DPR targets
                target_dpr = self._estimate_entity_dpr(debuff_step.target)
                score += target_dpr * 0.3

                # Penalty for legendary resistance targets
                if debuff_step.target.legendary_resistances_left > 0:
                    score -= 15 * debuff_step.target.legendary_resistances_left

        return score

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
                # Ranged healing spells need LOS (touch spells don't)
                if spell.range > 5 and not battle.has_line_of_sight(entity, target):
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

    def _try_heal_wounded_ally(self, entity, allies, battle):
        """Evaluate healing a wounded (but alive) ally as a tactical option.

        Returns (score, [ActionStep]) or None.
        Only triggers when an ally is below 40% HP and healing is available.
        Competes with offensive options via the scoring system.
        """
        wounded = [a for a in allies if 0 < a.hp < a.max_hp * 0.4 and not a.is_summon]
        if not wounded:
            return None

        # Find best healing spell (action-type)
        healing_spells = [s for s in entity.stats.spells_known
                          if s.heals and s.action_type == "action" and entity.can_cast_spell(s)]
        if not healing_spells:
            return None

        # Pick most wounded ally that's in range
        wounded.sort(key=lambda a: a.hp / max(a.max_hp, 1))

        for target in wounded:
            for spell in healing_spells:
                dist_ft = battle.get_distance(entity, target) * 5
                if dist_ft > spell.range:
                    continue
                if spell.range > 5 and not battle.has_line_of_sight(entity, target):
                    continue

                slot = spell.level
                # Calculate expected healing
                heal_amount = roll_dice(spell.heals)
                hp_deficit = target.max_hp - target.hp
                effective_heal = min(heal_amount, hp_deficit)

                # Score: more valuable when ally is close to death
                hp_pct = target.hp / max(target.max_hp, 1)
                urgency = (1.0 - hp_pct) * 30  # 0-30 bonus based on how low they are
                # Healers (cleric/druid/bard) get extra healing score
                score = effective_heal * 0.5 + urgency

                entity.use_spell_slot(slot)
                step = ActionStep(
                    step_type="spell",
                    description=f"{entity.name} casts {spell.name} on {target.name}, healing {heal_amount} HP.",
                    attacker=entity, target=target, spell=spell, slot_used=slot,
                    action_name=spell.name, damage=heal_amount, damage_type="healing"
                )
                return (score, [step])
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
        # Pick best healing potion (don't waste high-tier potions on small wounds)
        hp_deficit = entity.max_hp - entity.hp
        hp_pct = entity.hp / max(entity.max_hp, 1)
        best_potion = None
        best_avg = 0
        for item in entity.items:
            if not item.heals or item.item_type != "potion":
                continue
            if item.uses <= 0 and item.uses != -1:
                continue
            avg = average_damage(item.heals)
            # Don't waste supreme potion on small wounds unless desperate
            if avg > hp_deficit * 2.5 and hp_pct > 0.25:
                continue
            if avg > best_avg:
                best_avg = avg
                best_potion = item

        if best_potion:
            if best_potion.uses > 0:
                best_potion.uses -= 1
            healed = roll_dice(best_potion.heals)
            return ActionStep(
                step_type="spell",
                description=f"{entity.name} drinks {best_potion.name}, healing {healed} HP.",
                attacker=entity, target=entity, action_name=best_potion.name,
                damage=healed, damage_type="healing"
            )
        return None

    def _try_use_buff_potion(self, entity, enemies, battle):
        """Use a buff potion (resistance, speed, strength) pre-combat or when tactically smart.
        Returns an ActionStep or None. Consumes the item.
        Uses action (RAW: potions are an action to drink).
        """
        if entity.action_used:
            return None

        hp_pct = entity.hp / max(entity.max_hp, 1)

        for item in entity.items:
            if item.item_type != "potion" or item.uses <= 0 or not item.buff:
                continue

            buff = item.buff
            use = False

            # Potion of Speed (Haste) - high value, use when multiple enemies
            if buff == "haste" and len([e for e in enemies if e.hp > 0]) >= 2:
                use = True

            # Resistance potions - use if facing matching damage type
            elif buff.startswith("resistance:"):
                dmg_type = buff.split(":")[1]
                # Check if any enemy deals this damage type
                for enemy in enemies:
                    if enemy.hp <= 0:
                        continue
                    for a in enemy.stats.actions:
                        if a.damage_type == dmg_type:
                            use = True
                            break
                    if use:
                        break
                    for s in enemy.stats.spells_known + enemy.stats.cantrips:
                        if s.damage_type == dmg_type:
                            use = True
                            break
                    if use:
                        break

            # Strength potions - melee fighters when STR < potion value
            elif buff.startswith("strength:"):
                new_str = int(buff.split(":")[1])
                if (entity.stats.abilities.strength < new_str
                        and self._get_combat_preference(entity) == "melee"):
                    use = True

            # Temp HP potions
            elif buff.startswith("temp_hp:") and hp_pct < 0.8:
                use = True

            # Invisibility - use when low HP and ranged fighter
            elif buff == "invisible" and hp_pct < 0.4:
                use = True

            if use:
                item.uses -= 1
                desc = f"{entity.name} drinks {item.name}."

                # Apply buff effects
                if buff == "haste":
                    entity.active_effects["Haste"] = 10
                    desc += " [Hasted!]"
                elif buff.startswith("resistance:"):
                    dmg_type = buff.split(":")[1]
                    entity.active_effects[f"Potion Resistance ({dmg_type})"] = 100
                    if dmg_type not in entity.stats.damage_resistances:
                        entity.stats.damage_resistances.append(dmg_type)
                    desc += f" [Resistance to {dmg_type}]"
                elif buff.startswith("strength:"):
                    new_str = int(buff.split(":")[1])
                    entity.stats.abilities.strength = new_str
                    desc += f" [STR → {new_str}]"
                elif buff.startswith("temp_hp:"):
                    thp = int(buff.split(":")[1])
                    entity.temp_hp = max(entity.temp_hp, thp)
                    desc += f" [+{thp} temp HP]"
                elif buff == "invisible":
                    entity.add_condition("Invisible")
                    entity.active_effects["Potion Invisibility"] = 100
                    desc += " [Invisible]"
                elif buff.startswith("fly:"):
                    fly_speed = int(buff.split(":")[1])
                    entity.stats.fly_speed = max(entity.stats.fly_speed, fly_speed)
                    entity.active_effects["Potion Flying"] = 100
                    desc += f" [Fly {fly_speed} ft]"

                entity.action_used = True
                return ActionStep(
                    step_type="spell",
                    description=desc,
                    attacker=entity, target=entity,
                    action_name=item.name,
                )
        return None

    def _try_use_offensive_item(self, entity, target, battle):
        """Use an offensive consumable item (alchemist's fire, holy water, acid, etc).
        Returns an ActionStep or None.
        """
        if entity.action_used or not target or target.hp <= 0:
            return None

        best_item = None
        best_score = 0

        for item in entity.items:
            if item.uses <= 0 and item.uses != -1:
                continue
            if not item.damage_dice or item.item_type in ("weapon", "armor", "shield"):
                continue
            if item.heals:
                continue  # Healing items handled elsewhere

            score = 0
            avg = average_damage(item.damage_dice)

            # Holy Water: bonus vs undead/fiend
            if "holy water" in item.name.lower():
                if target.stats.creature_type.lower() in ("undead", "fiend"):
                    score = avg * 2  # Extra valuable vs undead/fiend
                else:
                    continue  # Don't waste on others

            # Alchemist's Fire: ongoing damage
            elif "alchemist" in item.name.lower():
                score = avg * 2  # Ongoing damage value

            # Acid
            elif "acid" in item.name.lower():
                score = avg

            # Necklace of Fireballs
            elif "fireball" in item.name.lower():
                nearby = [e for e in battle.get_enemies_of(entity)
                          if e.hp > 0 and battle.get_distance(target, e) * 5 <= 20]
                score = avg * max(1, len(nearby))

            # Generic damage items
            else:
                score = avg

            if score > best_score:
                best_score = score
                best_item = item

        if not best_item or best_score < 5:
            return None

        if best_item.uses > 0:
            best_item.uses -= 1

        dmg = roll_dice(best_item.damage_dice)
        entity.action_used = True
        return ActionStep(
            step_type="attack",
            description=f"{entity.name} uses {best_item.name} on {target.name} for {dmg} damage.",
            attacker=entity, target=target,
            action_name=best_item.name,
            damage=dmg, damage_type=best_item.description.split()[-1] if best_item.damage_dice else "fire",
            is_hit=True,
        )

    def _try_use_healing_potion_bonus(self, entity):
        """Use a healing potion as a bonus action (common house rule / variant).
        Only used when entity has no better bonus action and is hurt.
        Returns an ActionStep or None.
        """
        if entity.bonus_action_used:
            return None

        hp_pct = entity.hp / max(entity.max_hp, 1)
        if hp_pct > 0.5:
            return None

        # Find best healing potion for the situation
        best_potion = None
        best_heal = 0
        hp_deficit = entity.max_hp - entity.hp

        for item in entity.items:
            if item.item_type != "potion" or item.uses <= 0:
                continue
            if not item.heals:
                continue

            avg_heal = average_damage(item.heals)
            # Don't waste supreme potion on small wounds
            if avg_heal > hp_deficit * 2 and hp_pct > 0.3:
                continue
            if avg_heal > best_heal:
                best_heal = avg_heal
                best_potion = item

        if not best_potion:
            return None

        best_potion.uses -= 1
        healed = roll_dice(best_potion.heals)
        entity.bonus_action_used = True
        return ActionStep(
            step_type="bonus_attack",
            description=f"{entity.name} drinks {best_potion.name}, healing {healed} HP.",
            attacker=entity, target=entity,
            action_name=best_potion.name,
            damage=healed, damage_type="healing",
        )

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
        if preference == "melee" and entity.hp > entity.max_hp * DISENGAGE_HP_LOW:
            return None
        if not threats:
            return None

        threat = threats[0]
        entity.is_disengaging = True
        move_step = self._move_away(entity, threat, battle)

        if move_step:
            move_step.description = f"{entity.name} Disengages (Action) and retreats."
            move_step.step_type = "move"
            return move_step
        entity.is_disengaging = False
        return None

    def _try_dodge_action(self, entity, enemies, battle):
        """Use Dodge action when threatened, low HP, and no good offensive option.

        PHB p.192: Until start of next turn, attacks against you have disadvantage
        (if you can see the attacker), and you have advantage on DEX saves.
        Only worth it when adjacent enemies threaten us and we're wounded.
        """
        threats = [e for e in enemies if battle.is_adjacent(entity, e) and e.hp > 0]
        if not threats:
            return None
        hp_pct = entity.hp / max(entity.max_hp, 1)
        # Only dodge when below threshold with 2+ threats, or critical threshold with 1+
        if hp_pct > DODGE_HP_THRESHOLD:
            return None
        if hp_pct > DODGE_CRITICAL_THRESHOLD and len(threats) < 2:
            return None

        entity.is_dodging = True
        return ActionStep(
            step_type="wait",
            description=f"{entity.name} takes the Dodge action (attacks have disadvantage).",
            attacker=entity, action_name="Dodge",
        )

    def _try_dash_action(self, entity, enemies, allies, battle):
        target = self._pick_target(entity, enemies, battle)
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
        """
        PHB p.195 Grapple:
        - Contested Athletics vs Athletics/Acrobatics
        - Target must be no more than one size larger
        - Grappler must not be incapacitated
        """
        from engine.rules import can_grapple, resolve_grapple

        allowed, reason = can_grapple(entity, target)
        if not allowed:
            return None

        success, msg = resolve_grapple(entity, target)
        if success:
            entity.start_grapple(target)
            return ActionStep(
                step_type="attack", description=msg,
                attacker=entity, target=target, action_name="Grapple",
                applies_condition="Grappled"
            )
        else:
            return ActionStep(
                step_type="attack", description=msg,
                attacker=entity, target=target, action_name="Grapple"
            )

    def _try_shove_action(self, entity, target, prone=True, battle=None):
        """
        PHB p.195-196 Shove:
        - Contested Athletics vs Athletics/Acrobatics
        - Target must be no more than one size larger
        - On success: knock prone OR push 5ft

        When ``prone=False`` and ``battle`` is provided, the push is actually
        applied via ``battle.push_entity`` so destination hazards / gaps /
        cliff falls trigger automatically.
        """
        from engine.rules import can_shove, resolve_shove

        allowed, reason = can_shove(entity, target)
        if not allowed:
            return None

        success, msg = resolve_shove(entity, target, prone=prone)
        if success and prone:
            target.add_condition("Prone")
            return ActionStep(
                step_type="attack", description=msg,
                attacker=entity, target=target, action_name="Shove",
                applies_condition="Prone"
            )
        if success and not prone and battle is not None:
            info = battle.push_entity(target, entity.grid_x, entity.grid_y,
                                       distance=5)
            extra = []
            if info["fell_into_gap"]:
                extra.append(f"pushed into {info['destination_type'] or 'a gap'}")
            elif info["hazard_damage"] > 0:
                extra.append(f"took {info['hazard_damage']} hazard damage at destination")
            elif info["fell_from"] >= 10:
                extra.append(f"fell {info['fell_from']} ft off the platform")
            if extra:
                msg = msg + " — " + "; ".join(extra)
            return ActionStep(
                step_type="attack", description=msg,
                attacker=entity, target=target, action_name="Shove"
            )
        return ActionStep(
            step_type="attack", description=msg,
            attacker=entity, target=target, action_name="Shove"
        )

    def _try_aoe_spell(self, entity, enemies, allies, battle):
        """Cast best AoE spell with optimal targeting.

        God-mode: evaluates EV per spell considering:
        - Exact save bonuses of each target
        - Damage immunities/resistances/vulnerabilities
        - Kill potential (overkill on weak enemies = waste)
        - Condition application value
        - Spell slot conservation
        Threshold: 2+ enemies for high damage, always if total EV > single target option.
        """
        aoe_spells = [s for s in entity.stats.spells_known if s.aoe_radius > 0 and s.damage_dice]
        if not aoe_spells:
            return None

        can_sculpt = entity.has_feature("sculpt_spells")

        best_step = None
        best_total_ev = 0.0

        for spell in aoe_spells:
            if spell.level == 0:
                continue
            if not entity.has_spell_slot(spell.level):
                continue

            # Lower threshold: 2 targets is worth it for most AoE
            # 1 target is worth it for very high damage spells (Disintegrate AoE, etc.)
            min_targets = 2
            avg_dmg = average_damage(spell.damage_dice)
            if avg_dmg > 30:
                min_targets = 1

            result = self._best_aoe_cluster(entity, enemies, allies, battle,
                                               spell.aoe_radius,
                                               shape=spell.aoe_shape,
                                               avoid_allies=not can_sculpt,
                                               damage_type=spell.damage_type)
            if not result:
                continue
            clusters, (cx, cy) = result
            if not clusters or len(clusters) < min_targets:
                continue

            # Calculate total EV per target with precise save calculations
            total_ev = 0.0
            dc = spell.save_dc_fixed or (entity.stats.spell_save_dc or 13)

            for t in clusters:
                base = self._estimate_damage(_get_spell_damage_dice(spell, entity), spell.damage_type, t)
                if base <= 0:
                    continue

                if spell.save_ability:
                    save_bonus = t.get_save_bonus(spell.save_ability)
                    # Check if target has magic resistance
                    has_magic_res = t.has_feature("magic_resistance")
                    fail_chance = 1.0 - ((21 + save_bonus - dc) / 20.0)
                    if has_magic_res:
                        # Advantage on save = square the success chance
                        success = 1.0 - fail_chance
                        fail_chance = 1.0 - (1.0 - (1.0 - success) ** 2)
                    fail_chance = max(0.05, min(0.95, fail_chance))

                    if spell.half_on_save:
                        ev = base * fail_chance + (base / 2.0) * (1.0 - fail_chance)
                    else:
                        ev = base * fail_chance
                else:
                    ev = base

                # Kill bonus (finishing off wounded enemies)
                if base >= t.hp:
                    ev *= 1.2

                # Concentration disruption bonus
                if t.concentrating_on:
                    ev += 5

                total_ev += ev

            # Slot efficiency: compare EV per slot level
            slot_efficiency = total_ev / max(spell.level, 1)

            if total_ev > best_total_ev:
                best_total_ev = total_ev
                best_step = (spell, clusters, cx, cy)

        if best_step:
            spell, clusters, cx, cy = best_step
            # Decide slot: upcast by 1 for big AoEs when 3+ enemies are caught and a higher slot is free.
            # Save top-tier slots (7+) for boss moments unless the caller really wants to burn them.
            chosen_slot = spell.level
            if spell.damage_scaling:
                highest = entity.get_highest_slot()
                if highest > spell.level and len(clusters) >= 3 and highest <= 6:
                    # Upcast one level to gain scaling damage on a crowd
                    if entity.spell_slots.get(entity._LEVEL_KEYS.get(spell.level + 1, ""), 0) > 0:
                        chosen_slot = spell.level + 1

            if chosen_slot != spell.level:
                ok = entity.use_spell_slot_exact(chosen_slot)
                if not ok:
                    chosen_slot = spell.level
                    ok = entity.use_spell_slot(spell.level)
            else:
                ok = entity.use_spell_slot(spell.level)
            if ok:
                slot = chosen_slot
                dc = spell.save_dc_fixed if spell.save_dc_fixed else \
                     (entity.stats.spell_save_dc or 8 + entity.stats.proficiency_bonus
                      + entity.get_modifier(entity.stats.spellcasting_ability))

                raw_dmg = roll_dice(_get_spell_damage_dice(spell, entity, slot))

                # Empowered Evocation: add INT mod to evocation damage
                if entity.has_feature("empowered_evocation"):
                    raw_dmg += entity.get_modifier("intelligence")

                # Elemental Affinity (Sorcerer): add CHA mod to matching element
                if entity.has_feature("elemental_affinity"):
                    raw_dmg += entity.get_modifier("charisma")

                if spell.concentration:
                    entity.start_concentration(spell)

                upcast_tag = f" [upcast {slot}]" if slot > spell.level else ""
                return ActionStep(
                    step_type="spell",
                    description=f"{entity.name} casts {spell.name} (DC {dc} {spell.save_ability}){upcast_tag}",
                    attacker=entity, targets=clusters, spell=spell, slot_used=slot,
                    damage=raw_dmg, damage_type=spell.damage_type,
                    action_name=spell.name, aoe_center=(cx, cy),
                    save_dc=dc if dc else 0,
                    save_ability=spell.save_ability,
                )
        return None

    def _try_debuff_spell(self, entity, enemies, allies, battle):
        """Cast best debuff spell targeting enemy's weakest save.

        God-mode: evaluates each debuff by:
        - Target's exact save bonus vs our DC (failure probability)
        - Magic Resistance consideration
        - Condition value (Paralyzed > Stunned > Restrained > etc.)
        - Target threat level (disable high-DPR enemies)
        - Legendary Resistance (don't waste debuffs on LR targets)
        - Condition immunity check
        - Whether concentration is worth switching
        """
        debuff_spells = [s for s in entity.stats.spells_known
                         if s.applies_condition and s.targets == "single"]
        if not debuff_spells:
            return None

        dc = entity.stats.spell_save_dc or (8 + entity.stats.proficiency_bonus
             + entity.get_modifier(entity.stats.spellcasting_ability))

        best_spell = None
        best_target = None
        best_ev = 0.0

        # Condition value scores (how impactful is the condition?)
        condition_values = {
            "Paralyzed": 50,   # Auto-crit melee, auto-fail STR/DEX saves
            "Stunned": 40,     # Incapacitated + auto-fail STR/DEX saves
            "Petrified": 45,   # Basically dead
            "Unconscious": 45, # Auto-crit + incapacitated
            "Restrained": 25,  # Advantage + disadvantage
            "Blinded": 25,     # Advantage on attacks vs them
            "Frightened": 20,  # Disadvantage + can't approach
            "Charmed": 15,     # Can't attack charmer
            "Poisoned": 15,    # Disadvantage on attacks + checks
            "Prone": 10,       # Advantage melee, but can stand
            "Grappled": 10,    # Speed 0
            "Deafened": 5,
        }

        for spell in debuff_spells:
            if not entity.has_spell_slot(spell.level):
                continue
            # Don't switch concentration unless new spell is significantly better
            if spell.concentration and entity.concentrating_on:
                current_value = 0
                if entity.concentrating_on.applies_condition:
                    current_value = condition_values.get(entity.concentrating_on.applies_condition, 10)
                new_value = condition_values.get(spell.applies_condition, 10)
                if new_value < current_value * 1.5:
                    continue  # Current concentration is good enough

            candidates = [e for e in enemies if e.hp > 0
                          and not e.has_condition(spell.applies_condition)]

            # Filter immune targets
            if spell.applies_condition:
                candidates = [e for e in candidates
                              if spell.applies_condition not in e.stats.condition_immunities]
            if not candidates:
                continue

            spell_dc = spell.save_dc_fixed if spell.save_dc_fixed else dc

            for target in candidates:
                dist_ft = battle.get_distance(entity, target) * 5
                if dist_ft > spell.range:
                    continue
                # LOS check for targeted spells
                if not self._can_see_target(entity, target, battle):
                    continue

                # Calculate failure probability
                save_bonus = target.get_save_bonus(spell.save_ability)
                has_magic_res = target.has_feature("magic_resistance")
                fail_chance = 1.0 - ((21 + save_bonus - dc) / 20.0)
                if has_magic_res:
                    success = 1.0 - fail_chance
                    fail_chance = 1.0 - (1.0 - (1.0 - success) ** 2)
                fail_chance = max(0.05, min(0.95, fail_chance))

                # Skip if chance is too low
                if fail_chance < 0.2:
                    continue

                # Legendary Resistance: target will auto-succeed
                if target.legendary_resistances_left > 0:
                    # Only worth it to burn LR if we have more debuffs to follow up
                    remaining_debuff_slots = sum(1 for s in debuff_spells
                                                  if entity.has_spell_slot(s.level))
                    if remaining_debuff_slots <= target.legendary_resistances_left:
                        continue  # Not enough slots to burn through all LR
                    # Reduce fail_chance to represent LR burn value
                    fail_chance *= 0.3  # LR burn has some value but reduced

                # Calculate EV
                cond_value = condition_values.get(spell.applies_condition, 10)
                target_threat = self._estimate_entity_dpr(target)

                # Higher value for disabling high-threat targets
                ev = cond_value * fail_chance * (1.0 + target_threat * 0.02)

                # Bonus: Hold Person on melee-only enemies = devastating
                if spell.applies_condition in ("Paralyzed", "Stunned"):
                    if self._get_combat_preference(target) == "melee":
                        ev *= 1.3
                    # Extra bonus if allies are adjacent (auto-crit)
                    adj_allies = [a for a in allies if battle.is_adjacent(a, target) and a.hp > 0]
                    ev += len(adj_allies) * 10 * fail_chance

                # Also consider the damage component of damage+debuff spells
                if spell.damage_dice:
                    dmg_ev = self._estimate_damage(spell.damage_dice, spell.damage_type, target)
                    if spell.save_ability:
                        if spell.half_on_save:
                            dmg_ev = dmg_ev * fail_chance + (dmg_ev / 2.0) * (1.0 - fail_chance)
                        else:
                            dmg_ev = dmg_ev * fail_chance
                    ev += dmg_ev

                if ev > best_ev:
                    best_ev = ev
                    best_spell = spell
                    best_target = target

        if best_spell and best_target:
            entity.use_spell_slot(best_spell.level)
            spell_dc = best_spell.save_dc_fixed if best_spell.save_dc_fixed else dc
            if best_spell.concentration:
                entity.start_concentration(best_spell)

            desc = f"{entity.name} casts {best_spell.name} on {best_target.name} (DC {spell_dc} {best_spell.save_ability})"
            return ActionStep(
                step_type="spell", description=desc,
                attacker=entity, target=best_target, spell=best_spell,
                slot_used=best_spell.level, action_name=best_spell.name,
                save_dc=spell_dc, save_ability=best_spell.save_ability,
                applies_condition=best_spell.applies_condition,
                damage=roll_dice(_get_spell_damage_dice(best_spell, entity)) if best_spell.damage_dice else 0,
                damage_type=best_spell.damage_type if best_spell.damage_dice else "",
            )
        return None

    def _try_terrain_spell(self, entity, enemies, allies, battle):
        """Try casting a non-damage terrain spell (Darkness, Fog Cloud, Silence).

        Returns (score, [ActionStep]) or None.
        Damaging terrain spells (Wall of Fire, Spike Growth) are handled by _try_aoe_spell.
        """
        terrain_spells = [s for s in entity.stats.spells_known
                          if s.creates_terrain and not s.damage_dice and not s.applies_condition
                          and s.level > 0 and entity.has_spell_slot(s.level)]

        if not terrain_spells:
            return None

        # Don't replace good concentration
        if entity.concentrating_on:
            return None

        best_score = 0
        best_step = None

        for spell in terrain_spells:
            # Find best cluster of enemies to cover
            result = self._best_aoe_cluster(
                entity, enemies, allies, battle,
                spell.aoe_radius, shape=spell.aoe_shape,
                avoid_allies=True, damage_type="")
            if not result:
                continue

            clusters, (cx, cy) = result
            enemies_hit = len([t for t in clusters if t in enemies])
            allies_hit = len([t for t in clusters if t in allies])

            if enemies_hit == 0:
                continue

            # Score based on tactical value
            score = 0
            if spell.creates_terrain == "darkness":
                # Darkness is useful for ranged enemies (blocks their LOS)
                # Check if entity has Devil's Sight or Blindsight
                has_darkvision_immunity = (entity.has_feature("devils_sight") or
                                           entity.has_feature("blindsight") or
                                           entity.has_feature("truesight"))
                if has_darkvision_immunity:
                    score = enemies_hit * 25  # Very valuable with Devil's Sight
                else:
                    score = enemies_hit * 8   # Risky without immunity

            elif spell.creates_terrain == "fog_cloud":
                # Fog blocks LOS - useful to break ranged enemy advantage
                pref = self._get_combat_preference(entity)
                if pref == "melee":
                    score = enemies_hit * 12  # Melee benefits from fog vs ranged enemies
                else:
                    score = enemies_hit * 5   # Ranged doesn't want fog as much

            elif spell.creates_terrain == "silence":
                # Silence is very valuable vs spellcasters
                for t in clusters:
                    if t in enemies and t.stats.spells_known:
                        score += 30  # Huge value vs casters
                    elif t in enemies:
                        score += 5

            else:
                score = enemies_hit * 10  # Generic terrain spell

            # Penalty for hitting allies
            score -= allies_hit * 20

            # Scale by spell level cost
            score -= spell.level * 3

            if score > best_score:
                best_score = score
                slot = spell.level
                dc = entity.stats.spell_save_dc or (8 + entity.stats.proficiency_bonus +
                      entity.get_modifier(entity.stats.spellcasting_ability))
                entity.use_spell_slot(slot)
                entity.start_concentration(spell)
                best_step = ActionStep(
                    step_type="spell",
                    description=f"{entity.name} casts {spell.name} (slot {slot}).",
                    attacker=entity, targets=clusters, spell=spell, slot_used=slot,
                    damage=0, damage_type="",
                    action_name=spell.name, aoe_center=(cx, cy),
                    save_dc=dc,
                )

        if best_step:
            return (best_score, [best_step])
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

                # LOS + range check
                if not self._can_ranged_attack(entity, target, battle, range_ft=spell.range):
                    continue

                # Calculate damage against THIS target (vulnerability/resistance)
                effective_dice = _get_spell_damage_dice(spell, entity)
                base_dmg = self._estimate_damage(effective_dice, spell.damage_type, target)
                if base_dmg <= 0: continue
                base_dmg += extra

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
                    dis = entity.has_attack_disadvantage(target, is_ranged=True, is_threatened=is_threatened, battle=battle)
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

            # Scale cantrip damage dice by caster level
            effective_dice = _get_spell_damage_dice(spell, entity)

            if spell.save_ability:
                dmg = roll_dice(effective_dice) + int(extra)
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
                dis = entity.has_attack_disadvantage(target, is_ranged=True, is_threatened=is_threatened, battle=battle)
                total, nat, is_crit, is_fumble, roll_str = roll_attack(atk_bonus, adv, dis)
                is_hit = total >= target.stats.armor_class and not is_fumble
                dmg = roll_dice_critical(effective_dice) if is_crit else roll_dice(effective_dice)
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
            
            # Filter targets by range and LOS for ranged attacks
            reachable_enemies = []
            for e in alive_enemies:
                if battle.get_distance(entity, e) * 5 > sub.range:
                    continue
                # Ranged attacks need LOS, melee don't
                if sub.range > 10 and not self._can_see_target(entity, e, battle):
                    continue
                reachable_enemies.append(e)

            t = self._pick_target(entity, reachable_enemies, battle)
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

        # --- TCoE: Ranger Dreadful Strikes (Fey Wanderer) ---
        if entity.has_feature("dreadful_strikes") and step.is_hit and first_attack:
            ds_feat = entity.get_feature("dreadful_strikes")
            ds_dice = ds_feat.mechanic_value if ds_feat else "1d4"
            ds_dmg = roll_dice_critical(ds_dice) if step.is_crit else roll_dice(ds_dice)
            step.bonus_damage += ds_dmg
            step.damage += ds_dmg
            step.damage_type = "psychic"
            bonus_parts.append(f"Dreadful Strikes +{ds_dmg}")

        # --- TCoE: Ranger Gathered Swarm (Swarmkeeper) ---
        if entity.has_feature("gathered_swarm") and step.is_hit and first_attack:
            gs_feat = entity.get_feature("gathered_swarm")
            gs_dice = gs_feat.mechanic_value if gs_feat else "1d6"
            gs_dmg = roll_dice_critical(gs_dice) if step.is_crit else roll_dice(gs_dice)
            step.bonus_damage += gs_dmg
            step.damage += gs_dmg
            bonus_parts.append(f"Gathered Swarm +{gs_dmg}")

        # --- TCoE: Rogue Wails from the Grave (Phantom) ---
        if (entity.has_feature("wails_from_grave") and step.is_hit and first_attack
                and entity.has_feature("sneak_attack") and entity.sneak_attack_used):
            # Wails triggers after Sneak Attack - deal half SA dice as necrotic to 2nd target
            sa_dice = entity.get_sneak_attack_dice()
            if sa_dice and entity.can_use_feature("Wails from the Grave"):
                # Parse SA dice count and halve it
                try:
                    num = int(sa_dice.split("d")[0]) // 2
                    if num >= 1:
                        wails_dice = f"{num}d6"
                        wails_dmg = roll_dice(wails_dice)
                        step.bonus_damage += wails_dmg
                        step.damage += wails_dmg
                        bonus_parts.append(f"Wails from Grave {wails_dice}={wails_dmg}")
                        entity.use_feature("Wails from the Grave")
                except (ValueError, IndexError):
                    pass

        # --- TCoE: Fighter Giant's Might (Rune Knight) ---
        if entity.has_feature("giants_might") and step.is_hit and first_attack:
            gm_feat = entity.get_feature("giants_might")
            gm_dice = gm_feat.mechanic_value if gm_feat else "1d6"
            gm_dmg = roll_dice_critical(gm_dice) if step.is_crit else roll_dice(gm_dice)
            step.bonus_damage += gm_dmg
            step.damage += gm_dmg
            bonus_parts.append(f"Giant's Might +{gm_dmg}")

        # --- TCoE: Fighter Psionic Strike (Psi Warrior) ---
        if entity.has_feature("psionic_power") and step.is_hit and first_attack:
            pp_feat = entity.get_feature("psionic_power")
            pp_dice = pp_feat.mechanic_value if pp_feat else "1d6"
            if entity.can_use_feature("Psionic Power"):
                pp_dmg = roll_dice_critical(pp_dice) if step.is_crit else roll_dice(pp_dice)
                step.bonus_damage += pp_dmg
                step.damage += pp_dmg
                bonus_parts.append(f"Psionic Strike +{pp_dmg}")
                entity.use_feature("Psionic Power")

        # --- TCoE: Warlock Genie's Wrath ---
        if entity.has_feature("genies_wrath") and step.is_hit and first_attack:
            gw_dmg = entity.stats.proficiency_bonus
            step.bonus_damage += gw_dmg
            step.damage += gw_dmg
            bonus_parts.append(f"Genie's Wrath +{gw_dmg}")

        # --- TCoE: Monk Hand of Harm (Way of Mercy) ---
        if (entity.has_feature("hand_of_harm") and step.is_hit and first_attack
                and entity.ki_points_left > 0 and step.action and step.action.range <= 5):
            hoh_dice = "1d6"
            wis_mod = entity.get_modifier("wisdom")
            hoh_dmg = roll_dice(hoh_dice) + max(0, wis_mod)
            step.bonus_damage += hoh_dmg
            step.damage += hoh_dmg
            entity.ki_points_left -= 1
            bonus_parts.append(f"Hand of Harm +{hoh_dmg}")

        # --- TCoE: Cleric Voice of Authority (Order Domain) ---
        # Note: This triggers on spell cast, not on attack - handled in spell resolution

        # --- TCoE: Bard Unsettling Words (College of Eloquence) ---
        # Note: This is a bonus action debuff, handled in pre-combat bonus phase

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

        adv = entity.has_attack_advantage(target, is_ranged, dist, battle=battle)
        # Long range: normal_range = action.range, long_range = action.long_range
        dist_ft = dist * 5  # grid units to feet
        normal_range = action.range if is_ranged else 0
        long_range = getattr(action, "long_range", 0) or 0
        dis = entity.has_attack_disadvantage(target, is_ranged, is_threatened=is_threatened,
                                             distance_ft=dist_ft, normal_range=normal_range,
                                             long_range=long_range, battle=battle)
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

        # Equipment: Add extra damage from magic weapons (Flame Tongue, Frost Brand, etc.)
        equipped_weapon = None
        for item in entity.items:
            if item.equipped and item.item_type == "weapon" and item.name == action.name:
                equipped_weapon = item
                break
        # Also check by matching weapon properties to action
        if not equipped_weapon:
            for item in entity.items:
                if item.equipped and item.item_type == "weapon" and item.weapon_damage_dice:
                    if item.weapon_damage_dice in action.damage_dice:
                        equipped_weapon = item
                        break

        if equipped_weapon and equipped_weapon.extra_damage_dice and is_hit:
            extra = roll_dice(equipped_weapon.extra_damage_dice)
            if is_crit:
                extra += roll_dice(equipped_weapon.extra_damage_dice)
            dmg += extra
            desc += f" +{extra} {equipped_weapon.extra_damage_type}"

        # Determine if magical
        is_magical = False
        if entity.has_feature("magic_weapons") or entity.has_feature("ki_empowered_strikes"):
            is_magical = True
        if entity.is_summon:
            is_magical = True
        # Check if equipped weapon is magical
        if equipped_weapon and equipped_weapon.is_magical:
            is_magical = True

        return ActionStep(
            step_type="attack", description=desc,
            attacker=entity, target=target, action_name=action.name,
            action=action, attack_roll=total, attack_roll_str=roll_str, nat_roll=nat,
            is_crit=is_crit, is_hit=is_hit,
            damage=dmg, damage_type=action.damage_type, applies_condition=action.applies_condition,
            condition_dc=action.condition_dc, save_ability=action.condition_save,
            is_magical=is_magical
        )

    # ------------------------------------------------------------------ #
    # Bonus Action                                                         #
    # ------------------------------------------------------------------ #

    def _decide_bonus_action(self, entity, enemies, allies, battle, plan=None) -> List[ActionStep]:
        """Optimal post-attack bonus action selection.

        Priority order (highest to lowest):
        1. EMERGENCY: Healing Word for dying allies
        2. Command Spiritual Weapon (free DPR each turn)
        3. Flurry of Blows (Monk - 2 extra attacks + potential Stunning Strike)
        4. Bonus action attacks (Offhand, Polearm Master, etc.)
        5. Second Wind (Fighter self-heal)
        6. Monster abilities (Aggressive, Nimble Escape)
        7. Hunter's Mark / Hex (if not cast pre-combat)
        8. Spiritual Weapon summon
        9. Bardic Inspiration
        10. Other bonus action spells
        """
        if entity.bonus_action_used:
            return []

        # Check if a leveled spell was cast with Action (prevents Bonus Action spells PHB p.202)
        leveled_spell_cast = False
        if plan:
            for s in plan.steps:
                if s.step_type == "spell" and s.slot_used > 0:
                    leveled_spell_cast = True
                    break

        # --- 1. EMERGENCY: Healing Word for dying allies (highest priority bonus action) ---
        if not leveled_spell_cast:
            revive_step = self._try_revive_ally_spell(entity, allies, battle, action_type="bonus")
            if revive_step:
                entity.bonus_action_used = True
                return [revive_step]

        # --- 2. Command existing Spiritual Weapon ---
        my_weapons = [e for e in battle.entities
                      if e.is_summon and e.summon_owner == entity and "Spiritual Weapon" in e.name]
        for weapon in my_weapons:
            target = self._pick_target(weapon, enemies, battle)
            if target:
                steps = []
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

        # --- 3. Monk: Flurry of Blows (offensive) or Patient Defense (defensive) ---
        if entity.ki_points_left > 0:
            if entity.has_feature("flurry_of_blows"):
                hp_pct = entity.hp / max(entity.max_hp, 1)
                threats = [e for e in enemies if battle.is_adjacent(entity, e) and e.hp > 0]
                # Patient Defense: Dodge as bonus when low HP and surrounded
                if (entity.has_feature("patient_defense") and hp_pct < DODGE_HP_THRESHOLD
                        and len(threats) >= 2):
                    entity.ki_points_left -= 1
                    entity.is_dodging = True
                    entity.bonus_action_used = True
                    return [ActionStep(
                        step_type="bonus_attack",
                        description=f"{entity.name} uses Patient Defense (Dodge, 1 Ki).",
                        attacker=entity, target=entity, action_name="Patient Defense",
                    )]
                # Step of the Wind: Disengage or Dash as bonus action (1 ki)
                # Use when ranged-threatened or need to close distance
                if entity.has_feature("step_of_the_wind"):
                    # Disengage if we're a ranged monk surrounded
                    if threats and self._get_combat_preference(entity) == "ranged":
                        entity.ki_points_left -= 1
                        entity.is_disengaging = True
                        entity.movement_left += entity.stats.speed  # Dash component
                        entity.bonus_action_used = True
                        return [ActionStep(
                            step_type="bonus_attack",
                            description=f"{entity.name} uses Step of the Wind (Disengage + Dash, 1 Ki).",
                            attacker=entity, target=entity, action_name="Step of the Wind",
                        )]

                # Otherwise Flurry of Blows for offense
                target = self._pick_target(entity, enemies, battle)
                if target and battle.is_adjacent(entity, target):
                    return self._monk_flurry_of_blows(entity, target, allies, battle)

        # --- 3b. Second Wind early if on a defensive turn (Dodge action) ---
        took_dodge = plan and any(s.action_name == "Dodge" for s in plan.steps)
        if took_dodge:
            sw_step = self._try_second_wind(entity)
            if sw_step:
                return [sw_step]

        # --- 3c. Two-Weapon Fighting (PHB p.195) ---
        # If entity attacked with a light melee weapon, can make off-hand bonus attack
        if plan and not entity.bonus_action_used:
            main_attacked = any(
                s.step_type in ("attack", "multiattack") and s.action
                and "light" in getattr(s.action, "properties", [])
                and s.action.range <= 10  # melee weapon
                for s in plan.steps
            )
            if main_attacked:
                # Find an off-hand light weapon (different from main-hand)
                main_names = {s.action.name for s in plan.steps
                              if s.step_type in ("attack", "multiattack") and s.action}
                has_dual_wielder = entity.has_feature("dual_wielder")
                has_twf_style = entity.has_feature("two_weapon_fighting") or entity.has_feature("fighting_style_twf")
                offhand = None
                for a in entity.stats.actions:
                    if a.name in main_names or a.is_multiattack:
                        continue
                    if a.range > 10 or not a.damage_dice:
                        continue  # ranged/no damage
                    if "light" in getattr(a, "properties", []) or has_dual_wielder:
                        offhand = a
                        break
                if offhand:
                    target = self._pick_target(entity, enemies, battle)
                    if target and battle.is_adjacent(entity, target):
                        step = self._execute_attack(entity, offhand, target, battle)
                        step.step_type = "bonus_attack"
                        step.action_name = f"{offhand.name} (off-hand)"
                        # PHB: off-hand doesn't add ability mod to damage
                        # unless Two-Weapon Fighting style
                        if not has_twf_style:
                            ability_mod = max(entity.get_modifier("strength"), entity.get_modifier("dexterity"))
                            step.damage = max(0, step.damage - ability_mod)
                        self._apply_class_attack_bonuses(entity, step, target, allies, battle, first_attack=False)
                        entity.bonus_action_used = True
                        return [step]

        # --- 4. Bonus action attacks (Offhand, PAM, etc.) ---
        for ba in entity.stats.bonus_actions:
            if not ba.damage_dice:
                continue
            target = self._pick_target(entity, enemies, battle)
            if not target:
                continue
            dist = battle.get_distance(entity, target)
            if ba.range / 5.0 >= dist:
                # Ranged bonus attacks need LOS
                if ba.range > 10 and not self._can_see_target(entity, target, battle):
                    continue
                step = self._execute_attack(entity, ba, target, battle)
                step.step_type = "bonus_attack"
                # Apply class bonuses (Rage, HM, etc.)
                self._apply_class_attack_bonuses(entity, step, target, allies, battle, first_attack=False)
                entity.bonus_action_used = True
                return [step]

        # --- 5. Second Wind (Fighter) ---
        sw_step = self._try_second_wind(entity)
        if sw_step:
            return [sw_step]

        # --- 6. Monster: Aggressive ---
        if entity.has_feature("aggressive"):
            target = self._pick_target(entity, enemies, battle)
            if target:
                entity.movement_left += entity.stats.speed
                move_step = self._move_toward(entity, target, allies, battle)
                if move_step:
                    entity.bonus_action_used = True
                    move_step.description = f"{entity.name} uses Aggressive to move closer."
                    return [move_step]

        # --- 6b. Monster: Nimble Escape ---
        if entity.has_feature("nimble_escape"):
            threats = [e for e in enemies if battle.is_adjacent(entity, e)]
            if threats:
                entity.is_disengaging = True
                move_step = self._move_away(entity, threats[0], battle)
                if move_step:
                    entity.bonus_action_used = True
                    move_step.description = f"{entity.name} uses Nimble Escape to Disengage & Retreat."
                    return [move_step]
                entity.is_disengaging = False

        # --- 7. Hunter's Mark / Hex (if not already cast pre-combat) ---
        if not leveled_spell_cast:
            hm_step = self._try_hunters_mark(entity, enemies, battle)
            if hm_step:
                return [hm_step]
            hex_step = self._try_hex(entity, enemies, battle)
            if hex_step:
                return [hex_step]

        # --- 8. Spiritual Weapon summon ---
        if not leveled_spell_cast:
            sw_step = self._try_summon_spiritual_weapon(entity, enemies, battle)
            if sw_step:
                return [sw_step]

        # --- 9. Bardic Inspiration (Bard) ---
        if entity.has_feature("bardic_inspiration") and entity.bardic_inspiration_left > 0:
            # Inspire the ally most likely to benefit (lowest HP% = most likely targeted)
            candidates = [a for a in allies if a != entity and a.hp > 0]
            if candidates:
                # Prioritize: melee fighters in danger, then lowest HP%
                target = min(candidates, key=lambda a: (
                    0 if (a.hp / a.max_hp < 0.5) else 1,
                    a.hp / a.max_hp
                ))
                entity.bardic_inspiration_left -= 1
                entity.bonus_action_used = True
                return [ActionStep(
                    step_type="bonus_attack",
                    description=f"{entity.name} gives Bardic Inspiration to {target.name}.",
                    attacker=entity, target=target, action_name="Bardic Inspiration"
                )]

        # --- 10. Rogue Cunning Action (post-attack) ---
        if entity.has_feature("cunning_action"):
            threats = [e for e in enemies if battle.is_adjacent(entity, e) and e.hp > 0]
            if threats and self._get_combat_preference(entity) == "ranged":
                entity.movement_left += entity.stats.speed
                move_step = self._move_away(entity, threats[0], battle)
                if move_step:
                    entity.bonus_action_used = True
                    move_step.description = f"{entity.name} uses Cunning Action: Disengage & Retreat."
                    return [move_step]

        # --- 11. Bonus Action Spells (Heals, Buffs) ---
        if not leveled_spell_cast:
            for spell in entity.stats.spells_known:
                if spell.action_type != "bonus":
                    continue
                if spell.level > 0 and not entity.has_spell_slot(spell.level):
                    continue
                # Self-heal if hurt
                if spell.heals and entity.hp < entity.max_hp * 0.6:
                    if spell.level == 0 or entity.use_spell_slot(spell.level):
                        healed = roll_dice(spell.heals)
                        entity.bonus_action_used = True
                        return [ActionStep(
                            step_type="bonus_attack",
                            description=f"{entity.name} uses bonus {spell.name}, heals {healed} HP.",
                            attacker=entity, target=entity, spell=spell,
                            slot_used=spell.level, damage=healed, action_name=spell.name,
                        )]
                # Concentration buffs
                if spell.concentration and not entity.concentrating_on:
                    target = self._pick_target(entity, enemies, battle)
                    if target and (spell.level == 0 or entity.use_spell_slot(spell.level)):
                        entity.start_concentration(spell)
                        entity.bonus_action_used = True
                        return [ActionStep(
                            step_type="bonus_attack",
                            description=f"{entity.name} casts bonus {spell.name} (Concentration).",
                            attacker=entity, target=entity, spell=spell,
                            slot_used=spell.level, action_name=spell.name,
                        )]

        # --- 12. Healing Potion as Bonus Action (variant rule, common in play) ---
        potion_step = self._try_use_healing_potion_bonus(entity)
        if potion_step:
            return [potion_step]

        return []

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
                applies_condition="Turned"
            )
        return None

    def _try_hunters_mark(self, entity, enemies, battle):
        """Cast Hunter's Mark on best target."""
        if entity.concentrating_on:
            return None  # Already concentrating
        hm = next((s for s in entity.stats.spells_known if s.name == "Hunter's Mark"), None)
        if not hm or not entity.has_spell_slot(1):
            return None

        target = self._pick_target(entity, enemies, battle)
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

        target = self._pick_target(entity, enemies, battle)
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

        target = self._pick_target(entity, enemies, battle)
        if not target:
            return None

        # Find spawn position adjacent to target
        spawn_x, spawn_y = target.grid_x, target.grid_y
        found_spawn = False
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = target.grid_x + dx, target.grid_y + dy
                if battle.is_passable(nx, ny, exclude=entity):
                    spawn_x, spawn_y = nx, ny
                    found_spawn = True
                    break
            if found_spawn:
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
            adv = entity.has_attack_advantage(target, is_ranged=False, battle=battle)
            dis = entity.has_attack_disadvantage(target, is_ranged=False, battle=battle)
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
                stun_dc = 8 + entity.stats.proficiency_bonus + entity.get_modifier("wisdom")
                desc_parts[-1] += f" [Stunning Strike DC {stun_dc} CON]"

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
        """Strategic legendary action selection.

        MM p.11 Legendary Actions:
        - Only at END of another creature's turn
        - One at a time
        - Actions regain at START of creature's own turn
        - Can't use while incapacitated

        Strategy:
        - Score each legendary action by EV
        - Prefer cheap actions early, save expensive ones for key moments
        - Use AoE legendary actions (Wing Attack, Tail Sweep) when surrounded
        - Target concentrators and low-HP enemies
        - Don't use all actions on first enemy turn - spread them out
        """
        from engine.rules import can_use_legendary_action
        allowed, reason = can_use_legendary_action(entity)
        if not allowed:
            return None

        enemies = battle.get_enemies_of(entity)
        if not enemies:
            return None

        leg_feats = [f for f in entity.stats.features if f.feature_type == "legendary"]
        if not leg_feats:
            return None

        best_step = None
        best_score = 0.0

        for feat in leg_feats:
            if feat.legendary_cost > entity.legendary_actions_left:
                continue

            leg_action = next((a for a in entity.stats.actions if a.name == feat.name
                               and a.action_type == "legendary"), None)
            if not leg_action:
                continue

            # --- AoE legendary actions (Wing Attack, Frightful Presence) ---
            if leg_action.aoe_radius > 0:
                allies = battle.get_allies_of(entity)
                result = self._best_aoe_cluster(entity, enemies, allies, battle,
                                                   leg_action.aoe_radius,
                                                   shape=leg_action.aoe_shape or "sphere",
                                                   damage_type=leg_action.damage_type)
                if result:
                    clusters, (cx, cy) = result
                    if clusters:
                        # Score based on number of targets and damage
                        aoe_dmg = average_damage(leg_action.damage_dice) if leg_action.damage_dice else 0
                        score = aoe_dmg * len(clusters) * 0.6

                        # Bonus for condition application
                        if leg_action.applies_condition:
                            score += len(clusters) * 8

                        # Cost efficiency
                        score /= max(feat.legendary_cost, 1)

                        if score > best_score:
                            best_score = score
                            raw_dmg = roll_dice(leg_action.damage_dice) if leg_action.damage_dice else 0
                            best_step = ActionStep(
                                step_type="legendary",
                                description=f"[LEGENDARY] {entity.name} uses {feat.name}!",
                                attacker=entity, targets=clusters, action=leg_action,
                                damage=raw_dmg, damage_type=leg_action.damage_type,
                                action_name=feat.name, aoe_center=(cx, cy),
                                save_dc=leg_action.condition_dc, save_ability=leg_action.condition_save
                            )
                continue

            # --- Single-target legendary actions ---
            # Score each potential target
            for target in enemies:
                if target.hp <= 0:
                    continue
                dist = battle.get_distance(entity, target)
                if leg_action.range / 5.0 < dist:
                    continue

                score = 0.0
                if leg_action.damage_dice:
                    dmg = self._estimate_damage(leg_action.damage_dice, leg_action.damage_type, target)
                    hit_chance = (21 + leg_action.attack_bonus - target.stats.armor_class) / 20.0
                    hit_chance = max(0.05, min(0.95, hit_chance))
                    score = dmg * hit_chance

                # Bonus for finishing off wounded enemies
                avg_dmg = average_damage(leg_action.damage_dice) if leg_action.damage_dice else 0
                if avg_dmg >= target.hp:
                    score *= 1.5

                # Bonus for hitting concentrators
                if target.concentrating_on:
                    score += 10

                # Bonus for condition application
                if leg_action.applies_condition:
                    if leg_action.applies_condition not in target.stats.condition_immunities:
                        score += 10

                # Cost efficiency
                score /= max(feat.legendary_cost, 1)

                if score > best_score:
                    best_score = score
                    step = self._execute_attack(entity, leg_action, target, battle)
                    step.step_type = "legendary"
                    step.description = f"[LEGENDARY] " + step.description
                    best_step = step

        if best_step:
            # Find the feat used and deduct cost
            for feat in leg_feats:
                if feat.name == best_step.action_name or (best_step.action and feat.name == best_step.action.name):
                    entity.legendary_actions_left -= feat.legendary_cost
                    break
                # Also check description match for AoE
                if feat.name in best_step.description:
                    entity.legendary_actions_left -= feat.legendary_cost
                    break
            else:
                # Fallback: deduct cheapest cost
                entity.legendary_actions_left -= min(f.legendary_cost for f in leg_feats)
            return best_step
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
    # Reaction decisions (NPC auto-use)                                    #
    # ------------------------------------------------------------------ #

    # Spells considered "high impact" — always worth countering if able.
    _COUNTER_PRIORITY_SPELLS = {
        "Fireball", "Cone of Cold", "Lightning Bolt", "Ice Storm", "Cloudkill",
        "Meteor Swarm", "Fire Storm", "Circle of Death", "Sunburst", "Tsunami",
        "Hypnotic Pattern", "Hold Person", "Hold Monster", "Banishment",
        "Polymorph", "Confusion", "Fear", "Dominate Person", "Dominate Monster",
        "Mass Suggestion", "Power Word Stun", "Power Word Kill", "Feeblemind",
        "Wall of Force", "Forcecage", "Telekinesis", "Evard's Black Tentacles",
        "Otiluke's Resilient Sphere", "Bigby's Hand", "Spirit Guardians",
        "Revivify", "Raise Dead", "Healing Word", "Mass Healing Word",
        "Heal", "Mass Heal", "Cure Wounds", "Prayer of Healing",
    }

    def should_counterspell(self, reactor, caster, spell, spell_level: int, battle) -> bool:
        """Decide whether ``reactor`` should spend their reaction on Counterspell.

        spell may be ``None`` if only the level is known (DM path). reactor is
        assumed to have Counterspell and a slot ≥3 already.
        """
        if reactor.reaction_used or reactor.is_incapacitated():
            return False
        # Never counter an ally (e.g. Bless on the caster's own team)
        if reactor.is_player == caster.is_player:
            return False

        # Level-based auto-success check.
        own_slot = None
        for lvl in (spell_level, spell_level + 1, spell_level + 2):
            if lvl >= 3 and reactor.has_spell_slot(lvl):
                own_slot = lvl
                break

        spell_name = spell.name if spell else ""
        is_priority = spell_name in self._COUNTER_PRIORITY_SPELLS
        is_aoe = bool(spell and (spell.aoe_radius or spell.aoe_shape))
        is_control = bool(spell and spell.applies_condition)
        is_heal = spell_name in ("Healing Word", "Mass Healing Word", "Cure Wounds",
                                 "Prayer of Healing", "Heal", "Mass Heal",
                                 "Revivify", "Raise Dead")

        # Counter slot ≤ cast slot: auto-success, cheap win if worth it.
        if own_slot is not None and own_slot <= spell_level:
            # Spells level ≥3 are almost always worth countering; for lvl 1-2
            # spells, only counter priority/AoE/control.
            if spell_level >= 3:
                return True
            if is_priority or is_aoe or is_control or is_heal:
                return True
            # Low-value lvl 1-2 spell: don't waste a 3rd slot.
            return False

        # Counter slot < cast slot: DC 10 + spell_level ability check.
        # Only attempt if the spell is clearly high-impact.
        if reactor.has_spell_slot(3):
            if is_priority or (is_aoe and spell_level >= 3) or (is_control and spell_level >= 3):
                # Expected DC check success probability rough gate.
                ab_mod = reactor.get_modifier(reactor.stats.spellcasting_ability) if reactor.stats.spellcasting_ability else 0
                prof = reactor.stats.proficiency_bonus
                needed = (10 + spell_level) - (ab_mod + prof)
                if needed <= 15:  # ≥30% success
                    return True
        return False

    def should_silvery_barbs(self, reactor, attacker, target, step, battle) -> bool:
        """Decide whether ``reactor`` should use Silvery Barbs on an incoming hit.

        Reactor must have the spell known, a slot ≥1, see the attacker, and be
        within 60 ft of the attacker. Caller is expected to have done the
        possess/slot/reaction availability checks already, but we re-check to
        be safe.
        """
        if reactor.reaction_used or reactor.is_incapacitated():
            return False
        if reactor.is_player == attacker.is_player:
            return False  # Don't counter allies
        sb = next((s for s in reactor.stats.spells_known if s.name == "Silvery Barbs"), None)
        if not sb or not reactor.has_spell_slot(sb.level):
            return False
        if battle.get_distance(reactor, attacker) * 5 > 60:
            return False
        if not battle.has_line_of_sight(reactor, attacker):
            return False
        # Only spend a slot on crits or tight hits that might miss on reroll.
        if step.is_crit:
            return True
        # For non-crit hits, only react if attack_roll is within 3 of AC
        # (reroll has a real chance of turning the hit into a miss).
        if step.attack_roll > 0 and target is not None:
            if step.attack_roll - target.armor_class <= 3:
                return True
        return False

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _pick_target(self, entity, enemies, battle=None) -> Optional["Entity"]:
        """God-mode target selection: score all enemies considering everything.
        Prioritizes DM-forced target, then team focus, then score-based selection."""
        alive = [e for e in enemies if e.hp > 0]
        if not alive:
            return None
        # DM override: forced target takes absolute priority
        if entity.dm_forced_target and entity.dm_forced_target.hp > 0:
            forced = entity.dm_forced_target
            entity.dm_forced_target = None  # Clear after use (one turn only)
            return forced
        # Use team focus fire: coordinate with allies to kill one target at a time
        focus = self._get_team_focus_target(entity, alive)
        if focus:
            return focus
        return max(alive, key=lambda e: self._score_target(entity, e, battle))

    def _score_target(self, entity, target, battle=None):
        """Comprehensive target scoring - god mode sees everything.

        Factors:
        1. Kill potential (can we finish them this turn?)
        2. Focus fire (already wounded = higher priority)
        3. Threat level (DPR, spells, concentration effects)
        4. Concentration disruption value
        5. Healer/support priority
        6. Vulnerability to our damage types
        7. Save weakness for our spells
        8. Reachability (can we actually hit them?)
        9. AC difficulty
        10. Mark priority (Hunter's Mark, Hex)
        11. Line of sight (can we see them?)
        12. Elevation advantage/disadvantage
        """
        s = 0.0
        hp_pct = target.hp / max(target.max_hp, 1)
        dist = math.hypot(entity.grid_x - target.grid_x, entity.grid_y - target.grid_y)

        # --- 1. KILL POTENTIAL: Massive bonus if we can finish them ---
        our_est_dmg = self._estimate_entity_dpr(entity)
        if target.hp <= our_est_dmg * 1.2:
            s += KILL_POTENTIAL_BONUS

        # --- 2. FOCUS FIRE: Wounded targets get escalating bonus ---
        # The more wounded, the higher priority (finish what allies started)
        if hp_pct < 1.0:
            s += (1.0 - hp_pct) * FOCUS_FIRE_WEIGHT

        # --- 3. THREAT LEVEL: High DPR enemies are priority ---
        threat_dpr = self._estimate_entity_dpr(target)
        s += threat_dpr * THREAT_DPR_WEIGHT

        # Spellcasters with remaining slots are high threat
        if target.has_spell_slot(1):
            remaining_slots = sum(target.spell_slots.values())
            s += remaining_slots * SPELL_SLOT_THREAT

        # --- 4. CONCENTRATION DISRUPTION: Break their buffs/debuffs ---
        if target.concentrating_on:
            conc_spell = target.concentrating_on
            conc_value = conc_spell.level * CONC_LEVEL_VALUE
            # AoE concentration spells (Spirit Guardians, Hypnotic Pattern) = very high value
            if conc_spell.aoe_radius > 0:
                conc_value += CONC_AOE_BONUS
            # Debuff concentration (Hold Person, Banishment) = high value
            if conc_spell.applies_condition:
                conc_value += CONC_CONDITION_BONUS
            # Summon concentration (Animate Dead, Conjure Animals)
            if conc_spell.summon_name:
                conc_value += CONC_SUMMON_BONUS
            s += conc_value

        # --- 5. HEALER/SUPPORT PRIORITY: Take out healers early ---
        has_healing = any(sp.heals for sp in target.stats.spells_known)
        if has_healing and target.has_spell_slot(1):
            s += HEALER_PRIORITY_BONUS
        # Bards with inspiration
        if target.bardic_inspiration_left > 0:
            s += 8

        # --- 6. VULNERABILITY: Bonus for targets weak to our damage ---
        our_damage_types = set()
        for a in entity.stats.actions:
            if a.damage_type:
                our_damage_types.add(a.damage_type.lower())
        for sp in entity.stats.spells_known + entity.stats.cantrips:
            if sp.damage_type:
                our_damage_types.add(sp.damage_type.lower())

        for dtype in our_damage_types:
            if dtype in [x.lower() for x in target.stats.damage_vulnerabilities]:
                s += 15
                break

        # Penalty for immune targets (don't waste attacks)
        immune_count = 0
        for dtype in our_damage_types:
            if dtype in [x.lower() for x in target.stats.damage_immunities]:
                immune_count += 1
        if our_damage_types and immune_count == len(our_damage_types):
            s -= 80  # All our damage is immune - avoid this target

        # --- 7. SAVE WEAKNESS: For spellcasters, prefer targets with low saves ---
        if entity.stats.spellcasting_ability:
            # Check if target has notably low saves
            for save_name in ["Wisdom", "Dexterity", "Constitution"]:
                save_bonus = target.get_save_bonus(save_name)
                if save_bonus <= 0:
                    s += 5  # Weak save = easier to land spells

        # --- 8. REACHABILITY: Penalty for distant targets ---
        s -= dist * 1.5

        # Far targets get additional penalty if we're melee
        pref = self._get_combat_preference(entity)
        if pref == "melee" and dist > 6:  # > 30ft away
            s -= (dist - 6) * 3  # Extra penalty for melee trying to reach far targets

        # --- 9. AC DIFFICULTY: Low AC = easier to hit ---
        ac_diff = target.stats.armor_class - 14  # 14 = baseline
        s -= ac_diff * 1.5

        # --- 10. MARK PRIORITY: Huge bonus for marked targets ---
        if entity.marked_target == target:
            s += 35

        # --- 11. CONDITION BONUS: Targets already debuffed are easier ---
        if target.has_condition("Prone") and dist <= 1.5:
            s += 10  # Advantage on melee attacks
        if target.has_condition("Grappled") and target.grappled_by == entity:
            s += 20  # We're grappling them - finish them off
        if target.has_condition("Stunned") or target.has_condition("Paralyzed"):
            s += 25  # Auto-advantage + auto-crit in melee
        if target.has_condition("Restrained"):
            s += 8

        # --- 12. LEGENDARY CREATURE PENALTY: Don't waste debuffs on them ---
        if target.legendary_resistances_left > 0 and entity.stats.spellcasting_ability:
            s -= target.legendary_resistances_left * 5

        # --- 13. LINE OF SIGHT: Can't target what we can't see ---
        if battle:
            if not self._can_see_target(entity, target, battle):
                s -= 30  # Heavy penalty (not impossible, might move to see them)

            # --- 14. ELEVATION ADVANTAGE ---
            elev_diff = entity.elevation - target.elevation
            if elev_diff > 0:
                s += min(elev_diff / 5.0, 4) * 2  # Bonus for height advantage
            elif elev_diff < 0:
                pref = self._get_combat_preference(entity)
                if pref == "ranged":
                    s -= 3  # Slight penalty for shooting upward

        return s

    def _get_team_focus_target(self, entity, enemies) -> Optional["Entity"]:
        """Coordinate with allies to focus fire on one target.

        God-mode AI: look at all allies and pick the best shared target.
        Priority: wounded enemies > high-threat enemies > nearest to team.
        """
        if not enemies:
            return None

        # Find wounded enemies (allies already started damaging them)
        wounded = [e for e in enemies if e.hp < e.max_hp and e.hp > 0]

        if wounded:
            # Among wounded, pick the one closest to death
            # But also consider if we can actually reach them
            best = None
            best_score = -999

            for w in wounded:
                score = 0.0
                # How close to death? (more wounded = higher priority)
                hp_pct = w.hp / max(w.max_hp, 1)
                score += (1.0 - hp_pct) * 60

                # Can we reach them?
                dist = math.hypot(entity.grid_x - w.grid_x, entity.grid_y - w.grid_y)
                score -= dist * 2

                # Threat level
                score += self._estimate_entity_dpr(w) * 0.3

                # Kill potential this turn
                our_dmg = self._estimate_entity_dpr(entity)
                if w.hp <= our_dmg * 1.5:
                    score += 30  # We can kill them!

                if score > best_score:
                    best_score = score
                    best = w

            # Only focus fire if the score is meaningfully better than just picking nearest
            if best and best_score > 10:
                return best

        return None

    def _estimate_entity_dpr(self, entity) -> float:
        """Estimate an entity's damage per round (all sources).

        God-mode: sees all actions, spells, features, and calculates expected DPR.
        """
        dpr = 0.0

        # Physical attacks
        multi = next((a for a in entity.stats.actions if a.is_multiattack), None)
        if multi:
            # Multiattack DPR
            sub_names = multi.multiattack_targets or []
            for name in sub_names:
                sub = next((a for a in entity.stats.actions if a.name == name and not a.is_multiattack), None)
                if sub:
                    dmg_str = f"{sub.damage_dice}+{sub.damage_bonus}" if sub.damage_bonus else sub.damage_dice
                    dpr += average_damage(dmg_str) * 0.65  # ~65% hit chance avg
            if not sub_names and multi.multiattack_count > 0:
                non_multi = [a for a in entity.stats.actions if not a.is_multiattack and a.damage_dice]
                if non_multi:
                    best = max(non_multi, key=lambda a: average_damage(a.damage_dice))
                    dmg_str = f"{best.damage_dice}+{best.damage_bonus}" if best.damage_bonus else best.damage_dice
                    dpr += average_damage(dmg_str) * 0.65 * multi.multiattack_count
        else:
            # Best single attack
            attacks = [a for a in entity.stats.actions if not a.is_multiattack and a.damage_dice]
            if attacks:
                best = max(attacks, key=lambda a: average_damage(a.damage_dice))
                dmg_str = f"{best.damage_dice}+{best.damage_bonus}" if best.damage_bonus else best.damage_dice
                dpr += average_damage(dmg_str) * 0.65

        # Spell DPR (best damage spell or cantrip) - scale cantrips by caster level
        all_spells = entity.stats.spells_known + entity.stats.cantrips
        damage_spells = [s for s in all_spells if s.damage_dice]
        if damage_spells:
            best_spell = max(damage_spells, key=lambda s: average_damage(_get_spell_damage_dice(s, entity)))
            spell_dpr = average_damage(_get_spell_damage_dice(best_spell, entity)) * 0.6  # ~60% save/hit
            # Only count spell DPR if it's better than physical (caster probably uses best option)
            dpr = max(dpr, spell_dpr)

        # Class feature bonuses
        if entity.rage_active:
            dpr += entity.get_rage_damage_bonus() * 2  # Assume 2 attacks
        if entity.has_feature("sneak_attack"):
            sa_dice = entity.get_sneak_attack_dice()
            if sa_dice:
                dpr += average_damage(sa_dice) * 0.65
        if entity.has_feature("divine_smite") and entity.has_spell_slot(1):
            dpr += average_damage("2d8") * 0.65  # Estimate smite on one hit

        return dpr

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
        has_los = self._can_see_target(entity, target, battle)

        valid_actions = []
        for a in actions:
            # Check range
            if a.range / 5.0 < dist:
                continue
            # Ranged attacks require line of sight
            if a.range > 10 and not has_los:
                continue
            # Melee attacks don't need LOS (you're adjacent, you can feel them)
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
        """Find melee spot adjacent to target that minimizes AoE vulnerability.

        God-mode: knows exact AoE capabilities of all enemies and their ranges.
        Evaluates each candidate position by:
        1. How many allies would be caught in the same AoE centered on this position
        2. Distance from enemy AoE casters (stay spread from the AoE origin)
        3. Travel cost (prefer closer positions)
        """
        enemies = battle.get_enemies_of(entity)

        # Calculate AoE threat with specific radius info
        aoe_threats = []
        for e in enemies:
            if e.hp <= 0:
                continue
            for a in e.stats.actions:
                if a.aoe_radius > 0 and a.damage_dice:
                    aoe_threats.append((e, a.aoe_radius, average_damage(a.damage_dice)))
            for s in e.stats.spells_known:
                if s.aoe_radius > 0 and s.damage_dice and e.has_spell_slot(max(s.level, 1)):
                    aoe_threats.append((e, s.aoe_radius, average_damage(s.damage_dice)))

        if not aoe_threats:
            return None

        # Max AoE radius we need to worry about
        max_aoe_radius = max(t[1] for t in aoe_threats) / 5.0  # Convert to squares

        # Find all valid melee spots around target
        candidates = []
        t_size = target.size_in_squares

        for x in range(int(target.grid_x) - 1, int(target.grid_x) + t_size + 1):
            for y in range(int(target.grid_y) - 1, int(target.grid_y) + t_size + 1):
                if not battle.is_passable(x, y, exclude=entity):
                    continue
                if x >= target.grid_x and x < target.grid_x + t_size and \
                   y >= target.grid_y and y < target.grid_y + t_size:
                    continue
                candidates.append((x, y))

        if not candidates:
            return None

        best_score = -9999
        best_spot = None

        for (cx, cy) in candidates:
            travel = math.hypot(cx - entity.grid_x, cy - entity.grid_y)
            if travel * 5 > entity.movement_left:
                continue

            score = -travel * 2  # Base: prefer closer spots

            # Clumping penalty: for each ally within AoE radius, penalty scales with damage
            for ally in allies:
                if ally == entity or ally.hp <= 0:
                    continue
                d = math.hypot(cx - ally.grid_x, cy - ally.grid_y)
                if d < max_aoe_radius:
                    # Weight by actual AoE threat damage
                    for _, aoe_radius, aoe_dmg in aoe_threats:
                        if d < aoe_radius / 5.0:
                            score -= aoe_dmg * 0.3 * ((aoe_radius / 5.0 - d) / (aoe_radius / 5.0))

            # Bonus for being far from AoE origin points (cone/line avoidance)
            for enemy, aoe_radius, aoe_dmg in aoe_threats:
                dist_from_enemy = math.hypot(cx - enemy.grid_x, cy - enemy.grid_y)
                # For cones/lines originating from enemy, being to the side helps
                # Simple heuristic: spread perpendicular to enemy-target axis
                if dist_from_enemy < aoe_radius / 5.0:
                    score -= aoe_dmg * 0.1

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

            # Import LOS check for center point visibility
            from engine.terrain import check_los_blocked

            for (ccx, ccy) in candidates:
                # Caster must have LOS to AoE center point
                if check_los_blocked(battle.terrain, int(ecx), int(ecy), int(ccx), int(ccy)):
                    continue
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
