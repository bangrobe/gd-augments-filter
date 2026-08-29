#!/usr/bin/env python3
"""Export grimdawn_augments.db → web/public/data/augments.json.

Schema matches the file the React app expects (see web/check.mjs).
Run: python3 export_db_to_json.py
"""
import json
import os
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "grimdawn_augments.db")
OUT_PATH = os.path.join(HERE, "web", "public", "data", "augments.json")


def main():
    if not os.path.exists(DB_PATH):
        raise SystemExit(f"DB not found: {DB_PATH} — run build_db.py first")

    # NOTE: one sqlite3 connection holds a single active cursor. We must
    # fetchall() the outer query first, then open separate connections for
    # the per-augment stats/effects queries.
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    version = con.execute("SELECT value FROM meta WHERE key='game_version'").fetchone()
    game_version = version["value"] if version else "unknown"

    augments = []
    rows = con.execute(
        "SELECT id, name, rarity, item_level, slot_group, slots, factions, faction_names,"
        " expansions, expansion_names, rep_tier, rep_tier_name, description, cls,"
        " untradeable, raw, sold_by, has_damage, has_resist, has_retaliation"
        " FROM augments ORDER BY item_level, name"
    ).fetchall()

    # Per-augment connection so nested queries don't disturb the outer loop.
    con2 = sqlite3.connect(DB_PATH)
    con2.row_factory = sqlite3.Row
    for row in rows:
        stats = [
            {"key": s["stat_key"], "value": s["stat_value"], "label": s["label"]}
            for s in con2.execute(
                "SELECT stat_key, stat_value, label FROM augment_stats"
                " WHERE augment_id=? ORDER BY rowid",
                (row["id"],),
            )
        ]
        effects = [
            f"{e['damage_type']}:{e['direction']}"
            for e in con2.execute(
                "SELECT damage_type, direction FROM augment_effects"
                " WHERE augment_id=? ORDER BY damage_type, direction",
                (row["id"],),
            )
        ]
        augments.append(
            {
                "id": row["id"],
                "name": row["name"],
                "rarity": row["rarity"],
                "item_level": row["item_level"],
                "slot_group": row["slot_group"],
                "slots": row["slots"],
                "factions": row["factions"],
                "faction_names": row["faction_names"],
                "expansions": row["expansions"],
                "expansion_names": row["expansion_names"],
                "rep_tier": row["rep_tier"],
                "rep_tier_name": row["rep_tier_name"],
                "description": row["description"],
                "cls": row["cls"],
                "untradeable": row["untradeable"],
                "raw": row["raw"],
                "sold_by": (json.loads(row["sold_by"]) if row["sold_by"] else []),
                "has_damage": row["has_damage"],
                "has_resist": row["has_resist"],
                "has_retaliation": row["has_retaliation"],
                "effects": effects,
                "stats": stats,
            }
        )

    out = {
        "game_version": game_version,
        "count": len(augments),
        "augments": augments,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"Wrote {len(augments)} augments → {OUT_PATH} ({os.path.getsize(OUT_PATH) // 1024}KB)")


if __name__ == "__main__":
    main()
