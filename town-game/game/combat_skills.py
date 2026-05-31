import json
import os
import random

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_combat_skills_data():
    """å è½½æææè½æ°æ?""
    path = os.path.join(DATA_DIR, "combat_skills.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("combat_skills", {})


def get_all_combat_skills():
    """è·åææèä¸çæææè?""
    return load_combat_skills_data()


def get_profession_skills(profession):
    """è·åæå®èä¸çæææè½åè¡?""
    all_skills = load_combat_skills_data()
    return all_skills.get(profession, [])


def get_skill_data(profession, skill_id):
    """è·åæå®æè½çæ°æ®"""
    skills = get_profession_skills(profession)
    for skill in skills:
        if skill["ID"] == skill_id:
            return skill
    return None


def check_requirements(player, requirements):
    """æ£æ¥ç©å®¶æ¯å¦æ»¡è¶³æè½éæ±?""
    attr_map = {
        "æè?: "craft",
        "ä½å": "grit",
        "æºæ§": "wit",
        "é­å": "charm"
    }
    for attr, value in requirements.items():
        player_attr = attr_map.get(attr, attr)
        if getattr(player, player_attr, 0) < value:
            return False
    return True


def get_available_combat_skills(player):
    """è·åç©å®¶å½åå¯è§£éçæææè?""
    skills = get_profession_skills(player.profession)
    available = []
    for skill in skills:
        if skill["ID"] not in player.combat_skills:
            if check_requirements(player, skill.get("éæ±?, {})):
                available.append(skill)
    return available


def unlock_combat_skill(player, skill_id):
    """è§£éæææè?""
    skill = get_skill_data(player.profession, skill_id)
    if not skill:
        return False, "æè½ä¸å­å¨"

    if skill_id in player.combat_skills:
        return False, "ä½ å·²ç»å­¦ä¼äºè¿ä¸ªæè?

    if not check_requirements(player, skill.get("éæ±?, {})):
        return False, "å±æ§ä¸è¶³ï¼æ æ³å­¦ä¹ "

    player.add_combat_skill(skill_id)
    return True, skill.get("event", "ä½ å­¦ä¼äºæ°æè½ï¼")


def execute_skill(skill, player, enemy, combat_engine):
    """æ§è¡æææè½ææ?""
    effect = skill.get("ææ", {})
    messages = []

    # ç²¾åæå» - å¿å®å½ä¸­
    if effect.get("å¿å®å½ä¸­"):
        damage_formula = effect.get("ä¼¤å®³å¬å¼", "æºæ§*2")
        damage = calculate_formula_damage(damage_formula, player)
        enemy["生命值"] -= damage
        messages.append(("ç²¾åæå»ï¼ä½ é æ {0} ç¹ä¼¤å®³ï¼".format(damage), "skill"))
        return True, messages

    # éé¤çå» - 2d6 + ä½åä¼¤å®³
    if effect.get("ä¼¤å®³") and effect.get("ä¼¤å®³å å¼å±æ?):
        base_damage = roll_dice(effect["ä¼¤å®³"])
        attr_map = {"ä½å": "grit", "æºæ§": "wit", "é­å": "charm", "æè?: "craft"}
        bonus_attr_name = attr_map.get(effect["ä¼¤å®³å å¼å±æ?], effect["ä¼¤å®³å å¼å±æ?])
        bonus_attr = getattr(player, bonus_attr_name, 0)
        bonus = bonus_attr // 2
        damage = base_damage + bonus
        enemy["生命值"] -= damage
        messages.append(("éé¤çå»ï¼é æ {0} ç¹ä¼¤å®³ï¼".format(damage), "crit"))
        return True, messages

    # éå æç« - å¤æ®µæ»å»
    if effect.get("å¤éæ»å»æ¬¡æ°"):
        total_damage = 0
        for i in range(effect["å¤éæ»å»æ¬¡æ°"]):
            base_damage = roll_dice(effect["ä¼¤å®³"])
            attr_map = {"ä½å": "grit", "æºæ§": "wit", "é­å": "charm", "æè?: "craft"}
            bonus_attr_name = attr_map.get(effect.get("ä¼¤å®³å å¼å±æ?, "ä½å"), "grit")
            bonus_attr = getattr(player, bonus_attr_name, 0)
            bonus = bonus_attr // effect.get("ä¼¤å®³å å¼é¤æ?, 1)
            damage = base_damage + bonus
            enemy["生命值"] -= damage
            total_damage += damage
            messages.append(("ç¬¬{0}å»é æ {1} ç¹ä¼¤å®³ï¼".format(i + 1, damage), "hit"))
        messages.append(("éå æç«ï¼å±é æ {0} ç¹ä¼¤å®³ï¼".format(total_damage), "crit"))
        return True, messages

    # ä¸çº¿é·é± - ç©æ+å¢ä¼¤
    if effect.get("ç©æåå"):
        enemy["状态效果"]["眩晕"] = effect["ç©æåå"]
        enemy["状态效果"]["伤害增幅"] = effect.get("ä¼¤å®³å¢å¹", 0)
        messages.append(("ä¸çº¿é·é±ï¼æäººè¢«ç©æ {0} ååï¼åå°ä¼¤å®³å¢å?0%ï¼?.format(effect["ç©æåå"]), "skill"))
        return True, messages

    # åæä¼ªè£ - éä½æäººæ»å»
    if effect.get("æäººæ»å»éä½"):
        duration = effect.get("æç»­åå", 2)
        enemy["状态效果"]["攻击降低"] = effect["æäººæ»å»éä½"]
        enemy["状态效果"]["攻击降低回合"] = duration
        messages.append(("åæä¼ªè£ï¼æäººæ»å»åéä½30%ï¼æç»?{0} ååï¼?.format(duration), "skill"))
        return True, messages

    # å½è¿ç»çº¿ - åè¡+æ æ
    if effect.get("æ²»çé?):
        heal_amount = roll_dice(effect["æ²»çé?])
        attr_map = {"ä½å": "grit", "æºæ§": "wit", "é­å": "charm", "æè?: "craft"}
        heal_attr_name = attr_map.get(effect.get("æ²»çå å¼å±æ?, "é­å"), "charm")
        heal_bonus = getattr(player, heal_attr_name, 0)
        total_heal = heal_amount + heal_bonus
        player.hp = min(player.max_hp, player.hp + total_heal)
        invincible_turns = effect.get("æ æåå", 1)
        player.status_effects = getattr(player, "status_effects", {})
        player.status_effects["无敌"] = invincible_turns
        messages.append(("å½è¿ç»çº¿ï¼åå¤?{0} HPï¼è·å¾?{1} ååæ æï¼?.format(total_heal, invincible_turns), "heal"))
        return True, messages

    # æ¶é´åé?- æäººåéï¼èªå·±é¢å¤è¡å¨
    if effect.get("é¢å¤è¡å¨æ¬¡æ°"):
        enemy["状态效果"]["减速"] = effect.get("æäººåéåå?, 1)
        messages.append(("æ¶é´åéï¼æäººè¡å¨ååï¼ä½ è·å¾é¢å¤è¡å¨æºä¼ï¼?, "skill"))
        # é¢å¤è¡å¨éè¿combat_engineå¤ç
        return True, messages

    # é½¿è½®é£æ´ - æºæ§*3ä¼¤å®³
    if effect.get("ä¼¤å®³å¬å¼") and "æºæ§*3" in effect["ä¼¤å®³å¬å¼"]:
        damage = player.wit * 3
        enemy["生命值"] -= damage
        messages.append(("é½¿è½®é£æ´ï¼éæ¾ææé½¿è½®ï¼é æ {0} ç¹ä¼¤å®³ï¼".format(damage), "crit"))
        return True, messages

    # ç¥è¯è¯å - éä½ææ»é?    if effect.get("æäººæ»å»éä½") and effect.get("æäººæ¤ç²éä½"):
        duration = effect.get("æç»­åå", 3)
        enemy["状态效果"]["攻击降低"] = effect["æäººæ»å»éä½"]
        enemy["状态效果"]["攻击降低回合"] = duration
        enemy["状态效果"]["护甲降低"] = effect["æäººæ¤ç²éä½"]
        enemy["状态效果"]["护甲降低回合"] = duration
        enemy["护甲"] -= effect["æäººæ¤ç²éä½"]
        messages.append(("ç¥è¯è¯åï¼æäººæ»å»åé²å¾¡åéä½?ç¹ï¼æç»­ {0} ååï¼?.format(duration), "skill"))
        return True, messages

    # ç«æ²¹ç?- 3d6ä¼¤å®³+çç§DOT
    if effect.get("æç»­ä¼¤å®³"):
        damage = roll_dice(effect["ä¼¤å®³"])
        enemy["生命值"] -= damage
        dot = effect["æç»­ä¼¤å®³"]
        dot_damage = roll_dice(dot["ä¼¤å®³"])
        enemy["状态效果"]["燃烧伤害"] = dot_damage
        enemy["状态效果"]["燃烧回合"] = dot["æç»­åå"]
        messages.append(("ç«æ²¹ç¶ï¼é æ {0} ç¹ä¼¤å®³ï¼æäººå¼å§çç§ï¼".format(damage), "crit"))
        messages.append(("çç§å°æ¯ååé æ {0} ç¹ä¼¤å®³ï¼æç»­ {1} ååã?.format(dot_damage, dot["æç»­åå"]), "damage"))
        return True, messages

    # é©å½å·è§ - å¨å±æ§å æ?    if effect.get("èªèº«å¢çå±æ?):
        buff = effect["èªèº«å¢çå±æ?]
        duration = effect.get("æç»­åå", 3)
        attr_map = {"æè?: "craft", "ä½å": "grit", "æºæ§": "wit", "é­å": "charm"}
        for attr, value in buff.items():
            player_attr = attr_map.get(attr, attr)
            setattr(player, player_attr + "_buff", value)
        player.status_effects = getattr(player, "status_effects", {})
        player.status_effects["增益"] = buff
        player.status_effects["增益回合"] = duration
        buff_desc = "ã?.join(["{0}+{1}".format(k, v) for k, v in buff.items()])
        messages.append(("é©å½å·è§ï¼{0}ï¼æç»?{1} ååï¼?.format(buff_desc, duration), "skill"))
        return True, messages

    # ççä¹å£° - æºæ§*2+é­å*2ä¼¤å®³ï¼éè·æ¦ç
    if effect.get("éè·æ¦ç"):
        damage = player.wit * 2 + player.charm * 2
        enemy["生命值"] -= damage
        messages.append(("ççä¹å£°ï¼é æ {0} ç¹ä¼¤å®³ï¼".format(damage), "crit"))
        if random.random() < effect["éè·æ¦ç"]:
            enemy["生命值"] = 0
            messages.append(("æäººè¢«çççåééæï¼è½èèéï¼", "skill"))
        return True, messages

    messages.append(("æè½æææªå®ä¹", "system"))
    return False, messages


def calculate_formula_damage(formula, player):
    """è®¡ç®å¬å¼ä¼¤å®³"""
    if "æºæ§*2" in formula and "é­å" not in formula:
        return player.wit * 2
    elif "æºæ§*3" in formula:
        return player.wit * 3
    elif "é­å*2" in formula:
        return player.charm * 2
    elif "æºæ§*2+é­å*2" in formula:
        return player.wit * 2 + player.charm * 2
    return 0


def roll_dice(dice_str):
    """è§£æå¹¶ææ·éª°å­?""
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
