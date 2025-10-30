from ..Core import Core


class Summoner(Core):
    def get_summoner_infos(self, puuid, platform="euw1"):
        url = self._build_server_url(platform, f"/lol/summoner/v4/summoners/by-puuid/{puuid}")
        return self._make_request(url)
