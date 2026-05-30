import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


MAX_ATTRIBUTE = 10
MAX_LEVEL = 15

# DND风格经验表
EXP_TABLE = {
    1: 0, 2: 30, 3: 90, 4: 180, 5: 300,
    6: 450, 7: 650, 8: 900, 9: 1200, 10: 1600,
    11: 2100, 12: 2700, 13: 3400, 14: 4200, 15: 5200,
}

# 阶位战斗加成
RANK_COMBAT_BONUS = {
    0: {"attack": 0, "ac": 0, "crit": 0},    # 学徒
    1: {"attack": 1, "ac": 0, "crit": 0},    # 帮工
    2: {"attack": 1, "ac": 1, "crit": 0},    # 匠人
    3: {"attack": 1, "ac": 1, "crit": 1},    # 师傅
    4: {"attack": 2, "ac": 1, "crit": 1},    # 大师
    5: {"attack": 2, "ac": 2, "crit": 1},    # 宗师
    6: {"attack": 3, "ac": 2, "crit": 2},    # 巨匠
}


class Player:
    def __init__(self, name="", profession="blacksmith"):
        self.name = name
        self.profession = profession
        self.profession_name = ""
        self.rank = "学徒"
        self.rank_level = 0

        # Base attributes (1-10)
        self.craft = 1
        self.wit = 1
        self.charm = 1
        self.grit = 1

        # Resources
        self.gold = 10
        self.reputation = 0
        self.exp = 0
        self.level = 1

        # Combat attributes
        self.hp = 0
        self.max_hp = 0
        self.combat_skills = []  # 解锁的战斗技能ID列表

        # Skills (unlocked skill names)
        self.skills = []

        # Inventory
        self.inventory = ["伦敦东区地图"]

        # Flags for story progression
        self.flags = {}

        # NPC relationships (npc_id -> affinity)
        self.relationships = {}

        # 初始化HP
        self.recalc_hp()

    def set_attribute(self, attr, value):
        setattr(self, attr, min(MAX_ATTRIBUTE, max(1, value)))

    def add_attribute(self, attr, value):
        current = getattr(self, attr, 1)
        new_val = min(MAX_ATTRIBUTE, current + value)
        setattr(self, attr, new_val)
        return new_val > current

    @property
    def total_attr(self):
        return self.craft + self.wit + self.charm + self.grit

    def recalc_hp(self):
        """重新计算最大HP"""
        self.max_hp = 8 + self.grit * 2 + self.level
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        elif self.hp == 0:
            self.hp = self.max_hp

    def calc_attack_bonus(self):
        """计算攻击加值"""
        base = (self.craft + self.grit) // 4
        level_bonus = self.level // 3
        rank_bonus = RANK_COMBAT_BONUS.get(self.rank_level, {}).get("attack", 0)
        return base + level_bonus + rank_bonus

    def calc_damage_bonus(self):
        """计算伤害加值"""
        return self.grit // 2

    def calc_ac(self, equipment_ac=0):
        """计算护甲等级"""
        base = 10 + self.grit // 2
        rank_bonus = RANK_COMBAT_BONUS.get(self.rank_level, {}).get("ac", 0)
        return base + rank_bonus + equipment_ac

    def calc_evasion(self):
        """计算闪避加值"""
        return (self.wit + self.charm) // 4

    def get_crit_threshold(self):
        """获取暴击阈值（d20骰子结果>=此值触发暴击）"""
        rank_crit = RANK_COMBAT_BONUS.get(self.rank_level, {}).get("crit", 0)
        if self.level >= 11:
            return max(14, 16 - rank_crit)
        elif self.level >= 6:
            return max(15, 17 - rank_crit)
        else:
            return max(16, 18 - rank_crit)

    def add_exp(self, amount):
        """添加经验，返回升级次数"""
        self.exp += amount
        levels_gained = 0
        while self.level < MAX_LEVEL and self.exp >= EXP_TABLE.get(self.level + 1, 99999):
            self.exp -= EXP_TABLE.get(self.level + 1, 99999)
            self.level += 1
            levels_gained += 1
            self.recalc_hp()
        return levels_gained

    def get_exp_to_next(self):
        """获取下一级所需经验"""
        if self.level >= MAX_LEVEL:
            return 0
        return EXP_TABLE.get(self.level + 1, 99999) - self.exp

    def has_combat_skill(self, skill_id):
        """检查是否拥有战斗技能"""
        return skill_id in self.combat_skills

    def add_combat_skill(self, skill_id):
        """解锁战斗技能"""
        if skill_id not in self.combat_skills:
            self.combat_skills.append(skill_id)
            return True
        return False

    def add_gold(self, amount):
        self.gold = max(0, self.gold + amount)

    def add_reputation(self, amount):
        self.reputation = max(0, self.reputation + amount)

    def add_skill(self, skill_name):
        if skill_name not in self.skills:
            self.skills.append(skill_name)
            return True
        return False

    def has_skill(self, skill_name):
        return skill_name in self.skills

    def has_item(self, item_name):
        return item_name in self.inventory

    def add_item(self, item_name):
        if item_name not in self.inventory:
            self.inventory.append(item_name)
            return True
        return False

    def remove_item(self, item_name):
        if item_name in self.inventory:
            self.inventory.remove(item_name)
            return True
        return False

    def set_flag(self, key, value=True):
        self.flags[key] = value

    def has_flag(self, key):
        return self.flags.get(key, False)

    def get_relationship(self, npc_id):
        return self.relationships.get(npc_id, 0)

    def modify_relationship(self, npc_id, amount):
        current = self.relationships.get(npc_id, 0)
        self.relationships[npc_id] = max(-100, min(100, current + amount))

    def skill_check(self, attribute, difficulty):
        value = getattr(self, attribute, 0)
        return value >= difficulty

    def get_save_data(self):
        return {
            "name": self.name,
            "profession": self.profession,
            "profession_name": self.profession_name,
            "rank": self.rank,
            "rank_level": self.rank_level,
            "craft": self.craft,
            "wit": self.wit,
            "charm": self.charm,
            "grit": self.grit,
            "gold": self.gold,
            "reputation": self.reputation,
            "exp": self.exp,
            "level": self.level,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "combat_skills": self.combat_skills,
            "skills": self.skills,
            "inventory": self.inventory,
            "flags": self.flags,
            "relationships": self.relationships,
        }

    @classmethod
    def from_save_data(cls, data):
        p = cls()
        for key, value in data.items():
            setattr(p, key, value)
        # 兼容旧存档：如果没有level/hp字段则初始化
        if not hasattr(p, 'level') or p.level is None:
            p.level = 1
        if not hasattr(p, 'hp') or p.hp is None:
            p.recalc_hp()
        if not hasattr(p, 'combat_skills') or p.combat_skills is None:
            p.combat_skills = []
        return p

    def load_profession_data(self):
        path = os.path.join(DATA_DIR, "professions.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        prof = data.get(self.profession, {})
        self.profession_name = prof.get("name", "未知")
        self.rank = prof.get("ranks", ["学徒"])[0]
        return prof

    def check_endings(self):
        """检查玩家满足哪些结局条件"""
        path = os.path.join(DATA_DIR, "endings.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        endings = data.get("endings", {})
        achieved = []
        
        for ending_id, ending in endings.items():
            conditions = ending.get("conditions", {})
            meets = True
            
            # 检查阶位等级
            if "min_rank_level" in conditions and self.rank_level < conditions["min_rank_level"]:
                meets = False
            if "max_rank_level" in conditions and self.rank_level > conditions["max_rank_level"]:
                meets = False
            
            # 检查声望
            if "min_reputation" in conditions and self.reputation < conditions["min_reputation"]:
                meets = False
            if "max_reputation" in conditions and self.reputation > conditions["max_reputation"]:
                meets = False
            
            # 检查金币
            if "min_gold" in conditions and self.gold < conditions["min_gold"]:
                meets = False
            if "max_gold" in conditions and self.gold > conditions["max_gold"]:
                meets = False
            
            # 检查属性
            for attr in ["craft", "wit", "charm", "grit"]:
                if f"min_{attr}" in conditions and getattr(self, attr, 0) < conditions[f"min_{attr}"]:
                    meets = False
                if f"max_{attr}" in conditions and getattr(self, attr, 0) > conditions[f"max_{attr}"]:
                    meets = False
            
            # 检查必需的技能
            if "required_skills" in conditions:
                for skill in conditions["required_skills"]:
                    if skill not in self.skills:
                        meets = False
                        break
            
            # 检查必需的标志
            if "required_flags" in conditions:
                for flag in conditions["required_flags"]:
                    if not self.has_flag(flag):
                        meets = False
                        break
            
            # 检查关系总值
            if "max_relationship_total" in conditions:
                total_rel = sum(self.relationships.values())
                if total_rel > conditions["max_relationship_total"]:
                    meets = False
            
            if meets:
                achieved.append(ending)
        
        return achieved
