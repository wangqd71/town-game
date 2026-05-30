import json
import os
import random

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_combat_skills_data():
    """加载战斗技能数据"""
    path = os.path.join(DATA_DIR, "combat_skills.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("combat_skills", {})


def get_all_combat_skills():
    """获取所有职业的战斗技能"""
    return load_combat_skills_data()


def get_profession_skills(profession):
    """获取指定职业的战斗技能列表"""
    all_skills = load_combat_skills_data()
    return all_skills.get(profession, [])


def get_skill_data(profession, skill_id):
    """获取指定技能的数据"""
    skills = get_profession_skills(profession)
    for skill in skills:
        if skill["id"] == skill_id:
            return skill
    return None


def check_requirements(player, requirements):
    """检查玩家是否满足技能需求"""
    for attr, value in requirements.items():
        if getattr(player, attr, 0) < value:
            return False
    return True


def get_available_combat_skills(player):
    """获取玩家当前可解锁的战斗技能"""
    skills = get_profession_skills(player.profession)
    available = []
    for skill in skills:
        if skill["id"] not in player.combat_skills:
            if check_requirements(player, skill.get("requirements", {})):
                available.append(skill)
    return available


def unlock_combat_skill(player, skill_id):
    """解锁战斗技能"""
    skill = get_skill_data(player.profession, skill_id)
    if not skill:
        return False, "技能不存在"

    if skill_id in player.combat_skills:
        return False, "你已经学会了这个技能"

    if not check_requirements(player, skill.get("requirements", {})):
        return False, "属性不足，无法学习"

    player.add_combat_skill(skill_id)
    return True, skill.get("event", "你学会了新技能！")


def execute_skill(skill, player, enemy, combat_engine):
    """执行战斗技能效果"""
    effect = skill.get("effect", {})
    messages = []

    # 精准打击 - 必定命中
    if effect.get("guaranteed_hit"):
        damage_formula = effect.get("damage_formula", "wit*2")
        damage = calculate_formula_damage(damage_formula, player)
        enemy["hp"] -= damage
        messages.append(("精准打击！你造成 {0} 点伤害！".format(damage), "skill"))
        return True, messages

    # 重锤猛击 - 2d6 + grit伤害
    if effect.get("damage") and effect.get("damage_bonus_attr"):
        base_damage = roll_dice(effect["damage"])
        bonus_attr = getattr(player, effect["damage_bonus_attr"], 0)
        bonus = bonus_attr // 2
        damage = base_damage + bonus
        enemy["hp"] -= damage
        messages.append(("重锤猛击！造成 {0} 点伤害！".format(damage), "crit"))
        return True, messages

    # 铁匠怒火 - 多段攻击
    if effect.get("multi_attack"):
        total_damage = 0
        for i in range(effect["multi_attack"]):
            base_damage = roll_dice(effect["damage"])
            bonus_attr = getattr(player, effect.get("damage_bonus_attr", "grit"), 0)
            bonus = bonus_attr // effect.get("damage_bonus_div", 1)
            damage = base_damage + bonus
            enemy["hp"] -= damage
            total_damage += damage
            messages.append(("第{0}击造成 {1} 点伤害！".format(i + 1, damage), "hit"))
        messages.append(("铁匠怒火！共造成 {0} 点伤害！".format(total_damage), "crit"))
        return True, messages

    # 丝线陷阱 - 眩晕+增伤
    if effect.get("stun"):
        enemy["status_effects"]["stun"] = effect["stun"]
        enemy["status_effects"]["damage_amplify"] = effect.get("damage_amplify", 0)
        messages.append(("丝线陷阱！敌人被眩晕 {0} 回合，受到伤害增加50%！".format(effect["stun"]), "skill"))
        return True, messages

    # 华服伪装 - 降低敌人攻击
    if effect.get("enemy_attack_reduction"):
        duration = effect.get("duration", 2)
        enemy["status_effects"]["attack_reduction"] = effect["enemy_attack_reduction"]
        enemy["status_effects"]["attack_reduction_turns"] = duration
        messages.append(("华服伪装！敌人攻击力降低30%，持续 {0} 回合！".format(duration), "skill"))
        return True, messages

    # 命运织线 - 回血+无敌
    if effect.get("heal"):
        heal_amount = roll_dice(effect["heal"])
        heal_bonus = getattr(player, effect.get("heal_bonus_attr", "charm"), 0)
        total_heal = heal_amount + heal_bonus
        player.hp = min(player.max_hp, player.hp + total_heal)
        invincible_turns = effect.get("invincible", 1)
        player.status_effects = getattr(player, "status_effects", {})
        player.status_effects["invincible"] = invincible_turns
        messages.append(("命运织线！回复 {0} HP，获得 {1} 回合无敌！".format(total_heal, invincible_turns), "heal"))
        return True, messages

    # 时间减速 - 敌人减速，自己额外行动
    if effect.get("extra_turns"):
        enemy["status_effects"]["slow"] = effect.get("enemy_slow", 1)
        messages.append(("时间减速！敌人行动减半，你获得额外行动机会！", "skill"))
        # 额外行动通过combat_engine处理
        return True, messages

    # 齿轮风暴 - wit*3伤害
    if effect.get("damage_formula") and "wit*3" in effect["damage_formula"]:
        damage = player.wit * 3
        enemy["hp"] -= damage
        messages.append(("齿轮风暴！释放所有齿轮，造成 {0} 点伤害！".format(damage), "crit"))
        return True, messages

    # 知识诅咒 - 降低敌攻防
    if effect.get("enemy_attack_reduction") and effect.get("enemy_ac_reduction"):
        duration = effect.get("duration", 3)
        enemy["status_effects"]["attack_reduction"] = effect["enemy_attack_reduction"]
        enemy["status_effects"]["attack_reduction_turns"] = duration
        enemy["status_effects"]["ac_reduction"] = effect["enemy_ac_reduction"]
        enemy["status_effects"]["ac_reduction_turns"] = duration
        enemy["ac"] -= effect["enemy_ac_reduction"]
        messages.append(("知识诅咒！敌人攻击和防御各降低2点，持续 {0} 回合！".format(duration), "skill"))
        return True, messages

    # 火油瓶 - 3d6伤害+燃烧DOT
    if effect.get("dot"):
        damage = roll_dice(effect["damage"])
        enemy["hp"] -= damage
        dot = effect["dot"]
        dot_damage = roll_dice(dot["damage"])
        enemy["status_effects"]["burn_damage"] = dot_damage
        enemy["status_effects"]["burn_turns"] = dot["duration"]
        messages.append(("火油瓶！造成 {0} 点伤害，敌人开始燃烧！".format(damage), "crit"))
        messages.append(("燃烧将每回合造成 {0} 点伤害，持续 {1} 回合。".format(dot_damage, dot["duration"]), "damage"))
        return True, messages

    # 革命号角 - 全属性加成
    if effect.get("self_buff"):
        buff = effect["self_buff"]
        duration = effect.get("duration", 3)
        for attr, value in buff.items():
            current = getattr(player, attr, 0)
            setattr(player, attr + "_buff", value)
        player.status_effects = getattr(player, "status_effects", {})
        player.status_effects["buff"] = buff
        player.status_effects["buff_turns"] = duration
        buff_desc = "、".join(["{0}+{1}".format(k, v) for k, v in buff.items()])
        messages.append(("革命号角！{0}，持续 {1} 回合！".format(buff_desc, duration), "skill"))
        return True, messages

    # 真理之声 - wit*2+charm*2伤害，逃跑概率
    if effect.get("flee_chance"):
        damage = player.wit * 2 + player.charm * 2
        enemy["hp"] -= damage
        messages.append(("真理之声！造成 {0} 点伤害！".format(damage), "crit"))
        if random.random() < effect["flee_chance"]:
            enemy["hp"] = 0
            messages.append(("敌人被真理的力量震慑，落荒而逃！", "skill"))
        return True, messages

    messages.append(("技能效果未定义", "system"))
    return False, messages


def calculate_formula_damage(formula, player):
    """计算公式伤害"""
    if "wit*2" in formula:
        return player.wit * 2
    elif "wit*3" in formula:
        return player.wit * 3
    elif "charm*2" in formula:
        return player.charm * 2
    elif "wit*2+charm*2" in formula:
        return player.wit * 2 + player.charm * 2
    return 0


def roll_dice(dice_str):
    """解析并投掷骰子"""
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
