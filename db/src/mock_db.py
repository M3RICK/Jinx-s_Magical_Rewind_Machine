"""In-memory database for development and testing."""

import time
from typing import Optional, List, Dict
from copy import deepcopy


_MOCK_STORAGE = {
    'players': {},
    'stories': {},
    'riot_id_index': {}
}


def reset_mock_storage():
    global _MOCK_STORAGE
    _MOCK_STORAGE = {
        'players': {},
        'stories': {},
        'riot_id_index': {}
    }


def seed_test_data():
    test_player = {
        'puuid': 'MOCK_PUUID_12345',
        'riot_id': 'theoppstopper#bigra',
        'region': 'euw1',
        'winrate': 52.5,
        'main_role': 'JUNGLE',
        'main_champions': ['Lee Sin', 'Elise', 'Graves'],
        'created_at': int(time.time()),
        'updated_at': int(time.time())
    }

    _MOCK_STORAGE['players']['MOCK_PUUID_12345'] = test_player
    _MOCK_STORAGE['riot_id_index']['theoppstopper#bigra'] = 'MOCK_PUUID_12345'

    test_stories = {
        'intro': {
            'zone_id': 'intro',
            'zone_name': 'Overview',
            'story_text': 'Welcome to your Rift Rewind! You\'ve played 42 games this month with a 52% win rate. Your jungle control has improved significantly, but there\'s always room to grow. Let\'s explore the map together!',
            'stats': {
                'total_games': 42,
                'wins': 22,
                'losses': 20,
                'avg_kda': 3.2
            },
            'generated_at': int(time.time()),
            'puuid': 'MOCK_PUUID_12345'
        },
        'baron_pit': {
            'zone_id': 'baron_pit',
            'zone_name': 'Baron Nashor',
            'story_text': 'Baron Nashor has become your nemesis! You\'ve fallen 12 times in his pit this month, often contesting when your team was behind. Try warding earlier and only fighting when you have vision advantage—patience wins Baron, not bravery.',
            'stats': {
                'deaths': 12,
                'barons_secured': 5,
                'barons_lost': 7,
                'participation': 15
            },
            'generated_at': int(time.time()),
            'puuid': 'MOCK_PUUID_12345'
        },
        'dragon_pit': {
            'zone_id': 'dragon_pit',
            'zone_name': 'Dragon Soul',
            'story_text': 'You\'re a Dragon master! 73% objective control with only 2 deaths during contests. Your early ward coverage at 4:30 has saved your team countless times. Keep it up!',
            'stats': {
                'deaths': 2,
                'dragons_secured': 18,
                'dragons_lost': 7,
                'participation': 25
            },
            'generated_at': int(time.time()),
            'puuid': 'MOCK_PUUID_12345'
        },
        'jungle': {
            'zone_id': 'jungle',
            'zone_name': 'Jungle',
            'story_text': 'Your jungle pathing is efficient, averaging 6.2 CS/min. However, you tend to over-farm when your laners need help. Try balancing farming with gank opportunities—a well-timed gank is worth 3 camps!',
            'stats': {
                'avg_cs_per_min': 6.2,
                'deaths_in_jungle': 8,
                'time_spent_pct': 45.3
            },
            'generated_at': int(time.time()),
            'puuid': 'MOCK_PUUID_12345'
        },
        'river': {
            'zone_id': 'river',
            'zone_name': 'River Control',
            'story_text': 'River skirmishes are your battlefield! You\'ve participated in 28 river fights with a 60% win rate. Your vision control is solid, but watch out for late rotations—3 deaths came from arriving after your team.',
            'stats': {
                'deaths': 6,
                'kills': 14,
                'assists': 22,
                'skirmishes': 28
            },
            'generated_at': int(time.time()),
            'puuid': 'MOCK_PUUID_12345'
        },
        'top_lane': {
            'zone_id': 'top_lane',
            'zone_name': 'Top Lane',
            'story_text': 'Top lane has seen better days. You average 2 ganks per game, but your success rate is only 35%. Try ganking post-level 3 when your laner has CC, and avoid diving without vision.',
            'stats': {
                'deaths': 5,
                'successful_ganks': 7,
                'failed_ganks': 13
            },
            'generated_at': int(time.time()),
            'puuid': 'MOCK_PUUID_12345'
        },
        'mid_lane': {
            'zone_id': 'mid_lane',
            'zone_name': 'Mid Lane',
            'story_text': 'Mid lane is your most impactful zone! 45% of your successful ganks happen here. Your timing around mid priority is excellent—keep pressuring mid to unlock roams.',
            'stats': {
                'deaths': 3,
                'successful_ganks': 15,
                'failed_ganks': 8
            },
            'generated_at': int(time.time()),
            'puuid': 'MOCK_PUUID_12345'
        },
        'bot_lane': {
            'zone_id': 'bot_lane',
            'zone_name': 'Bot Lane',
            'story_text': 'Bot lane ganks are hit-or-miss. You tend to force ganks even when pushed in. Wait for your bot lane to freeze or slow-push before committing—patience pays off!',
            'stats': {
                'deaths': 4,
                'successful_ganks': 9,
                'failed_ganks': 11
            },
            'generated_at': int(time.time()),
            'puuid': 'MOCK_PUUID_12345'
        }
    }

    _MOCK_STORAGE['stories']['MOCK_PUUID_12345'] = test_stories

    print("✓ Mock DB seeded with test player: theoppstopper#bigra")


