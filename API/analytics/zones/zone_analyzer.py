from .zone_definitions import STORY_ZONES
from .objective_stats import extract_objective_zone_stats
from .region_stats import extract_region_zone_stats
from .overview_stats import extract_overview_stats


def extract_zone_stats(matches, zone_id):
    zone_config = STORY_ZONES.get(zone_id)
    if not zone_config:
        return {}

    if 'objective' in zone_config:
        return extract_objective_zone_stats(matches, zone_id, zone_config)
    elif 'region' in zone_config:
        return extract_region_zone_stats(matches, zone_id, zone_config)

    return {}


def extract_all_zones(matches):
    zone_stats = {}

    for zone_id in STORY_ZONES.keys():
        zone_stats[zone_id] = extract_zone_stats(matches, zone_id)

    zone_stats['intro'] = extract_overview_stats(matches)

    return zone_stats


def analyze_player_zones(processed_stats):
    return extract_all_zones(processed_stats)
