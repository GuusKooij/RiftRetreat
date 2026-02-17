"""
Achievements: Custom milestone badges and achievement tracking.

Detects milestones from match data and awards badges for
notable accomplishments throughout the season.
"""

from collections import defaultdict
from datetime import datetime


# Rarity tiers and colors
RARITY_COLORS = {
    'Common': '#7B818C',     # grey
    'Rare': '#2196F3',       # blue
    'Epic': '#9C27B0',       # purple
    'Legendary': '#C8AA6E',  # gold
}

ACHIEVEMENT_RARITY = {
    # Common — basic milestones
    'games_10': 'Common', 'wins_10': 'Common', 'streak_3': 'Common',
    'champs_5': 'Common', 'doubles_10': 'Common', 'fb_5': 'Common',
    # Rare — moderate effort
    'games_50': 'Rare', 'games_100': 'Rare', 'wins_25': 'Rare',
    'streak_5': 'Rare', 'champs_10': 'Rare', 'quadrakill': 'Rare',
    'all_roles': 'Rare', 'triples_5': 'Rare', 'fb_10': 'Rare',
    'marathon_5': 'Rare',
    # Epic — difficult
    'games_200': 'Epic', 'wins_50': 'Epic', 'streak_7': 'Epic',
    'perfect_game': 'Epic', 'kda_10': 'Epic', 'cs_10': 'Epic',
    'vision_100': 'Epic', 'damage_40k': 'Epic', 'champs_20': 'Epic',
    'marathon_8': 'Epic',
    # Legendary — very rare
    'games_500': 'Legendary', 'wins_100': 'Legendary',
    'streak_10': 'Legendary', 'pentakill': 'Legendary',
}

