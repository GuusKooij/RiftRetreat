"""
StatsAnalyzer: Computes performance stats from match data.

Provides: overall stats, per-champion, per-role, per-queue breakdowns,
win condition analysis, rolling trends, matchup analysis, personal records,
win rate calendar, game timing analysis, and comeback/throw detection.
"""

import statistics
from collections import defaultdict
from datetime import datetime


class StatsAnalyzer:
    def __init__(self, matches: list[dict]):
        self.matches = matches

    def _avg(self, values: list) -> float:
        return round(sum(values) / max(len(values), 1), 1)

    def _calc_kda(self, kills: float, deaths: float, assists: float) -> float:
        return round((kills + assists) / max(deaths, 1), 2)

    def _compute_stats(self, match_list: list[dict]) -> dict:
        """Compute aggregate stats for a list of matches."""
        if not match_list:
            return {
                'games': 0, 'wins': 0, 'losses': 0, 'winrate': 0,
                'avg_kills': 0, 'avg_deaths': 0, 'avg_assists': 0, 'avg_kda': 0,
                'avg_cs_per_min': 0, 'avg_vision_score': 0, 'avg_damage': 0,
                'avg_gold': 0, 'avg_kp': 0,
            }

        wins = sum(1 for m in match_list if m['win'])
        losses = len(match_list) - wins
        avg_k = self._avg([m['kills'] for m in match_list])
        avg_d = self._avg([m['deaths'] for m in match_list])
        avg_a = self._avg([m['assists'] for m in match_list])

        return {
            'games': len(match_list),
            'wins': wins,
            'losses': losses,
            'winrate': round(wins / len(match_list) * 100, 1),
            'avg_kills': avg_k,
            'avg_deaths': avg_d,
            'avg_assists': avg_a,
            'avg_kda': self._calc_kda(avg_k, avg_d, avg_a),
            'avg_cs_per_min': self._avg([m['cs_per_min'] for m in match_list]),
            'avg_vision_score': self._avg([m['vision_score'] for m in match_list]),
            'avg_damage': self._avg([m['total_damage_dealt'] for m in match_list]),
            'avg_gold': self._avg([m['gold_earned'] for m in match_list]),
            'avg_kp': self._avg([m['kill_participation'] for m in match_list]),
        }

    def overall(self) -> dict:
        """Overall stats across all matches."""
        return self._compute_stats(self.matches)

    def by_queue(self) -> dict:
        """Stats broken down by queue type."""
        solo = [m for m in self.matches if m['queue_id'] == 420]
        flex = [m for m in self.matches if m['queue_id'] == 440]
        return {
            'solo_duo': self._compute_stats(solo),
            'flex': self._compute_stats(flex),
        }

    def by_champion(self, min_games: int = 1) -> list[dict]:
        """Stats per champion, sorted by games played."""
        groups = defaultdict(list)
        for m in self.matches:
            groups[m['champion']].append(m)

        result = []
        for champ, games in groups.items():
            if len(games) < min_games:
                continue
            stats = self._compute_stats(games)
            stats['champion'] = champ
            stats['champion_id'] = games[0].get('champion_id')
            # Most played role for this champ
            roles = [g['role'] for g in games if g['role']]
            stats['main_role'] = max(set(roles), key=roles.count) if roles else ''
            result.append(stats)

        result.sort(key=lambda x: x['games'], reverse=True)
        return result

    def by_role(self) -> list[dict]:
        """Stats per role."""
        groups = defaultdict(list)
        for m in self.matches:
            role = m.get('role', '')
            if role:
                groups[role].append(m)

        result = []
        for role, games in groups.items():
            stats = self._compute_stats(games)
            stats['role'] = role
            result.append(stats)

        result.sort(key=lambda x: x['games'], reverse=True)
        return result

    def win_conditions(self) -> list[dict]:
        """Compare stat averages in wins vs losses. Rank by biggest gap."""
        wins = [m for m in self.matches if m['win']]
        losses = [m for m in self.matches if not m['win']]

        if not wins or not losses:
            return []

        stats_to_compare = [
            ('kill_participation', 'Kill Participation', '%', False),
            ('cs_per_min', 'CS/min', '', False),
            ('vision_score', 'Vision Score', '', False),
            ('total_damage_dealt', 'Damage Dealt', '', False),
            ('gold_earned', 'Gold Earned', '', False),
            ('deaths', 'Deaths', '', True),  # Lower is better
            ('kills', 'Kills', '', False),
            ('assists', 'Assists', '', False),
        ]

        conditions = []
        for key, label, suffix, lower_is_better in stats_to_compare:
            win_avg = self._avg([m[key] for m in wins])
            loss_avg = self._avg([m[key] for m in losses])

            if lower_is_better:
                gap = loss_avg - win_avg  # Positive means wins have lower (better)
            else:
                gap = win_avg - loss_avg  # Positive means wins have higher (better)

            # Normalize gap as a percentage of the average
            overall_avg = (win_avg + loss_avg) / 2
            gap_pct = round(abs(gap) / max(overall_avg, 1) * 100, 1)

            conditions.append({
                'stat': key,
                'label': label,
                'suffix': suffix,
                'win_avg': win_avg,
                'loss_avg': loss_avg,
                'gap': round(gap, 1),
                'gap_pct': gap_pct,
                'lower_is_better': lower_is_better,
            })

        conditions.sort(key=lambda x: x['gap_pct'], reverse=True)
        return conditions

    def recent_form(self, count: int = 10) -> list[dict]:
        """Last N matches in chronological order (most recent first)."""
        sorted_matches = sorted(self.matches, key=lambda m: m['game_start'], reverse=True)
        return sorted_matches[:count]

    def rolling_trend(self, window: int = 10) -> list[dict]:
        """Rolling average over a window of games (chronological order)."""
        sorted_matches = sorted(self.matches, key=lambda m: m['game_start'])
        trends = []

        for i in range(window - 1, len(sorted_matches)):
            chunk = sorted_matches[i - window + 1:i + 1]
            stats = self._compute_stats(chunk)
            stats['game_start'] = chunk[-1]['game_start']
            stats['game_index'] = i + 1
            trends.append(stats)

        return trends

    # --- Matchup Analysis ---

    def enemy_champion_matchups(self) -> list[dict]:
        """WR against specific enemy champions (laning opponent by role)."""
        matchups = defaultdict(lambda: {'wins': 0, 'losses': 0, 'games': []})

        for m in self.matches:
            player_role = m.get('role', '')
            if not player_role:
                continue
            for opp in m.get('opponents', []):
                if opp.get('role') == player_role:
                    key = opp['champion']
                    if m['win']:
                        matchups[key]['wins'] += 1
                    else:
                        matchups[key]['losses'] += 1
                    matchups[key]['games'].append(m)

        result = []
        for champ, data in matchups.items():
            total = data['wins'] + data['losses']
            result.append({
                'enemy_champion': champ,
                'games': total,
                'wins': data['wins'],
                'losses': data['losses'],
                'winrate': round(data['wins'] / total * 100, 1),
            })

        result.sort(key=lambda x: x['games'], reverse=True)
        return result

    def enemy_matchups_by_role(self) -> dict[str, list[dict]]:
        """WR against specific enemy champions, grouped by your role."""
        matchups = defaultdict(lambda: defaultdict(lambda: {'wins': 0, 'losses': 0}))

        for m in self.matches:
            player_role = m.get('role', '')
            if not player_role:
                continue
            display_role = 'SUPPORT' if player_role == 'UTILITY' else player_role
            for opp in m.get('opponents', []):
                if opp.get('role') == player_role:
                    key = opp['champion']
                    if m['win']:
                        matchups[display_role][key]['wins'] += 1
                    else:
                        matchups[display_role][key]['losses'] += 1

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

    def duo_partner_analysis(self) -> list[dict]:
        """Track recurring teammates and WR with each."""
        partners = defaultdict(lambda: {'wins': 0, 'losses': 0, 'champions': [], 'name': '', 'tag': ''})

        for m in self.matches:
            for tm in m.get('teammates', []):
                puuid = tm.get('puuid', '')
                if not puuid:
                    continue
                if m['win']:
                    partners[puuid]['wins'] += 1
                else:
                    partners[puuid]['losses'] += 1
                partners[puuid]['champions'].append(tm['champion'])
                partners[puuid]['name'] = tm.get('summoner_name', '')
                partners[puuid]['tag'] = tm.get('tag_line', '')

        result = []
        for puuid, data in partners.items():
            total = data['wins'] + data['losses']
            if total < 2:
                continue
            # Top 5 champions played by this partner
            champ_counts = defaultdict(int)
            for c in data['champions']:
                champ_counts[c] += 1
            # Sort by count and get top 5
            top_champs = sorted(champ_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            top_champs_list = [champ for champ, count in top_champs]
            most_played = top_champs[0][0] if top_champs else ''

            result.append({
                'summoner_name': data['name'],
                'tag_line': data['tag'],
                'games': total,
                'wins': data['wins'],
                'losses': data['losses'],
                'winrate': round(data['wins'] / total * 100, 1),
                'most_played': most_played,
                'top_champions': top_champs_list,  # List of top 5 champions
            })

        result.sort(key=lambda x: x['games'], reverse=True)
        return result

    # --- Game Timing Analysis ---

    def game_timing_analysis(self) -> dict:
        """Average game duration in wins vs losses, first blood rate, objective stats."""
        wins = [m for m in self.matches if m['win']]
        losses = [m for m in self.matches if not m['win']]

        fb_involved = sum(1 for m in self.matches if m.get('first_blood', False))
        fb_wins = sum(1 for m in wins if m.get('first_blood', False))

        return {
            'avg_duration_wins': self._avg([m['game_duration_min'] for m in wins]) if wins else 0,
            'avg_duration_losses': self._avg([m['game_duration_min'] for m in losses]) if losses else 0,
            'avg_duration_all': self._avg([m['game_duration_min'] for m in self.matches]),
            'first_blood_rate': round(fb_involved / max(len(self.matches), 1) * 100, 1),
            'first_blood_wr': round(fb_wins / max(fb_involved, 1) * 100, 1) if fb_involved else 0,
            'avg_dragon_kills': self._avg([m.get('dragon_kills', 0) for m in self.matches]),
            'avg_baron_kills': self._avg([m.get('baron_kills', 0) for m in self.matches]),
            'avg_turret_kills': self._avg([m.get('turret_kills', 0) for m in self.matches]),
            'total_games': len(self.matches),
        }

    # --- Win Rate Calendar ---

    def win_rate_calendar(self) -> list[dict]:
        """Win rate by date for calendar heatmap display."""
        daily = defaultdict(lambda: {'wins': 0, 'losses': 0})

        for m in self.matches:
            date = m['game_start'][:10]
            if m['win']:
                daily[date]['wins'] += 1
            else:
                daily[date]['losses'] += 1

        result = []
        for date, data in sorted(daily.items()):
            total = data['wins'] + data['losses']
            result.append({
                'date': date,
                'games': total,
                'wins': data['wins'],
                'losses': data['losses'],
                'winrate': round(data['wins'] / total * 100, 1),
                'net': data['wins'] - data['losses'],
            })

        return result

    # --- Comeback / Throw Detection ---

    def comeback_throw_analysis(self) -> dict:
        """Detect comebacks (won while behind in gold) and throws (lost while ahead)."""
        comebacks = []
        throws = []
        stomps = []
        clean_wins = []
        games_with_data = 0

        for m in self.matches:
            gold_diff = m.get('game_end_gold_diff')
            if gold_diff is None:
                continue

            games_with_data += 1

            if m['win'] and gold_diff < -2000:
                comebacks.append(m)
            elif not m['win'] and gold_diff > 2000:
                throws.append(m)
            elif m['win'] and gold_diff > 5000:
                stomps.append(m)
            elif not m['win'] and gold_diff < -5000:
                pass  # got stomped
            elif m['win']:
                clean_wins.append(m)

        total = max(games_with_data, 1)
        return {
            'comebacks': len(comebacks),
            'throws': len(throws),
            'stomps': len(stomps),
            'comeback_rate': round(len(comebacks) / total * 100, 1),
            'throw_rate': round(len(throws) / total * 100, 1),
            'total_games': len(self.matches),
            'games_with_data': games_with_data,
        }

    # --- Personal Records ---

    def personal_records(self) -> list[dict]:
        """Track personal bests across all matches."""
        if not self.matches:
            return []

        records = []

        # Highest KDA game
        best_kda = max(self.matches, key=lambda m: (m['kills'] + m['assists']) / max(m['deaths'], 1))
        kda_val = round((best_kda['kills'] + best_kda['assists']) / max(best_kda['deaths'], 1), 1)
        records.append({
            'record': 'Best KDA',
            'value': f"{kda_val} ({best_kda['kills']}/{best_kda['deaths']}/{best_kda['assists']})",
            'champion': best_kda['champion'],
            'date': best_kda['game_start'][:10],
            'win': best_kda['win'],
        })

        # Most kills
        most_kills = max(self.matches, key=lambda m: m['kills'])
        records.append({
            'record': 'Most Kills',
            'value': str(most_kills['kills']),
            'champion': most_kills['champion'],
            'date': most_kills['game_start'][:10],
            'win': most_kills['win'],
        })

        # Most assists
        most_assists = max(self.matches, key=lambda m: m['assists'])
        records.append({
            'record': 'Most Assists',
            'value': str(most_assists['assists']),
            'champion': most_assists['champion'],
            'date': most_assists['game_start'][:10],
            'win': most_assists['win'],
        })

        # Highest CS
        best_cs = max(self.matches, key=lambda m: m['cs'])
        records.append({
            'record': 'Most CS',
            'value': f"{best_cs['cs']} ({best_cs['cs_per_min']}/min)",
            'champion': best_cs['champion'],
            'date': best_cs['game_start'][:10],
            'win': best_cs['win'],
        })

        # Best CS/min
        best_csm = max(self.matches, key=lambda m: m['cs_per_min'])
        records.append({
            'record': 'Best CS/min',
            'value': f"{best_csm['cs_per_min']}/min ({best_csm['cs']} CS in {best_csm['game_duration_min']}m)",
            'champion': best_csm['champion'],
            'date': best_csm['game_start'][:10],
            'win': best_csm['win'],
        })

        # Most damage
        best_dmg = max(self.matches, key=lambda m: m['total_damage_dealt'])
        records.append({
            'record': 'Most Damage',
            'value': f"{best_dmg['total_damage_dealt']:,}",
            'champion': best_dmg['champion'],
            'date': best_dmg['game_start'][:10],
            'win': best_dmg['win'],
        })

        # Best vision score
        best_vis = max(self.matches, key=lambda m: m['vision_score'])
        records.append({
            'record': 'Best Vision Score',
            'value': str(best_vis['vision_score']),
            'champion': best_vis['champion'],
            'date': best_vis['game_start'][:10],
            'win': best_vis['win'],
        })

        # Highest KP
        best_kp = max(self.matches, key=lambda m: m['kill_participation'])
        records.append({
            'record': 'Highest Kill Participation',
            'value': f"{best_kp['kill_participation']}%",
            'champion': best_kp['champion'],
            'date': best_kp['game_start'][:10],
            'win': best_kp['win'],
        })

        # Most gold
        best_gold = max(self.matches, key=lambda m: m['gold_earned'])
        records.append({
            'record': 'Most Gold Earned',
            'value': f"{best_gold['gold_earned']:,}",
            'champion': best_gold['champion'],
            'date': best_gold['game_start'][:10],
            'win': best_gold['win'],
        })

        # Fastest win
        wins = [m for m in self.matches if m['win']]
        if wins:
            fastest = min(wins, key=lambda m: m['game_duration_min'])
            records.append({
                'record': 'Fastest Win',
                'value': f"{fastest['game_duration_min']}min",
                'champion': fastest['champion'],
                'date': fastest['game_start'][:10],
                'win': True,
            })

        # Perfect game (most kills with 0 deaths)
        deathless = [m for m in self.matches if m['deaths'] == 0]
        if deathless:
            best_deathless = max(deathless, key=lambda m: m['kills'] + m['assists'])
            records.append({
                'record': 'Best Deathless Game',
                'value': f"{best_deathless['kills']}/{best_deathless['deaths']}/{best_deathless['assists']}",
                'champion': best_deathless['champion'],
                'date': best_deathless['game_start'][:10],
                'win': best_deathless['win'],
            })

        # Multi-kills
        pentas = [m for m in self.matches if m.get('penta_kills', 0) > 0]
        quadras = [m for m in self.matches if m.get('quadra_kills', 0) > 0]
        triples = [m for m in self.matches if m.get('triple_kills', 0) > 0]
        doubles = [m for m in self.matches if m.get('double_kills', 0) > 0]

        if pentas:
            records.append({
                'record': 'Pentakills',
                'value': f"{sum(m['penta_kills'] for m in pentas)} total ({len(pentas)} games)",
                'champion': pentas[0]['champion'],
                'date': pentas[0]['game_start'][:10],
                'win': pentas[0]['win'],
            })
        if quadras:
            records.append({
                'record': 'Quadrakills',
                'value': f"{sum(m['quadra_kills'] for m in quadras)} total ({len(quadras)} games)",
                'champion': quadras[0]['champion'],
                'date': quadras[0]['game_start'][:10],
                'win': quadras[0]['win'],
            })

        return records

    def multi_kill_summary(self) -> dict:
        """Summary of multi-kills achieved."""
        return {
            'double_kills': sum(m.get('double_kills', 0) for m in self.matches),
            'triple_kills': sum(m.get('triple_kills', 0) for m in self.matches),
            'quadra_kills': sum(m.get('quadra_kills', 0) for m in self.matches),
            'penta_kills': sum(m.get('penta_kills', 0) for m in self.matches),
        }
