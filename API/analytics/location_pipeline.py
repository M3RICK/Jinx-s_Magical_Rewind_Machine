from typing import Dict, List, Optional
from .map_utils import (
    OBJECTIVE_LOCATIONS,
    calculate_distance,
    get_region,
    is_near_objective
)

# Mais quelle merveille cette pipeline de localisation, non?

MAP_AREAS = {
    'BARON_PIT': {
        'center': OBJECTIVE_LOCATIONS['BARON'],
        'radius': 2500,
        'relevant_metrics': ['teamfighting', 'objective_control', 'vision'],
        'event_types': ['CHAMPION_KILL', 'ELITE_MONSTER_KILL', 'WARD_PLACED', 'WARD_KILL']
    },
    'DRAGON_PIT': {
        'center': OBJECTIVE_LOCATIONS['DRAGON'],
        'radius': 2500,
        'relevant_metrics': ['teamfighting', 'objective_control', 'vision'],
        'event_types': ['CHAMPION_KILL', 'ELITE_MONSTER_KILL', 'WARD_PLACED', 'WARD_KILL']
    },
    'TOP_LANE': {
        'center': {'x': 3000, 'y': 12000},
        'radius': 4000,
        'relevant_metrics': ['laning', 'wave_management', 'trading'],
        'event_types': ['CHAMPION_KILL', 'BUILDING_KILL', 'LEVEL_UP']
    },
    'MID_LANE': {
        'center': {'x': 7410, 'y': 7410},
        'radius': 4000,
        'relevant_metrics': ['laning', 'wave_management', 'trading', 'roaming'],
        'event_types': ['CHAMPION_KILL', 'BUILDING_KILL', 'LEVEL_UP']
    },
    'BOT_LANE': {
        'center': {'x': 12000, 'y': 3000},
        'radius': 4000,
        'relevant_metrics': ['laning', 'wave_management', 'trading'],
        'event_types': ['CHAMPION_KILL', 'BUILDING_KILL', 'LEVEL_UP']
    },
    'BLUE_JUNGLE': {
        'center': {'x': 5000, 'y': 7000},
        'radius': 3500,
        'relevant_metrics': ['jungle_pathing', 'objective_control', 'vision'],
        'event_types': ['CHAMPION_KILL', 'ELITE_MONSTER_KILL', 'WARD_PLACED']
    },
    'RED_JUNGLE': {
        'center': {'x': 9820, 'y': 7820},
        'radius': 3500,
        'relevant_metrics': ['jungle_pathing', 'objective_control', 'vision'],
        'event_types': ['CHAMPION_KILL', 'ELITE_MONSTER_KILL', 'WARD_PLACED']
    },
}


def is_in_area(x: int, y: int, area_name: str) -> bool:
    if area_name not in MAP_AREAS:
        return False

    area = MAP_AREAS[area_name]
    center = area['center']
    radius = area['radius']

    distance = calculate_distance(x, y, center['x'], center['y'])
    return distance <= radius


def filter_events_by_location(
    timeline_frames: List[Dict],
    area_name: str,
    event_types: Optional[List[str]] = None
) -> List[Dict]:
    if area_name not in MAP_AREAS:
        return []

    area = MAP_AREAS[area_name]
    if event_types is None:
        event_types = area['event_types']

    filtered_events = []

    for frame in timeline_frames:
        if 'events' not in frame:
            continue

        timestamp = frame.get('timestamp', 0)

        for event in frame['events']:
            event_type = event.get('type')

            if event_type not in event_types:
                continue

            position = event.get('position', {})
            x = position.get('x', 0)
            y = position.get('y', 0)

            if x > 0 and y > 0 and is_in_area(x, y, area_name):
                filtered_events.append({
                    'timestamp': timestamp / 60000,  # en minutes
                    'event_type': event_type,
                    'position': {'x': x, 'y': y},
                    'area': area_name,
                    'raw_event': event
                })

    return filtered_events


