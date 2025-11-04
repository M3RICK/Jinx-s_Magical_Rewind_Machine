"""
League of Legends data tools for AI chatbot.
Provides Claude with tools to query champions, items, runes, and builds from league_data.db
"""

import sqlite3
import json
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "league_data.db"

def get_db_connection():
    """Create and return a database connection."""
    return sqlite3.connect(str(DB_PATH))


def search_champions(query: str = None, role: str = None):
    """
    Search for champions by name or role.

    Args:
        query: Champion name (partial match allowed)
        role: Champion role (Marksman, Fighter, Mage, etc.)

    Returns:
        List of matching champions with basic info
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = "SELECT champion_id, name, title, primary_role, secondary_role, difficulty FROM champions WHERE 1=1"
    params = []
    if query:
        sql += " AND (name LIKE ? OR champion_id LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%"])
    if role:
        sql += " AND (primary_role LIKE ? OR secondary_role LIKE ?)"
        params.extend([f"%{role}%", f"%{role}%"])
    sql += " LIMIT 10"

    cursor.execute(sql, params)
    results = cursor.fetchall()
    conn.close()

    champions = []
    for row in results:
        champions.append({
            "id": row[0],
            "name": row[1],
            "title": row[2],
            "primary_role": row[3],
            "secondary_role": row[4],
            "difficulty": row[5]
        })
    return champions


def get_champion_details(champion_id: str):
    """
    Get detailed information about a specific champion.

    Args:
        champion_id: Champion ID (e.g., "Jinx", "MasterYi")

    Returns:
        Detailed champion info including stats and abilities
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT champion_id, name, title, primary_role, secondary_role, difficulty,
               hp, hp_per_level, mp, mp_per_level, armor, armor_per_level,
               magic_resist, magic_resist_per_level, attack_damage, attack_damage_per_level,
               attack_speed, attack_speed_per_level, attack_range, move_speed,
               passive, q_ability, w_ability, e_ability, r_ability, blurb
        FROM champions WHERE champion_id = ? OR name = ?
    """, (champion_id, champion_id))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None
    champion = {
        "id": row[0],
        "name": row[1],
        "title": row[2],
        "primary_role": row[3],
        "secondary_role": row[4],
        "difficulty": row[5],
        "base_stats": {
            "hp": row[6],
            "hp_per_level": row[7],
            "mp": row[8],
            "mp_per_level": row[9],
            "armor": row[10],
            "armor_per_level": row[11],
            "magic_resist": row[12],
            "magic_resist_per_level": row[13],
            "attack_damage": row[14],
            "attack_damage_per_level": row[15],
            "attack_speed": row[16],
            "attack_speed_per_level": row[17],
            "attack_range": row[18],
            "move_speed": row[19]
        },
        "abilities": {
            "passive": json.loads(row[20]) if row[20] else None,
            "q": json.loads(row[21]) if row[21] else None,
            "w": json.loads(row[22]) if row[22] else None,
            "e": json.loads(row[23]) if row[23] else None,
            "r": json.loads(row[24]) if row[24] else None
        },
        "lore": row[25]
    }
    return champion


def search_items(query: str = None, tags: str = None):
    """
    Search for items by name or tags.

    Args:
        query: Item name (partial match allowed)
        tags: Item tags (Damage, Tank, Support, etc.)

    Returns:
        List of matching items with basic info
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = """
        SELECT item_id, name, plaintext, cost_total, tags, mythic, legendary, purchasable
        FROM items WHERE purchasable = 1
    """
    params = []
    if query:
        sql += " AND name LIKE ?"
        params.append(f"%{query}%")
    if tags:
        sql += " AND tags LIKE ?"
        params.append(f"%{tags}%")
    sql += " LIMIT 15"
    cursor.execute(sql, params)
    results = cursor.fetchall()
    conn.close()

    items = []
    for row in results:
        items.append({
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "cost": row[3],
            "tags": row[4],
            "mythic": bool(row[5]),
            "legendary": bool(row[6])
        })
    return items


