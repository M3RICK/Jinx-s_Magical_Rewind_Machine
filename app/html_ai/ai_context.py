"""
Build AI context from authenticated player with privacy rules.
"""

def build_ai_context_from_player(player):
    """
    Build AI coaching context from authenticated player object.

    Args:
        player: Player object from DynamoDB (already fetched)

    Returns:
        Dict with AI context and privacy prompt
    """
    # Extract player info
    riot_id = player.riot_id
    puuid = player.puuid
    region = player.region
    main_role = getattr(player, 'main_role', None)
    winrate = getattr(player, 'winrate', None)
    main_champions = getattr(player, 'main_champions', None)

    # Format rank
    current_rank = None
    if hasattr(player, 'current_rank') and player.current_rank:
        rank_obj = player.current_rank
        current_rank = f"{rank_obj.tier} {rank_obj.division}"

    # Build privacy-aware system prompt addition
    privacy_prompt = f"""

PLAYER SESSION CONTEXT:
You are now coaching player: {riot_id}
- PUUID: {puuid[:16]}...
- Region: {region}
- Main Role: {main_role or 'Not yet determined'}
- Winrate: {f"{winrate}%" if winrate else "Not yet determined (needs more matches)"}
- Current Rank: {current_rank or 'Unranked'}
- Main Champions: {', '.join(main_champions[:3]) if main_champions else 'Not yet determined'}

Remember this player's context throughout the conversation.

PRIVACY & DATA ACCESS RULES (CRITICAL - SECURITY REQUIREMENT):

YOU ARE ONLY AUTHORIZED TO ACCESS DATA FOR: {riot_id} (PUUID: {puuid[:16]}...)

ALLOWED:
Access all data for {riot_id}
Use your tools (champion/item/rune database) - this is public game knowledge
Answer general League questions
Discuss publicly visible info about other players if asked (ranks, match results)

STRICTLY FORBIDDEN:
NEVER access AI chat conversations from other players
NEVER show sensitive stats/data from other players' profiles
NEVER look up other players in the database
NEVER imply you can see other players' private coaching sessions

If asked about another player's private data, respond:
"I can only access detailed data for your account ({riot_id}). I can help with general League knowledge or publicly visible information."

VIOLATING THESE RULES COMPROMISES USER PRIVACY AND IS A SECURITY BREACH.
"""

    return {
        'riot_id': riot_id,
        'puuid': puuid,
        'region': region,
        'main_role': main_role,
        'winrate': winrate,
        'rank': current_rank,
        'main_champions': main_champions,
        'privacy_prompt': privacy_prompt
    }
