def build_intro_prompt(stats, mode='coach'):
    role = stats.get('main_role', 'Unknown')
    winrate = stats.get('winrate', 0)
    kda = stats.get('avg_kda', 0)
    champions = stats.get('main_champions', [])

    champ_names = ', '.join([c['name'] for c in champions[:2]])

    if mode == 'roast':
        prompt = f"""Generate a SAVAGE and HILARIOUS roast (2-3 sentences) for a League of Legends player:
- Main Role: {role}
- Winrate: {winrate}%
- KDA: {kda}
- Top Champions: {champ_names}

Be brutally honest and funny! If their winrate is bad, roast them. If their KDA is low, make jokes about feeding.
Be creative and savage but not mean-spirited. Write in second person like you're trash-talking them.
Example tone: "Ah yes, another {role} player with a {winrate}% winrate. I've seen Bronze players with better stats..."
"""
    else:  # coach mode
        prompt = f"""Generate a professional and encouraging introduction (2-3 sentences) for a League of Legends player:
- Main Role: {role}
- Winrate: {winrate}%
- KDA: {kda}
- Top Champions: {champ_names}

Be constructive and motivating. Highlight their strengths and provide actionable advice for improvement.
Write in second person with a supportive coaching tone.
Example tone: "As a {role} main, you show solid fundamentals with {champ_names}..."
"""
    return prompt


def build_baron_prompt(stats, mode='coach'):
    deaths = stats.get('deaths_near', 0)
    secured = stats.get('objectives_secured', 0)
    lost = stats.get('objectives_lost', 0)
    control_rate = stats.get('objective_control_rate', 0)

    if mode == 'roast':
        prompt = f"""Generate a SAVAGE roast (2-3 sentences) about this player's Baron Nashor performance:
- Deaths near Baron: {deaths}
- Barons secured: {secured}
- Barons lost to enemy: {lost}
- Control rate: {control_rate}%

If they die a lot at Baron, roast them HARD. If they have low control rate, make jokes about them donating Baron to the enemy team.
Be creative and brutal! Examples: "Baron pit has become your personal graveyard", "You've fed more at Baron than a Thanksgiving turkey"
Write in second person with savage humor.
"""
    else:  # coach mode
        prompt = f"""Generate a professional coaching analysis (2-3 sentences) about this player's Baron Nashor performance:
- Deaths near Baron: {deaths}
- Barons secured: {secured}
- Barons lost to enemy: {lost}
- Control rate: {control_rate}%

Provide constructive feedback. If they struggle, suggest vision control and timing improvements. If they excel, acknowledge it.
Write in second person with a supportive coaching tone.
"""
    return prompt


def build_dragon_prompt(stats, mode='coach'):
    deaths = stats.get('deaths_near', 0)
    secured = stats.get('objectives_secured', 0)
    lost = stats.get('objectives_lost', 0)
    control_rate = stats.get('objective_control_rate', 0)

    if mode == 'roast':
        prompt = f"""Generate a HILARIOUS roast (2-3 sentences) about this player's Dragon control:
- Deaths near Dragon pit: {deaths}
- Dragons secured: {secured}
- Dragons lost to enemy: {lost}
- Control rate: {control_rate}%

If they have low control, roast them about feeding dragons to the enemy. If they die a lot, make jokes about the dragon eating them instead.
Be creative and savage! Example: "The dragons have started a fan club for you... because you keep feeding them"
Write in second person with brutal humor.
"""
    else:  # coach mode
        prompt = f"""Generate a constructive analysis (2-3 sentences) about this player's Dragon control:
- Deaths near Dragon pit: {deaths}
- Dragons secured: {secured}
- Dragons lost to enemy: {lost}
- Control rate: {control_rate}%

Provide actionable advice on dragon priority and team coordination. Acknowledge strengths and suggest improvements.
Write in second person with a professional coaching tone.
"""
    return prompt