def get_item_details(item_id: int):
    """
    Get detailed information about a specific item.

    Args:
        item_id: Item ID number

    Returns:
        Detailed item info including all stats
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM items WHERE item_id = ?", (item_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    item = {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "plaintext": row[3],
        "cost": {
            "total": row[4],
            "base": row[5],
            "sell": row[6]
        },
        "stats": {
            "hp": row[7],
            "mp": row[8],
            "armor": row[9],
            "magic_resist": row[10],
            "attack_damage": row[11],
            "ability_power": row[12],
            "flat_attack_speed": row[13],
            "percent_attack_speed": row[14],
            "crit_chance": row[15],
            "movement_speed": row[16],
            "percent_movement_speed": row[17],
            "health_regen": row[18],
            "mana_regen": row[19],
            "life_steal": row[20],
            "ability_haste": row[21],
            "lethality": row[22],
            "magic_pen": row[23],
            "percent_armor_pen": row[24],
            "percent_magic_pen": row[25]
        },
        "builds_from": json.loads(row[26]) if row[26] else [],
        "builds_into": json.loads(row[27]) if row[27] else [],
        "tags": row[28],
        "mythic": bool(row[30]),
        "legendary": bool(row[31])
    }
    return item


def get_recommended_build(champion_id: str, role: str = None):
    """
    Get recommended build for a champion in a specific role.

    Args:
        champion_id: Champion ID (e.g., "Jinx")
        role: Role (ADC, Top, Mid, Jungle, Support) - optional

    Returns:
        Recommended build including items, runes, and summoner spells
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = "SELECT * FROM recommended_builds WHERE champion_id = ?"
    params = [champion_id]
    if role:
        sql += " AND role LIKE ?"
        params.append(f"%{role}%")

    cursor.execute(sql, params)
    results = cursor.fetchall()
    conn.close()

    if not results:
        return None
    builds = []
    for row in results:
        builds.append({
            "champion_id": row[1],
            "role": row[2],
            "starter_items": json.loads(row[3]) if row[3] else [],
            "core_items": json.loads(row[4]) if row[4] else [],
            "situational_items": json.loads(row[5]) if row[5] else [],
            "runes": {
                "primary_tree": row[6],
                "keystone_id": row[7],
                "primary_runes": json.loads(row[8]) if row[8] else [],
                "secondary_tree": row[9],
                "secondary_runes": json.loads(row[10]) if row[10] else [],
                "stat_shards": json.loads(row[11]) if row[11] else []
            },
            "summoner_spells": [row[12], row[13]]
        })
    return builds


def get_champion_counters(champion_id: str):
    """
    Get champions that counter the specified champion.

    Args:
        champion_id: Champion ID

    Returns:
        List of counter champions with strength and notes
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT cc.counter_champion_id, c.name, cc.counter_strength, cc.role_specific, cc.notes
        FROM champion_counters cc
        JOIN champions c ON cc.counter_champion_id = c.champion_id
        WHERE cc.champion_id = ?
    """, (champion_id,))
    results = cursor.fetchall()
    conn.close()

    counters = []
    for row in results:
        counters.append({
            "counter_id": row[0],
            "counter_name": row[1],
            "strength": row[2],
            "role_specific": row[3],
            "notes": row[4]
        })
    return counters


