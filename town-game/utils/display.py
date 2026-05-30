import os
import sys
import time

# ANSI colors
COLORS = {
    "reset":   "\033[0m",
    "bold":    "\033[1m",
    "dim":     "\033[2m",
    "red":     "\033[31m",
    "green":   "\033[32m",
    "yellow":  "\033[33m",
    "blue":    "\033[34m",
    "magenta": "\033[35m",
    "cyan":    "\033[36m",
    "white":   "\033[37m",
    "bg_black": "\033[40m",
}


def init():
    if os.name == "nt":
        os.system("")


def color(text, *color_names):
    codes = "".join(COLORS.get(c, "") for c in color_names)
    return f"{codes}{text}{COLORS['reset']}"


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def print_centered(text, width=50, *color_names):
    display_text = color(text, *color_names) if color_names else text
    padding = max(0, (width - len(text)) // 2)
    print(" " * padding + display_text)


def print_separator(char="─", width=50, *color_names):
    line = char * width
    print(color(line, *color_names) if color_names else line)


def print_header(title, width=50):
    clear()
    print()
    print_separator("═", width, "cyan")
    print_centered(title, width, "bold", "cyan")
    print_separator("═", width, "cyan")
    print()


def print_narrator(text, pause=0.02):
    print(color("[旁白]", "dim", "cyan"), end=" ")
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(pause)
    print()


def print_dialogue(speaker, text, mood="neutral"):
    mood_colors = {
        "neutral": "white",
        "happy": "green",
        "angry": "red",
        "sad": "blue",
        "wise": "yellow",
        "mysterious": "magenta",
        "serious": "cyan",
    }
    mood_color = mood_colors.get(mood, "white")
    print(color(f"【{speaker}】", "bold", mood_color))
    print(f"  {color('「', 'dim')}{text}{color('」', 'dim')}")
    print()


def print_player_thought(text):
    print(color("[内心]", "dim", "yellow"), end=" ")
    print(color(text, "yellow"))
    print()


def print_system(text):
    print(color(f"  ▸ {text}", "dim"))
    print()


def print_reward(text, amount):
    print(color(f"  ★ {text} +{amount}", "green", "bold"))


def print_penalty(text, amount):
    print(color(f"  ✗ {text} -{amount}", "red"))


def print_status_bar(player):
    bar_width = 50
    exp_to_next = player.get_exp_to_next()
    exp_bar_width = 20
    exp_progress = int((player.exp / max(1, player.get_exp_to_next() + player.exp)) * exp_bar_width) if player.level < 15 else exp_bar_width
    exp_bar = "#" * exp_progress + "-" * (exp_bar_width - exp_progress)

    # HP bar
    hp_bar_width = 15
    hp_progress = int((player.hp / max(1, player.max_hp)) * hp_bar_width)
    hp_bar = "█" * hp_progress + "░" * (hp_bar_width - hp_progress)

    print_separator("─", bar_width)
    print(color(f"  {player.name}  |  {player.profession_name}  |  {player.rank}  |  Lv.{player.level}", "bold"))
    print(color(f"  HP: [{hp_bar}] {player.hp}/{player.max_hp}", "red"))
    print(color(f"  金币: {player.gold}  |  声望: {player.reputation}", "yellow"))

    # Format attributes with max indicator
    def fmt_attr(name, val, max_val=10):
        indicator = "*" if val >= max_val else ""
        return f"{name}:{val}{indicator}"

    print(color(f"  {fmt_attr('技艺', player.craft)}  {fmt_attr('智慧', player.wit)}  {fmt_attr('魅力', player.charm)}  {fmt_attr('体力', player.grit)}", "cyan"))

    if player.level < 15:
        print(color(f"  经验: [{exp_bar}] {player.exp}/{player.get_exp_to_next()} (升级)", "green"))
    else:
        print(color(f"  经验: [{exp_bar}] {player.exp} (MAX)", "green"))
    print_separator("─", bar_width)
    print()


def print_combat_header(enemy_name):
    print()
    print_separator("═", 50, "red")
    print_centered("⚔ 战斗开始 ⚔", 50, "bold", "red")
    print_separator("═", 50, "red")
    print(color(f"  敌人: {enemy_name}", "bold", "red"))
    print()


def print_enemy_status(enemy):
    hp_bar_width = 20
    hp_progress = int((enemy["hp"] / max(1, enemy["max_hp"])) * hp_bar_width)
    hp_bar = "█" * hp_progress + "░" * (hp_bar_width - hp_progress)
    print(color(f"  {enemy['name']}: [{hp_bar}] {enemy['hp']}/{enemy['max_hp']} HP", "red"))
    print(color(f"  护甲等级(AC): {enemy['ac']}", "yellow"))
    print()


def print_player_combat_status(player):
    hp_bar_width = 20
    hp_progress = int((player.hp / max(1, player.max_hp)) * hp_bar_width)
    hp_bar = "█" * hp_progress + "░" * (hp_bar_width - hp_progress)
    print(color(f"  你: [{hp_bar}] {player.hp}/{player.max_hp} HP", "green"))
    print(color(f"  攻击加值: +{player.calc_attack_bonus()}  |  AC: {player.calc_ac()}", "cyan"))
    print()


def print_combat_log(text, log_type="normal"):
    type_colors = {
        "normal": "white",
        "hit": "green",
        "miss": "yellow",
        "crit": "red",
        "damage": "red",
        "heal": "green",
        "skill": "cyan",
        "system": "dim",
    }
    color_name = type_colors.get(log_type, "white")
    print(color(f"  ▸ {text}", color_name))


def print_combat_menu(options):
    print(color("  ── 选择行动 ──", "cyan", "bold"))
    for i, opt in enumerate(options, 1):
        print(color(f"  [{i}] {opt}", "white"))
    print()
