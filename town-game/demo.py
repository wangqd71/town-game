import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.display import (
    init, clear, print_header, print_separator, print_centered,
    print_narrator, print_dialogue, print_player_thought, print_system,
    print_reward, print_status_bar, color
)
from utils.input import choice_menu, confirm, wait_for_enter, text_input
from game.player import Player
from game.skills import load_professions, try_promote, get_available_skills
from game.economy import get_available_orders, complete_order, get_shop_items, buy_item, random_event
from game.dialogue import run_dialogue, show_skill_event
from game.npc import get_npc, get_available_dialogues, get_location_npcs
from game.world import get_location, get_connections, get_location_description

init()

def demo_mode():
    clear()
    print_header("铁与火之歌 — 演示模式")
    print(color("  本演示将展示游戏的核心玩法", "yellow"))
    print(color("  按 Ctrl+C 退出演示", "dim"))
    print()

    # Create character
    print_narrator("1842年，伦敦东区。你是一个16岁的孤儿，父母在工厂事故中丧生。")
    time.sleep(1)
    print_narrator("一位名叫格雷的老匠人在街角发现了饥寒交迫的你，将你带回了他的工坊。")
    time.sleep(1)
    print_dialogue("格雷师傅", "\"从今天起，你就是我的学徒了。\"他说道。")
    time.sleep(1)

    # Create player
    player = Player("艾伦", "blacksmith")
    player.craft = 3
    player.wit = 2
    player.charm = 1
    player.grit = 2
    player.load_profession_data()

    clear()
    print_header("角色创建完成")
    print(color(f"  姓名: {player.name}", "bold"))
    print(color(f"  职业: {player.profession_name}", "bold"))
    print(color(f"  阶位: {player.rank}", "bold"))
    print()
    print(color(f"  技艺: {player.craft}  智慧: {player.wit}  魅力: {player.charm}  体力: {player.grit}", "cyan"))
    print(color(f"  金币: {player.gold}  声望: {player.reputation}", "yellow"))
    print()
    time.sleep(2)

    # Show workshop
    clear()
    print_header("格雷师傅的工坊")
    loc = get_location("workshop")
    print(color(f"  >> {loc['name']}", "bold", "green"))
    print(color(f"  {loc['description']}", "white"))
    print()
    time.sleep(1)

    # Talk to master
    print_narrator("你走进工坊，格雷师傅正在炉火旁锻造。")
    time.sleep(1)
    print_dialogue("格雷师傅", "孩子，手艺人靠的是手，不是嘴。今天你打算做些什么？", "wise")
    time.sleep(1)

    # Demonstrate skill event
    clear()
    print_header("学习技能")
    print_narrator("你第一次尝试锻造。在格雷师傅的指导下，你颤抖着将烧红的铁块浸入油中。")
    time.sleep(1)
    print_narrator("滋啦一声，青烟升起。你完成了人生中的第一次淬火。")
    time.sleep(1)

    # Add skill and show event
    player.add_skill("铁锤与火钳")
    tree = load_professions()["blacksmith"]["skill_tree"]
    for branch, skills in tree.items():
        for skill in skills:
            if skill["name"] == "铁锤与火钳":
                show_skill_event(skill)
                break
    time.sleep(2)

    # Show orders
    clear()
    print_header("接单工作")
    orders = get_available_orders(player)
    print(color(f"  当前可接订单: {len(orders)}个", "yellow"))
    print()
    for order in orders[:2]:
        print(color(f"  - {order['name']}", "white"))
        print(color(f"    {order['description']}", "dim"))
        print(color(f"    报酬: 金币{order['gold']} 声望{order['reputation']}", "green"))
        print()
    time.sleep(2)

    # Complete an order
    print_narrator("你接下了修理马蹄铁的订单。")
    time.sleep(1)
    print_narrator("你花了两天时间，终于完成了。农夫满意地付了钱。")
    time.sleep(1)

    result = complete_order(player, orders[0])
    print_reward("金币", result["gold"])
    print_reward("经验", result["exp"])
    print_reward("声望", result["reputation"])
    print()

    # Show shop
    clear()
    print_header("市场商店")
    print(color(f"  你的金币: {player.gold}", "yellow"))
    print()
    items = get_shop_items(player)
    for item in items[:3]:
        print(color(f"  - {item['name']} - {item['cost']}金币", "white"))
        print(color(f"    {item['description']}", "dim"))
        print()
    time.sleep(2)

    # Final status
    clear()
    print_header("角色状态")
    print_status_bar(player)

    print(color("  已习得技能:", "cyan"))
    for skill in player.skills:
        print(color(f"    [+] {skill}", "green"))
    print()

    print(color("  演示结束！", "yellow", "bold"))
    print(color("  运行 python main.py 开始完整游戏体验", "dim"))
    print()

if __name__ == "__main__":
    try:
        demo_mode()
    except KeyboardInterrupt:
        print(color("\n\n  演示已退出。", "yellow"))
        sys.exit(0)
