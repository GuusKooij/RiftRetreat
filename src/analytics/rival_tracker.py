"""
RivalTracker: Identifies frequently faced enemy champions and players.
"""

from collections import defaultdict


class RivalTracker:
    def __init__(self, matches: list[dict]):
        self.matches = matches

    def frequent_enemy_champions(self, min_games: int = 3) -> list[dict]:
        """Most commonly faced enemy champions with your WR against them."""
        champ_data = defaultdict(lambda: {'wins': 0, 'losses': 0})

        for m in self.matches:
            for opp in m.get('opponents', []):
                champ = opp.get('champion', '')
                if not champ:
                    continue
                if m['win']:
                    champ_data[champ]['wins'] += 1
                else:
                    champ_data[champ]['losses'] += 1

        results = []
        for champ, data in champ_data.items():
            total = data['wins'] + data['losses']
            if total < min_games:
                continue
            results.append({
                'champion': champ,
                'games': total,
                'wins': data['wins'],
                'losses': data['losses'],
                'winrate': round(data['wins'] / total * 100, 1),
            })

        results.sort(key=lambda x: x['games'], reverse=True)
        return results

    def frequent_enemy_players(self, min_games: int = 2) -> list[dict]:
        """Specific players faced multiple times (requires opponent PUUIDs in match data)."""
        player_data = defaultdict(lambda: {
            'wins': 0, 'losses': 0, 'name': '', 'tag': '', 'champions': []
        })

        for m in self.matches:
            for opp in m.get('opponents', []):
                puuid = opp.get('puuid', '')
                if not puuid:
                    continue
                if m['win']:
                    player_data[puuid]['wins'] += 1
                else:
                    player_data[puuid]['losses'] += 1
                player_data[puuid]['name'] = opp.get('summoner_name', '')
                player_data[puuid]['tag'] = opp.get('tag_line', '')
                player_data[puuid]['champions'].append(opp.get('champion', ''))

        results = []
        for puuid, data in player_data.items():
            total = data['wins'] + data['losses']
            if total < min_games:
                continue

            # Most played champion by this opponent
            champ_counts = defaultdict(int)
            for c in data['champions']:
                champ_counts[c] += 1
            most_played = max(champ_counts, key=champ_counts.get) if champ_counts else ''

            results.append({
                'puuid': puuid,
                'summoner_name': data['name'],
                'tag_line': data['tag'],
                'games': total,
                'wins': data['wins'],
                'losses': data['losses'],
                'winrate': round(data['wins'] / total * 100, 1),
                'most_played': most_played,
            })

        results.sort(key=lambda x: x['games'], reverse=True)
        return results