def get_area_stats(
    timeline_frames: List[Dict],
    participant_id: int,
    area_name: str
) -> Dict:
    if area_name not in MAP_AREAS:
        return {}

    area = MAP_AREAS[area_name]
    events = filter_events_by_location(timeline_frames, area_name)

    participant_events = []
    for event_data in events:
        event = event_data['raw_event']

        if (event.get('participantId') == participant_id or
            event.get('victimId') == participant_id or
            event.get('killerId') == participant_id or
            participant_id in event.get('assistingParticipantIds', [])):
            participant_events.append(event_data)

    kills_in_area = sum(1 for e in participant_events
                       if e['event_type'] == 'CHAMPION_KILL' and
                       e['raw_event'].get('killerId') == participant_id)

    deaths_in_area = sum(1 for e in participant_events
                        if e['event_type'] == 'CHAMPION_KILL' and
                        e['raw_event'].get('victimId') == participant_id)

    assists_in_area = sum(1 for e in participant_events
                         if e['event_type'] == 'CHAMPION_KILL' and
                         participant_id in e['raw_event'].get('assistingParticipantIds', []))

    return {
        'area_name': area_name,
        'total_events': len(participant_events),
        'kills': kills_in_area,
        'deaths': deaths_in_area,
        'assists': assists_in_area,
        'kda': (kills_in_area + assists_in_area) / max(deaths_in_area, 1),
        'event_timeline': participant_events,
        'relevant_metrics': area['relevant_metrics']
    }


def aggregate_location_data(
    match_data: Dict,
    timeline_data: Dict,
    participant_id: int
) -> Dict:
    if not timeline_data or 'info' not in timeline_data or 'frames' not in timeline_data['info']:
        return {}

    frames = timeline_data['info']['frames']

    location_stats = {}
    for area_name in MAP_AREAS.keys():
        location_stats[area_name] = get_area_stats(frames, participant_id, area_name)

    return location_stats


def get_location_heatmap_data(
    processed_matches: List[Dict],
    area_name: Optional[str] = None
) -> Dict:
    heatmap = {
        'kills': [],
        'deaths': [],
        'assists': [],
        'objectives': []
    }

    for match in processed_matches:
        death_events = match.get('death_events', [])
        for death in death_events:
            x = death.get('x', 0)
            y = death.get('y', 0)

            if x > 0 and y > 0:
                if area_name is None or is_in_area(x, y, area_name):
                    heatmap['deaths'].append({
                        'x': x,
                        'y': y,
                        'timestamp': death.get('timestamp', 0)
                    })

    return heatmap


def create_location_pipeline(
    processed_stats: List[Dict],
    area_filter: Optional[str] = None
) -> Dict:
    # Ah oui, la fameuse pipeline qui fait tout le travail pendant que vous sirotez votre café
    pipeline_data = {
        'area_filter': area_filter,
        'areas_analyzed': list(MAP_AREAS.keys()) if not area_filter else [area_filter],
        'area_statistics': {},
        'heatmap_data': {},
        'summary': {}
    }

    areas_to_analyze = [area_filter] if area_filter else list(MAP_AREAS.keys())

    for area in areas_to_analyze:
        area_config = MAP_AREAS[area]

        total_kills = 0
        total_deaths = 0
        total_assists = 0
        total_events = 0

        for match in processed_stats:
            location_data = match.get('location_data', {}).get(area, {})
            total_kills += location_data.get('kills', 0)
            total_deaths += location_data.get('deaths', 0)
            total_assists += location_data.get('assists', 0)
            total_events += location_data.get('total_events', 0)

        games_analyzed = len(processed_stats)

        pipeline_data['area_statistics'][area] = {
            'avg_kills_per_game': round(total_kills / games_analyzed, 2) if games_analyzed > 0 else 0,
            'avg_deaths_per_game': round(total_deaths / games_analyzed, 2) if games_analyzed > 0 else 0,
            'avg_assists_per_game': round(total_assists / games_analyzed, 2) if games_analyzed > 0 else 0,
            'avg_events_per_game': round(total_events / games_analyzed, 2) if games_analyzed > 0 else 0,
            'kda': round((total_kills + total_assists) / max(total_deaths, 1), 2),
            'relevant_metrics': area_config['relevant_metrics']
        }

        pipeline_data['heatmap_data'][area] = get_location_heatmap_data(processed_stats, area)

    pipeline_data['summary'] = {
        'total_matches': len(processed_stats),
        'areas_with_activity': [
            area for area, stats in pipeline_data['area_statistics'].items()
            if stats['avg_events_per_game'] > 0
        ]
    }

    return pipeline_data
