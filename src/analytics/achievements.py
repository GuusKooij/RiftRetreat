"""
Achievements: Custom milestone badges and achievement tracking.

Detects milestones from match data and awards badges for
notable accomplishments throughout the season.
"""

from collections import defaultdict
from datetime import datetime


# Achievement definitions: (id, name, description, check_function_name)
ACHIEVEMENT_DEFS = [
    # Game count milestones
    ('games_10', 'Getting Started', 'Play 10 ranked games', 'check_games', 10),
    ('games_50', 'Dedicated Player', 'Play 50 ranked games', 'check_games', 50),
    ('games_100', 'Century', 'Play 100 ranked games', 'check_games', 100),
    ('games_200', 'Grinder', 'Play 200 ranked games', 'check_games', 200),
    ('games_500', 'No Life', 'Play 500 ranked games', 'check_games', 500),

    # Win milestones
    ('wins_10', 'Winner', 'Win 10 ranked games', 'check_wins', 10),
    ('wins_25', 'Consistent', 'Win 25 ranked games', 'check_wins', 25),
    ('wins_50', 'Half Century W', 'Win 50 ranked games', 'check_wins', 50),
    ('wins_100', 'Triple Digits', 'Win 100 ranked games', 'check_wins', 100),

    # Streak milestones
    ('streak_3', 'Hot Streak', 'Win 3 games in a row', 'check_win_streak', 3),
    ('streak_5', 'On Fire', 'Win 5 games in a row', 'check_win_streak', 5),
    ('streak_7', 'Unstoppable', 'Win 7 games in a row', 'check_win_streak', 7),
    ('streak_10', 'Legendary Streak', 'Win 10 games in a row', 'check_win_streak', 10),

    # Performance milestones
    ('perfect_game', 'Perfect Game', 'Win a game with 0 deaths', 'check_perfect_game', None),
    ('pentakill', 'PENTAKILL!', 'Get a pentakill in ranked', 'check_pentakill', None),
    ('quadrakill', 'Quadra!', 'Get a quadrakill in ranked', 'check_quadrakill', None),
    ('kda_10', 'KDA King', 'Achieve 10+ KDA in a game (min 5 kills)', 'check_kda_10', None),
    ('cs_10', 'Farm God', 'Average 10+ CS/min in a game', 'check_cs_10', None),
    ('vision_100', 'Ward Bot', 'Get 100+ vision score in a game', 'check_vision_100', None),
    ('damage_40k', 'Carry Mode', 'Deal 40,000+ damage in a game', 'check_damage_40k', None),

    # Champion pool
    ('champs_5', 'Diverse Pool', 'Play 5 different champions', 'check_unique_champs', 5),
    ('champs_10', 'Flexible', 'Play 10 different champions', 'check_unique_champs', 10),
    ('champs_20', 'Jack of All Trades', 'Play 20 different champions', 'check_unique_champs', 20),

    # Role milestones
    ('all_roles', 'Fill Player', 'Play a game in all 5 roles', 'check_all_roles', None),

    # Multi-kill collector
    ('doubles_10', 'Seeing Double', 'Get 10 double kills total', 'check_total_doubles', 10),
    ('triples_5', 'Triple Threat', 'Get 5 triple kills total', 'check_total_triples', 5),

    # First blood
    ('fb_5', 'First Strike', 'Get first blood 5 times', 'check_first_bloods', 5),
    ('fb_10', 'Early Bird', 'Get first blood 10 times', 'check_first_bloods', 10),

    # Session milestones
    ('marathon_5', 'Marathon Session', 'Play 5+ games in a single session', 'check_marathon', 5),
    ('marathon_8', 'Iron Will', 'Play 8+ games in a single session', 'check_marathon', 8),
]


