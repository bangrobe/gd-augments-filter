#!/usr/bin/env python3
"""Build grimdawn_augments.db v3 — Bleeding damage type + player-friendly VI labels."""
import json, sqlite3, os, re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
parsed = json.load(open(os.path.join(HERE, "augments_parsed.json"), encoding="utf-8"))

CLS_SLOT = {
    "c10": ("Weapon", "1H Melee"), "c11": ("Weapon", "1H Ranged"), "c12": ("Weapon", "2H Melee"),
    "c13": ("Weapon", "2H Ranged"), "c14": ("Weapon", "Caster"), "c15": ("Weapon", "Shield"),
    "c16": ("Weapon", "Offhand"),
    "c20": ("Armor", "Head"), "c21": ("Armor", "Shoulders"), "c22": ("Armor", "Chest"),
    "c23": ("Armor", "Hands"), "c24": ("Armor", "Legs"), "c25": ("Armor", "Feet"),
    "c26": ("Armor", "Waist"), "c27": ("Armor", "Any Armor"),
    "c28": ("Jewelry", "Ring"), "c29": ("Jewelry", "Ring"), "c30": ("Jewelry", "Amulet"),
    "c31": ("Jewelry", "Medal"), "c32": ("Jewelry", "Any Jewelry"), "c40": ("Jewelry", "Medal"),
    "c41": ("Jewelry", "Amulet"), "c42": ("Relic", "Relic"), "c43": ("Relic", "Relic"),
}
EXP_NAME = {"gdx1": "Ashes of Malmouth", "gdx2": "Forgotten Gods", "gdx3": "Fangs of Asterkarn"}
FACTION = {
    "f1": "Devil's Crossing", "f2": "Kymon's Chosen", "f3": "The Outcast", "f4": "House of Valor",
    "f5": "The Order of Death's Vigil", "f6": "The Circle of Cunning", "f7": "The Beastmaster's Treasure",
    "f8": "The Coven of Ugdenbog", "f9": "The Black Legion", "f10": "The Scholars of Luminerr",
    "f11": "The Sentinels of Stone", "f12": "The Eternal Band", "f13": "The Bodukon's Wrath",
    "f14": "The Shrine of the Dread", "f15": "The Faction of Asterkarn",
}
REP_TIER = {"tagFactionStateFriend1": "Friendly I", "tagFactionStateFriend4": "Friendly IV",
            "tagFactionStateFriend5": "Friendly V"}

# damage-type classification (includes Bleeding)
DMG = {"Physical": "offensivePhysical", "Fire": "offensiveFire", "Cold": "offensiveCold",
       "Lightning": "offensiveLightning", "Poison": "offensivePoison", "Aether": "offensiveAether",
       "Chaos": "offensiveChaos", "Pierce": "offensivePierce", "Vitality": "offensiveLife",
       "Elemental": "offensiveElemental", "Bleeding": "offensiveBleeding"}
RES = {"Physical": "defensivePhysical", "Fire": "defensiveFire", "Cold": "defensiveCold",
       "Lightning": "defensiveLightning", "Poison": "defensivePoison", "Aether": "defensiveAether",
       "Chaos": "defensiveChaos", "Pierce": "defensivePierce", "Vitality": "defensiveLife",
       "Elemental": "defensiveElemental", "Bleeding": "defensiveBleeding"}
RET = {"Physical": "retaliationPhysical", "Fire": "retaliationFire", "Cold": "retaliationCold",
       "Lightning": "retaliationLightning", "Poison": "retaliationPoison", "Aether": "retaliationAether",
       "Chaos": "retaliationChaos", "Vitality": "retaliationLife", "Bleeding": "retaliationBleeding"}
DT = {"Physical": "Vật lý", "Fire": "Lửa", "Cold": "Băng", "Lightning": "Sét", "Poison": "Độc",
      "Aether": "Aether", "Chaos": "Hỗn mang", "Pierce": "Xuyên giáp", "Vitality": "Sinh lực",
      "Elemental": "Nguyên tố", "Bleeding": "Chảy máu"}

