import asyncio
import json
from datetime import datetime
from ..Core import Core
from ..league.summoner import Summoner
from ..league.rank import Rank
from ..league.match import Match
from ..analytics.stats_extractor import extract_match_stats


class BenchmarkBuilder:
    def __init__(self, core=None):
        self.core = core or Core()
        self.summoner_api = Summoner(self.core)
        self.rank_api = Rank(self.core)
        self.match_api = Match(self.core)

    async def build_benchmarks(
        self,
        region,
        platform,
        matches_per_rank=100,
        output_file="API/benchmarks/benchmark_cache.json",
    ):
        print(f"\n{'=' * 60}")
        print(f"  Building Real Benchmarks from Match Data")
        print(f"{'=' * 60}\n")

        rank_tiers = [
            "IRON",
            "BRONZE",
            "SILVER",
            "GOLD",
            "PLATINUM",
            "EMERALD",
            "DIAMOND",
            "MASTER",
            "GRANDMASTER",
            "CHALLENGER",
        ]

        roles = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]

        raw_data = {rank: {role: {} for role in roles} for rank in rank_tiers}

        for rank in rank_tiers:
            print(f"\n[{rank}] Fetching matches...")

            players = await self.get_players_from_rank(rank, platform, limit=20)

            if not players:
                print(f"  ⚠ No players found for {rank}, skipping...")
                continue

            print(f"  Found {len(players)} {rank} players")

            match_ids = set()
            for i, player_puuid in enumerate(players):
                player_matches = await self.match_api.get_match_history(
                    player_puuid, region, count=10
                )
                if player_matches:
                    match_ids.update(player_matches)

                if len(match_ids) >= matches_per_rank:
                    break

                if (i + 1) % 5 == 0:
                    print(
                        f"    Progress: {i + 1}/{len(players)} players, {len(match_ids)} matches"
                    )
                    await asyncio.sleep(0.5)

            print(f"  Analyzing {len(match_ids)} matches...")

            for idx, match_id in enumerate(list(match_ids)[:matches_per_rank]):
                match_data = await self.match_api.get_match_details(match_id, region)
                if not match_data:
                    continue

                for participant in match_data["info"]["participants"]:
                    puuid = participant["puuid"]
                    stats = extract_match_stats(match_data, puuid)

                    if not stats:
                        continue

                    role = stats.get("role", "UNKNOWN")
                    if role not in roles:
                        continue

                    if role not in raw_data[rank]:
                        raw_data[rank][role] = {}

                    for key in [
                        "cs_per_min",
                        "vision_score",
                        "kda",
                        "cs_at_10",
                        "damage_per_min",
                        "gold_per_minute",
                        "kill_participation",
                    ]:
                        if key in stats and stats[key] is not None:
                            if key not in raw_data[rank][role]:
                                raw_data[rank][role][key] = []
                            raw_data[rank][role][key].append(stats[key])

                if (idx + 1) % 10 == 0:
                    print(
                        f"    Processed: {idx + 1}/{min(len(match_ids), matches_per_rank)}"
                    )
                    await asyncio.sleep(0.2)

        print(f"\n{'=' * 60}")
        print(f"  Calculating Benchmark Averages")
        print(f"{'=' * 60}\n")

        benchmarks = self.calculate_averages(raw_data)

        cache_data = {
            "generated_at": datetime.now().isoformat(),
            "region": region,
            "platform": platform,
            "matches_analyzed": matches_per_rank,
            "benchmarks": benchmarks,
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Benchmarks saved to {output_file}")
        print(f"  Generated at: {cache_data['generated_at']}")

        return benchmarks

    async def get_players_from_rank(self, rank, platform, limit=20):
        try:
            queue = "RANKED_SOLO_5x5"
            tier = rank
            division = "I"

            if rank in ["MASTER", "GRANDMASTER", "CHALLENGER"]:
                entries = await self.core.client.get_lol_league_v4_entries_by_division(
                    region=platform,
                    queue=queue,
                    tier=tier,
                    division="I",
                    queries={"page": 1}
                )
            else:
                entries = await self.core.client.get_lol_league_v4_entries_by_division(
                    region=platform,
                    queue=queue,
                    tier=tier,
                    division=division,
                    queries={"page": 1}
                )

            puuids = []
            for entry in entries[:limit]:
                summoner_id = entry.get("summonerId")
                if summoner_id:
                    summoner_data = await self.summoner_api.get_summoner_by_id(
                        summoner_id, platform
                    )
                    if summoner_data:
                        puuids.append(summoner_data.get("puuid"))

                if len(puuids) >= limit:
                    break

                await asyncio.sleep(0.1)

            return puuids

        except Exception as e:
            print(f"  Error fetching players: {e}")
            return []

    def calculate_averages(self, raw_data):
        benchmarks = {}

        for rank, roles in raw_data.items():
            benchmarks[rank] = {}

            for role, stats in roles.items():
                if not stats:
                    continue

                benchmarks[rank][role] = {}

                for stat_name, values in stats.items():
                    if values:
                        avg = sum(values) / len(values)
                        benchmarks[rank][role][stat_name] = round(avg, 2)

        return benchmarks
