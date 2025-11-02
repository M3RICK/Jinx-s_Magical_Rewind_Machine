import asyncio
from API.models.player import Player


async def main():
    #    async with Player("theoppstopper", "bigra", platform="euw1") as player:
    async with Player("sad and bad", "2093", platform="euw1") as player:
        await player.load_profile()

        await player.load_recent_matches(10)
        await player.load_match_timelines()

        player.process_matches()

        if "monthly_trends" in player.aggregated_stats:
            print("\nMONTHLY TRENDS")
            print(player.aggregated_stats["monthly_trends"])

        if "champion_performance" in player.aggregated_stats:
            print("\nCHAMPION PERFORMANCE")
            for champ in player.aggregated_stats["champion_performance"][:5]:
                print(
                    f"{champ['champion_name']}: {champ['games']} games, {champ['win_rate'] * 100:.0f}% WR"
                )

        print("\nEXPORTING DATA")
        player.export_to_json("player_data.json")


if __name__ == "__main__":
    asyncio.run(main())
