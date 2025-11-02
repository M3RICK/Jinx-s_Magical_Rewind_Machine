def count_wins(matches):
    wins = 0
    for match in matches:
        if match.get('win'):
            wins += 1
    return wins


def sum_kda(matches):
    total_kills = 0
    total_deaths = 0
    total_assists = 0

    for match in matches:
        total_kills += match.get('kills', 0)
        total_deaths += match.get('deaths', 0)
        total_assists += match.get('assists', 0)

    return total_kills, total_deaths, total_assists


def calculate_kda(kills, deaths, assists):
    if deaths == 0:
        return round(kills + assists, 2)
    return round((kills + assists) / deaths, 2)


def find_main_role(matches):
    role_counts = {}

    for match in matches:
        role = match.get('role')
        if role:
            role_counts[role] = role_counts.get(role, 0) + 1

    if not role_counts:
        return None

    return max(role_counts, key=role_counts.get)


def find_top_champions(matches, limit=3):
    champion_counts = {}

    for match in matches:
        champion = match.get('champion_name')
        if champion:
            champion_counts[champion] = champion_counts.get(champion, 0) + 1

    sorted_champs = sorted(champion_counts.items(), key=lambda x: x[1], reverse=True)

    return [
        {'name': champ, 'games': count}
        for champ, count in sorted_champs[:limit]
    ]


def calculate_winrate(wins, total_matches):
    if total_matches == 0:
        return 0.0
    return round(wins / total_matches * 100, 1)


def extract_overview_stats(matches):
    if not matches:
        return {}

    total_matches = len(matches)
    total_wins = count_wins(matches)
    kills, deaths, assists = sum_kda(matches)
    main_role = find_main_role(matches)
    top_champions = find_top_champions(matches, limit=3)
    kda = calculate_kda(kills, deaths, assists)
    winrate = calculate_winrate(total_wins, total_matches)

    return {
        'zone_id': 'intro',
        'zone_name': 'Overview',
        'total_matches': total_matches,
        'total_wins': total_wins,
        'total_kills': kills,
        'total_deaths': deaths,
        'total_assists': assists,
        'main_role': main_role,
        'main_champions': top_champions,
        'avg_kda': kda,
        'winrate': winrate
    }
