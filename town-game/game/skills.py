import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_professions():
    path = os.path.join(DATA_DIR, "professions.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_rank_info(profession, rank_level):
    data = load_professions()
    prof = data.get(profession, {})
    ranks = prof.get("ranks", ["学徒"])
    if 0 <= rank_level < len(ranks):
        return rank_level, ranks[rank_level]
    return rank_level, ranks[-1]


def get_skill_tree(profession):
    data = load_professions()
    prof = data.get(profession, {})
    return prof.get("skill_tree", {})


def get_available_skills(player):
    tree = get_skill_tree(player.profession)
    available = []
    for branch, skills in tree.items():
        for skill in skills:
            if skill["name"] not in player.skills:
                req = skill.get("requirements", {})
                meets_req = True
                for attr, val in req.items():
                    if getattr(player, attr, 0) < val:
                        meets_req = False
                        break
                if meets_req:
                    available.append((branch, skill))
    return available


def try_promote(player):
    data = load_professions()
    prof = data.get(player.profession, {})
    ranks = prof.get("ranks", [])
    reqs = prof.get("rank_requirements", {})

    next_level = player.rank_level + 1
    if next_level >= len(ranks):
        return False, "你已达最高阶位。"

    req = reqs.get(str(next_level), {})
    for attr, val in req.items():
        if attr == "gold":
            if player.gold < val:
                return False, f"金币不足（需要 {val}，当前 {player.gold}）"
        elif attr == "reputation":
            if player.reputation < val:
                return False, f"声望不足（需要 {val}，当前 {player.reputation}）"
        elif attr == "skills":
            for s in val:
                if s not in player.skills:
                    return False, f"未习得技能：{s}"
        elif hasattr(player, attr):
            if getattr(player, attr) < val:
                return False, f"{attr}不足（需要 {val}，当前 {getattr(player, attr)}）"

    player.rank_level = next_level
    player.rank = ranks[next_level]
    return True, f"恭喜！你晋升为【{ranks[next_level]}】！"
