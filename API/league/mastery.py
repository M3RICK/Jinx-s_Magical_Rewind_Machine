class ChampionMastery:

    def __init__(self, core):
        self.core = core

    def get_all_masteries(self, puuid, platform="euw1"):
        try:
            return self.core.watcher.champion_mastery.by_puuid(platform, puuid)
        except Exception as e:
            print(f"Error fetching all masteries: {e}")
            return None


    def get_top_masteries(self, puuid, platform="euw1", count=10):
        try:
            all_masteries = self.core.watcher.champion_mastery.by_puuid(
                platform,
                puuid
            )

            if all_masteries:
                sorted_masteries = sorted(
                    all_masteries,
                    key=lambda x: x['championPoints'],
                    reverse=True
                )
                return sorted_masteries[:count]

            return None
        except Exception as e:
            print(f"Error fetching top masteries: {e}")
            return None
