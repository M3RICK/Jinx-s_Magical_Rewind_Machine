"""
Initialize SQLite database for League of Legends static data.

This script creates the database schema for storing:
- Items (stats, costs, build paths)
- Champions (abilities, roles, stats)
- Runes (trees, descriptions)
- Champion counters

Run this script once to set up the database structure.
"""

import sqlite3
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'league_data.db')

def create_tables():
    """Create all tables for League of Legends data."""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ITEMS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            item_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            plaintext TEXT,
            cost_total INTEGER,
            cost_base INTEGER,
            cost_sell INTEGER,

            -- Stats
            flat_hp INTEGER DEFAULT 0,
            flat_mp INTEGER DEFAULT 0,
            flat_armor INTEGER DEFAULT 0,
            flat_magic_resist INTEGER DEFAULT 0,
            flat_attack_damage INTEGER DEFAULT 0,
            flat_ability_power INTEGER DEFAULT 0,
            flat_attack_speed REAL DEFAULT 0,
            percent_attack_speed REAL DEFAULT 0,
            flat_crit_chance REAL DEFAULT 0,
            flat_movement_speed INTEGER DEFAULT 0,
            percent_movement_speed REAL DEFAULT 0,
            flat_health_regen REAL DEFAULT 0,
            flat_mana_regen REAL DEFAULT 0,
            percent_life_steal REAL DEFAULT 0,
            flat_ability_haste INTEGER DEFAULT 0,
            flat_lethality INTEGER DEFAULT 0,
            flat_magic_pen INTEGER DEFAULT 0,
            percent_armor_pen REAL DEFAULT 0,
            percent_magic_pen REAL DEFAULT 0,

            -- Build paths (JSON arrays stored as TEXT)
            builds_from TEXT,  -- "[1001, 1036]" (item IDs)
            builds_into TEXT,  -- "[3031, 6676]"

            -- Tags
            tags TEXT,  -- "['Damage', 'CriticalStrike', 'AttackSpeed']"

            -- Metadata
            purchasable BOOLEAN DEFAULT 1,
            mythic BOOLEAN DEFAULT 0,
            legendary BOOLEAN DEFAULT 0,

            -- Image
            image_full TEXT,
            image_sprite TEXT
        )
    """)

    # CHAMPIONS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS champions (
            champion_id TEXT PRIMARY KEY,  -- "Jinx", "MasterYi", etc.
            champion_key INTEGER UNIQUE,   -- Numeric ID from Riot API
            name TEXT NOT NULL,            -- Display name
            title TEXT,                    -- "The Loose Cannon"

            -- Roles
            primary_role TEXT,             -- "Marksman", "Fighter", etc.
            secondary_role TEXT,
            tags TEXT,                     -- "['Marksman', 'Mage']"

            -- Difficulty
            difficulty INTEGER,            -- 1-10 scale

            -- Base stats
            hp REAL,
            hp_per_level REAL,
            mp REAL,
            mp_per_level REAL,
            armor REAL,
            armor_per_level REAL,
            magic_resist REAL,
            magic_resist_per_level REAL,
            attack_damage REAL,
            attack_damage_per_level REAL,
            attack_speed REAL,
            attack_speed_per_level REAL,
            attack_range REAL,
            move_speed REAL,

            -- Abilities (stored as JSON)
            passive TEXT,  -- JSON: {"name": "...", "description": "..."}
            q_ability TEXT,
            w_ability TEXT,
            e_ability TEXT,
            r_ability TEXT,

            -- Lore
            blurb TEXT,

            -- Image
            image_full TEXT,
            image_sprite TEXT,
            splash_art TEXT,
            loading_screen TEXT
        )
    """)

    # CHAMPION COUNTERS TABLE
    # TODO: Potentially have a webscraping script to update with most known counters and credit site source
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS champion_counters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            champion_id TEXT NOT NULL,
            counter_champion_id TEXT NOT NULL,
            counter_strength TEXT,  -- 'strong', 'moderate', 'weak'
            role_specific TEXT,     -- Which role this counter applies to
            notes TEXT,             -- Why this is a counter

            FOREIGN KEY (champion_id) REFERENCES champions(champion_id),
            FOREIGN KEY (counter_champion_id) REFERENCES champions(champion_id),
            UNIQUE(champion_id, counter_champion_id)
        )
    """)

    # RUNES TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS runes (
            rune_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            rune_tree TEXT NOT NULL,  -- "Precision", "Domination", etc.
            slot INTEGER,              -- 0 = Keystone, 1-3 = regular slots
            is_keystone BOOLEAN,

            -- Description
            short_desc TEXT,
            long_desc TEXT,

            -- Image
            icon TEXT
        )
    """)

    # RUNE TREES TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rune_trees (
            tree_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,  -- "Precision", "Domination", etc.
            icon TEXT,

            -- Primary stats when used as primary tree
            primary_stat_1 TEXT,
            primary_stat_2 TEXT,
            primary_stat_3 TEXT
        )
    """)

    # RECOMMENDED BUILDS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommended_builds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            champion_id TEXT NOT NULL,
            role TEXT NOT NULL,  -- "ADC", "Top", "Mid", etc.

            -- Core items (in order)
            starter_items TEXT,    -- "[1001, 2003, 2003]"
            core_items TEXT,       -- "[3031, 3046, 3094]"
            situational_items TEXT, -- "[3033, 3036, 3139]"

            -- Runes
            primary_tree TEXT,     -- "Precision"
            keystone_id INTEGER,
            primary_runes TEXT,    -- "[rune_id1, rune_id2, rune_id3]"
            secondary_tree TEXT,   -- "Domination"
            secondary_runes TEXT,  -- "[rune_id1, rune_id2]"
            stat_shards TEXT,      -- "[offense, flex, defense]"

            -- Summoner spells
            summoner_spell_1 TEXT, -- "Flash"
            summoner_spell_2 TEXT, -- "Heal"

            -- Skill order
            skill_priority TEXT,   -- "Q>E>W" or similar

            -- Metadata
            patch TEXT,            -- "14.23"
            win_rate REAL,         -- If available from external source
            pick_rate REAL,
            source TEXT,           -- "u.gg", "op.gg", "manual", etc.

            FOREIGN KEY (champion_id) REFERENCES champions(champion_id),
            UNIQUE(champion_id, role, patch)
        )
    """)

    # PATCH VERSION TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patch_version (
            id INTEGER PRIMARY KEY CHECK (id = 1),  -- Only allow one row
            version TEXT NOT NULL,                  -- Current patch version (e.g., "14.23.1")
            last_updated TEXT NOT NULL              -- ISO 8601 timestamp of last sync
        )
    """)

    # Create indexes for faster queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_cost ON items(cost_total)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_tags ON items(tags)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_champions_role ON champions(primary_role)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_champions_difficulty ON champions(difficulty)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_counters_champion ON champion_counters(champion_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_runes_tree ON runes(rune_tree)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_builds_champion ON recommended_builds(champion_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_builds_role ON recommended_builds(role)")

    conn.commit()
    conn.close()

def drop_all_tables():
    """Drop all tables (useful for resetting the database)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    tables = ['items', 'champions', 'champion_counters', 'runes', 'rune_trees', 'recommended_builds', 'patch_version']

    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")

    conn.commit()
    conn.close()

def main():
    """Main function."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--reset':
        drop_all_tables()

    create_tables()

if __name__ == "__main__":
    main()
