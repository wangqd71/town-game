import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.display import (
    init, clear, print_header, print_separator, print_centered,
    print_narrator, print_dialogue, print_player_thought, print_system,
    print_reward, print_status_bar, color,
    print_combat_header, print_enemy_status, print_player_combat_status,
    print_combat_log, print_combat_menu
)
from utils.input import choice_menu, confirm, wait_for_enter, text_input
from game.player import Player
from game.skills import load_professions, try_promote, get_available_skills
from game.economy import get_available_orders, complete_order, get_shop_items, buy_item, random_event, get_available_side_quests, complete_side_quest
from game.dialogue import run_dialogue
from game.npc import get_npc, get_available_dialogues, get_location_npcs
from game.world import get_location, get_connections, get_location_description, generate_text_map
from game.save import save_game, load_game, save_exists, delete_save

init()

GAME_TITLE = "铁与火之歌 — 19世纪欧洲手工艺人传奇"


def title_screen():
    clear()
    print()
    print_separator("═", 50, "cyan")
    print_centered("铁与火之歌", 50, "bold", "yellow")
    print_centered("19世纪欧洲手工艺人传奇", 50, "cyan")
    print_separator("═", 50, "cyan")
    print()
    print_centered("在工业革命的浪潮中，做一个坚守手艺的灵魂", 50, "dim")
    print()

    options = ["新的旅程", "继续旅程", "退出游戏"]
    if not save_exists():
        options = ["新的旅程", "退出游戏"]

    idx = choice_menu(options)
    choice = options[idx]

    if choice == "新的旅程":
        return "new"
    elif choice == "继续旅程":
        return "load"
    else:
        return "quit"


def create_character():
    clear()
    print_header("角色创建")

    print_narrator("1842年，伦敦东区。你是一个16岁的孤儿，父母在工厂事故中丧生。")
    wait_for_enter()
    print_narrator("一位名叫格雷的老匠人在街角发现了饥寒交迫的你，将你带回了他的工坊。")
    wait_for_enter()
    print_narrator("\"从今天起，你就是我的学徒了。\"他说道。")
    wait_for_enter()

    name = text_input("为你的角色取一个名字：")

    clear()
    print_header("选择你的职业")
    profs = load_professions()
    prof_keys = list(profs.keys())

    for i, (key, prof) in enumerate(profs.items(), 1):
        print(color(f"  [{i}] {prof['name']}", "bold", "cyan"))
        print(color(f"      {prof['description']}", "dim"))
        print()

    idx = choice_menu([profs[k]["名称"] for k in prof_keys])
    chosen_prof = prof_keys[idx]

    clear()
    print_header("分配属性点")
    print(color("  你有 6 点可以分配到四个属性中。", "yellow"))
    print(color("  每个属性至少1点，最多4点。属性上限为10点。", "dim"))
    print()

    attrs = {"craft": "技艺", "wit": "智慧", "charm": "魅力", "grit": "体力"}
    points = 6
    values = {}

    for attr_key, attr_name in attrs.items():
        remaining = points - sum(values.values())
        # If no points left, assign minimum (1)
        if remaining <= 0:
            values[attr_key] = 1
            continue
        while True:
            remaining = points - sum(values.values())
            print(color(f"  剩余点数: {remaining}", "yellow"))
            max_val = min(4, remaining)
            raw = input(color(f"  {attr_name} (1-{max_val}, 剩余{remaining}点): ", "cyan")).strip()
            try:
                val = int(raw)
                if 1 <= val <= max_val:
                    values[attr_key] = val
                    break
                else:
                    print(color(f"  无效的点数。请输入 1-{max_val}。", "red"))
            except ValueError:
                print(color("  请输入数字。", "red"))
        print()

    player = Player(name, chosen_prof)
    player.craft = values["craft"]
    player.wit = values["wit"]
    player.charm = values["charm"]
    player.grit = values["grit"]
    player.load_profession_data()
    player.recalc_hp()  # 初始化HP

    clear()
    print_header("角色确认")
    print(color(f"  姓名: {player.name}", "bold"))
    print(color(f"  职业: {player.profession_name}", "bold"))
    print(color(f"  阶位: {player.rank}", "bold"))
    print(color(f"  等级: {player.level}  HP: {player.hp}/{player.max_hp}", "green"))
    print()
    print(color(f"  技艺: {player.craft}  智慧: {player.wit}  魅力: {player.charm}  体力: {player.grit}", "cyan"))
    print(color(f"  金币: {player.gold}  声望: {player.reputation}", "yellow"))
    print()

    if not confirm("确认这个角色？"):
        return create_character()

    return player


