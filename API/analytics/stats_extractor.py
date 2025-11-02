from ..utils.helpers import detect_role
from .role_metrics import extract_role_metrics
from .map_utils import is_near_objective, OBJECTIVE_PROXIMITY_THRESHOLD
from .laning_phase import analyze_wave_management, analyze_trading_efficiency
from .location_pipeline import aggregate_location_data


def find_participant_data(match, puuid):
    # récup participant, team, role et adversaire
    my_participant = None
    my_team_id = None
    my_role = None
    opponent_champion = None

    for participant in match["info"]["participants"]:
        if participant["puuid"] == puuid:
            my_participant = participant
            my_team_id = participant["teamId"]
            my_role = detect_role(participant)

        if my_role and my_team_id:
            is_enemy = participant["teamId"] != my_team_id
            if is_enemy and detect_role(participant) == my_role:
                opponent_champion = participant["championName"]

    return my_participant, my_team_id, my_role, opponent_champion


def calculate_team_stats(participants, team_id):
    # kills et dégâts totaux de la team
    team_kills = 0
    team_damage = 0

    for participant in participants:
        if participant["teamId"] == team_id:
            team_kills += participant["kills"]
            team_damage += participant["totalDamageDealtToChampions"]

    return team_kills, team_damage


def extract_rune_data(participant):
    # extraction des runes
    perks = participant.get("perks")
    if not perks:
        return {
            "primary_rune_style": 0,
            "sub_rune_style": 0,
            "primary_rune_selections": [],
            "sub_rune_selections": []
        }

    styles = perks.get("styles", [])
    if not styles:
        return {
            "primary_rune_style": 0,
            "sub_rune_style": 0,
            "primary_rune_selections": [],
            "sub_rune_selections": []
        }

    primary_style = styles[0] if len(styles) > 0 else {}
    sub_style = styles[1] if len(styles) > 1 else {}

    return {
        "primary_rune_style": primary_style.get("style", 0),
        "sub_rune_style": sub_style.get("style", 0),
        "primary_rune_selections": [s.get("perk", 0) for s in primary_style.get("selections", [])],
        "sub_rune_selections": [s.get("perk", 0) for s in sub_style.get("selections", [])]
    }


def calculate_kill_participation(participant, team_kills, challenges):
    # participation aux kills
    kill_participation = challenges.get("killParticipation", 0)
    if kill_participation == 0 and team_kills > 0:
        player_kills = participant["kills"]
        player_assists = participant["assists"]
        kill_participation = (player_kills + player_assists) / team_kills
    return kill_participation


def calculate_damage_share(participant, team_damage, challenges):
    # part des dégâts de la team
    damage_share = challenges.get("teamDamagePercentage", 0)
    if damage_share == 0 and team_damage > 0:
        player_damage = participant["totalDamageDealtToChampions"]
        damage_share = player_damage / team_damage
    return damage_share


