import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_npcs():
    path = os.path.join(DATA_DIR, "npcs.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_npc(npc_id):
    npcs = load_npcs()
    return npcs.get(npc_id)


def get_npc_dialogue(npc_id, dialogue_key="greeting"):
    npc = get_npc(npc_id)
    if not npc:
        return None
    dialogues = npc.get("dialogues", {})
    return dialogues.get(dialogue_key)


def get_available_dialogues(npc_id, player):
    npc = get_npc(npc_id)
    if not npc:
        return []
    dialogues = npc.get("dialogues", {})
    available = []
    for key, node in dialogues.items():
        req = node.get("requires", {})
        if req.get("flag") and not player.has_flag(req["flag"]):
            continue
        if req.get("min_reputation") and player.reputation < req["min_reputation"]:
            continue
        if req.get("profession") and req["profession"] != player.profession:
            continue
        available.append((key, node))
    return available


def get_location_npcs(location_id):
    npcs = load_npcs()
    result = []
    for npc_id, npc in npcs.items():
        if npc.get("location") == location_id:
            result.append((npc_id, npc))
    return result
