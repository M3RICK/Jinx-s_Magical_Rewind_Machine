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
                if summoner and "id" in summoner:
                    summoner_id = summoner["id"]
                    return await self.core.client.get_lol_league_v4_entries_by_summoner(
                        region=platform,
                        encrypted_summoner_id=summoner_id
                    )
                else:
                    print(f"[WARNING] Summoner data incomplete or missing for PUUID: {identifier[:16]}...")
                    return None
            else:
                return await self.core.client.get_lol_league_v4_entries_by_summoner(
                    region=platform,
                    encrypted_summoner_id=identifier
                )
        except Exception as e:
            print(f"Error fetching rank info: {e}")
            import traceback
            traceback.print_exc()
            return None
