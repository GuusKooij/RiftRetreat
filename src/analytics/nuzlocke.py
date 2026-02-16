"""
NuzlockeTracker: LoL Nuzlocke challenge mode (manual tracking).

Rules: For every champion you play, you can only lose with them ONCE.
Win = keep the champion. Lose = eliminated.
Track your progress manually: click a champion, then click Win or Loss.
"""

import json
import os
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

    def record_result(self, champion: str, win: bool):
        """Manually record a win or loss for a champion in the active run."""
        run = self.get_active_run()
        if not run:
            return

        # Don't allow recording for eliminated champions
        if champion in run['eliminated']:
            return

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

        self.save()

    def update_run(self, matches: list[dict]):
        """Legacy: no-op for manual mode."""
        pass

    def get_earned_tokens(self, run: dict = None) -> int:
        """Calculate how many tokens have been earned (1 per 10 wins)."""
        if run is None:
            run = self.get_active_run()
        if not run:
            return 0

        wins = run.get('total_wins', 0)
        return wins // 10  # Integer division: 10 wins = 1 token, 20 wins = 2 tokens, etc.

    def resurrect_random_champion(self) -> tuple[bool, str]:
        """Use a resurrection token to bring back a RANDOM eliminated champion (gambling wheel).

        Returns (success: bool, champion_name: str or error_message: str)
        """
        import random

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
        }

    def get_all_runs(self) -> list[dict]:
        """Get summary of all runs."""
        return [self.get_run_stats(r) for r in self.runs]
