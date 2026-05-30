from utils.display import color


def choice_menu(options, prompt="请选择：", allow_back=False):
    if allow_back:
        options = options + ["[返回]"]

    for i, option in enumerate(options, 1):
        number = color(f"  [{i}]", "cyan", "bold")
        text = color(option, "white") if not option.startswith("[") else color(option, "dim")
        print(f"{number} {text}")
    print()

    while True:
        raw = input(color(f"  {prompt} ", "yellow")).strip()
        if not raw:
            continue
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return idx
        except ValueError:
            pass
        print(color("  请输入有效数字。", "red"))


def confirm(prompt="确认？", yes_text="是", no_text="否"):
    options = [yes_text, no_text]
    for i, opt in enumerate(options, 1):
        print(f"  {color(f'[{i}]', 'cyan')} {color(opt, 'white')}")
    print()

    while True:
        raw = input(color(f"  {prompt} ", "yellow")).strip()
        if raw in ("1", "2"):
            return raw == "1"
        print(color("  请输入 1 或 2。", "red"))


def text_input(prompt="输入：", min_length=1, max_length=20):
    while True:
        raw = input(color(f"  {prompt} ", "yellow")).strip()
        if min_length <= len(raw) <= max_length:
            return raw
        print(color(f"  请输入 {min_length}-{max_length} 个字符。", "red"))


def wait_for_enter(text="按回车继续..."):
    input(color(f"\n  {text}", "dim"))


def skill_check(attribute_name, value, difficulty):
    success = value >= difficulty
    if success:
        print(color(f"  ✓ {attribute_name}判定成功 ({value} >= {difficulty})", "green"))
    else:
        print(color(f"  ✗ {attribute_name}判定失败 ({value} < {difficulty})", "red"))
    return success
