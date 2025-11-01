from ..utils.helpers import get_month_timestamps, get_month_name
import asyncio


class Match:

    def __init__(self, core):
        self.core = core

    async def get_match_history(
        self,
        puuid,
        region="europe",
        count=20,
        start=0,
        start_time=None,
        end_time=None
    ):
        try:
            queries = {
                "start": start,
                "count": count
            }
            if start_time is not None:
                queries["startTime"] = start_time
            if end_time is not None:
                queries["endTime"] = end_time

            matches = await self.core.client.get_lol_match_v5_match_ids_by_puuid(
                region=region,
                puuid=puuid,
                queries=queries
            )
            return matches
        except Exception as e:
            print(f"Error fetching match history: {e}")
            return None

    async def get_match_details(self, match_id, region="europe"):
        try:
            match_data = await self.core.client.get_lol_match_v5_match(
                region=region,
                id=match_id
            )
            return match_data
        except Exception as e:
            print(f"Error fetching match details for {match_id}: {e}")
            return None


    async def get_match_timeline(self, match_id, region="europe"):
        try:
            timeline = await self.core.client.get_lol_match_v5_match_timeline(
                region=region,
                id=match_id
            )
            return timeline
        except Exception as e:
            print(f"Error fetching match timeline for {match_id}: {e}")
            return None


    async def get_year_match_history(self, puuid, region="europe", year=2024):
        print(f"\n{'=' * 60}")
        print(f"  Fetching all matches for {year}")
        print(f"{'=' * 60}\n")

        all_match_ids = []

        for month in range(1, 13):
            start_time, end_time = get_month_timestamps(year, month)
            month_name = get_month_name(year, month)

            print(f"{month_name}...", end=" ")

            month_matches = await self._fetch_matches_with_pagination(
                puuid, region, start_time, end_time
            )

            all_match_ids.extend(month_matches)
            print(f"{len(month_matches)} matches")

            await asyncio.sleep(0.5)

        print(f"\n{'=' * 60}")
        print(f"Total: {len(all_match_ids)} matches")
        print(f"{'=' * 60}\n")

        return all_match_ids


    async def get_bulk_match_details(self, match_ids, region="europe"):
        print(f"Fetching details for {len(match_ids)} matches...")

        matches = []
        for i, match_id in enumerate(match_ids):
            match_data = await self.get_match_details(match_id, region)
            if match_data:
                matches.append(match_data)

            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{len(match_ids)}")

        print(f"Loaded {len(matches)} match details")
        return matches


    async def _fetch_matches_with_pagination(
        self,
        puuid,
        region,
        start_time,
        end_time
    ):
        all_matches = []
        start_index = 0
        batch_size = 100

        while True:
            batch = await self.get_match_history(
                puuid=puuid,
                region=region,
                count=batch_size,
                start=start_index,
                start_time=start_time,
                end_time=end_time,
            )

            if not batch or len(batch) == 0:
                break

            all_matches.extend(batch)

            if len(batch) < batch_size:
                break

            start_index += batch_size
            await asyncio.sleep(0.1)

        return all_matches
