# Real Benchmark System

This benchmark system calculates **real average statistics** from actual match data via the Riot API, instead of using hardcoded values.

## How It Works

1. **Benchmark Builder** (`benchmark_builder.py`)
   - Fetches players from each rank tier (Iron → Challenger)
   - Retrieves their recent matches
   - Extracts stats (CS/min, vision score, KDA, etc.)
   - Calculates real averages by rank and role
   - Saves to `benchmark_cache.json`

2. **Benchmark Loader** (`benchmark_loader.py`)
   - Loads benchmarks from cache
   - Falls back to hardcoded values if cache is missing/stale
   - Provides same interface as old system

3. **Fallback Data** (`fallback_data.py`)
   - Contains hardcoded values as backup
   - Used when cache doesn't exist or is too old

## Usage

### Generate Real Benchmarks

Run this command from the project root:

```bash
python generate_benchmarks.py
```

**Note:** This takes 30-60 minutes due to API rate limits.

### Using Benchmarks in Code

The system works automatically - no code changes needed!

```python
from API.benchmarks import get_benchmark, calculate_percentile

# Get benchmark for GOLD top laners
cs_benchmark = get_benchmark("cs_per_min", "TOP", "GOLD")
# Returns: 6.2 (real average from match data)

# Calculate percentile
player_cs = 7.5
percentile = calculate_percentile(player_cs, cs_benchmark)
# Returns: 70 (player is 70th percentile)
```

### Benchmark Stats Available

- `cs_per_min` - Creep score per minute
- `cs_at_10` - CS at 10 minutes
- `vision_score` - Vision score
- `kda` - Kill/Death/Assist ratio
- `damage_per_min` - Damage per minute
- `gold_per_minute` - Gold per minute
- `kill_participation` - Kill participation rate

## Cache Management

### Check Cache Status

The loader automatically prints cache status:
```
[Benchmarks] Loaded real benchmarks from cache
[Benchmarks] Generated: 2025-10-30 14:23
[Benchmarks] Age: 5 days
```

### Cache Expiration

- Cache is considered **stale after 30 days**
- System falls back to hardcoded values when stale
- Re-run `generate_benchmarks.py` to refresh

### Manual Cache Location

Cache file: `API/benchmarks/benchmark_cache.json`

You can:
- Delete it to force fallback to hardcoded values
- Share it with teammates (same benchmarks)
- Version control it (optional)

## Why Real Benchmarks?

### Before (Hardcoded):
```python
CS_BENCHMARKS = {
    "TOP": {"GOLD": 6.0}  # Guess!
}
```

### After (Real Data):
```python
# From analyzing 100 GOLD top lane matches:
{
  "GOLD": {
    "TOP": {"cs_per_min": 6.23}  # Actual average!
  }
}
```

## Benefits

✅ **Accurate** - Based on real match data, not guesses
✅ **Up-to-date** - Refresh monthly to track meta changes
✅ **Comprehensive** - More stats than manually maintained values
✅ **Legal** - Uses official Riot API
✅ **Automatic** - Falls back seamlessly if cache is missing

## Recommendations

- **Generate benchmarks monthly** to stay current with patches
- **Use same region** as your target players (default: EUW)
- **Keep cache in version control** if you want consistent benchmarks across team
- **Run during off-hours** to avoid hitting personal rate limits
