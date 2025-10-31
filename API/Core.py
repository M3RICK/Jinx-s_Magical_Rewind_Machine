import aiohttp, asyncio
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

    async def _make_request(self, url, params=None, retries=3):
        headers = {"X-Riot-Token": self.api_key}
        timeout = aiohttp.ClientTimeout(total=10)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()

                    elif response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", 1))
                        print(f"[429] Rate limit hit, waiting {retry_after}s...")
                        await asyncio.sleep(retry_after)
                        return await self._make_request(url, params, retries)

                    elif response.status in {500, 502, 503, 504}:
                        if retries > 0:
                            print(f"[{response.status}] Server error, retrying... ({retries} left)")
                            await asyncio.sleep(2)
                            return await self._make_request(url, params, retries - 1)
                        else:
                            print(f"[{response.status}] Server error, no retries left.")
                            return None
                    else:
                        text = await response.text()
                        print(f"[{response.status}] Unexpected error: {text[:200]}")
                        return None

        except aiohttp.ClientConnectorError:
            print("[ERROR] Connection failed (network issue or invalid URL).")
            return None

        except asyncio.TimeoutError:
            if retries > 0:
                print("[TIMEOUT] Retrying request...")
                return await self._make_request(url, params, retries - 1)
            else:
                print("[TIMEOUT] Request failed after multiple retries.")
                return None

        except aiohttp.ClientError as e:
            print(f"[CLIENT ERROR] {e}")
            return None

        except Exception as e:
            print(f"[UNEXPECTED ERROR] {type(e).__name__}: {e}")
            return None

    def _build_region_url(self, region, path):
        return f"{self.REGION_URLS[region]}{path}"
