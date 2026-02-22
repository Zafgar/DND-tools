import math
import random
from engine.entities import Entity
from data.models import CreatureStats, AbilityScores, Action
from data.library import library
from engine.dice import roll_dice
from data.conditions import CONDITIONS

class BattleSystem:
    def __init__(self, log_callback, initial_entities=None):
        self.grid_size = 60
        self.entities = initial_entities if initial_entities else []
        self.turn_index = 0
        self.log = log_callback
        self.round = 1
        
        # Jos lista on tyhjä, ladataan demo (vain varmuuden vuoksi)
        if not self.entities:
            self._init_demo_entities()
            
        self.start_combat()

    def start_combat(self):
        # Heitetään initiative kaikille
        # HUOM: Oikeassa versiossa kysyisimme tässä pelaajien heitot UI:ssa.
        # Nyt simuloimme pelaajien heitot, jotta koodi toimii suoraan.
        for entity in self.entities:
            roll = entity.roll_initiative()
            
        # Järjestetään suuruusjärjestykseen (korkein ensin)
        self.entities.sort(key=lambda e: e.initiative, reverse=True)
        self.log("Initiative heitetty ja järjestetty.")

    def _init_demo_entities(self):
        # 1. Paladin (Player)
        paladin_stats = CreatureStats(
            name="Hero Paladin",
            hit_points=120,
            armor_class=18,
            speed=30,
            abilities=AbilityScores(strength=18, constitution=16, charisma=14),
            actions=[Action("Longsword", "Melee Weapon Attack", attack_bonus=7, damage_dice="1d8", damage_bonus=4)]
        )
        self.entities.append(Entity(paladin_stats, 5, 5, is_player=True))

        # 2. Wizard (Player)
        wizard_stats = CreatureStats(
            name="Hero Wizard",
            hit_points=60,
            armor_class=12,
            speed=30,
            abilities=AbilityScores(intelligence=20, wisdom=14, dexterity=14),
            actions=[Action("Firebolt", "Ranged Spell Attack", attack_bonus=8, damage_dice="2d10", range=120)]
        )
        self.entities.append(Entity(wizard_stats, 4, 6, is_player=True))

        # 3. Bugbear (Enemy from Library)
        bugbear = library.get_monster("Bugbear")
        self.entities.append(Entity(bugbear, 10, 5, is_player=False))

        # 4. Dire Wolf (Enemy from Library)
        wolf = library.get_monster("Dire Wolf")
        self.entities.append(Entity(wolf, 10, 7, is_player=False))

    def get_current_entity(self):
        return self.entities[self.turn_index]

    def next_turn(self):
        self.turn_index += 1
        if self.turn_index >= len(self.entities):
            self.turn_index = 0
            self.round += 1
            self.log(f"--- ROUND {self.round} ---")
            
        current = self.get_current_entity()
        current.reset_turn() # Nollataan action/bonus action flagit
        self.log(f"Vuoro vaihtui: {current.name}")
        
        # Tarkista statukset ja muistuta DM:ää
        if current.conditions:
            for cond in current.conditions:
                desc = CONDITIONS.get(cond, "")
                self.log(f"[!] STATUS: {cond} - {desc}")
                
        return current

    def update_initiative(self, entity, delta):
        """Päivittää initiativen ja järjestää listan uudelleen säilyttäen vuoron."""
        current = self.get_current_entity()
        entity.initiative += delta
        self.entities.sort(key=lambda e: e.initiative, reverse=True)
        self.turn_index = self.entities.index(current)

    def is_occupied(self, x, y, exclude=None):
        """Tarkistaa onko sijainti varattu (päällekkäisyys)."""
        for entity in self.entities:
            if entity == exclude: continue
            if entity.hp <= 0: continue # Kuolleet eivät blokkaa
            if math.hypot(entity.grid_x - x, entity.grid_y - y) < 0.9:
                return True
        return False

    def _get_distance(self, e1, e2):
        return math.hypot(e1.grid_x - e2.grid_x, e1.grid_y - e2.grid_y)

    def _is_adjacent(self, e1, e2):
        return self._get_distance(e1, e2) < 1.5

    def _get_flanking_position(self, target, allies):
        """Etsii ruudun, joka on kohteen vastakkaisella puolella suhteessa liittolaiseen."""
        for ally in allies:
            if self._is_adjacent(ally, target):
                # Liittolainen on vieressä. Lasketaan vastakkainen ruutu.
                dx = target.grid_x - ally.grid_x
                dy = target.grid_y - ally.grid_y
                flank_x = target.grid_x + dx
                flank_y = target.grid_y + dy
                
                # Tarkistetaan onko ruutu vapaa
                if not self.is_occupied(flank_x, flank_y):
                    return (flank_x, flank_y)
        return None

    def calculate_ai_turn(self, entity):
        """
        Kehittynyt AI:
        1. Tunnistaa liittolaiset ja viholliset.
        2. Pisteyttää kohteet (HP, etäisyys, AC).
        3. Liikkuu taktisesti (Flank > Melee > Range).
        4. Valitse paras toiminto (Multiattack > Action).
        """
        # 0. TARKISTA TILA (Conditions)
        incapacitated_conds = ["Incapacitated", "Paralyzed", "Stunned", "Unconscious", "Petrified"]
        if any(entity.has_condition(c) for c in incapacitated_conds):
            return {"type": "wait", "message": f"{entity.name} is incapacitated and cannot act."}

        # Tarkista onko toiminto jo käytetty
        if entity.action_used:
            return {"type": "done", "message": f"{entity.name} has finished acting."}

        enemies = [e for e in self.entities if e.is_player and e.hp > 0]
        allies = [e for e in self.entities if not e.is_player and e.hp > 0 and e != entity]
        
        if not enemies:
            return {"type": "wait", "message": f"{entity.name} ei löydä kohteita."}

        # --- 1. KOHTEEN VALINTA (Target Selection) ---
        best_target = None
        best_score = -9999

        for enemy in enemies:
            score = 0
            dist = self._get_distance(entity, enemy)
            score -= dist * 2 # Läheisyys on plussaa
            
            # HP: Jos vihollinen on kuolemaisillaan (<40%), se on prioriteetti
            if (enemy.hp / enemy.max_hp) < 0.4: score += 20
            
            # AC: Jos AC on matala, helpompi osua
            score -= (enemy.stats.armor_class - 10)

            if score > best_score:
                best_score = score
                best_target = enemy

        target = best_target
        dist_to_target = self._get_distance(entity, target)
        
        # --- 2. LIIKKUMINEN (Movement Logic) ---
        # Check for speed 0 conditions
        cant_move_conds = ["Grappled", "Restrained"]
        can_move = not any(entity.has_condition(c) for c in cant_move_conds)
        
        actions = entity.stats.actions or [Action("Unarmed", "Melee", 0, "1d4")]
        melee_actions = [a for a in actions if a.range <= 5]
        wants_melee = len(melee_actions) > 0
        
        dest_x, dest_y = entity.grid_x, entity.grid_y
        moved_message = ""
        
        start_pos = (entity.grid_x, entity.grid_y)
        if can_move:
            # Prone logic: Stand up if prone (consumes movement/turn for simplicity)
            if entity.has_condition("Prone"):
                entity.remove_condition("Prone")
                return {"type": "wait", "message": f"{entity.name} stands up from Prone."}

            if wants_melee and dist_to_target > 1.5:
                flank_pos = self._get_flanking_position(target, allies)
                target_x, target_y = flank_pos if flank_pos else (target.grid_x, target.grid_y)
                
                move_speed_squares = entity.stats.speed // 5
                for _ in range(move_speed_squares):
                    curr_dist = math.hypot(target_x - entity.grid_x, target_y - entity.grid_y)
                    if curr_dist <= 0.5: break
                    if self._is_adjacent(entity, target) and not flank_pos: break
                    
                    dx = target_x - entity.grid_x
                    dy = target_y - entity.grid_y
                    
                    next_x, next_y = entity.grid_x, entity.grid_y
                    if abs(dx) > abs(dy):
                        next_x += 1 if dx > 0 else -1
                    elif dy != 0:
                        next_y += 1 if dy > 0 else -1
                    
                    if not self.is_occupied(next_x, next_y, exclude=entity):
                        entity.grid_x, entity.grid_y = next_x, next_y
                
                moved_message = f"{entity.name} liikkuu taktisesti."
        elif any(entity.has_condition(c) for c in cant_move_conds):
            moved_message = f"{entity.name} cannot move (Grappled/Restrained)."
            
        has_moved = (entity.grid_x, entity.grid_y) != start_pos
        if has_moved: entity.movement_left = 0 # Yksinkertaistus: liike kuluttaa kaiken

        # --- 3. TOIMINTO (Action Selection) ---
        dist_to_target = self._get_distance(entity, target)
        possible_actions = [a for a in actions if a.range >= (dist_to_target * 5) - 2]
        
        if not possible_actions:
            if has_moved:
                return {"type": "move", "message": moved_message}
            else:
                return {"type": "wait", "message": f"{entity.name} waits (no valid targets)."}

        # Valitse paras isku (suurin damage dice)
        best_action = max(possible_actions, key=lambda a: int(a.damage_dice.split('d')[0]) * int(a.damage_dice.split('d')[1]) if 'd' in a.damage_dice else 0)
        
        # Advantage / Disadvantage Logic
        has_advantage = False
        has_disadvantage = False
        flank_msg = ""
        
        # Check Poisoned
        if entity.has_condition("Poisoned"):
            has_disadvantage = True
            flank_msg += "(Poisoned Disadv) "
            
        # Check Flanking or Prone Target (Melee only)
        if best_action.range <= 5:
            if any(self._is_adjacent(a, target) for a in allies):
                has_advantage = True
                flank_msg += "(Flank Adv) "
            if target.has_condition("Prone") and self._is_adjacent(entity, target):
                has_advantage = True
                flank_msg += "(Prone Target Adv) "

        # Roll
        r1 = random.randint(1, 20)
        r2 = random.randint(1, 20)
        base_roll = max(r1, r2) if (has_advantage and not has_disadvantage) else min(r1, r2) if (has_disadvantage and not has_advantage) else r1
        
        attack_roll = base_roll + best_action.attack_bonus
            
        damage_string = f"{best_action.damage_dice}"
        if best_action.damage_bonus:
            damage_string += f"+{best_action.damage_bonus}"
            dmg = roll_dice(damage_string)
            
            return {
                "type": "attack",
                "attacker": entity,
                "target": target,
                "action_name": best_action.name,
                "attack_roll": attack_roll,
                "damage": dmg,
                "message": f"{moved_message} {entity.name} hyökkää {flank_msg} ({best_action.name}) -> {target.name}".strip()
            }

    def get_entity_at(self, x, y):
        for entity in self.entities:
            # Käytetään etäisyyttä (0.5 ruutua), koska koordinaatit ovat liukulukuja
            # Korjaus: Lasketaan etäisyys ruudun keskipisteestä (grid_x + 0.5)
            center_x = entity.grid_x + 0.5
            center_y = entity.grid_y + 0.5
            if math.hypot(center_x - x, center_y - y) < 0.5:
                return entity
        return None

    def create_player_attack(self, player, target):
        # Pelaajan hyökkäys. Tässä voitaisiin avata ikkuna, josta valita toiminto.
        # Nyt käytetään yksinkertaisuuden vuoksi ensimmäistä.
        action = player.stats.actions[0] if player.stats.actions else Action("Unarmed", "Melee", 0, "1d4")
        
        # Simuloidaan pelaajan heitto. Oikeassa versiossa tämä syötettäisiin manuaalisesti.
        attack_roll = random.randint(1, 20) + action.attack_bonus
        
        damage_string = f"{action.damage_dice}"
        if action.damage_bonus:
            damage_string += f"+{action.damage_bonus}"
        dmg = roll_dice(damage_string)
        
        return {
            "type": "attack",
            "attacker": player,
            "target": target,
            "action_name": action.name,
            "attack_roll": attack_roll,
            "damage": dmg,
            "message": f"{player.name} hyökkää ({action.name}) -> {target.name}"
        }

    def resolve_attack(self, pending_action, hit_confirmed):
        if not pending_action or pending_action["type"] != "attack":
            return

        target = pending_action["target"]
        
        # Merkitään toiminto käytetyksi
        pending_action["attacker"].action_used = True
        
        if hit_confirmed:
            dmg = pending_action["damage"]
            target.hp -= dmg
            self.log(f"OSUMA! {target.name} ottaa {dmg} vahinkoa.")
            if target.hp <= 0:
                self.log(f"{target.name} kaatui!")
        else:
            self.log(f"OHI! (Tai torjuttu). Ei vahinkoa.")