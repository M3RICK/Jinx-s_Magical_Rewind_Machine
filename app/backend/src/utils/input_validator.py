import re
from typing import Tuple, Optional


GAME_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_\.]{3,16}$')
TAG_LINE_PATTERN = re.compile(r'^[a-zA-Z0-9]{3,5}$')
ZONE_ID_PATTERN = re.compile(r'^[a-z_]{2,50}$')
PLATFORM_PATTERN = re.compile(r'^[a-z0-9]{2,5}$')

DANGEROUS_CHARS = ['<', '>', '"', "'", '\\', ';', '(', ')', '{', '}', '$', '`']


def validate_game_name(game_name: str) -> Tuple[bool, Optional[str]]:
    if not game_name or not isinstance(game_name, str):
        return False, "gameName must be a string"

    if len(game_name) < 3 or len(game_name) > 16:
        return False, "gameName must be 3-16 characters"

    if not GAME_NAME_PATTERN.match(game_name):
        return False, "gameName contains invalid characters"

    if any(char in game_name for char in DANGEROUS_CHARS):
        return False, "gameName contains forbidden characters"

    return True, None


def validate_tag_line(tag_line: str) -> Tuple[bool, Optional[str]]:
    if not tag_line or not isinstance(tag_line, str):
        return False, "tagLine must be a string"

    if len(tag_line) < 3 or len(tag_line) > 5:
        return False, "tagLine must be 3-5 characters"

    if not TAG_LINE_PATTERN.match(tag_line):
        return False, "tagLine must be alphanumeric only"

    return True, None


def validate_zone_id(zone_id: str) -> Tuple[bool, Optional[str]]:
    if not zone_id or not isinstance(zone_id, str):
        return False, "zone_id must be a string"

    if len(zone_id) < 2 or len(zone_id) > 50:
        return False, "zone_id must be 2-50 characters"

    if not ZONE_ID_PATTERN.match(zone_id):
        return False, "zone_id contains invalid characters"

    return True, None


def validate_platform(platform: str, valid_platforms: list) -> Tuple[bool, Optional[str]]:
    if not platform or not isinstance(platform, str):
        return False, "platform must be a string"

    if not PLATFORM_PATTERN.match(platform):
        return False, "platform contains invalid characters"

    if platform not in valid_platforms:
        return False, f"Invalid platform. Must be one of: {', '.join(valid_platforms)}"

    return True, None


def validate_match_count(match_count, min_count: int = 5, max_count: int = 50) -> Tuple[bool, Optional[str], Optional[int]]:
    try:
        count = int(match_count)

        if count < min_count or count > max_count:
            return False, f"matchCount must be between {min_count} and {max_count}", None

        return True, None, count
    except (ValueError, TypeError):
        return False, "matchCount must be a valid number", None


def validate_story_mode(story_mode: str, valid_modes: list = ['coach', 'roast']) -> Tuple[bool, Optional[str]]:
    if not story_mode:
        return True, None

    if not isinstance(story_mode, str):
        return False, "storyMode must be a string"

    if story_mode not in valid_modes:
        return False, f"Invalid storyMode. Must be one of: {', '.join(valid_modes)}"

    return True, None


def validate_riot_id(riot_id: str) -> Tuple[bool, Optional[str]]:
    if not riot_id or not isinstance(riot_id, str):
        return False, "riot_id must be a string"

    separator = '#' if '#' in riot_id else '-' if '-' in riot_id else None
    if not separator:
        return False, "Invalid riot_id format (must contain # or -)"

    parts = riot_id.split(separator)
    if len(parts) != 2:
        return False, "Invalid riot_id format (must be name#tag or name-tag)"

    game_name, tag_line = parts

    is_valid, error = validate_game_name(game_name)
    if not is_valid:
        return False, f"Invalid game name: {error}"

    is_valid, error = validate_tag_line(tag_line)
    if not is_valid:
        return False, f"Invalid tag line: {error}"

    return True, None


def sanitize_string(value: str, max_length: int = 100) -> str:
    if not isinstance(value, str):
        return ""

    value = value[:max_length]
    value = value.replace('\x00', '')
    value = value.strip()

    return value


def sanitize_html(value: str) -> str:
    if not isinstance(value, str):
        return ""

    replacements = {
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '/': '&#x2F;',
        '\\': '&#x5C;'
    }

    for char, entity in replacements.items():
        value = value.replace(char, entity)

    return value