def extract_match_stats(match, puuid):
    # extraction stats joueur d'un match
    my_participant, my_team_id, my_role, opponent_champion = find_participant_data(match, puuid)

    if not my_participant:
        return None

    team_kills, team_damage = calculate_team_stats(match["info"]["participants"], my_team_id)
    challenges = my_participant.get("challenges", {})

    kill_participation = calculate_kill_participation(my_participant, team_kills, challenges)
    damage_share = calculate_damage_share(my_participant, team_damage, challenges)

    game_duration_minutes = match["info"]["gameDuration"] / 60
    total_cs = my_participant["totalMinionsKilled"] + my_participant["neutralMinionsKilled"]
    player_damage = my_participant["totalDamageDealtToChampions"]
    player_vision = my_participant["visionScore"]

    rune_data = extract_rune_data(my_participant)

    stats = {
        "match_id": match["metadata"]["matchId"],
        "game_duration": match["info"]["gameDuration"],
        "game_creation": match["info"]["gameCreation"],
        "game_end": match["info"]["gameEndTimestamp"],
        "queue_id": match["info"]["queueId"],
        "role": my_role,
        "champion_id": my_participant["championId"],
        "champion_name": my_participant["championName"],
        "win": my_participant["win"],
        "kills": my_participant["kills"],
        "deaths": my_participant["deaths"],
        "assists": my_participant["assists"],
        "kda": (
            (my_participant["kills"] + my_participant["assists"]) /
            max(my_participant["deaths"], 1)
        ),
        "total_minions_killed": my_participant["totalMinionsKilled"],
        "neutral_minions_killed": my_participant["neutralMinionsKilled"],
        "cs_per_min": total_cs / game_duration_minutes,
        "gold_earned": my_participant["goldEarned"],
        "gold_spent": my_participant.get("goldSpent", 0),
        "total_damage_to_champions": player_damage,
        "damage_per_min": player_damage / game_duration_minutes,
        "vision_score": player_vision,
        "wards_placed": my_participant["wardsPlaced"],
        "wards_killed": my_participant["wardsKilled"],
        "control_wards_placed": my_participant["detectorWardsPlaced"],
        "vision_score_per_min": player_vision / game_duration_minutes,
        "turret_kills": my_participant["turretKills"],
        "inhibitor_kills": my_participant["inhibitorKills"],
        "dragon_kills": my_participant.get("dragonKills", 0),
        "baron_kills": my_participant.get("baronKills", 0),
        "double_kills": my_participant["doubleKills"],
        "triple_kills": my_participant["tripleKills"],
        "quadra_kills": my_participant["quadraKills"],
        "penta_kills": my_participant["pentaKills"],
        "team_position": my_participant.get("teamPosition", "UNKNOWN"),
        "summoner_level": my_participant.get("summonerLevel", 0),
        "kill_participation": round(kill_participation, 3),
        "damage_share": round(damage_share, 3),
        "first_blood_kill": my_participant.get("firstBloodKill", False),
        "first_blood_assist": my_participant.get("firstBloodAssist", False),
        "first_tower_kill": my_participant.get("firstTowerKill", False),
        "first_tower_assist": my_participant.get("firstTowerAssist", False),
        "total_damage_taken": my_participant.get("totalDamageTaken", 0),
        "damage_self_mitigated": my_participant.get("damageSelfMitigated", 0),
        "solo_kills": challenges.get("soloKills", 0),
        "turret_plates_taken": challenges.get("turretPlatesTaken", 0),
        "turret_takedowns": my_participant.get("turretTakedowns", 0),
        "objectives_stolen": my_participant.get("objectivesStolen", 0),
        "gold_per_minute": challenges.get("goldPerMinute", 0),
        "vision_score_advantage_lane": challenges.get(
            "visionScoreAdvantageLaneOpponent",
            0
        ),
        "max_cs_advantage_lane": challenges.get(
            "maxCsAdvantageOnLaneOpponent",
            0
        ),
        "max_level_lead_lane": challenges.get(
            "maxLevelLeadLaneOpponent",
            0
        ),
        "opponent_champion": opponent_champion,
        "summoner1_id": my_participant.get("summoner1Id", 0),
        "summoner2_id": my_participant.get("summoner2Id", 0),
        "summoner1_casts": my_participant.get("summoner1Casts", 0),
        "summoner2_casts": my_participant.get("summoner2Casts", 0),
        **rune_data,
        "item0": my_participant.get("item0", 0),
        "item1": my_participant.get("item1", 0),
        "item2": my_participant.get("item2", 0),
        "item3": my_participant.get("item3", 0),
        "item4": my_participant.get("item4", 0),
        "item5": my_participant.get("item5", 0),
        "item6": my_participant.get("item6", 0),
        "time_ccing_others": my_participant.get("timeCCingOthers", 0),
        "total_time_cc_dealt": my_participant.get("totalTimeCCDealt", 0),
        "total_time_spent_dead": my_participant.get("totalTimeSpentDead", 0),
        "longest_time_spent_living": my_participant.get("longestTimeSpentLiving", 0),
        "total_heal": my_participant.get("totalHeal", 0),
        "total_heals_on_teammates": my_participant.get("totalHealsOnTeammates", 0),
        "total_damage_shielded_on_teammates": my_participant.get("totalDamageShieldedOnTeammates", 0),
        "rift_herald_takedowns": challenges.get("riftHeraldTakedowns", 0),
        "nexus_takedowns": my_participant.get("nexusTakedowns", 0),
        "nexus_kills": my_participant.get("nexusKills", 0),
        "game_ended_in_early_surrender": my_participant.get("gameEndedInEarlySurrender", False),
        "game_ended_in_surrender": my_participant.get("gameEndedInSurrender", False),
        "team_early_surrendered": my_participant.get("teamEarlySurrendered", False),
        "takedowns_first_10_minutes": challenges.get("takedownsFirst10Minutes", 0),
        "lane_minions_first_10_minutes": challenges.get("laneMinionsFirst10Minutes", 0),
        "early_laning_phase_gold_exp_advantage": challenges.get("earlyLaningPhaseGoldExpAdvantage", 0),
        "jungler_kills_early_jungle": challenges.get("junglerKillsEarlyJungle", 0),
        "epic_monster_steals": challenges.get("epicMonsterSteals", 0),
        "baron_takedowns": challenges.get("baronTakedowns", 0),
        "dragon_takedowns": challenges.get("dragonTakedowns", 0),
        "elder_dragon_kills": challenges.get("elderDragonKillsWithOpposingSoul", 0),
        "damage_per_minute_challenge": challenges.get("damagePerMinute", 0),
        "kda_challenge": challenges.get("kda", 0),
        "effective_heal_and_shielding": challenges.get("effectiveHealAndShielding", 0),
        "kill_after_hidden_with_ally": challenges.get("killAfterHiddenWithAlly", 0),
        "knocked_enemy_into_team_and_kill": challenges.get("knockEnemyIntoTeamAndKillThem", 0),
        "multi_kill_one_spell": challenges.get("multiKillOneSpell", 0),
        "pick_kill_with_ally": challenges.get("pickKillWithAlly", 0),
        "solo_baron_kills": challenges.get("soloBaronKills", 0),
        "solo_turrents": challenges.get("soloTurrents", 0),
        "takedowns_after_gaining_level_advantage": challenges.get("takedownsAfterGainingLevelAdvantage", 0),
        "teleport_takedowns": challenges.get("teleportTakedowns", 0),
        "three_wards_one_sweeper": challenges.get("threeWardsOneSweeperCount", 0),
        "vision_score_per_minute_challenge": challenges.get("visionScorePerMinute", 0),
        "wards_guarded": challenges.get("wardsGuarded", 0),
        "control_ward_time_coverage": challenges.get("controlWardTimeCoverageInRiverOrEnemyHalf", 0),
    }

    return stats


