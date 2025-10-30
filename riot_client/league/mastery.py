from ..Core import Core


class ChampionMastery(Core):
    def get_all_masteries(self, puuid, platform="euw1"):
        url = self._build_server_url(platform, f"/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}")
        return self._make_request(url)

    def get_top_masteries(self, puuid, platform="euw1", count=10):
        url = self._build_server_url(platform, f"/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/top")
        params = {"count": count}
        return self._make_request(url, params=params)
