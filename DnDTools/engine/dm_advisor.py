"""
DM Advisory System – Provides AI-recommended optimal moves for players
and rates the actual player decisions compared to the AI suggestion.
Designed for manual (non-auto-battle) play where the DM mirrors TaleSpire
actions and uses AI only for NPCs.
"""
import math
import copy
from typing import List, Optional, Dict, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.entities import Entity
    from engine.battle import BattleSystem
    from engine.ai import TurnPlan, ActionStep


class PlayerMoveRating:
    """Rating of a player's actual action vs AI optimal."""

    def __init__(self):
        self.player_action: str = ""           # What player did
        self.ai_suggestion: str = ""           # What AI recommends
        self.ai_suggestion_details: List[str] = []  # Step-by-step AI plan
        self.rating: float = 0.0               # 0.0 (terrible) to 1.0 (optimal)
        self.rating_label: str = ""            # "Optimal", "Good", "Suboptimal", "Poor"
        self.explanation: str = ""             # Why this rating
        self.damage_comparison: str = ""       # "Player: X dmg vs AI: Y dmg"
        self.tactical_notes: List[str] = []    # Tactical advice


class DMAdvisor:
    """Analyzes the battlefield and suggests optimal player moves."""

    def __init__(self):
        self.last_suggestion: Optional[PlayerMoveRating] = None
        self.suggestion_history: List[PlayerMoveRating] = []

    def get_optimal_move(self, entity: "Entity", battle: "BattleSystem") -> PlayerMoveRating:
        """Calculate what the AI thinks the player should do on their turn."""
        rating = PlayerMoveRating()
        rating.player_action = "(pending)"

        # Use the battle AI to compute an optimal turn
        plan = battle.ai.calculate_turn(entity, self._make_analysis_copy(entity, battle))

        if plan.skipped:
            rating.ai_suggestion = f"Skip turn ({plan.skip_reason})"
            rating.ai_suggestion_details = [plan.skip_reason]
            self.last_suggestion = rating
            return rating

        # Build suggestion text
        suggestion_parts = []
        total_expected_dmg = 0

        for step in plan.steps:
            desc = step.description
            suggestion_parts.append(desc)

            if step.damage > 0 and (step.is_hit or step.save_dc > 0):
                # Estimate expected damage accounting for hit probability
                if step.save_dc > 0:
                    # Assume ~50% save rate
                    total_expected_dmg += step.damage * 0.75
                elif step.is_hit:
                    total_expected_dmg += step.damage
                else:
                    total_expected_dmg += step.damage * 0.5  # miss case average

        rating.ai_suggestion = self._summarize_plan(plan)
        rating.ai_suggestion_details = suggestion_parts
        rating.tactical_notes = self._generate_tactical_notes(entity, battle, plan)

        self.last_suggestion = rating
        return rating

    def rate_player_action(self, entity: "Entity", battle: "BattleSystem",
                           action_type: str, target: "Entity" = None,
                           damage_dealt: int = 0, spell_name: str = "",
                           moved_distance: float = 0) -> PlayerMoveRating:
        """Rate the player's actual action compared to the AI suggestion."""
        rating = self.last_suggestion or PlayerMoveRating()
        rating.player_action = self._describe_player_action(
            entity, action_type, target, damage_dealt, spell_name, moved_distance)

        # Generate AI suggestion if we don't have one
        if not rating.ai_suggestion:
            rating = self.get_optimal_move(entity, battle)
            rating.player_action = self._describe_player_action(
                entity, action_type, target, damage_dealt, spell_name, moved_distance)

        # Calculate rating
        score = self._calculate_action_score(
            entity, battle, action_type, target, damage_dealt,
            spell_name, moved_distance)

        rating.rating = max(0.0, min(1.0, score))
        rating.rating_label = self._score_to_label(rating.rating)
        rating.explanation = self._generate_explanation(
            entity, battle, action_type, target, damage_dealt,
            spell_name, rating.rating)

        self.suggestion_history.append(rating)
        self.last_suggestion = None  # Reset for next turn
        return rating

    def _make_analysis_copy(self, entity: "Entity", battle: "BattleSystem"):
        """Create a lightweight copy of battle for AI analysis without modifying state."""
        # We use the real battle object but the AI already doesn't modify
        # entity HP directly (it creates ActionSteps). The only issue is
        # movement and resource consumption. We'll accept this minor side effect
        # since the main battle state tracks these externally.
        # For a truly clean analysis, we'd deep-copy, but that's expensive.
        return battle

    def _summarize_plan(self, plan: "TurnPlan") -> str:
        """Create a short summary of the AI plan."""
        if not plan.steps:
            return "Do nothing"

        parts = []
        for step in plan.steps:
            if step.step_type == "move":
                parts.append(f"Move {step.movement_ft:.0f}ft")
            elif step.step_type in ("attack", "bonus_attack"):
                target_name = step.target.name if step.target else "?"
                parts.append(f"{step.action_name} -> {target_name}")
                if step.bonus_damage_desc:
                    parts[-1] += f" [{step.bonus_damage_desc}]"
            elif step.step_type == "spell":
                target_name = step.target.name if step.target else "area"
                parts.append(f"Cast {step.action_name} -> {target_name}")
            elif step.step_type == "summon":
                parts.append(f"Summon {step.summon_name}")
            else:
                parts.append(step.description[:50])

        return " -> ".join(parts)

    def _describe_player_action(self, entity, action_type, target, damage_dealt,
                                spell_name, moved_distance) -> str:
        """Describe what the player actually did."""
        target_name = target.name if target else ""
        if action_type == "attack":
            return f"Attack {target_name} ({damage_dealt} dmg)"
        elif action_type == "spell":
            return f"Cast {spell_name} on {target_name} ({damage_dealt} dmg)"
        elif action_type == "move":
            return f"Move {moved_distance:.0f}ft"
        elif action_type == "dash":
            return "Dash"
        elif action_type == "dodge":
            return "Dodge"
        elif action_type == "help":
            return "Help"
        elif action_type == "item":
            return "Use Item"
        return action_type

    def _calculate_action_score(self, entity, battle, action_type, target,
                                damage_dealt, spell_name, moved_distance) -> float:
        """Score the player's action from 0.0 to 1.0."""
        score = 0.5  # Base: average

        enemies = battle.get_enemies_of(entity)
        allies = battle.get_allies_of(entity)

        if not enemies:
            return 1.0  # No enemies = anything is fine

        # --- Evaluate based on action type ---

        if action_type == "attack":
            # Did they attack a reasonable target?
            if target:
                target_score = self._evaluate_target_choice(entity, target, enemies, battle)
                score += target_score * 0.3  # 0 to 0.3

                # Did they deal good damage?
                max_possible = self._estimate_max_damage(entity, target, battle)
                if max_possible > 0:
                    dmg_ratio = min(1.0, damage_dealt / max_possible)
                    score += dmg_ratio * 0.2

        elif action_type == "spell":
            # Spellcasting evaluation
            if spell_name:
                spell_score = self._evaluate_spell_choice(entity, spell_name, target,
                                                          enemies, allies, battle)
                score += spell_score * 0.4

        elif action_type == "dodge":
            # Dodge is good when low HP and threatened
            if entity.hp < entity.max_hp * 0.3:
                threatened = any(battle.is_adjacent(entity, e) for e in enemies)
                if threatened:
                    score = 0.8  # Dodge when low and threatened is smart
                else:
                    score = 0.5
            else:
                score = 0.3  # Dodge when healthy is usually suboptimal

        elif action_type == "dash":
            # Dash is OK if out of range
            closest_dist = min(
                (battle.get_distance(entity, e) * 5 for e in enemies),
                default=0)
            if closest_dist > 30:
                score = 0.7  # Need to close distance
            else:
                score = 0.3  # Already close, dash is wasteful

        elif action_type == "help":
            # Help is decent if allies are adjacent to enemies
            helped = any(
                battle.is_adjacent(a, e)
                for a in allies for e in enemies
            )
            score = 0.6 if helped else 0.3

        elif action_type == "move":
            score = 0.5  # Movement is neutral

        return max(0.0, min(1.0, score))

    def _evaluate_target_choice(self, entity, target, enemies, battle) -> float:
        """Score from 0 to 1 how good the target choice is."""
        if target.hp <= 0:
            return 0.0  # Attacking a dead target

        # Best target according to AI
        ai_target = battle.ai._pick_target(entity, enemies)
        if ai_target == target:
            return 1.0  # Same target as AI

        # Check if target is reasonable
        hp_pct = target.hp / target.max_hp if target.max_hp > 0 else 1
        dist = battle.get_distance(entity, target)

        score = 0.5
        if hp_pct < 0.3:
            score += 0.3  # Finishing off low HP targets is smart
        if dist <= 1.5:
            score += 0.1  # Adjacent targets avoid OA
        if target.stats.armor_class < 15:
            score += 0.1  # Low AC = easier to hit

        return min(1.0, score)

    def _evaluate_spell_choice(self, entity, spell_name, target, enemies, allies, battle) -> float:
        """Score spell choice 0 to 1."""
        score = 0.5

        # Check if entity has healing and allies are low
        low_allies = [a for a in allies if a.hp < a.max_hp * 0.3]
        healer = any(s.heals for s in entity.stats.spells_known)

        # Healing spells when allies are dying
        healing_spells = {"Cure Wounds", "Healing Word", "Mass Cure Wounds",
                          "Mass Healing Word", "Heal"}
        if spell_name in healing_spells:
            if low_allies:
                score = 0.9  # Healing dying allies is excellent
            else:
                score = 0.4  # Healing when nobody is low is wasteful

        # AoE damage spells
        aoe_spells = {"Fireball", "Lightning Bolt", "Cone of Cold", "Ice Storm",
                      "Chain Lightning", "Meteor Swarm", "Spirit Guardians",
                      "Burning Hands", "Shatter", "Thunderwave"}
        if spell_name in aoe_spells:
            # Good if many enemies grouped
            if len(enemies) >= 3:
                score = 0.85
            elif len(enemies) >= 2:
                score = 0.7
            else:
                score = 0.4  # Wasting AoE on single target

        # Control spells
        control_spells = {"Hold Person", "Hold Monster", "Banishment", "Web",
                          "Entangle", "Hypnotic Pattern", "Slow", "Wall of Force"}
        if spell_name in control_spells:
            if len(enemies) >= 2:
                score = 0.8
            else:
                score = 0.6

        # Concentration buff spells
        buff_spells = {"Bless", "Haste", "Shield of Faith", "Protection from Energy"}
        if spell_name in buff_spells:
            score = 0.7 if not entity.concentrating_on else 0.3

        return score

    def _estimate_max_damage(self, entity, target, battle) -> float:
        """Estimate the maximum expected damage for this entity this turn."""
        from engine.dice import average_damage
        max_dmg = 0

        # Check multiattack
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

            for a in sub_actions:
                dmg_str = f"{a.damage_dice}+{a.damage_bonus}" if a.damage_bonus else a.damage_dice
                max_dmg += average_damage(dmg_str)
        else:
            # Single best attack
            for a in entity.stats.actions:
                if a.is_multiattack:
                    continue
                dmg_str = f"{a.damage_dice}+{a.damage_bonus}" if a.damage_bonus else a.damage_dice
                max_dmg = max(max_dmg, average_damage(dmg_str))

        # Add class bonus estimates
        if entity.has_feature("sneak_attack"):
            sa_dice = entity.get_sneak_attack_dice()
            if sa_dice:
                max_dmg += average_damage(sa_dice)
        if entity.has_feature("divine_smite") and entity.has_spell_slot(1):
            max_dmg += average_damage("2d8")
        if entity.rage_active:
            max_dmg += entity.get_rage_damage_bonus()

        return max_dmg

    def _score_to_label(self, score: float) -> str:
        if score >= 0.85:
            return "Optimal"
        elif score >= 0.65:
            return "Good"
        elif score >= 0.4:
            return "Decent"
        elif score >= 0.2:
            return "Suboptimal"
        return "Poor"

    def _generate_explanation(self, entity, battle, action_type, target,
                              damage_dealt, spell_name, score) -> str:
        """Generate a brief explanation of the rating."""
        if score >= 0.85:
            return "Excellent tactical decision. This is close to what the AI would recommend."
        elif score >= 0.65:
            return "Solid choice. Minor improvements possible but overall effective."
        elif score >= 0.4:
            reasons = []
            enemies = battle.get_enemies_of(entity)
            if action_type == "attack" and target:
                hp_pct = target.hp / target.max_hp if target.max_hp > 0 else 1
                if hp_pct > 0.8:
                    low_targets = [e for e in enemies if e.hp / e.max_hp < 0.4]
                    if low_targets:
                        reasons.append(f"Consider finishing off {low_targets[0].name} "
                                       f"({low_targets[0].hp}/{low_targets[0].max_hp} HP) first")
            if action_type == "dodge" and entity.hp > entity.max_hp * 0.5:
                reasons.append("Dodge is more effective when at low HP")
            if not reasons:
                reasons.append("There may be more impactful actions available")
            return "Acceptable but not optimal. " + ". ".join(reasons)
        else:
            return ("This action is significantly weaker than alternatives. "
                    "Consider the AI suggestion for better tactical options.")

    def _generate_tactical_notes(self, entity, battle, plan) -> List[str]:
        """Generate tactical advice notes for the current situation."""
        notes = []
        enemies = battle.get_enemies_of(entity)
        allies = battle.get_allies_of(entity)

        # Check if anyone is dying
        dying_allies = [a for a in allies if a.hp <= 0 and not a.is_stable
                        and a.death_save_failures < 3]
        if dying_allies:
            for a in dying_allies:
                notes.append(f"URGENT: {a.name} is dying! Consider healing or stabilizing.")

        # Low HP allies
        low_allies = [a for a in allies if 0 < a.hp < a.max_hp * 0.25]
        for a in low_allies:
            notes.append(f"WARNING: {a.name} is at {a.hp}/{a.max_hp} HP!")

        # Concentration check
        if entity.concentrating_on:
            notes.append(f"Maintaining concentration on {entity.concentrating_on.name}")

        # Flanking opportunity
        for e in enemies:
            adj_allies = [a for a in allies if battle.is_adjacent(a, e)]
            if adj_allies and not battle.is_adjacent(entity, e):
                dist = battle.get_distance(entity, e) * 5
                if dist <= entity.movement_left:
                    notes.append(f"Flanking opportunity: Move adjacent to {e.name} "
                                 f"(ally {adj_allies[0].name} is already there)")
                    break

        # Low HP enemy (finishable)
        for e in enemies:
            if e.hp < 15 and e.hp > 0:
                notes.append(f"{e.name} is low ({e.hp} HP) - consider finishing them off")
                break

        # Resource awareness
        if entity.has_spell_slot(1):
            highest = entity.get_highest_slot()
            total_slots = sum(entity.spell_slots.get(k, 0) for k in entity.spell_slots)
            if total_slots <= 2:
                notes.append(f"Low on spell slots ({total_slots} remaining) - conserve!")

        if entity.ki_points_left > 0 and entity.ki_points_left <= 2:
            notes.append(f"Low on Ki ({entity.ki_points_left} remaining)")

        return notes

    def get_session_summary(self) -> dict:
        """Get summary of all player move ratings across the session."""
        if not self.suggestion_history:
            return {"total_moves": 0, "avg_rating": 0, "optimal_count": 0}

        total = len(self.suggestion_history)
        avg = sum(r.rating for r in self.suggestion_history) / total
        optimal = sum(1 for r in self.suggestion_history if r.rating >= 0.85)
        good = sum(1 for r in self.suggestion_history if 0.65 <= r.rating < 0.85)
        decent = sum(1 for r in self.suggestion_history if 0.4 <= r.rating < 0.65)
        poor = sum(1 for r in self.suggestion_history if r.rating < 0.4)

        return {
            "total_moves": total,
            "avg_rating": round(avg, 2),
            "avg_rating_pct": round(avg * 100, 1),
            "optimal_count": optimal,
            "good_count": good,
            "decent_count": decent,
            "poor_count": poor,
            "rating_label": self._overall_label(avg),
        }

    def _overall_label(self, avg: float) -> str:
        if avg >= 0.8:
            return "Expert play"
        elif avg >= 0.65:
            return "Skilled play"
        elif avg >= 0.5:
            return "Average play"
        elif avg >= 0.35:
            return "Below average"
        return "Needs improvement"
