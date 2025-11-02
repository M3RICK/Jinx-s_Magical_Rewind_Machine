class Rank:

    def __init__(self, core):
        self.core = core

    async def get_rank_info(self, identifier, platform, by_puuid=True):
        try:
            if by_puuid:
                # Use PUUID directly to fetch league entries (more efficient)
                return await self.core.client.get_lol_league_v4_entries_by_puuid(
                    region=platform,
                    puuid=identifier
                )
            else:
                # Fallback: fetch by summoner ID
                return await self.core.client.get_lol_league_v4_entries_by_summoner(
                    region=platform,
                    encrypted_summoner_id=identifier
                )
        except Exception as e:
            print(f"Error fetching rank info: {e}")
            return None
