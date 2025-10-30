class Summoner:

    def __init__(self, core):
        self.core = core

    def get_summoner_infos(self, puuid, platform="euw1"):
        try:
            return self.core.watcher.summoner.by_puuid(platform, puuid)
        except Exception as e:
            print(f"Error fetching summoner info: {e}")
            return None

    def get_summoner_by_id(self, summoner_id, platform="euw1"):
        try:
            return self.core.watcher.summoner.by_id(platform, summoner_id)
        except Exception as e:
            print(f"Error fetching summoner by ID: {e}")
            return None
