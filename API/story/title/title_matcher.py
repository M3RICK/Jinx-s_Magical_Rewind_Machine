from .title_rules import (
    KDA_THRESHOLDS,
    DEATH_THRESHOLDS,
    WINRATE_THRESHOLDS,
    CHAMPION_TITLES,
    ROLE_BASED_TITLES,
    GENERIC_TITLES
)


def calculate_avg_deaths(total_deaths, total_matches):
    if total_matches == 0:
        return 0
    return total_deaths / total_matches


def classify_kda(kda):
    if kda >= KDA_THRESHOLDS['very_high']:
        return 'very_high'
    elif kda >= KDA_THRESHOLDS['high']:
        return 'high'
    elif kda >= KDA_THRESHOLDS['medium']:
        return 'medium'
    elif kda >= KDA_THRESHOLDS['low']:
        return 'low'
    return 'very_low'


def classify_deaths(avg_deaths):
    if avg_deaths <= DEATH_THRESHOLDS['very_low']:
        return 'very_low'
    elif avg_deaths <= DEATH_THRESHOLDS['low']:
        return 'low'
    elif avg_deaths <= DEATH_THRESHOLDS['medium']:
        return 'medium'
    elif avg_deaths <= DEATH_THRESHOLDS['high']:
        return 'high'
    return 'very_high'


def classify_winrate(winrate):
    if winrate >= WINRATE_THRESHOLDS['very_high']:
        return 'very_high'
    elif winrate >= WINRATE_THRESHOLDS['high']:
        return 'high'
    elif winrate >= WINRATE_THRESHOLDS['medium']:
        return 'medium'
    elif winrate >= WINRATE_THRESHOLDS['low']:
        return 'low'
    return 'very_low'


def get_main_champion(overview_stats):
    champions = overview_stats.get('main_champions', [])
    if not champions:
        return None
    return champions[0].get('name')


def match_champion_title(champion_name, kda_class, death_class):
    champion_rules = CHAMPION_TITLES.get(champion_name)
    if not champion_rules:
        return None

    if kda_class in ['very_high', 'high'] and 'high_kda' in champion_rules:
        return champion_rules['high_kda']

    if death_class in ['high', 'very_high'] and 'high_deaths' in champion_rules:
        return champion_rules['high_deaths']

    if death_class in ['very_low', 'low'] and 'low_deaths' in champion_rules:
        return champion_rules['low_deaths']

    return champion_rules.get('default')


def match_role_title(role, kda_class, death_class, winrate_class):
    role_rules = ROLE_BASED_TITLES.get(role)
    if not role_rules:
        return None

    if kda_class in ['very_high', 'high'] and 'high_kda' in role_rules:
        return role_rules['high_kda']

    if death_class in ['very_low', 'low'] and 'low_deaths' in role_rules:
        return role_rules['low_deaths']

    if death_class in ['high', 'very_high'] and 'high_deaths' in role_rules:
        return role_rules['high_deaths']

    if winrate_class in ['very_high', 'high'] and 'high_winrate' in role_rules:
        return role_rules['high_winrate']

    return role_rules.get('default')


def match_generic_title(kda_class, death_class, winrate_class, total_matches):
    if total_matches < 10:
        return GENERIC_TITLES['beginner']

    if kda_class == 'very_high':
        return GENERIC_TITLES['very_high_kda']

    if winrate_class in ['very_high', 'high']:
        return GENERIC_TITLES['high_winrate']

    if winrate_class == 'very_low':
        return GENERIC_TITLES['low_winrate']

    if death_class == 'very_high':
        return GENERIC_TITLES['very_high_deaths']

    return GENERIC_TITLES['default']
