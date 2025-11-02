from typing import Dict, List
from .movement_tracker import (
    track_map_presence,
    analyze_roaming,
    analyze_early_lane_presence,
    calculate_jungle_time
)


def extract_role_metrics(match_data: Dict, timeline_data: Dict,
                        participant_id: int, role: str, team_side: str) -> Dict:
    metrics = {'role': role, 'participant_id': participant_id}

    metrics['map_presence'] = track_map_presence(timeline_data, participant_id)
    metrics['roaming'] = analyze_roaming(timeline_data, participant_id, role)
    metrics['early_lane_presence'] = analyze_early_lane_presence(timeline_data, participant_id, role)
    metrics['jungle_proximity'] = calculate_jungle_time(timeline_data, participant_id)

    return metrics


def aggregate_role_metrics(processed_matches: List[Dict], role: str) -> Dict:
    role_matches = [m for m in processed_matches if m.get('role') == role]
    if not role_matches:
        return {}

    total_roam_count = 0
    total_time_roaming = 0
    total_home_lane_time = 0
    total_early_lane_presence = 0

    region_totals = {'TOP_LANE': 0, 'MID_LANE': 0, 'BOT_LANE': 0, 'JUNGLE': 0, 'RIVER': 0}
    matches_with_timeline = 0

    for match in role_matches:
        role_stats = match.get('role_specific_stats', {})
        if not role_stats:
            continue

        matches_with_timeline += 1

        roaming = role_stats.get('roaming', {})
        total_roam_count += roaming.get('roam_count', 0)
        total_time_roaming += roaming.get('time_roaming_percent', 0)
        total_home_lane_time += roaming.get('time_in_lane_percent', 0)

        map_presence = role_stats.get('map_presence', {})
        region_dist = map_presence.get('region_distribution', {})
        for region, percent in region_dist.items():
            if region in region_totals:
                region_totals[region] += percent

        early = role_stats.get('early_lane_presence', {})
        total_early_lane_presence += early.get('early_lane_presence_percent', 0)

    if matches_with_timeline == 0:
        return {'games_with_timeline_data': 0}

    return {
        'games_analyzed': matches_with_timeline,
        'avg_roams_per_game': round(total_roam_count / matches_with_timeline, 2),
        'avg_time_roaming_percent': round(total_time_roaming / matches_with_timeline, 2),
        'avg_time_in_lane_percent': round(total_home_lane_time / matches_with_timeline, 2),
        'avg_early_lane_presence_percent': round(total_early_lane_presence / matches_with_timeline, 2),
        'avg_region_distribution': {
            region: round(total / matches_with_timeline, 2)
            for region, total in region_totals.items()
        }
    }
