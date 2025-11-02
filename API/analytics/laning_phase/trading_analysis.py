from typing import Dict, List, Optional
from ..map_utils import LANING_CHECKPOINTS


def analyze_trading_efficiency(
    match_data: Dict,
    timeline_data: Dict,
    participant_id: int,
    opponent_id: Optional[int] = None,
    laning_end_time: int = 14
) -> Dict:

    if not timeline_data or "info" not in timeline_data or "frames" not in timeline_data["info"]:
        return {}

    frames = timeline_data["info"]["frames"]

    participant = None
    opponent = None
    for p in match_data["info"]["participants"]:
        if p["participantId"] == participant_id:
            participant = p
        if opponent_id and p["participantId"] == opponent_id:
            opponent = p

    if not participant:
        return {}

    damage_trades = []
    last_damage_dealt = 0
    last_damage_taken = 0

    damage_at_checkpoints = {
        "5min": {},
        "10min": {},
        "14min": {}
    }

    for frame in frames:
        timestamp_minutes = frame["timestamp"] / 60000

        if timestamp_minutes > laning_end_time:
            break

        participant_frame = frame["participantFrames"].get(str(participant_id))
        if not participant_frame:
            continue

        damage_dealt = participant_frame.get("damageStats", {}).get("totalDamageDoneToChampions", 0)
        damage_taken = participant_frame.get("damageStats", {}).get("totalDamageTaken", 0)

        damage_dealt_delta = damage_dealt - last_damage_dealt
        damage_taken_delta = damage_taken - last_damage_taken

        if damage_dealt_delta > 0 or damage_taken_delta > 0:
            trade_efficiency = 0
            if damage_taken_delta > 0:
                trade_efficiency = damage_dealt_delta / damage_taken_delta
            elif damage_dealt_delta > 0:
                trade_efficiency = float('inf')

            damage_trades.append({
                "timestamp": timestamp_minutes,
                "damage_dealt": damage_dealt_delta,
                "damage_taken": damage_taken_delta,
                "trade_efficiency": trade_efficiency if trade_efficiency != float('inf') else 999,
                "total_damage_dealt": damage_dealt,
                "total_damage_taken": damage_taken
            })

        if LANING_CHECKPOINTS['5MIN_START'] <= timestamp_minutes <= LANING_CHECKPOINTS['5MIN_END']:
            damage_at_checkpoints["5min"] = {
                "damage_dealt": damage_dealt,
                "damage_taken": damage_taken,
                "timestamp": timestamp_minutes
            }
        elif LANING_CHECKPOINTS['10MIN_START'] <= timestamp_minutes <= LANING_CHECKPOINTS['10MIN_END']:
            damage_at_checkpoints["10min"] = {
                "damage_dealt": damage_dealt,
                "damage_taken": damage_taken,
                "timestamp": timestamp_minutes
            }
        elif LANING_CHECKPOINTS['14MIN_START'] <= timestamp_minutes <= laning_end_time:
            damage_at_checkpoints["14min"] = {
                "damage_dealt": damage_dealt,
                "damage_taken": damage_taken,
                "timestamp": timestamp_minutes
            }

        last_damage_dealt = damage_dealt
        last_damage_taken = damage_taken

    total_damage_dealt_in_lane = last_damage_dealt
    total_damage_taken_in_lane = last_damage_taken

    overall_trade_efficiency = 0
    if total_damage_taken_in_lane > 0:
        overall_trade_efficiency = total_damage_dealt_in_lane / total_damage_taken_in_lane

    opponent_trading = {}
    if opponent_id:
        opponent_damage_dealt = 0
        opponent_damage_taken = 0

        for frame in frames:
            timestamp_minutes = frame["timestamp"] / 60000
            if timestamp_minutes > laning_end_time:
                break

            opponent_frame = frame["participantFrames"].get(str(opponent_id))
            if opponent_frame:
                opponent_damage_dealt = opponent_frame.get("damageStats", {}).get("totalDamageDoneToChampions", 0)
                opponent_damage_taken = opponent_frame.get("damageStats", {}).get("totalDamageTaken", 0)

        opponent_trading = {
            "damage_dealt": opponent_damage_dealt,
            "damage_taken": opponent_damage_taken,
            "trade_efficiency": opponent_damage_dealt / opponent_damage_taken if opponent_damage_taken > 0 else 0
        }

    damage_self_mitigated = participant.get("damageSelfMitigated", 0)
    total_damage_to_champions = participant.get("totalDamageDealtToChampions", 0)
    total_damage_taken_full_game = participant.get("totalDamageTaken", 0)

    laning_damage_dealt_pct = 0
    if total_damage_to_champions > 0:
        laning_damage_dealt_pct = (total_damage_dealt_in_lane / total_damage_to_champions) * 100

    laning_damage_taken_pct = 0
    if total_damage_taken_full_game > 0:
        laning_damage_taken_pct = (total_damage_taken_in_lane / total_damage_taken_full_game) * 100

    return {
        "laning_phase_end": laning_end_time,
        "total_damage_dealt_in_lane": round(total_damage_dealt_in_lane, 1),
        "total_damage_taken_in_lane": round(total_damage_taken_in_lane, 1),
        "damage_differential": round(total_damage_dealt_in_lane - total_damage_taken_in_lane, 1),
        "trade_efficiency_ratio": round(overall_trade_efficiency, 2),
        "damage_dealt_per_minute_laning": round(total_damage_dealt_in_lane / laning_end_time, 1),
        "damage_taken_per_minute_laning": round(total_damage_taken_in_lane / laning_end_time, 1),
        "laning_damage_pct_of_total": round(laning_damage_dealt_pct, 1),
        "laning_damage_taken_pct_of_total": round(laning_damage_taken_pct, 1),
        "damage_trades_count": len(damage_trades),
        "damage_checkpoints": damage_at_checkpoints,
        "opponent_trading": opponent_trading,
        "damage_self_mitigated_full_game": damage_self_mitigated,
        "mitigation_ratio": round(damage_self_mitigated / total_damage_taken_full_game, 2) if total_damage_taken_full_game > 0 else 0
    }


def aggregate_trading_stats(processed_matches: List[Dict]) -> Dict:

    matches_with_trading = [
        m for m in processed_matches
        if "trading_analysis" in m and m["trading_analysis"]
    ]

    if not matches_with_trading:
        return {}

    total_games = len(matches_with_trading)

    total_trade_efficiency = sum(
        m["trading_analysis"].get("trade_efficiency_ratio", 0)
        for m in matches_with_trading
    )

    total_damage_dealt = sum(
        m["trading_analysis"].get("total_damage_dealt_in_lane", 0)
        for m in matches_with_trading
    )

    total_damage_taken = sum(
        m["trading_analysis"].get("total_damage_taken_in_lane", 0)
        for m in matches_with_trading
    )

    positive_trades = sum(
        1 for m in matches_with_trading
        if m["trading_analysis"].get("damage_differential", 0) > 0
    )

    return {
        "games_analyzed": total_games,
        "avg_trade_efficiency": round(total_trade_efficiency / total_games, 2),
        "avg_damage_dealt_in_lane": round(total_damage_dealt / total_games, 1),
        "avg_damage_taken_in_lane": round(total_damage_taken / total_games, 1),
        "avg_damage_differential": round((total_damage_dealt - total_damage_taken) / total_games, 1),
        "positive_trade_rate": round(positive_trades / total_games, 2),
        "avg_mitigation_ratio": round(
            sum(m["trading_analysis"].get("mitigation_ratio", 0) for m in matches_with_trading) / total_games,
            2
        )
    }
