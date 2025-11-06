import time
from .prompt_builder import build_prompt
from .bedrock_client import generate_story


def generate_zone_story(zone_id, zone_stats, story_mode='coach'):
    """
    Generate a story for a specific zone.

    Args:
        zone_id: Zone identifier (e.g., 'baron_pit')
        zone_stats: Statistics for the zone
        story_mode: 'coach' for helpful advice or 'roast' for savage humor

    Returns:
        Generated story text or None
    """
    prompt = build_prompt(zone_id, zone_stats, mode=story_mode)

    if not prompt:
        return None

    story = generate_story(prompt, zone_id, mode=story_mode)
    return story


def generate_all_stories(zone_stats_dict, story_mode='coach'):
    """
    Generate stories for all zones.

    Args:
        zone_stats_dict: Dictionary of zone_id -> stats
        story_mode: 'coach' for helpful advice or 'roast' for savage humor

    Returns:
        Dictionary of zone_id -> {zone_name, story, stats}
    """
    stories = {}

    mode_emoji = "🎓" if story_mode == 'coach' else "🔥"
    print(f"\n{mode_emoji} Generating stories in {story_mode.upper()} mode...")

    for i, (zone_id, stats) in enumerate(zone_stats_dict.items()):
        zone_name = stats.get('zone_name', zone_id)
        print(f"  [{i+1}/{len(zone_stats_dict)}] {zone_name}...")

        story = generate_zone_story(zone_id, stats, story_mode)

        if story:
            stories[zone_id] = {
                'zone_name': zone_name,
                'story': story,
                'stats': stats
            }

        # Rate limiting between API calls
        if i < len(zone_stats_dict) - 1:
            time.sleep(2)

    print(f"✅ Generated {len(stories)} stories in {story_mode} mode\n")
    return stories
