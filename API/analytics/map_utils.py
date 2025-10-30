import math

MAP_SIZE = 14820

MAP_REGIONS = {
    'TOP_LANE': {'x_min': 0, 'x_max': 6000, 'y_min': 10000, 'y_max': MAP_SIZE},
    'MID_LANE': {'x_min': 4000, 'x_max': 10820, 'y_min': 4000, 'y_max': 10820},
    'BOT_LANE': {'x_min': 10000, 'x_max': MAP_SIZE, 'y_min': 0, 'y_max': 6000},
    'RIVER': {'x_min': 6000, 'x_max': 8820, 'y_min': 6000, 'y_max': 8820}
}

ROLE_HOME_REGIONS = {
    'TOP': ['TOP_LANE'],
    'MIDDLE': ['MID_LANE'],
    'BOTTOM': ['BOT_LANE'],
    'UTILITY': ['BOT_LANE', 'RIVER', 'JUNGLE'],
    'JUNGLE': ['JUNGLE', 'RIVER']
}


def get_region(x: int, y: int) -> str:
    if (MAP_REGIONS['TOP_LANE']['x_min'] <= x <= MAP_REGIONS['TOP_LANE']['x_max'] and
        MAP_REGIONS['TOP_LANE']['y_min'] <= y <= MAP_REGIONS['TOP_LANE']['y_max']):
        return 'TOP_LANE'

    if (MAP_REGIONS['BOT_LANE']['x_min'] <= x <= MAP_REGIONS['BOT_LANE']['x_max'] and
        MAP_REGIONS['BOT_LANE']['y_min'] <= y <= MAP_REGIONS['BOT_LANE']['y_max']):
        return 'BOT_LANE'

    if (MAP_REGIONS['MID_LANE']['x_min'] <= x <= MAP_REGIONS['MID_LANE']['x_max'] and
        MAP_REGIONS['MID_LANE']['y_min'] <= y <= MAP_REGIONS['MID_LANE']['y_max']):
        return 'MID_LANE'

    if (MAP_REGIONS['RIVER']['x_min'] <= x <= MAP_REGIONS['RIVER']['x_max'] and
        MAP_REGIONS['RIVER']['y_min'] <= y <= MAP_REGIONS['RIVER']['y_max']):
        return 'RIVER'

    return 'JUNGLE'


def calculate_distance(x1: int, y1: int, x2: int, y2: int) -> float:
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)


OBJECTIVE_LOCATIONS = {
    'BARON': {'x': 5000, 'y': 10400},
    'DRAGON': {'x': 9800, 'y': 4400},
    'RIFT_HERALD': {'x': 5000, 'y': 10400},
    'BLUE_NEXUS': {'x': 1748, 'y': 1748},
    'RED_NEXUS': {'x': 13172, 'y': 13172},
    'BLUE_BASE_TURRET': {'x': 3651, 'y': 3696},
    'RED_BASE_TURRET': {'x': 11261, 'y': 11397},
    'BLUE_MID_INHIB_TURRET': {'x': 5048, 'y': 4812},
    'RED_MID_INHIB_TURRET': {'x': 9767, 'y': 10113},
}


def get_nearest_objective(x: int, y: int) -> tuple:
    nearest = None
    min_distance = float('inf')

    for obj_name, obj_pos in OBJECTIVE_LOCATIONS.items():
        dist = calculate_distance(x, y, obj_pos['x'], obj_pos['y'])
        if dist < min_distance:
            min_distance = dist
            nearest = obj_name

    return nearest, min_distance


def is_near_objective(x: int, y: int, threshold: int = 3000) -> dict:
    obj_name, distance = get_nearest_objective(x, y)

    return {
        'near_objective': distance < threshold,
        'objective_name': obj_name if distance < threshold else None,
        'distance': round(distance, 1)
    }
