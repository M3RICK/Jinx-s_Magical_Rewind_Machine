"""
Populate SQLite database with League of Legends data from Riot Data Dragon.

Fetches:
- Items from Data Dragon
- Champions from Data Dragon
- Runes from Data Dragon

Run this after creating the database with init_league_db.py
"""

import sqlite3
import aiohttp
import asyncio
import json
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'league_data.db')

# Riot Data Dragon URLs
LATEST_VERSION_URL = "https://ddragon.leagueoflegends.com/api/versions.json"
BASE_URL = "https://ddragon.leagueoflegends.com/cdn"

async def get_latest_patch():
    """Get the latest patch version from Riot."""
    async with aiohttp.ClientSession() as session:
        async with session.get(LATEST_VERSION_URL) as response:
            versions = await response.json()
            return versions[0]  # Most recent version

async def fetch_items(patch):
    """Fetch all items from Data Dragon."""
    url = f"{BASE_URL}/{patch}/data/en_US/item.json"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

async def fetch_champions(patch):
    """Fetch all champions from Data Dragon."""
    url = f"{BASE_URL}/{patch}/data/en_US/champion.json"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

async def fetch_champion_detail(champion_id, patch, session):
    """Fetch detailed info for a specific champion."""
    url = f"{BASE_URL}/{patch}/data/en_US/champion/{champion_id}.json"
    async with session.get(url) as response:
        return await response.json()

async def fetch_runes(patch):
    """Fetch all runes from Data Dragon."""
    url = f"{BASE_URL}/{patch}/data/en_US/runesReforged.json"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

def populate_items(conn, items_data, patch):
    """Insert items into database."""
    cursor = conn.cursor()

    items = items_data.get('data', {})
    count = 0

    for item_id, item in items.items():
        # Skip items that shouldn't be in the shop
        gold = item.get('gold', {})
        if not gold.get('purchasable', True):
            continue

        # Extract stats
        stats = item.get('stats', {})

        # Parse build paths
        builds_from = json.dumps(item.get('from', []))
        builds_into = json.dumps(item.get('into', []))
        tags = json.dumps(item.get('tags', []))

        # Image info
        image = item.get('image', {})

        cursor.execute("""
            INSERT OR REPLACE INTO items (
                item_id, name, description, plaintext,
                cost_total, cost_base, cost_sell,
                flat_hp, flat_mp, flat_armor, flat_magic_resist,
                flat_attack_damage, flat_ability_power,
                flat_attack_speed, percent_attack_speed,
                flat_crit_chance, flat_movement_speed, percent_movement_speed,
                flat_health_regen, flat_mana_regen, percent_life_steal,
                flat_ability_haste, flat_lethality,
                builds_from, builds_into, tags,
                purchasable, mythic, legendary,
                image_full, image_sprite
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            int(item_id),
            item.get('name', ''),
            item.get('description', ''),
            item.get('plaintext', ''),
            gold.get('total', 0),
            gold.get('base', 0),
            gold.get('sell', 0),
            int(stats.get('FlatHPPoolMod', 0)),
            int(stats.get('FlatMPPoolMod', 0)),
            int(stats.get('FlatArmorMod', 0)),
            int(stats.get('FlatSpellBlockMod', 0)),
            int(stats.get('FlatPhysicalDamageMod', 0)),
            int(stats.get('FlatMagicDamageMod', 0)),
            stats.get('FlatAttackSpeedMod', 0),
            stats.get('PercentAttackSpeedMod', 0),
            stats.get('FlatCritChanceMod', 0),
            int(stats.get('FlatMovementSpeedMod', 0)),
            stats.get('PercentMovementSpeedMod', 0),
            stats.get('FlatHPRegenMod', 0),
            stats.get('FlatMPRegenMod', 0),
            stats.get('PercentLifeStealMod', 0),
            int(stats.get('FlatCooldownReductionMod', 0)),  # Ability haste
            int(stats.get('FlatPhysicalDamageLethality', 0)),
            builds_from,
            builds_into,
            tags,
            gold.get('purchasable', True),
            item.get('isMythic', False),
            'Legendary' in item.get('description', ''),
            image.get('full', ''),
            image.get('sprite', '')
        ))
        count += 1

    conn.commit()

async def populate_champions(conn, champions_data, patch):
    """Insert champions into database."""
    cursor = conn.cursor()

    champions = champions_data.get('data', {})

    # Fetch all champion details concurrently for speed
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_champion_detail(champ_id, patch, session) for champ_id in champions.keys()]
        champion_details = await asyncio.gather(*tasks)

    # Create a mapping of champion_id to detailed data
    details_map = {}
    for detail in champion_details:
        for champ_id, champ_detail in detail['data'].items():
            details_map[champ_id] = champ_detail

    # Insert each champion into database
    for champ_id, champ in champions.items():
        champ_detail = details_map[champ_id]

        # Stats
        stats = champ_detail.get('stats', {})

        # Abilities
        spells = champ_detail.get('spells', [])
        passive = champ_detail.get('passive', {})

        # Roles
        tags = champ.get('tags', [])
        primary_role = tags[0] if len(tags) > 0 else None
        secondary_role = tags[1] if len(tags) > 1 else None

        # Image
        image = champ.get('image', {})

        cursor.execute("""
            INSERT OR REPLACE INTO champions (
                champion_id, champion_key, name, title,
                primary_role, secondary_role, tags, difficulty,
                hp, hp_per_level, mp, mp_per_level,
                armor, armor_per_level, magic_resist, magic_resist_per_level,
                attack_damage, attack_damage_per_level,
                attack_speed, attack_speed_per_level,
                attack_range, move_speed,
                passive, q_ability, w_ability, e_ability, r_ability,
                blurb, image_full, image_sprite
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            champ_id,
            int(champ.get('key', 0)),
            champ.get('name', ''),
            champ.get('title', ''),
            primary_role,
            secondary_role,
            json.dumps(tags),
            champ.get('info', {}).get('difficulty', 0),
            stats.get('hp', 0),
            stats.get('hpperlevel', 0),
            stats.get('mp', 0),
            stats.get('mpperlevel', 0),
            stats.get('armor', 0),
            stats.get('armorperlevel', 0),
            stats.get('spellblock', 0),
            stats.get('spellblockperlevel', 0),
            stats.get('attackdamage', 0),
            stats.get('attackdamageperlevel', 0),
            stats.get('attackspeed', 0),
            stats.get('attackspeedperlevel', 0),
            stats.get('attackrange', 0),
            stats.get('movespeed', 0),
            json.dumps({'name': passive.get('name', ''), 'description': passive.get('description', '')}),
            json.dumps({'name': spells[0].get('name', ''), 'description': spells[0].get('description', '')}) if len(spells) > 0 else None,
            json.dumps({'name': spells[1].get('name', ''), 'description': spells[1].get('description', '')}) if len(spells) > 1 else None,
            json.dumps({'name': spells[2].get('name', ''), 'description': spells[2].get('description', '')}) if len(spells) > 2 else None,
            json.dumps({'name': spells[3].get('name', ''), 'description': spells[3].get('description', '')}) if len(spells) > 3 else None,
            champ.get('blurb', ''),
            image.get('full', ''),
            image.get('sprite', '')
        ))

    conn.commit()

