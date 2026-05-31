import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


MAX_ATTRIBUTE = 10
MAX_LEVEL = 15

# DNDé£æ ¼ç»éªè¡?EXP_TABLE = {
    1: 0, 2: 30, 3: 90, 4: 180, 5: 300,
    6: 450, 7: 650, 8: 900, 9: 1200, 10: 1600,
    11: 2100, 12: 2700, 13: 3400, 14: 4200, 15: 5200,
}

# é¶ä½ææå æ
RANK_COMBAT_BONUS = {
    0: {"æ»å»": 0, "æ¤ç²": 0, "æ´å»": 0},    # å­¦å¾
    1: {"æ»å»": 1, "æ¤ç²": 0, "æ´å»": 0},    # å¸®å·¥
    2: {"æ»å»": 1, "æ¤ç²": 1, "æ´å»": 0},    # å äºº
    3: {"æ»å»": 1, "æ¤ç²": 1, "æ´å»": 1},    # å¸å
    4: {"æ»å»": 2, "æ¤ç²": 1, "æ´å»": 1},    # å¤§å¸
    5: {"æ»å»": 2, "æ¤ç²": 2, "æ´å»": 1},    # å®å¸
    6: {"æ»å»": 3, "æ¤ç²": 2, "æ´å»": 2},    # å·¨å 
}


class Player:
    def __init__(self, name="", profession="blacksmith"):
        self.name = name
        self.profession = profession
        self.profession_name = ""
        self.rank = "å­¦å¾"
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
        self.combat_skills = []  # è§£éçæææè½IDåè¡¨

        # Skills (unlocked skill names)
        self.skills = []

        # Inventory
        self.inventory = ["ä¼¦æ¦ä¸åºå°å¾"]

        # Flags for story progression
        self.flags = {}

        # NPC relationships (npc_id -> affinity)
        self.relationships = {}

        # åå§åHP
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
        """éæ°è®¡ç®æå¤§HP"""
        self.max_hp = 8 + self.grit * 2 + self.level
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        elif self.hp == 0:
            self.hp = self.max_hp

    def calc_attack_bonus(self):
        """è®¡ç®æ»å»å å?""
        base = (self.craft + self.grit) // 4
        level_bonus = self.level // 3
        rank_bonus = RANK_COMBAT_BONUS.get(self.rank_level, {}).get("æ»å»", 0)
        return base + level_bonus + rank_bonus

    def calc_damage_bonus(self):
        """è®¡ç®ä¼¤å®³å å?""
        return self.grit // 2

    def calc_ac(self, equipment_ac=0):
        """è®¡ç®æ¤ç²ç­çº§"""
        base = 10 + self.grit // 2
        rank_bonus = RANK_COMBAT_BONUS.get(self.rank_level, {}).get("æ¤ç²", 0)
        return base + rank_bonus + equipment_ac

    def calc_evasion(self):
        """è®¡ç®éªé¿å å?""
        return (self.wit + self.charm) // 4

    def get_crit_threshold(self):
        """è·åæ´å»éå¼ï¼d20éª°å­ç»æ>=æ­¤å¼è§¦åæ´å»ï¼"""
        rank_crit = RANK_COMBAT_BONUS.get(self.rank_level, {}).get("æ´å»", 0)
        if self.level >= 11:
            return max(14, 16 - rank_crit)
        elif self.level >= 6:
            return max(15, 17 - rank_crit)
        else:
            return max(16, 18 - rank_crit)

    def add_exp(self, amount):
        """æ·»å ç»éªï¼è¿ååçº§æ¬¡æ?""
        self.exp += amount
        levels_gained = 0
        while self.level < MAX_LEVEL and self.exp >= EXP_TABLE.get(self.level + 1, 99999):
            self.exp -= EXP_TABLE.get(self.level + 1, 99999)
            self.level += 1
            levels_gained += 1
            self.recalc_hp()
        return levels_gained

    def get_exp_to_next(self):
        """è·åä¸ä¸çº§æéç»éª"""
        if self.level >= MAX_LEVEL:
            return 0
        return EXP_TABLE.get(self.level + 1, 99999) - self.exp

    def has_combat_skill(self, skill_id):
        """æ£æ¥æ¯å¦æ¥ææææè?""
        return skill_id in self.combat_skills

    def add_combat_skill(self, skill_id):
        """è§£éæææè?""
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
        # å¼å®¹æ§å­æ¡£ï¼å¦ææ²¡ælevel/hpå­æ®µååå§å
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
        self.profession_name = prof.get("name", "æªç¥")
        self.rank = prof.get("ranks", ["å­¦å¾"])[0]
        return prof

    def check_endings(self):
        """æ£æ¥ç©å®¶æ»¡è¶³åªäºç»å±æ¡ä»¶"""
        path = os.path.join(DATA_DIR, "endings.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        endings = data.get("endings", {})
        achieved = []
        
        for ending_id, ending in endings.items():
            conditions = ending.get("conditions", {})
            meets = True
            
            # æ£æ¥é¶ä½ç­çº?            if "æä½é¶ä½? in conditions and self.rank_level < conditions["æä½é¶ä½?]:
                meets = False
            if "æé«é¶ä½? in conditions and self.rank_level > conditions["æé«é¶ä½?]:
                meets = False
            
            # æ£æ¥å£°æ?            if "æä½å£°æ? in conditions and self.reputation < conditions["æä½å£°æ?]:
                meets = False
            if "æé«å£°æ? in conditions and self.reputation > conditions["æé«å£°æ?]:
                meets = False
            
            # æ£æ¥éå¸?            if "æä½éå¸? in conditions and self.gold < conditions["æä½éå¸?]:
                meets = False
            if "æé«éå¸? in conditions and self.gold > conditions["æé«éå¸?]:
                meets = False
            
            # æ£æ¥å±æ?            for attr, attr_cn in [("craft", "æè?), ("wit", "æºæ§"), ("charm", "é­å"), ("grit", "ä½å")]:
                if f"æä½{attr_cn}" in conditions and getattr(self, attr, 0) < conditions[f"æä½{attr_cn}"]:
                    meets = False
                if f"æé«{attr_cn}" in conditions and getattr(self, attr, 0) > conditions[f"æé«{attr_cn}"]:
                    meets = False
            
            # æ£æ¥å¿éçæè?            if "å¿éæè? in conditions:
                for skill in conditions["å¿éæè?]:
                    if skill not in self.skills:
                        meets = False
                        break
            
            # æ£æ¥å¿éçæ å¿?            if "å¿éæ å¿" in conditions:
                for flag in conditions["å¿éæ å¿"]:
                    if not self.has_flag(flag):
                        meets = False
                        break
            
            # æ£æ¥å³ç³»æ»å?            if "max_relationship_total" in conditions:
                total_rel = sum(self.relationships.values())
                if total_rel > conditions["最高关系总值"]:
                    meets = False
            
            if meets:
                achieved.append(ending)
        
        return achieved
