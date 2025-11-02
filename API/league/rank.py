class Rank:

    def __init__(self, core):
        self.core = core

    async def get_rank_info(self, identifier, platform, by_puuid=True):
        try:
            if by_puuid:
                summoner = await self.core.client.get_lol_summoner_v4_by_puuid(
                    region=platform,
                    puuid=identifier
                )
                if summoner:
                    summoner_id = summoner["id"]
                    return await self.core.client.get_lol_league_v4_entries_by_summoner(
                        region=platform,
                        encrypted_summoner_id=summoner_id
                    )
            else:
                return await self.core.client.get_lol_league_v4_entries_by_summoner(
                    region=platform,
                    encrypted_summoner_id=identifier
                )
            return None
        except Exception as e:
            print(f"Error fetching rank info: {e}")
            return None
