import random


MOCK_STORIES = {
    "baron_pit": [
        "Baron Nashor has become your nemesis! You've fallen here multiple times this month. Try warding earlier and only fighting when you have vision advantage.",
        "You're showing good Baron control! Your team secures it 65% of the time when you're alive. Keep that pressure up.",
        "Baron fights are your weak spot. Consider rotating earlier and setting up vision 60 seconds before spawn."
    ],
    "dragon_pit": [
        "Dragon master! 73% objective control with minimal deaths. Your early ward coverage is paying off.",
        "You're struggling at Dragon. Too many late rotations cost your team souls. Start moving at 30 seconds before spawn.",
        "Solid Dragon performance. Your team gets first Dragon 68% of games when you're jungle."
    ],
    "top_lane": [
        "Top lane is your comfort zone. 58% win rate with excellent CS numbers. Wave management is on point.",
        "You're getting bullied top. Down 25 CS at 10 minutes on average. Focus on safer farming patterns.",
        "Strong laning phase! You're ahead in gold at 10 minutes in 70% of games."
    ],
    "mid_lane": [
        "Mid lane roaming needs work. You're missing 2-3 waves per roam. Push faster before leaving.",
        "Excellent mid pressure! Your roams lead to kills 45% of the time. Keep the map presence up.",
        "You're playing mid too passively. Only 1.2 roams per game. Your sidelanes need help."
    ],
    "bot_lane": [
        "Bot lane positioning is risky. You're dying to ganks 4+ times per game. Ward deeper and track the jungler.",
        "Strong bot lane! 2v2 trades are heavily favored. You're winning lane 65% of games.",
        "Your support synergy needs work. You're often too far apart during fights."
    ],
    "jungle": [
        "Jungle pathing is inefficient. You're down 15 CS at 10 minutes vs enemy jungler. Optimize your clear.",
        "Gank-heavy style! 68% successful gank rate, but your farm suffers. Balance it better.",
        "Strong jungle control! You're consistently ahead in CS and objectives. Keep counterjungling."
    ],
    "default": [
        "Your overall performance shows potential. Focus on consistency and decision-making.",
        "Mixed results across the map. Identify your strongest role and spam it for climbing.",
        "You're improving! Win rate is trending up over the last 20 games."
    ]
}


def generate_mock_story(zone_id, player_stats=None):
    """
    Generate a mock story for testing without using AI tokens.

    Args:
        zone_id: The map zone identifier
        player_stats: Optional stats dict (ignored for mock)

    Returns:
        A randomized mock story string
    """
    stories = MOCK_STORIES.get(zone_id, MOCK_STORIES["default"])
    return random.choice(stories)


def generate_mock_title(player_data=None):
    """Generate a mock player title for testing."""
    titles = [
        "The Iron Tactician",
        "Baron Slayer",
        "Dragon Soul Hunter",
        "The Rift Wanderer",
        "Splitpush Specialist",
        "Team Fight Commander",
        "The Comeback King",
        "Lane Dominator",
        "Vision Master"
    ]
    return random.choice(titles)