def extract_cs_and_gold_milestones(frames, participant_id, opponent_id):
    milestones = {
        "cs_at_10": 0,
        "gold_at_10": 0,
        "xp_at_10": 0,
        "level_at_10": 0,
        "cs_at_15": 0,
        "gold_at_15": 0,
        "xp_at_15": 0,
        "level_at_15": 0,
        "cs_at_20": 0,
        "gold_diff_at_10": 0,
        "gold_diff_at_15": 0,
        "xp_diff_at_10": 0,
        "xp_diff_at_15": 0,
        "cs_by_phase": {"0-10": 0, "10-20": 0, "20-30": 0},
    }

    cs_at_start = 0
    cs_at_10_mark = 0
    cs_at_20_mark = 0

    for frame in frames:
        timestamp_minutes = frame["timestamp"] / 60000
        participant_frame = frame["participantFrames"].get(str(participant_id))

        if not participant_frame:
            continue

        minions_killed = participant_frame["minionsKilled"]
        jungle_minions = participant_frame["jungleMinionsKilled"]
        current_cs = minions_killed + jungle_minions

        if timestamp_minutes <= 1:
            cs_at_start = current_cs

        if 9 <= timestamp_minutes <= 10:
            milestones["cs_at_10"] = current_cs
            milestones["gold_at_10"] = participant_frame["totalGold"]
            milestones["xp_at_10"] = participant_frame["xp"]
            milestones["level_at_10"] = participant_frame["level"]
            cs_at_10_mark = current_cs

            if opponent_id:
                opponent_frame = frame["participantFrames"].get(str(opponent_id))
                if opponent_frame:
                    milestones["gold_diff_at_10"] = (
                        participant_frame["totalGold"] - opponent_frame["totalGold"]
                    )
                    milestones["xp_diff_at_10"] = (
                        participant_frame["xp"] - opponent_frame["xp"]
                    )

        if 14 <= timestamp_minutes <= 15:
            milestones["cs_at_15"] = current_cs
            milestones["gold_at_15"] = participant_frame["totalGold"]
            milestones["xp_at_15"] = participant_frame["xp"]
            milestones["level_at_15"] = participant_frame["level"]

            if opponent_id:
                opponent_frame = frame["participantFrames"].get(str(opponent_id))
                if opponent_frame:
                    milestones["gold_diff_at_15"] = (
                        participant_frame["totalGold"] - opponent_frame["totalGold"]
                    )
                    milestones["xp_diff_at_15"] = (
                        participant_frame["xp"] - opponent_frame["xp"]
                    )

        if 19 <= timestamp_minutes <= 20:
            milestones["cs_at_20"] = current_cs
            cs_at_20_mark = current_cs

    milestones["cs_by_phase"]["0-10"] = cs_at_10_mark - cs_at_start
    milestones["cs_by_phase"]["10-20"] = cs_at_20_mark - cs_at_10_mark
    milestones["cs_by_phase"]["20-30"] = milestones["cs_at_20"]

    return milestones


