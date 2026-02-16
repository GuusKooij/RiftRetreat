"""
ChampionAnalyzer: Champion pool analysis and recommendations.

Analyzes per-champion performance, identifies strengths/weaknesses,
recommends which champions to prioritize or drop, and provides
consistency scoring and champion bingo/collection tracking.
"""

import statistics
from collections import defaultdict


class ChampionAnalyzer:
    def __init__(self, matches: list[dict], mastery: list[dict], data_dragon):
        self.matches = matches
        self.mastery = mastery
        self.dd = data_dragon

        # Build mastery lookup by champion ID
        self.mastery_by_id = {m['championId']: m for m in mastery}

    def _avg(self, values: list) -> float:
        return round(sum(values) / max(len(values), 1), 1)

    def champion_pool(self) -> list[dict]:
        """Full champion pool analysis with stats and mastery."""
        groups = defaultdict(list)
        for m in self.matches:
            groups[m['champion']].append(m)

        pool = []
        for champ, games in groups.items():
            wins = sum(1 for g in games if g['win'])
            champ_id = games[0].get('champion_id')
            mastery_data = self.mastery_by_id.get(champ_id, {})

            # Most common role
            roles = [g['role'] for g in games if g['role']]
            main_role = max(set(roles), key=roles.count) if roles else ''

            entry = {
                'champion': champ,
                'champion_id': champ_id,
                'games': len(games),
                'wins': wins,
                'losses': len(games) - wins,
                'winrate': round(wins / len(games) * 100, 1),
                'avg_kills': self._avg([g['kills'] for g in games]),
                'avg_deaths': self._avg([g['deaths'] for g in games]),
                'avg_assists': self._avg([g['assists'] for g in games]),
                'avg_kda': round(
                    (sum(g['kills'] + g['assists'] for g in games)) /
                    max(sum(g['deaths'] for g in games), 1), 2
                ),
                'avg_cs_per_min': self._avg([g['cs_per_min'] for g in games]),
                'avg_damage': self._avg([g['total_damage_dealt'] for g in games]),
                'avg_kp': self._avg([g['kill_participation'] for g in games]),
                'main_role': main_role,
                'mastery_level': mastery_data.get('championLevel', 0),
                'mastery_points': mastery_data.get('championPoints', 0),
            }

            # Categorize
            if len(games) >= 3:
                if entry['winrate'] >= 55:
                    entry['rating'] = 'strong'
                elif entry['winrate'] <= 45:
                    entry['rating'] = 'weak'
                else:
                    entry['rating'] = 'average'
            else:
                entry['rating'] = 'small_sample'

            pool.append(entry)

        pool.sort(key=lambda x: x['games'], reverse=True)
        return pool

    def recommendations(self) -> dict:
        """Generate champion recommendations: prioritize, drop, and potential picks."""
        pool = self.champion_pool()

        prioritize = [c for c in pool if c['rating'] == 'strong']
        prioritize.sort(key=lambda x: x['winrate'], reverse=True)

        drop = [c for c in pool if c['rating'] == 'weak']
        drop.sort(key=lambda x: x['winrate'])

        average = [c for c in pool if c['rating'] == 'average']
        small_sample = [c for c in pool if c['rating'] == 'small_sample']

        return {
            'prioritize': prioritize,
            'drop': drop,
            'average': average,
            'small_sample': small_sample,
        }

    def role_champions(self) -> dict:
        """Group champion performance by role."""
        role_groups = defaultdict(list)
        pool = self.champion_pool()

        for champ in pool:
            if champ['main_role']:
                role_groups[champ['main_role']].append(champ)

        return dict(role_groups)

    def get_champions_by_winrate(self, min_games: int = 3) -> list[dict]:
        """Get champions sorted by winrate (min games filter)."""
        pool = self.champion_pool()
        filtered = [c for c in pool if c['games'] >= min_games]
        filtered.sort(key=lambda x: x['winrate'], reverse=True)
        return filtered

    def mastery_overview(self, top_n: int = 20) -> list[dict]:
        """Top champions by mastery with enriched data."""
        sorted_mastery = sorted(
            self.mastery, key=lambda m: m.get('championPoints', 0), reverse=True
        )

        result = []
        for m in sorted_mastery[:top_n]:
            champ_id = m['championId']
            name = self.dd.get_champion_name(champ_id)

            # Check if played this season
            season_games = [g for g in self.matches if g.get('champion_id') == champ_id]
            season_wins = sum(1 for g in season_games if g['win'])

            result.append({
                'champion': name,
                'champion_id': champ_id,
                'mastery_level': m.get('championLevel', 0),
                'mastery_points': m.get('championPoints', 0),
                'marks_required': m.get('markRequiredForNextLevel', 0),
                'season_milestone': m.get('championSeasonMilestone', 0),
                'last_played': m.get('lastPlayTime', 0),
                'chest_granted': m.get('chestGranted', False),
                'season_games': len(season_games),
                'season_wins': season_wins,
                'season_wr': round(season_wins / max(len(season_games), 1) * 100, 1),
            })

        return result

    def unplayed_champions(self) -> list[dict]:
        """Champions owned (have mastery) but not played this season."""
        played_ids = {m['champion_id'] for m in self.matches}

        unplayed = []
        for m in self.mastery:
            if m['championId'] not in played_ids:
                name = self.dd.get_champion_name(m['championId'])
                champ_data = self.dd.get_champion_by_id(m['championId'])
                tags = champ_data.get('tags', []) if champ_data else []

                unplayed.append({
                    'champion': name,
                    'champion_id': m['championId'],
                    'mastery_level': m.get('championLevel', 0),
                    'mastery_points': m.get('championPoints', 0),
                    'tags': tags,
                })

        unplayed.sort(key=lambda x: x['mastery_points'], reverse=True)
        return unplayed

    # --- Consistency Scoring ---

    def consistency_scores(self) -> list[dict]:
        """Rate consistency on each champion (low variance = reliable, high = coinflip).

        Uses coefficient of variation on KDA ratio per game.
        """
        groups = defaultdict(list)
        for m in self.matches:
            groups[m['champion']].append(m)

        result = []
        for champ, games in groups.items():
            if len(games) < 3:
                continue

            kda_ratios = [(g['kills'] + g['assists']) / max(g['deaths'], 1) for g in games]
            cs_values = [g['cs_per_min'] for g in games]

            kda_mean = statistics.mean(kda_ratios)
            kda_stdev = statistics.stdev(kda_ratios) if len(kda_ratios) > 1 else 0
            kda_cv = round(kda_stdev / max(kda_mean, 0.1), 2)

            cs_mean = statistics.mean(cs_values)
            cs_stdev = statistics.stdev(cs_values) if len(cs_values) > 1 else 0
            cs_cv = round(cs_stdev / max(cs_mean, 0.1), 2)

            # Combined consistency score (lower = more consistent, 0-100 scale inverted)
            raw_score = (kda_cv + cs_cv) / 2
            consistency = max(0, round((1 - min(raw_score, 1)) * 100))

            wins = sum(1 for g in games if g['win'])
            label = 'reliable' if consistency >= 70 else ('coinflip' if consistency < 40 else 'moderate')

            result.append({
                'champion': champ,
                'champion_id': games[0].get('champion_id'),
                'games': len(games),
                'winrate': round(wins / len(games) * 100, 1),
                'consistency': consistency,
                'kda_variance': kda_cv,
                'cs_variance': cs_cv,
                'label': label,
            })

        result.sort(key=lambda x: x['consistency'], reverse=True)
        return result

    # --- Champion Bingo / Collection Tracker ---

    def champion_bingo(self) -> list[dict]:
        """Grid of ALL champions with status: never_played / played / won / mastery_5 / mastery_10."""
        all_champs = self.dd.get_champion_list() if self.dd else []
        mastery_by_id = {m['championId']: m for m in self.mastery}

        played_ids = {m['champion_id'] for m in self.matches}
        won_ids = {m['champion_id'] for m in self.matches if m['win']}

        bingo = []
        for champ in all_champs:
            cid = champ['id']
            m_data = mastery_by_id.get(cid, {})
            m_level = m_data.get('championLevel', 0)
            m_points = m_data.get('championPoints', 0)

            if m_level >= 10:
                status = 'mastery_10'
            elif m_level >= 5:
                status = 'mastery_5'
            elif cid in won_ids:
                status = 'won'
            elif cid in played_ids:
                status = 'played'
            elif m_points > 0:
                status = 'owned'
            else:
                status = 'never_played'

            bingo.append({
                'champion': champ['name'],
                'champion_id': cid,
                'tags': champ['tags'],
                'status': status,
                'mastery_level': m_level,
                'mastery_points': m_points,
            })

        bingo.sort(key=lambda x: x['champion'])
        return bingo

    def bingo_summary(self) -> dict:
        """Summary counts for bingo board."""
        bingo = self.champion_bingo()
        counts = defaultdict(int)
        for b in bingo:
            counts[b['status']] += 1

        total = len(bingo)
        collected = total - counts.get('never_played', 0)

        return {
            'total_champions': total,
            'collected': collected,
            'never_played': counts.get('never_played', 0),
            'owned': counts.get('owned', 0),
            'played': counts.get('played', 0),
            'won': counts.get('won', 0),
            'mastery_5': counts.get('mastery_5', 0),
            'mastery_10': counts.get('mastery_10', 0),
            'completion_pct': round(collected / max(total, 1) * 100, 1),
        }
