class Summoner:

    def __init__(self, core):
        self.core = core

    async def get_summoner_infos(self, puuid, platform):
        try:
            summoner = await self.core.client.get_lol_summoner_v4_by_puuid(
                region=platform,
                puuid=puuid
            )
            return summoner
        except Exception as e:
            print(f"Error fetching summoner info: {e}")
            return None

    async def get_summoner_by_id(self, summoner_id, platform):
        try:
            summoner = await self.core.client.get_lol_summoner_v4_by_id(
                region=platform,
                encrypted_summoner_id=summoner_id
            )
            return summoner
        except Exception as e:
            print(f"Error fetching summoner by ID: {e}")
            return None