def show_tutorial():
    clear()
    print_header("新手引导")

    print(color("  欢迎来到《铁与火之歌》！", "bold", "yellow"))
    print(color("  这是一款以19世纪欧洲为背景的文字冒险游戏。", "white"))
    print()

    print(color("  ── 游戏目标 ──", "cyan", "bold"))
    print(color("  你是一名学徒匠人，目标是通过接单工作、学习技能，", "white"))
    print(color("  从「学徒」一路晋升为「巨匠」，开办自己的工坊。", "white"))
    print()

    print(color("  ── 四大属性 ──", "cyan", "bold"))
    print(color("  技艺：完成订单的核心能力，越高越容易成功", "white"))
    print(color("  智慧：学习新技能、触发特殊事件的条件", "white"))
    print(color("  魅力：社交谈判、触发支线任务的关键", "white"))
    print(color("  体力：耐力与健康，影响战斗HP和防御", "white"))
    print()

    print(color("  ── 战斗系统 ──", "red", "bold"))
    print(color("  在城镇中可能遭遇敌人，使用DND风格的回合制战斗", "white"))
    print(color("  HP = 8 + 体力×2 + 等级", "yellow"))
    print(color("  攻击检定：d20 + 攻击加值 ≥ 敌人护甲等级", "yellow"))
    print(color("  暴击：骰子≥18时伤害翻倍", "yellow"))
    print()

    print(color("  ── 前期建议 ──", "yellow", "bold"))
    print(color("  1. 多接单工作：积累金币和经验是成长的基础", "green"))
    print(color("  2. 去市场买材料：提升技艺属性，让接单更容易", "green"))
    print(color("  3. 与NPC对话：获取线索和隐藏任务", "green"))
    print(color("  4. 提升体力：增加HP和防御，在战斗中更持久", "green"))
    print()

    print(color("  ── 晋升之路 ──", "cyan", "bold"))
    print(color("  学徒 → 帮工 → 匠人 → 师傅 → 大师 → 宗师 → 巨匠", "yellow"))
    print(color("  每次晋升需要满足技艺、声望、金币等条件。", "white"))
    print(color("  晋升还会获得战斗加成！", "green"))
    print()

    print(color("  现在，开始你的匠人之旅吧！", "bold", "green"))
    print()

    wait_for_enter()


