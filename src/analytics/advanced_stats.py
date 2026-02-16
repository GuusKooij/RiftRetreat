"""Advanced match statistics: KP%, GPM, CSPM, first blood, comebacks, damage share."""

from typing import List, Dict, Any, Tuple


class AdvancedStatsAnalyzer:
    """Analyzes advanced statistics from match history."""

    def __init__(self, matches: List[Dict[str, Any]]):
        """Initialize with list of processed match dicts."""
        self.matches = matches

    # ── First Blood Stats ────────────────────────────────────────────────

    def get_first_blood_stats(self) -> Dict[str, Any]:
        """Calculate first blood statistics.

        Returns dict with:
        - total_games: int
        - first_blood_count: int (games where you got first blood)
        - first_blood_rate: float (percentage)
        - first_blood_winrate: float (winrate when getting first blood)
        """
        if not self.matches:
            return {
                'total_games': 0,
                'first_blood_count': 0,
                'first_blood_rate': 0.0,
                'first_blood_winrate': 0.0,
            }

        fb_games = [m for m in self.matches if m.get('first_blood', False)]
        fb_wins = [m for m in fb_games if m.get('win', False)]

        return {
            'total_games': len(self.matches),
            'first_blood_count': len(fb_games),
            'first_blood_rate': (len(fb_games) / len(self.matches)) * 100,
            'first_blood_winrate': (len(fb_wins) / len(fb_games) * 100) if fb_games else 0.0,
        }

    # ── Kill Participation ───────────────────────────────────────────────

    def get_kp_stats(self) -> Dict[str, Any]:
        """Calculate kill participation statistics.

        Returns dict with:
        - average_kp: float
        - max_kp: float
        - min_kp: float
        - recent_kp_trend: List[float] (last 10 games)
        """
        if not self.matches:
            return {
                'average_kp': 0.0,
                'max_kp': 0.0,
                'min_kp': 0.0,
                'recent_kp_trend': [],
            }

        kp_values = [m.get('kill_participation', 0.0) for m in self.matches]
        recent_kp = kp_values[:10] if len(kp_values) >= 10 else kp_values

        return {
            'average_kp': sum(kp_values) / len(kp_values) if kp_values else 0.0,
            'max_kp': max(kp_values) if kp_values else 0.0,
            'min_kp': min(kp_values) if kp_values else 0.0,
            'recent_kp_trend': recent_kp,
        }

    def get_kp_by_role(self) -> Dict[str, float]:
        """Get average KP% by role."""
        role_kp = {}
        for match in self.matches:
            role = match.get('role', 'UNKNOWN')
            kp = match.get('kill_participation', 0.0)

            if role not in role_kp:
                role_kp[role] = []
            role_kp[role].append(kp)

        return {
            role: sum(kps) / len(kps) if kps else 0.0
            for role, kps in role_kp.items()
        }

    # ── Gold Efficiency ──────────────────────────────────────────────────

    def get_gold_efficiency_stats(self) -> Dict[str, Any]:
        """Calculate gold efficiency (GPM, CSPM) statistics.

        Returns dict with:
        - average_gpm: float
        - average_cspm: float
        - best_gpm: float
        - best_cspm: float
        """
        if not self.matches:
            return {
                'average_gpm': 0.0,
                'average_cspm': 0.0,
                'best_gpm': 0.0,
                'best_cspm': 0.0,
                'gpm_by_role': {},
                'cspm_by_role': {},
            }

        gpm_values = []
        cspm_values = []

        for match in self.matches:
            gold = match.get('gold_earned', 0)
            duration_min = match.get('game_duration_min', 1)
            if duration_min > 0:
                gpm_values.append(gold / duration_min)

            cspm = match.get('cs_per_min', 0.0)
            cspm_values.append(cspm)

        return {
            'average_gpm': sum(gpm_values) / len(gpm_values) if gpm_values else 0.0,
            'average_cspm': sum(cspm_values) / len(cspm_values) if cspm_values else 0.0,
            'best_gpm': max(gpm_values) if gpm_values else 0.0,
            'best_cspm': max(cspm_values) if cspm_values else 0.0,
            'gpm_by_role': self._get_gpm_by_role(),
            'cspm_by_role': self._get_cspm_by_role(),
        }

    def _get_gpm_by_role(self) -> Dict[str, float]:
        """Get average GPM by role."""
        role_gpm = {}
        for match in self.matches:
            role = match.get('role', 'UNKNOWN')
            gold = match.get('gold_earned', 0)
            duration_min = match.get('game_duration_min', 1)

            if duration_min > 0:
                gpm = gold / duration_min
                if role not in role_gpm:
                    role_gpm[role] = []
                role_gpm[role].append(gpm)

        return {
            role: sum(gpms) / len(gpms) if gpms else 0.0
            for role, gpms in role_gpm.items()
        }

    def _get_cspm_by_role(self) -> Dict[str, float]:
        """Get average CSPM by role."""
        role_cspm = {}
        for match in self.matches:
            role = match.get('role', 'UNKNOWN')
            cspm = match.get('cs_per_min', 0.0)

            if role not in role_cspm:
                role_cspm[role] = []
            role_cspm[role].append(cspm)

        return {
            role: sum(cspms) / len(cspms) if cspms else 0.0
            for role, cspms in role_cspm.items()
        }

    # ── Damage Share ─────────────────────────────────────────────────────

    def get_damage_share_stats(self) -> Dict[str, Any]:
        """Calculate damage share statistics.

        Note: Requires team damage data which may not be available.
        Currently returns damage stats without team context.

        Returns dict with:
        - average_damage: float
        - average_damage_per_min: float
        - damage_by_role: Dict[str, float]
        """
        if not self.matches:
            return {
                'average_damage': 0.0,
                'average_damage_per_min': 0.0,
                'damage_by_role': {},
            }

        damage_values = [m.get('total_damage_dealt', 0) for m in self.matches]
        dpm_values = []

        for match in self.matches:
            dmg = match.get('total_damage_dealt', 0)
            duration_min = match.get('game_duration_min', 1)
            if duration_min > 0:
                dpm_values.append(dmg / duration_min)

        return {
            'average_damage': sum(damage_values) / len(damage_values) if damage_values else 0.0,
            'average_damage_per_min': sum(dpm_values) / len(dpm_values) if dpm_values else 0.0,
            'damage_by_role': self._get_damage_by_role(),
            'max_damage': max(damage_values) if damage_values else 0,
        }

    def _get_damage_by_role(self) -> Dict[str, float]:
        """Get average damage by role."""
        role_dmg = {}
        for match in self.matches:
            role = match.get('role', 'UNKNOWN')
            dmg = match.get('total_damage_dealt', 0)

            if role not in role_dmg:
                role_dmg[role] = []
            role_dmg[role].append(dmg)

        return {
            role: sum(dmgs) / len(dmgs) if dmgs else 0.0
            for role, dmgs in role_dmg.items()
        }

    # ── Comeback Tracker ─────────────────────────────────────────────────

    def get_comeback_stats(self) -> Dict[str, Any]:
        """Identify comeback victories (won from gold deficit).

        A true comeback is when you win despite having LESS gold at the end
        (negative gold_diff) or a very close game (small positive gold_diff).

        Positive gold_diff = your team ahead, negative = behind.

        Returns dict with:
        - comeback_wins: int (wins where team was behind or barely ahead)
        - comeback_games: List[Dict] (match details of comebacks)
        - comeback_winrate: float
        """
        if not self.matches:
            return {
                'comeback_wins': 0,
                'comeback_games': [],
                'comeback_winrate': 0.0,
                'total_wins': 0,
            }

        wins = [m for m in self.matches if m.get('win', False)]

        # True comeback: won with negative gold diff (you had less gold)
        # OR won with very small positive gold diff (<2000 = very close game)
        comeback_wins = [
            m for m in wins
            if m.get('game_end_gold_diff', 9999) < 2000  # Behind or barely ahead
        ]

        comeback_games = [
            {
                'match_id': m.get('match_id'),
                'champion': m.get('champion_name'),
                'kda': f"{m.get('kills')}/{m.get('deaths')}/{m.get('assists')}",
                'gold_diff': m.get('game_end_gold_diff', 0),
                'duration': m.get('game_duration_min', 0),
            }
            for m in comeback_wins
        ]

        return {
            'comeback_wins': len(comeback_wins),
            'comeback_games': comeback_games[:10],  # Top 10 most recent
            'comeback_winrate': (len(comeback_wins) / len(wins) * 100) if wins else 0.0,
            'total_wins': len(wins),
        }

    # ── Promotion Predictor ──────────────────────────────────────────

    def get_promotion_prediction(self, current_lp: int, current_wins: int, current_losses: int) -> Dict[str, Any]:
        """Predict games needed for promotion based on recent performance.

        Args:
            current_lp: Current LP (0-100)
            current_wins: Total wins in current rank
            current_losses: Total losses in current rank

        Returns dict with:
        - games_to_promos: int (estimated games until 100 LP)
        - avg_lp_per_game: float (net LP gain per game from recent matches)
        - recent_winrate: float (last 20 games WR)
        - confidence: str ('high', 'medium', 'low')
        - promo_ready: bool (already at 100 LP)
        """
        if current_lp >= 100:
            return {
                'promo_ready': True,
                'games_to_promos': 0,
                'avg_lp_per_game': 0.0,
                'recent_winrate': 0.0,
                'confidence': 'high',
            }

        # Calculate recent winrate (last 20 ranked games)
        ranked_matches = [m for m in self.matches if m.get('queue_type') in ['RANKED_SOLO_5x5', 'RANKED_FLEX_SR']]
        recent_ranked = ranked_matches[:20] if len(ranked_matches) >= 20 else ranked_matches

        if not recent_ranked:
            return {
                'promo_ready': False,
                'games_to_promos': 0,
                'avg_lp_per_game': 0.0,
                'recent_winrate': 0.0,
                'confidence': 'low',
            }

        recent_wins = sum(1 for m in recent_ranked if m.get('win', False))
        recent_winrate = (recent_wins / len(recent_ranked)) * 100

        # Estimate LP per game based on winrate
        # Typical: +20-25 LP for win, -15-20 LP for loss
        # Simplified model: assume +22 LP win, -18 LP loss
        avg_lp_per_win = 22
        avg_lp_per_loss = -18
        avg_lp_per_game = (recent_winrate / 100) * avg_lp_per_win + ((100 - recent_winrate) / 100) * avg_lp_per_loss

        # Calculate games needed
        lp_needed = 100 - current_lp
        if avg_lp_per_game <= 0:
            games_needed = 999  # Not gaining LP
        else:
            games_needed = int(lp_needed / avg_lp_per_game) + 1

        # Determine confidence based on sample size and consistency
        if len(recent_ranked) >= 15:
            confidence = 'high'
        elif len(recent_ranked) >= 8:
            confidence = 'medium'
        else:
            confidence = 'low'

        return {
            'promo_ready': False,
            'games_to_promos': games_needed,
            'avg_lp_per_game': round(avg_lp_per_game, 1),
            'recent_winrate': round(recent_winrate, 1),
            'confidence': confidence,
            'lp_needed': lp_needed,
        }

    # ── All Stats ────────────────────────────────────────────────────────

    def get_all_advanced_stats(self) -> Dict[str, Any]:
        """Get all advanced statistics in one call."""
        return {
            'first_blood': self.get_first_blood_stats(),
            'kill_participation': self.get_kp_stats(),
            'gold_efficiency': self.get_gold_efficiency_stats(),
            'damage_share': self.get_damage_share_stats(),
            'comebacks': self.get_comeback_stats(),
        }
