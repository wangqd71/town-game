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
        attr_map = {
            "æè?: "craft",
            "ä½å": "grit",
            "æºæ§": "wit",
            "é­å": "charm"
        }
        attr = attr_map.get(node.get("å±æ?, ""), node.get("å±æ?, node.get("attribute", "craft")))
        difficulty = node.get("é¾åº¦", node.get("difficulty", 5))
        success = player.skill_check(attr, difficulty)
        val = getattr(player, attr, 0)
        skill_check(attr.title(), val, difficulty)

        if success:
            success_node = node.get("æå", node.get("success"))
            if success_node:
                return run_dialogue(success_node, player, npc_name)
        else:
            fail_node = node.get("å¤±è´¥", node.get("fail"))
            if fail_node:
                return run_dialogue(fail_node, player, npc_name)
        return effects

    elif node.get("type") == "effect":
        apply_effects(node.get("ææ", node.get("effects", {})), player)
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
        req = choice.get("requires", choice.get("éæ±?, {}))
        if req.get("flag") and not player.has_flag(req["标志"]):
            continue
        if req.get("min_gold") and player.gold < req["最低金币"]:
            continue
        if req.get("min_reputation") and player.reputation < req["最低声望"]:
            continue
        if req.get("skill") and not player.has_skill(req["技能"]):
            continue
        if req.get("attribute") or req.get("å±æ?):
            attr = req.get("attribute", req.get("å±æ?))
            val = req.get("value", req.get("æ°å?, 5))
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
        for flag in chosen["设置标志"]:
            player.set_flag(flag)

    if chosen.get("effects") or chosen.get("ææ"):
        apply_effects(chosen.get("effects", chosen.get("ææ", {})), player)

    next_node = chosen.get("next")
    if next_node:
        result = run_dialogue(next_node, player, npc_name)
        effects.update(result)

    return effects


def apply_effects(effects, player):
    if "éå¸" in effects:
        player.add_gold(effects["éå¸"])
        if effects["éå¸"] > 0:
            print_reward("éå¸", effects["éå¸"])
        elif effects["éå¸"] < 0:
            from utils.display import print_penalty
            print_penalty("éå¸", abs(effects["éå¸"]))

    if "å£°æ" in effects:
        player.add_reputation(effects["å£°æ"])
        if effects["å£°æ"] > 0:
            print_reward("å£°æ", effects["å£°æ"])

    if "ç»éª" in effects:
        leveled = player.add_exp(effects["ç»éª"])
        print_reward("ç»éª", effects["ç»éª"])
        if leveled:
            print_system("ç­çº§æåï¼?)

    if "å±æ? in effects:
        attr = effects["å±æ?]
        val = effects.get("æ°å?, 1)
        if hasattr(player, attr):
            old_val = getattr(player, attr)
            player.add_attribute(attr, val)
            new_val = getattr(player, attr)
            if new_val > old_val:
                print_reward(attr.title(), val)
            else:
                print_system(f"{attr.title()} å·²è¾¾ä¸éï¼{MAX_ATTRIBUTE}ï¼?)

    if "æè? in effects:
        for skill_name in effects["æè?]:
            if player.add_skill(skill_name):
                print_reward("ä¹ å¾æè?, skill_name)
                # Show skill event if available
                from game.skills import load_professions
                profs = load_professions()
                tree = profs.get(player.profession, {}).get("skill_tree", {})
                for branch, skills in tree.items():
                    for skill in skills:
                        if skill\["Ãû³Æ"\] == skill_name:
                            show_skill_event(skill)
                            break

    if "relationship" in effects:
        for npc_id, val in effects["关系"].items():
            player.modify_relationship(npc_id, val)

    # æææè½è§£é?    if "æææè? in effects:
        from game.combat_skills import unlock_combat_skill
        for skill_id in effects["æææè?]:
            success, msg = unlock_combat_skill(player, skill_id)
            if success:
                print_reward("ä¹ å¾æææè?, msg)

    # è§¦åææï¼æäºè§¦åï¼
    if "è§¦åææ" in effects:
        combat_data = effects["è§¦åææ"]
        enemy_id = combat_data.get("enemy_id")
        if enemy_id:
            from game.combat import load_enemies
            enemies = load_enemies()
            if enemy_id in enemies:
                from utils.input import confirm
                enemy_data = enemies[enemy_id]
                print_system(f"é­éæäºº: {enemy_data['name']}ï¼?)
                if confirm("æ¯å¦è¿æï¼?):
                    # è¿ééè¦è°ç?handle_combatï¼ä½ç±äºå¾ªç¯ä¾èµï¼æä»¬è¿åæææ°æ?                    # ç±è°ç¨èå¤ç?                    return {"trigger_combat": enemy_data}


def show_skill_event(skill_data):
    """æ¾ç¤ºæè½çå·ä½äºä»¶åç©å?""
    if not skill_data:
        return

    print()
    print(color("  âââââââââââââââââââââââââââââââââââââââ?, "cyan"))
    print(color(f"  æè½ä¹ å¾? {skill_data['name']}", "bold", "cyan"))
    print(color("  âââââââââââââââââââââââââââââââââââââââ?, "cyan"))
    print()

    if skill_data.get("event"):
        print(color("  [äºä»¶]", "yellow", "bold"))
        print(color(f"  {skill_data['event']}", "white"))
        print()

    if skill_data.get("item"):
        print(color("  [è·å¾ç©å]", "green", "bold"))
        print(color(f"  {skill_data['item']}", "green"))
        print()

    if skill_data.get("description"):
        print(color("  [æè¿°]", "dim"))
        print(color(f"  {skill_data['description']}", "dim"))
        print()
