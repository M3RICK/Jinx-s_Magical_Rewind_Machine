from typing import Dict, List, Optional, Tuple
from ..map_utils import (
    LANE_POSITION_THRESHOLDS,
    FOUNTAIN_THRESHOLDS,
    RECALL_CONSTANTS,
)


def get_top_lane_zone(x: int, team_side: str) -> str:
    # zone top lane selon X
    early = LANE_POSITION_THRESHOLDS['EARLY_TOWER_X']
    late = LANE_POSITION_THRESHOLDS['LATE_TOWER_X']

    if team_side == "blue":
        if x < early:
            return "own_tower"
        elif x > late:
            return "enemy_tower"
        else:
            return "middle"
    else:
        if x > late:
            return "own_tower"
        elif x < early:
            return "enemy_tower"
        else:
            return "middle"


def get_mid_lane_zone(x: int, y: int, team_side: str) -> str:
    # zone mid lane en diagonale
    early_sum = LANE_POSITION_THRESHOLDS['MID_LANE_EARLY_SUM']
    late_sum = LANE_POSITION_THRESHOLDS['MID_LANE_LATE_SUM']
    position_sum = x + y

    if team_side == "blue":
        if position_sum < early_sum:
            return "own_tower"
        elif position_sum > late_sum:
            return "enemy_tower"
        else:
            return "middle"
    else:
        if position_sum > late_sum:
            return "own_tower"
        elif position_sum < early_sum:
            return "enemy_tower"
        else:
            return "middle"


def get_bot_lane_zone(y: int, team_side: str) -> str:
    # zone bot lane selon Y
    early = LANE_POSITION_THRESHOLDS['EARLY_TOWER_Y']
    late = LANE_POSITION_THRESHOLDS['LATE_TOWER_Y']

    if team_side == "blue":
        if y < early:
            return "own_tower"
        elif y > late:
            return "enemy_tower"
        else:
            return "middle"
    else:
        if y > late:
            return "own_tower"
        elif y < early:
            return "enemy_tower"
        else:
            return "middle"


def get_lane_position_zone(x: int, y: int, role: str, team_side: str) -> str:
    # détection zone lane
    if role == "TOP":
        return get_top_lane_zone(x, team_side)
    elif role == "MIDDLE":
        return get_mid_lane_zone(x, y, team_side)
    elif role == "BOTTOM":
        return get_bot_lane_zone(y, team_side)
    else:
        return "unknown"


def detect_wave_state(cs_rate: float, position_zone: str, time_in_zone: int) -> str:
    if position_zone == "own_tower" and time_in_zone > 45 and cs_rate < 7:
        return "freezing"

    if cs_rate > 9 and position_zone in ["middle", "enemy_tower"]:
        return "fast_push"

    if position_zone == "middle" and 6 < cs_rate < 9:
        return "slow_push"

    if position_zone == "enemy_tower" and time_in_zone < 30:
        return "crashed"

    if position_zone == "middle" and 5 < cs_rate < 8:
        return "neutral"

    return "unknown"


def analyze_recall_timing(
    frames: List[Dict],
    participant_id: int,
    laning_end_time: int = 14
) -> List[Dict]:
    recalls = []
    last_position = None
    last_gold = 0
    last_cs = 0
    position_history = []

    for frame in frames:
        timestamp_minutes = frame["timestamp"] / 60000
        if timestamp_minutes > laning_end_time:
            break

        participant_frame = frame["participantFrames"].get(str(participant_id))
        if not participant_frame:
            continue

        current_position = participant_frame.get("position", {})
        current_gold = participant_frame.get("totalGold", 0)
        current_cs = participant_frame.get("minionsKilled", 0) + participant_frame.get("jungleMinionsKilled", 0)

        position_history.append(current_position)
        if len(position_history) > 3:
            position_history.pop(0)

        if last_position:
            pos_x = current_position.get("x", 0)
            pos_y = current_position.get("y", 0)
            last_x = last_position.get("x", 0)
            last_y = last_position.get("y", 0)

            blue_max = FOUNTAIN_THRESHOLDS['BLUE_FOUNTAIN_MAX']
            red_min = FOUNTAIN_THRESHOLDS['RED_FOUNTAIN_MIN']

            at_fountain = (
                (pos_x < blue_max and pos_y < blue_max) or
                (pos_x > red_min and pos_y > red_min)
            )

            distance_moved = ((pos_x - last_x)**2 + (pos_y - last_y)**2)**0.5
            teleport_threshold = RECALL_CONSTANTS['TELEPORT_DISTANCE_THRESHOLD']

            if at_fountain or distance_moved > teleport_threshold:
                gold_on_recall = current_gold - last_gold
                cs_before_recall = last_cs

                recall_quality = "unknown"
                if gold_on_recall >= RECALL_CONSTANTS['GOOD_RECALL_GOLD']:
                    recall_quality = "good_gold"
                elif gold_on_recall >= RECALL_CONSTANTS['ACCEPTABLE_RECALL_GOLD']:
                    recall_quality = "acceptable"
                elif gold_on_recall < RECALL_CONSTANTS['EARLY_RECALL_GOLD']:
                    recall_quality = "early"

                recalls.append({
                    "timestamp": timestamp_minutes,
                    "gold_on_recall": gold_on_recall,
                    "cs_on_recall": cs_before_recall,
                    "recall_quality": recall_quality
                })

        last_position = current_position
        last_gold = current_gold
        last_cs = current_cs

    return recalls


