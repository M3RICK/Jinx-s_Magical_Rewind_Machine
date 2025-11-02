from datetime import datetime
from .role_metrics import aggregate_role_metrics
from .laning_phase import aggregate_trading_stats, aggregate_wave_management_stats


def calculate_basic_stats(processed_stats):
    total_games = len(processed_stats)
    wins = sum(1 for s in processed_stats if s["win"])

    return {
        "total_games": total_games,
        "wins": wins,
        "losses": total_games - wins,
        "win_rate": round(wins / total_games, 3),
        "avg_kda": round(sum(s["kda"] for s in processed_stats) / total_games, 2),
        "avg_kills": round(sum(s["kills"] for s in processed_stats) / total_games, 2),
        "avg_deaths": round(sum(s["deaths"] for s in processed_stats) / total_games, 2),
        "avg_assists": round(sum(s["assists"] for s in processed_stats) / total_games, 2),
        "avg_kill_participation": round(
            sum(s.get("kill_participation", 0) for s in processed_stats) / total_games, 3
        ),
        "avg_damage_share": round(
            sum(s.get("damage_share", 0) for s in processed_stats) / total_games, 3
        ),
    }


def calculate_farming_stats(processed_stats):
    total_games = len(processed_stats)

    return {
        "avg_cs_per_min": round(
            sum(s["cs_per_min"] for s in processed_stats) / total_games, 2
        ),
        "avg_total_cs": round(
            sum(s["total_minions_killed"] + s["neutral_minions_killed"] for s in processed_stats) / total_games, 1
        ),
    }


def calculate_vision_stats(processed_stats):
    total_games = len(processed_stats)

    return {
        "avg_vision_score": round(
            sum(s["vision_score"] for s in processed_stats) / total_games, 1
        ),
        "avg_wards_placed": round(
            sum(s["wards_placed"] for s in processed_stats) / total_games, 1
        ),
        "avg_control_wards": round(
            sum(s["control_wards_placed"] for s in processed_stats) / total_games, 1
        ),
    }


def calculate_damage_stats(processed_stats):
    total_games = len(processed_stats)

    return {
        "avg_damage_per_min": round(
            sum(s["damage_per_min"] for s in processed_stats) / total_games, 0
        ),
        "avg_total_damage": round(
            sum(s["total_damage_to_champions"] for s in processed_stats) / total_games, 0
        ),
    }


def calculate_early_game_stats(processed_stats):
    stats_with_cs10 = [s for s in processed_stats if "cs_at_10" in s and s["cs_at_10"] > 0]
    stats_with_gold_diff = [s for s in processed_stats if "gold_diff_at_15" in s and s["gold_diff_at_15"] != 0]

    total_games = len(processed_stats)
    first_blood_participations = sum(
        1 for s in processed_stats if s.get("first_blood_kill") or s.get("first_blood_assist")
    )
    first_tower_participations = sum(
        1 for s in processed_stats if s.get("first_tower_kill") or s.get("first_tower_assist")
    )

    early_game = {
        "first_blood_participation_rate": round(first_blood_participations / total_games, 3),
        "first_tower_participation_rate": round(first_tower_participations / total_games, 3),
    }

    if stats_with_cs10:
        count = len(stats_with_cs10)
        early_game["avg_cs_at_10"] = round(sum(s["cs_at_10"] for s in stats_with_cs10) / count, 1)
        early_game["avg_gold_at_10"] = round(sum(s["gold_at_10"] for s in stats_with_cs10) / count, 0)

    if stats_with_gold_diff:
        count = len(stats_with_gold_diff)
        early_game["avg_gold_diff_at_15"] = round(
            sum(s["gold_diff_at_15"] for s in stats_with_gold_diff) / count, 0
        )

    return early_game


