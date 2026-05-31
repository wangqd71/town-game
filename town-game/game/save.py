import json
import os

SAVE_DIR = os.path.join(os.path.dirname(__file__), "..", "saves")


def ensure_save_dir():
    os.makedirs(SAVE_DIR, exist_ok=True)


def save_game(player, filename="save.json"):
    ensure_save_dir()
    filepath = os.path.join(SAVE_DIR, filename)
    data = {
        "player": player.get_save_data(),
        "current_chapter": getattr(player, "_chapter", 0),
        "current_scene": getattr(player, "_scene", "start"),
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filepath


def load_game(filename="save.json"):
    filepath = os.path.join(SAVE_DIR, filename)
    if not os.path.exists(filepath):
        return None, None, None
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    from game.player import Player
    player = Player.from_save_data(data["玩家"])
    chapter = data.get("current_chapter", 0)
    scene = data.get("current_scene", "start")
    return player, chapter, scene


def save_exists(filename="save.json"):
    filepath = os.path.join(SAVE_DIR, filename)
    return os.path.exists(filepath)


def delete_save(filename="save.json"):
    filepath = os.path.join(SAVE_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False
