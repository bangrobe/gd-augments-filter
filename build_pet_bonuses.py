#!/usr/bin/env python3
"""Inject pet bonus stats vào grimdawn_augments.db.

Source: window.petBonuses={...} trong itemdb.js (grimtools).
Target augment có field `petBonusName` trong raw data (string ID như "pb446").

Vấn đề:
- 42 augment trong DB có `petBonusName` (string) trong raw data
- Nhưng `build_db.py` skip string fields khi lưu augment_stats
- → UI app không có stats nào cho pet → mất thông tin "Bonus to All Pets"

Solution:
- Tạo bảng `augment_pet_stats` riêng (clean separation)
- Mỗi row: (augment_id, stat_key, stat_value, label)
- Không conflict với PRIMARY KEY(augment_id, stat_key) của augment_stats
- UI sẽ render stats này dưới section riêng "Bonus to All Pets"

Run: python3 build_pet_bonuses.py
Sau đó: python3 export_db_to_json.py → build web app.
"""
import json
import os
import re
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "grimdawn_augments.db")
ITEMDB = os.path.join(HERE, "itemdb.js")
L10N = os.path.join(HERE, "l10n_en.js")


# --- 1. Parse petBonuses map from itemdb.js ---------------------------------
def parse_pet_bonuses():
    text = open(ITEMDB, encoding="utf-8", errors="replace").read()
    idx = text.find("window.petBonuses={")
    if idx < 0:
        raise SystemExit("petBonuses section not found in itemdb.js")
    depth = 0
    end = idx + len("window.petBonuses={")
    for i in range(end, min(end + 500000, len(text))):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            if depth == 0:
                end = i + 1
                break
            depth -= 1
    section = text[idx + len("window.petBonuses="):end]

    pet_map = {}
    # Each entry: pbNNN:{key:val,key:val}
    for m in re.finditer(r"(pb\d+)\s*:\s*\{([^}]+)\}", section):
        pb_id = m.group(1)
        content = m.group(2)
        stats = {}
        for kv in re.finditer(
            r'(\w+)\s*:\s*("[^"]*"|-?[\d.eE+-]+|true|false)', content
        ):
            k = kv.group(1)
            v_raw = kv.group(2)
            # skip meta
            if k in ("o", "templateName", "particleEffectAttachPoints"):
                continue
            if v_raw.startswith('"'):
                continue  # string values not used as stats
            try:
                v = (
                    float(v_raw)
                    if ("." in v_raw or "e" in v_raw.lower())
                    else int(v_raw)
                )
            except ValueError:
                continue
            stats[k] = v
        if stats:
            pet_map[pb_id] = stats
    return pet_map


# --- 2. Same humanize logic as build_db.py ---------------------------------
DMG = {
    "Physical": "offensivePhysical", "Fire": "offensiveFire", "Cold": "offensiveCold",
    "Lightning": "offensiveLightning", "Poison": "offensivePoison", "Aether": "offensiveAether",
    "Chaos": "offensiveChaos", "Pierce": "offensivePierce", "Vitality": "offensiveLife",
    "Elemental": "offensiveElemental", "Bleeding": "offensiveBleeding",
}
RES = {
    "Physical": "defensivePhysical", "Fire": "defensiveFire", "Cold": "defensiveCold",
    "Lightning": "defensiveLightning", "Poison": "defensivePoison", "Aether": "defensiveAether",
    "Chaos": "defensiveChaos", "Pierce": "defensivePierce", "Vitality": "defensiveLife",
    "Elemental": "defensiveElemental", "Bleeding": "defensiveBleeding",
}
RET = {
    "Physical": "retaliationPhysical", "Fire": "retaliationFire", "Cold": "retaliationCold",
    "Lightning": "retaliationLightning", "Poison": "retaliationPoison", "Aether": "retaliationAether",
    "Chaos": "retaliationChaos", "Vitality": "retaliationLife", "Bleeding": "retaliationBleeding",
}
DT = {
    "Physical": "Vật lý", "Fire": "Lửa", "Cold": "Băng", "Lightning": "Sét",
    "Poison": "Độc", "Aether": "Aether", "Chaos": "Hỗn mang", "Pierce": "Xuyên giáp",
    "Vitality": "Sinh lực", "Elemental": "Nguyên tố", "Bleeding": "Chảy máu",
}


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