class AchievementTracker:
    def __init__(self, matches: list[dict], tilt_detector=None):
        self.matches = sorted(matches, key=lambda m: m['game_start'])
        self.tilt_detector = tilt_detector

    def check_all(self) -> list[dict]:
        """Check all achievements and return earned ones."""
        earned = []
        for aid, name, desc, check_fn, threshold in ACHIEVEMENT_DEFS:
            checker = getattr(self, check_fn, None)
            if checker is None:
                continue

            if threshold is not None:
                result = checker(threshold)
            else:
                result = checker()

            if result:
                earned.append({
                    'id': aid,
                    'name': name,
                    'description': desc,
                    'earned': True,
                    'date': result if isinstance(result, str) else None,
                })

        return earned

    def progress_all(self) -> list[dict]:
        """Return all achievements with progress (earned or not)."""
        all_achievements = []
        for aid, name, desc, check_fn, threshold in ACHIEVEMENT_DEFS:
            checker = getattr(self, check_fn, None)
            if checker is None:
                continue

            if threshold is not None:
                result = checker(threshold)
                current = self._get_progress_value(check_fn, threshold)
            else:
                result = checker()
                current = 1 if result else 0
                threshold = 1

            all_achievements.append({
                'id': aid,
                'name': name,
                'description': desc,
                'earned': bool(result),
                'current': current,
                'target': threshold or 1,
                'progress_pct': min(round(current / max(threshold or 1, 1) * 100, 1), 100),
            })

        return all_achievements

    def _get_progress_value(self, check_fn: str, threshold) -> int:
        """Get current progress value for a given check function."""
        if check_fn == 'check_games':
            return len(self.matches)
        elif check_fn == 'check_wins':
            return sum(1 for m in self.matches if m['win'])
        elif check_fn == 'check_win_streak':
            return self._max_win_streak()
        elif check_fn == 'check_unique_champs':
            return len({m['champion'] for m in self.matches})
        elif check_fn == 'check_total_doubles':
            return sum(m.get('double_kills', 0) for m in self.matches)
        elif check_fn == 'check_total_triples':
            return sum(m.get('triple_kills', 0) for m in self.matches)
        elif check_fn == 'check_first_bloods':
            return sum(1 for m in self.matches if m.get('first_blood', False))
        elif check_fn == 'check_marathon':
            sessions = self.tilt_detector.detect_sessions() if self.tilt_detector else []
            return max((s['games'] for s in sessions), default=0)
        return 0

    # --- Check functions ---

    def check_games(self, threshold: int):
        if len(self.matches) >= threshold:
            if len(self.matches) >= threshold:
                return self.matches[threshold - 1]['game_start'][:10]
        return None

    def check_wins(self, threshold: int):
        wins = 0
        for m in self.matches:
            if m['win']:
                wins += 1
                if wins >= threshold:
                    return m['game_start'][:10]
        return None

    def check_win_streak(self, threshold: int):
        return self._max_win_streak() >= threshold

    def _max_win_streak(self) -> int:
        max_streak = 0
        current = 0
        for m in self.matches:
            if m['win']:
                current += 1
                max_streak = max(max_streak, current)
            else:
                current = 0
        return max_streak

    def check_perfect_game(self):
        for m in self.matches:
            if m['win'] and m['deaths'] == 0:
                return m['game_start'][:10]
        return None

    def check_pentakill(self):
        for m in self.matches:
            if m.get('penta_kills', 0) > 0:
                return m['game_start'][:10]
        return None

    def check_quadrakill(self):
        for m in self.matches:
            if m.get('quadra_kills', 0) > 0:
                return m['game_start'][:10]
        return None

    def check_kda_10(self):
        for m in self.matches:
            kda = (m['kills'] + m['assists']) / max(m['deaths'], 1)
            if kda >= 10 and m['kills'] >= 5:
                return m['game_start'][:10]
        return None

    def check_cs_10(self):
        for m in self.matches:
            if m['cs_per_min'] >= 10:
                return m['game_start'][:10]
        return None

    def check_vision_100(self):
        for m in self.matches:
            if m['vision_score'] >= 100:
                return m['game_start'][:10]
        return None

    def check_damage_40k(self):
        for m in self.matches:
            if m['total_damage_dealt'] >= 40000:
                return m['game_start'][:10]
        return None

    def check_unique_champs(self, threshold: int):
        champs = set()
        for m in self.matches:
            champs.add(m['champion'])
            if len(champs) >= threshold:
                return m['game_start'][:10]
        return None

    def check_all_roles(self):
        roles = {m.get('role', '') for m in self.matches if m.get('role')}
        needed = {'TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY'}
        if needed.issubset(roles):
            return True
        return None

    def check_total_doubles(self, threshold: int):
        total = sum(m.get('double_kills', 0) for m in self.matches)
        return total >= threshold

    def check_total_triples(self, threshold: int):
        total = sum(m.get('triple_kills', 0) for m in self.matches)
        return total >= threshold

    def check_first_bloods(self, threshold: int):
        total = sum(1 for m in self.matches if m.get('first_blood', False))
        return total >= threshold

    def check_marathon(self, threshold: int):
        if not self.tilt_detector:
            return None
        sessions = self.tilt_detector.detect_sessions()
        for s in sessions:
            if s['games'] >= threshold:
                return s['date']
        return None
