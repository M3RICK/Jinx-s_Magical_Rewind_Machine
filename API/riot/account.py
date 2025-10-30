class RiotAccountAPI:

    def __init__(self, core):
        self.core = core

    def get_puuid(self, game_name, tag_line, region="europe"):
        url = self.core._build_region_url(
            region, f"/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        )
        data = self.core._make_request(url)

        if data:
            return data["puuid"]
        return None