# Secret achievement definitions: (id, name, description, check_function_name)
SECRET_ACHIEVEMENT_DEFS = [
    ('secret_pacifist', 'The Pacifist', 'Win a game with 0 kills', 'check_secret_pacifist'),
    ('secret_ghost', 'Ghost', 'Win with 0 kills AND 0 deaths', 'check_secret_ghost'),
    ('secret_iron_will', 'Iron Will', 'Win while 10k+ gold behind', 'check_secret_iron_will'),
    ('secret_feeder', 'The Feeder', 'Die 20+ times in a single game', 'check_secret_feeder'),
    ('secret_zero_farm', 'Zero Farm', 'Win with less than 10 CS', 'check_secret_zero_farm'),
    ('secret_vision_blind', 'Vision Blind', 'Win with 0 vision score', 'check_secret_vision_blind'),
    ('secret_speed_run', 'Speed Run', 'Win a game in under 15 minutes', 'check_secret_speed_run'),
    ('secret_marathon', 'The Marathon', 'Play a 50+ minute game', 'check_secret_marathon'),
    ('secret_no_damage', 'What Damage?', 'Win dealing less than 5k damage', 'check_secret_no_damage'),
    ('secret_tank_god', 'Tank God', 'Take 60k+ damage in a single game', 'check_secret_tank_god'),
    ('secret_the_wall', 'The Wall', 'Take 80k+ damage AND win', 'check_secret_the_wall'),
    ('secret_obj_hunter', 'Dragon Slayer', 'Kill 5+ dragons in one game', 'check_secret_obj_hunter'),
    ('secret_tower_destroyer', 'Tower Destroyer', 'Destroy 6+ turrets in one game', 'check_secret_tower_destroyer'),
    ('secret_ward_machine', 'Ward Machine', 'Place 30+ wards in a single game', 'check_secret_ward_machine'),
    ('secret_fb_streak', 'First Blood Machine', 'Get first blood 3 games in a row', 'check_secret_fb_streak'),
    ('secret_no_assist', 'Solo Carry', 'Win with 0 assists', 'check_secret_no_assist'),
    ('secret_walking_ward', 'Walking Ward', 'Get 150+ vision score', 'check_secret_walking_ward'),
    ('secret_gold_miner', 'Gold Miner', 'Earn 25k+ gold in a single game', 'check_secret_gold_miner'),
    ('secret_cs_perfect', 'CS Perfectionist', 'Average 12+ CS/min in a game', 'check_secret_cs_perfect'),
    ('secret_dmg_dealer', 'Damage Dealer', 'Deal 50k+ total damage in a game', 'check_secret_dmg_dealer'),
    ('secret_quadra_collector', 'Quadra Collector', 'Get 3+ quadra kills total', 'check_secret_quadra_collector'),
    ('secret_comeback_king', 'Comeback King', 'Win 5 games while 2k+ gold behind', 'check_secret_comeback_king'),
    ('secret_baron_stealer', 'Baron Stealer', 'Kill 3+ barons in one game', 'check_secret_baron_stealer'),
    ('secret_inhibitor_breaker', 'Inhibitor Breaker', 'Destroy 3+ inhibitors in one game', 'check_secret_inhibitor_breaker'),
    ('secret_stomp_master', 'Stomp Master', 'Win 10 games with 5k+ gold lead', 'check_secret_stomp_master'),
    ('secret_double_double', 'Double-Double', '10+ kills AND 10+ assists in one game', 'check_secret_double_double'),
    ('secret_kill_secured', 'Kill Secured', 'Win with 20+ kills and less than 5 assists', 'check_secret_kill_secured'),
]


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

            rarity = ACHIEVEMENT_RARITY.get(aid, 'Common')
            all_achievements.append({
                'id': aid,
                'name': name,
                'description': desc,
                'earned': bool(result),
                'current': current,
                'target': threshold or 1,
                'progress_pct': min(round(current / max(threshold or 1, 1) * 100, 1), 100),
                'rarity': rarity,
                'rarity_color': RARITY_COLORS.get(rarity, '#7B818C'),
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

    # --- Secret achievement checks ---

    def progress_secrets(self) -> list[dict]:
        """Return all secret achievements. Earned ones show full details,
        unearned ones show as '???' with no hints."""
        results = []
        for sid, name, desc, check_fn in SECRET_ACHIEVEMENT_DEFS:
            checker = getattr(self, check_fn, None)
            if checker is None:
                continue
            result = checker()
            if result:
                results.append({
                    'id': sid,
                    'name': name,
                    'description': desc,
                    'earned': True,
                    'date': result if isinstance(result, str) else None,
                })
            else:
                results.append({
                    'id': sid,
                    'name': '???',
                    'description': 'Hidden until unlocked',
                    'earned': False,
                })
        return results

    def check_secret_pacifist(self):
        for m in self.matches:
            if m['win'] and m['kills'] == 0:
                return m['game_start'][:10]
        return None

    def check_secret_ghost(self):
        for m in self.matches:
            if m['win'] and m['kills'] == 0 and m['deaths'] == 0:
                return m['game_start'][:10]
        return None

    def check_secret_iron_will(self):
        for m in self.matches:
            if m['win'] and m.get('game_end_gold_diff', 0) < -10000:
                return m['game_start'][:10]
        return None

    def check_secret_feeder(self):
        for m in self.matches:
            if m['deaths'] >= 20:
                return m['game_start'][:10]
        return None

    def check_secret_zero_farm(self):
        for m in self.matches:
            if m['win'] and m.get('cs', 0) < 10:
                return m['game_start'][:10]
        return None

    def check_secret_vision_blind(self):
        for m in self.matches:
            if m['win'] and m.get('vision_score', 0) == 0:
                return m['game_start'][:10]
        return None

    def check_secret_speed_run(self):
        for m in self.matches:
            if m['win'] and m.get('game_duration_min', 99) < 15:
                return m['game_start'][:10]
        return None

    def check_secret_marathon(self):
        for m in self.matches:
            if m.get('game_duration_min', 0) >= 50:
                return m['game_start'][:10]
        return None

    def check_secret_no_damage(self):
        for m in self.matches:
            if m['win'] and m.get('total_damage_dealt', 99999) < 5000:
                return m['game_start'][:10]
        return None

    def check_secret_tank_god(self):
        for m in self.matches:
            if m.get('damage_taken', 0) >= 60000:
                return m['game_start'][:10]
        return None

    def check_secret_the_wall(self):
        for m in self.matches:
            if m['win'] and m.get('damage_taken', 0) >= 80000:
                return m['game_start'][:10]
        return None

    def check_secret_obj_hunter(self):
        for m in self.matches:
            if m.get('dragon_kills', 0) >= 5:
                return m['game_start'][:10]
        return None

    def check_secret_tower_destroyer(self):
        for m in self.matches:
            if m.get('turret_kills', 0) >= 6:
                return m['game_start'][:10]
        return None

    def check_secret_ward_machine(self):
        for m in self.matches:
            if m.get('wards_placed', 0) >= 30:
                return m['game_start'][:10]
        return None

    def check_secret_fb_streak(self):
        streak = 0
        for m in self.matches:
            if m.get('first_blood', False):
                streak += 1
                if streak >= 3:
                    return m['game_start'][:10]
            else:
                streak = 0
        return None

    def check_secret_no_assist(self):
        for m in self.matches:
            if m['win'] and m['assists'] == 0:
                return m['game_start'][:10]
        return None

    def check_secret_walking_ward(self):
        for m in self.matches:
            if m.get('vision_score', 0) >= 150:
                return m['game_start'][:10]
        return None

    def check_secret_gold_miner(self):
        for m in self.matches:
            if m.get('gold_earned', 0) >= 25000:
                return m['game_start'][:10]
        return None

    def check_secret_cs_perfect(self):
        for m in self.matches:
            if m.get('cs_per_min', 0) >= 12:
                return m['game_start'][:10]
        return None

    def check_secret_dmg_dealer(self):
        for m in self.matches:
            if m.get('total_damage_dealt', 0) >= 50000:
                return m['game_start'][:10]
        return None

    def check_secret_quadra_collector(self):
        total = sum(m.get('quadra_kills', 0) for m in self.matches)
        if total >= 3:
            return True
        return None

    def check_secret_comeback_king(self):
        count = 0
        for m in self.matches:
            if m['win'] and m.get('game_end_gold_diff', 0) < -2000:
                count += 1
                if count >= 5:
                    return m['game_start'][:10]
        return None

    def check_secret_baron_stealer(self):
        for m in self.matches:
            if m.get('baron_kills', 0) >= 3:
                return m['game_start'][:10]
        return None

    def check_secret_inhibitor_breaker(self):
        for m in self.matches:
            if m.get('inhibitor_kills', 0) >= 3:
                return m['game_start'][:10]
        return None

    def check_secret_stomp_master(self):
        count = 0
        for m in self.matches:
            if m['win'] and m.get('game_end_gold_diff', 0) >= 5000:
                count += 1
                if count >= 10:
                    return m['game_start'][:10]
        return None

    def check_secret_double_double(self):
        for m in self.matches:
            if m['kills'] >= 10 and m['assists'] >= 10:
                return m['game_start'][:10]
        return None

    def check_secret_kill_secured(self):
        for m in self.matches:
            if m['win'] and m['kills'] >= 20 and m['assists'] < 5:
                return m['game_start'][:10]
        return None
