import json
import os
import random

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def roll_dice(dice_str):
    """è§£æå¹¶ææ·éª°å­ï¼å¦?'1d6+2', '2d6', '3d6'"""
    if "+" in dice_str:
        parts = dice_str.split("+")
        dice_part = parts[0]
        bonus = int(parts[1])
    else:
        dice_part = dice_str
        bonus = 0

    if "d" in dice_part:
        count, sides = dice_part.split("d")
        count = int(count) if count else 1
        sides = int(sides)
        total = sum(random.randint(1, sides) for _ in range(count))
    else:
        total = int(dice_part)

    return total + bonus


def load_enemies():
    """å è½½æäººæ°æ®"""
    path = os.path.join(DATA_DIR, "enemies.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("enemies", {})


def get_random_enemy(location_id, player_level):
    """æ ¹æ®å°ç¹åç©å®¶ç­çº§è·åéæºæäº?""
    enemies = load_enemies()
    candidates = []
    for enemy_id, enemy in enemies.items():
        if location_id in enemy.get("åºç°å°ç¹", []):
            if player_level >= enemy.get("æä½ç©å®¶ç­çº?, 1):
                candidates.append((enemy_id, enemy))
    if not candidates:
        return None
    enemy_id, enemy_data = random.choice(candidates)
    return enemy_id, enemy_data.copy()


class CombatEngine:
    def __init__(self, player, enemy_data):
        self.player = player
        self.enemy = {
            "id": None,
            "name": enemy_data\["Ãû³Æ"\],
            "hp": enemy_data["çå½å?],
            "max_hp": enemy_data["çå½å?],
            "ac": enemy_data["æ¤ç²"],
            "attack_bonus": enemy_data["æ»å»å å?],
            "damage": enemy_data["ä¼¤å®³"],
            "exp_reward": enemy_data["ç»éªå¥å±"],
            "gold_reward": enemy_data["éå¸å¥å±"],
            "loot": enemy_data.get("æè½ç?, []),
            "attack_descriptions": enemy_data.get("æ»å»æè¿°", []),
            "status_effects": {},
        }
        self.turn = 0
        self.log = []
        self.is_player_turn = True
        self.combat_over = False
        self.player_won = False
        self.player_fled = False

        # æ£æ¥æ¯å¦æ¥æé»é æ¤ç²æè½ï¼è¢«å¨ACå æï¼?        self.equipment_ac = 0
        if player.has_combat_skill("bs_armor"):
            self.equipment_ac += 3

        # æ£æ¥æºå³æ¯ï¼éè¡¨å è¢«å¨ï¼ææå¼å§è®¾ç½®é·é±ï¼
        if player.has_combat_skill("wm_trap"):
            trap_damage = roll_dice("1d8")
            self.enemy["生命值"] -= trap_damage
            self.log.append(("ä½ å¨æåºä¸è®¾ç½®äºä¸ä¸ªæºå³é·é±ï¼æäººè¸©ä¸­åå° {0} ç¹ä¼¤å®³ï¼".format(trap_damage), "skill"))
            if self.enemy["生命值"] <= 0:
                self.combat_over = True
                self.player_won = True

    def get_player_ac(self):
        """è·åç©å®¶ACï¼åæ¬è¢«å¨æè½å æ?""
        base_ac = self.player.calc_ac(self.equipment_ac)
        # çéä¹ç¾ï¼HPä½äº30%æ¶ACç¿»å?        if self.player.has_combat_skill("bs_molten_shield"):
            if self.player.hp <= self.player.max_hp * 0.3:
                base_ac *= 2
        return base_ac

    def calculate_hit(self, attacker_bonus, target_ac, is_player=True):
        """æ»å»æ£å®ï¼d20 + bonus >= ac"""
        roll = random.randint(1, 20)
        crit_threshold = self.player.get_crit_threshold() if is_player else 18
        is_crit = roll >= crit_threshold
        hit = (roll + attacker_bonus) >= target_ac
        return hit, is_crit, roll

    def calculate_damage(self, base_damage_str, bonus, is_crit, skill_modifier=0):
        """è®¡ç®ä¼¤å®³"""
        damage = roll_dice(base_damage_str) + bonus + skill_modifier
        if is_crit:
            damage *= 2
        return max(1, damage)

    def get_player_attack_bonus(self):
        """è·åç©å®¶æ»å»å å?""
        return self.player.calc_attack_bonus()

    def get_player_damage_bonus(self):
        """è·åç©å®¶ä¼¤å®³å å?""
        return self.player.calc_damage_bonus()

    def player_normal_attack(self):
        """ç©å®¶æ®éæ»å?""
        attack_bonus = self.get_player_attack_bonus()
        player_ac = self.get_player_ac()
        hit, is_crit, roll = self.calculate_hit(attack_bonus, self.enemy["护甲"])

        if hit:
            damage = self.calculate_damage("1d6", self.get_player_damage_bonus(), is_crit)
            self.enemy["生命值"] -= damage
            if is_crit:
                self.log.append(("æ´å»ï¼éª°å­{0}ï¼ä½ é æ {1} ç¹ä¼¤å®³ï¼".format(roll, damage), "crit"))
            else:
                self.log.append(("å½ä¸­ï¼éª°å­{0}ï¼ä½ é æ {1} ç¹ä¼¤å®³ã?.format(roll, damage), "hit"))
        else:
            self.log.append(("æªå½ä¸­ï¼éª°å­{0}ã?.format(roll), "miss"))

        # éªé¿æ­¥æ³åå»
        if not hit and self.player.has_combat_skill("tl_dodge"):
            if random.random() < 0.5:
                counter_damage = self.calculate_damage("1d4", self.get_player_damage_bonus(), False)
                self.enemy["生命值"] -= counter_damage
                self.log.append(("éªé¿æåï¼ä½ åå»é æ {0} ç¹ä¼¤å®³ï¼".format(counter_damage), "skill"))

        # æ£æ¥æäººæ¯å¦æ­»äº?        self.check_combat_end()

    def use_skill(self, skill_id):
        """ä½¿ç¨æææè?""
        from game.combat_skills import get_skill_data, execute_skill
        skill = get_skill_data(self.player.profession, skill_id)
        if not skill:
            self.log.append(("æè½æªæ¾å°ï¼?, "system"))
            return

        if skill.get("ç±»å", skill.get("type")) == "passive":
            self.log.append(("{0} æ¯è¢«å¨æè½ï¼æ æ³ä¸»å¨ä½¿ç¨ã?.format(skill\["Ãû³Æ"\]), "system"))
            return

        success, messages = execute_skill(skill, self.player, self.enemy, self)
        for msg, msg_type in messages:
            self.log.append((msg, msg_type))

    def enemy_turn(self):
        """æäººåå"""
        if self.combat_over:
            return

        # æ£æ¥æ¯å¦è¢«ç©æ
        if self.enemy["状态效果"].get("stun", 0) > 0:
            self.enemy["状态效果"]["眩晕"] -= 1
            self.log.append(("æäººè¢«ç©æï¼æ æ³è¡å¨ï¼?, "skill"))
            return

        # è®¡ç®æäººæ»å»åï¼å¯è½è¢«éä½ï¼
        enemy_attack = self.enemy["攻击加值"]
        if self.enemy["状态效果"].get("attack_reduction", 0):
            enemy_attack -= self.enemy["状态效果"]["攻击降低"]

        player_ac = self.get_player_ac()
        hit, is_crit, roll = self.calculate_hit(enemy_attack, player_ac, is_player=False)

        # éªé¿å å?        evasion = self.player.calc_evasion()
        if random.randint(1, 20) <= evasion * 2:
            if not hit:
                self.log.append(("ä½ éªé¿äºæäººçæ»å»ï¼", "miss"))
                return

        if hit:
            # éæ©æ»å»æè¿°
            attack_desc = random.choice(self.enemy["攻击描述"]) if self.enemy["攻击描述"] else "æäººåèµ·æ»å»ï¼?
            damage = self.calculate_damage(self.enemy["伤害"], 0, is_crit)

            # éä½ä¼¤å®³
            if self.enemy["状态效果"].get("damage_reduction", 0):
                damage = int(damage * (1 - self.enemy["状态效果"]["伤害降低"]))

            self.player.hp -= damage
            if is_crit:
                self.log.append(("{0} æ´å»ï¼é æ {1} ç¹ä¼¤å®³ï¼".format(attack_desc, damage), "crit"))
            else:
                self.log.append(("{0} é æ {1} ç¹ä¼¤å®³ã?.format(attack_desc, damage), "damage"))
        else:
            attack_desc = random.choice(self.enemy["攻击描述"]) if self.enemy["攻击描述"] else "æäººåèµ·æ»å»ï¼?
            self.log.append(("{0} æªå½ä¸­ï¼".format(attack_desc), "miss"))

        # å¤ççç§DOT
        if self.enemy["状态效果"].get("burn_damage", 0):
            burn = self.enemy["状态效果"]["燃烧伤害"]
            self.enemy["生命值"] -= burn
            self.log.append(("æäººåå° {0} ç¹çç§ä¼¤å®³ï¼".format(burn), "damage"))
            self.enemy["状态效果"]["燃烧回合"] -= 1
            if self.enemy["状态效果"]["燃烧回合"] <= 0:
                del self.enemy["状态效果"]["燃烧伤害"]
                del self.enemy["状态效果"]["燃烧回合"]

        # å¤çæç»­ææ
        for effect in ["attack_reduction", "ac_reduction"]:
            if self.enemy["状态效果"].get(effect + "_turns", 0) > 0:
                self.enemy["状态效果"][effect + "_turns"] -= 1
                if self.enemy["状态效果"][effect + "_turns"] <= 0:
                    del self.enemy["状态效果"][effect]
                    del self.enemy["状态效果"][effect + "_turns"]

        # æ£æ¥ç©å®¶æ­»äº?        if self.player.hp <= 0:
            self.player.hp = 0
            self.combat_over = True
            self.player_won = False

    def check_combat_end(self):
        """æ£æ¥æææ¯å¦ç»æ?""
        if self.enemy["生命值"] <= 0:
            self.enemy["生命值"] = 0
            self.combat_over = True
            self.player_won = True
        elif self.player.hp <= 0:
            self.player.hp = 0
            self.combat_over = True
            self.player_won = False

    def get_rewards(self):
        """è·åææå¥å±"""
        if not self.player_won:
            return None

        rewards = {
            "ç»éª": self.enemy["经验奖励"],
            "éå¸": self.enemy["金币奖励"],
            "æè½ç?: self.enemy["掉落物"].copy(),
        }

        # åºç¨å¥å±
        levels_gained = self.player.add_exp(rewards["ç»éª"])
        self.player.add_gold(rewards["éå¸"])
        for item in rewards["æè½ç?]:
            self.player.add_item(item)

        rewards["åçº§æ?] = levels_gained
        return rewards

    def apply_defeat_penalty(self):
        """åºç¨æè´¥æ©ç½"""
        gold_lost = self.player.gold // 4
        self.player.add_gold(-gold_lost)
        self.player.hp = max(1, self.player.max_hp // 4)
        return gold_lost

    def try_flee(self):
        """å°è¯éè·ï¼?0%æ¦çæå"""
        if random.random() < 0.5:
            self.combat_over = True
            self.player_fled = True
            return True
        else:
            self.log.append(("éè·å¤±è´¥ï¼æäººè¶æºåèµ·æ»å»ï¼", "system"))
            self.enemy_turn()
            return False