def game_loop(player, current_location="工坊", chapter=0):
    while True:
        clear()
        print_status_bar(player)

        loc = get_location(current_location)
        if not loc:
            print_system("地点数据加载失败。")
            break

        print(color(f"  📍 {loc['name']}", "bold", "green"))
        print(color(f"  {loc['description']}", "white"))
        print()

        # Show random event chance
        if random.random() < 0.25:
            event = random_event(player)
            if event:
                print(color(f"  ── {event['name']} ──", "yellow", "bold"))
                print(color(f"  {event['text']}", "white"))
                if event.get("effects"):
                    from game.dialogue import apply_effects
                    apply_effects(event["效果"], player)
                print()
                wait_for_enter()

        # 随机战斗遭遇
        encounter_rate = loc.get("encounter_rate", 0.15)
        if random.random() < encounter_rate:
            from game.combat import get_random_enemy
            enemy_result = get_random_enemy(current_location, player.level)
            if enemy_result:
                enemy_id, enemy_data = enemy_result
                print(color(f"  ⚠ 遭遇敌人: {enemy_data['name']}！", "red", "bold"))
                print(color(f"  {enemy_data['description']}", "white"))
                if confirm("是否迎战？"):
                    handle_combat(player, enemy_data)
                else:
                    print_system("你选择了回避。")
                    wait_for_enter()

        # Menu options
        options = []
        actions = []

        # Talk to NPCs
        npcs_here = get_location_npcs(current_location)
        for npc_id, npc in npcs_here:
            options.append(f"与{npc['name']}对话")
            actions.append(("talk", npc_id))

        # Check skills
        options.append("查看技能树")
        actions.append(("skills", None))

        # 战斗技能学习
        from game.combat_skills import get_available_combat_skills
        available_combat = get_available_combat_skills(player)
        if available_combat:
            options.append(f"学习战斗技能 ({len(available_combat)}个可学)")
            actions.append(("learn_combat_skill", available_combat))

        # Do orders
        orders = get_available_orders(player)
        if orders:
            options.append(f"接单工作 ({len(orders)}个订单可选)")
            actions.append(("orders", orders))

        # Side quests
        side_quests = get_available_side_quests(player)
        if side_quests:
            options.append(f"支线任务 ({len(side_quests)}个可接)")
            actions.append(("side_quests", side_quests))

        # Shop
        options.append("逛市场买材料")
        actions.append(("shop", None))

        # 查看地图
        options.append("查看地图")
        actions.append(("map", None))

        # 探索战斗
        if current_location != "工坊":
            options.append("探索寻找敌人")
            actions.append(("explore_combat", None))

        # Move
        connections = get_connections(current_location)
        if connections:
            for conn_id in connections:
                conn_loc = get_location(conn_id)
                if conn_loc:
                    options.append(f"前往 {conn_loc['name']}")
                    actions.append(("move", conn_id))

        # Try promote
        can_promote, msg = try_promote(player)
        if can_promote:
            options.append(f"★ 尝试晋升！")
            actions.append(("promote", None))

        # Help
        options.append("查看帮助")
        actions.append(("help", None))

        # Save/quit
        options.append("查看状态")
        actions.append(("status", None))
        options.append("查看人生结局")
        actions.append(("ending", None))
        options.append("保存并休息")
        actions.append(("save", None))

        idx = choice_menu(options)
        action_type, action_data = actions[idx]

        if action_type == "talk":
            handle_talk(player, action_data)
        elif action_type == "skills":
            handle_skills(player)
        elif action_type == "orders":
            handle_orders(player, action_data)
        elif action_type == "side_quests":
            handle_side_quests(player, action_data)
        elif action_type == "shop":
            handle_shop(player)
        elif action_type == "map":
            handle_map(player, current_location)
        elif action_type == "move":
            # 显示离开当前地点的引导
            old_loc = get_location(current_location)
            if old_loc and old_loc.get("exit_text"):
                print_narrator(old_loc["离开文本"])
                wait_for_enter()
            # 移动到新地点
            current_location = action_data
            # 显示进入新地点的引导
            new_loc = get_location(current_location)
            if new_loc and new_loc.get("enter_text"):
                print_narrator(new_loc["进入文本"])
                wait_for_enter()
        elif action_type == "promote":
            handle_promote(player)
        elif action_type == "help":
            show_tutorial()
        elif action_type == "status":
            handle_status(player)
        elif action_type == "ending":
            handle_ending(player)
        elif action_type == "explore_combat":
            handle_explore_combat(player, current_location)
        elif action_type == "learn_combat_skill":
            handle_learn_combat_skill(player, action_data)
        elif action_type == "save":
            save_game(player)
            print_system("游戏已保存。")
            wait_for_enter()
            if confirm("要退出游戏吗？"):
                print_narrator("愿手艺与你同在。再见！")
                sys.exit(0)


