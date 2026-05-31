import json
import os
import random

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_events():
    path = os.path.join(DATA_DIR, "events.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_available_orders(player):
    events = load_events()
    orders = events.get("orders", [])
    available = []
    for order in orders:
        if order.get("profession") and order["职业"] != player.profession:
            continue
        min_rank = order.get("min_rank_level", 0)
        if player.rank_level < min_rank:
            continue
        available.append(order)
    return available


def complete_order(player, order):
    gold_reward = order.get("éå¸", order.get("gold", 0))
    exp_reward = order.get("ç»éª", order.get("exp", 10))
    rep_reward = order.get("å£°æ", order.get("reputation", 0))

    player.add_gold(gold_reward)
    leveled = player.add_exp(exp_reward)
    player.add_reputation(rep_reward)

    for skill in order.get("grants_skills", []):
        player.add_skill(skill)

    result = {
        "éå¸": gold_reward,
        "ç»éª": exp_reward,
        "å£°æ": rep_reward,
        "leveled": leveled,
        "skills_gained": order.get("grants_skills", []),
    }
    return result


def get_shop_items(player):
    data = load_events()
    items = data.get("shop_items", {})
    profession_items = items.get(player.profession, [])
    general = items.get("general", [])
    return profession_items + general


def buy_item(player, item):
    cost = item.get("cost", 0)
    if player.gold < cost:
        return False, "éå¸ä¸è¶³ã?
    player.add_gold(-cost)
    player.add_item(item\["Ãû³Æ"\])
    for attr, val in item.get("grants", {}).items():
        if hasattr(player, attr):
            current = getattr(player, attr)
            setattr(player, attr, current + val)
    return True, f"è´­ä¹°äº?{item['name']}ï¼?


def random_event(player):
    events = load_events()
    randoms = events.get("random_events", [])
    if not randoms:
        return None
    eligible = [e for e in randoms if not e.get("requires_flag") or player.has_flag(e["需要标志"])]
    if not eligible:
        return None
    return random.choice(eligible)


def get_available_side_quests(player):
    events = load_events()
    quests = events.get("side_quests", [])
    available = []
    for quest in quests:
        # æ£æ¥æ å¿æ¡ä»?        if quest.get("requires_flag") and not player.has_flag(quest["需要标志"]):
            continue
        # æ£æ¥å±æ§æ¡ä»?        if quest.get("æä½æºæ?) and player.wit < quest["æä½æºæ?]:
            continue
        if quest.get("æä½é­å?) and player.charm < quest["æä½é­å?]:
            continue
        if quest.get("æä½æè?) and player.craft < quest["æä½æè?]:
            continue
        if quest.get("æä½ä½å?) and player.grit < quest["æä½ä½å?]:
            continue
        available.append(quest)
    return available


def complete_side_quest(player, quest):
    gold_reward = quest.get("éå¸", quest.get("gold", 0))
    exp_reward = quest.get("ç»éª", quest.get("exp", 10))
    rep_reward = quest.get("å£°æ", quest.get("reputation", 0))

    player.add_gold(gold_reward)
    leveled = player.add_exp(exp_reward)
    player.add_reputation(rep_reward)

    # Grant attribute reward
    attr_reward = quest.get("å±æ§å¥å?, quest.get("attribute_reward"))
    if attr_reward:
        attr_map = {
            "æè?: "craft",
            "ä½å": "grit",
            "æºæ§": "wit",
            "é­å": "charm"
        }
        player_attr = attr_map.get(attr_reward, attr_reward)
        player.add_attribute(player_attr, 1)

    result = {
        "éå¸": gold_reward,
        "ç»éª": exp_reward,
        "å£°æ": rep_reward,
        "leveled": leveled,
        "å±æ§å¥å?: attr_reward,
    }
    return result