def build_herald_prompt(stats, mode='coach'):
    deaths = stats.get('deaths_near', 0)
    secured = stats.get('objectives_secured', 0)
    control_rate = stats.get('objective_control_rate', 0)

    if mode == 'roast':
        prompt = f"""Generate a SAVAGE roast (2-3 sentences) about this player's Rift Herald gameplay:
- Deaths near Herald: {deaths}
- Heralds secured: {secured}
- Control rate: {control_rate}%

If they ignore Herald, roast them about missing free objectives. If they die there, make jokes about the Herald killing them instead.
Be brutal and funny! Example: "Herald called, it wants its free turret plates back"
Write in second person with savage humor.
"""
    else:  # coach mode
        prompt = f"""Generate a helpful analysis (2-3 sentences) about this player's Rift Herald gameplay:
- Deaths near Herald: {deaths}
- Heralds secured: {secured}
- Control rate: {control_rate}%

Provide constructive feedback on Herald priority and usage. Suggest timing and coordination improvements.
Write in second person with a supportive coaching tone.
"""
    return prompt


def build_lane_prompt(stats, mode='coach'):
    zone_name = stats.get('zone_name', 'Lane')
    deaths = stats.get('deaths_in_region', 0)
    matches = stats.get('matches_played_in_role', 0)
    lane_perf = stats.get('lane_performance', {})

    if not lane_perf:
        return None

    avg_cs = lane_perf.get('avg_cs_at_10', 0)
    avg_gold_diff = lane_perf.get('avg_gold_diff_at_10', 0)

    if mode == 'roast':
        prompt = f"""Generate a BRUTAL roast (2-3 sentences) about this player's {zone_name} performance:
- Matches in this role: {matches}
- Deaths in lane: {deaths}
- Average CS at 10min: {avg_cs}
- Average gold difference at 10min: {avg_gold_diff:+.0f}

If their CS is low, roast them about missing cannon minions. If gold diff is negative, make jokes about getting gapped.
Be savage and creative! Example: "Your laning phase is so bad, even the minions feel sorry for you"
Write in second person with brutal humor.
"""
    else:  # coach mode
        prompt = f"""Generate a constructive analysis (2-3 sentences) about this player's {zone_name} performance:
- Matches in this role: {matches}
- Deaths in lane: {deaths}
- Average CS at 10min: {avg_cs}
- Average gold difference at 10min: {avg_gold_diff:+.0f}

Provide specific feedback on wave management, trading patterns, and early game decision-making.
Write in second person with a professional coaching tone.
"""
    return prompt


def build_region_prompt(stats, mode='coach'):
    zone_name = stats.get('zone_name', 'Region')
    deaths = stats.get('deaths_in_region', 0)
    time_spent = stats.get('avg_time_spent_percent', 0)

    if mode == 'roast':
        prompt = f"""Generate a SAVAGE roast (2-3 sentences) about this player's {zone_name} gameplay:
- Deaths in this area: {deaths}
- Average time spent here: {time_spent}%

If they die a lot in this area, roast them mercilessly. Make creative jokes about their positioning and decision-making.
Be brutal and funny! Example: "This area should be renamed in your honor... 'The Feeding Grounds'"
Write in second person with savage humor.
"""
    else:  # coach mode
        prompt = f"""Generate a helpful analysis (2-3 sentences) about this player's {zone_name} gameplay:
- Deaths in this area: {deaths}
- Average time spent here: {time_spent}%

Provide constructive feedback on positioning, vision control, and map awareness in this area.
Write in second person with a supportive coaching tone.
"""
    return prompt


def build_prompt(zone_id, stats, mode='coach'):
    """
    Build prompt for story generation based on zone and mode.

    Args:
        zone_id: Zone identifier (e.g., 'baron_pit', 'dragon_pit')
        stats: Statistics dictionary for the zone
        mode: 'coach' for helpful advice or 'roast' for savage humor

    Returns:
        Prompt string for AI generation
    """
    if zone_id == 'intro':
        return build_intro_prompt(stats, mode)
    elif zone_id == 'baron_pit':
        return build_baron_prompt(stats, mode)
    elif zone_id == 'dragon_pit':
        return build_dragon_prompt(stats, mode)
    elif zone_id == 'herald':
        return build_herald_prompt(stats, mode)
    elif zone_id in ['top_lane', 'mid_lane', 'bot_lane']:
        return build_lane_prompt(stats, mode)
    else:
        return build_region_prompt(stats, mode)
