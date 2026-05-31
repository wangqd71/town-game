from utils.display import print_dialogue, print_player_thought, print_system, print_reward, color
from utils.input import choice_menu, skill_check, confirm
from game.player import MAX_ATTRIBUTE


def run_dialogue(node, player, npc_name=""):
    if node is None:
        return {}

    effects = {}

    if node.get("type") == "dialogue":
        speaker = node.get("speaker", npc_name)
        mood = node.get("mood", "neutral")
        text = node.get("text", "")
        print_dialogue(speaker, text, mood)
        choices = node.get("choices", [])
        if choices:
            return handle_choices(choices, player, npc_name)
        next_node = node.get("next")
        if next_node:
            return run_dialogue(next_node, player, npc_name)
        return effects

    elif node.get("type") == "narrator":
        from utils.display import print_narrator
        print_narrator(node.get("text", ""))
        choices = node.get("choices", [])
        if choices:
            return handle_choices(choices, player, npc_name)
        next_node = node.get("next")
        if next_node:
            return run_dialogue(next_node, player, npc_name)
        return effects

    elif node.get("type") == "thought":
        print_player_thought(node.get("text", ""))
        next_node = node.get("next")
        if next_node:
            return run_dialogue(next_node, player, npc_name)
        return effects

    elif node.get("type") == "skill_check":
        attr = node.get("attribute", "craft")
        difficulty = node.get("difficulty", 5)
        success = player.skill_check(attr, difficulty)
        val = getattr(player, attr, 0)
        skill_check(attr.title(), val, difficulty)

        if success:
            success_node = node.get("success")
            if success_node:
                return run_dialogue(success_node, player, npc_name)
        else:
            fail_node = node.get("fail")
            if fail_node:
                return run_dialogue(fail_node, player, npc_name)
        return effects

    elif node.get("type") == "effect":
        apply_effects(node.get("effects", {}), player)
        choices = node.get("choices", [])
        if choices:
            return handle_choices(choices, player, npc_name)
        next_node = node.get("next")
        if next_node:
            return run_dialogue(next_node, player, npc_name)
        return effects

    return effects


def handle_choices(choices, player, npc_name=""):
    filtered = []
    for choice in choices:
        req = choice.get("requires", {})
        if req.get("flag") and not player.has_flag(req["flag"]):
            continue
        if req.get("min_gold") and player.gold < req["min_gold"]:
            continue
        if req.get("min_reputation") and player.reputation < req["min_reputation"]:
            continue
        if req.get("skill") and not player.has_skill(req["skill"]):
            continue
        if req.get("attribute"):
            attr = req["attribute"]
            val = req.get("value", 5)
            if getattr(player, attr, 0) < val:
                continue
        filtered.append(choice)

    if not filtered:
        return {}

    labels = [c.get("text", "...") for c in filtered]
    idx = choice_menu(labels)
    chosen = filtered[idx]

    effects = {}

    if chosen.get("set_flag"):
        for flag in chosen["set_flag"]:
            player.set_flag(flag)

    if chosen.get("effects"):
        apply_effects(chosen["effects"], player)

    next_node = chosen.get("next")
    if next_node:
        result = run_dialogue(next_node, player, npc_name)
        effects.update(result)

    return effects


def apply_effects(effects, player):
    if "gold" in effects:
        player.add_gold(effects["gold"])
        if effects["gold"] > 0:
            print_reward("金币", effects["gold"])
        elif effects["gold"] < 0:
            from utils.display import print_penalty
            print_penalty("金币", abs(effects["gold"]))

    if "reputation" in effects:
        player.add_reputation(effects["reputation"])
        if effects["reputation"] > 0:
            print_reward("声望", effects["reputation"])

    if "exp" in effects:
        leveled = player.add_exp(effects["exp"])
        print_reward("经验", effects["exp"])
        if leveled:
            print_system("等级提升！")

    if "attribute" in effects:
        attr = effects["attribute"]
        val = effects.get("value", 1)
        if hasattr(player, attr):
            old_val = getattr(player, attr)
            player.add_attribute(attr, val)
            new_val = getattr(player, attr)
            if new_val > old_val:
                print_reward(attr.title(), val)
            else:
                print_system(f"{attr.title()} 已达上限（{MAX_ATTRIBUTE}）")

    if "skills" in effects:
        for skill_name in effects["skills"]:
            if player.add_skill(skill_name):
                print_reward("习得技能", skill_name)
                # Show skill event if available
                from game.skills import load_professions
                profs = load_professions()
                tree = profs.get(player.profession, {}).get("skill_tree", {})
                for branch, skills in tree.items():
                    for skill in skills:
                        if skill["name"] == skill_name:
                            show_skill_event(skill)
                            break

    if "relationship" in effects:
        for npc_id, val in effects["relationship"].items():
            player.modify_relationship(npc_id, val)

    # 战斗技能解锁
    if "combat_skills" in effects:
        from game.combat_skills import unlock_combat_skill
        for skill_id in effects["combat_skills"]:
            success, msg = unlock_combat_skill(player, skill_id)
            if success:
                print_reward("习得战斗技能", msg)

    # 触发战斗（故事触发）
    if "trigger_combat" in effects:
        combat_data = effects["trigger_combat"]
        enemy_id = combat_data.get("enemy_id")
        if enemy_id:
            from game.combat import load_enemies
            enemies = load_enemies()
            if enemy_id in enemies:
                from utils.input import confirm
                enemy_data = enemies[enemy_id]
                print_system(f"遭遇敌人: {enemy_data['name']}！")
                if confirm("是否迎战？"):
                    # 这里需要调用 handle_combat，但由于循环依赖，我们返回战斗数据
                    # 由调用者处理
                    return {"trigger_combat": enemy_data}


def show_skill_event(skill_data):
    """显示技能的具体事件和物品"""
    if not skill_data:
        return

    print()
    print(color("  ═══════════════════════════════════════", "cyan"))
    print(color(f"  技能习得: {skill_data['name']}", "bold", "cyan"))
    print(color("  ═══════════════════════════════════════", "cyan"))
    print()

    if skill_data.get("event"):
        print(color("  [事件]", "yellow", "bold"))
        print(color(f"  {skill_data['event']}", "white"))
        print()

    if skill_data.get("item"):
        print(color("  [获得物品]", "green", "bold"))
        print(color(f"  {skill_data['item']}", "green"))
        print()

    if skill_data.get("description"):
        print(color("  [描述]", "dim"))
        print(color(f"  {skill_data['description']}", "dim"))
        print()
