import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_locations():
    path = os.path.join(DATA_DIR, "locations.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_location(location_id):
    locs = load_locations()
    return locs.get(location_id)


def get_connections(location_id):
    loc = get_location(location_id)
    if not loc:
        return []
    return loc.get("连接", [])


def get_location_description(location_id, player):
    loc = get_location(location_id)
    if not loc:
        return "未知地点。"
    desc = loc.get("描述", "")
    for flag, alt_desc in loc.get("flag_descriptions", {}).items():
        if player.has_flag(flag):
            desc = alt_desc
    return desc


def generate_text_map(current_location):
    """生成文字地图"""
    locs = load_locations()
    
    # 地点位置映射 (用于文字地图布局)
    location_positions = {
        "cathedral": (0, 0),
        "noble_district": (1, 0),
        "factory_district": (0, 1),
        "market": (1, 1),
        "workshop": (0, 2),
        "tavern": (1, 2),
    }
    
    # 地点简称
    short_names = {
        "cathedral": "大教堂",
        "noble_district": "贵族区",
        "factory_district": "工厂区",
        "market": "市  场",
        "workshop": "工  坊",
        "tavern": "酒  馆",
    }
    
    map_lines = []
    map_lines.append("  ┌─────────────────────────────────────┐")
    map_lines.append("  │         伦 敦 东 区 地 图           │")
    map_lines.append("  ├─────────────────────────────────────┤")
    map_lines.append("  │                                     │")
    map_lines.append("  │    [大教堂]─────[贵族区]            │")
    map_lines.append("  │        │           │                │")
    map_lines.append("  │        │           │                │")
    map_lines.append("  │    [工厂区]─────[市  场]            │")
    map_lines.append("  │        │           │                │")
    map_lines.append("  │        │           │                │")
    map_lines.append("  │    [工  坊]─────[酒  馆]            │")
    map_lines.append("  │                                     │")
    map_lines.append("  └─────────────────────────────────────┘")
    map_lines.append("")
    map_lines.append("  你现在的位置: " + locs.get(current_location, {}).get("名称", "未知"))
    map_lines.append("")
    map_lines.append("  ── 地点说明 ──")
    
    for loc_id, loc_data in locs.items():
        marker = "★" if loc_id == current_location else " "
        name = loc_data.get("名称", loc_id)
        map_lines.append(f"  {marker} {name}")
    
    return "\n".join(map_lines)