def search_runes(query: str = None, tree: str = None, keystone_only: bool = False):
    """
    Search for runes by name or tree.

    Args:
        query: Rune name (partial match)
        tree: Rune tree (Precision, Domination, Sorcery, etc.)
        keystone_only: Only return keystones if True

    Returns:
        List of matching runes
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = "SELECT rune_id, name, rune_tree, slot, is_keystone, short_desc FROM runes WHERE 1=1"
    params = []
    if query:
        sql += " AND name LIKE ?"
        params.append(f"%{query}%")
    if tree:
        sql += " AND rune_tree LIKE ?"
        params.append(f"%{tree}%")
    if keystone_only:
        sql += " AND is_keystone = 1"
    sql += " LIMIT 15"
    cursor.execute(sql, params)
    results = cursor.fetchall()
    conn.close()

    runes = []
    for row in results:
        runes.append({
            "id": row[0],
            "name": row[1],
            "tree": row[2],
            "slot": row[3],
            "is_keystone": bool(row[4]),
            "description": row[5]
        })
    return runes

TOOL_DEFINITIONS = [
    {
        "name": "search_champions",
        "description": "Search for League of Legends champions by name or role. Use this when a player asks about a specific champion or wants to know champions for a role.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Champion name or partial name (e.g., 'Jinx', 'Yi')"
                },
                "role": {
                    "type": "string",
                    "description": "Champion role: Marksman, Fighter, Mage, Tank, Support, Assassin"
                }
            }
        }
    },
    {
        "name": "get_champion_details",
        "description": "Get detailed information about a specific champion including stats, abilities, and scaling. Use this when discussing champion mechanics, builds, or playstyle.",
        "input_schema": {
            "type": "object",
            "properties": {
                "champion_id": {
                    "type": "string",
                    "description": "Champion ID or name (e.g., 'Jinx', 'MasterYi')"
                }
            },
            "required": ["champion_id"]
        }
    },
    {
        "name": "search_items",
        "description": "Search for League of Legends items by name or tags. Use this when discussing itemization or build paths.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Item name or partial name (e.g., 'Infinity', 'Edge')"
                },
                "tags": {
                    "type": "string",
                    "description": "Item category: Damage, Tank, Support, CriticalStrike, AttackSpeed, etc."
                }
            }
        }
    },
    {
        "name": "get_item_details",
        "description": "Get detailed information about a specific item including all stats and build paths. Use this when explaining item efficiency or synergies.",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_id": {
                    "type": "integer",
                    "description": "Item ID number"
                }
            },
            "required": ["item_id"]
        }
    },
    {
        "name": "get_recommended_build",
        "description": "Get recommended builds (items, runes, summoner spells) for a champion in a specific role. Use this when a player asks what to build or how to play a champion.",
        "input_schema": {
            "type": "object",
            "properties": {
                "champion_id": {
                    "type": "string",
                    "description": "Champion ID or name"
                },
                "role": {
                    "type": "string",
                    "description": "Role: ADC, Top, Mid, Jungle, Support (optional)"
                }
            },
            "required": ["champion_id"]
        }
    },
    {
        "name": "get_champion_counters",
        "description": "Get information about which champions counter a specific champion. Use this when discussing matchups or lane opponents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "champion_id": {
                    "type": "string",
                    "description": "Champion ID or name"
                }
            },
            "required": ["champion_id"]
        }
    },
    {
        "name": "search_runes",
        "description": "Search for runes by name or tree. Use this when discussing rune choices or explaining rune effects.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Rune name or partial name"
                },
                "tree": {
                    "type": "string",
                    "description": "Rune tree: Precision, Domination, Sorcery, Resolve, Inspiration"
                },
                "keystone_only": {
                    "type": "boolean",
                    "description": "Set to true to only search keystones"
                }
            }
        }
    }
]

def execute_tool(tool_name: str, tool_input: dict):
    """
    Execute a tool by name with the provided input.

    Args:
        tool_name: Name of the tool to execute
        tool_input: Dictionary of input parameters

    Returns:
        Tool execution result
    """
    tool_functions = {
        "search_champions": search_champions,
        "get_champion_details": get_champion_details,
        "search_items": search_items,
        "get_item_details": get_item_details,
        "get_recommended_build": get_recommended_build,
        "get_champion_counters": get_champion_counters,
        "search_runes": search_runes
    }
    if tool_name not in tool_functions:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        result = tool_functions[tool_name](**tool_input)
        return result
    except Exception as e:
        return {"error": str(e)}
