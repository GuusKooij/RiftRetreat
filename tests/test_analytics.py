"""Test analytics engine on saved data."""

from src.data.data_manager import DataManager
from src.analytics.stats import StatsAnalyzer
from src.analytics.tilt import TiltDetector
from src.analytics.champions import ChampionAnalyzer
from src.analytics.challenges import ChallengeAnalyzer


def main():
    dm = DataManager("Retreat", "EUW")
    dm.load_all()
    print(f"Loaded {len(dm.matches)} matches\n")

    # --- Stats ---
    stats = StatsAnalyzer(dm.matches)

    print("=== OVERALL ===")
    o = stats.overall()
    print(f"  {o['games']}G  {o['wins']}W {o['losses']}L  ({o['winrate']}% WR)")
    print(f"  KDA: {o['avg_kills']}/{o['avg_deaths']}/{o['avg_assists']} ({o['avg_kda']})")
    print(f"  CS/min: {o['avg_cs_per_min']}  Vision: {o['avg_vision_score']}  KP: {o['avg_kp']}%")

    print("\n=== BY QUEUE ===")
    q = stats.by_queue()
    for name, data in q.items():
        if data['games']:
            print(f"  {name}: {data['games']}G {data['winrate']}% WR  KDA {data['avg_kda']}")

    print("\n=== BY ROLE ===")
    for r in stats.by_role():
        print(f"  {r['role']}: {r['games']}G {r['winrate']}% WR  KDA {r['avg_kda']}")

    print("\n=== TOP CHAMPIONS ===")
    for c in stats.by_champion(min_games=2)[:8]:
        print(f"  {c['champion']:12s} {c['games']}G  {c['winrate']}% WR  KDA {c['avg_kda']}  ({c['main_role']})")

    print("\n=== WIN CONDITIONS ===")
    for wc in stats.win_conditions()[:5]:
        direction = "lower" if wc['lower_is_better'] else "higher"
        print(f"  {wc['label']}: {wc['win_avg']} (W) vs {wc['loss_avg']} (L) -- {direction} in wins ({wc['gap_pct']}% gap)")

    # --- Tilt ---
    tilt = TiltDetector(dm.matches)

    print("\n=== CURRENT STREAK ===")
    streak = tilt.current_streak()
    print(f"  {streak['count']} game {streak['type']} streak")

    print("\n=== LOSING STREAKS ===")
    for s in tilt.detect_streaks():
        if s['type'] == 'loss':
            print(f"  {s['count']}L streak: {', '.join(s['champions'])}")

    print("\n=== TIME OF DAY ===")
    for t in tilt.time_of_day_analysis():
        bar = '#' * t['games']
        print(f"  {t['hour_label']}  {t['games']:2d}G  {t['winrate']:5.1f}% WR  {bar}")

    print("\n=== SESSION DROPOFF ===")
    dropoff = tilt.session_dropoff()
    print(f"  Early game WR: {dropoff['early_wr']}%  |  Late game WR: {dropoff['late_wr']}%  |  Dropoff: {dropoff['dropoff']}%")

    # --- Champions ---
    ca = ChampionAnalyzer(dm.matches, dm.mastery, dm.dd)

    print("\n=== CHAMPION RECOMMENDATIONS ===")
    recs = ca.recommendations()
    print(f"  PRIORITIZE ({len(recs['prioritize'])}):")
    for c in recs['prioritize'][:5]:
        print(f"    {c['champion']:12s} {c['winrate']}% WR ({c['games']}G)  KDA {c['avg_kda']}")
    print(f"  DROP ({len(recs['drop'])}):")
    for c in recs['drop'][:5]:
        print(f"    {c['champion']:12s} {c['winrate']}% WR ({c['games']}G)  KDA {c['avg_kda']}")

    # --- Challenges ---
    ch = ChallengeAnalyzer(dm.challenges, dm.challenges_config, dm.matches, dm.mastery, dm.dd)

    print(f"\n=== CHALLENGE POINTS ===")
    tp = ch.total_points()
    print(f"  {tp.get('level', 'N/A')}: {tp.get('current', 0):,}/{tp.get('max', 0):,}")

    print("\n=== CLOSEST TO NEXT TIER ===")
    for c in ch.close_to_leveling(top_n=10):
        print(f"  {c['name'][:35]:35s}  {c['current_level']:12s} -> {c['next_tier'] or '?':12s}  {c['progress_pct']:5.1f}%  ({c['current_value']:.0f}/{c['next_threshold']:.0f})")

    print(f"\n=== CHAMPIONS NOT WON WITH ({len(ch.champions_not_won_with())}) ===")
    not_won = ch.champions_not_won_with()[:10]
    for c in not_won:
        print(f"  {c['champion']:15s} M{c['mastery_level']}  ({c['mastery_points']:,} pts)  [{', '.join(c['tags'])}]")

    print("\n=== CHALLENGE CHAMPION PICKS (Top 10) ===")
    for r in ch.champion_recommendations()[:10]:
        roles = '/'.join(r['suggested_roles'])
        new = " [NEW WIN]" if r['new_win'] else ""
        print(f"  {r['champion']:15s} Score:{r['score']:5.1f}  M{r['mastery_level']}  {roles:20s}  {', '.join(r['reasons'][:2])}{new}")

    print("\n=== IN-GAME TIPS ===")
    for tip in ch.get_in_game_tips()[:8]:
        print(f"  [{tip['challenge_name'][:30]:30s}] {tip['tip']}")
        print(f"    Progress: {tip['progress']}  ({tip['progress_pct']:.0f}%)")


if __name__ == '__main__':
    main()
