from typing import Dict, List
from .map_utils import get_region, calculate_distance, ROLE_HOME_REGIONS


def track_map_presence(timeline_data: Dict, participant_id: int) -> Dict:
    if not timeline_data or 'info' not in timeline_data:
        return {}

    frames = timeline_data['info'].get('frames', [])
    region_time = {'TOP_LANE': 0, 'MID_LANE': 0, 'BOT_LANE': 0, 'JUNGLE': 0, 'RIVER': 0}
    positions = []
    total_distance = 0

    for i, frame in enumerate(frames):
        if 'participantFrames' not in frame:
            continue

        participant_frame = frame['participantFrames'].get(str(participant_id))
        if not participant_frame or 'position' not in participant_frame:
            continue

        pos = participant_frame['position']
        x, y = pos.get('x', 0), pos.get('y', 0)

        if x == 0 and y == 0:
            continue

        region = get_region(x, y)
        region_time[region] += 1
        positions.append((x, y))

        if i > 0 and len(positions) >= 2:
            total_distance += calculate_distance(
                positions[-2][0], positions[-2][1],
                positions[-1][0], positions[-1][1]
            )

    total_frames = sum(region_time.values())
    if total_frames == 0:
        return {}

    region_percentages = {
        region: round((time / total_frames) * 100, 2)
        for region, time in region_time.items()
    }

    return {
        'region_distribution': region_percentages,
        'total_distance_traveled': round(total_distance, 2),
        'distance_per_minute': round(total_distance / max(total_frames, 1), 2),
        'frames_tracked': total_frames
    }


def analyze_roaming(timeline_data: Dict, participant_id: int, role: str) -> Dict:
    if not timeline_data or 'info' not in timeline_data or role not in ROLE_HOME_REGIONS:
        return {}

    frames = timeline_data['info'].get('frames', [])
    home_regions = ROLE_HOME_REGIONS[role]

    roam_count = 0
    in_roam = False
    frames_roaming = 0
    frames_home = 0

    for frame in frames:
        if 'participantFrames' not in frame:
            continue

        participant_frame = frame['participantFrames'].get(str(participant_id))
        if not participant_frame or 'position' not in participant_frame:
            continue

        pos = participant_frame['position']
        x, y = pos.get('x', 0), pos.get('y', 0)

        if x == 0 and y == 0:
            continue

        region = get_region(x, y)
        is_home = region in home_regions

        if is_home:
            frames_home += 1
            if in_roam:
                in_roam = False
        else:
            frames_roaming += 1
            if not in_roam:
                roam_count += 1
                in_roam = True

    total_frames = frames_home + frames_roaming
    if total_frames == 0:
        return {}

    return {
        'roam_count': roam_count,
        'time_in_lane_percent': round((frames_home / total_frames) * 100, 2),
        'time_roaming_percent': round((frames_roaming / total_frames) * 100, 2),
        'roams_per_10min': round((roam_count / total_frames) * 10, 2) if total_frames > 0 else 0
    }


def analyze_early_lane_presence(timeline_data: Dict, participant_id: int, role: str) -> Dict:
    if not timeline_data or 'info' not in timeline_data:
        return {}

    home_map = {'TOP': 'TOP_LANE', 'MIDDLE': 'MID_LANE', 'BOTTOM': 'BOT_LANE', 'UTILITY': 'BOT_LANE'}
    if role not in home_map:
        return {}

    frames = timeline_data['info'].get('frames', [])[:15]
    home_region = home_map[role]
    frames_in_lane = 0
    total_frames = 0

    for frame in frames:
        if 'participantFrames' not in frame:
            continue

        participant_frame = frame['participantFrames'].get(str(participant_id))
        if not participant_frame or 'position' not in participant_frame:
            continue

        pos = participant_frame['position']
        x, y = pos.get('x', 0), pos.get('y', 0)

        if x == 0 and y == 0:
            continue

        region = get_region(x, y)
        total_frames += 1

        if region == home_region:
            frames_in_lane += 1

    if total_frames == 0:
        return {}

    return {
        'early_lane_presence_percent': round((frames_in_lane / total_frames) * 100, 2)
    }


def calculate_jungle_time(timeline_data: Dict, participant_id: int) -> Dict:
    if not timeline_data or 'info' not in timeline_data:
        return {}

    frames = timeline_data['info'].get('frames', [])
    jungle_time = 0
    total_frames = 0

    for frame in frames:
        if 'participantFrames' not in frame:
            continue

        participant_frame = frame['participantFrames'].get(str(participant_id))
        if not participant_frame or 'position' not in participant_frame:
            continue

        pos = participant_frame['position']
        x, y = pos.get('x', 0), pos.get('y', 0)

        if x == 0 and y == 0:
            continue

        region = get_region(x, y)
        total_frames += 1

        if region == 'JUNGLE':
            jungle_time += 1

    if total_frames == 0:
        return {}

    return {
        'jungle_time_percent': round((jungle_time / total_frames) * 100, 2)
    }
