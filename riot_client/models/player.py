<<<<<<< HEAD:API/models/player.py
from ..Core import Core
from ..riot.account import RiotAccountAPI
from ..league.summoner import Summoner
from ..league.rank import Rank
from ..league.match import Match
from ..league.mastery import ChampionMastery
from ..analytics.stats_extractor import extract_match_stats, extract_timeline_stats
from ..analytics.stats_aggregator import aggregate_stats, get_role_specific_stats
from ..benchmarks.benchmark_loader import get_benchmark, calculate_percentile
from ..utils.region_helper import get_region_config, get_region_from_platform
import json
=======
from riot_client.riot.account import RiotAccountAPI
from riot_client.league.summoner import Summoner
from riot_client.league.rank import Rank
from riot_client.league.match import Match
from riot_client.league.mastery import ChampionMastery
>>>>>>> dev:riot_client/models/player.py


class Player:

    def __init__(self, game_name, tag_line, platform=None, region=None):
        self.game_name = game_name
        self.tag_line = tag_line

        if not platform and not region:
            platform, region = get_region_config()
            if not platform:
                raise ValueError("Region selection required")
        elif platform and not region:
            region = get_region_from_platform(platform)
        elif not platform and region:
            raise ValueError("Platform must be specified when region is provided")

        self.platform = platform
        self.region = region

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

    async def __aenter__(self):
        await self._core.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self._core.__aexit__(exc_type, exc_val, exc_tb)


    async def load_profile(self):
        print(f"Loading profile: {self.game_name}#{self.tag_line}")

        self.puuid = await self._account_api.get_puuid(
            self.game_name, self.tag_line, self.region
        )
        if not self.puuid:
            print("Failed to get PUUID")
            return False

        self.summoner_info = await self._summoner_api.get_summoner_infos(
            self.puuid, self.platform
        )
        self.rank_info = await self._rank_api.get_rank_info(
            self.puuid, self.platform, by_puuid=True
        )
        self.champion_mastery = await self._mastery_api.get_top_masteries(
            self.puuid, self.platform, count=5
        )

        print(f"Profile loaded")
        return True


    async def _get_match_details_cached(self, match_id):
        if match_id not in self._match_details_cache:
            match_data = await self._match_api.get_match_details(match_id, self.region)
            if match_data:
                self._match_details_cache[match_id] = match_data
        return self._match_details_cache.get(match_id)


    async def _process_match_ids(self, match_ids):
        print(f"Fetching match details and extracting player data...")

        for i, match_id in enumerate(match_ids):
            match_data = await self._get_match_details_cached(match_id)
            if match_data:
                player_stats = extract_match_stats(match_data, self.puuid)
                if player_stats:
                    self.processed_stats.append(player_stats)

            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{len(match_ids)}")

        print(f"Extracted data from {len(self.processed_stats)} matches")
        return self.processed_stats


    async def load_recent_matches(self, count=100):
        print(f"\nLoading {count} most recent matches...")
        self.match_history = await self._match_api.get_match_history(
            self.puuid, self.region, count=count
        )
        print(f"Found {len(self.match_history)} matches")

        return await self._process_match_ids(self.match_history)


    async def load_year_matches(self, year=2024):
        self.match_history = await self._match_api.get_year_match_history(
            self.puuid, self.region, year
        )
        return await self._process_match_ids(self.match_history)


    async def load_match_timelines(self):
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

            timeline = await self._match_api.get_match_timeline(match_id, self.region)
            if timeline:
                match_data = await self._get_match_details_cached(match_id)
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
<<<<<<< HEAD:API/models/player.py
=======

    def _extract_match_stats(self, match):
        my_participant = None
        for participant in match["info"]["participants"]:
            if participant["puuid"] == self.puuid:
                my_participant = participant
                break

        if not my_participant:
            return None

        stats = {
            "match_id": match["metadata"]["matchId"],
            "game_duration": match["info"]["gameDuration"],
            "game_creation": match["info"]["gameCreation"],
            "game_end": match["info"]["gameEndTimestamp"],
            "queue_id": match["info"]["queueId"],
            # Role & champion
            "role": self._detect_role(my_participant),
            "champion_id": my_participant["championId"],
            "champion_name": my_participant["championName"],
            # Performance
            "win": my_participant["win"],
            "kills": my_participant["kills"],
            "deaths": my_participant["deaths"],
            "assists": my_participant["assists"],
            "kda": (my_participant["kills"] + my_participant["assists"])
            / max(my_participant["deaths"], 1),
            # Farming
            "total_minions_killed": my_participant["totalMinionsKilled"],
            "neutral_minions_killed": my_participant["neutralMinionsKilled"],
            "cs_per_min": (
                my_participant["totalMinionsKilled"]
                + my_participant["neutralMinionsKilled"]
            )
            / (match["info"]["gameDuration"] / 60),
            # Gold & Damage
            "gold_earned": my_participant["goldEarned"],
            "total_damage_to_champions": my_participant["totalDamageDealtToChampions"],
            "damage_per_min": my_participant["totalDamageDealtToChampions"]
            / (match["info"]["gameDuration"] / 60),
            # Vision
            "vision_score": my_participant["visionScore"],
            "wards_placed": my_participant["wardsPlaced"],
            "wards_killed": my_participant["wardsKilled"],
            "control_wards_placed": my_participant["detectorWardsPlaced"],
            "vision_score_per_min": my_participant["visionScore"]
            / (match["info"]["gameDuration"] / 60),
            # Objectives
            "turret_kills": my_participant["turretKills"],
            "inhibitor_kills": my_participant["inhibitorKills"],
            "dragon_kills": my_participant.get("dragonKills", 0),
            "baron_kills": my_participant.get("baronKills", 0),
            # Combat
            "double_kills": my_participant["doubleKills"],
            "triple_kills": my_participant["tripleKills"],
            "quadra_kills": my_participant["quadraKills"],
            "penta_kills": my_participant["pentaKills"],
            # Other
            "team_position": my_participant.get("teamPosition", "UNKNOWN"),
            "summoner_level": my_participant.get("summonerLevel", 0),
        }

        return stats

    def process_matches(self):
        if not self.matches:
            print("No matches loaded. Call load_recent_matches() first.")
            return None

        print(f"\n{'=' * 60}")
        print(f"  Processing {len(self.matches)} matches...")
        print(f"{'=' * 60}\n")

        processed_stats = []

        has_timelines = hasattr(self, "timelines") and self.timelines

        for i, match in enumerate(self.matches):
            stats = self._extract_match_stats(match)
            if stats:
                if has_timelines and i < len(self.timelines):
                    timeline_stats = self._extract_timeline_stats(match, self.timelines[i])
                    if timeline_stats:
                        stats.update(timeline_stats)
                processed_stats.append(stats)

        self.aggregated_stats = self._aggregate_stats(processed_stats)

        print(f"Processing complete!\n")
        return self.aggregated_stats

    def _extract_timeline_stats(self, match, timeline):
        my_participant = None
        participant_id = None

        for participant in match["info"]["participants"]:
            if participant["puuid"] == self.puuid:
                my_participant = participant
                participant_id = participant["participantId"]
                break

        if not my_participant or not timeline:
            return None

        timeline_stats = {
            "cs_at_10": 0,
            "gold_at_10": 0,
            "xp_at_10": 0,
            "level_at_10": 0,
            "death_events": [],
        }

        if "info" in timeline and "frames" in timeline["info"]:
            for frame in timeline["info"]["frames"]:
                timestamp_minutes = frame["timestamp"] / 60000

                if 9 <= timestamp_minutes <= 10:
                    participant_frame = frame["participantFrames"].get(str(participant_id))
                    if participant_frame:
                        timeline_stats["cs_at_10"] = (
                            participant_frame["minionsKilled"]
                            + participant_frame["jungleMinionsKilled"]
                        )
                        timeline_stats["gold_at_10"] = participant_frame["totalGold"]
                        timeline_stats["xp_at_10"] = participant_frame["xp"]
                        timeline_stats["level_at_10"] = participant_frame["level"]

                if "events" in frame:
                    for event in frame["events"]:
                        if (
                            event["type"] == "CHAMPION_KILL"
                            and event.get("victimId") == participant_id
                        ):
                            death_time = event["timestamp"] / 60000
                            timeline_stats["death_events"].append(
                                {
                                    "timestamp": death_time,
                                    "x": event.get("position", {}).get("x", 0),
                                    "y": event.get("position", {}).get("y", 0),
                                    "killer_id": event.get("killerId"),
                                }
                            )

        deaths_0_10 = sum(1 for d in timeline_stats["death_events"] if d["timestamp"] <= 10)
        deaths_10_20 = sum(1 for d in timeline_stats["death_events"] if 10 < d["timestamp"] <= 20)
        deaths_20_30 = sum(1 for d in timeline_stats["death_events"] if 20 < d["timestamp"] <= 30)
        deaths_30_plus = sum(1 for d in timeline_stats["death_events"] if d["timestamp"] > 30)

        timeline_stats["death_timing"] = {
            "0-10min": deaths_0_10,
            "10-20min": deaths_10_20,
            "20-30min": deaths_20_30,
            "30min+": deaths_30_plus,
        }

        return timeline_stats

    def _aggregate_stats(self, processed_stats):
        if not processed_stats:
            return {}

        from datetime import datetime

        total_games = len(processed_stats)

        role_counts = {}
        for stat in processed_stats:
            role = stat["role"]
            role_counts[role] = role_counts.get(role, 0) + 1

        primary_role = max(role_counts, key=role_counts.get)

        wins = sum(1 for s in processed_stats if s["win"])

        champion_stats = {}
        for stat in processed_stats:
            champ_id = stat["champion_id"]
            if champ_id not in champion_stats:
                champion_stats[champ_id] = {
                    "champion_name": stat["champion_name"],
                    "games": 0,
                    "wins": 0,
                    "total_kda": 0,
                    "total_cs_per_min": 0,
                }

            champion_stats[champ_id]["games"] += 1
            if stat["win"]:
                champion_stats[champ_id]["wins"] += 1
            champion_stats[champ_id]["total_kda"] += stat["kda"]
            champion_stats[champ_id]["total_cs_per_min"] += stat["cs_per_min"]

        champion_performance = []
        for champ_id, data in champion_stats.items():
            champion_performance.append(
                {
                    "champion_id": champ_id,
                    "champion_name": data["champion_name"],
                    "games": data["games"],
                    "win_rate": data["wins"] / data["games"],
                    "avg_kda": round(data["total_kda"] / data["games"], 2),
                    "avg_cs_per_min": round(data["total_cs_per_min"] / data["games"], 2),
                }
            )

        champion_performance.sort(key=lambda x: x["games"], reverse=True)

        stats_with_cs10 = [
            s for s in processed_stats if "cs_at_10" in s and s["cs_at_10"] > 0
        ]

        if stats_with_cs10:
            avg_cs_at_10 = sum(s["cs_at_10"] for s in stats_with_cs10) / len(stats_with_cs10)
            avg_gold_at_10 = sum(s["gold_at_10"] for s in stats_with_cs10) / len(stats_with_cs10)
        else:
            avg_cs_at_10 = None
            avg_gold_at_10 = None

        all_death_events = []
        death_timing_total = {"0-10min": 0, "10-20min": 0, "20-30min": 0, "30min+": 0}

        for stat in processed_stats:
            if "death_events" in stat:
                all_death_events.extend(stat["death_events"])
            if "death_timing" in stat:
                for period, count in stat["death_timing"].items():
                    death_timing_total[period] += count

        monthly_performance = {}

        for stat in processed_stats:
            if "game_creation" in stat:
                date = datetime.fromtimestamp(stat["game_creation"] / 1000)
                month_key = date.strftime("%Y-%m")

                if month_key not in monthly_performance:
                    monthly_performance[month_key] = {
                        "games": 0,
                        "wins": 0,
                        "total_kda": 0,
                    }

                monthly_performance[month_key]["games"] += 1
                if stat["win"]:
                    monthly_performance[month_key]["wins"] += 1
                monthly_performance[month_key]["total_kda"] += stat["kda"]

        for month, data in monthly_performance.items():
            data["win_rate"] = round(data["wins"] / data["games"], 2)
            data["avg_kda"] = round(data["total_kda"] / data["games"], 2)

        aggregated = {
            "player_info": {
                "puuid": self.puuid,
                "game_name": self.game_name,
                "tag_line": self.tag_line,
                "summoner_level": self.summoner_info.get("summonerLevel")
                if self.summoner_info
                else 0,
                "total_games_analyzed": total_games,
                "primary_role": primary_role,
                "rank": self._get_rank_string(),
            },
            "role_distribution": role_counts,
            "overall_performance": {
                "total_games": total_games,
                "wins": wins,
                "losses": total_games - wins,
                "win_rate": round(wins / total_games, 3),
                "avg_kda": round(
                    sum(s["kda"] for s in processed_stats) / total_games, 2
                ),
                "avg_kills": round(
                    sum(s["kills"] for s in processed_stats) / total_games, 2
                ),
                "avg_deaths": round(
                    sum(s["deaths"] for s in processed_stats) / total_games, 2
                ),
                "avg_assists": round(
                    sum(s["assists"] for s in processed_stats) / total_games, 2
                ),
            },
            "early_game": {
                "avg_cs_at_10": round(avg_cs_at_10, 1) if avg_cs_at_10 else None,
                "avg_gold_at_10": round(avg_gold_at_10, 0) if avg_gold_at_10 else None,
            },
            "farming": {
                "avg_cs_per_min": round(
                    sum(s["cs_per_min"] for s in processed_stats) / total_games, 2
                ),
            },
            "vision": {
                "avg_vision_score": round(
                    sum(s["vision_score"] for s in processed_stats) / total_games, 1
                ),
                "avg_wards_placed": round(
                    sum(s["wards_placed"] for s in processed_stats) / total_games, 1
                ),
                "avg_control_wards": round(
                    sum(s["control_wards_placed"] for s in processed_stats) / total_games,
                    1,
                ),
            },
            "damage": {
                "avg_damage_per_min": round(
                    sum(s["damage_per_min"] for s in processed_stats) / total_games, 0
                ),
            },
            "death_analysis": {
                "total_deaths": sum(s["deaths"] for s in processed_stats),
                "death_timing": death_timing_total,
                "death_events": all_death_events,
            },
            "champion_performance": champion_performance[:10],
            "monthly_trends": dict(sorted(monthly_performance.items())),
            "raw_match_stats": processed_stats,
        }

        return aggregated

    def get_role_specific_stats(self, role=None):
        if not self.aggregated_stats:
            print("No aggregated stats. Call process_matches() first.")
            return None

        target_role = role or self.aggregated_stats["player_info"]["primary_role"]

        role_matches = [
            m
            for m in self.aggregated_stats["raw_match_stats"]
            if m["role"] == target_role
        ]

        if not role_matches:
            return None

        total = len(role_matches)
        wins = sum(1 for m in role_matches if m["win"])

        return {
            "role": target_role,
            "games": total,
            "win_rate": wins / total,
            "avg_kda": sum(m["kda"] for m in role_matches) / total,
            "avg_cs_per_min": sum(m["cs_per_min"] for m in role_matches) / total,
            "avg_vision_score": sum(m["vision_score"] for m in role_matches) / total,
            "avg_damage_per_min": sum(m["damage_per_min"] for m in role_matches)
            / total,
        }

    def load_match_timelines(self):
        if not self.match_history:
            print("No match history. Load matches first.")
            return []

        print(f"\nFetching timelines for {len(self.match_history)} matches...")
        print(f"   (This will take a while due to rate limits)\n")

        self.timelines = []

        for i, match_id in enumerate(self.match_history):
            timeline = self._match_api.get_match_timeline(match_id, self.region)
            if timeline:
                self.timelines.append(timeline)

            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{len(self.match_history)}")

        print(f"\nLoaded {len(self.timelines)} timelines\n")
        return self.timelines

    def _get_rank_string(self):
        if self.rank_info:
            for queue in self.rank_info:
                if queue["queueType"] == "RANKED_SOLO_5x5":
                    return f"{queue['tier']}_{queue['rank']}"
        return "UNRANKED"

    def add_benchmarks(self):
        from riot_client.benchmarks import get_benchmark, calculate_percentile

        if not self.aggregated_stats:
            print("No aggregated stats. Call process_matches() first.")
            return

        rank = self.aggregated_stats["player_info"].get("rank", "UNRANKED")
        primary_role = self.aggregated_stats["player_info"]["primary_role"]

        player_cs_per_min = self.aggregated_stats["farming"]["avg_cs_per_min"]
        player_vision = self.aggregated_stats["vision"]["avg_vision_score"]
        player_kda = self.aggregated_stats["overall_performance"]["avg_kda"]
        player_cs_at_10 = self.aggregated_stats.get("early_game", {}).get("avg_cs_at_10")

        benchmark_cs_per_min = get_benchmark("cs_per_min", primary_role, rank)
        benchmark_vision = get_benchmark("vision_score", primary_role, rank)
        benchmark_kda = get_benchmark("kda", primary_role, rank)
        benchmark_cs_at_10 = get_benchmark("cs_at_10", primary_role, rank)

        self.aggregated_stats["benchmarks"] = {
            "rank": rank,
            "role": primary_role,
            "cs_per_min": {
                "player": player_cs_per_min,
                "rank_average": benchmark_cs_per_min,
                "percentile": calculate_percentile(
                    player_cs_per_min, benchmark_cs_per_min
                ),
                "difference": round(player_cs_per_min - benchmark_cs_per_min, 2)
                if benchmark_cs_per_min
                else None,
            },
            "vision_score": {
                "player": player_vision,
                "rank_average": benchmark_vision,
                "percentile": calculate_percentile(player_vision, benchmark_vision),
                "difference": round(player_vision - benchmark_vision, 1)
                if benchmark_vision
                else None,
            },
            "kda": {
                "player": player_kda,
                "rank_average": benchmark_kda,
                "percentile": calculate_percentile(player_kda, benchmark_kda),
                "difference": round(player_kda - benchmark_kda, 2)
                if benchmark_kda
                else None,
            },
        }

        if player_cs_at_10 and benchmark_cs_at_10:
            self.aggregated_stats["benchmarks"]["cs_at_10"] = {
                "player": player_cs_at_10,
                "rank_average": benchmark_cs_at_10,
                "percentile": calculate_percentile(player_cs_at_10, benchmark_cs_at_10),
                "difference": round(player_cs_at_10 - benchmark_cs_at_10, 1),
            }

    def identify_weaknesses(self):
        if "benchmarks" not in self.aggregated_stats:
            print("No benchmarks. Call add_benchmarks() first.")
            return [], []

        weaknesses = []
        strengths = []

        benchmarks = self.aggregated_stats["benchmarks"]

        if (
            benchmarks["cs_per_min"]["percentile"]
            and benchmarks["cs_per_min"]["percentile"] < 40
        ):
            diff_percent = abs(
                benchmarks["cs_per_min"]["difference"]
                / benchmarks["cs_per_min"]["rank_average"]
                * 100
            )
            weaknesses.append(
                f"CS per minute is {diff_percent:.0f}% below rank average "
                f"({benchmarks['cs_per_min']['player']:.1f} vs {benchmarks['cs_per_min']['rank_average']:.1f})"
            )
        elif (
            benchmarks["cs_per_min"]["percentile"]
            and benchmarks["cs_per_min"]["percentile"] > 60
        ):
            strengths.append(
                f"Strong farming (top {100 - benchmarks['cs_per_min']['percentile']}%)"
            )

        if (
            benchmarks["vision_score"]["percentile"]
            and benchmarks["vision_score"]["percentile"] < 40
        ):
            diff_percent = abs(
                benchmarks["vision_score"]["difference"]
                / benchmarks["vision_score"]["rank_average"]
                * 100
            )
            weaknesses.append(
                f"Vision score is {diff_percent:.0f}% below rank average "
                f"({benchmarks['vision_score']['player']:.1f} vs {benchmarks['vision_score']['rank_average']})"
            )
        elif (
            benchmarks["vision_score"]["percentile"]
            and benchmarks["vision_score"]["percentile"] > 60
        ):
            strengths.append(
                f"Good vision control (top {100 - benchmarks['vision_score']['percentile']}%)"
            )

        if benchmarks["kda"]["percentile"] and benchmarks["kda"]["percentile"] < 40:
            weaknesses.append(
                f"KDA below rank average "
                f"({benchmarks['kda']['player']:.2f} vs {benchmarks['kda']['rank_average']:.2f})"
            )
        elif benchmarks["kda"]["percentile"] and benchmarks["kda"]["percentile"] > 60:
            strengths.append(f"High KDA (top {100 - benchmarks['kda']['percentile']}%)")

        if "cs_at_10" in benchmarks and benchmarks["cs_at_10"]["percentile"]:
            if benchmarks["cs_at_10"]["percentile"] < 40:
                weaknesses.append(
                    f"Early game CS is weak (CS@10: {benchmarks['cs_at_10']['player']:.0f} vs "
                    f"rank avg {benchmarks['cs_at_10']['rank_average']})"
                )
            elif benchmarks["cs_at_10"]["percentile"] > 60:
                strengths.append(
                    f"Strong early laning (top {100 - benchmarks['cs_at_10']['percentile']}%)"
                )

        if "death_analysis" in self.aggregated_stats:
            death_timing = self.aggregated_stats["death_analysis"]["death_timing"]
            total_deaths = sum(death_timing.values())

            if total_deaths > 0:
                early_death_percent = death_timing["0-10min"] / total_deaths
                if early_death_percent > 0.25:
                    weaknesses.append(
                        f"Dies too often in early game ({early_death_percent * 100:.0f}% of deaths before 10min)"
                    )

        champ_perf = self.aggregated_stats.get("champion_performance", [])
        if champ_perf:
            top_champ = champ_perf[0]
            if top_champ["games"] >= 10:
                if top_champ["win_rate"] < 0.45:
                    weaknesses.append(
                        f"Low win rate on most-played champion {top_champ['champion_name']} ({top_champ['win_rate'] * 100:.0f}%)"
                    )
                elif top_champ["win_rate"] > 0.55:
                    strengths.append(
                        f"High win rate on {top_champ['champion_name']} ({top_champ['win_rate'] * 100:.0f}%)"
                    )

        self.aggregated_stats["weaknesses"] = weaknesses
        self.aggregated_stats["strengths"] = strengths

        return weaknesses, strengths
>>>>>>> dev:riot_client/models/player.py