# TODO: Potentially have a webscraping script to update with most known build and credit site source

def populate_runes(conn, runes_data):
    """Insert runes into database."""
    cursor = conn.cursor()

    rune_count = 0
    tree_count = 0

    for tree in runes_data:
        tree_name = tree.get('key', '')  # "Precision", "Domination", etc.
        tree_id = tree.get('id', 0)

        # Insert rune tree
        cursor.execute("""
            INSERT OR REPLACE INTO rune_trees (
                tree_id, name, icon
            ) VALUES (?, ?, ?)
        """, (
            tree_id,
            tree_name,
            tree.get('icon', '')
        ))
        tree_count += 1

        # Insert individual runes
        for slot_index, slot in enumerate(tree.get('slots', [])):
            for rune in slot.get('runes', []):
                is_keystone = slot_index == 0

                cursor.execute("""
                    INSERT OR REPLACE INTO runes (
                        rune_id, name, rune_tree, slot, is_keystone,
                        short_desc, long_desc, icon
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rune.get('id', 0),
                    rune.get('name', ''),
                    tree_name,
                    slot_index,
                    is_keystone,
                    rune.get('shortDesc', ''),
                    rune.get('longDesc', ''),
                    rune.get('icon', '')
                ))
                rune_count += 1

    conn.commit()

async def main():
    """Main function to populate all data."""
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    patch = await get_latest_patch()
    print(f"Populating database with patch {patch} data...")
    conn = sqlite3.connect(DB_PATH)

    try:
        print("Fetching items...")
        items_data = await fetch_items(patch)
        populate_items(conn, items_data, patch)
        print("✓ Items populated")

        print("Fetching champions...")
        champions_data = await fetch_champions(patch)
        await populate_champions(conn, champions_data, patch)
        print("✓ Champions populated")

        print("Fetching runes...")
        runes_data = await fetch_runes(patch)
        populate_runes(conn, runes_data)
        print("✓ Runes populated")

        print("Database population complete!")

    except Exception as e:
        import traceback
        print("Error populating database:")
        traceback.print_exc()

    finally:
        conn.close()

if __name__ == "__main__":
    asyncio.run(main())
