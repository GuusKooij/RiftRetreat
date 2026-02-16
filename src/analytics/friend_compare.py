"""
FriendComparer: Compares your ranked stats with a friend's.
Uses only league entries (rank, WR, games) — no individual match fetching.
"""


RANK_VALUES = {
    'IRON': 1, 'BRONZE': 2, 'SILVER': 3, 'GOLD': 4,
    'PLATINUM': 5, 'EMERALD': 6, 'DIAMOND': 7,
    'MASTER': 8, 'GRANDMASTER': 9, 'CHALLENGER': 10,
}
RANK_DIVISION = {'IV': 0, 'III': 0.25, 'II': 0.5, 'I': 0.75}


def rank_value(tier: str, rank: str) -> float:
    base = RANK_VALUES.get(tier.upper(), 0) if tier else 0
    return base + RANK_DIVISION.get(rank, 0)


def rank_display(tier: str, rank: str, lp: int = 0) -> str:
    if not tier:
        return "Unranked"
    t = tier.capitalize()
    if tier.upper() in ('MASTER', 'GRANDMASTER', 'CHALLENGER'):
        return f"{t} ({lp} LP)"
    return f"{t} {rank}"


class FriendComparer:
    """Compares two players' ranked stats from league entries."""

    def __init__(self, user_entries: list[dict], friend_entries: list[dict],
                 user_name: str = "You", friend_name: str = "Friend"):
        self.user_entries = user_entries
        self.friend_entries = friend_entries
        self.user_name = user_name
        self.friend_name = friend_name

    def _get_solo_entry(self, entries: list[dict]) -> dict:
        """Get solo/duo queue entry."""
        for e in entries:
            if e.get('queueType') == 'RANKED_SOLO_5x5':
                return e
        return {}

    def _get_flex_entry(self, entries: list[dict]) -> dict:
        """Get flex queue entry."""
        for e in entries:
            if e.get('queueType') == 'RANKED_FLEX_SR':
                return e
        return {}

    def _extract_stats(self, entry: dict) -> dict:
        """Extract stats from a league entry."""
        if not entry:
            return {
                'tier': '', 'rank': '', 'lp': 0,
                'wins': 0, 'losses': 0, 'games': 0,
                'winrate': 0, 'rank_display': 'Unranked',
                'rank_value': 0,
            }

        tier = entry.get('tier', '')
        rank_str = entry.get('rank', '')
        wins = entry.get('wins', 0)
        losses = entry.get('losses', 0)
        total = wins + losses
        lp = entry.get('leaguePoints', 0)

        return {
            'tier': tier,
            'rank': rank_str,
            'lp': lp,
            'wins': wins,
            'losses': losses,
            'games': total,
            'winrate': round(wins / max(total, 1) * 100, 1) if total else 0,
            'rank_display': rank_display(tier, rank_str, lp),
            'rank_value': rank_value(tier, rank_str),
        }

    def compare_solo(self) -> dict:
        """Compare solo/duo queue stats."""
        user = self._extract_stats(self._get_solo_entry(self.user_entries))
        friend = self._extract_stats(self._get_solo_entry(self.friend_entries))

        return {
            'queue': 'Solo/Duo',
            'user': user,
            'friend': friend,
            'higher_rank': self.user_name if user['rank_value'] > friend['rank_value']
                          else (self.friend_name if friend['rank_value'] > user['rank_value'] else 'Same'),
            'higher_wr': self.user_name if user['winrate'] > friend['winrate']
                        else (self.friend_name if friend['winrate'] > user['winrate'] else 'Same'),
            'more_games': self.user_name if user['games'] > friend['games']
                         else (self.friend_name if friend['games'] > user['games'] else 'Same'),
        }

    def compare_flex(self) -> dict:
        """Compare flex queue stats."""
        user = self._extract_stats(self._get_flex_entry(self.user_entries))
        friend = self._extract_stats(self._get_flex_entry(self.friend_entries))

        return {
            'queue': 'Flex',
            'user': user,
            'friend': friend,
            'higher_rank': self.user_name if user['rank_value'] > friend['rank_value']
                          else (self.friend_name if friend['rank_value'] > user['rank_value'] else 'Same'),
            'higher_wr': self.user_name if user['winrate'] > friend['winrate']
                        else (self.friend_name if friend['winrate'] > user['winrate'] else 'Same'),
            'more_games': self.user_name if user['games'] > friend['games']
                         else (self.friend_name if friend['games'] > user['games'] else 'Same'),
        }

    def summary(self) -> dict:
        """Overall comparison summary."""
        solo = self.compare_solo()
        flex = self.compare_flex()

        user_points = 0
        friend_points = 0

        for comp in [solo, flex]:
            if comp['higher_rank'] == self.user_name:
                user_points += 2
            elif comp['higher_rank'] == self.friend_name:
                friend_points += 2

            if comp['higher_wr'] == self.user_name:
                user_points += 1
            elif comp['higher_wr'] == self.friend_name:
                friend_points += 1

        if user_points > friend_points:
            verdict = f"{self.user_name} is ranked higher overall"
        elif friend_points > user_points:
            verdict = f"{self.friend_name} is ranked higher overall"
        else:
            verdict = "Very evenly matched!"

        return {
            'solo': solo,
            'flex': flex,
            'verdict': verdict,
            'user_points': user_points,
            'friend_points': friend_points,
        }