def calculate_champion_performance(processed_stats):
    champion_stats = {}
    for stat in processed_stats:
        champ_id = stat["champion_id"]
        if champ_id not in champion_stats:
            champion_stats[champ_id] = {
                "champion_name": stat["champion_name"],
                "games": 0,
                "wins": 0,
                "total_kda": 0,
                "total_cs_per_min": 0,
            }

        champion_stats[champ_id]["games"] += 1
        if stat["win"]:
            champion_stats[champ_id]["wins"] += 1
        champion_stats[champ_id]["total_kda"] += stat["kda"]
        champion_stats[champ_id]["total_cs_per_min"] += stat["cs_per_min"]

    champion_performance = []
    for champ_id, data in champion_stats.items():
        champion_performance.append({
            "champion_id": champ_id,
            "champion_name": data["champion_name"],
            "games": data["games"],
            "win_rate": round(data["wins"] / data["games"], 3),
            "avg_kda": round(data["total_kda"] / data["games"], 2),
            "avg_cs_per_min": round(data["total_cs_per_min"] / data["games"], 2),
        })

    champion_performance.sort(key=lambda x: x["games"], reverse=True)
    return champion_performance


def calculate_role_distribution(processed_stats):
    role_counts = {}
    for stat in processed_stats:
        role = stat["role"]
        role_counts[role] = role_counts.get(role, 0) + 1

    primary_role = max(role_counts, key=role_counts.get) if role_counts else "UNKNOWN"
    return role_counts, primary_role


def calculate_monthly_trends(processed_stats):
    monthly_performance = {}

    for stat in processed_stats:
        if "game_creation" in stat:
            date = datetime.fromtimestamp(stat["game_creation"] / 1000)
            month_key = date.strftime("%Y-%m")

            if month_key not in monthly_performance:
                monthly_performance[month_key] = {
                    "games": 0,
                    "wins": 0,
                    "total_kda": 0,
                }

            monthly_performance[month_key]["games"] += 1
            if stat["win"]:
                monthly_performance[month_key]["wins"] += 1
            monthly_performance[month_key]["total_kda"] += stat["kda"]

    for month, data in monthly_performance.items():
        data["win_rate"] = round(data["wins"] / data["games"], 3)
        data["avg_kda"] = round(data["total_kda"] / data["games"], 2)

    return dict(sorted(monthly_performance.items()))


def calculate_lane_dominance_stats(processed_stats):
    total_games = len(processed_stats)

    return {
        "avg_solo_kills": round(
            sum(s.get("solo_kills", 0) for s in processed_stats) / total_games, 2
        ),
        "avg_turret_plates": round(
            sum(s.get("turret_plates_taken", 0) for s in processed_stats) / total_games, 2
        ),
        "avg_cs_advantage": round(
            sum(s.get("max_cs_advantage_lane", 0) for s in processed_stats) / total_games, 1
        ),
        "avg_level_lead": round(
            sum(s.get("max_level_lead_lane", 0) for s in processed_stats) / total_games, 2
        ),
    }


def calculate_utility_stats(processed_stats):
    total_games = len(processed_stats)

    return {
        "avg_time_spent_dead": round(
            sum(s.get("total_time_spent_dead", 0) for s in processed_stats) / total_games, 1
        ),
        "avg_time_ccing_others": round(
            sum(s.get("time_ccing_others", 0) for s in processed_stats) / total_games, 1
        ),
        "avg_total_heal": round(
            sum(s.get("total_heal", 0) for s in processed_stats) / total_games, 0
        ),
        "avg_heals_on_teammates": round(
            sum(s.get("total_heals_on_teammates", 0) for s in processed_stats) / total_games, 0
        ),
        "avg_damage_shielded_on_teammates": round(
            sum(s.get("total_damage_shielded_on_teammates", 0) for s in processed_stats) / total_games, 0
        ),
        "avg_longest_time_living": round(
            sum(s.get("longest_time_spent_living", 0) for s in processed_stats) / total_games, 1
        ),
    }