class MockPlayer:
    def __init__(self, puuid, riot_id, region, winrate=None, main_role=None,
                 main_champions=None, current_rank=None):
        self.puuid = puuid
        self.riot_id = riot_id
        self.region = region
        self.winrate = winrate
        self.main_role = main_role
        self.main_champions = main_champions or []
        self.current_rank = current_rank
        self.created_at = int(time.time())
        self.updated_at = int(time.time())

    def to_dynamodb_item(self):
        return {
            'puuid': self.puuid,
            'riot_id': self.riot_id,
            'region': self.region,
            'winrate': self.winrate,
            'main_role': self.main_role,
            'main_champions': self.main_champions,
            'current_rank': self.current_rank,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dynamodb_item(cls, item):
        if not item:
            return None
        return cls(
            puuid=item['puuid'],
            riot_id=item['riot_id'],
            region=item['region'],
            winrate=item.get('winrate'),
            main_role=item.get('main_role'),
            main_champions=item.get('main_champions', []),
            current_rank=item.get('current_rank')
        )


class MockPlayerRepository:
    def __init__(self, dynamodb_resource=None):
        pass

    def get_by_puuid(self, puuid: str) -> Optional[MockPlayer]:
        player_data = _MOCK_STORAGE['players'].get(puuid)
        if not player_data:
            return None
        return MockPlayer.from_dynamodb_item(player_data)

    def get_by_riot_id(self, riot_id: str) -> Optional[MockPlayer]:
        puuid = _MOCK_STORAGE['riot_id_index'].get(riot_id)
        if not puuid:
            return None
        return self.get_by_puuid(puuid)

    def create(self, player: MockPlayer) -> MockPlayer:
        player_data = player.to_dynamodb_item()
        _MOCK_STORAGE['players'][player.puuid] = player_data
        _MOCK_STORAGE['riot_id_index'][player.riot_id] = player.puuid
        print(f"✓ Mock DB: Created player {player.riot_id}")
        return player

    def update(self, player: MockPlayer) -> MockPlayer:
        player.updated_at = int(time.time())
        player_data = player.to_dynamodb_item()
        _MOCK_STORAGE['players'][player.puuid] = player_data
        print(f"✓ Mock DB: Updated player {player.riot_id}")
        return player

    def delete(self, puuid: str) -> bool:
        if puuid in _MOCK_STORAGE['players']:
            player_data = _MOCK_STORAGE['players'][puuid]
            riot_id = player_data['riot_id']
            del _MOCK_STORAGE['players'][puuid]
            if riot_id in _MOCK_STORAGE['riot_id_index']:
                del _MOCK_STORAGE['riot_id_index'][riot_id]
            print(f"✓ Mock DB: Deleted player {puuid}")
            return True
        return False

    def exists(self, puuid: str) -> bool:
        return puuid in _MOCK_STORAGE['players']

    def exists_by_riot_id(self, riot_id: str) -> bool:
        return riot_id in _MOCK_STORAGE['riot_id_index']


def store_story(puuid: str, zone_id: str, story_text: str,
                zone_name: str, stats: dict) -> dict:
    timestamp = int(time.time())
    ttl = timestamp + (7 * 24 * 60 * 60)

    story_data = {
        'puuid': puuid,
        'zone_id': zone_id,
        'story_text': story_text,
        'zone_name': zone_name,
        'generated_at': timestamp,
        'ttl': ttl,
        'stats': stats
    }

    if puuid not in _MOCK_STORAGE['stories']:
        _MOCK_STORAGE['stories'][puuid] = {}

    _MOCK_STORAGE['stories'][puuid][zone_id] = story_data
    return story_data


def store_all_stories(puuid: str, stories_dict: dict) -> dict:
    stored_stories = {}

    for zone_id, story_data in stories_dict.items():
        story = store_story(
            puuid=puuid,
            zone_id=zone_id,
            story_text=story_data['story'],
            zone_name=story_data['zone_name'],
            stats=story_data.get('stats', {})
        )
        stored_stories[zone_id] = story

    print(f"✓ Mock DB: Stored {len(stored_stories)} stories for PUUID {puuid}")
    return stored_stories


def get_story(puuid: str, zone_id: str) -> Optional[dict]:
    player_stories = _MOCK_STORAGE['stories'].get(puuid, {})
    return player_stories.get(zone_id)


def get_all_stories(puuid: str) -> List[dict]:
    player_stories = _MOCK_STORAGE['stories'].get(puuid, {})
    return list(player_stories.values())


def delete_story(puuid: str, zone_id: str) -> bool:
    if puuid in _MOCK_STORAGE['stories']:
        if zone_id in _MOCK_STORAGE['stories'][puuid]:
            del _MOCK_STORAGE['stories'][puuid][zone_id]
            print(f"✓ Mock DB: Deleted story {zone_id} for {puuid}")
            return True
    return False


def delete_all_stories(puuid: str) -> int:
    if puuid in _MOCK_STORAGE['stories']:
        count = len(_MOCK_STORAGE['stories'][puuid])
        _MOCK_STORAGE['stories'][puuid] = {}
        print(f"✓ Mock DB: Deleted {count} stories for {puuid}")
        return count
    return 0


def story_exists(puuid: str, zone_id: str) -> bool:
    return get_story(puuid, zone_id) is not None


def is_story_fresh(puuid: str, zone_id: str, max_age_seconds: int = 604800) -> bool:
    story = get_story(puuid, zone_id)

    if not story:
        return False

    current_time = int(time.time())
    generated_at = story.get('generated_at', 0)
    age = current_time - generated_at

    return age < max_age_seconds


seed_test_data()
print("✓ Mock DB initialized (in-memory storage)")