def extract_death_events(frames, participant_id):
    death_events = []

    for frame in frames:
        if "events" not in frame:
            continue

        timestamp_minutes = frame["timestamp"] / 60000

        for event in frame["events"]:
            if event["type"] == "CHAMPION_KILL" and event.get("victimId") == participant_id:
                position = event.get("position", {})
                death_x = position.get("x", 0)
                death_y = position.get("y", 0)

                objective_proximity = None
                if death_x > 0 and death_y > 0:
                    objective_proximity = is_near_objective(death_x, death_y, threshold=OBJECTIVE_PROXIMITY_THRESHOLD)

                death_events.append({
                    "timestamp": timestamp_minutes,
                    "x": death_x,
                    "y": death_y,
                    "killer_id": event.get("killerId"),
                    "assisting_participants": event.get("assistingParticipantIds", []),
                    "near_objective": objective_proximity.get("near_objective") if objective_proximity else False,
                    "objective_name": objective_proximity.get("objective_name") if objective_proximity else None,
                    "objective_distance": objective_proximity.get("distance") if objective_proximity else None,
                })

    return death_events


def calculate_death_metrics(death_events):
    deaths_0_10 = sum(1 for d in death_events if d["timestamp"] <= 10)
    deaths_10_20 = sum(1 for d in death_events if 10 < d["timestamp"] <= 20)
    deaths_20_30 = sum(1 for d in death_events if 20 < d["timestamp"] <= 30)
    deaths_30_plus = sum(1 for d in death_events if d["timestamp"] > 30)

    death_timing = {
        "0-10min": deaths_0_10,
        "10-20min": deaths_10_20,
        "20-30min": deaths_20_30,
        "30min+": deaths_30_plus,
    }

    death_clusters = []
    if len(death_events) >= 2:
        sorted_deaths = sorted(death_events, key=lambda x: x["timestamp"])
        for i in range(len(sorted_deaths) - 1):
            time_diff = sorted_deaths[i + 1]["timestamp"] - sorted_deaths[i]["timestamp"]
            if time_diff <= 2:
                death_clusters.append({"time": sorted_deaths[i]["timestamp"], "count": 2})

    clustered_count = sum(c["count"] for c in death_clusters)

    objective_deaths = [d for d in death_events if d.get("near_objective")]
    objective_deaths_pct = len(objective_deaths) / len(death_events) if death_events else 0

    return {
        "death_timing": death_timing,
        "death_clusters": len(death_clusters),
        "clustered_deaths": clustered_count if death_clusters else 0,
        "objective_deaths_count": len(objective_deaths),
        "objective_deaths_percentage": objective_deaths_pct,
    }


def extract_item_completions(frames, participant_id):
    item_completions = []

    for frame in frames:
        if "events" not in frame:
            continue

        timestamp_minutes = frame["timestamp"] / 60000

        for event in frame["events"]:
            if (event["type"] == "ITEM_PURCHASED" and
                event.get("participantId") == participant_id):
                item_id = event.get("itemId", 0)
                if item_id >= 3000:
                    item_completions.append({
                        "item_id": item_id,
                        "timestamp": timestamp_minutes,
                    })

    return item_completions


