class ChampionMastery:

    def __init__(self, core):
        self.core = core

    async def get_all_masteries(self, puuid, platform):
        try:
            masteries = await self.core.client.get_lol_champion_v4_masteries_by_puuid(
                region=platform,
                puuid=puuid
            )
            return masteries
        except Exception as e:
            print(f"Error fetching all masteries: {e}")
            return None


    async def get_top_masteries(self, puuid, platform, count=10):
        try:
            top_masteries = await self.core.client.get_lol_champion_v4_top_masteries_by_puuid(
                region=platform,
                puuid=puuid
            )
            return top_masteries[:count] if top_masteries else []
        except Exception as e:
            print(f"Error fetching top masteries: {e}")
            return None
