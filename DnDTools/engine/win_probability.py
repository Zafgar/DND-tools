"""
Win Probability Calculator – estimates the probability that players will win
the current combat based on remaining HP, action economy, damage potential,
resources, and positional factors. Updates after each action.
"""
import math
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.entities import Entity
    from engine.battle import BattleSystem


class WinProbabilityCalculator:
    """Monte-Carlo-free win probability estimator using heuristic factors."""

    def __init__(self):
        self.history: List[dict] = []  # Timeline of probability snapshots

    def calculate(self, battle: "BattleSystem") -> dict:
        """Calculate current win probability for players."""
        players = [e for e in battle.entities if e.is_player and e.hp > 0]
        enemies = [e for e in battle.entities
                   if not e.is_player and e.hp > 0 and not e.is_lair and not e.is_summon]
        player_summons = [e for e in battle.entities
                          if e.is_summon and e.is_player and e.hp > 0]
        enemy_summons = [e for e in battle.entities
                         if e.is_summon and not e.is_player and e.hp > 0]

        if not enemies:
            return self._make_result(1.0, "No enemies remaining", battle.round)
        if not players:
            return self._make_result(0.0, "No players remaining", battle.round)

        # Factor 1: Effective HP ratio
        player_ehp = self._calc_effective_hp(players)
        enemy_ehp = self._calc_effective_hp(enemies)
        # Include summons at reduced weight
        player_ehp += self._calc_effective_hp(player_summons) * 0.3
        enemy_ehp += self._calc_effective_hp(enemy_summons) * 0.3

        hp_ratio = player_ehp / max(1, player_ehp + enemy_ehp)

        # Factor 2: Damage per round ratio
        player_dpr = sum(self._estimate_dpr(e) for e in players)
        enemy_dpr = sum(self._estimate_dpr(e) for e in enemies)
        player_dpr += sum(self._estimate_dpr(e) for e in player_summons) * 0.5
        enemy_dpr += sum(self._estimate_dpr(e) for e in enemy_summons) * 0.5

        dpr_ratio = player_dpr / max(1, player_dpr + enemy_dpr)

        # Factor 3: Action economy (number of entities)
        player_actions = len(players) + len(player_summons) * 0.5
        enemy_actions = len(enemies) + len(enemy_summons) * 0.5
        action_ratio = player_actions / max(1, player_actions + enemy_actions)

        # Factor 4: Resource advantage (spell slots, features, ki, etc.)
        player_resources = sum(self._resource_score(e) for e in players)
        enemy_resources = sum(self._resource_score(e) for e in enemies)
        resource_ratio = (player_resources + 1) / max(1, player_resources + enemy_resources + 2)

        # Factor 5: Condition advantage (debuffs on enemies vs players)
        condition_advantage = self._condition_factor(players, enemies)

        # Factor 6: Rounds to kill estimation
        rtk_factor = self._rounds_to_kill_factor(player_dpr, enemy_dpr,
                                                  player_ehp, enemy_ehp)

        # Weighted combination
        weights = {
            "hp": 0.25,
            "dpr": 0.25,
            "action_economy": 0.15,
            "resources": 0.15,
            "conditions": 0.10,
            "rtk": 0.10,
        }

        raw_prob = (
            weights["hp"] * hp_ratio +
            weights["dpr"] * dpr_ratio +
            weights["action_economy"] * action_ratio +
            weights["resources"] * resource_ratio +
            weights["conditions"] * condition_advantage +
            weights["rtk"] * rtk_factor
        )

        # Apply sigmoid-like curve to avoid extremes (5%-95% range)
        # This makes the probability more realistic
        probability = self._apply_confidence_curve(raw_prob)

        detail = (f"HP:{hp_ratio:.0%} DPR:{dpr_ratio:.0%} "
                  f"Actions:{action_ratio:.0%} Resources:{resource_ratio:.0%}")

        result = self._make_result(probability, detail, battle.round)

        # Store components for UI display
        result["factors"] = {
            "hp_ratio": round(hp_ratio, 3),
            "dpr_ratio": round(dpr_ratio, 3),
            "action_ratio": round(action_ratio, 3),
            "resource_ratio": round(resource_ratio, 3),
            "condition_advantage": round(condition_advantage, 3),
            "rtk_factor": round(rtk_factor, 3),
        }
        result["team_stats"] = {
            "player_ehp": round(player_ehp, 0),
            "enemy_ehp": round(enemy_ehp, 0),
            "player_dpr": round(player_dpr, 1),
            "enemy_dpr": round(enemy_dpr, 1),
            "player_count": len(players),
            "enemy_count": len(enemies),
        }

        self.history.append(result)
        return result

    def _make_result(self, probability: float, detail: str, round_num: int) -> dict:
        return {
            "probability": round(max(0.0, min(1.0, probability)), 3),
            "percentage": round(max(0.0, min(100.0, probability * 100)), 1),
            "detail": detail,
            "round": round_num,
            "label": self._prob_label(probability),
        }

    def _prob_label(self, prob: float) -> str:
        if prob >= 0.85:
            return "Decisive Advantage"
        elif prob >= 0.7:
            return "Strong Advantage"
        elif prob >= 0.55:
            return "Slight Advantage"
        elif prob >= 0.45:
            return "Even Fight"
        elif prob >= 0.3:
            return "Slight Disadvantage"
        elif prob >= 0.15:
            return "Strong Disadvantage"
        return "Dire Situation"

    def _apply_confidence_curve(self, raw: float) -> float:
        """Apply a sigmoid curve to keep probabilities in 5%-95% range."""
        # Logistic function centered at 0.5
        x = (raw - 0.5) * 6  # Scale factor
        sigmoid = 1.0 / (1.0 + math.exp(-x))
        # Map to 0.05-0.95 range
        return 0.05 + sigmoid * 0.90

    # ------------------------------------------------------------------ #
    # Component Calculators                                                #
    # ------------------------------------------------------------------ #

    def _calc_effective_hp(self, entities: List["Entity"]) -> float:
        """Calculate effective HP considering AC, resistances, temp HP."""
        total = 0.0
        for e in entities:
            base_hp = e.hp + e.temp_hp
            # AC effectiveness: higher AC means HP is worth more
            # Average attack bonus is roughly +5 to +8
            avg_atk = 6.5
            hit_chance = max(0.05, min(0.95, (21 - (e.stats.armor_class - avg_atk)) / 20))
            effective = base_hp / max(0.1, hit_chance)

            # Resistance bonus
            resistance_types = len(e.stats.damage_resistances)
            if resistance_types > 0:
                effective *= 1.0 + min(0.3, resistance_types * 0.1)

            # Rage halves physical damage
            if e.rage_active:
                effective *= 1.4

            # Condition penalties
            if e.is_incapacitated():
                effective *= 0.3
            elif e.has_condition("Stunned") or e.has_condition("Paralyzed"):
                effective *= 0.2

            total += effective
        return total

    def _estimate_dpr(self, entity: "Entity") -> float:
        """Estimate damage per round for an entity."""
        from engine.dice import average_damage

        if entity.is_incapacitated() or entity.hp <= 0:
            return 0.0

        best_dpr = 0.0

        # Multiattack
        multi = next((a for a in entity.stats.actions if a.is_multiattack), None)
        if multi:
            count = multi.multiattack_count
            sub_actions = []
            for name in multi.multiattack_targets or []:
                found = next((a for a in entity.stats.actions
                              if a.name == name and not a.is_multiattack), None)
                if found:
                    sub_actions.append(found)
            if not sub_actions:
                non_multi = [a for a in entity.stats.actions if not a.is_multiattack]
                if non_multi:
                    sub_actions = [non_multi[0]] * count

            total = 0.0
            for a in sub_actions:
                dmg_str = f"{a.damage_dice}+{a.damage_bonus}" if a.damage_bonus else a.damage_dice
                # Assume ~65% hit rate
                total += average_damage(dmg_str) * 0.65
            best_dpr = max(best_dpr, total)
        else:
            # Single attacks
            for a in entity.stats.actions:
                if a.is_multiattack:
                    continue
                dmg_str = f"{a.damage_dice}+{a.damage_bonus}" if a.damage_bonus else a.damage_dice
                est = average_damage(dmg_str) * 0.65
                best_dpr = max(best_dpr, est)

        # Add class mechanic bonuses
        if entity.has_feature("sneak_attack") and not entity.sneak_attack_used:
            sa_dice = entity.get_sneak_attack_dice()
            if sa_dice:
                best_dpr += average_damage(sa_dice) * 0.65

        if entity.has_feature("divine_smite") and entity.has_spell_slot(1):
            best_dpr += average_damage("2d8") * 0.65

        if entity.rage_active:
            best_dpr += entity.get_rage_damage_bonus() * 0.65

        if (entity.concentrating_on and
                entity.concentrating_on.name in ("Hunter's Mark", "Hex")):
            best_dpr += average_damage("1d6") * 0.65

        # Spell DPR (if higher than attacks)
        spell_dpr = self._estimate_spell_dpr(entity)
        best_dpr = max(best_dpr, spell_dpr)

        # Bonus action attacks
        for ba in entity.stats.bonus_actions:
            if ba.damage_dice:
                dmg_str = f"{ba.damage_dice}+{ba.damage_bonus}" if ba.damage_bonus else ba.damage_dice
                best_dpr += average_damage(dmg_str) * 0.65

        return best_dpr

    def _estimate_spell_dpr(self, entity: "Entity") -> float:
        """Estimate spell damage per round."""
        from engine.dice import average_damage

        best = 0.0
        for spell in entity.stats.spells_known + entity.stats.cantrips:
            if not spell.damage_dice:
                continue
            if spell.level > 0 and not entity.has_spell_slot(spell.level):
                continue
            avg = average_damage(spell.damage_dice)
            if spell.aoe_radius > 0:
                avg *= 2.5  # Assume hitting ~2.5 targets on average
            if spell.save_ability:
                avg *= 0.75  # ~50% save chance, half damage on save
            else:
                avg *= 0.65  # Attack roll hit chance
            best = max(best, avg)

        return best

    def _resource_score(self, entity: "Entity") -> float:
        """Score remaining resources (0-100 scale)."""
        score = 0.0

        # Spell slots (higher slots worth more)
        for lvl in range(1, 10):
            key = {1: "1st", 2: "2nd", 3: "3rd"}.get(lvl, f"{lvl}th")
            slots = entity.spell_slots.get(key, 0)
            score += slots * (lvl * 2)  # Level 5 slot = 10 points per slot

        # Class resources
        score += entity.ki_points_left * 1.5
        score += entity.sorcery_points_left * 1.5
        score += entity.lay_on_hands_left * 0.3
        score += entity.rages_left * 5
        score += entity.bardic_inspiration_left * 3

        # Feature uses
        for name, uses in entity.feature_uses.items():
            score += uses * 2

        # Legendary resources
        score += entity.legendary_resistances_left * 10
        score += entity.legendary_actions_left * 5

        return score

    def _condition_factor(self, players: List["Entity"],
                          enemies: List["Entity"]) -> float:
        """Calculate condition advantage factor (0.0 to 1.0, 0.5 = neutral)."""
        from data.conditions import INCAPACITATING_CONDITIONS

        player_debuffs = 0
        enemy_debuffs = 0

        for p in players:
            player_debuffs += len(p.conditions)
            if p.conditions & INCAPACITATING_CONDITIONS:
                player_debuffs += 3  # Extra penalty for incapacitation

        for e in enemies:
            enemy_debuffs += len(e.conditions)
            if e.conditions & INCAPACITATING_CONDITIONS:
                enemy_debuffs += 3

        total = player_debuffs + enemy_debuffs
        if total == 0:
            return 0.5

        # More enemy debuffs = better for players
        return 0.5 + (enemy_debuffs - player_debuffs) / max(1, total * 2)

    def _rounds_to_kill_factor(self, player_dpr: float, enemy_dpr: float,
                                player_ehp: float, enemy_ehp: float) -> float:
        """Factor based on how many rounds each side needs to kill the other."""
        player_rtk = enemy_ehp / max(1, player_dpr)   # Rounds for players to kill enemies
        enemy_rtk = player_ehp / max(1, enemy_dpr)     # Rounds for enemies to kill players

        # If players can kill faster, advantage
        if player_rtk + enemy_rtk == 0:
            return 0.5
        return enemy_rtk / max(1, player_rtk + enemy_rtk)

    # ------------------------------------------------------------------ #
    # History / Timeline                                                   #
    # ------------------------------------------------------------------ #

    def get_trend(self, last_n: int = 5) -> str:
        """Get trend direction from recent history."""
        if len(self.history) < 2:
            return "stable"

        recent = self.history[-last_n:]
        if len(recent) < 2:
            return "stable"

        first = recent[0]["probability"]
        last = recent[-1]["probability"]
        diff = last - first

        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        return "stable"

    def get_history_for_display(self) -> List[dict]:
        """Get probability history for UI charting."""
        return [
            {"round": h["round"], "probability": h["percentage"]}
            for h in self.history
        ]


