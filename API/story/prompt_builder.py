def build_intro_prompt(stats, mode='coach'):
    role = stats.get('main_role', 'Unknown')
    winrate = stats.get('winrate', 0)
    kda = stats.get('avg_kda', 0)
    champions = stats.get('main_champions', [])

    champ_names = ', '.join([c['name'] for c in champions[:2]])

    if mode == 'roast':
        prompt = f"""Roast this player (2-3 sentences, savage but funny):
Role: {role} | WR: {winrate}% | KDA: {kda} | Champs: {champ_names}
Write in 2nd person."""
    else:  # coach mode
        prompt = f"""Write a coaching intro (2-3 sentences, supportive):
Role: {role} | WR: {winrate}% | KDA: {kda} | Champs: {champ_names}
Highlight strengths, suggest improvements. 2nd person."""
    return prompt


def build_baron_prompt(stats, mode='coach'):
    deaths = stats.get('deaths_near', 0)
    secured = stats.get('objectives_secured', 0)
    lost = stats.get('objectives_lost', 0)
    control_rate = stats.get('objective_control_rate', 0)

    if mode == 'roast':
        prompt = f"""Roast Baron performance (2-3 sentences, brutal):
Deaths: {deaths} | Secured: {secured} | Lost: {lost} | Control: {control_rate}%
2nd person, savage humor."""
    else:  # coach mode
        prompt = f"""Coach Baron performance (2-3 sentences):
Deaths: {deaths} | Secured: {secured} | Lost: {lost} | Control: {control_rate}%
Constructive feedback, suggest improvements. 2nd person."""
    return prompt


def build_dragon_prompt(stats, mode='coach'):
    deaths = stats.get('deaths_near', 0)
    secured = stats.get('objectives_secured', 0)
    lost = stats.get('objectives_lost', 0)
    control_rate = stats.get('objective_control_rate', 0)

    if mode == 'roast':
        prompt = f"""Roast Dragon control (2-3 sentences, hilarious):
Deaths: {deaths} | Secured: {secured} | Lost: {lost} | Control: {control_rate}%
2nd person, brutal humor."""
    else:  # coach mode
        prompt = f"""Coach Dragon control (2-3 sentences):
Deaths: {deaths} | Secured: {secured} | Lost: {lost} | Control: {control_rate}%
Actionable advice, acknowledge strengths. 2nd person."""
    return prompt


def build_herald_prompt(stats, mode='coach'):
    deaths = stats.get('deaths_near', 0)
    secured = stats.get('objectives_secured', 0)
    control_rate = stats.get('objective_control_rate', 0)

    if mode == 'roast':
        prompt = f"""Roast Herald gameplay (2-3 sentences, savage):
Deaths: {deaths} | Secured: {secured} | Control: {control_rate}%
2nd person, brutal humor."""
    else:  # coach mode
        prompt = f"""Coach Herald gameplay (2-3 sentences):
Deaths: {deaths} | Secured: {secured} | Control: {control_rate}%
Herald priority and timing tips. 2nd person."""
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
        prompt = f"""Roast {zone_name} performance (2-3 sentences, brutal):
Matches: {matches} | Deaths: {deaths} | CS@10: {avg_cs} | Gold@10: {avg_gold_diff:+.0f}
2nd person, savage."""
    else:  # coach mode
        prompt = f"""Coach {zone_name} performance (2-3 sentences):
Matches: {matches} | Deaths: {deaths} | CS@10: {avg_cs} | Gold@10: {avg_gold_diff:+.0f}
Wave management and trading tips. 2nd person."""
    return prompt


def build_region_prompt(stats, mode='coach'):
    zone_name = stats.get('zone_name', 'Region')
    deaths = stats.get('deaths_in_region', 0)
    time_spent = stats.get('avg_time_spent_percent', 0)

    if mode == 'roast':
        prompt = f"""Roast {zone_name} gameplay (2-3 sentences, savage):
Deaths: {deaths} | Time spent: {time_spent}%
2nd person, brutal jokes."""
    else:  # coach mode
        prompt = f"""Coach {zone_name} gameplay (2-3 sentences):
Deaths: {deaths} | Time spent: {time_spent}%
Positioning and vision tips. 2nd person."""
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
