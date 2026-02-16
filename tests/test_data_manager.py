"""Quick test to verify DataManager fetches and saves everything."""

from src.data.data_manager import DataManager


def progress(current, total, message):
    if total > 0:
        print(f"  [{current}/{total}] {message}")
    else:
        print(f"  {message}")


def main():
    dm = DataManager("Retreat", "EUW", region='EUW')

    print("=== DataManager Test ===\n")

    # Try loading existing data first
    if dm.load_all():
        print(f"Loaded existing data: {len(dm.matches)} matches, {len(dm.mastery)} mastery entries")
        print(f"Profile: {dm.profile.get('game_name')}#{dm.profile.get('tag_line')}")
    else:
        print("No existing data found.")

    # Fetch everything
    print("\nFetching all data from API...")
    success = dm.fetch_all(progress_callback=progress)

    if not success:
        print("Failed to fetch data!")
        return

    print(f"\n=== Results ===")
    print(f"Profile: {dm.profile.get('game_name')}#{dm.profile.get('tag_line')} (Level {dm.profile.get('summoner_level')})")

    # Ranked stats
    for entry in dm.ranked_stats:
        queue = "Solo/Duo" if entry['queueType'] == 'RANKED_SOLO_5x5' else "Flex"
        print(f"  {queue}: {entry['tier']} {entry['rank']} {entry['leaguePoints']}LP ({entry['wins']}W {entry['losses']}L)")

    # Matches
    print(f"\nMatches: {len(dm.matches)} total")
    print(f"  Solo/Duo: {len(dm.get_solo_matches())}")
    print(f"  Flex: {len(dm.get_flex_matches())}")

    # Mastery
    print(f"\nMastery: {len(dm.mastery)} champions")
    if dm.mastery:
        top3 = sorted(dm.mastery, key=lambda m: m.get('championPoints', 0), reverse=True)[:3]
        for m in top3:
            name = dm.dd.get_champion_name(m['championId'])
            print(f"  {name}: M{m.get('championLevel', 0)} ({m.get('championPoints', 0):,} pts)")

    # Challenges
    print(f"\nChallenges: {len(dm.challenges.get('challenges', []))} progressed")
    print(f"Challenge configs: {len(dm.challenges_config)} definitions")

    # Challenge sample
    if dm.challenges.get('challenges'):
        print(f"\nTotal challenge points: {dm.challenges.get('totalPoints', {})}")

    # Climb history
    print(f"\nClimb history snapshots: {len(dm.climb_history)}")

    print("\nAll data saved to data/ folder!")


if __name__ == '__main__':
    main()