# ------------------------------------------------------------------ #
# Pre-Combat Encounter Danger Assessment                               #
# ------------------------------------------------------------------ #

def assess_encounter_danger(players: List["Entity"],
                            enemies: List["Entity"]) -> dict:
    """
    Calculate encounter danger BEFORE combat starts.
    Uses D&D 5e CR/XP system plus additional heuristic analysis.
    """
    if not players or not enemies:
        return {
            "difficulty": "N/A",
            "danger_score": 0,
            "xp_total": 0,
            "adjusted_xp": 0,
            "survival_estimate": "N/A",
            "details": "Need both players and enemies",
        }

    # --- Standard D&D 5e XP Difficulty ---
    total_xp = sum(e.stats.xp for e in enemies)

    # Monster count multiplier (DMG rules)
    monster_count = len(enemies)
    if monster_count == 1:
        mult = 1.0
    elif monster_count == 2:
        mult = 1.5
    elif monster_count <= 6:
        mult = 2.0
    elif monster_count <= 10:
        mult = 2.5
    elif monster_count <= 14:
        mult = 3.0
    else:
        mult = 4.0

    # Adjust for party size
    party_size = len(players)
    if party_size < 3:
        mult *= 1.5
    elif party_size >= 6:
        mult *= 0.5

    adjusted_xp = int(total_xp * mult)

    # Party XP thresholds (based on character level)
    # Using average level of party
    avg_level = max(1, sum(
        e.stats.character_level if e.stats.character_level > 0 else 5
        for e in players
    ) // party_size)

    # XP thresholds per character level (from DMG)
    THRESHOLDS = {
        1: (25, 50, 75, 100), 2: (50, 100, 150, 200), 3: (75, 150, 225, 400),
        4: (125, 250, 375, 500), 5: (250, 500, 750, 1100), 6: (300, 600, 900, 1400),
        7: (350, 750, 1100, 1700), 8: (450, 900, 1400, 2100), 9: (550, 1100, 1600, 2400),
        10: (600, 1200, 1900, 2800), 11: (800, 1600, 2400, 3600),
        12: (1000, 2000, 3000, 4500), 13: (1100, 2200, 3400, 5100),
        14: (1250, 2500, 3800, 5700), 15: (1400, 2800, 4300, 6400),
        16: (1600, 3200, 4800, 7200), 17: (2000, 3900, 5900, 8800),
        18: (2100, 4200, 6300, 9500), 19: (2400, 4900, 7300, 10900),
        20: (2800, 5700, 8500, 12700),
    }

    thresholds = THRESHOLDS.get(avg_level, THRESHOLDS[5])
    easy_t = thresholds[0] * party_size
    medium_t = thresholds[1] * party_size
    hard_t = thresholds[2] * party_size
    deadly_t = thresholds[3] * party_size

    if adjusted_xp >= deadly_t * 2:
        difficulty = "TPK Risk"
        danger_level = 6
    elif adjusted_xp >= deadly_t:
        difficulty = "Deadly"
        danger_level = 5
    elif adjusted_xp >= hard_t:
        difficulty = "Hard"
        danger_level = 4
    elif adjusted_xp >= medium_t:
        difficulty = "Medium"
        danger_level = 3
    elif adjusted_xp >= easy_t:
        difficulty = "Easy"
        danger_level = 2
    else:
        difficulty = "Trivial"
        danger_level = 1

    # --- Heuristic Danger Analysis ---
    # Compare effective combat power
    from engine.dice import average_damage

    player_total_hp = sum(e.hp for e in players)
    enemy_total_hp = sum(e.hp for e in enemies)

    player_avg_ac = sum(e.stats.armor_class for e in players) / max(1, party_size)
    enemy_avg_ac = sum(e.stats.armor_class for e in enemies) / max(1, monster_count)

    # Estimate player DPR
    player_dpr = 0
    for p in players:
        best = 0
        multi = next((a for a in p.stats.actions if a.is_multiattack), None)
        if multi:
            count = multi.multiattack_count
            for a in p.stats.actions:
                if not a.is_multiattack:
                    dmg_str = f"{a.damage_dice}+{a.damage_bonus}" if a.damage_bonus else a.damage_dice
                    best += average_damage(dmg_str) * 0.65
                    count -= 1
                    if count <= 0:
                        break
        else:
            for a in p.stats.actions:
                if a.is_multiattack:
                    continue
                dmg_str = f"{a.damage_dice}+{a.damage_bonus}" if a.damage_bonus else a.damage_dice
                best = max(best, average_damage(dmg_str) * 0.65)
        player_dpr += best

    enemy_dpr = 0
    for e in enemies:
        best = 0
        multi = next((a for a in e.stats.actions if a.is_multiattack), None)
        if multi:
            count = multi.multiattack_count
            for a in e.stats.actions:
                if not a.is_multiattack:
                    dmg_str = f"{a.damage_dice}+{a.damage_bonus}" if a.damage_bonus else a.damage_dice
                    best += average_damage(dmg_str) * 0.65
                    count -= 1
                    if count <= 0:
                        break
        else:
            for a in e.stats.actions:
                if a.is_multiattack:
                    continue
                dmg_str = f"{a.damage_dice}+{a.damage_bonus}" if a.damage_bonus else a.damage_dice
                best = max(best, average_damage(dmg_str) * 0.65)
        enemy_dpr += best

    # Rounds to kill
    player_rtk = enemy_total_hp / max(1, player_dpr)
    enemy_rtk = player_total_hp / max(1, enemy_dpr)

    if enemy_rtk >= player_rtk * 2:
        survival = "Very likely to win with minimal casualties"
    elif enemy_rtk >= player_rtk * 1.3:
        survival = "Likely to win, possible casualties"
    elif enemy_rtk >= player_rtk * 0.8:
        survival = "Close fight, expect casualties"
    elif enemy_rtk >= player_rtk * 0.5:
        survival = "Dangerous, multiple casualties expected"
    else:
        survival = "Extremely dangerous, TPK likely without good tactics"

    # Danger score: 0-100
    danger_score = min(100, int(
        (danger_level / 6.0) * 40 +
        (1.0 - min(1.0, enemy_rtk / max(1, player_rtk))) * 40 +
        (monster_count / max(1, party_size)) * 10 +
        (enemy_avg_ac - player_avg_ac) * 2
    ))

    return {
        "difficulty": difficulty,
        "danger_level": danger_level,
        "danger_score": max(0, danger_score),
        "xp_total": total_xp,
        "adjusted_xp": adjusted_xp,
        "thresholds": {
            "easy": easy_t, "medium": medium_t,
            "hard": hard_t, "deadly": deadly_t,
        },
        "party_level_avg": avg_level,
        "survival_estimate": survival,
        "combat_estimate": {
            "player_total_hp": player_total_hp,
            "enemy_total_hp": enemy_total_hp,
            "player_dpr": round(player_dpr, 1),
            "enemy_dpr": round(enemy_dpr, 1),
            "player_rounds_to_kill": round(player_rtk, 1),
            "enemy_rounds_to_kill": round(enemy_rtk, 1),
            "expected_rounds": round((player_rtk + enemy_rtk) / 2, 1),
        },
        "details": (f"{difficulty} encounter | Party Lvl ~{avg_level} | "
                    f"XP: {total_xp} (adj: {adjusted_xp}) | "
                    f"Est. {round(player_rtk, 1)} rounds"),
    }
