import requests


class Core:
    REGION_URLS = {
        "americas": "https://americas.api.riotgames.com",
        "europe": "https://europe.api.riotgames.com",
        "asia": "https://asia.api.riotgames.com",
        "sea": "https://sea.api.riotgames.com",
    }

    SERVERS_URLS = {
        "br1": "https://br1.api.riotgames.com",
        "euw1": "https://euw1.api.riotgames.com",
        "eun1": "https://eun1.api.riotgames.com",
        "jp1": "https://jp1.api.riotgames.com",
        "kr": "https://kr.api.riotgames.com",
        "la1": "https://la1.api.riotgames.com",
        "la2": "https://la2.api.riotgames.com",
        "me1": "https://me1.api.riotgames.com",
        "na1": "https://na1.api.riotgames.com",
        "oc1": "https://oc1.api.riotgames.com",
        "ru": "https://ru.api.riotgames.com",
        "sg2": "https://sg2.api.riotgames.com",
        "tr1": "https://tr1.api.riotgames.com",
        "tw2": "https://tw2.api.riotgames.com",
        "vn2": "https://vn2.api.riotgames.com",
    }

    def __init__(self, api_key_path="donotpush/riot_api_key.txt"):
        self.api_key = self._load_api_key(api_key_path)

    def _load_api_key(self, path):
        with open(path, "r") as f:
            return f.read().strip()

    def _make_request(self, url, params=None):
        headers = {"X-Riot-Token": self.api_key}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error {response.status_code}: {response.text}")
            return None