def detect_dt(key):
    for t, pat in DMG.items():
        if key.startswith(pat) or key == "offensiveBase" + t + "Max":
            return t
    for t, pat in RES.items():
        if key.startswith(pat):
            return t
    for t, pat in RET.items():
        if key.startswith(pat):
            return t
    return None

def classify(key):
    dt = detect_dt(key)
    if dt is None:
        return None
    if "Slow" in key:
        # làm chậm/suy yếu damage type của địch -> coi như hướng kháng (offensive-side)
        return ("resist", dt)
    if key.startswith("offensive") or key == "offensiveBase" + dt + "Max":
        return ("damage", dt)
    if key.startswith("defensive"):
        return ("resist", dt)
    if key.startswith("retaliation"):
        return ("retaliation", dt)
    return None

def fmt_val(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    if f.is_integer():
        return str(int(f))
    return f"{f:.1f}"

def humanize(key, val):
    """Player-friendly Vietnamese label for a stat key + value."""
    v = fmt_val(val)
    sign = "+" if (isinstance(val, (int, float)) and val >= 0) else ""
    dt = detect_dt(key)
    dtvi = DT.get(dt, dt) if dt else ""
    # OFFENSIVE
    if key.startswith("offensive"):
        if "Slow" in key:
            # damage type = word after "Slow" (e.g. offensiveSlowPhysicalModifier -> Physical)
            rest = key.replace("Slow", "")
            slow_dt = dt or detect_dt(rest)
            slow_vi = DT.get(slow_dt, slow_dt) if slow_dt else ""
            if key.endswith("Modifier"):
                return f"Làm chậm {sign}{v}% tốc độ {slow_vi} của địch".replace("  ", " ")
            if "Duration" in key:
                return f"Làm chậm tốc độ {slow_vi} của địch: {sign}{v} giây"
            return f"Làm chậm tốc độ {slow_vi} của địch ({sign}{v})"
        if "ResistanceReduction" in key:
            return f"Giảm {sign}{v}% kháng {dtvi} của địch"
        if "TotalDamageModifier" in key:
            return f"Tăng {sign}{v}% tổng sát thương"
        if "Confusion" in key:
            return f"{sign}{v}% cơ hội gây Bối rối" if "Chance" in key else f"Gây Bối rối {sign}{v}"
        if "Freeze" in key:
            return f"{sign}{v}% cơ hội làm Đóng băng" if "Chance" in key else f"Làm Đóng băng {sign}{v}"
        if "Stun" in key:
            return f"{sign}{v}% cơ hội làm Choáng" if "Chance" in key else f"Làm Choáng {sign}{v}"
        if dt:
            if key.endswith("Modifier"):
                return f"Tăng {sign}{v}% sát thương {dtvi}"
            if key.endswith("Min"):
                return f"{sign}{v} sát thương {dtvi} (flat)"
            if key.endswith("Max"):
                return f"{sign}{v} sát thương {dtvi} tối đa"
            if "Base" in key:
                return f"{sign}{v} sát thương {dtvi} cơ bản"
        return key
    # DEFENSIVE
    if key.startswith("defensive"):
        if "Block" in key:
            if "Chance" in key:
                return f"{sign}{v}% tỉ lệ Block"
            if "Amount" in key:
                return f"{sign}{v}% lượng Block"
            if "Recovery" in key:
                return f"Phục hồi Block {sign}{v}"
            return f"Block {sign}{v}%"
        if "Protection" in key:
            return f"Tăng {sign}{v}% Giáp" if key.endswith("Modifier") else f"{sign}{v} Giáp"
        if "Absorption" in key:
            return f"Tăng {sign}{v}% Hấp thụ"
        if "BonusProtection" in key:
            return f"{sign}{v} Giáp cộng thêm"
        if "Petrify" in key:
            return f"{sign}{v} Kháng Hóa đá"
        if "Trap" in key:
            return f"{sign}{v} Kháng Bẫy"
        if "Stun" in key:
            return f"{sign}{v} Kháng Choáng"
        if "Freeze" in key:
            return f"{sign}{v} Kháng Đóng băng"
        if "Bleeding" in key:
            return f"{sign}{v} Kháng Chảy máu"
        if "TotalSpeedResistance" in key:
            return f"{sign}{v}% Kháng làm chậm"
        if "PercentReflectionResistance" in key:
            return f"{sign}{v}% Kháng Phản chiếu"
        if "SlowLifeLeach" in key:
            return f"{sign}{v} Hút máu khi chậm"
        if dt:
            if key.endswith("MaxResist"):
                return f"{sign}{v} kháng tối đa {dtvi}"
            return f"{sign}{v} kháng {dtvi}"
        return key
    # CHARACTER
    if key.startswith("character"):
        if "OffensiveAbility" in key:
            return f"{sign}{v} Điểm Tấn công (OA)" if key.endswith("Modifier") else f"{sign}{v} OA"
        if "DefensiveAbility" in key:
            return f"{sign}{v} Điểm Phòng thủ (DA)" if key.endswith("Modifier") else f"{sign}{v} DA"
        if "Life" in key:
            if "Regen" in key:
                return f"Hồi {sign}{v} máu/giây" if "Modifier" in key else f"Hồi sinh {sign}{v}"
            return f"Tăng {sign}{v}% Máu" if key.endswith("Modifier") else f"{sign}{v} Máu"
        if "Mana" in key:
            if "Regen" in key:
                return f"Hồi {sign}{v} mana/giây"
            return f"Tăng {sign}{v}% Mana" if key.endswith("Modifier") else f"{sign}{v} Mana"
        if "RunSpeed" in key:
            return f"Tăng {sign}{v}% tốc độ chạy"
        if "AttackSpeed" in key:
            return f"Tăng {sign}{v}% tốc độ đánh"
        if "SpellCastSpeed" in key:
            return f"Tăng {sign}{v}% tốc độ niệm"
        if "HealIncreasePercent" in key:
            return f"Tăng {sign}{v}% hồi máu"
        if "EnergyAbsorptionPercent" in key:
            return f"{sign}{v}% hấp thụ năng lượng"
        if "DefensiveBlockRecoveryReduction" in key:
            return f"Giảm {sign}{v} phục hồi block"
        if "Strength" in key:
            return f"{sign}{v} Sức mạnh"
        if "Dexterity" in key:
            return f"{sign}{v} Nhanh nhẹn"
        if "Intelligence" in key:
            return f"{sign}{v} Trí tuệ"
        if "Spirit" in key:
            return f"{sign}{v} Tinh thần"
        if "ConstitutionModifier" in key:
            return f"Tăng {sign}{v}% Thể chất"
        return key
    # RETALIATION
    if key.startswith("retaliation"):
        if key == "retaliationTotalDamageModifier":
            return f"Tăng {sign}{v}% sát thương phản"
        if dt:
            return f"Phản {sign}{v} sát thương {dtvi}"
        return key
    # RACIAL
    if key.startswith("racial"):
        if "PercentDamage" in key:
            return f"Tăng {sign}{v}% sát thương vs loài"
        if "PercentDefense" in key:
            return f"Tăng {sign}{v}% phòng thủ vs loài"
        if "Race" in key:
            return f"Loài: {val}"
        return key
    # PET
    if key.startswith("pet"):
        if "BonusName" in key:
            return "Có chỉ số Pet"
        if "Defensive" in key:
            return f"{sign}{v} phòng thủ Pet"
        if "Avoidance" in key:
            return f"{sign}{v}% né tránh Pet"
        return key
    # AUGMENT / SKILL
    if key.startswith("augment"):
        if "AllLevel" in key:
            return f"+{val} level tất cả kỹ năng augment"
        if "MasteryLevel" in key:
            return f"+{val} level mastery augment"
        if "MasteryName" in key:
            return f"Mastery augment: {val}"
        if "SkillLevel" in key:
            return f"+{val} level kỹ năng augment"
        return key
    if key.startswith("itemSkill"):
        if "Name" in key:
            return f"Kỹ năng: {val}"
        if "LevelEq" in key:
            return f"Yêu cầu level kỹ năng: {val}"
        return key
    if key.startswith("modified"):
        if "Name" in key:
            return f"Kỹ năng sửa đổi: {val}"
        if "Level" in key:
            return f"+{val} level kỹ năng sửa đổi"
        return key
    return key

def humanize(key, val):
    """Player-friendly English label for a stat key + value."""
    v = fmt_val(val)
    sign = "+" if (isinstance(val, (int, float)) and val >= 0) else ""
    dt = detect_dt(key)
    EN = {"Physical":"Physical","Fire":"Fire","Cold":"Cold","Lightning":"Lightning","Poison":"Poison",
          "Aether":"Aether","Chaos":"Chaos","Pierce":"Pierce","Vitality":"Vitality","Elemental":"Elemental",
          "Bleeding":"Bleeding"}
    dtvi = EN.get(dt, dt) if dt else ""
    if key.startswith("offensive"):
        if "Slow" in key:
            rest = key.replace("Slow", "")
            slow_dt = dt or detect_dt(rest)
            slow_en = EN.get(slow_dt, slow_dt) if slow_dt else ""
            if key.endswith("Modifier"):
                return f"Slow {sign}{v}% {slow_en} damage of enemies"
            if "Duration" in key:
                return f"Slow {slow_en} damage of enemies: {sign}{v}s"
            return f"Slow {slow_en} damage of enemies ({sign}{v})"
        if "ResistanceReduction" in key:
            return f"Reduce enemy {dtvi} resistance {sign}{v}%"
        if "TotalDamageModifier" in key:
            return f"Increase Total Damage {sign}{v}%"
        if "Confusion" in key:
            return f"{sign}{v}% Chance of Confusion" if "Chance" in key else f"Confusion {sign}{v}"
        if "Freeze" in key:
            return f"{sign}{v}% Chance to Freeze" if "Chance" in key else f"Freeze {sign}{v}"
        if "Stun" in key:
            return f"{sign}{v}% Chance to Stun" if "Chance" in key else f"Stun {sign}{v}"
        if dt:
            if key.endswith("Modifier"):
                return f"Increase {dtvi} Damage {sign}{v}%"
            if key.endswith("Min"):
                return f"{sign}{v} {dtvi} Damage (flat)"
            if key.endswith("Max"):
                return f"{sign}{v} Max {dtvi} Damage"
            if "Base" in key:
                return f"{sign}{v} Base {dtvi} Damage"
        return key
    if key.startswith("defensive"):
        if "Block" in key:
            if "Chance" in key:
                return f"{sign}{v}% Block Chance"
            if "Amount" in key:
                return f"{sign}{v}% Block Amount"
            if "Recovery" in key:
                return f"Block Recovery {sign}{v}"
            return f"Block {sign}{v}%"
        if "Protection" in key:
            return f"Increase Armor {sign}{v}%" if key.endswith("Modifier") else f"{sign}{v} Armor"
        if "Absorption" in key:
            return f"Increase Absorption {sign}{v}%"
        if "BonusProtection" in key:
            return f"{sign}{v} Bonus Armor"
        if "Petrify" in key:
            return f"{sign}{v} Petrify Resistance"
        if "Trap" in key:
            return f"{sign}{v} Trap Resistance"
        if "Stun" in key:
            return f"{sign}{v} Stun Resistance"
        if "Freeze" in key:
            return f"{sign}{v} Freeze Resistance"
        if "Bleeding" in key:
            return f"{sign}{v} Bleeding Resistance"
        if "TotalSpeedResistance" in key:
            return f"{sign}{v}% Slow Resistance"
        if "PercentReflectionResistance" in key:
            return f"{sign}{v}% Reflection Resistance"
        if "SlowLifeLeach" in key:
            return f"{sign}{v} Life Leech when Slowed"
        if dt:
            if key.endswith("MaxResist"):
                return f"{sign}{v} Max {dtvi} Resistance"
            return f"{sign}{v} {dtvi} Resistance"
        return key
    if key.startswith("character"):
        if "OffensiveAbility" in key:
            return f"{sign}{v} Offensive Ability (OA)" if key.endswith("Modifier") else f"{sign}{v} OA"
        if "DefensiveAbility" in key:
            return f"{sign}{v} Defensive Ability (DA)" if key.endswith("Modifier") else f"{sign}{v} DA"
        if "Life" in key:
            if "Regen" in key:
                return f"Regen {sign}{v} Life/s" if "Modifier" in key else f"{sign}{v} Life Regeneration"
            return f"Increase {sign}{v}% Life" if key.endswith("Modifier") else f"{sign}{v} Life"
        if "Mana" in key:
            if "Regen" in key:
                return f"Regen {sign}{v} Mana/s"
            return f"Increase {sign}{v}% Mana" if key.endswith("Modifier") else f"{sign}{v} Mana"
        if "RunSpeed" in key:
            return f"Increase {sign}{v}% Run Speed"
        if "AttackSpeed" in key:
            return f"Increase {sign}{v}% Attack Speed"
        if "SpellCastSpeed" in key:
            return f"Increase {sign}{v}% Cast Speed"
        if "HealIncreasePercent" in key:
            return f"Increase {sign}{v}% Healing"
        if "EnergyAbsorptionPercent" in key:
            return f"{sign}{v}% Energy Absorption"
        if "DefensiveBlockRecoveryReduction" in key:
            return f"Reduce Block Recovery {sign}{v}"
        if "Strength" in key:
            return f"{sign}{v} Strength"
        if "Dexterity" in key:
            return f"{sign}{v} Dexterity"
        if "Intelligence" in key:
            return f"{sign}{v} Intelligence"
        if "Spirit" in key:
            return f"{sign}{v} Spirit"
        if "ConstitutionModifier" in key:
            return f"Increase {sign}{v}% Constitution"
        return key
    if key.startswith("retaliation"):
        if key == "retaliationTotalDamageModifier":
            return f"Increase Retaliation Damage {sign}{v}%"
        if dt:
            return f"Retaliate {sign}{v} {dtvi} Damage"
        return key
    if key.startswith("racial"):
        if "PercentDamage" in key:
            return f"Increase {sign}{v}% Damage vs Race"
        if "PercentDefense" in key:
            return f"Increase {sign}{v}% Defense vs Race"
        if "Race" in key:
            return f"Race: {val}"
        return key
    if key.startswith("pet"):
        if "BonusName" in key:
            return "Has Pet Bonus"
        if "Defensive" in key:
            return f"{sign}{v} Pet Defense"
        if "Avoidance" in key:
            return f"{sign}{v}% Pet Avoidance"
        return key
    if key.startswith("augment"):
        if "AllLevel" in key:
            return f"+{val} to all augment skill levels"
        if "MasteryLevel" in key:
            return f"+{val} to augment mastery level"
        if "MasteryName" in key:
            return f"Augment Mastery: {val}"
        if "SkillLevel" in key:
            return f"+{val} to augment skill level"
        return key
    if key.startswith("itemSkill"):
        if "Name" in key:
            return f"Skill: {val}"
        if "LevelEq" in key:
            return f"Requires skill level: {val}"
        return key
    if key.startswith("modified"):
        if "Name" in key:
            return f"Modified Skill: {val}"
        if "Level" in key:
            return f"+{val} to modified skill level"
        return key
    return key

def clean(v):
    if isinstance(v, str):
        return v.replace("^w^n", " | ").replace("^w", "").strip()
    return v

# --- build -----------------------------------------------------------------
db_path = os.path.join(HERE, "grimdawn_augments.db")
if os.path.exists(db_path):
    os.remove(db_path)
con = sqlite3.connect(db_path)
cur = con.cursor()
# Grim Dawn version (from itemdb.js: window.gameVersion="Version X.Y.Z.W")
version_match = re.search(r'window\.gameVersion="([^"]+)"',
    open(os.path.join(HERE, "itemdb.js"), encoding="utf-8", errors="replace").read())
GAME_VERSION = version_match.group(1) if version_match else "unknown"
cur.execute("""CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);""")
cur.execute("INSERT INTO meta VALUES('game_version', ?)", (GAME_VERSION,))
cur.execute("""CREATE TABLE augments(
    id TEXT PRIMARY KEY, name TEXT, rarity TEXT, item_level INTEGER,
    slot_group TEXT, slots TEXT, factions TEXT, faction_names TEXT,
    expansions TEXT, expansion_names TEXT, rep_tier TEXT, rep_tier_name TEXT,
    description TEXT, image TEXT, cls TEXT, untradeable INTEGER, raw TEXT,
    has_damage INTEGER DEFAULT 0, has_resist INTEGER DEFAULT 0, has_retaliation INTEGER DEFAULT 0);""")
cur.execute("""CREATE TABLE augment_stats(augment_id TEXT, stat_key TEXT, stat_value REAL, label TEXT,
    PRIMARY KEY(augment_id, stat_key));""")
cur.execute("""CREATE TABLE augment_effects(augment_id TEXT, damage_type TEXT, direction TEXT,
    PRIMARY KEY(augment_id, damage_type, direction));""")
cur.execute("CREATE INDEX idx_aug_slot ON augments(slot_group);")
cur.execute("CREATE INDEX idx_aug_rarity ON augments(rarity);")
cur.execute("CREATE INDEX idx_eff ON augment_effects(damage_type, direction);")

rows = stat_rows = eff_rows = 0
for k, p in parsed.items():
    cls = p.get("cls_list") or []
    slots = sorted({CLS_SLOT.get(c, ("?", c))[1] for c in cls})
    slot_group = sorted({CLS_SLOT.get(c, ("?", c))[0] for c in cls})
    factions = p.get("factions") or []
    exps = p.get("expansion") or []
    desc = clean(p.get("desc", ""))
    eff = defaultdict(set)
    for sk, sv in p.items():
        c = classify(sk)
        if c and isinstance(sv, (int, float)) and sv != 0:
            eff[c[0]].add(c[1])
    cur.execute("""INSERT OR REPLACE INTO augments VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (p["id"], clean(p.get("name", "")), p.get("f"), int(p.get("itemLevel", 0) or 0),
         ",".join(slot_group), ",".join(slots), ",".join(factions),
         ",".join(FACTION.get(f, f) for f in factions), ",".join(exps),
         ",".join(EXP_NAME.get(e, e) for e in exps), p.get("repTier") or "",
         REP_TIER.get(p.get("repTier"), "") or "", desc, p.get("n", ""), ",".join(cls),
         int(p.get("untradeable", 0) or 0), json.dumps(p, ensure_ascii=False),
         1 if eff.get("damage") else 0, 1 if eff.get("resist") else 0, 1 if eff.get("retaliation") else 0))
    rows += 1
    # store ALL numeric stats with English label (skip meta keys)
    META = {"itemLevel", "k", "n", "untradeable", "id", "l"}
    for sk, sv in p.items():
        if sk in META:
            continue
        if isinstance(sv, (int, float)) and sv != 0 and re.match(r'^[a-z]', sk):
            label = humanize(sk, sv)
            cur.execute("INSERT OR REPLACE INTO augment_stats VALUES(?,?,?,?)",
                        (p["id"], sk, float(sv), label))
            stat_rows += 1
    for direction, types in eff.items():
        for t in types:
            cur.execute("INSERT OR REPLACE INTO augment_effects VALUES(?,?,?)", (p["id"], t, direction))
            eff_rows += 1

con.commit()
con.close()
print(f"Built v4: augments={rows}, augment_stats={stat_rows}, augment_effects={eff_rows}")
print(f"Game version: {GAME_VERSION}")
# sanity
import sqlite3 as s
cc = s.connect(db_path)
print("Bleeding effects:", cc.execute("SELECT count(*) FROM augment_effects WHERE damage_type='Bleeding'").fetchone()[0])
print("Sample labels:", cc.execute("SELECT stat_key,label FROM augment_stats WHERE augment_id='it439' LIMIT 6").fetchall())
