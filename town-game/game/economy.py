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
        if order.get("profession") and order["profession"] != player.profession:
            continue
        min_rank = order.get("min_rank_level", 0)
        if player.rank_level < min_rank:
            continue
        available.append(order)
    return available


def complete_order(player, order):
    gold_reward = order.get("gold", 0)
    exp_reward = order.get("exp", 10)
    rep_reward = order.get("reputation", 0)

    player.add_gold(gold_reward)
    leveled = player.add_exp(exp_reward)
    player.add_reputation(rep_reward)

    for skill in order.get("grants_skills", []):
        player.add_skill(skill)

    result = {
        "gold": gold_reward,
        "exp": exp_reward,
        "reputation": rep_reward,
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
        return False, "金币不足。"
    player.add_gold(-cost)
    player.add_item(item["name"])
    for attr, val in item.get("grants", {}).items():
        if hasattr(player, attr):
            current = getattr(player, attr)
            setattr(player, attr, current + val)
    return True, f"购买了 {item['name']}！"


def random_event(player):
    events = load_events()
    randoms = events.get("random_events", [])
    if not randoms:
        return None
    eligible = [e for e in randoms if not e.get("requires_flag") or player.has_flag(e["requires_flag"])]
    if not eligible:
        return None
    return random.choice(eligible)


def get_available_side_quests(player):
    events = load_events()
    quests = events.get("side_quests", [])
    available = []
    for quest in quests:
        # 检查标志条件
        if quest.get("requires_flag") and not player.has_flag(quest["requires_flag"]):
            continue
        # 检查属性条件
        if quest.get("min_wit") and player.wit < quest["min_wit"]:
            continue
        if quest.get("min_charm") and player.charm < quest["min_charm"]:
            continue
        if quest.get("min_craft") and player.craft < quest["min_craft"]:
            continue
        if quest.get("min_grit") and player.grit < quest["min_grit"]:
            continue
        available.append(quest)
    return available


def complete_side_quest(player, quest):
    gold_reward = quest.get("gold", 0)
    exp_reward = quest.get("exp", 10)
    rep_reward = quest.get("reputation", 0)

    player.add_gold(gold_reward)
    leveled = player.add_exp(exp_reward)
    player.add_reputation(rep_reward)

    # Grant attribute reward
    attr_reward = quest.get("attribute_reward")
    if attr_reward:
        player.add_attribute(attr_reward, 1)

    result = {
        "gold": gold_reward,
        "exp": exp_reward,
        "reputation": rep_reward,
        "leveled": leveled,
        "attribute_reward": attr_reward,
    }
    return result
