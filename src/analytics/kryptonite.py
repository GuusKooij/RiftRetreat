"""
KryptoniteAnalyzer: Analyzes your win rate against all enemy champions
to identify worst matchups, best matchups, and suggest bans.
"""

from collections import defaultdict


class KryptoniteAnalyzer:
    def __init__(self, matches: list[dict], min_games: int = 2):
        self.matches = matches
        self.min_games = min_games

    def all_enemy_matchups(self) -> list[dict]:
        """WR against ALL enemy champions (all 5 enemies per game, not just lane)."""
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
            results.append({
                'enemy_champion': champ,
                'games': total,
                'wins': data['wins'],
                'losses': data['losses'],
                'winrate': round(data['wins'] / total * 100, 1),
            })

        results.sort(key=lambda x: x['games'], reverse=True)
        return results

    def worst_matchups(self, count: int = 10) -> list[dict]:
        """Enemies with lowest WR against, filtered by min_games."""
        matchups = self.all_enemy_matchups()
        filtered = [m for m in matchups if m['games'] >= self.min_games]
        filtered.sort(key=lambda x: x['winrate'])

        for m in filtered:
            m['ban_priority'] = round((1 - m['winrate'] / 100) * m['games'], 1)

        return filtered[:count]

    def best_matchups(self, count: int = 10) -> list[dict]:
        """Enemies with highest WR against, filtered by min_games."""
        matchups = self.all_enemy_matchups()
        filtered = [m for m in matchups if m['games'] >= self.min_games]
        filtered.sort(key=lambda x: x['winrate'], reverse=True)
        return filtered[:count]

    def matchups_by_role(self) -> dict[str, list[dict]]:
        """Grouped by your role: WR against enemy champions you laned against."""
        matchups = defaultdict(lambda: defaultdict(lambda: {'wins': 0, 'losses': 0}))

        for m in self.matches:
            player_role = m.get('role', '')
            if not player_role:
                continue
            display_role = 'SUPPORT' if player_role == 'UTILITY' else player_role

            for opp in m.get('opponents', []):
                if opp.get('role') == player_role:
                    champ = opp.get('champion', '')
                    if not champ:
                        continue
                    if m['win']:
                        matchups[display_role][champ]['wins'] += 1
                    else:
                        matchups[display_role][champ]['losses'] += 1

        result = {}
        for role, champs in matchups.items():
            role_list = []
            for champ, data in champs.items():
                total = data['wins'] + data['losses']
                role_list.append({
                    'enemy_champion': champ,
                    'games': total,
                    'wins': data['wins'],
                    'losses': data['losses'],
                    'winrate': round(data['wins'] / total * 100, 1),
                })
            role_list.sort(key=lambda x: x['games'], reverse=True)
            result[role] = role_list

        return result

    def suggested_bans(self, count: int = 5) -> list[dict]:
        """Top ban suggestions with human-readable messages."""
        worst = self.worst_matchups(count=count)
        for m in worst:
            m['message'] = (
                f"Ban {m['enemy_champion']}: "
                f"{m['losses']}L in {m['games']} games ({m['winrate']}% WR)"
            )
        return worst

    def lane_opponent_matchups(self) -> list[dict]:
        """WR against lane opponents only (role-matched)."""
        matchups = defaultdict(lambda: {'wins': 0, 'losses': 0})

        for m in self.matches:
            player_role = m.get('role', '')
            if not player_role:
                continue
            for opp in m.get('opponents', []):
                if opp.get('role') == player_role:
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
            results.append({
                'enemy_champion': champ,
                'games': total,
                'wins': data['wins'],
                'losses': data['losses'],
                'winrate': round(data['wins'] / total * 100, 1),
            })

        results.sort(key=lambda x: x['games'], reverse=True)
        return results