def calculate_cs_differential_curve(
    frames: List[Dict],
    participant_id: int,
    opponent_id: Optional[int],
    laning_end_time: int = 14
) -> List[Dict]:
    # courbe de CS et diff au cours du temps
    cs_curve = []

    for frame in frames:
        timestamp_minutes = frame["timestamp"] / 60000
        if timestamp_minutes > laning_end_time:
            break

        participant_frame = frame["participantFrames"].get(str(participant_id))
        if not participant_frame:
            continue

        player_cs = (
            participant_frame.get("minionsKilled", 0) +
            participant_frame.get("jungleMinionsKilled", 0)
        )

        cs_diff = 0
        if opponent_id:
            opponent_frame = frame["participantFrames"].get(str(opponent_id))
            if opponent_frame:
                opponent_cs = (
                    opponent_frame.get("minionsKilled", 0) +
                    opponent_frame.get("jungleMinionsKilled", 0)
                )
                cs_diff = player_cs - opponent_cs

        cs_curve.append({
            "timestamp": round(timestamp_minutes, 1),
            "cs": player_cs,
            "cs_diff": cs_diff
        })

    return cs_curve


def track_zone_positioning(
    frames: List[Dict],
    participant_id: int,
    role: str,
    team_side: str,
    laning_end_time: int
) -> Dict:
    # suivi du temps par zone
    zone_time = {"own_tower": 0, "middle": 0, "enemy_tower": 0, "unknown": 0}
    wave_states = []
    current_zone = "unknown"
    zone_start_time = 0
    cs_window = []
    last_cs = 0

    for frame in frames:
        timestamp_minutes = frame["timestamp"] / 60000
        timestamp_seconds = frame["timestamp"] / 1000

        if timestamp_minutes > laning_end_time:
            break

        participant_frame = frame["participantFrames"].get(str(participant_id))
        if not participant_frame:
            continue

        position = participant_frame.get("position", {})
        pos_x = position.get("x", 0)
        pos_y = position.get("y", 0)

        current_cs = (
            participant_frame.get("minionsKilled", 0) +
            participant_frame.get("jungleMinionsKilled", 0)
        )

        if pos_x > 0 and pos_y > 0:
            zone = get_lane_position_zone(pos_x, pos_y, role, team_side)

            if zone != current_zone:
                time_in_zone = timestamp_seconds - zone_start_time
                zone_time[current_zone] = zone_time.get(current_zone, 0) + time_in_zone
                current_zone = zone
                zone_start_time = timestamp_seconds

            cs_window.append({"time": timestamp_minutes, "cs": current_cs})
            cs_window = [entry for entry in cs_window if timestamp_minutes - entry["time"] <= 2]

            cs_rate = 0
            if len(cs_window) >= 2:
                time_diff = cs_window[-1]["time"] - cs_window[0]["time"]
                cs_diff = cs_window[-1]["cs"] - cs_window[0]["cs"]
                if time_diff > 0:
                    cs_rate = cs_diff / time_diff

            time_in_current_zone = timestamp_seconds - zone_start_time
            wave_state = detect_wave_state(cs_rate, zone, time_in_current_zone)

            wave_states.append({
                "timestamp": timestamp_minutes,
                "zone": zone,
                "wave_state": wave_state,
                "cs_rate": round(cs_rate, 2)
            })

        last_cs = current_cs

    return {
        "zone_time": zone_time,
        "wave_states": wave_states
    }


def calculate_zone_percentages(zone_time: Dict) -> Dict:
    # pourcentages par zone
    total_time = sum(zone_time.values())
    return {
        zone: round((time / total_time * 100), 1) if total_time > 0 else 0
        for zone, time in zone_time.items()
    }


def calculate_wave_state_distribution(wave_states: List[Dict]) -> Dict:
    # distribution des états de wave
    wave_state_counts = {}
    for state_entry in wave_states:
        state = state_entry["wave_state"]
        wave_state_counts[state] = wave_state_counts.get(state, 0) + 1
    return wave_state_counts


