import requests
import time
from riotwatcher import LolWatcher


class Core:

    REGION_URLS = {
        "americas": "https://americas.api.riotgames.com",
        "europe": "https://europe.api.riotgames.com",
        "asia": "https://asia.api.riotgames.com",
        "sea": "https://sea.api.riotgames.com",
    }

    def __init__(self, api_key_path="donotpush/riot_api_key.txt", shared_watcher=None):
        self.api_key = self._load_api_key(api_key_path)
        self.watcher = shared_watcher if shared_watcher else LolWatcher(self.api_key)

    def _load_api_key(self, path):
        with open(path, "r") as f:
            return f.read().strip()

    def _make_request(self, url, params=None):
        headers = {"X-Riot-Token": self.api_key}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 1))
            print(f"Rate limit hit, waiting {retry_after} seconds...")
            time.sleep(retry_after)
            return self._make_request(url, params)
        else:
            print(f"Error {response.status_code}: {response.text}")
            return None

    def _build_region_url(self, region, path):
        return f"{self.REGION_URLS[region]}{path}"
