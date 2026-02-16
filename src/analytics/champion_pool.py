"""Champion pool analysis: diversity, one-tricks, comfort picks, personal tier list."""

from typing import List, Dict, Any
from collections import defaultdict


class ChampionPoolAnalyzer:
    """Analyzes player's champion pool for diversity, comfort picks, and performance tiers."""

    def __init__(self, matches: List[Dict[str, Any]]):
        """Initialize with list of processed match dicts."""
        self.matches = matches

    def get_role_diversity_score(self) -> Dict[str, Any]:
        """Calculate role diversity score (0-100).

        Higher score = more diverse role pool
        100 = plays all 5 roles equally
        0 = only plays one role

        Returns dict with:
        - diversity_score: float (0-100)
        - role_distribution: Dict[str, int] (games per role)
        - most_played_role: str
        - least_played_role: str
        - rating: str ('Specialist', 'Focused', 'Flexible', 'Fill Player')
        """
        if not self.matches:
            return {
                'diversity_score': 0.0,
                'role_distribution': {},
                'most_played_role': '',
                'least_played_role': '',
                'rating': 'No Data',
            }

        # Count games per role
        role_counts: Dict[str, int] = defaultdict(int)
        for match in self.matches:
            role = match.get('role', 'UNKNOWN')
            if role != 'UNKNOWN':
                role_counts[role] += 1

        if not role_counts:
            return {
                'diversity_score': 0.0,
                'role_distribution': {},
                'most_played_role': '',
                'least_played_role': '',
                'rating': 'No Data',
            }

        total_games = sum(role_counts.values())
        num_roles = len(role_counts)

        # Calculate diversity using entropy-like measure
        # Perfect diversity (5 roles equally) = 100
        # Single role only = 0
        if num_roles == 1:
            diversity_score = 0.0
        else:
            # Calculate how evenly distributed the games are
            ideal_per_role = total_games / 5  # If perfectly split across 5 roles
            variance = sum((count - ideal_per_role) ** 2 for count in role_counts.values())
            max_variance = (total_games - ideal_per_role) ** 2 * 5  # All games in one role

            # Normalize to 0-100 (lower variance = higher diversity)
            diversity_score = max(0, (1 - variance / max_variance) * 100) if max_variance > 0 else 0

        # Determine rating
        if diversity_score >= 70:
            rating = 'Fill Player'
        elif diversity_score >= 50:
            rating = 'Flexible'
        elif diversity_score >= 25:
            rating = 'Focused'
        else:
            rating = 'Specialist'

        most_played = max(role_counts.items(), key=lambda x: x[1])[0]
        least_played = min(role_counts.items(), key=lambda x: x[1])[0] if num_roles > 1 else most_played

        return {
            'diversity_score': round(diversity_score, 1),
            'role_distribution': dict(role_counts),
            'most_played_role': most_played,
            'least_played_role': least_played,
            'rating': rating,
        }

    def detect_one_tricks(self, min_games: int = 10) -> Dict[str, Any]:
        """Detect if player is one-tricking any champions.

        One-trick criteria:
        - Champion played in >=30% of all games
        - At least min_games on the champion

        Returns dict with:
        - is_one_trick: bool
        - one_trick_champions: List[Dict] (champs meeting criteria)
        - total_games: int
        """
        if not self.matches:
            return {
                'is_one_trick': False,
                'one_trick_champions': [],
                'total_games': 0,
            }

        champ_counts: Dict[str, int] = defaultdict(int)
        champ_wins: Dict[str, int] = defaultdict(int)

        for match in self.matches:
            champ = match.get('champion_name', 'Unknown')
            champ_counts[champ] += 1
            if match.get('win', False):
                champ_wins[champ] += 1

        total_games = len(self.matches)
        one_trick_threshold = total_games * 0.30

        one_tricks = []
        for champ, games in champ_counts.items():
            if games >= min_games and games >= one_trick_threshold:
                wins = champ_wins[champ]
                wr = (wins / games * 100) if games > 0 else 0
                pick_rate = (games / total_games * 100) if total_games > 0 else 0

                one_tricks.append({
                    'champion': champ,
                    'games': games,
                    'wins': wins,
                    'losses': games - wins,
                    'winrate': round(wr, 1),
                    'pick_rate': round(pick_rate, 1),
                })

        # Sort by games played
        one_tricks.sort(key=lambda x: x['games'], reverse=True)

        return {
            'is_one_trick': len(one_tricks) > 0,
            'one_trick_champions': one_tricks,
            'total_games': total_games,
        }

    def get_comfort_picks(self, min_games: int = 5) -> Dict[str, Any]:
        """Identify comfort picks (high WR, enough games).

        Comfort pick criteria:
        - At least min_games played
        - Winrate >= 55%

        Returns dict with:
        - comfort_picks: List[Dict] (sorted by WR)
        - safe_picks: List[Dict] (50-54.9% WR, good fallbacks)
        - learning_picks: List[Dict] (<50% WR, avoid or practice)
        """
        if not self.matches:
            return {
                'comfort_picks': [],
                'safe_picks': [],
                'learning_picks': [],
            }

        champ_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {'games': 0, 'wins': 0})

        for match in self.matches:
            champ = match.get('champion_name', 'Unknown')
            champ_stats[champ]['games'] += 1
            if match.get('win', False):
                champ_stats[champ]['wins'] += 1

        comfort_picks = []
        safe_picks = []
        learning_picks = []

        for champ, stats in champ_stats.items():
            games = stats['games']
            wins = stats['wins']

            if games < min_games:
                continue

            wr = (wins / games * 100) if games > 0 else 0
            data = {
                'champion': champ,
                'games': games,
                'wins': wins,
                'losses': games - wins,
                'winrate': round(wr, 1),
            }

            if wr >= 55:
                comfort_picks.append(data)
            elif wr >= 50:
                safe_picks.append(data)
            else:
                learning_picks.append(data)

        # Sort all by winrate desc
        comfort_picks.sort(key=lambda x: x['winrate'], reverse=True)
        safe_picks.sort(key=lambda x: x['winrate'], reverse=True)
        learning_picks.sort(key=lambda x: x['winrate'], reverse=True)

        return {
            'comfort_picks': comfort_picks,
            'safe_picks': safe_picks,
            'learning_picks': learning_picks,
        }

    def get_personal_tier_list(self, min_games: int = 3, mastery_data: List[Dict[str, Any]] | None = None, dd=None, include_unplayed: bool = True) -> Dict[str, Any]:
        """Generate personal tier list based on performance.

        Tiers:
        - S: WR >= 65%, games >= min_games
        - A: WR >= 55%, games >= min_games
        - B: WR >= 50%, games >= min_games
        - C: WR >= 45%, games >= min_games
        - D: WR < 45%, games >= min_games
        - Potential: < min_games but high mastery (M5+) OR historical good performance

        Args:
            min_games: Minimum games required for ranking
            mastery_data: Optional list of mastery dicts from API
            dd: DataDragon instance for champion ID to name mapping
            include_unplayed: Include champions not played this season but with mastery

        Returns dict with:
        - tiers: Dict[str, List[Dict]] (S, A, B, C, D, Potential tiers)
        - unranked: List[Dict] (too few games, no mastery)
        """
        champ_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'games': 0,
            'wins': 0,
            'kills': 0,
            'deaths': 0,
            'assists': 0,
        })

        # Collect stats from matches
        if self.matches:
            for match in self.matches:
                champ = match.get('champion_name', 'Unknown')
                champ_stats[champ]['games'] += 1
                if match.get('win', False):
                    champ_stats[champ]['wins'] += 1
                champ_stats[champ]['kills'] += match.get('kills', 0)
                champ_stats[champ]['deaths'] += match.get('deaths', 0)
                champ_stats[champ]['assists'] += match.get('assists', 0)

        # Build mastery lookup by champion name
        mastery_by_name = {}
        played_champs = set(champ_stats.keys())

        if mastery_data and dd:
            for m in mastery_data:
                champ_id = m.get('championId')
                points = m.get('championPoints', 0)
                level = m.get('championLevel', 0)

                # Map champion ID to name
                champ_data = dd.get_champion_by_id(champ_id)
                if champ_data:
                    champ_name = champ_data.get('name', '')
                    mastery_by_name[champ_name] = {
                        'points': points,
                        'level': level,
                    }

        tiers: Dict[str, List[Dict[str, Any]]] = {'S': [], 'A': [], 'B': [], 'C': [], 'D': [], 'Potential': []}
        unranked = []

        # Process champions played this season
        for champ, stats in champ_stats.items():
            games = stats['games']
            wins = stats['wins']

            wr = (wins / games * 100) if games > 0 else 0
            avg_k = stats['kills'] / games if games > 0 else 0
            avg_d = stats['deaths'] / games if games > 0 else 0
            avg_a = stats['assists'] / games if games > 0 else 0
            kda = ((avg_k + avg_a) / avg_d) if avg_d > 0 else (avg_k + avg_a)

            data = {
                'champion': champ,
                'games': games,
                'wins': wins,
                'losses': games - wins,
                'winrate': round(wr, 1),
                'kda': round(kda, 2),
                'mastery_points': mastery_by_name.get(champ, {}).get('points', 0),
                'mastery_level': mastery_by_name.get(champ, {}).get('level', 0),
                'played_this_season': True,
            }

            if games < min_games:
                # Few games but might have mastery - add to Potential
                if data['mastery_level'] >= 5:
                    tiers['Potential'].append(data)
                else:
                    unranked.append(data)
            elif wr >= 65:
                tiers['S'].append(data)
            elif wr >= 55:
                tiers['A'].append(data)
            elif wr >= 50:
                tiers['B'].append(data)
            elif wr >= 45:
                tiers['C'].append(data)
            else:
                tiers['D'].append(data)

        # Add unplayed champions with high mastery (M5+)
        if include_unplayed and mastery_by_name:
            for champ_name, mastery_info in mastery_by_name.items():
                if champ_name not in played_champs and mastery_info['level'] >= 5:
                    data = {
                        'champion': champ_name,
                        'games': 0,
                        'wins': 0,
                        'losses': 0,
                        'winrate': 0.0,
                        'kda': 0.0,
                        'mastery_points': mastery_info['points'],
                        'mastery_level': mastery_info['level'],
                        'played_this_season': False,
                    }
                    tiers['Potential'].append(data)

        # Sort each tier
        for tier_name, tier_list in tiers.items():
            if tier_name == 'Potential':
                # Sort Potential by mastery level desc, then points desc
                tier_list.sort(key=lambda x: (x['mastery_level'], x['mastery_points']), reverse=True)
            else:
                # Sort by WR desc, then games desc
                tier_list.sort(key=lambda x: (x['winrate'], x['games']), reverse=True)

        unranked.sort(key=lambda x: x['games'], reverse=True)

        return {
            'tiers': tiers,
            'unranked': unranked,
        }
