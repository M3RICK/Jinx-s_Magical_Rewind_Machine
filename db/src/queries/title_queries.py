import time
from ..db_handshake import get_dynamodb_reasources
from .db_utils import convert_floats_to_decimal, convert_decimals_to_float


def get_table():
    dynamodb = get_dynamodb_reasources()
    return dynamodb.Table('PlayerTitles')


def store_title(puuid, title, reason, stats, version='current'):
    table = get_table()

    timestamp = int(time.time())
    ttl = timestamp + (30 * 24 * 60 * 60)

    item = {
        'puuid': puuid,
        'version': version,
        'title': title,
        'reason': reason,
        'stats': convert_floats_to_decimal(stats),
        'generated_at': timestamp,
        'ttl': ttl
    }

    table.put_item(Item=item)
    return convert_decimals_to_float(item)


def get_title(puuid, version='current'):
    table = get_table()

    response = table.get_item(
        Key={
            'puuid': puuid,
            'version': version
        }
    )

    item = response.get('Item')
    return convert_decimals_to_float(item) if item else None


def get_current_title(puuid):
    return get_title(puuid, version='current')


def get_all_titles(puuid):
    table = get_table()

    response = table.query(
        KeyConditionExpression='puuid = :puuid',
        ExpressionAttributeValues={
            ':puuid': puuid
        }
    )

    items = response.get('Items', [])
    return [convert_decimals_to_float(item) for item in items]


def delete_title(puuid, version='current'):
    table = get_table()

    table.delete_item(
        Key={
            'puuid': puuid,
            'version': version
        }
    )


def delete_all_titles(puuid):
    titles = get_all_titles(puuid)

    for title in titles:
        delete_title(puuid, title['version'])

    return len(titles)


def title_exists(puuid, version='current'):
    title = get_title(puuid, version)
    return title is not None


def is_title_fresh(puuid, max_age_seconds=2592000, version='current'):
    title = get_title(puuid, version)

    if not title:
        return False

    current_time = int(time.time())
    generated_at = title.get('generated_at', 0)
    age = current_time - generated_at

    return age < max_age_seconds
