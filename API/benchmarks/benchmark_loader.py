import json
import os
from datetime import datetime, timedelta
from .fallback_data import (
    CS_BENCHMARKS as FALLBACK_CS,
    CS_AT_10_BENCHMARKS as FALLBACK_CS_AT_10,
    VISION_SCORE_BENCHMARKS as FALLBACK_VISION,
    KDA_BENCHMARKS as FALLBACK_KDA
)


_BENCHMARK_CACHE = None
_CACHE_LOADED_AT = None


def load_benchmarks(cache_file="API/benchmarks/benchmark_cache.json", max_age_days=30):
    global _BENCHMARK_CACHE, _CACHE_LOADED_AT

    if _BENCHMARK_CACHE and _CACHE_LOADED_AT:
        return _BENCHMARK_CACHE

    if not os.path.exists(cache_file):
        print(f"[Benchmarks] Cache file not found: {cache_file}")
        print(f"[Benchmarks] Using fallback hardcoded values")
        return None

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            cache_data = json.load(f)

        generated_at = datetime.fromisoformat(cache_data["generated_at"])
        age = datetime.now() - generated_at

        if age > timedelta(days=max_age_days):
            print(f"[Benchmarks] Cache is {age.days} days old (max: {max_age_days})")
            print(f"[Benchmarks] Using fallback hardcoded values")
            print(f"[Benchmarks] Run benchmark_builder.py to refresh")
            return None

        _BENCHMARK_CACHE = cache_data["benchmarks"]
        _CACHE_LOADED_AT = datetime.now()

        print(f"[Benchmarks] Loaded real benchmarks from cache")
        print(f"[Benchmarks] Generated: {generated_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"[Benchmarks] Age: {age.days} days")

        return _BENCHMARK_CACHE

    except Exception as e:
        print(f"[Benchmarks] Error loading cache: {e}")
        print(f"[Benchmarks] Using fallback hardcoded values")
        return None


def get_benchmark(stat_type, role, rank):
    benchmarks = load_benchmarks()

    rank_tier = rank.split("_")[0] if rank else None

    if benchmarks and rank_tier in benchmarks:
        rank_data = benchmarks[rank_tier]

        if role and role in rank_data:
            role_data = rank_data[role]
            if stat_type in role_data:
                return role_data[stat_type]

        if stat_type == "kda":
            kda_values = []
            for role_name, role_data in rank_data.items():
                if "kda" in role_data:
                    kda_values.append(role_data["kda"])
            if kda_values:
                return round(sum(kda_values) / len(kda_values), 2)

    if stat_type == "cs_per_min":
        return FALLBACK_CS.get(role, {}).get(rank_tier)
    elif stat_type == "cs_at_10":
        return FALLBACK_CS_AT_10.get(role, {}).get(rank_tier)
    elif stat_type == "vision_score":
        return FALLBACK_VISION.get(role, {}).get(rank_tier)
    elif stat_type == "kda":
        return FALLBACK_KDA.get(rank_tier)

    return None


def calculate_percentile(player_value, benchmark_value):
    if not benchmark_value:
        return None

    deviation = (player_value - benchmark_value) / benchmark_value
    percentile = 50 + (deviation * 100)

    return max(1, min(99, int(percentile)))
