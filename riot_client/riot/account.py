class RiotAccountAPI:

    def __init__(self, core):
        self.core = core

    async def get_puuid(self, game_name, tag_line, region="europe"):
        try:
            account = await self.core.client.get_account_v1_by_riot_id(
                region=region,
                game_name=game_name,
                tag_line=tag_line
            )
            if account:
                return account["puuid"]
            return None
        except Exception as e:
            print(f"Error fetching PUUID for {game_name}#{tag_line}: {e}")
            return None
