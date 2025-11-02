def build_intro_prompt(stats):
    role = stats.get('main_role', 'Unknown')
    winrate = stats.get('winrate', 0)
    kda = stats.get('avg_kda', 0)
    champions = stats.get('main_champions', [])

    champ_names = ', '.join([c['name'] for c in champions[:2]])

    prompt = f"""Generate a brief, engaging introduction story (2-3 sentences) for a League of Legends player with these stats:
- Main Role: {role}
- Winrate: {winrate}%
- KDA: {kda}
- Top Champions: {champ_names}

Make it personal, narrative-driven, and fun. Avoid generic responses. Write in second person ("You're a...").
"""
    return prompt


def build_baron_prompt(stats):
    deaths = stats.get('deaths_near', 0)
    secured = stats.get('objectives_secured', 0)
    lost = stats.get('objectives_lost', 0)
    control_rate = stats.get('objective_control_rate', 0)

    prompt = f"""Generate a brief story (2-3 sentences) about this player's Baron Nashor performance:
- Deaths near Baron: {deaths}
- Barons secured: {secured}
- Barons lost to enemy: {lost}
- Control rate: {control_rate}%

Create a narrative about their Baron gameplay. If they die a lot, make it dramatic. If they have good control, praise them. Include actionable advice.
Write in second person ("You've...").
"""
    return prompt


def build_dragon_prompt(stats):
    deaths = stats.get('deaths_near', 0)
    secured = stats.get('objectives_secured', 0)
    lost = stats.get('objectives_lost', 0)
    control_rate = stats.get('objective_control_rate', 0)

    prompt = f"""Generate a brief story (2-3 sentences) about this player's Dragon control:
- Deaths near Dragon pit: {deaths}
- Dragons secured: {secured}
- Dragons lost to enemy: {lost}
- Control rate: {control_rate}%

Create a narrative about their Dragon gameplay. Make it engaging and personalized. Include actionable advice.
Write in second person ("You're...").
"""
    return prompt


def build_herald_prompt(stats):
    deaths = stats.get('deaths_near', 0)
    secured = stats.get('objectives_secured', 0)
    control_rate = stats.get('objective_control_rate', 0)

    prompt = f"""Generate a brief story (2-3 sentences) about this player's Rift Herald gameplay:
- Deaths near Herald: {deaths}
- Heralds secured: {secured}
- Control rate: {control_rate}%

Create a short narrative about their Herald performance. Make it fun and actionable.
Write in second person.
"""
    return prompt


def build_lane_prompt(stats):
    zone_name = stats.get('zone_name', 'Lane')
    deaths = stats.get('deaths_in_region', 0)
    matches = stats.get('matches_played_in_role', 0)
    lane_perf = stats.get('lane_performance', {})

    if not lane_perf:
        return None

    avg_cs = lane_perf.get('avg_cs_at_10', 0)
    avg_gold_diff = lane_perf.get('avg_gold_diff_at_10', 0)

    prompt = f"""Generate a brief story (2-3 sentences) about this player's {zone_name} performance:
- Matches in this role: {matches}
- Deaths in lane: {deaths}
- Average CS at 10min: {avg_cs}
- Average gold difference at 10min: {avg_gold_diff:+.0f}

Create a narrative about their laning phase. Praise strengths, mention weaknesses with advice.
Write in second person.
"""
    return prompt


def build_region_prompt(stats):
    zone_name = stats.get('zone_name', 'Region')
    deaths = stats.get('deaths_in_region', 0)
    time_spent = stats.get('avg_time_spent_percent', 0)

    prompt = f"""Generate a brief story (2-3 sentences) about this player's {zone_name} gameplay:
- Deaths in this area: {deaths}
- Average time spent here: {time_spent}%

Create a short, engaging narrative about their performance in this area.
Write in second person.
"""
    return prompt


def build_prompt(zone_id, stats):
    if zone_id == 'intro':
        return build_intro_prompt(stats)
    elif zone_id == 'baron_pit':
        return build_baron_prompt(stats)
    elif zone_id == 'dragon_pit':
        return build_dragon_prompt(stats)
    elif zone_id == 'herald':
        return build_herald_prompt(stats)
    elif zone_id in ['top_lane', 'mid_lane', 'bot_lane']:
        return build_lane_prompt(stats)
    else:
        return build_region_prompt(stats)