def fmt_val(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    if f.is_integer():
        return str(int(f))
    return f"{f:.1f}"


def humanize(key, val):
    """Vietnamese label - port of build_db.py humanize() (the first one)."""
    v = fmt_val(val)
    sign = "+" if (isinstance(val, (int, float)) and val >= 0) else ""
    dt = detect_dt(key)
    dtvi = DT.get(dt, dt) if dt else ""
    if key.startswith("offensive"):
        if "Slow" in key:
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
        if "CritDamageModifier" in key:
            return f"Tăng {sign}{v}% sát thương chí mạng"
        if "DamageMultModifier" in key:
            return f"Nhân {sign}{v} hệ số sát thương"
        if "GlobalChance" in key:
            return f"{sign}{v}% cơ hội kích hoạt toàn cục"
        if "Confusion" in key:
            return (
                f"{sign}{v}% cơ hội gây Bối rối"
                if "Chance" in key
                else f"Gây Bối rối {sign}{v}"
            )
        if "Freeze" in key:
            return (
                f"{sign}{v}% cơ hội làm Đóng băng"
                if "Chance" in key
                else f"Làm Đóng băng {sign}{v}"
            )
        if "Stun" in key:
            return (
                f"{sign}{v}% cơ hội làm Choáng"
                if "Chance" in key
                else f"Làm Choáng {sign}{v}"
            )
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
            return (
                f"Tăng {sign}{v}% Giáp"
                if key.endswith("Modifier")
                else f"{sign}{v} Giáp"
            )
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
    if key.startswith("character"):
        if "OffensiveAbility" in key:
            return (
                f"{sign}{v} Điểm Tấn công (OA)"
                if key.endswith("Modifier")
                else f"{sign}{v} OA"
            )
        if "DefensiveAbility" in key:
            return (
                f"{sign}{v} Điểm Phòng thủ (DA)"
                if key.endswith("Modifier")
                else f"{sign}{v} DA"
            )
        if "Life" in key:
            if "Regen" in key:
                return (
                    f"Hồi {sign}{v} máu/giây"
                    if "Modifier" in key
                    else f"Hồi sinh {sign}{v}"
                )
            return (
                f"Tăng {sign}{v}% Máu"
                if key.endswith("Modifier")
                else f"{sign}{v} Máu"
            )
        if "Mana" in key:
            if "Regen" in key:
                return f"Hồi {sign}{v} mana/giây"
            return (
                f"Tăng {sign}{v}% Mana"
                if key.endswith("Modifier")
                else f"{sign}{v} Mana"
            )
        if "TotalSpeedModifier" in key:
            return f"Tăng {sign}{v}% tốc độ tổng"
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
    if key.startswith("retaliation"):
        if key == "retaliationTotalDamageModifier":
            return f"Tăng {sign}{v}% sát thương phản"
        if dt:
            return f"Phản {sign}{v} sát thương {dtvi}"
        return key
    if key.startswith("racial"):
        if "PercentDamage" in key:
            return f"Tăng {sign}{v}% sát thương vs loài"
        if "PercentDefense" in key:
            return f"Tăng {sign}{v}% phòng thủ vs loài"
        if "Race" in key:
            return f"Loài: {val}"
        return key
    return key


def humanize_en(key, val):
    """English label - port of build_db.py second humanize()."""
    v = fmt_val(val)
    sign = "+" if (isinstance(val, (int, float)) and val >= 0) else ""
    dt = detect_dt(key)
    EN = {
        "Physical": "Physical", "Fire": "Fire", "Cold": "Cold", "Lightning": "Lightning",
        "Poison": "Poison", "Aether": "Aether", "Chaos": "Chaos", "Pierce": "Pierce",
        "Vitality": "Vitality", "Elemental": "Elemental", "Bleeding": "Bleeding",
    }
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
        if "CritDamageModifier" in key:
            return f"Increase Critical Damage {sign}{v}%"
        if "DamageMultModifier" in key:
            return f"Multiply damage by {sign}{v}"
        if "GlobalChance" in key:
            return f"{sign}{v}% Global Chance"
        if "Confusion" in key:
            return (
                f"{sign}{v}% Chance of Confusion"
                if "Chance" in key
                else f"Confusion {sign}{v}"
            )
        if "Freeze" in key:
            return (
                f"{sign}{v}% Chance to Freeze"
                if "Chance" in key
                else f"Freeze {sign}{v}"
            )
        if "Stun" in key:
            return (
                f"{sign}{v}% Chance to Stun"
                if "Chance" in key
                else f"Stun {sign}{v}"
            )
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
            return (
                f"Increase Armor {sign}{v}%"
                if key.endswith("Modifier")
                else f"{sign}{v} Armor"
            )
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
            return (
                f"{sign}{v} Offensive Ability (OA)"
                if key.endswith("Modifier")
                else f"{sign}{v} OA"
            )
        if "DefensiveAbility" in key:
            return (
                f"{sign}{v} Defensive Ability (DA)"
                if key.endswith("Modifier")
                else f"{sign}{v} DA"
            )
        if "Life" in key:
            if "Regen" in key:
                return (
                    f"Regen {sign}{v} Life/s"
                    if "Modifier" in key
                    else f"{sign}{v} Life Regeneration"
                )
            return (
                f"Increase {sign}{v}% Life"
                if key.endswith("Modifier")
                else f"{sign}{v} Life"
            )
        if "Mana" in key:
            if "Regen" in key:
                return f"Regen {sign}{v} Mana/s"
            return (
                f"Increase {sign}{v}% Mana"
                if key.endswith("Modifier")
                else f"{sign}{v} Mana"
            )
        if "TotalSpeedModifier" in key:
            return f"Increase Total Speed {sign}{v}%"
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
    return key


# --- 3. Main: write to DB --------------------------------------------------
def main():
    print(f"[1] Parsing petBonuses from itemdb.js ({os.path.getsize(ITEMDB) // 1024}KB)…")
    pet_map = parse_pet_bonuses()
    print(f"    -> {len(pet_map)} pet bonus templates")

    print(f"[2] Connecting to {DB}")
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    # 2a. Create new table
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS augment_pet_stats(
            augment_id TEXT,
            pet_bonus_id TEXT,
            stat_key TEXT,
            stat_value REAL,
            label_vi TEXT,
            label_en TEXT,
            PRIMARY KEY(augment_id, stat_key)
        )
        """
    )
    con.execute("DELETE FROM augment_pet_stats")
    print("    -> augment_pet_stats ready")

    # 2b. Find augments with petBonusName
    rows = con.execute(
        "SELECT id, name, raw FROM augments WHERE raw LIKE '%petBonusName%'"
    ).fetchall()
    print(f"[3] Found {len(rows)} augments with petBonusName")

    inserted = 0
    unresolved = []
    no_data = []
    samples = []
    for r in rows:
        try:
            raw = json.loads(r["raw"])
        except (json.JSONDecodeError, TypeError):
            continue
        pet_id = raw.get("petBonusName")
        if not pet_id:
            continue
        pet_stats = pet_map.get(pet_id)
        if not pet_stats:
            unresolved.append((r["id"], r["name"], pet_id))
            continue
        # Insert all pet stats for this augment
        for stat_key, stat_val in pet_stats.items():
            label_vi = humanize(stat_key, stat_val)
            label_en = humanize_en(stat_key, stat_val)
            con.execute(
                "INSERT OR REPLACE INTO augment_pet_stats VALUES(?,?,?,?,?,?)",
                (r["id"], pet_id, stat_key, float(stat_val), label_vi, label_en),
            )
            inserted += 1
        if len(samples) < 5:
            samples.append((r["id"], r["name"], pet_id, list(pet_stats.items())[:3]))

    con.commit()

    print(f"[4] Inserted {inserted} pet stat rows")
    if unresolved:
        print(f"    ⚠ {len(unresolved)} augments have petBonusName but no entry in itemdb.js petBonuses:")
        for aid, name, pet in unresolved[:5]:
            print(f"      {aid} {name} → {pet}")
    print()
    print("[5] Sample rows:")
    for aid, name, pet, items in samples:
        print(f"  {aid} {name} (petBonus={pet}):")
        for k, v in items:
            print(f"    {k}={v} → VI: {humanize(k, v)!r}")
            print(f"                   EN: {humanize_en(k, v)!r}")
    print()

    # Sanity check
    total_with = con.execute(
        "SELECT count(DISTINCT augment_id) FROM augment_pet_stats"
    ).fetchone()[0]
    print(f"[6] Augments with pet stats: {total_with}")

    # Sample query: lookup it7473 (Blight Beast Pustules)
    print("\n[7] Lookup it7473 (Blight Beast Pustules):")
    for row in con.execute(
        "SELECT * FROM augment_pet_stats WHERE augment_id='it7473'"
    ).fetchall():
        print(f"    {dict(row)}")

    con.close()
    print("\n✓ Done. Now run: python3 export_db_to_json.py")


if __name__ == "__main__":
    main()