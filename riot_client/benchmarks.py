# CS per minute benchmarks by rank and role
CS_BENCHMARKS = {
    "TOP": {
        "IRON": 4.5,
        "BRONZE": 5.0,
        "SILVER": 5.5,
        "GOLD": 6.0,
        "PLATINUM": 6.5,
        "EMERALD": 7.0,
        "DIAMOND": 7.5,
        "MASTER": 8.0,
        "GRANDMASTER": 8.5,
        "CHALLENGER": 9.0,
    },
    "JUNGLE": {
        "IRON": 3.5,
        "BRONZE": 4.0,
        "SILVER": 4.5,
        "GOLD": 5.0,
        "PLATINUM": 5.5,
        "EMERALD": 6.0,
        "DIAMOND": 6.5,
        "MASTER": 7.0,
        "GRANDMASTER": 7.5,
        "CHALLENGER": 8.0,
    },
    "MIDDLE": {
        "IRON": 4.8,
        "BRONZE": 5.3,
        "SILVER": 5.8,
        "GOLD": 6.3,
        "PLATINUM": 6.8,
        "EMERALD": 7.3,
        "DIAMOND": 7.8,
        "MASTER": 8.3,
        "GRANDMASTER": 8.8,
        "CHALLENGER": 9.3,
    },
    "BOTTOM": {
        "IRON": 5.0,
        "BRONZE": 5.5,
        "SILVER": 6.0,
        "GOLD": 6.5,
        "PLATINUM": 7.0,
        "EMERALD": 7.5,
        "DIAMOND": 8.0,
        "MASTER": 8.5,
        "GRANDMASTER": 9.0,
        "CHALLENGER": 9.5,
    },
    "UTILITY": {
        "IRON": 1.5,
        "BRONZE": 1.8,
        "SILVER": 2.0,
        "GOLD": 2.2,
        "PLATINUM": 2.5,
        "EMERALD": 2.7,
        "DIAMOND": 3.0,
        "MASTER": 3.2,
        "GRANDMASTER": 3.5,
        "CHALLENGER": 3.8,
    },
}

# CS at 10min benchmarks
CS_AT_10_BENCHMARKS = {
    "TOP": {
        "IRON": 55,
        "BRONZE": 60,
        "SILVER": 65,
        "GOLD": 70,
        "PLATINUM": 75,
        "EMERALD": 80,
        "DIAMOND": 85,
        "MASTER": 90,
        "GRANDMASTER": 92,
        "CHALLENGER": 95,
    },
    "MIDDLE": {
        "IRON": 58,
        "BRONZE": 63,
        "SILVER": 68,
        "GOLD": 73,
        "PLATINUM": 78,
        "EMERALD": 83,
        "DIAMOND": 88,
        "MASTER": 92,
        "GRANDMASTER": 95,
        "CHALLENGER": 98,
    },
    "BOTTOM": {
        "IRON": 60,
        "BRONZE": 65,
        "SILVER": 70,
        "GOLD": 75,
        "PLATINUM": 80,
        "EMERALD": 85,
        "DIAMOND": 90,
        "MASTER": 95,
        "GRANDMASTER": 98,
        "CHALLENGER": 100,
    },
}

# Vision score benchmarks
VISION_SCORE_BENCHMARKS = {
    "TOP": {
        "IRON": 8,
        "BRONZE": 10,
        "SILVER": 12,
        "GOLD": 14,
        "PLATINUM": 16,
        "EMERALD": 18,
        "DIAMOND": 20,
        "MASTER": 22,
        "GRANDMASTER": 24,
        "CHALLENGER": 26,
    },
    "JUNGLE": {
        "IRON": 12,
        "BRONZE": 15,
        "SILVER": 18,
        "GOLD": 21,
        "PLATINUM": 24,
        "EMERALD": 27,
        "DIAMOND": 30,
        "MASTER": 33,
        "GRANDMASTER": 36,
        "CHALLENGER": 40,
    },
    "MIDDLE": {
        "IRON": 10,
        "BRONZE": 12,
        "SILVER": 14,
        "GOLD": 16,
        "PLATINUM": 18,
        "EMERALD": 20,
        "DIAMOND": 22,
        "MASTER": 24,
        "GRANDMASTER": 26,
        "CHALLENGER": 28,
    },
    "BOTTOM": {
        "IRON": 12,
        "BRONZE": 15,
        "SILVER": 18,
        "GOLD": 21,
        "PLATINUM": 24,
        "EMERALD": 27,
        "DIAMOND": 30,
        "MASTER": 33,
        "GRANDMASTER": 36,
        "CHALLENGER": 40,
    },
    "UTILITY": {
        "IRON": 20,
        "BRONZE": 25,
        "SILVER": 30,
        "GOLD": 35,
        "PLATINUM": 40,
        "EMERALD": 45,
        "DIAMOND": 50,
        "MASTER": 55,
        "GRANDMASTER": 60,
        "CHALLENGER": 65,
    },
}

# KDA benchmarks
KDA_BENCHMARKS = {
    "IRON": 2.0,
    "BRONZE": 2.2,
    "SILVER": 2.4,
    "GOLD": 2.6,
    "PLATINUM": 2.8,
    "EMERALD": 3.0,
    "DIAMOND": 3.2,
    "MASTER": 3.5,
    "GRANDMASTER": 3.8,
    "CHALLENGER": 4.0,
}


def get_benchmark(stat_type, role, rank):
    """
    Get benchmark value for a specific stat, role, and rank

    Args:
        stat_type: 'cs_per_min', 'cs_at_10', 'vision_score', 'kda'
        role: Player's role
        rank: Player's rank tier (e.g., 'GOLD')

    Returns:
        Benchmark value or None
    """
    rank = rank.split("_")[0]  # Convert GOLD_II to GOLD

    if stat_type == "cs_per_min":
        return CS_BENCHMARKS.get(role, {}).get(rank)
    elif stat_type == "cs_at_10":
        return CS_AT_10_BENCHMARKS.get(role, {}).get(rank)
    elif stat_type == "vision_score":
        return VISION_SCORE_BENCHMARKS.get(role, {}).get(rank)
    elif stat_type == "kda":
        return KDA_BENCHMARKS.get(rank)

    return None


def calculate_percentile(player_value, benchmark_value):
    """
    Calculate rough percentile based on comparison to benchmark
    Benchmark = 50th percentile

    Args:
        player_value: Player's stat value
        benchmark_value: Rank average (50th percentile)

    Returns:
        Estimated percentile (0-100)
    """
    if not benchmark_value:
        return None

    # Simple calculation: every 10% deviation = 10 percentile points
    deviation = (player_value - benchmark_value) / benchmark_value
    percentile = 50 + (deviation * 100)

    # Clamp between 1 and 99
    return max(1, min(99, int(percentile)))
