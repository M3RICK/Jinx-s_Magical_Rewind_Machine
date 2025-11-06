import time
from ..db_handshake import get_dynamodb_reasources
from .db_utils import convert_floats_to_decimal, convert_decimals_to_float


def get_table():
    dynamodb = get_dynamodb_reasources()
    return dynamodb.Table('MapStories')


def store_story(puuid, zone_id, story_text, zone_name, stats, story_mode='coach'):
    table = get_table()

    timestamp = int(time.time())
    ttl = timestamp + (7 * 24 * 60 * 60)

    item = {
        'puuid': puuid,
        'zone_id': zone_id,
        'story_text': story_text,
        'zone_name': zone_name,
        'story_mode': story_mode,  # Store which mode generated this story
        'generated_at': timestamp,
        'ttl': ttl,
        'stats': convert_floats_to_decimal(stats)
    }

    table.put_item(Item=item)
    return convert_decimals_to_float(item)


def store_all_stories(puuid, stories_dict, story_mode='coach'):
    stored_stories = {}

    for zone_id, story_data in stories_dict.items():
        story = store_story(
            puuid=puuid,
            zone_id=zone_id,
            story_text=story_data['story'],
            zone_name=story_data['zone_name'],
            stats=story_data.get('stats', {}),
            story_mode=story_mode
        )
        stored_stories[zone_id] = story

    return stored_stories


def get_story(puuid, zone_id):
    table = get_table()

    response = table.get_item(
        Key={
            'puuid': puuid,
            'zone_id': zone_id
        }
    )

    item = response.get('Item')
    return convert_decimals_to_float(item) if item else None


def get_all_stories(puuid):
    table = get_table()

    response = table.query(
        KeyConditionExpression='puuid = :puuid',
        ExpressionAttributeValues={
            ':puuid': puuid
        }
    )

    items = response.get('Items', [])
    return [convert_decimals_to_float(item) for item in items]


def delete_story(puuid, zone_id):
    table = get_table()

    table.delete_item(
        Key={
            'puuid': puuid,
            'zone_id': zone_id
        }
    )


def delete_all_stories(puuid):
    stories = get_all_stories(puuid)

    for story in stories:
        delete_story(puuid, story['zone_id'])

    return len(stories)


def story_exists(puuid, zone_id):
    story = get_story(puuid, zone_id)
    return story is not None


def check_story_mode(puuid, requested_mode):
    """
    Check if cached stories match the requested mode.

    Args:
        puuid: Player's PUUID
        requested_mode: The mode user requested ('coach' or 'roast')

    Returns:
        True if stories exist and match mode, False otherwise
    """
    stories = get_all_stories(puuid)

    if not stories:
        return False

    # Check first story's mode (all should be same mode)
    cached_mode = stories[0].get('story_mode', 'coach')
    return cached_mode == requested_mode


def is_story_fresh(puuid, zone_id, max_age_seconds=604800):
    story = get_story(puuid, zone_id)

    if not story:
        return False

    current_time = int(time.time())
    generated_at = story.get('generated_at', 0)
    age = current_time - generated_at

    return age < max_age_seconds