def extract_objectives_and_turrets(frames, participant_id, team_id):
    objective_events = []
    turret_events = []

    for frame in frames:
        if "events" not in frame:
            continue

        timestamp_minutes = frame["timestamp"] / 60000

        for event in frame["events"]:
            if event["type"] == "ELITE_MONSTER_KILL":
                monster_type = event.get("monsterType", "")
                killer_team_id = event.get("killerTeamId")

                objective_events.append({
                    "type": monster_type,
                    "timestamp": timestamp_minutes,
                    "team": "ally" if killer_team_id == team_id else "enemy",
                    "killer_team_id": killer_team_id,
                })

            elif event["type"] == "BUILDING_KILL":
                building_type = event.get("buildingType", "")
                killer_id = event.get("killerId")
                team_id_building = event.get("teamId")

                if building_type == "TOWER_BUILDING":
                    turret_events.append({
                        "timestamp": timestamp_minutes,
                        "team": "ally" if team_id_building != team_id else "enemy",
                        "assisted": killer_id == participant_id or participant_id in event.get("assistingParticipantIds", []),
                    })

    return objective_events, turret_events


def calculate_objective_throws(objective_events, death_events):
    objective_throws = []

    for obj_event in objective_events:
        if obj_event["team"] == "enemy" and obj_event["type"] in ["BARON_NASHOR", "DRAGON", "RIFTHERALD"]:
            for death in death_events:
                time_diff = obj_event["timestamp"] - death["timestamp"]
                if 0 < time_diff <= 1.5:
                    objective_throws.append({
                        "death_time": death["timestamp"],
                        "objective_type": obj_event["type"],
                        "objective_time": obj_event["timestamp"],
                        "time_before_objective": round(time_diff, 2),
                    })

    return objective_throws


def extract_timeline_stats(match, timeline, puuid, role=None):
    my_participant = None
    participant_id = None
    team_id = None
    my_role = role
    opponent_id = None

    for participant in match["info"]["participants"]:
        if participant["puuid"] == puuid:
            my_participant = participant
            participant_id = participant["participantId"]
            team_id = participant["teamId"]
            if not my_role:
                my_role = detect_role(participant)

        if my_role and team_id:
            is_enemy = participant["teamId"] != team_id
            if is_enemy and detect_role(participant) == my_role:
                opponent_id = participant["participantId"]

    if not my_participant or not timeline:
        return None

    if "info" not in timeline or "frames" not in timeline["info"]:
        return None

    frames = timeline["info"]["frames"]

    milestones = extract_cs_and_gold_milestones(frames, participant_id, opponent_id)
    death_events = extract_death_events(frames, participant_id)
    death_metrics = calculate_death_metrics(death_events)
    item_completions = extract_item_completions(frames, participant_id)
    objective_events, turret_events = extract_objectives_and_turrets(frames, participant_id, team_id)
    objective_throws = calculate_objective_throws(objective_events, death_events)

    team_side = 'blue' if team_id == 100 else 'red'
    role_specific_stats = extract_role_metrics(
        match_data=match,
        timeline_data=timeline,
        participant_id=participant_id,
        role=my_role,
        team_side=team_side
    )

    wave_management = {}
    trading_analysis = {}
    if my_role and my_role != "JUNGLE":
        wave_management = analyze_wave_management(
            match_data=match,
            timeline_data=timeline,
            participant_id=participant_id,
            role=my_role,
            team_side=team_side,
            opponent_id=opponent_id,
            laning_end_time=14
        )

        trading_analysis = analyze_trading_efficiency(
            match_data=match,
            timeline_data=timeline,
            participant_id=participant_id,
            opponent_id=opponent_id,
            laning_end_time=14
        )

    location_data = aggregate_location_data(
        match_data=match,
        timeline_data=timeline,
        participant_id=participant_id
    )

    timeline_stats = {
        **milestones,
        "death_events": death_events,
        "item_completion_times": item_completions,
        "objective_events": objective_events,
        "turret_events": turret_events,
        "objective_throws": objective_throws,
        "objective_throws_count": len(objective_throws),
        "role_specific_stats": role_specific_stats,
        "wave_management": wave_management,
        "trading_analysis": trading_analysis,
        "location_data": location_data,
        **death_metrics,
    }

    return timeline_stats
