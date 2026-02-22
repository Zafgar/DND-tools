"""
D&D 5e 2014 Tactical AI for NPCs.
Computes an optimal TurnPlan for a given entity.
"""
import math
import random
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
    new_x: float = 0.0
    new_y: float = 0.0
    movement_ft: float = 0.0
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

        # ----- 2. MAIN ACTION -----
        action_step = self._decide_action(entity, enemies, allies, battle)
        if action_step:
            plan.steps.append(action_step)

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

    def _move_toward(self, entity, target, allies, battle):
        """Move toward target, trying flanking position. Respects terrain."""
        speed_sq = int(entity.movement_left // 5)
        flank = self._flanking_position(entity, target, allies, battle)
        dest_x = flank[0] if flank else target.grid_x
        dest_y = flank[1] if flank else target.grid_y

        start_x, start_y = entity.grid_x, entity.grid_y
        for _ in range(speed_sq):
            if math.hypot(entity.grid_x - dest_x, entity.grid_y - dest_y) < 0.5:
                break
            if battle.is_adjacent(entity, target):
                break
            dx = dest_x - entity.grid_x
            dy = dest_y - entity.grid_y
            nx, ny = entity.grid_x, entity.grid_y
            if abs(dx) >= abs(dy):
                nx += 1 if dx > 0 else -1
            else:
                ny += 1 if dy > 0 else -1
            if battle.is_passable(nx, ny, exclude=entity):
                entity.grid_x, entity.grid_y = nx, ny
            else:
                # Try the other axis as fallback
                nx2, ny2 = entity.grid_x, entity.grid_y
                if abs(dx) >= abs(dy):
                    ny2 += 1 if dy > 0 else (-1 if dy < 0 else 0)
                else:
                    nx2 += 1 if dx > 0 else (-1 if dx < 0 else 0)
                if battle.is_passable(nx2, ny2, exclude=entity):
                    entity.grid_x, entity.grid_y = nx2, ny2
                else:
                    break  # Fully blocked

        moved_ft = math.hypot(entity.grid_x - start_x, entity.grid_y - start_y) * 5
        if moved_ft < 0.5:
            return None
        entity.movement_left -= moved_ft
        return ActionStep(
            step_type="move",
            description=f"{entity.name} moves {moved_ft:.0f} ft.",
            attacker=entity,
            new_x=entity.grid_x, new_y=entity.grid_y,
            movement_ft=moved_ft,
        )

    def _move_toward_point(self, entity, tx, ty, battle):
        speed_sq = int(entity.movement_left // 5)
        start_x, start_y = entity.grid_x, entity.grid_y
        for _ in range(speed_sq):
            if math.hypot(entity.grid_x - tx, entity.grid_y - ty) < 0.5:
                break
            dx = tx - entity.grid_x
            dy = ty - entity.grid_y
            nx = entity.grid_x + (1 if dx > 0 else -1 if dx < 0 else 0)
            ny = entity.grid_y + (1 if dy > 0 else -1 if dy < 0 else 0)
            if abs(dx) < abs(dy):
                nx, ny = entity.grid_x, entity.grid_y + (1 if dy > 0 else -1)
            if battle.is_passable(nx, ny, exclude=entity):
                entity.grid_x, entity.grid_y = nx, ny
            else:
                break
        moved_ft = math.hypot(entity.grid_x - start_x, entity.grid_y - start_y) * 5
        if moved_ft < 0.5:
            return None
        entity.movement_left -= moved_ft
        return ActionStep(step_type="move",
                          description=f"{entity.name} repositions {moved_ft:.0f} ft.",
                          attacker=entity, new_x=entity.grid_x, new_y=entity.grid_y,
                          movement_ft=moved_ft)

    def _move_away(self, entity, threat, battle):
        speed_sq = int(entity.movement_left // 5)
        start_x, start_y = entity.grid_x, entity.grid_y
        for _ in range(speed_sq):
            dx = entity.grid_x - threat.grid_x
            dy = entity.grid_y - threat.grid_y
            if abs(dx) >= abs(dy):
                nx = entity.grid_x + (1 if dx >= 0 else -1)
                ny = entity.grid_y
            else:
                nx = entity.grid_x
                ny = entity.grid_y + (1 if dy >= 0 else -1)
            if battle.is_passable(nx, ny, exclude=entity):
                entity.grid_x, entity.grid_y = nx, ny
            else:
                break
        moved_ft = math.hypot(entity.grid_x - start_x, entity.grid_y - start_y) * 5
        if moved_ft < 0.5:
            return None
        entity.movement_left -= moved_ft
        return ActionStep(step_type="move",
                          description=f"{entity.name} disengages and moves {moved_ft:.0f} ft.",
                          attacker=entity, new_x=entity.grid_x, new_y=entity.grid_y,
                          movement_ft=moved_ft)

    # ------------------------------------------------------------------ #
    # Main Action                                                          #
    # ------------------------------------------------------------------ #

    def _decide_action(self, entity, enemies, allies, battle):
        if entity.action_used:
            return None

        # Self-heal if critical and has healing ability
        if entity.hp / entity.max_hp < 0.25:
            heal_step = self._try_heal_action(entity)
            if heal_step:
                entity.action_used = True
                return heal_step

        # AoE spell if 3+ enemies grouped
        if entity.has_spell_slot(1) or entity.stats.cantrips:
            aoe_step = self._try_aoe_spell(entity, enemies, battle)
            if aoe_step:
                entity.action_used = True
                return aoe_step

        # Debuff spell (high-value target)
        if entity.has_spell_slot(1):
            debuff_step = self._try_debuff_spell(entity, enemies, battle)
            if debuff_step:
                entity.action_used = True
                return debuff_step

        # Best damage spell / cantrip
        if entity.stats.spells_known or entity.stats.cantrips:
            spell_step = self._try_damage_spell(entity, enemies, battle)
            if spell_step:
                entity.action_used = True
                return spell_step

        # Multiattack
        multi = next((a for a in entity.stats.actions if a.is_multiattack), None)
        if multi:
            step = self._execute_multiattack(entity, multi, enemies, battle)
            entity.action_used = True
            return step

        # Single best attack
        target = self._pick_target(entity, enemies)
        best_action = self._best_melee_or_ranged(entity, target, battle)
        if best_action:
            step = self._execute_attack(entity, best_action, target, battle)
            entity.action_used = True
            return step

        return None

    def _try_heal_action(self, entity):
        """Try to use a healing spell or potion."""
        # Check healing spells
        for spell in entity.stats.spells_known:
            if spell.heals and spell.targets == "self":
                slot = entity.get_slot_for_level(spell.level) if spell.level > 0 else 0
                if spell.level == 0 or entity.use_spell_slot(spell.level):
                    healed = roll_dice(spell.heals)
                    entity.heal(healed)
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
                entity.heal(healed)
                return ActionStep(
                    step_type="bonus_attack",
                    description=f"{entity.name} uses {item.name}, healing {healed} HP.",
                    attacker=entity, target=entity, action_name=item.name,
                )
        return None

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
                target_results = []
                total_desc = f"{entity.name} casts {spell.name} (Level {slot})"
                for t in clusters:
                    save_bonus = t.get_save_bonus(spell.save_ability)
                    roll = random.randint(1, 20) + save_bonus
                    dc = spell.save_dc_fixed if spell.save_dc_fixed else \
                         (entity.stats.spell_save_dc or 8 + entity.stats.proficiency_bonus
                          + entity.get_modifier(entity.stats.spellcasting_ability))
                    saved = roll >= dc
                    dmg = roll_dice(spell.damage_dice)
                    if saved and spell.half_on_save:
                        dmg //= 2
                    elif saved:
                        dmg = 0
                    dmg_dealt, _ = t.take_damage(dmg, spell.damage_type)
                    if not saved and spell.applies_condition:
                        t.add_condition(spell.applies_condition)
                    target_results.append((t, dmg_dealt, saved))

                desc_parts = []
                for t, d, s in target_results:
                    saved_str = " (saved, half)" if s and spell.half_on_save else " (saved)" if s else ""
                    desc_parts.append(f"{t.name} {d} dmg{saved_str}")
                return ActionStep(
                    step_type="spell",
                    description=f"{total_desc}: " + ", ".join(desc_parts),
                    attacker=entity, targets=clusters, spell=spell, slot_used=slot,
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
            save_bonus = target.get_save_bonus(spell.save_ability)
            roll = random.randint(1, 20) + save_bonus
            saved = roll >= dc
            if not saved:
                target.add_condition(spell.applies_condition)
                if spell.concentration:
                    entity.start_concentration(spell)
                desc = f"{entity.name} casts {spell.name} → {target.name}: FAILED save, {spell.applies_condition}!"
            else:
                desc = f"{entity.name} casts {spell.name} → {target.name}: saved ({roll} vs DC {dc})."
            return ActionStep(
                step_type="spell", description=desc,
                attacker=entity, target=target, spell=spell, slot_used=slot,
                action_name=spell.name, save_dc=dc, save_ability=spell.save_ability,
                applies_condition=spell.applies_condition if not saved else "",
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
                # Save-based spell
                save_bonus = target.get_save_bonus(spell.save_ability)
                roll = random.randint(1, 20) + save_bonus
                saved = roll >= dc
                dmg = roll_dice(spell.damage_dice)
                if saved and spell.half_on_save:
                    dmg //= 2
                elif saved:
                    dmg = 0
                dmg_dealt, _ = target.take_damage(dmg, spell.damage_type)
                saved_str = " (save, half)" if saved and spell.half_on_save else " (saved)" if saved else ""
                desc = (f"{entity.name} casts {spell.name} → {target.name}: "
                        f"{dmg_dealt} {spell.damage_type} dmg{saved_str}")
                return ActionStep(
                    step_type="spell", description=desc,
                    attacker=entity, target=target, spell=spell, slot_used=slot,
                    action_name=spell.name, damage=dmg_dealt,
                    damage_type=spell.damage_type, save_dc=dc,
                    save_ability=spell.save_ability,
                )
            else:
                # Attack roll
                adv = entity.has_attack_advantage(target, is_ranged=True)
                dis = entity.has_attack_disadvantage(target, is_ranged=True)
                total, nat, is_crit, is_fumble, roll_str = roll_attack(atk_bonus, adv, dis)
                is_hit = total >= target.stats.armor_class and not is_fumble
                dmg = 0
                if is_hit:
                    dmg = roll_dice_critical(spell.damage_dice) if is_crit else roll_dice(spell.damage_dice)
                    dmg_dealt, _ = target.take_damage(dmg, spell.damage_type)
                    dmg = dmg_dealt
                hit_str = "CRIT! " if is_crit else "Hit " if is_hit else "Miss "
                desc = (f"{entity.name} casts {spell.name} ({roll_str}+{atk_bonus}={total} "
                        f"vs AC {target.stats.armor_class}) {hit_str}→ {target.name}: {dmg} {spell.damage_type}")
                return ActionStep(
                    step_type="spell", description=desc,
                    attacker=entity, target=target, spell=spell, slot_used=slot,
                    action_name=spell.name, attack_roll=total, attack_roll_str=roll_str,
                    nat_roll=nat, is_crit=is_crit, is_hit=is_hit,
                    damage=dmg, damage_type=spell.damage_type,
                )
        return None

    def _execute_multiattack(self, entity, multi_action, enemies, battle):
        """Execute all attacks in a multiattack action."""
        steps_desc = []
        total_damage = 0
        primary_target = self._pick_target(entity, enemies)
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

        targets_used = []
        for sub in sub_actions:
            t = self._pick_target(entity, [e for e in enemies if e.hp > 0])
            if not t:
                break
            dist = battle.get_distance(entity, t)
            if sub.range // 5 < dist - 0.5:
                continue
            adv = entity.has_attack_advantage(t, is_ranged=sub.range > 5)
            dis = entity.has_attack_disadvantage(t, is_ranged=sub.range > 5)
            # Check flanking bonus
            allies_adj = [a for a in battle.get_allies_of(entity) if battle.is_adjacent(a, t)]
            if allies_adj:
                adv = True
            total, nat, is_crit, is_fumble, roll_str = roll_attack(sub.attack_bonus, adv, dis)
            is_hit = total >= t.stats.armor_class and not is_fumble
            crit_auto = (t.has_condition("Paralyzed") or t.has_condition("Unconscious")) and dist <= 1.5
            if crit_auto:
                is_crit, is_hit = True, True
            dmg = 0
            dtype = sub.damage_type
            if is_hit:
                dmg_str = f"{sub.damage_dice}+{sub.damage_bonus}" if sub.damage_bonus else sub.damage_dice
                dmg = roll_dice_critical(dmg_str) if is_crit else roll_dice(dmg_str)
                dmg_dealt, broke = t.take_damage(dmg, dtype)
                dmg = dmg_dealt
                total_damage += dmg
                if sub.applies_condition and not t.has_condition(sub.applies_condition):
                    if sub.condition_save:
                        save_bonus = t.get_save_bonus(sub.condition_save)
                        save_roll = random.randint(1, 20) + save_bonus
                        if save_roll < sub.condition_dc:
                            t.add_condition(sub.applies_condition)
                    else:
                        t.add_condition(sub.applies_condition)

            hit_str = "CRIT! " if is_crit else "HIT " if is_hit else "MISS "
            steps_desc.append(f"{sub.name} vs {t.name} ({roll_str}+{sub.attack_bonus}={total} "
                               f"vs AC {t.stats.armor_class}): {hit_str}{dmg} {dtype}")
            targets_used.append(t)

        return ActionStep(
            step_type="attack",
            description=f"{entity.name} Multiattack: " + " | ".join(steps_desc),
            attacker=entity,
            target=primary_target,
            targets=list(set(targets_used)),
            action_name=multi_action.name,
            damage=total_damage,
            is_hit=True,
        )

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

        dmg = 0
        if is_hit:
            dmg_str = f"{action.damage_dice}+{action.damage_bonus}" if action.damage_bonus else action.damage_dice
            dmg = roll_dice_critical(dmg_str) if is_crit else roll_dice(dmg_str)
            dmg_dealt, _ = target.take_damage(dmg, action.damage_type)
            dmg = dmg_dealt
            if action.applies_condition and not target.has_condition(action.applies_condition):
                if action.condition_save:
                    save_bonus = target.get_save_bonus(action.condition_save)
                    save_roll = random.randint(1, 20) + save_bonus
                    if save_roll < action.condition_dc:
                        target.add_condition(action.applies_condition)
                else:
                    target.add_condition(action.applies_condition)

        hit_str = "CRIT! " if is_crit else "HIT " if is_hit else "MISS "
        desc = (f"{entity.name} {action.name} ({roll_str}+{action.attack_bonus}={total} "
                f"vs AC {target.stats.armor_class}): {hit_str}{dmg} {action.damage_type} → {target.name}")
        return ActionStep(
            step_type="attack", description=desc,
            attacker=entity, target=target, action_name=action.name,
            attack_roll=total, attack_roll_str=roll_str, nat_roll=nat,
            is_crit=is_crit, is_hit=is_hit,
            damage=dmg, damage_type=action.damage_type,
        )

    # ------------------------------------------------------------------ #
    # Bonus Action                                                         #
    # ------------------------------------------------------------------ #

    def _decide_bonus_action(self, entity, enemies, allies, battle):
        if entity.bonus_action_used:
            return None

        # Check bonus action attacks
        for ba in entity.stats.bonus_actions:
            target = self._pick_target(entity, enemies)
            if not target:
                continue
            dist = battle.get_distance(entity, target)
            if ba.range // 5 >= dist - 0.5:
                step = self._execute_attack(entity, ba, target, battle)
                step.step_type = "bonus_attack"
                entity.bonus_action_used = True
                return step

        # Healing bonus action spell
        for spell in entity.stats.spells_known:
            if spell.heals and spell.action_type == "bonus" and entity.hp < entity.max_hp * 0.7:
                if spell.level == 0 or entity.use_spell_slot(spell.level):
                    healed = roll_dice(spell.heals)
                    entity.heal(healed)
                    entity.bonus_action_used = True
                    return ActionStep(
                        step_type="bonus_attack",
                        description=f"{entity.name} uses bonus {spell.name}, heals {healed} HP.",
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
        def score(e):
            hp_pct = e.hp / e.max_hp
            dist = math.hypot(entity.grid_x - e.grid_x, entity.grid_y - e.grid_y)
            s = -dist * 2
            if hp_pct < 0.4:
                s += 20
            s -= (e.stats.armor_class - 12)
            return s
        return max(alive, key=score)

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
