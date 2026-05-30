import json
import os
import random

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def roll_dice(dice_str):
    """解析并投掷骰子，如 '1d6+2', '2d6', '3d6'"""
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
    """加载敌人数据"""
    path = os.path.join(DATA_DIR, "enemies.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("enemies", {})


def get_random_enemy(location_id, player_level):
    """根据地点和玩家等级获取随机敌人"""
    enemies = load_enemies()
    candidates = []
    for enemy_id, enemy in enemies.items():
        if location_id in enemy.get("locations", []):
            if player_level >= enemy.get("min_player_level", 1):
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
            "name": enemy_data["name"],
            "hp": enemy_data["hp"],
            "max_hp": enemy_data["hp"],
            "ac": enemy_data["ac"],
            "attack_bonus": enemy_data["attack_bonus"],
            "damage": enemy_data["damage"],
            "exp_reward": enemy_data["exp_reward"],
            "gold_reward": enemy_data["gold_reward"],
            "loot": enemy_data.get("loot", []),
            "attack_descriptions": enemy_data.get("attack_descriptions", []),
            "status_effects": {},
        }
        self.turn = 0
        self.log = []
        self.is_player_turn = True
        self.combat_over = False
        self.player_won = False
        self.player_fled = False

        # 检查是否拥有锻造护甲技能（被动AC加成）
        self.equipment_ac = 0
        if player.has_combat_skill("bs_armor"):
            self.equipment_ac += 3

        # 检查机关术（钟表匠被动，战斗开始设置陷阱）
        if player.has_combat_skill("wm_trap"):
            trap_damage = roll_dice("1d8")
            self.enemy["hp"] -= trap_damage
            self.log.append(("你在战场上设置了一个机关陷阱，敌人踩中受到 {0} 点伤害！".format(trap_damage), "skill"))
            if self.enemy["hp"] <= 0:
                self.combat_over = True
                self.player_won = True

    def get_player_ac(self):
        """获取玩家AC，包括被动技能加成"""
        base_ac = self.player.calc_ac(self.equipment_ac)
        # 熔铁之盾：HP低于30%时AC翻倍
        if self.player.has_combat_skill("bs_molten_shield"):
            if self.player.hp <= self.player.max_hp * 0.3:
                base_ac *= 2
        return base_ac

    def calculate_hit(self, attacker_bonus, target_ac, is_player=True):
        """攻击检定：d20 + bonus >= ac"""
        roll = random.randint(1, 20)
        crit_threshold = self.player.get_crit_threshold() if is_player else 18
        is_crit = roll >= crit_threshold
        hit = (roll + attacker_bonus) >= target_ac
        return hit, is_crit, roll

    def calculate_damage(self, base_damage_str, bonus, is_crit, skill_modifier=0):
        """计算伤害"""
        damage = roll_dice(base_damage_str) + bonus + skill_modifier
        if is_crit:
            damage *= 2
        return max(1, damage)

    def get_player_attack_bonus(self):
        """获取玩家攻击加值"""
        return self.player.calc_attack_bonus()

    def get_player_damage_bonus(self):
        """获取玩家伤害加值"""
        return self.player.calc_damage_bonus()

    def player_normal_attack(self):
        """玩家普通攻击"""
        attack_bonus = self.get_player_attack_bonus()
        player_ac = self.get_player_ac()
        hit, is_crit, roll = self.calculate_hit(attack_bonus, self.enemy["ac"])

        if hit:
            damage = self.calculate_damage("1d6", self.get_player_damage_bonus(), is_crit)
            self.enemy["hp"] -= damage
            if is_crit:
                self.log.append(("暴击！骰子{0}，你造成 {1} 点伤害！".format(roll, damage), "crit"))
            else:
                self.log.append(("命中！骰子{0}，你造成 {1} 点伤害。".format(roll, damage), "hit"))
        else:
            self.log.append(("未命中！骰子{0}。".format(roll), "miss"))

        # 闪避步法反击
        if not hit and self.player.has_combat_skill("tl_dodge"):
            if random.random() < 0.5:
                counter_damage = self.calculate_damage("1d4", self.get_player_damage_bonus(), False)
                self.enemy["hp"] -= counter_damage
                self.log.append(("闪避成功！你反击造成 {0} 点伤害！".format(counter_damage), "skill"))

        # 检查敌人是否死亡
        self.check_combat_end()

    def use_skill(self, skill_id):
        """使用战斗技能"""
        from game.combat_skills import get_skill_data, execute_skill
        skill = get_skill_data(self.player.profession, skill_id)
        if not skill:
            self.log.append(("技能未找到！", "system"))
            return

        if skill.get("type") == "passive":
            self.log.append(("{0} 是被动技能，无法主动使用。".format(skill["name"]), "system"))
            return

        success, messages = execute_skill(skill, self.player, self.enemy, self)
        for msg, msg_type in messages:
            self.log.append((msg, msg_type))

    def enemy_turn(self):
        """敌人回合"""
        if self.combat_over:
            return

        # 检查是否被眩晕
        if self.enemy["status_effects"].get("stun", 0) > 0:
            self.enemy["status_effects"]["stun"] -= 1
            self.log.append(("敌人被眩晕，无法行动！", "skill"))
            return

        # 计算敌人攻击力（可能被降低）
        enemy_attack = self.enemy["attack_bonus"]
        if self.enemy["status_effects"].get("attack_reduction", 0):
            enemy_attack -= self.enemy["status_effects"]["attack_reduction"]

        player_ac = self.get_player_ac()
        hit, is_crit, roll = self.calculate_hit(enemy_attack, player_ac, is_player=False)

        # 闪避加值
        evasion = self.player.calc_evasion()
        if random.randint(1, 20) <= evasion * 2:
            if not hit:
                self.log.append(("你闪避了敌人的攻击！", "miss"))
                return

        if hit:
            # 选择攻击描述
            attack_desc = random.choice(self.enemy["attack_descriptions"]) if self.enemy["attack_descriptions"] else "敌人发起攻击！"
            damage = self.calculate_damage(self.enemy["damage"], 0, is_crit)

            # 降低伤害
            if self.enemy["status_effects"].get("damage_reduction", 0):
                damage = int(damage * (1 - self.enemy["status_effects"]["damage_reduction"]))

            self.player.hp -= damage
            if is_crit:
                self.log.append(("{0} 暴击！造成 {1} 点伤害！".format(attack_desc, damage), "crit"))
            else:
                self.log.append(("{0} 造成 {1} 点伤害。".format(attack_desc, damage), "damage"))
        else:
            attack_desc = random.choice(self.enemy["attack_descriptions"]) if self.enemy["attack_descriptions"] else "敌人发起攻击！"
            self.log.append(("{0} 未命中！".format(attack_desc), "miss"))

        # 处理燃烧DOT
        if self.enemy["status_effects"].get("burn_damage", 0):
            burn = self.enemy["status_effects"]["burn_damage"]
            self.enemy["hp"] -= burn
            self.log.append(("敌人受到 {0} 点燃烧伤害！".format(burn), "damage"))
            self.enemy["status_effects"]["burn_turns"] -= 1
            if self.enemy["status_effects"]["burn_turns"] <= 0:
                del self.enemy["status_effects"]["burn_damage"]
                del self.enemy["status_effects"]["burn_turns"]

        # 处理持续效果
        for effect in ["attack_reduction", "ac_reduction"]:
            if self.enemy["status_effects"].get(effect + "_turns", 0) > 0:
                self.enemy["status_effects"][effect + "_turns"] -= 1
                if self.enemy["status_effects"][effect + "_turns"] <= 0:
                    del self.enemy["status_effects"][effect]
                    del self.enemy["status_effects"][effect + "_turns"]

        # 检查玩家死亡
        if self.player.hp <= 0:
            self.player.hp = 0
            self.combat_over = True
            self.player_won = False

    def check_combat_end(self):
        """检查战斗是否结束"""
        if self.enemy["hp"] <= 0:
            self.enemy["hp"] = 0
            self.combat_over = True
            self.player_won = True
        elif self.player.hp <= 0:
            self.player.hp = 0
            self.combat_over = True
            self.player_won = False

    def get_rewards(self):
        """获取战斗奖励"""
        if not self.player_won:
            return None

        rewards = {
            "exp": self.enemy["exp_reward"],
            "gold": self.enemy["gold_reward"],
            "loot": self.enemy["loot"].copy(),
        }

        # 应用奖励
        levels_gained = self.player.add_exp(rewards["exp"])
        self.player.add_gold(rewards["gold"])
        for item in rewards["loot"]:
            self.player.add_item(item)

        rewards["levels_gained"] = levels_gained
        return rewards

    def apply_defeat_penalty(self):
        """应用战败惩罚"""
        gold_lost = self.player.gold // 4
        self.player.add_gold(-gold_lost)
        self.player.hp = max(1, self.player.max_hp // 4)
        return gold_lost

    def try_flee(self):
        """尝试逃跑，50%概率成功"""
        if random.random() < 0.5:
            self.combat_over = True
            self.player_fled = True
            return True
        else:
            self.log.append(("逃跑失败！敌人趁机发起攻击！", "system"))
            self.enemy_turn()
            return False