def analyze_cs_trend(cs_curve: List[Dict]) -> str:
    # tendance CS: amélioration ou déclin
    cs_values = [entry["cs_diff"] for entry in cs_curve if entry["cs_diff"] != 0]

    if len(cs_curve) < 4:
        return "stable"

    midpoint = len(cs_curve) // 2
    early_avg = sum(entry["cs_diff"] for entry in cs_curve[:midpoint]) / midpoint
    late_avg = sum(entry["cs_diff"] for entry in cs_curve[midpoint:]) / midpoint

    if late_avg > early_avg + 5:
        return "improving"
    elif late_avg < early_avg - 5:
        return "declining"
    else:
        return "stable"


def analyze_wave_management(
    match_data: Dict,
    timeline_data: Dict,
    participant_id: int,
    role: str,
    team_side: str,
    opponent_id: Optional[int] = None,
    laning_end_time: int = 14
) -> Dict:
    # analyse complète wave management
    if not timeline_data or "info" not in timeline_data or "frames" not in timeline_data["info"]:
        return {}

    frames = timeline_data["info"]["frames"]

    zone_data = track_zone_positioning(frames, participant_id, role, team_side, laning_end_time)
    zone_time = zone_data["zone_time"]
    wave_states = zone_data["wave_states"]

    recalls = analyze_recall_timing(frames, participant_id, laning_end_time)
    cs_curve = calculate_cs_differential_curve(frames, participant_id, opponent_id, laning_end_time)

    zone_percentages = calculate_zone_percentages(zone_time)
    wave_state_counts = calculate_wave_state_distribution(wave_states)
    cs_trend = analyze_cs_trend(cs_curve)

    cs_values = [entry["cs_diff"] for entry in cs_curve if entry["cs_diff"] != 0]
    avg_cs_diff = sum(cs_values) / len(cs_values) if cs_values else 0

    return {
        "laning_end_time": laning_end_time,
        "zone_time_percentages": zone_percentages,
        "time_near_enemy_tower": zone_time["enemy_tower"],
        "time_near_own_tower": zone_time["own_tower"],
        "wave_state_distribution": wave_state_counts,
        "recalls_during_laning": recalls,
        "recall_count": len(recalls),
        "avg_gold_on_recall": round(
            sum(r["gold_on_recall"] for r in recalls) / len(recalls), 0
        ) if recalls else 0,
        "good_recalls": sum(1 for r in recalls if r["recall_quality"] == "good_gold"),
        "early_recalls": sum(1 for r in recalls if r["recall_quality"] == "early"),
        "cs_differential_curve": cs_curve,
        "avg_cs_differential": round(avg_cs_diff, 1),
        "cs_trend": cs_trend,
        "lane_pressure_score": round(
            zone_percentages.get("enemy_tower", 0) - zone_percentages.get("own_tower", 0), 1
        )
    }


def aggregate_wave_management_stats(processed_matches: List[Dict], role: str = None) -> Dict:

    matches_with_wave_data = [
        m for m in processed_matches
        if "wave_management" in m and m["wave_management"]
        and (role is None or m.get("role") == role)
    ]

    if not matches_with_wave_data:
        return {}

    total_games = len(matches_with_wave_data)

    total_lane_pressure = sum(
        m["wave_management"].get("lane_pressure_score", 0)
        for m in matches_with_wave_data
    )

    total_recalls = sum(
        m["wave_management"].get("recall_count", 0)
        for m in matches_with_wave_data
    )

    total_good_recalls = sum(
        m["wave_management"].get("good_recalls", 0)
        for m in matches_with_wave_data
    )

    total_early_recalls = sum(
        m["wave_management"].get("early_recalls", 0)
        for m in matches_with_wave_data
    )

    avg_zone_percentages = {
        "own_tower": 0,
        "middle": 0,
        "enemy_tower": 0,
        "unknown": 0
    }

    for match in matches_with_wave_data:
        zone_pcts = match["wave_management"].get("zone_time_percentages", {})
        for zone, pct in zone_pcts.items():
            avg_zone_percentages[zone] += pct

    for zone in avg_zone_percentages:
        avg_zone_percentages[zone] = round(avg_zone_percentages[zone] / total_games, 1)

    return {
        "games_analyzed": total_games,
        "avg_lane_pressure_score": round(total_lane_pressure / total_games, 1),
        "avg_recalls_per_game": round(total_recalls / total_games, 1),
        "recall_efficiency": round(
            (total_good_recalls / total_recalls * 100) if total_recalls > 0 else 0, 1
        ),
        "early_recall_rate": round(
            (total_early_recalls / total_recalls * 100) if total_recalls > 0 else 0, 1
        ),
        "avg_zone_distribution": avg_zone_percentages,
        "avg_cs_differential": round(
            sum(m["wave_management"].get("avg_cs_differential", 0) for m in matches_with_wave_data) / total_games,
            1
        )
    }
