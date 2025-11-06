from .title_matcher import (
    calculate_avg_deaths,
    classify_kda,
    classify_deaths,
    classify_winrate,
    get_main_champion,
    match_champion_title,
    match_role_title,
    match_generic_title
)


def generate_player_title(overview_stats):
    if not overview_stats:
        return "The Summoner", "No data available"

    kda = overview_stats.get('avg_kda', 0)
    total_deaths = overview_stats.get('total_deaths', 0)
    total_matches = overview_stats.get('total_matches', 1)
    winrate = overview_stats.get('winrate', 0)
    main_role = overview_stats.get('main_role')
    main_champion = get_main_champion(overview_stats)

    avg_deaths = calculate_avg_deaths(total_deaths, total_matches)

    kda_class = classify_kda(kda)
    death_class = classify_deaths(avg_deaths)
    winrate_class = classify_winrate(winrate)

    title = None
    reason = ""

    if main_champion:
        title = match_champion_title(main_champion, kda_class, death_class)
        if title:
            reason = f"Main champion: {main_champion}"

    if not title and main_role:
        title = match_role_title(main_role, kda_class, death_class, winrate_class)
        if title:
            reason = f"Role-based: {main_role}, {kda:.2f} KDA, {winrate:.1f}% WR"

    if not title:
        title = match_generic_title(kda_class, death_class, winrate_class, total_matches)
        reason = f"General performance: {kda:.2f} KDA, {winrate:.1f}% WR"

    return title, reason


def generate_title_with_stats(overview_stats):
    title, reason = generate_player_title(overview_stats)

    return {
        'title': title,
        'reason': reason,
        'stats': {
            'kda': overview_stats.get('avg_kda', 0),
            'winrate': overview_stats.get('winrate', 0),
            'main_role': overview_stats.get('main_role'),
            'main_champion': get_main_champion(overview_stats),
            'total_matches': overview_stats.get('total_matches', 0)
        }
    }
