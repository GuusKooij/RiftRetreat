"""
ItemBuildAnalyzer: Analyzes item builds per champion to identify
which core items correlate with wins.
"""

from collections import defaultdict


# Boot item IDs (common boots)
BOOT_IDS = {
    3006, 3009, 3020, 3047, 3111, 3117, 3158,  # Standard boots
    2422,  # Slightly Magical Footwear (rune)
}


class ItemBuildAnalyzer:
    def __init__(self, matches: list[dict], data_dragon):
        self.matches = matches
        self.dd = data_dragon

    def _is_completed_item(self, item_id: int) -> bool:
        """Check if an item is a completed (non-component) item."""
        if item_id == 0:
            return False
        item_data = self.dd.items.get(str(item_id), {})
        gold = item_data.get('gold', {})
        total_gold = gold.get('total', 0)
        purchasable = gold.get('purchasable', True)
        return total_gold >= 2500 and purchasable

    def _is_boots(self, item_id: int) -> bool:
        """Check if an item is boots."""
        if item_id in BOOT_IDS:
            return True
        item_data = self.dd.items.get(str(item_id), {})
        tags = item_data.get('tags', [])
        return 'Boots' in tags

    def _get_item_name(self, item_id: int) -> str:
        """Get item name by ID."""
        return self.dd.get_item_name(item_id)

    def items_by_champion(self, min_games: int = 3) -> list[dict]:
        """Per-champion core item win rate analysis."""
        champ_groups = defaultdict(list)
        for m in self.matches:
            champ_groups[m['champion']].append(m)

        results = []
        for champ, games in champ_groups.items():
            if len(games) < min_games:
                continue

            item_stats = defaultdict(lambda: {'wins': 0, 'losses': 0})

            for game in games:
                items = game.get('items', [])
                seen = set()
                for item_id in items:
                    if item_id == 0 or self._is_boots(item_id) or item_id in seen:
                        continue
                    if not self._is_completed_item(item_id):
                        continue
                    seen.add(item_id)
                    if game['win']:
                        item_stats[item_id]['wins'] += 1
                    else:
                        item_stats[item_id]['losses'] += 1

            item_list = []
            for item_id, data in item_stats.items():
                total = data['wins'] + data['losses']
                if total < 2:
                    continue
                item_list.append({
                    'item_id': item_id,
                    'item_name': self._get_item_name(item_id),
                    'games': total,
                    'wins': data['wins'],
                    'losses': data['losses'],
                    'winrate': round(data['wins'] / total * 100, 1),
                    'pick_rate': round(total / len(games) * 100, 1),
                })

            item_list.sort(key=lambda x: x['games'], reverse=True)

            wins = sum(1 for g in games if g['win'])
            results.append({
                'champion': champ,
                'champion_id': games[0].get('champion_id'),
                'total_games': len(games),
                'winrate': round(wins / len(games) * 100, 1),
                'core_items': item_list[:8],
            })

        results.sort(key=lambda x: x['total_games'], reverse=True)
        return results

    def first_item_analysis(self, champion: str, min_games: int = 2) -> list[dict]:
        """Compare win rates by the most expensive non-boots item built (proxy for first item)."""
        games = [m for m in self.matches if m['champion'] == champion]
        if len(games) < min_games:
            return []

        item_stats = defaultdict(lambda: {'wins': 0, 'losses': 0})

        for game in games:
            items = game.get('items', [])
            # Find most expensive completed non-boots item
            best_item = None
            best_gold = 0
            for item_id in items:
                if item_id == 0 or self._is_boots(item_id):
                    continue
                if not self._is_completed_item(item_id):
                    continue
                item_data = self.dd.items.get(str(item_id), {})
                gold = item_data.get('gold', {}).get('total', 0)
                if gold > best_gold:
                    best_gold = gold
                    best_item = item_id

            if best_item:
                if game['win']:
                    item_stats[best_item]['wins'] += 1
                else:
                    item_stats[best_item]['losses'] += 1

        results = []
        for item_id, data in item_stats.items():
            total = data['wins'] + data['losses']
            if total < min_games:
                continue
            results.append({
                'item_id': item_id,
                'item_name': self._get_item_name(item_id),
                'games': total,
                'wins': data['wins'],
                'losses': data['losses'],
                'winrate': round(data['wins'] / total * 100, 1),
            })

        results.sort(key=lambda x: x['games'], reverse=True)
        return results

    def boots_analysis(self, min_games: int = 2) -> list[dict]:
        """WR by boots choice across all games."""
        boot_stats = defaultdict(lambda: {'wins': 0, 'losses': 0})

        for game in self.matches:
            items = game.get('items', [])
            for item_id in items:
                if item_id and self._is_boots(item_id):
                    if game['win']:
                        boot_stats[item_id]['wins'] += 1
                    else:
                        boot_stats[item_id]['losses'] += 1
                    break  # Only count first boots found

        results = []
        for item_id, data in boot_stats.items():
            total = data['wins'] + data['losses']
            if total < min_games:
                continue
            results.append({
                'item_id': item_id,
                'item_name': self._get_item_name(item_id),
                'games': total,
                'wins': data['wins'],
                'losses': data['losses'],
                'winrate': round(data['wins'] / total * 100, 1),
            })

        results.sort(key=lambda x: x['games'], reverse=True)
        return results

    def get_champion_names(self, min_games: int = 3) -> list[str]:
        """Get list of champions with enough games for item analysis."""
        champ_counts = defaultdict(int)
        for m in self.matches:
            champ_counts[m['champion']] += 1
        return sorted([c for c, n in champ_counts.items() if n >= min_games])
