from ..map_utils import get_region
from .zone_definitions import ROLE_TO_REGION


def count_deaths_in_region(matches, region_name):
    death_count = 0

    for match in matches:
        death_events = match.get('death_events', [])
        for death in death_events:
            death_region = get_region(death['x'], death['y'])
            if death_region == region_name:
                death_count += 1

    return death_count


def calculate_avg_time_in_region(matches, region_name):
    total_time_percent = 0
    region_match_count = 0

    for match in matches:
        role_stats = match.get('role_specific_stats', {})
        map_presence = role_stats.get('map_presence', {})
        region_dist = map_presence.get('region_distribution', {})

        time_in_region = region_dist.get(region_name, 0)
        if time_in_region > 0:
            total_time_percent += time_in_region
            region_match_count += 1

    if region_match_count == 0:
        return 0.0

    return round(total_time_percent / region_match_count, 1)


def count_role_matches(matches, region_name):
    match_count = 0

    for match in matches:
        player_role = match.get('role')
        if ROLE_TO_REGION.get(player_role) == region_name:
            match_count += 1

    return match_count


def extract_lane_performance(matches, region_name):
    if region_name not in ['TOP_LANE', 'MID_LANE', 'BOT_LANE']:
        return {}

    cs_at_10_list = []
    gold_diff_at_10_list = []
    kills_list = []
    deaths_list = []
    assists_list = []

    for match in matches:
        player_role = match.get('role')
        if ROLE_TO_REGION.get(player_role) == region_name:
            cs_at_10_list.append(match.get('cs_at_10', 0))
            gold_diff_at_10_list.append(match.get('gold_diff_at_10', 0))
            kills_list.append(match.get('kills', 0))
            deaths_list.append(match.get('deaths', 0))
            assists_list.append(match.get('assists', 0))

    if not cs_at_10_list:
        return {}

    return {
        'avg_cs_at_10': round(sum(cs_at_10_list) / len(cs_at_10_list), 1),
        'avg_gold_diff_at_10': round(sum(gold_diff_at_10_list) / len(gold_diff_at_10_list), 1),
        'avg_kills': round(sum(kills_list) / len(kills_list), 1),
        'avg_deaths': round(sum(deaths_list) / len(deaths_list), 1),
        'avg_assists': round(sum(assists_list) / len(assists_list), 1)
    }


def extract_region_zone_stats(matches, zone_id, zone_config):
    region_name = zone_config['region']
    total_matches = len(matches)

    deaths_in_region = count_deaths_in_region(matches, region_name)
    avg_time_spent = calculate_avg_time_in_region(matches, region_name)
    role_matches = count_role_matches(matches, region_name)
    lane_performance = extract_lane_performance(matches, region_name)

    return {
        'zone_id': zone_id,
        'zone_name': zone_config['name'],
        'total_matches': total_matches,
        'deaths_in_region': deaths_in_region,
        'avg_time_spent_percent': avg_time_spent,
        'matches_played_in_role': role_matches,
        'avg_deaths_per_match': round(deaths_in_region / total_matches, 2) if total_matches > 0 else 0,
        'lane_performance': lane_performance
    }
