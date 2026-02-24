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
        try:
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

            # Calculate averages for cross-referencing
            all_players = players + player_summons
            all_enemies = enemies + enemy_summons
            
            avg_player_ac = self._get_average_ac(all_players)
            avg_enemy_ac = self._get_average_ac(all_enemies)
            avg_player_atk = self._get_average_attack_bonus(all_players)
            avg_enemy_atk = self._get_average_attack_bonus(all_enemies)

            # Analyze damage types for resistance/immunity checking
            player_dmg_types = self._get_team_damage_profile(all_players)
            enemy_dmg_types = self._get_team_damage_profile(all_enemies)

            # Calculate average saves for spell DPR estimation
            avg_player_saves = self._get_average_saves(all_players)
            avg_enemy_saves = self._get_average_saves(all_enemies)

            # Calculate Healing Potential (HP reserve)
            player_healing = sum(self._estimate_healing_potential(e) for e in players)
            enemy_healing = sum(self._estimate_healing_potential(e) for e in enemies)

            # Factor 1: Effective HP ratio
            player_ehp = self._calc_effective_hp(players, avg_enemy_atk, enemy_dmg_types)
            enemy_ehp = self._calc_effective_hp(enemies, avg_player_atk, player_dmg_types)
            # Include summons at reduced weight
            player_ehp += self._calc_effective_hp(player_summons, avg_enemy_atk, enemy_dmg_types) * 0.3
            enemy_ehp += self._calc_effective_hp(enemy_summons, avg_player_atk, player_dmg_types) * 0.3

            # Add healing buffer to EHP (weighted 50% since it costs actions)
            player_ehp += player_healing * 0.5
            enemy_ehp += enemy_healing * 0.5

            # Calculate raw HP percentages for momentum tracking
            player_hp_pct, enemy_hp_pct = self._get_hp_percentages(players, enemies)

            hp_ratio = player_ehp / max(1, player_ehp + enemy_ehp)

            # Factor 2: Damage per round ratio
            player_dpr = sum(self._estimate_dpr(e, avg_enemy_ac, avg_enemy_saves, enemies) for e in players)
            enemy_dpr = sum(self._estimate_dpr(e, avg_player_ac, avg_player_saves, players) for e in enemies)
            player_dpr += sum(self._estimate_dpr(e, avg_enemy_ac, avg_enemy_saves, enemies) for e in player_summons) * 0.5
            enemy_dpr += sum(self._estimate_dpr(e, avg_player_ac, avg_player_saves, players) for e in enemy_summons) * 0.5

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

            # Factor 8: Positional Advantage
            position_factor = self._calculate_positional_advantage(players, enemies, battle)

            # Factor 7: Momentum (Trend)
            # Are players losing HP slower than enemies relative to previous rounds?
            momentum_factor = self._calculate_momentum(player_hp_pct, enemy_hp_pct)

            # Factor 9: Death Spiral (Critical HP)
            # If many members are near death (<15% HP), risk of losing actions skyrockets
            player_crit = sum(1 for e in players if e.hp / e.max_hp < 0.15)
            enemy_crit = sum(1 for e in enemies if e.hp / e.max_hp < 0.15)
            p_crit_ratio = player_crit / max(1, len(players))
            e_crit_ratio = enemy_crit / max(1, len(enemies))
            death_spiral_factor = 0.5 + (e_crit_ratio - p_crit_ratio) * 0.5

            # Weighted combination
            weights = {
                "hp": 0.15,
                "dpr": 0.20,
                "action_economy": 0.20,
                "resources": 0.10,
                "conditions": 0.10,
                "rtk": 0.10,
                "momentum": 0.05,
                "position": 0.10,
                "death_spiral": 0.10, # New factor
            }

            raw_prob = (
                weights["hp"] * hp_ratio +
                weights["dpr"] * dpr_ratio +
                weights["action_economy"] * action_ratio +
                weights["resources"] * resource_ratio +
                weights["conditions"] * condition_advantage +
                weights["rtk"] * rtk_factor +
                weights["momentum"] * momentum_factor +
                weights["position"] * position_factor +
                weights["death_spiral"] * death_spiral_factor
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
                "position_factor": round(position_factor, 3),
            }
            result["team_stats"] = {
                "player_ehp": round(player_ehp, 0),
                "enemy_ehp": round(enemy_ehp, 0),
                "player_dpr": round(player_dpr, 1),
                "enemy_dpr": round(enemy_dpr, 1),
                "player_count": len(players),
                "enemy_count": len(enemies),
                "raw_hp_stats": {
                    "player_pct": player_hp_pct,
                    "enemy_pct": enemy_hp_pct
                }
            }

            self.history.append(result)
            return result
        except Exception as e:
            print(f"[ERROR] Win probability calculation failed: {e}")
            return None

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
        # Softer curve to allow more "middle ground" (50/50)
        x = (raw - 0.5) * 4  # Reduced scale factor from 6 to 4
        sigmoid = 1.0 / (1.0 + math.exp(-x))
        # Map to 0.05-0.95 range but keep center linear-ish
        return 0.05 + sigmoid * 0.90

    # ------------------------------------------------------------------ #
    # Component Calculators                                                #
    # ------------------------------------------------------------------ #

    def _get_average_ac(self, entities: List["Entity"]) -> float:
        if not entities: return 15.0
        return sum(e.stats.armor_class for e in entities) / len(entities)

    def _get_average_attack_bonus(self, entities: List["Entity"]) -> float:
        if not entities: return 5.0
        total = 0
        for e in entities:
            best = 0
            for a in e.stats.actions:
                best = max(best, a.attack_bonus)
            if e.stats.spell_attack_bonus:
                best = max(best, e.stats.spell_attack_bonus)
            total += best
        return total / len(entities)

    def _get_average_saves(self, entities: List["Entity"]) -> Dict[str, float]:
        if not entities: return {}
        abilities = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
        totals = {k: 0.0 for k in abilities}
        for e in entities:
            for ab in abilities:
                totals[ab] += e.get_save_bonus(ab)
        return {k: v / len(entities) for k, v in totals.items()}

    def _get_team_damage_profile(self, entities: List["Entity"]) -> set:
        """Return set of damage types this team is capable of dealing."""
        types = set()
        for e in entities:
            # Actions
            for a in e.stats.actions:
                if a.damage_type: types.add(a.damage_type.lower())
            # Spells
            for s in e.stats.spells_known + e.stats.cantrips:
                if s.damage_type: types.add(s.damage_type.lower())
            # Features
            if e.has_feature("divine_smite") or e.has_feature("improved_divine_smite"):
                types.add("radiant")
            if e.has_feature("sneak_attack"):
                # Assume basic weapon types for sneak attack
                types.update(["piercing", "slashing"])
        return types

    def _calc_effective_hp(self, entities: List["Entity"], opposing_atk_bonus: float,
                           opposing_damage_types: set) -> float:
        """Calculate effective HP considering AC, resistances, temp HP."""
        total = 0.0
        for e in entities:
            base_hp = e.hp + e.temp_hp
            # AC effectiveness: higher AC means HP is worth more
            # Calculate chance to be hit based on opposing attack bonus
            hit_chance = (21 + opposing_atk_bonus - e.stats.armor_class) / 20.0
            hit_chance = max(0.05, min(0.95, hit_chance))
            
            # Adjust for conditions granting Advantage to attackers (Restrained, Paralyzed, etc.)
            if e.has_condition("Restrained") or e.has_condition("Paralyzed") or \
               e.has_condition("Stunned") or e.has_condition("Unconscious") or \
               e.has_condition("Blinded"):
                # Probability of being hit increases significantly with Advantage
                # Formula: p_adv = 1 - (1-p)^2
                hit_chance = 1.0 - (1.0 - hit_chance) ** 2

            effective = base_hp / max(0.1, hit_chance)

            # Resistance bonus
            # Only count resistances that match opposing damage types
            relevant_resists = 0
            relevant_vulns = 0
            
            for dt in opposing_damage_types:
                if dt in e.stats.damage_resistances:
                    relevant_resists += 1
                if dt in e.stats.damage_vulnerabilities:
                    relevant_vulns += 1
                # Rage check
                if e.rage_active and dt in ("bludgeoning", "piercing", "slashing"):
                    relevant_resists += 1

            if relevant_resists > 0:
                effective *= 1.5  # ~50% reduction means 2x EHP, but assume mixed damage so 1.5x
            if relevant_vulns > 0:
                effective *= 0.6  # Vulnerability reduces EHP

            # Condition penalties
            if e.is_incapacitated():
                effective *= 0.3
            elif e.has_condition("Stunned") or e.has_condition("Paralyzed"):
                effective *= 0.2

            # Penalties for bad positioning/state
            if e.has_condition("Prone"):
                effective *= 0.85  # Vulnerable to melee
            if e.has_condition("Grappled"):
                effective *= 0.9   # Cannot move to safety

            # Player Death Save Buffer (players don't die instantly at 0 HP)
            if e.is_player and e.hp > 0:
                effective += 10

            total += effective
        return total

    def _estimate_dpr(self, entity: "Entity", target_ac: float, target_saves: dict, targets: List["Entity"]) -> float:
        """Estimate damage per round for an entity."""
        from engine.dice import average_damage

        if entity.is_incapacitated() or entity.hp <= 0:
            return 0.0

        # --- Range Check ---
        # If entity cannot reach any enemy, DPR is effectively 0 for this turn
        enemies = targets # Use passed targets list
        if not enemies: return 0.0
        
        # Calculate approximate distance to closest enemy
        closest_dist_ft = min(math.hypot(entity.grid_x - e.grid_x, entity.grid_y - e.grid_y) * 5 for e in enemies)
        
        # Simplified range check (assuming average distance if battle ref not avail, or 0)
        # For win prob, we assume they can engage eventually.
        
        # Determine max effective range (Movement + Action Range)
        max_action_range = 5
        for a in entity.stats.actions:
            max_action_range = max(max_action_range, a.range)
        for s in entity.stats.spells_known:
            if s.damage_dice:
                max_action_range = max(max_action_range, s.range)
        
        # If melee only, we can move. If ranged, we can shoot.
        # Effective threat range = Speed + Action Range
        # Use current speed (accounts for Grappled/Restrained/Prone)
        current_speed = entity.get_speed()
        threat_range = current_speed + max_action_range
        
        if closest_dist_ft > threat_range:
            # Cannot reach anyone this turn to deal damage
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
                hit_chance = (21 + a.attack_bonus - target_ac) / 20.0
                hit_chance = max(0.05, min(0.95, hit_chance))
                
                # Check immunity
                if self._is_team_immune(targets, a.damage_type):
                    hit_chance = 0.0

                total += average_damage(dmg_str) * hit_chance
            best_dpr = max(best_dpr, total)
        else:
            # Single attacks
            for a in entity.stats.actions:
                if a.is_multiattack:
                    continue
                dmg_str = f"{a.damage_dice}+{a.damage_bonus}" if a.damage_bonus else a.damage_dice
                hit_chance = (21 + a.attack_bonus - target_ac) / 20.0
                hit_chance = max(0.05, min(0.95, hit_chance))
                
                # Check immunity
                if self._is_team_immune(targets, a.damage_type):
                    hit_chance = 0.0

                est = average_damage(dmg_str) * hit_chance
                best_dpr = max(best_dpr, est)

        # Base hit chance for features (approximate)
        base_hit_chance = max(0.05, min(0.95, (21 + entity.stats.proficiency_bonus + 3 - target_ac) / 20.0))

        # Add class mechanic bonuses
        if entity.has_feature("sneak_attack") and not entity.sneak_attack_used:
            sa_dice = entity.get_sneak_attack_dice()
            if sa_dice:
                best_dpr += average_damage(sa_dice) * base_hit_chance

        if entity.has_feature("divine_smite") and entity.has_spell_slot(1):
            best_dpr += average_damage("2d8") * base_hit_chance

        if entity.rage_active:
            best_dpr += entity.get_rage_damage_bonus() * base_hit_chance

        if (entity.concentrating_on and
                entity.concentrating_on.name in ("Hunter's Mark", "Hex")):
            best_dpr += average_damage("1d6") * base_hit_chance

        # Spell DPR (if higher than attacks)
        spell_dpr = self._estimate_spell_dpr(entity, target_ac, target_saves, targets)
        best_dpr = max(best_dpr, spell_dpr)

        # --- Legendary Actions ---
        # Add estimated damage from legendary actions (if any)
        if entity.stats.legendary_action_count > 0:
            leg_actions = [a for a in entity.stats.actions if a.action_type == "legendary"]
            # If no explicit legendary actions found, assume basic attack can be used (common homebrew/fallback)
            if not leg_actions:
                leg_actions = [a for a in entity.stats.actions if not a.is_multiattack and a.damage_dice]
            
            if leg_actions:
                # Pick best option
                best_leg = max(leg_actions, key=lambda a: average_damage(f"{a.damage_dice}+{a.damage_bonus}" if a.damage_bonus else a.damage_dice))
                dmg_str = f"{best_leg.damage_dice}+{best_leg.damage_bonus}" if best_leg.damage_bonus else best_leg.damage_dice
                
                hit_chance = (21 + best_leg.attack_bonus - target_ac) / 20.0
                hit_chance = max(0.05, min(0.95, hit_chance))

                # Check immunity
                if self._is_team_immune(targets, best_leg.damage_type):
                    hit_chance = 0.0
                
                # Assume 1 action cost per attack for estimation
                leg_dpr = average_damage(dmg_str) * hit_chance * entity.stats.legendary_action_count
                best_dpr += leg_dpr

        # Bonus action attacks
        for ba in entity.stats.bonus_actions:
            if ba.damage_dice:
                dmg_str = f"{ba.damage_dice}+{ba.damage_bonus}" if ba.damage_bonus else ba.damage_dice
                hit_chance = (21 + ba.attack_bonus - target_ac) / 20.0
                hit_chance = max(0.05, min(0.95, hit_chance))
                if self._is_team_immune(targets, ba.damage_type):
                    hit_chance = 0.0
                best_dpr += average_damage(dmg_str) * hit_chance

        # Apply offensive penalties (Disadvantage on attacks)
        if entity.has_condition("Poisoned") or entity.has_condition("Frightened") or \
           entity.has_condition("Restrained") or entity.has_condition("Blinded") or \
           entity.has_condition("Prone") or entity.exhaustion >= 3:
            best_dpr *= 0.65 # Disadvantage penalty estimate

        return best_dpr

    def _estimate_spell_dpr(self, entity: "Entity", target_ac: float, target_saves: dict, targets: List["Entity"]) -> float:
        """Estimate spell damage per round."""
        from engine.dice import average_damage

        best = 0.0
        for spell in entity.stats.spells_known + entity.stats.cantrips:
            if not spell.damage_dice:
                continue
            if spell.level > 0 and not entity.has_spell_slot(spell.level):
                continue
            
            # Check immunity
            if self._is_team_immune(targets, spell.damage_type):
                continue

            avg = average_damage(spell.damage_dice)
            if spell.aoe_radius > 0:
                avg *= 2.5  # Assume hitting ~2.5 targets on average
            if spell.save_ability:
                # Find best target (lowest save bonus) to simulate smart AI
                dc = spell.save_dc_fixed or (entity.stats.spell_save_dc or 10)
                best_fail_chance = 0.0
                
                if targets:
                    for t in targets:
                        bonus = t.get_save_bonus(spell.save_ability)
                        success_chance = (21 + bonus - dc) / 20.0
                        success_chance = max(0.05, min(0.95, success_chance))
                        fail_chance = 1.0 - success_chance
                        if fail_chance > best_fail_chance:
                            best_fail_chance = fail_chance
                else:
                    # Fallback to average if no targets list
                    bonus = target_saves.get(spell.save_ability, 0)
                    success_chance = (21 + bonus - dc) / 20.0
                    success_chance = max(0.05, min(0.95, success_chance))
                    best_fail_chance = 1.0 - success_chance
                
                if spell.half_on_save:
                    avg = avg * best_fail_chance + (avg / 2.0) * (1.0 - best_fail_chance)
                else:
                    avg = avg * best_fail_chance
            else:
                atk = spell.attack_bonus_fixed or (
                    entity.stats.spell_attack_bonus or 
                    entity.stats.proficiency_bonus + entity.get_modifier(entity.stats.spellcasting_ability))
                hit_chance = (21 + atk - target_ac) / 20.0
                avg *= max(0.05, min(0.95, hit_chance))
            best = max(best, avg)

        return best

    def _is_team_immune(self, targets: List["Entity"], damage_type: str) -> bool:
        """Check if ALL targets are immune to this damage type."""
        if not targets or not damage_type: return False
        for t in targets:
            if damage_type.lower() not in t.stats.damage_immunities:
                return False # At least one target is not immune
        return True

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

    def _get_hp_percentages(self, players, enemies):
        p_cur = sum(e.hp for e in players)
        p_max = sum(e.max_hp for e in players)
        e_cur = sum(e.hp for e in enemies)
        e_max = sum(e.max_hp for e in enemies)
        return (p_cur / max(1, p_max), e_cur / max(1, e_max))

    def _calculate_momentum(self, current_p_pct, current_e_pct) -> float:
        """
        Calculate momentum based on HP trends.
        Returns 0.0 (Enemies gaining fast) to 1.0 (Players gaining fast).
        0.5 is neutral (both losing at same rate or no change).
        """
        if not self.history:
            return 0.5

        # Look back 1-2 snapshots
        prev = self.history[-1]
        if "raw_hp_stats" not in prev.get("team_stats", {}):
            return 0.5
        
        prev_p_pct = prev["team_stats"]["raw_hp_stats"]["player_pct"]
        prev_e_pct = prev["team_stats"]["raw_hp_stats"]["enemy_pct"]

        # Delta: Positive means we kept HP better than they did
        p_delta = current_p_pct - prev_p_pct # usually negative
        e_delta = current_e_pct - prev_e_pct # usually negative

        # If players lost less HP % than enemies, that's good momentum
        # diff > 0 means players doing better
        diff = p_delta - e_delta
        
        # Clamp to 0.0 - 1.0 range centered at 0.5
        return max(0.0, min(1.0, 0.5 + diff * 2))

    def _calculate_positional_advantage(self, players, enemies, battle) -> float:
        """
        Analyze positions:
        - Are squishies safe?
        - Are enemies clumped for AoE?
        - Are players clumped vs enemy AoE?
        Returns 0.0 (Terrible positioning) to 1.0 (Perfect positioning).
        """
        score = 0.5  # Neutral start

        # 1. Melee Threat vs Safety
        for p in players:
            # Identify if squishy (low AC or Caster class)
            is_squishy = p.stats.armor_class < 15 or p.stats.character_class in ("Wizard", "Sorcerer", "Bard", "Warlock")
            
            closest_enemy_dist = 999
            nearest_enemy = None
            for e in enemies:
                d = battle.get_distance(p, e) * 5
                if d < closest_enemy_dist:
                    closest_enemy_dist = d
                    nearest_enemy = e
            
            if nearest_enemy:
                threat_range = nearest_enemy.stats.speed
                if closest_enemy_dist <= 5:
                    # In melee
                    if is_squishy: score -= 0.05 # Bad for squishy
                elif closest_enemy_dist <= threat_range:
                    # Can be reached next turn
                    if is_squishy: score -= 0.02
                else:
                    # Safe from immediate melee
                    if is_squishy: score += 0.02

        # 2. AoE Potential (Players hitting Enemies)
        player_aoe_potential = 0
        for p in players:
            has_aoe = any(s.aoe_radius > 0 for s in p.stats.spells_known)
            if has_aoe:
                # Check for clusters of enemies
                cluster = battle.ai._best_aoe_cluster(p, enemies, players, battle, 20)
                if len(cluster) >= 2:
                    player_aoe_potential += 1
        score += min(0.15, player_aoe_potential * 0.05)

        # 3. AoE Vulnerability (Enemies hitting Players)
        enemy_aoe_threat = 0
        for e in enemies:
            cluster = battle.ai._best_aoe_cluster(e, players, enemies, battle, 20)
            if len(cluster) >= 2:
                enemy_aoe_threat += 1
        score -= min(0.15, enemy_aoe_threat * 0.05)

        return max(0.0, min(1.0, score))

    def _estimate_healing_potential(self, entity: "Entity") -> float:
        """Estimate potential HP recovery available to this entity."""
        from engine.dice import average_damage
        potential = 0.0
        
        # 1. Class Features
        if entity.lay_on_hands_left > 0:
            potential += entity.lay_on_hands_left
        
        if entity.has_feature("second_wind") and entity.can_use_feature("Second Wind"):
            # 1d10 + level
            potential += 5.5 + entity.stats.character_level

        if entity.has_feature("wholeness_of_body") and entity.can_use_feature("Wholeness of Body"):
            # 3 * level
            potential += 3 * entity.stats.character_level
            
        if entity.has_feature("combat_wild_shape"):
            # Moon Druid buffer estimate
            potential += 10

        # 2. Potions
        for item in entity.items:
            if item.heals and item.uses > 0:
                potential += average_damage(item.heals) * item.uses

        # 3. Spells (Heuristic: if has healing spells, count % of slots as HP pool)
        has_healing_spell = any(s.heals for s in entity.stats.spells_known)
        if has_healing_spell:
            slot_healing = 0
            level_keys = {1:"1st",2:"2nd",3:"3rd",4:"4th",5:"5th",6:"6th",7:"7th",8:"8th",9:"9th"}
            for lvl in range(1, 10):
                key = level_keys.get(lvl, f"{lvl}th")
                count = entity.spell_slots.get(key, 0)
                # Approx 1d8+3 (7.5) per level scaling heuristic
                slot_healing += count * (lvl * 5 + 4)
            potential += slot_healing * 0.4

        return potential

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
    try:
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
    except Exception as e:
        print(f"[ERROR] Encounter assessment failed: {e}")
        return {
            "difficulty": "Error",
            "danger_score": 0,
            "xp_total": 0,
            "adjusted_xp": 0,
            "survival_estimate": "Calculation Error",
            "details": str(e),
        }