def handle_talk(player, npc_id):
    clear()
    npc = get_npc(npc_id)
    if not npc:
        return

    print_header(f"与{npc['name']}对话")

    available = get_available_dialogues(npc_id, player)
    if not available:
        print_dialogue(npc["名称"], "没什么好说的。", "neutral")
        wait_for_enter()
        return

    labels = []
    for key, node in available:
        label = node.get("text", "...")[:30]
        if node.get("type") == "skill_check":
            label += " [技能判定]"
        labels.append(label)

    idx = choice_menu(labels + ["离开"])
    if idx == len(available):
        return

    dialogue_key, node = available[idx]
    run_dialogue(node, player, npc["名称"])
    wait_for_enter()


def handle_skills(player):
    clear()
    print_header("技能树")

    tree = load_professions()[player.profession]["技能树"]

    for branch_name, skills in tree.items():
        print(color(f"  ── {branch_name} ──", "cyan", "bold"))
        for skill in skills:
            unlocked = skill["名称"] in player.skills
            status = color("✓", "green") if unlocked else color("✗", "dim")
            name_display = color(skill["名称"], "green") if unlocked else color(skill["名称"], "white")
            print(f"    {status} {name_display}")
            if unlocked and skill.get("item"):
                print(color(f"      [物品] {skill['item']}", "green", "dim"))
            else:
                print(color(f"      {skill['description']}", "dim"))
            if not unlocked and skill.get("requirements"):
                reqs = [f"{k}:{v}" for k, v in skill["需求"].items()]
                print(color(f"      需求: {', '.join(reqs)}", "dim"))
        print()

    available = get_available_skills(player)
    if available:
        print(color("  可学习的新技能:", "yellow"))
        for branch, skill in available:
            print(color(f"    ★ [{branch}] {skill['name']}", "yellow"))
            print(color(f"      {skill['description']}", "yellow", "dim"))

    wait_for_enter()


