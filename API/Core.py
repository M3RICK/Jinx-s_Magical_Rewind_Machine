import aiohttp, asyncio
import os
from pulsefire.clients import RiotAPIClient


class Core:
    REGION_URLS = {
        "americas": "https://americas.api.riotgames.com",
        "europe": "https://europe.api.riotgames.com",
        "asia": "https://asia.api.riotgames.com",
        "sea": "https://sea.api.riotgames.com",
    }

    def __init__(self):
        self.api_key = self.load_api_key()
        self.client = RiotAPIClient(default_headers={"X-Riot-Token": self.api_key})

    def load_api_key(self):
        api_key = os.getenv("RIOT_API_KEY")
        if api_key:
            return api_key.strip()

        raise ValueError(
            "RIOT_API_KEY not found please set RIOT_API_KEY environment variable in your .env file"
        )

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)
        await asyncio.sleep(0.1)  # petite pause pour fermer les connexions
        return False

    async def make_request(self, url, params=None, retries=3):
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
                        return await self.make_request(url, params, retries)

                    elif response.status in {500, 502, 503, 504}:
                        if retries > 0:
                            print(
                                f"[{response.status}] Server error, retrying... ({retries} left)"
                            )
                            await asyncio.sleep(2)
                            return await self.make_request(url, params, retries - 1)
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
                return await self.make_request(url, params, retries - 1)
            else:
                print("[TIMEOUT] Request failed after multiple retries.")
                return None

        except aiohttp.ClientError as e:
            print(f"[CLIENT ERROR] {e}")
            return None

        except Exception as e:
            print(f"[UNEXPECTED ERROR] {type(e).__name__}: {e}")
            return None

    def build_region_url(self, region, path):
        return f"{self.REGION_URLS[region]}{path}"
