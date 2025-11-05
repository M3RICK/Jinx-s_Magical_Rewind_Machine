class Rank:

    def __init__(self, core):
        self.core = core

    async def get_rank_info(self, identifier, platform, by_puuid=True):
        """
        Get rank information for a player.

        Args:
            identifier: PUUID or encrypted summoner ID
            platform: Platform region (e.g., 'euw1', 'na1')
            by_puuid: If True, use PUUID. If False, use summoner ID.

        Returns:
            List of league entries or None if not found
        """
        try:
            if by_puuid:
                # Use direct PUUID method (Riot API v4 supports this now)
                return await self.core.client.get_lol_league_v4_entries_by_puuid(
                    region=platform,
                    puuid=identifier
                )
            else:
                # Use summoner ID method
                return await self.core.client.get_lol_league_v4_entries_by_summoner(
                    region=platform,
                    encrypted_summoner_id=identifier
                )
        except Exception as e:
            print(f"[ERROR] Error fetching rank info: {e}")
            import traceback
            traceback.print_exc()
            return None
