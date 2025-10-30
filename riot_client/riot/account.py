from ..Core import Core


class RiotAccountAPI(Core):
    def get_puuid(self, game_name, tag_line, region="europe"):
        url = self._build_region_url(region, f"/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}")
        data = self._make_request(url)

        if data:
            return data["puuid"]
        return None
