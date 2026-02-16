"""Vision score analysis: trends, by role, comparative analysis."""

from typing import List, Dict, Any


class VisionAnalyzer:
    """Analyzes vision score patterns and trends."""

    def __init__(self, matches: List[Dict[str, Any]]):
        """Initialize with list of processed match dicts."""
        self.matches = matches

    def get_vision_stats(self) -> Dict[str, Any]:
        """Calculate comprehensive vision statistics.

        Returns dict with:
        - average_vision: float
        - max_vision: float
        - min_vision: float
        - vision_trend: List[float] (last 20 games)
        - vision_by_role: Dict[str, float]
        - vision_in_wins: float (avg in wins)
        - vision_in_losses: float (avg in losses)
        - control_wards: Dict (avg control wards placed/destroyed)
        """
        if not self.matches:
            return {
                'average_vision': 0.0,
                'max_vision': 0.0,
                'min_vision': 0.0,
                'vision_trend': [],
                'vision_by_role': {},
                'vision_in_wins': 0.0,
                'vision_in_losses': 0.0,
                'control_wards_placed': 0.0,
                'control_wards_destroyed': 0.0,
                'wards_placed': 0.0,
                'wards_destroyed': 0.0,
            }

        vision_scores = [m.get('vision_score', 0) for m in self.matches]

        # Wins vs losses
        wins = [m for m in self.matches if m.get('win', False)]
        losses = [m for m in self.matches if not m.get('win', False)]

        vision_in_wins = [m.get('vision_score', 0) for m in wins]
        vision_in_losses = [m.get('vision_score', 0) for m in losses]

        # Ward stats
        control_placed = [m.get('detector_wards_placed', 0) for m in self.matches]
        wards_placed = [m.get('wards_placed', 0) for m in self.matches]
        wards_killed = [m.get('wards_killed', 0) for m in self.matches]

        return {
            'average_vision': sum(vision_scores) / len(vision_scores) if vision_scores else 0.0,
            'max_vision': max(vision_scores) if vision_scores else 0.0,
            'min_vision': min(vision_scores) if vision_scores else 0.0,
            'vision_trend': vision_scores[:20] if len(vision_scores) >= 20 else vision_scores,
            'vision_by_role': self._get_vision_by_role(),
            'vision_in_wins': sum(vision_in_wins) / len(vision_in_wins) if vision_in_wins else 0.0,
            'vision_in_losses': sum(vision_in_losses) / len(vision_in_losses) if vision_in_losses else 0.0,
            'control_wards_placed': sum(control_placed) / len(control_placed) if control_placed else 0.0,
            'wards_placed': sum(wards_placed) / len(wards_placed) if wards_placed else 0.0,
            'wards_destroyed': sum(wards_killed) / len(wards_killed) if wards_killed else 0.0,
        }

    def _get_vision_by_role(self) -> Dict[str, float]:
        """Get average vision score by role."""
        role_vision = {}
        for match in self.matches:
            role = match.get('role', 'UNKNOWN')
            vision = match.get('vision_score', 0)

            if role not in role_vision:
                role_vision[role] = []
            role_vision[role].append(vision)

        return {
            role: sum(scores) / len(scores) if scores else 0.0
            for role, scores in role_vision.items()
        }

    def get_vision_rating(self, avg_vision: float, role: str = None) -> str:
        """Rate vision score performance.

        Benchmarks (approximate):
        - Support: 80+ excellent, 60-80 good, 40-60 average, <40 poor
        - Others: 50+ excellent, 35-50 good, 20-35 average, <20 poor
        """
        if role and role.upper() == 'UTILITY':
            # Support benchmarks
            if avg_vision >= 80:
                return 'Excellent'
            elif avg_vision >= 60:
                return 'Good'
            elif avg_vision >= 40:
                return 'Average'
            else:
                return 'Needs Improvement'
        else:
            # Other roles
            if avg_vision >= 50:
                return 'Excellent'
            elif avg_vision >= 35:
                return 'Good'
            elif avg_vision >= 20:
                return 'Average'
            else:
                return 'Needs Improvement'
