from ..Core import Core
from datetime import datetime
import time


class Match(Core):
    def get_match_history(
        self, puuid, region="europe", count=20, start=0, start_time=None, end_time=None
    ):
        url = self._build_region_url(
            region, f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
        )

        params = {"count": count, "start": start}
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        return self._make_request(url, params=params)

    def get_match_details(self, match_id, region="europe"):
        url = self._build_region_url(region, f"/lol/match/v5/matches/{match_id}")
        return self._make_request(url)

    def get_match_timeline(self, match_id, region="europe"):
        url = self._build_region_url(
            region, f"/lol/match/v5/matches/{match_id}/timeline"
        )
        return self._make_request(url)

    def get_year_match_history(self, puuid, region="europe", year=2024):
        print(f"\n{'=' * 60}")
        print(f"  Fetching all matches for {year}")
        print(f"{'=' * 60}\n")

        all_match_ids = []

        for month in range(1, 13):
            start_time, end_time = self._get_month_timestamps(year, month)
            month_name = self._get_month_name(year, month)

            print(f"{month_name}...", end=" ")

            month_matches = self._fetch_matches_with_pagination(
                puuid, region, start_time, end_time
            )

            all_match_ids.extend(month_matches)
            print(f"{len(month_matches)} matches")

            time.sleep(0.5)

        print(f"\n{'=' * 60}")
        print(f"Total: {len(all_match_ids)} matches")
        print(f"{'=' * 60}\n")

        return all_match_ids

    def get_bulk_match_details(self, match_ids, region="europe"):
        print(f"Fetching details for {len(match_ids)} matches...")

        matches = []
        for i, match_id in enumerate(match_ids):
            match_data = self.get_match_details(match_id, region)
            if match_data:
                matches.append(match_data)

            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{len(match_ids)}")

        print(f"Loaded {len(matches)} match details")
        return matches

    def _fetch_matches_with_pagination(self, puuid, region, start_time, end_time):
        all_matches = []
        start_index = 0
        batch_size = 100

        while True:
            batch = self.get_match_history(
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
            time.sleep(0.1)

        return all_matches

    def _get_month_timestamps(self, year, month):
        start_date = datetime(year, month, 1)

        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        return int(start_date.timestamp()), int(end_date.timestamp())

    def _get_month_name(self, year, month):
        date = datetime(year, month, 1)
        return date.strftime("%B %Y")

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
            "match_id": match["metadata"]["matchId"],
            "cs_at_10": 0,
            "gold_at_10": 0,
            "xp_at_10": 0,
            "level_at_10": 0,
            "deaths": [],  # List of death events with timestamps and locations
            "total_deaths": my_participant["deaths"],
        }

        # Process timeline frames (every minute)
        if "info" in timeline and "frames" in timeline["info"]:
            for frame in timeline["info"]["frames"]:
                timestamp_minutes = frame["timestamp"] / 60000  # Convert ms to minutes

                # Get stats at 10 minutes
                if 9 <= timestamp_minutes <= 10:
                    participant_frame = frame["participantFrames"].get(
                        str(participant_id)
                    )
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
                            death_time = event["timestamp"] / 60000  # Minutes
                            timeline_stats["deaths"].append(
                                {
                                    "timestamp": death_time,
                                    "x": event.get("position", {}).get("x", 0),
                                    "y": event.get("position", {}).get("y", 0),
                                    "killer_id": event.get("killerId"),
                                }
                            )

        deaths_0_10 = sum(1 for d in timeline_stats["deaths"] if d["timestamp"] <= 10)
        deaths_10_20 = sum(
            1 for d in timeline_stats["deaths"] if 10 < d["timestamp"] <= 20
        )
        deaths_20_30 = sum(
            1 for d in timeline_stats["deaths"] if 20 < d["timestamp"] <= 30
        )
        deaths_30_plus = sum(1 for d in timeline_stats["deaths"] if d["timestamp"] > 30)

        timeline_stats["death_timing"] = {
            "0-10min": deaths_0_10,
            "10-20min": deaths_10_20,
            "20-30min": deaths_20_30,
            "30min+": deaths_30_plus,
        }

        return timeline_stats

    def process_matches(self):
        if not self.matches:
            print("No matches loaded.")
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
                    timeline_stats = self._extract_timeline_stats(
                        match, self.timelines[i]
                    )
                    if timeline_stats:
                        stats.update(timeline_stats)

                processed_stats.append(stats)

        self.aggregated_stats = self._aggregate_enhanced_stats(processed_stats)

        print(f"Processing complete!\n")
        return self.aggregated_stats

    def _aggregate_enhanced_stats(self, processed_stats):
        if not processed_stats:
            return {}

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
                    "avg_cs_per_min": round(
                        data["total_cs_per_min"] / data["games"], 2
                    ),
                }
            )

        champion_performance.sort(key=lambda x: x["games"], reverse=True)

        stats_with_cs10 = [
            s for s in processed_stats if "cs_at_10" in s and s["cs_at_10"] > 0
        ]

        if stats_with_cs10:
            avg_cs_at_10 = sum(s["cs_at_10"] for s in stats_with_cs10) / len(
                stats_with_cs10
            )
            avg_gold_at_10 = sum(s["gold_at_10"] for s in stats_with_cs10) / len(
                stats_with_cs10
            )
        else:
            avg_cs_at_10 = None
            avg_gold_at_10 = None

        all_deaths = []
        death_timing_total = {"0-10min": 0, "10-20min": 0, "20-30min": 0, "30min+": 0}

        for stat in processed_stats:
            if "deaths" in stat:
                all_deaths.extend(stat["deaths"])
                if "death_timing" in stat:
                    for period, count in stat["death_timing"].items():
                        death_timing_total[period] += count

        from datetime import datetime

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
                    sum(s["control_wards_placed"] for s in processed_stats)
                    / total_games,
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
                "death_locations": all_deaths,
            },
            "champion_performance": champion_performance[:10],
            "monthly_trends": dict(sorted(monthly_performance.items())),
            "raw_match_stats": processed_stats,
        }

        return aggregated

    def _get_rank_string(self):
        if self.rank_info:
            for queue in self.rank_info:
                if queue["queueType"] == "RANKED_SOLO_5x5":
                    return f"{queue['tier']}_{queue['rank']}"
                    return "UNRANKED"

    def add_benchmarks(self):
        if not self.aggregated_stats:
            print("No aggregated stats. Call process_matches() first.")
            return

        rank = self.aggregated_stats["player_info"]["rank"]
        primary_role = self.aggregated_stats["player_info"]["primary_role"]

        player_cs_per_min = self.aggregated_stats["farming"]["avg_cs_per_min"]
        player_vision = self.aggregated_stats["vision"]["avg_vision_score"]
        player_kda = self.aggregated_stats["overall_performance"]["avg_kda"]
        player_cs_at_10 = self.aggregated_stats["early_game"].get("avg_cs_at_10")

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
            return []

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

        death_timing = self.aggregated_stats["death_analysis"]["death_timing"]
        total_deaths = sum(death_timing.values())

        if total_deaths > 0:
            early_death_percent = death_timing["0-10min"] / total_deaths
            if early_death_percent > 0.25:
                weaknesses.append(
                    f"Dies too often in early game ({early_death_percent * 100:.0f}% of deaths before 10min)"
                )

        champ_perf = self.aggregated_stats["champion_performance"]
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