def handle_orders(player, orders):
    clear()
    print_header("接单工作")

    labels = [f"{o['name']} - 金币:{o['gold']} 声望:{o['reputation']}" for o in orders]
    labels.append("算了，不接了")

    idx = choice_menu(labels)
    if idx == len(orders):
        return

    order = orders[idx]
    print_narrator(f"你接下了「{order['name']}」的订单。")

    # Simple skill check
    success = player.skill_check("craft", 3 + player.rank_level * 2)
    val = player.craft
    diff = 3 + player.rank_level * 2
    from utils.input import skill_check as sc
    sc("技艺", val, diff)

    if success:
        result = complete_order(player, order)
        print_reward("金币", result["金币"])
        print_reward("经验", result["经验"])
        if result["声望"] > 0:
            print_reward("声望", result["声望"])
        if result["升级"]:
            print_system("等级提升！")
        # Show skill events for any new skills
        if result.get("skills_gained"):
            tree = load_professions()[player.profession]["技能树"]
            for branch, skills in tree.items():
                for skill in skills:
                    if skill["名称"] in result["获得技能"]:
                        from game.dialogue import show_skill_event
                        show_skill_event(skill)
    else:
        print_system("订单完成得不太好，只得到了基本报酬。")
        player.add_gold(order["金币"] // 3)
        player.add_exp(order["经验"] // 3)

    wait_for_enter()


def handle_side_quests(player, quests):
    clear()
    print_header("支线任务")

    labels = []
    for q in quests:
        reqs = []
        if q.get("min_wit"):
            reqs.append(f"智慧>={q['min_wit']}")
        if q.get("min_charm"):
            reqs.append(f"魅力>={q['min_charm']}")
        if q.get("min_craft"):
            reqs.append(f"技艺>={q['min_craft']}")
        if q.get("min_grit"):
            reqs.append(f"体力>={q['min_grit']}")
        req_str = f" [{','.join(reqs)}]" if reqs else ""
        labels.append(f"{q['name']} - 金币:{q['gold']} 声望:{q['reputation']}{req_str}")
    labels.append("算了，不接了")

    idx = choice_menu(labels)
    if idx == len(quests):
        return

    quest = quests[idx]
    print_narrator(f"你接下了「{quest['name']}」的支线任务。")
    print_narrator(quest['description'])
    wait_for_enter()

    # Complete the side quest
    result = complete_side_quest(player, quest)
    print_reward("金币", result["金币"])
    print_reward("经验", result["经验"])
    if result["声望"] > 0:
        print_reward("声望", result["声望"])
    if result.get("attribute_reward"):
        print_reward(result["属性奖励"].title(), 1)
        print_system(f"你的{result['attribute_reward'].title()}提升了！")
    if result["升级"]:
        print_system("等级提升！")

    wait_for_enter()


def handle_shop(player):
    clear()
    print_header("市场商店")
    print(color(f"  你的金币: {player.gold}", "yellow"))
    print()

    items = get_shop_items(player)
    labels = [f"{item['name']} - {item['cost']}金币 ({item['description']})" for item in items]
    labels.append("离开商店")

    idx = choice_menu(labels)
    if idx == len(items):
        return

    item = items[idx]
    success, msg = buy_item(player, item)
    print_system(msg)
    wait_for_enter()


def handle_map(player, current_location):
    """显示地图"""
    clear()
    print_header("查看地图")
    
    map_text = generate_text_map(current_location)
    print(map_text)
    
    wait_for_enter()


def handle_ending(player):
    """显示结局"""
    clear()
    print_header("人生终章")
    
    endings = player.check_endings()
    
    if not endings:
        # 如果没有满足任何结局条件，显示普通结局
        print(color("  你的人生还在继续……", "white"))
        print()
        print(color("  也许还不到总结的时候。", "dim"))
        print(color("  继续努力，创造属于你的传奇。", "dim"))
        wait_for_enter()
        return
    
    # 显示所有满足的结局
    print(color("  你的人生达到了以下成就：", "yellow"))
    print()
    
    for i, ending in enumerate(endings, 1):
        print(color(f"  [{i}] {ending['name']}", "bold", "cyan"))
        print(color(f"      {ending['description']}", "dim"))
        print()
    
    print(color("  选择一个结局来查看完整故事：", "yellow"))
    
    labels = [ending['name'] for ending in endings]
    labels.append("暂时不看")
    
    idx = choice_menu(labels)
    if idx == len(endings):
        return
    
    # 显示选中的结局
    clear()
    selected = endings[idx]
    print_header(selected['name'])
    
    for line in selected['ending_text']:
        if line:
            print_narrator(line)
            import time
            time.sleep(0.5)
        else:
            print()
    
    print()
    print_separator("═", 50, "yellow")
    print_centered("游戏结束", 50, "bold", "yellow")
    print_separator("═", 50, "yellow")
    
    wait_for_enter()


def check_game_end_conditions(player):
    """检查是否应该结束游戏"""
    # 达到最高阶位且声望足够
    if player.rank_level >= 6 and player.reputation >= 100:
        return True
    # 金币为负且声望过低
    if player.gold <= 0 and player.reputation <= -20:
        return True
    return False


def handle_promote(player):
    clear()
    print_header("晋升考验")

    success, msg = try_promote(player)
    if success:
        from game.skills import load_professions
        profs = load_professions()
        ranks = profs[player.profession]["ranks"]
        print(color(f"  ★ {msg}", "green", "bold"))
        print(color(f"  你现在的阶位: {player.rank}", "cyan"))
    else:
        print(color(f"  ✗ 晋升失败: {msg}", "red"))

    wait_for_enter()


def handle_learn_combat_skill(player, available_skills):
    """学习战斗技能"""
    clear()
    print_header("学习战斗技能")

    labels = [f"{s['name']} - {s['description'][:30]}..." for s in available_skills]
    labels.append("取消")

    idx = choice_menu(labels)
    if idx == len(available_skills):
        return

    skill = available_skills[idx]
    from game.combat_skills import unlock_combat_skill
    success, msg = unlock_combat_skill(player, skill["ID"])

    if success:
        print(color(f"  ★ {msg}", "green", "bold"))
    else:
        print(color(f"  ✗ {msg}", "red"))

    wait_for_enter()


def handle_explore_combat(player, current_location):
    """主动探索寻找敌人"""
    from game.combat import get_random_enemy
    enemy_result = get_random_enemy(current_location, player.level)
    if not enemy_result:
        print_system("这片区域暂时安全，没有发现敌人。")
        wait_for_enter()
        return

    enemy_id, enemy_data = enemy_result
    print(color(f"  你发现了: {enemy_data['name']}！", "red", "bold"))
    print(color(f"  {enemy_data['description']}", "white"))
    if confirm("是否发起攻击？"):
        handle_combat(player, enemy_data)


def handle_combat(player, enemy_data):
    """处理战斗"""
    from game.combat import CombatEngine

    engine = CombatEngine(player, enemy_data)

    while not engine.combat_over:
        clear()
        print_combat_header(engine.enemy["名称"])

        # 显示状态
        print_enemy_status(engine.enemy)
        print_player_combat_status(player)

        # 显示战斗日志
        if engine.log:
            print(color("  ── 战斗日志 ──", "cyan", "bold"))
            for msg, msg_type in engine.log[-5:]:  # 只显示最近5条
                print_combat_log(msg, msg_type)
            print()

        # 玩家回合
        if engine.is_player_turn and not engine.combat_over:
            options = ["普通攻击"]

            # 添加可用技能
            from game.combat_skills import get_skill_data
            for skill_id in player.combat_skills:
                skill = get_skill_data(player.profession, skill_id)
                if skill and skill.get("type") == "active":
                    options.append(skill["名称"])

            options.append("逃跑")

            print_combat_menu(options)
            try:
                choice = int(input(color("  选择行动 (输入数字): ", "cyan")).strip()) - 1
                if choice < 0 or choice >= len(options):
                    print_system("无效选择，请重试。")
                    continue
            except ValueError:
                print_system("请输入数字。")
                continue

            if choice == 0:
                engine.player_normal_attack()
            elif choice == len(options) - 1:
                if engine.try_flee():
                    print_system("你成功逃跑了！")
                    wait_for_enter()
                    return
            else:
                # 使用技能
                skill_id = player.combat_skills[choice - 1]
                engine.use_skill(skill_id)

            engine.check_combat_end()

        # 敌人回合
        if not engine.combat_over and not engine.is_player_turn:
            engine.enemy_turn()
            engine.check_combat_end()

        # 切换回合
        engine.is_player_turn = not engine.is_player_turn
        engine.turn += 1

        if not engine.combat_over:
            wait_for_enter()

    # 战斗结束
    clear()
    print_combat_header(engine.enemy["名称"])

    if engine.player_fled:
        print(color("  你成功逃离了战斗！", "yellow"))
        wait_for_enter()
        return

    if engine.player_won:
        print(color("  ★ 战斗胜利！★", "green", "bold"))
        print()

        rewards = engine.get_rewards()
        print(color("  获得奖励:", "cyan", "bold"))
        print_reward("经验", rewards["经验"])
        print_reward("金币", rewards["金币"])
        if rewards["掉落物"]:
            print(color(f"  掉落物品: {', '.join(rewards['loot'])}", "green"))
        if rewards["升级数"] > 0:
            print(color(f"  ★ 升级了！当前等级: {player.level} ★", "yellow", "bold"))
            print(color(f"  HP已恢复: {player.hp}/{player.max_hp}", "green"))
    else:
        print(color("  ✗ 战斗失败...✗", "red", "bold"))
        gold_lost = engine.apply_defeat_penalty()
        print(color(f"  你失去了 {gold_lost} 金币，被送回了工坊。", "red"))
        print(color(f"  HP恢复至: {player.hp}/{player.max_hp}", "yellow"))

    wait_for_enter()


def handle_status(player):
    clear()
    print_header("角色状态")
    print_status_bar(player)

    # 战斗属性
    print(color("  ── 战斗属性 ──", "red", "bold"))
    print(color(f"  攻击加值: +{player.calc_attack_bonus()}", "yellow"))
    print(color(f"  伤害加值: +{player.calc_damage_bonus()}", "yellow"))
    print(color(f"  护甲等级(AC): {player.calc_ac()}", "yellow"))
    print(color(f"  闪避加值: +{player.calc_evasion()}", "yellow"))
    print(color(f"  暴击阈值: ≥{player.get_crit_threshold()}", "yellow"))
    print()

    # 战斗技能
    print(color("  ── 战斗技能 ──", "cyan", "bold"))
    if player.combat_skills:
        from game.combat_skills import get_skill_data
        for skill_id in player.combat_skills:
            skill = get_skill_data(player.profession, skill_id)
            if skill:
                skill_type = "被动" if skill.get("type") == "passive" else "主动"
                print(color(f"    ✓ [{skill_type}] {skill['name']}", "green"))
                print(color(f"      {skill['description']}", "dim"))
    else:
        print(color("    （无）", "dim"))

    # 可学习的战斗技能
    from game.combat_skills import get_available_combat_skills
    available = get_available_combat_skills(player)
    if available:
        print(color("  可学习的新战斗技能:", "yellow"))
        for skill in available:
            print(color(f"    ★ {skill['name']}", "yellow"))
            print(color(f"      {skill['description']}", "yellow", "dim"))
    print()

    print(color("  已习得技能:", "cyan"))
    if player.skills:
        for skill in player.skills:
            print(color(f"    ✓ {skill}", "green"))
    else:
        print(color("    （无）", "dim"))
    print()

    print(color("  背包:", "cyan"))
    if player.inventory:
        for item in player.inventory:
            print(color(f"    • {item}", "white"))
    else:
        print(color("    （空）", "dim"))
    print()

    print(color("  已解锁的条件:", "cyan"))
    for flag, val in player.flags.items():
        if val:
            print(color(f"    • {flag}", "dim"))
    print()

    wait_for_enter()


def main():
    result = title_screen()

    if result == "quit":
        print_narrator("愿手艺与你同在。再见！")
        sys.exit(0)
    elif result == "load":
        player, chapter, scene = load_game()
        if player is None:
            print_system("存档加载失败。")
            wait_for_enter()
            return main()
        print_system(f"欢迎回来，{player.name}。")
        wait_for_enter()
    else:
        player = create_character()
        chapter = 0
        scene = "工坊"

        # Tutorial
        show_tutorial()

        # Opening narration
        clear()
        print_header("序章：炉火旁的新生活")
        print_narrator("格雷师傅的工坊里，炉火噼啪作响。")
        wait_for_enter()
        print_narrator("你第一次握住锤子，感觉到它的重量。这不仅仅是一块铁——这是你的未来。")
        wait_for_enter()
        print_dialogue("格雷师傅", "从今天起，这里就是你的家。好好学，总有一天你会出师的。", "wise")
        wait_for_enter()
        print_narrator("窗外，工厂的烟囱遮蔽了天空。一个时代正在结束，另一个时代正在开始。")
        wait_for_enter()
        print_narrator("而你，将在这个十字路口，选择自己的道路。")
        wait_for_enter()

    game_loop(player, scene, chapter)


if __name__ == "__main__":
    main()
