from ..Core import Core
from ..riot.account import RiotAccountAPI
from ..league.summoner import Summoner
from ..league.rank import Rank
from ..league.match import Match
from ..league.mastery import ChampionMastery
from ..analytics.stats_extractor import extract_match_stats, extract_timeline_stats
from ..analytics.stats_aggregator import aggregate_stats, get_role_specific_stats
from ..benchmarks.benchmark_loader import get_benchmark, calculate_percentile
import json


class Player:

    def __init__(self, game_name, tag_line, region="europe", platform="euw1"):
        self.game_name = game_name
        self.tag_line = tag_line
        self.region = region
        self.platform = platform

        self._core = Core()

        self._account_api = RiotAccountAPI(self._core)
        self._summoner_api = Summoner(self._core)
        self._rank_api = Rank(self._core)
        self._match_api = Match(self._core)
        self._mastery_api = ChampionMastery(self._core)

        self.puuid = None
        self.summoner_info = None
        self.rank_info = None
        self.match_history = []
        self.processed_stats = []
        self.champion_mastery = None
        self.aggregated_stats = {}

        self._match_details_cache = {}


    def load_profile(self):
        print(f"Loading profile: {self.game_name}#{self.tag_line}")

        self.puuid = self._account_api.get_puuid(
            self.game_name, self.tag_line, self.region
        )
        if not self.puuid:
            print("Failed to get PUUID")
            return False

        self.summoner_info = self._summoner_api.get_summoner_infos(
            self.puuid, self.platform
        )
        self.rank_info = self._rank_api.get_rank_info(
            self.puuid, self.platform, by_puuid=True
        )
        self.champion_mastery = self._mastery_api.get_top_masteries(
            self.puuid, self.platform, count=5
        )

        print(f"Profile loaded")
        return True


    def _get_match_details_cached(self, match_id):
        if match_id not in self._match_details_cache:
            match_data = self._match_api.get_match_details(match_id, self.region)
            if match_data:
                self._match_details_cache[match_id] = match_data
        return self._match_details_cache.get(match_id)


    def _process_match_ids(self, match_ids):
        print(f"Fetching match details and extracting player data...")

        for i, match_id in enumerate(match_ids):
            match_data = self._get_match_details_cached(match_id)
            if match_data:
                player_stats = extract_match_stats(match_data, self.puuid)
                if player_stats:
                    self.processed_stats.append(player_stats)

            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{len(match_ids)}")

        print(f"Extracted data from {len(self.processed_stats)} matches")
        return self.processed_stats


    def load_recent_matches(self, count=100):
        print(f"\nLoading {count} most recent matches...")
        self.match_history = self._match_api.get_match_history(
            self.puuid, self.region, count=count
        )
        print(f"Found {len(self.match_history)} matches")

        return self._process_match_ids(self.match_history)


    def load_year_matches(self, year=2024):
        self.match_history = self._match_api.get_year_match_history(
            self.puuid, self.region, year
        )
        return self._process_match_ids(self.match_history)


    def load_match_timelines(self):
        if not self.match_history:
            print("No match history. Load matches first.")
            return []

        if not self.processed_stats:
            print("No processed stats. Load matches first.")
            return []

        print(f"\nFetching timelines for {len(self.match_history)} matches...")
        print(f"   (This will take a while due to rate limits)\n")

        stats_by_match_id = {stat["match_id"]: stat for stat in self.processed_stats}

        for i, match_id in enumerate(self.match_history):
            stat_entry = stats_by_match_id.get(match_id)

            if not stat_entry:
                continue

            timeline = self._match_api.get_match_timeline(match_id, self.region)
            if timeline:
                match_data = self._get_match_details_cached(match_id)
                if match_data:
                    timeline_stats = extract_timeline_stats(
                        match_data,
                        timeline,
                        self.puuid,
                        role=stat_entry.get("role")
                    )
                    if timeline_stats:
                        stat_entry.update(timeline_stats)

            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{len(self.match_history)}")

        print(f"\nTimeline data merged into processed stats\n")
        return self.processed_stats


    def process_matches(self):
        if not self.processed_stats:
            print("No processed stats. Call load_recent_matches() first.")
            return None

        print(f"\n{'=' * 60}")
        print(f"  Aggregating {len(self.processed_stats)} matches...")
        print(f"{'=' * 60}\n")

        self.aggregated_stats = aggregate_stats(
            self.processed_stats,
            self.puuid,
            self.game_name,
            self.tag_line,
            self.summoner_info,
            self.rank_info
        )

        print(f"Processing complete!\n")
        return self.aggregated_stats


    def add_benchmarks(self):
        if not self.aggregated_stats:
            print("No aggregated stats. Run process_matches() first.")
            return

        player_info = self.aggregated_stats.get("player_info", {})
        primary_role = player_info.get("primary_role")
        rank = player_info.get("rank", "UNRANKED")

        if rank == "UNRANKED":
            print("Player is unranked. Using SILVER benchmarks as default.")
            rank = "SILVER_I"

        rank_tier = rank.split("_")[0]

        benchmarks = {}

        farming = self.aggregated_stats.get("farming", {})
        early_game = self.aggregated_stats.get("early_game", {})
        vision = self.aggregated_stats.get("vision", {})
        overall = self.aggregated_stats.get("overall_performance", {})

        player_cs_per_min = farming.get("avg_cs_per_min")
        if player_cs_per_min and primary_role:
            cs_benchmark = get_benchmark("cs_per_min", primary_role, rank_tier)
            if cs_benchmark:
                benchmarks["cs_per_min"] = {
                    "player": round(player_cs_per_min, 2),
                    "benchmark": cs_benchmark,
                    "percentile": calculate_percentile(
                        player_cs_per_min,
                        cs_benchmark
                    ),
                    "difference": round(player_cs_per_min - cs_benchmark, 2),
                }

        player_cs_at_10 = early_game.get("avg_cs_at_10")
        if player_cs_at_10 and primary_role:
            cs10_benchmark = get_benchmark("cs_at_10", primary_role, rank_tier)
            if cs10_benchmark:
                benchmarks["cs_at_10"] = {
                    "player": round(player_cs_at_10, 1),
                    "benchmark": cs10_benchmark,
                    "percentile": calculate_percentile(
                        player_cs_at_10,
                        cs10_benchmark
                    ),
                    "difference": round(player_cs_at_10 - cs10_benchmark, 1),
                }

        player_vision = vision.get("avg_vision_score")
        if player_vision and primary_role:
            vision_benchmark = get_benchmark(
                "vision_score",
                primary_role,
                rank_tier
            )
            if vision_benchmark:
                benchmarks["vision_score"] = {
                    "player": round(player_vision, 1),
                    "benchmark": vision_benchmark,
                    "percentile": calculate_percentile(
                        player_vision,
                        vision_benchmark
                    ),
                    "difference": round(player_vision - vision_benchmark, 1),
                }

        player_kda = overall.get("avg_kda")
        if player_kda:
            kda_benchmark = get_benchmark("kda", None, rank_tier)
            if kda_benchmark:
                benchmarks["kda"] = {
                    "player": round(player_kda, 2),
                    "benchmark": kda_benchmark,
                    "percentile": calculate_percentile(
                        player_kda,
                        kda_benchmark
                    ),
                    "difference": round(player_kda - kda_benchmark, 2),
                }

        self.aggregated_stats["benchmarks"] = benchmarks
        print(f"Benchmarks added for {primary_role} @ {rank_tier}")
        return benchmarks


    def get_role_specific_stats(self, role=None):
        return get_role_specific_stats(self.aggregated_stats, role)


    def export_to_json(self, filepath="player_data.json"):
        data = {
            "player_info": {
                "game_name": self.game_name,
                "tag_line": self.tag_line,
                "puuid": self.puuid,
                "region": self.region,
                "platform": self.platform,
            },
            "summoner_info": self.summoner_info,
            "rank_info": self.rank_info,
            "champion_mastery": self.champion_mastery,
            "processed_stats": self.processed_stats,
            "aggregated_stats": (
                self.aggregated_stats if self.aggregated_stats else None
            ),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\nData exported to {filepath}")
        stats_count = len(self.processed_stats)
        print(f"  - {stats_count} player match stats (player-specific data only)")
        return filepath


    def __str__(self):
        rank_str = "Unranked"
        if self.rank_info:
            for queue in self.rank_info:
                if queue["queueType"] == "RANKED_SOLO_5x5":
                    rank_str = f"{queue['tier']} {queue['rank']}"
        return f"Player({self.game_name}#{self.tag_line}, {rank_str})"
