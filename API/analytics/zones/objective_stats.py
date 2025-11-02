from ..map_utils import OBJECTIVE_LOCATIONS, calculate_distance, OBJECTIVE_PROXIMITY_THRESHOLD
from .zone_definitions import OBJECTIVE_TYPE_MAPPING


def count_deaths_near_objective(matches, objective_name, proximity):
    obj_location = OBJECTIVE_LOCATIONS.get(objective_name)
    if not obj_location:
        return 0, []

    death_count = 0
    death_details = []

    for match in matches:
        death_events = match.get('death_events', [])
        for death in death_events:
            dist = calculate_distance(
                death['x'], death['y'],
                obj_location['x'], obj_location['y']
            )

            if dist < proximity:
                death_count += 1
                death_details.append({
                    'timestamp': death.get('timestamp', 0),
                    'distance': round(dist, 1),
                    'match_id': match.get('match_id')
                })

    return death_count, death_details


def count_objective_control(matches, objective_name):
    secured = 0
    lost = 0

    event_type_match = OBJECTIVE_TYPE_MAPPING.get(objective_name)

    for match in matches:
        objective_events = match.get('objective_events', [])
        for event in objective_events:
            if event['type'] == event_type_match:
                if event.get('team') == 'ally':
                    secured += 1
                else:
                    lost += 1

    return secured, lost


def count_objective_participations(matches, objective_name):
    participation_count = 0

    stat_field_map = {
        'BARON': 'baron_takedowns',
        'DRAGON': 'dragon_takedowns',
        'RIFT_HERALD': 'rift_herald_takedowns'
    }

    field = stat_field_map.get(objective_name)
    if not field:
        return 0

    for match in matches:
        participation_count += match.get(field, 0)

    return participation_count


def calculate_objective_control_rate(secured, lost):
    total = secured + lost
    if total == 0:
        return 0.0
    return round(secured / total * 100, 1)


def extract_objective_zone_stats(matches, zone_id, zone_config):
    objective_name = zone_config['objective']
    proximity = zone_config.get('proximity', OBJECTIVE_PROXIMITY_THRESHOLD)

    deaths_near, death_details = count_deaths_near_objective(matches, objective_name, proximity)
    secured, lost = count_objective_control(matches, objective_name)
    participations = count_objective_participations(matches, objective_name)

    total_matches = len(matches)
    control_rate = calculate_objective_control_rate(secured, lost)

    return {
        'zone_id': zone_id,
        'zone_name': zone_config['name'],
        'total_matches': total_matches,
        'deaths_near': deaths_near,
        'death_details': death_details,
        'objectives_secured': secured,
        'objectives_lost': lost,
        'objective_control_rate': control_rate,
        'participated_in_fights': participations,
        'avg_deaths_per_match': round(deaths_near / total_matches, 2) if total_matches > 0 else 0
    }
