"""
NuzlockeTracker: LoL Nuzlocke challenge mode (manual tracking).

Rules: For every champion you play, you can only lose with them ONCE.
Win = keep the champion. Lose = eliminated.
Track your progress manually: click a champion, then click Win or Loss.
"""

import json
import os
import random
from datetime import datetime
from collections import defaultdict
from config import DATA_DIR


class NuzlockeTracker:
    """Tracks a Nuzlocke-style challenge run with manual win/loss input."""

    def __init__(self):
        self.runs: list[dict] = []
        self._path = os.path.join(DATA_DIR, 'nuzlocke.json')
        self.load()

    def load(self):
        if os.path.exists(self._path):
            with open(self._path, 'r', encoding='utf-8') as f:
                self.runs = json.load(f)
        else:
            self.runs = []

    def save(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(self._path, 'w', encoding='utf-8') as f:
            json.dump(self.runs, f, indent=2, ensure_ascii=False)

    def start_new_run(self, matches: list[dict] = None) -> dict:
        """Start a new Nuzlocke run.

        Args:
            matches: Optional match data (unused in manual mode)

        Tokens: Earn 1 token every 10 wins (no starting tokens)
        """
        run = {
            'id': len(self.runs) + 1,
            'started': datetime.now().isoformat(),
            'ended': None,
            'active': True,
            'eliminated': [],
            'survived': [],
            'total_games': 0,
            'total_wins': 0,
            'history': [],
            'tokens_used': 0,
            'resurrections': [],  # List of {champion, date, was_random}
        }
        self.runs.append(run)
        self.save()
        return run

    def get_active_run(self) -> dict | None:
        """Get the currently active run, if any."""
        for run in reversed(self.runs):
            if run.get('active', False):
                return run
        return None

    def end_run(self):
        """End the currently active run. This is permanent."""
        run = self.get_active_run()
        if run:
            run['active'] = False
            run['ended'] = datetime.now().isoformat()
            self.save()

    def delete_run(self, run_id: int):
        """Delete a run by ID."""
        self.runs = [r for r in self.runs if r.get('id') != run_id]
        # Re-number remaining runs
        for i, r in enumerate(self.runs, 1):
            r['id'] = i
        self.save()

    def record_result(self, champion: str, win: bool) -> dict | None:
        """Manually record a win or loss for a champion in the active run.

        Returns streak event dict if a milestone was hit, else None.
        """
        run = self.get_active_run()
        if not run:
            return None

        # Don't allow recording for eliminated champions
        if champion in run['eliminated']:
            return None

        run['total_games'] += 1
        run['history'].append({
            'champion': champion,
            'win': win,
            'date': datetime.now().strftime('%Y-%m-%d'),
        })

        if win:
            run['total_wins'] += 1
            if champion not in run['survived']:
                run['survived'].append(champion)
        else:
            run['eliminated'].append(champion)
            if champion in run['survived']:
                run['survived'].remove(champion)

        # Check for streak milestones
        streak_event = self._check_and_apply_streak_bonus(run)

        self.save()
        return streak_event

    def update_run(self, matches: list[dict]):
        """Legacy: no-op for manual mode."""
        pass

    def get_earned_tokens(self, run: dict = None) -> int:
        """Calculate how many tokens have been earned (1 per 10 wins + streak bonuses)."""
        if run is None:
            run = self.get_active_run()
        if not run:
            return 0

        wins = run.get('total_wins', 0)
        streak_tokens = run.get('streak_tokens', 0)
        return wins // 10 + streak_tokens

    def get_current_streak(self, run: dict = None) -> dict:
        """Get the current win/loss streak from history.

        Returns {'type': 'win'|'loss'|'none', 'count': int}

        Entries with 'streak_neutral' are treated as streak breakers for win
        streaks but are skipped when counting loss streaks.
        """
        if run is None:
            run = self.get_active_run()
        if not run or not run.get('history'):
            return {'type': 'none', 'count': 0}

        history = run['history']

        # Find the last non-neutral entry to determine streak type
        last_result = None
        for h in reversed(history):
            if h.get('streak_neutral'):
                continue
            last_result = h['win']
            break

        if last_result is None:
            return {'type': 'none', 'count': 0}

        streak_type = 'win' if last_result else 'loss'
        count = 0

        for h in reversed(history):
            # Neutral entries break win streaks but are skipped for loss streaks
            if h.get('streak_neutral'):
                if streak_type == 'win':
                    break  # Breaks the win streak
                continue  # Skip for loss streak counting
            if h['win'] == last_result:
                count += 1
            else:
                break

        return {'type': streak_type, 'count': count}

    def _check_and_apply_streak_bonus(self, run: dict) -> dict | None:
        """Check if a streak milestone (every 5) was hit and apply bonus/penalty.

        Returns event dict or None:
        - {'type': 'win_bonus', 'streak': int} for win streak milestone
        - {'type': 'loss_penalty', 'streak': int, 'champion': str} for loss streak milestone
        """
        streak = self.get_current_streak(run)
        if streak['count'] == 0 or streak['count'] % 5 != 0:
            return None

        if streak['type'] == 'win':
            # Every 5 wins: bonus token
            if 'streak_tokens' not in run:
                run['streak_tokens'] = 0
            run['streak_tokens'] += 1
            return {'type': 'win_bonus', 'streak': streak['count']}

        elif streak['type'] == 'loss':
            # Every 5 losses: lose a random alive champion
            # Capture the pool before elimination for the spinning wheel
            pool = list(run.get('survived', []))
            success, champion = self._eliminate_random_alive_champion(run)
            if success:
                return {'type': 'loss_penalty', 'streak': streak['count'], 'champion': champion, 'pool': pool}

        return None

    def _eliminate_random_alive_champion(self, run: dict) -> tuple[bool, str]:
        """Eliminate a random alive (survived) champion as a streak penalty.

        Returns (success, champion_name)
        """
        survived = run.get('survived', [])
        if not survived:
            return False, ""

        chosen = random.choice(survived)
        run['survived'].remove(chosen)
        run['eliminated'].append(chosen)
        return True, chosen

    def get_mvp_champion(self, run: dict = None) -> dict | None:
        """Get the champion with the longest consecutive win streak.

        Returns {'champion': str, 'streak': int, 'wins': int, 'losses': int} or None
        """
        if run is None:
            run = self.get_active_run()
        if not run or not run.get('history'):
            return None

        # Track per-champion: max consecutive wins, total wins, total losses
        champ_data = defaultdict(lambda: {'max_streak': 0, 'current_streak': 0, 'wins': 0, 'losses': 0})

        for h in run['history']:
            name = h['champion']
            if h['win']:
                champ_data[name]['wins'] += 1
                champ_data[name]['current_streak'] += 1
                champ_data[name]['max_streak'] = max(
                    champ_data[name]['max_streak'],
                    champ_data[name]['current_streak']
                )
            else:
                champ_data[name]['losses'] += 1
                champ_data[name]['current_streak'] = 0

        if not champ_data:
            return None

        # Find champion with highest max_streak (ties broken by wins)
        best = max(
            champ_data.items(),
            key=lambda x: (x[1]['max_streak'], x[1]['wins'])
        )

        if best[1]['max_streak'] == 0:
            return None

        return {
            'champion': best[0],
            'streak': best[1]['max_streak'],
            'wins': best[1]['wins'],
            'losses': best[1]['losses'],
        }

    def get_graveyard_stats(self, run: dict = None) -> list[dict]:
        """Get enhanced graveyard stats for eliminated champions.

        Returns list sorted by wins_before_death DESC (saddest first):
        [{'champion': str, 'wins_before_death': int, 'game_number': int}]
        """
        if run is None:
            run = self.get_active_run()
        if not run:
            return []

        eliminated = set(run.get('eliminated', []))
        if not eliminated:
            return []

        # Track wins before death, game number of death, and death cause
        champ_wins = defaultdict(int)
        champ_death_game = {}
        champ_death_cause = {}
        game_number = 0

        for h in run['history']:
            game_number += 1
            name = h['champion']
            if h['win']:
                champ_wins[name] += 1
            else:
                if name in eliminated and name not in champ_death_game:
                    champ_death_game[name] = game_number
                    if h.get('penalty_type') == 'played_eliminated':
                        champ_death_cause[name] = 'played_eliminated'
                        champ_death_cause[name + '_trigger'] = h.get('trigger_champion', '?')

        stats = []
        for champ in eliminated:
            game_num = champ_death_game.get(champ, 0)
            cause = champ_death_cause.get(champ, '')
            # game_number 0 means eliminated via streak penalty (no loss in history)
            stats.append({
                'champion': champ,
                'wins_before_death': champ_wins.get(champ, 0),
                'game_number': game_num,
                'was_penalty': game_num == 0 or cause != '',
                'death_cause': cause if cause else ('streak_penalty' if game_num == 0 else 'loss'),
                'trigger_champion': champ_death_cause.get(champ + '_trigger', ''),
            })

        # Sort by saddest first (most wins before death)
        stats.sort(key=lambda x: x['wins_before_death'], reverse=True)
        return stats

    def resurrect_random_champion(self) -> tuple[bool, str]:
        """Use a resurrection token to bring back a RANDOM eliminated champion (gambling wheel).

        Returns (success: bool, champion_name: str or error_message: str)
        """
        run = self.get_active_run()
        if not run:
            return False, "No active run"

        # Check if any champions eliminated
        if not run.get('eliminated'):
            return False, "No eliminated champions"

        # Check if tokens available (earn 1 per 10 wins)
        earned_tokens = self.get_earned_tokens(run)
        used_tokens = run.get('tokens_used', 0)
        tokens_left = earned_tokens - used_tokens

        if tokens_left <= 0:
            return False, "No tokens available"

        # GAMBLING WHEEL: randomly pick an eliminated champion
        eliminated = run['eliminated']
        chosen_champion = random.choice(eliminated)

        # Use token and revive
        run['tokens_used'] += 1
        run['eliminated'].remove(chosen_champion)
        run['resurrections'].append({
            'champion': chosen_champion,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'was_random': True,
        })

        self.save()
        return True, chosen_champion

    def penalize_played_eliminated(self, champion: str) -> tuple[bool, str]:
        """Penalize the player for picking an eliminated champion in a real game.

        Eliminates a random alive (survived) champion as punishment.
        Returns (success, eliminated_champion_name or error_message).
        """
        run = self.get_active_run()
        if not run:
            return False, "No active run"

        if champion not in run.get('eliminated', []):
            return False, f"{champion} is not eliminated"

        survived = run.get('survived', [])
        if not survived:
            return False, "No alive champions to eliminate"

        chosen = random.choice(survived)
        run['survived'].remove(chosen)
        run['eliminated'].append(chosen)

        # Record in history as a special penalty entry
        # streak_neutral: breaks win streaks but doesn't count toward loss streaks
        run['history'].append({
            'champion': chosen,
            'win': False,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'penalty_type': 'played_eliminated',
            'trigger_champion': champion,
            'streak_neutral': True,
        })
        run['total_games'] += 1

        self.save()
        return True, chosen

    def get_streak_events(self, run: dict = None) -> list[dict]:
        """Reconstruct streak milestone events from run history.

        Returns list of:
        - {'type': 'win_bonus', 'streak': int, 'game_number': int}
        - {'type': 'loss_penalty', 'streak': int, 'game_number': int, 'champion': str}
        """
        if run is None:
            run = self.get_active_run()
        if not run or not run.get('history'):
            return []

        events = []
        history = run['history']
        eliminated_set = set(run.get('eliminated', []))

        for i in range(len(history)):
            # Count streak ending at position i
            current_result = history[i]['win']
            count = 0
            for j in range(i, -1, -1):
                if history[j]['win'] == current_result:
                    count += 1
                else:
                    break

            if count > 0 and count % 5 == 0:
                game_num = i + 1
                if current_result:
                    events.append({
                        'type': 'win_bonus',
                        'streak': count,
                        'game_number': game_num,
                    })
                else:
                    # Find which champion was penalty-eliminated at this point
                    # (champions in eliminated but without a loss entry in history)
                    events.append({
                        'type': 'loss_penalty',
                        'streak': count,
                        'game_number': game_num,
                    })

        return events

    def get_run_stats(self, run: dict = None) -> dict:
        """Get stats for a run (active or specific)."""
        if run is None:
            run = self.get_active_run()
        if not run:
            return {}

        # Compute per-champion stats from history
        champ_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'games': 0})
        for h in run['history']:
            champ_stats[h['champion']]['games'] += 1
            if h['win']:
                champ_stats[h['champion']]['wins'] += 1
            else:
                champ_stats[h['champion']]['losses'] += 1

        # Best champions (most wins)
        best_champs = sorted(
            champ_stats.items(),
            key=lambda x: x[1]['wins'],
            reverse=True
        )[:5]

        # Calculate earned tokens (1 per 10 wins)
        earned_tokens = self.get_earned_tokens(run)
        used_tokens = run.get('tokens_used', 0)

        return {
            'id': run['id'],
            'active': run.get('active', False),
            'started': run['started'],
            'ended': run.get('ended'),
            'total_games': run['total_games'],
            'total_wins': run['total_wins'],
            'survived_count': len(run['survived']),
            'eliminated_count': len(run['eliminated']),
            'survived': run['survived'],
            'eliminated': run['eliminated'],
            'history': run['history'],
            'champ_stats': dict(champ_stats),
            'best_champs': best_champs,
            'tokens_earned': earned_tokens,
            'tokens_used': used_tokens,
            'tokens_remaining': earned_tokens - used_tokens,
            'resurrections': run.get('resurrections', []),
            'streak_events': self.get_streak_events(run),
            'graveyard': self.get_graveyard_stats(run),
            'mvp': self.get_mvp_champion(run),
        }

    def get_all_runs(self) -> list[dict]:
        """Get summary of all runs."""
        return [self.get_run_stats(r) for r in self.runs]
