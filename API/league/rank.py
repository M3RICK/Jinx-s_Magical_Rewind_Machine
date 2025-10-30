class Rank:

    def __init__(self, core):
        self.core = core

    def get_rank_info(self, identifier, platform="euw1", by_puuid=True):
        try:
            if by_puuid:
                return self.core.watcher.league.by_puuid(platform, identifier)
            else:
                return self.core.watcher.league.by_summoner(platform, identifier)
        except Exception as e:
            print(f"Error fetching rank info: {e}")
            return None
