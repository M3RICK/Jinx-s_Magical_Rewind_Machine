import time
from .prompt_builder import build_prompt
from .bedrock_client import generate_story


def generate_zone_story(zone_id, zone_stats):
    prompt = build_prompt(zone_id, zone_stats)

    if not prompt:
        return None

    story = generate_story(prompt)
    return story


def generate_all_stories(zone_stats_dict):
    stories = {}

    for i, (zone_id, stats) in enumerate(zone_stats_dict.items()):
        print(f"Generating story for {stats.get('zone_name', zone_id)}...")
        story = generate_zone_story(zone_id, stats)

        if story:
            stories[zone_id] = {
                'zone_name': stats.get('zone_name'),
                'story': story,
                'stats': stats
            }

        if i < len(zone_stats_dict) - 1:
            time.sleep(2)

    return stories
