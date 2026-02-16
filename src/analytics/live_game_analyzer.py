"""
LiveGameAnalyzer: Provides champion stats, matchup data, ban suggestions,
counter-pick recommendations, win prediction, and role-specific tips
for use during champion select and in-game.
"""

from collections import defaultdict


# Rank to numeric value for win prediction
RANK_VALUES = {
    'IRON': 1, 'BRONZE': 2, 'SILVER': 3, 'GOLD': 4,
    'PLATINUM': 5, 'EMERALD': 6, 'DIAMOND': 7,
    'MASTER': 8, 'GRANDMASTER': 9, 'CHALLENGER': 10,
}
RANK_DIVISION = {'IV': 0, 'III': 0.25, 'II': 0.5, 'I': 0.75}


class LiveGameAnalyzer:
    def __init__(self, matches, champion_analyzer=None):
        self.matches = matches or []
        self.champion_analyzer = champion_analyzer
        self._champ_stats_cache = {}
        self._matchup_cache = {}

    def get_personal_champion_stats(self, champion_name: str) -> dict:
        """Get your stats on a specific champion from match history."""
        if champion_name in self._champ_stats_cache:
            return self._champ_stats_cache[champion_name]

        games = [m for m in self.matches if m.get('champion') == champion_name]
        if not games:
            return {}

        wins = sum(1 for g in games if g['win'])
        avg = lambda vals: round(sum(vals) / max(len(vals), 1), 1)

        stats = {
            'champion': champion_name,
            'games': len(games),
            'wins': wins,
            'losses': len(games) - wins,
            'winrate': round(wins / len(games) * 100, 1),
            'avg_kills': avg([g['kills'] for g in games]),
            'avg_deaths': avg([g['deaths'] for g in games]),
            'avg_assists': avg([g['assists'] for g in games]),
            'avg_kda': round(
                sum(g['kills'] + g['assists'] for g in games) /
                max(sum(g['deaths'] for g in games), 1), 2
            ),
            'avg_cs_per_min': avg([g['cs_per_min'] for g in games]),
            'avg_damage': avg([g['total_damage_dealt'] for g in games]),
            'avg_kp': avg([g['kill_participation'] for g in games]),
            'avg_vision': avg([g['vision_score'] for g in games]),
        }
        self._champ_stats_cache[champion_name] = stats
        return stats

    def get_matchup_vs(self, enemy_champion: str) -> dict:
        """Get your win rate against a specific enemy champion (all roles)."""
        if enemy_champion in self._matchup_cache:
            return self._matchup_cache[enemy_champion]

        wins = 0
        losses = 0
        for m in self.matches:
            for opp in m.get('opponents', []):
                if opp.get('champion') == enemy_champion:
                    if m['win']:
                        wins += 1
                    else:
                        losses += 1
                    break  # Count each game once

        total = wins + losses
        result = {
            'enemy_champion': enemy_champion,
            'games': total,
            'wins': wins,
            'losses': losses,
            'winrate': round(wins / max(total, 1) * 100, 1) if total else 0,
        }
        self._matchup_cache[enemy_champion] = result
        return result

    def get_lane_matchup_vs(self, enemy_champion: str, my_role: str = None) -> dict:
        """Get your win rate against a specific enemy lane opponent (role-matched)."""
        wins = 0
        losses = 0
        for m in self.matches:
            player_role = m.get('role', '')
            if my_role and player_role != my_role:
                continue
            for opp in m.get('opponents', []):
                if opp.get('champion') == enemy_champion and opp.get('role') == player_role:
                    if m['win']:
                        wins += 1
                    else:
                        losses += 1
                    break

        total = wins + losses
        return {
            'enemy_champion': enemy_champion,
            'games': total,
            'wins': wins,
            'losses': losses,
            'winrate': round(wins / max(total, 1) * 100, 1) if total else 0,
        }

    def get_matchup_summary(self, enemy_champion: str) -> str:
        """Human-readable matchup summary."""
        m = self.get_matchup_vs(enemy_champion)
        if m['games'] == 0:
            return f"No games vs {enemy_champion}"
        return f"You are {m['wins']}-{m['losses']} vs {enemy_champion} ({m['winrate']}% WR)"

    def suggest_bans(self, top_n: int = 5) -> list[dict]:
        """Suggest bans based on enemies you lose to most (min 2 games)."""
        matchups = defaultdict(lambda: {'wins': 0, 'losses': 0})

        for m in self.matches:
            for opp in m.get('opponents', []):
                champ = opp.get('champion', '')
                if not champ:
                    continue
                if m['win']:
                    matchups[champ]['wins'] += 1
                else:
                    matchups[champ]['losses'] += 1

        results = []
        for champ, data in matchups.items():
            total = data['wins'] + data['losses']
            if total < 2:
                continue
            wr = data['wins'] / total
            # Ban priority: low WR + high game count
            ban_priority = (1 - wr) * total
            results.append({
                'champion': champ,
                'games': total,
                'wins': data['wins'],
                'losses': data['losses'],
                'winrate': round(wr * 100, 1),
                'ban_priority': round(ban_priority, 1),
                'reason': f"{data['losses']}L in {total} games ({round(wr * 100)}% WR)",
            })

        results.sort(key=lambda x: x['ban_priority'], reverse=True)
        return results[:top_n]

    def suggest_counter_picks(self, enemy_champions: list[str], my_role: str = None) -> list[dict]:
        """Suggest your champions with good WR against visible enemies."""
        # Get all champions you've played
        champ_groups = defaultdict(list)
        for m in self.matches:
            if my_role and m.get('role') != my_role:
                continue
            champ_groups[m['champion']].append(m)

        suggestions = []
        for my_champ, games in champ_groups.items():
            if len(games) < 2:
                continue

            # Count wins/losses specifically against visible enemies
            vs_wins = 0
            vs_losses = 0
            for g in games:
                dominated_enemies = [opp.get('champion') for opp in g.get('opponents', [])]
                if any(e in enemy_champions for e in dominated_enemies):
                    if g['win']:
                        vs_wins += 1
                    else:
                        vs_losses += 1

            vs_total = vs_wins + vs_losses
            if vs_total < 1:
                continue

            overall_wins = sum(1 for g in games if g['win'])
            overall_wr = round(overall_wins / len(games) * 100, 1)
            vs_wr = round(vs_wins / max(vs_total, 1) * 100, 1)

            suggestions.append({
                'champion': my_champ,
                'overall_games': len(games),
                'overall_winrate': overall_wr,
                'vs_games': vs_total,
                'vs_wins': vs_wins,
                'vs_winrate': vs_wr,
            })

        suggestions.sort(key=lambda x: (x['vs_winrate'], x['overall_winrate']), reverse=True)
        return suggestions[:5]

    def predict_win(self, team_ranks: list[dict], enemy_ranks: list[dict]) -> dict:
        """Predict win % based on average team ranks.

        Each entry: {'tier': 'GOLD', 'rank': 'II', 'wins': 50, 'losses': 40}
        """
        def rank_value(entry):
            tier = entry.get('tier', '').upper()
            div = entry.get('rank', 'IV')
            base = RANK_VALUES.get(tier, 4)
            return base + RANK_DIVISION.get(div, 0)

        def avg_rank(entries):
            values = [rank_value(e) for e in entries if e.get('tier')]
            return sum(values) / max(len(values), 1) if values else 4.0

        team_avg = avg_rank(team_ranks)
        enemy_avg = avg_rank(enemy_ranks)

        # Linear model: each rank tier difference ~= 10% WR swing
        diff = team_avg - enemy_avg
        win_pct = 50 + (diff * 10)
        win_pct = max(15, min(85, win_pct))  # Clamp 15-85%

        return {
            'team_avg_rank': round(team_avg, 2),
            'enemy_avg_rank': round(enemy_avg, 2),
            'rank_diff': round(diff, 2),
            'win_percentage': round(win_pct, 1),
        }

    def get_role_tips(self, champion_name: str, role: str = None) -> list[str]:
        """Generate contextual tips based on personal stats on a champion."""
        stats = self.get_personal_champion_stats(champion_name)
        tips = []

        if not stats:
            tips.append(f"First time on {champion_name} in ranked -- play safe!")
            return tips

        if stats['games'] == 1:
            tips.append(f"Only 1 game on {champion_name} -- limited data")

        if stats['avg_deaths'] >= 6:
            tips.append(f"You average {stats['avg_deaths']} deaths on {champion_name} -- focus on staying alive")
        elif stats['avg_deaths'] <= 2.5:
            tips.append(f"Great survivability on {champion_name} ({stats['avg_deaths']} avg deaths)")

        if stats['avg_cs_per_min'] < 6 and role in ('TOP', 'MIDDLE', 'BOTTOM'):
            tips.append(f"CS/min is {stats['avg_cs_per_min']} -- try to hit 7+ for your role")

        if stats['avg_kp'] < 45 and role in ('JUNGLE', 'UTILITY'):
            tips.append(f"Kill participation is low ({stats['avg_kp']}%) -- look for more plays")

        if stats['avg_vision'] < 15 and role == 'UTILITY':
            tips.append(f"Vision score averaging {stats['avg_vision']} -- ward more aggressively")

        if stats['winrate'] >= 60 and stats['games'] >= 3:
            tips.append(f"Strong pick! {stats['winrate']}% WR over {stats['games']} games")
        elif stats['winrate'] <= 40 and stats['games'] >= 3:
            tips.append(f"Struggling on {champion_name} ({stats['winrate']}% WR) -- consider alternatives")

        return tips

    @staticmethod
    def rank_to_display(tier: str, rank: str, lp: int = 0) -> str:
        """Convert rank data to display string like 'Gold II (45 LP)'."""
        if not tier:
            return "Unranked"
        tier_display = tier.capitalize()
        if tier.upper() in ('MASTER', 'GRANDMASTER', 'CHALLENGER'):
            return f"{tier_display} ({lp} LP)"
        return f"{tier_display} {rank}"

    @staticmethod
    def rank_to_short(tier: str, rank: str) -> str:
        """Short rank display like 'G2', 'D4', 'M'."""
        if not tier:
            return "?"
        abbrev = tier[0].upper()
        if tier.upper() in ('MASTER', 'GRANDMASTER', 'CHALLENGER'):
            return abbrev
        div_map = {'IV': '4', 'III': '3', 'II': '2', 'I': '1'}
        return f"{abbrev}{div_map.get(rank, '')}"