def calculate_economic_stats(processed_stats):
    total_games = len(processed_stats)

    return {
        "avg_gold_spent": round(
            sum(s.get("gold_spent", 0) for s in processed_stats) / total_games, 0
        ),
        "avg_gold_efficiency": round(
            sum(
                s.get("total_damage_to_champions", 0) / max(s.get("gold_earned", 1), 1)
                for s in processed_stats
            ) / total_games, 2
        ),
    }


def calculate_objective_stats(processed_stats):
    total_games = len(processed_stats)

    return {
        "avg_baron_takedowns": round(
            sum(s.get("baron_takedowns", 0) for s in processed_stats) / total_games, 2
        ),
        "avg_dragon_takedowns": round(
            sum(s.get("dragon_takedowns", 0) for s in processed_stats) / total_games, 2
        ),
        "avg_herald_takedowns": round(
            sum(s.get("rift_herald_takedowns", 0) for s in processed_stats) / total_games, 2
        ),
        "avg_epic_monster_steals": round(
            sum(s.get("epic_monster_steals", 0) for s in processed_stats) / total_games, 2
        ),
    }


def calculate_summoner_spell_stats(processed_stats):
    total_games = len(processed_stats)

    return {
        "avg_summoner1_casts": round(
            sum(s.get("summoner1_casts", 0) for s in processed_stats) / total_games, 1
        ),
        "avg_summoner2_casts": round(
            sum(s.get("summoner2_casts", 0) for s in processed_stats) / total_games, 1
        ),
    }


def calculate_macro_stats(processed_stats):
    stats_with_timeline = [s for s in processed_stats if "death_events" in s]
    total_games = len(processed_stats)

    if not stats_with_timeline:
        return {}

    all_death_events = []
    for stat in stats_with_timeline:
        all_death_events.extend(stat.get("death_events", []))

    death_timing = {
        "0-10min": 0,
        "10-20min": 0,
        "20-30min": 0,
        "30min+": 0,
    }

    for death in all_death_events:
        timestamp = death.get("timestamp", 0)
        if timestamp <= 10:
            death_timing["0-10min"] += 1
        elif timestamp <= 20:
            death_timing["10-20min"] += 1
        elif timestamp <= 30:
            death_timing["20-30min"] += 1
        else:
            death_timing["30min+"] += 1

    total_clustered = sum(s.get("clustered_deaths", 0) for s in stats_with_timeline)
    total_deaths = sum(len(s.get("death_events", [])) for s in stats_with_timeline)
    objective_deaths_total = sum(s.get("objective_deaths_count", 0) for s in stats_with_timeline)
    objective_throws_total = sum(s.get("objective_throws_count", 0) for s in stats_with_timeline)

    stats_with_turrets = [s for s in stats_with_timeline if "turret_events" in s]
    turret_participation = 0
    turret_lost = 0
    if stats_with_turrets:
        for stat in stats_with_turrets:
            for turret_event in stat.get("turret_events", []):
                if turret_event.get("team") == "ally" and turret_event.get("assisted"):
                    turret_participation += 1
                elif turret_event.get("team") == "enemy":
                    turret_lost += 1

    return {
        "death_analysis": {
            "death_timing": death_timing,
            "avg_deaths_per_game": round(
                sum(s["deaths"] for s in processed_stats) / total_games, 2
            ),
            "clustered_deaths": total_clustered,
            "death_clusters": sum(s.get("death_clusters", 0) for s in stats_with_timeline),
            "total_deaths": total_deaths,
            "objective_deaths": objective_deaths_total,
            "objective_deaths_percentage": round(
                (objective_deaths_total / total_deaths * 100) if total_deaths > 0 else 0, 1
            ),
            "objective_throws_count": objective_throws_total,
            "avg_objective_throws_per_game": round(
                objective_throws_total / len(stats_with_timeline), 2
            ),
        },
        "tower_participation": {
            "avg_tower_assists_per_game": round(
                turret_participation / len(stats_with_turrets), 2
            ) if stats_with_turrets else 0,
            "avg_towers_lost_per_game": round(
                turret_lost / len(stats_with_turrets), 2
            ) if stats_with_turrets else 0,
        },
    }


