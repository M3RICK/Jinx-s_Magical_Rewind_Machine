from ..Core import Core


class Rank(Core):
    def get_rank_info(self, identifier, platform="euw1", by_puuid=True):
        endpoint = "by-puuid" if by_puuid else "by-summoner"
        url = self._build_server_url(platform, f"/lol/league/v4/entries/{endpoint}/{identifier}")
        return self._make_request(url)
