"""
TiltDetector: Identifies tilting patterns from match data.

Detects: losing streaks, play sessions, time-of-day patterns,
performance drop-off within sessions.
"""

from collections import defaultdict
from datetime import datetime


class TiltDetector:
    SESSION_GAP_HOURS = 2  # Games more than 2 hours apart = different sessions

    def __init__(self, matches: list[dict]):
        # Sort chronologically
        self.matches = sorted(matches, key=lambda m: m['game_start'])

    def _avg(self, values: list) -> float:
        return round(sum(values) / max(len(values), 1), 1)

    def detect_streaks(self) -> list[dict]:
        """Find all win/loss streaks of 3+."""
        if not self.matches:
            return []

        streaks = []
        current_type = self.matches[0]['win']
        current_count = 1
        start_idx = 0

        for i in range(1, len(self.matches)):
            if self.matches[i]['win'] == current_type:
                current_count += 1
            else:
                if current_count >= 3:
                    streaks.append({
                        'type': 'win' if current_type else 'loss',
                        'count': current_count,
                        'start': self.matches[start_idx]['game_start'],
                        'end': self.matches[i - 1]['game_start'],
                        'champions': [self.matches[j]['champion'] for j in range(start_idx, i)],
                    })
                current_type = self.matches[i]['win']
                current_count = 1
                start_idx = i

        # Check final streak
        if current_count >= 3:
            streaks.append({
                'type': 'win' if current_type else 'loss',
                'count': current_count,
                'start': self.matches[start_idx]['game_start'],
                'end': self.matches[-1]['game_start'],
                'champions': [self.matches[j]['champion'] for j in range(start_idx, len(self.matches))],
            })

        return streaks

    def detect_sessions(self) -> list[dict]:
        """Group games into play sessions (gap > 2 hours = new session)."""
        if not self.matches:
            return []

        sessions = []
        current_session = [self.matches[0]]

        for i in range(1, len(self.matches)):
            prev_time = datetime.fromisoformat(self.matches[i - 1]['game_start'])
            curr_time = datetime.fromisoformat(self.matches[i]['game_start'])
            gap_hours = (curr_time - prev_time).total_seconds() / 3600

            if gap_hours > self.SESSION_GAP_HOURS:
                sessions.append(self._build_session(current_session))
                current_session = [self.matches[i]]
            else:
                current_session.append(self.matches[i])

        sessions.append(self._build_session(current_session))
        return sessions

    def _build_session(self, games: list[dict]) -> dict:
        """Build session summary from a list of games."""
        wins = sum(1 for g in games if g['win'])
        losses = len(games) - wins

        avg_kda_num = self._avg([g['kills'] + g['assists'] for g in games])
        avg_deaths = self._avg([g['deaths'] for g in games])

        # Check for performance drop-off (first half vs second half)
        mid = max(len(games) // 2, 1)
        first_half = games[:mid]
        second_half = games[mid:]

        first_wr = sum(1 for g in first_half if g['win']) / max(len(first_half), 1) * 100
        second_wr = sum(1 for g in second_half if g['win']) / max(len(second_half), 1) * 100

        is_tilt = (
            losses >= 3 and
            wins / max(len(games), 1) < 0.4
        )

        return {
            'date': games[0]['game_start'][:10],
            'start_time': games[0]['game_start'],
            'end_time': games[-1]['game_start'],
            'games': len(games),
            'wins': wins,
            'losses': losses,
            'winrate': round(wins / len(games) * 100, 1),
            'avg_kills': self._avg([g['kills'] for g in games]),
            'avg_deaths': avg_deaths,
            'avg_assists': self._avg([g['assists'] for g in games]),
            'champions': [g['champion'] for g in games],
            'results': ['W' if g['win'] else 'L' for g in games],
            'first_half_wr': round(first_wr, 1),
            'second_half_wr': round(second_wr, 1),
            'is_tilt': is_tilt,
        }

    def time_of_day_analysis(self) -> list[dict]:
        """Win rate bucketed by hour of day."""
        buckets = defaultdict(lambda: {'wins': 0, 'losses': 0})

        for m in self.matches:
            hour = datetime.fromisoformat(m['game_start']).hour
            if m['win']:
                buckets[hour]['wins'] += 1
            else:
                buckets[hour]['losses'] += 1

        result = []
        for hour in sorted(buckets.keys()):
            data = buckets[hour]
            total = data['wins'] + data['losses']
            result.append({
                'hour': hour,
                'hour_label': f"{hour:02d}:00",
                'games': total,
                'wins': data['wins'],
                'losses': data['losses'],
                'winrate': round(data['wins'] / total * 100, 1),
            })

        return result

    def session_dropoff(self) -> dict:
        """Compare performance in early games vs late games within sessions."""
        sessions = self.detect_sessions()
        multi_game_sessions = [s for s in sessions if s['games'] >= 3]

        if not multi_game_sessions:
            return {'early_wr': 0, 'late_wr': 0, 'dropoff': 0, 'sessions_analyzed': 0}

        early_wins = sum(s['first_half_wr'] for s in multi_game_sessions)
        late_wins = sum(s['second_half_wr'] for s in multi_game_sessions)
        count = len(multi_game_sessions)

        early_avg = round(early_wins / count, 1)
        late_avg = round(late_wins / count, 1)

        return {
            'early_wr': early_avg,
            'late_wr': late_avg,
            'dropoff': round(early_avg - late_avg, 1),
            'sessions_analyzed': count,
        }

    def current_streak(self) -> dict:
        """Get the current (most recent) streak."""
        if not self.matches:
            return {'type': 'none', 'count': 0}

        streak_type = self.matches[-1]['win']
        count = 1

        for i in range(len(self.matches) - 2, -1, -1):
            if self.matches[i]['win'] == streak_type:
                count += 1
            else:
                break

        return {
            'type': 'win' if streak_type else 'loss',
            'count': count,
        }