def calculate_enhanced_early_game_stats(processed_stats):
    stats_with_cs10 = [s for s in processed_stats if "cs_at_10" in s and s["cs_at_10"] > 0]
    stats_with_xp_diff = [s for s in processed_stats if "xp_diff_at_15" in s and s.get("xp_diff_at_15") is not None]

    total_games = len(processed_stats)

    early_game = {
        "avg_takedowns_first_10_min": round(
            sum(s.get("takedowns_first_10_minutes", 0) for s in processed_stats) / total_games, 2
        ),
    }

    if stats_with_cs10:
        count = len(stats_with_cs10)
        if "gold_diff_at_10" in stats_with_cs10[0]:
            early_game["avg_gold_diff_at_10"] = round(
                sum(s.get("gold_diff_at_10", 0) for s in stats_with_cs10) / count, 0
            )
        if "xp_diff_at_10" in stats_with_cs10[0]:
            early_game["avg_xp_diff_at_10"] = round(
                sum(s.get("xp_diff_at_10", 0) for s in stats_with_cs10) / count, 0
            )

    if stats_with_xp_diff:
        count = len(stats_with_xp_diff)
        early_game["avg_xp_diff_at_15"] = round(
            sum(s.get("xp_diff_at_15", 0) for s in stats_with_xp_diff) / count, 0
        )

    return early_game


def get_role_performance(processed_stats, role_counts):
    role_performance = {}
    for role, count in role_counts.items():
        if count >= 3:
            role_matches = [m for m in processed_stats if m["role"] == role]
            role_wins = sum(1 for m in role_matches if m["win"])
            role_kda = sum(m["kda"] for m in role_matches)
            role_cs = sum(m["cs_per_min"] for m in role_matches)

            role_performance[role] = {
                "games": count,
                "win_rate": round(role_wins / count, 3),
                "avg_kda": round(role_kda / count, 2),
                "avg_cs_per_min": round(role_cs / count, 2),
            }

    return role_performance


def calculate_contextual_performance(processed_stats):
    stats_with_gold_diff = [
        s for s in processed_stats
        if "gold_diff_at_15" in s and s.get("gold_diff_at_15") is not None
    ]

    if not stats_with_gold_diff:
        return {}

    ahead_games = [s for s in stats_with_gold_diff if s["gold_diff_at_15"] >= 300]
    behind_games = [s for s in stats_with_gold_diff if s["gold_diff_at_15"] <= -300]
    even_games = [s for s in stats_with_gold_diff if -300 < s["gold_diff_at_15"] < 300]

    contextual = {}

    if ahead_games:
        ahead_wins = sum(1 for g in ahead_games if g["win"])
        contextual["when_ahead"] = {
            "games": len(ahead_games),
            "win_rate": round(ahead_wins / len(ahead_games), 3),
            "avg_kda": round(sum(g["kda"] for g in ahead_games) / len(ahead_games), 2),
            "avg_gold_diff": round(sum(g["gold_diff_at_15"] for g in ahead_games) / len(ahead_games), 0),
        }

    if behind_games:
        behind_wins = sum(1 for g in behind_games if g["win"])
        contextual["when_behind"] = {
            "games": len(behind_games),
            "win_rate": round(behind_wins / len(behind_games), 3),
            "avg_kda": round(sum(g["kda"] for g in behind_games) / len(behind_games), 2),
            "avg_gold_diff": round(sum(g["gold_diff_at_15"] for g in behind_games) / len(behind_games), 0),
        }

    if even_games:
        even_wins = sum(1 for g in even_games if g["win"])
        contextual["when_even"] = {
            "games": len(even_games),
            "win_rate": round(even_wins / len(even_games), 3),
            "avg_kda": round(sum(g["kda"] for g in even_games) / len(even_games), 2),
        }

    return contextual


def aggregate_stats(processed_stats, puuid, game_name, tag_line, summoner_info, rank_info):
    if not processed_stats:
        return {}

    role_counts, primary_role = calculate_role_distribution(processed_stats)
    rank_string = get_rank_string(rank_info)

    basic_stats = calculate_basic_stats(processed_stats)
    farming_stats = calculate_farming_stats(processed_stats)
    vision_stats = calculate_vision_stats(processed_stats)
    damage_stats = calculate_damage_stats(processed_stats)
    early_game_stats = calculate_early_game_stats(processed_stats)
    enhanced_early_game_stats = calculate_enhanced_early_game_stats(processed_stats)
    lane_dominance_stats = calculate_lane_dominance_stats(processed_stats)
    utility_stats = calculate_utility_stats(processed_stats)
    economic_stats = calculate_economic_stats(processed_stats)
    objective_stats = calculate_objective_stats(processed_stats)
    summoner_spell_stats = calculate_summoner_spell_stats(processed_stats)
    macro_stats = calculate_macro_stats(processed_stats)
    champion_performance = calculate_champion_performance(processed_stats)
    monthly_trends = calculate_monthly_trends(processed_stats)
    role_performance = get_role_performance(processed_stats, role_counts)
    contextual_performance = calculate_contextual_performance(processed_stats)

    role_specific_analytics = {}
    for role in role_counts.keys():
        if role_counts[role] >= 3:
            role_metrics = aggregate_role_metrics(processed_stats, role)
            if role_metrics:
                role_specific_analytics[role] = role_metrics

    trading_stats = aggregate_trading_stats(processed_stats)
    wave_management_stats = aggregate_wave_management_stats(processed_stats, role=primary_role)

    aggregated = {
        "player_info": {
            "puuid": puuid,
            "game_name": game_name,
            "tag_line": tag_line,
            "summoner_level": summoner_info.get("summonerLevel") if summoner_info else 0,
            "total_games_analyzed": basic_stats["total_games"],
            "primary_role": primary_role,
            "rank": rank_string,
        },
        "role_distribution": role_counts,
        "overall_performance": basic_stats,
        "contextual_performance": contextual_performance,
        "early_game": early_game_stats,
        "enhanced_early_game": enhanced_early_game_stats,
        "farming": farming_stats,
        "vision": vision_stats,
        "damage": damage_stats,
        "lane_dominance": lane_dominance_stats,
        "utility": utility_stats,
        "economic_efficiency": economic_stats,
        "objective_control": objective_stats,
        "summoner_spells": summoner_spell_stats,
        "death_analysis": macro_stats.get("death_analysis", {}),
        "tower_participation": macro_stats.get("tower_participation", {}),
        "laning_phase": {
            "trading": trading_stats,
            "wave_management": wave_management_stats,
        },
        "champion_performance": champion_performance[:10],
        "monthly_trends": monthly_trends,
        "role_performance": role_performance,
        "role_specific_analytics": role_specific_analytics,
        "raw_match_stats": processed_stats,
    }

    return aggregated


def get_rank_string(rank_info):
    if rank_info:
        for queue in rank_info:
            if queue["queueType"] == "RANKED_SOLO_5x5":
                return f"{queue['tier']}_{queue['rank']}"
    return "UNRANKED"


def get_role_specific_stats(aggregated_stats, role=None):
    if not aggregated_stats:
        return None

    target_role = role or aggregated_stats["player_info"]["primary_role"]

    role_matches = [
        m
        for m in aggregated_stats["raw_match_stats"]
        if m["role"] == target_role
    ]

    if not role_matches:
        return None

    total = len(role_matches)
    wins = sum(1 for m in role_matches if m["win"])

    return {
        "role": target_role,
        "games": total,
        "win_rate": wins / total,
        "avg_kda": sum(m["kda"] for m in role_matches) / total,
        "avg_cs_per_min": sum(m["cs_per_min"] for m in role_matches) / total,
        "avg_vision_score": sum(m["vision_score"] for m in role_matches) / total,
        "avg_damage_per_min": sum(m["damage_per_min"] for m in role_matches)
        / total,
    }
