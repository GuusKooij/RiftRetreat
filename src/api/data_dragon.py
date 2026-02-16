import requests
import json
import os
from typing import Optional, Dict, List
from config import CACHE_DIR


class DataDragon:
    """
    Data Dragon API wrapper for static League of Legends data
    (Champions, items, runes, summoner spells, etc.)
    """

    def __init__(self):
        self.base_url = "https://ddragon.leagueoflegends.com"
        self.cdn_url = "https://ddragon.leagueoflegends.com/cdn"
        self.version = None
        self.champions = {}
        self.champion_id_map = {}  # Map champion ID to champion key
        self.items = {}  # Map item ID (str) to item data
        self.summoner_spells = {}  # Map spell key to spell data
        self.runes_reforged = []  # Rune trees from runesReforged.json
        self._item_name_to_id = {}  # Map item name (lower) to item ID str

        # Ensure cache directory exists
        os.makedirs(CACHE_DIR, exist_ok=True)

        self.initialize()

    def initialize(self):
        """Initialize Data Dragon with latest version and champion data"""
        self.version = self.get_latest_version()
        if self.version:
            self.load_champion_data()
            self.load_item_data()
            self.load_summoner_spells()
            self.load_runes_reforged()

    def get_latest_version(self) -> Optional[str]:
        """Get the latest League of Legends version"""
        cache_file = os.path.join(CACHE_DIR, 'version.json')

        try:
            # Try cache first
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    if 'version' in data:
                        print(f"Using cached version: {data['version']}")
                        return data['version']

            # Fetch from API
            response = requests.get(f"{self.base_url}/api/versions.json", timeout=10)
            if response.status_code == 200:
                versions = response.json()
                latest_version = versions[0]

                # Cache the version
                with open(cache_file, 'w') as f:
                    json.dump({'version': latest_version}, f)

                print(f"Latest LoL version: {latest_version}")
                return latest_version
            else:
                print(f"Failed to fetch versions: {response.status_code}")
                return None

        except Exception as e:
            print(f"Error getting latest version: {e}")
            return None

    def load_champion_data(self):
        """Load champion data from Data Dragon"""
        if not self.version:
            print("No version available, cannot load champion data")
            return

        cache_file = os.path.join(CACHE_DIR, f'champions_{self.version}.json')

        try:
            # Try cache first
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.champions = data['data']
                    self._build_id_map()
                    print(f"Loaded {len(self.champions)} champions from cache")
                    return

            # Fetch from API
            url = f"{self.cdn_url}/{self.version}/data/en_US/champion.json"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                self.champions = data['data']

                # Cache the data
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                self._build_id_map()
                print(f"Loaded {len(self.champions)} champions from Data Dragon")
            else:
                print(f"Failed to fetch champion data: {response.status_code}")

        except Exception as e:
            print(f"Error loading champion data: {e}")

    def _build_id_map(self):
        """Build a map from champion ID (int) to champion key (string)"""
        self.champion_id_map = {}
        for champ_key, champ_data in self.champions.items():
            champ_id = int(champ_data['key'])
            self.champion_id_map[champ_id] = champ_key

    def load_item_data(self):
        """Load item data from Data Dragon"""
        if not self.version:
            return

        cache_file = os.path.join(CACHE_DIR, f'items_{self.version}.json')

        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.items = data.get('data', {})
                    self._build_item_name_map()
                    return

            url = f"{self.cdn_url}/{self.version}/data/en_US/item.json"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                self.items = data.get('data', {})

                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                self._build_item_name_map()
        except Exception as e:
            print(f"Error loading item data: {e}")

    def _build_item_name_map(self):
        """Build a map from item name (lowercase) to item ID"""
        self._item_name_to_id = {}
        for item_id, item_data in self.items.items():
            name = item_data.get('name', '').lower()
            if name:
                self._item_name_to_id[name] = item_id

    def load_summoner_spells(self):
        """Load summoner spell data from Data Dragon"""
        if not self.version:
            return

        cache_file = os.path.join(CACHE_DIR, f'summoner_{self.version}.json')

        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.summoner_spells = data.get('data', {})
                    return

            url = f"{self.cdn_url}/{self.version}/data/en_US/summoner.json"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                self.summoner_spells = data.get('data', {})

                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error loading summoner spell data: {e}")

    def load_runes_reforged(self):
        """Load runes reforged data from Data Dragon"""
        if not self.version:
            return

        cache_file = os.path.join(CACHE_DIR, f'runesReforged_{self.version}.json')

        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.runes_reforged = json.load(f)
                    return

            url = f"{self.cdn_url}/{self.version}/data/en_US/runesReforged.json"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                self.runes_reforged = response.json()

                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(self.runes_reforged, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error loading runes reforged data: {e}")

    def get_item_name(self, item_id: int) -> str:
        """Get item name by ID. Returns empty string for item 0 (empty slot)."""
        if item_id == 0:
            return ""
        item = self.items.get(str(item_id), {})
        return item.get('name', f'Item {item_id}')

    def get_item_id_by_name(self, item_name: str) -> Optional[str]:
        """Get item ID by name (case insensitive). Returns None if not found."""
        return self._item_name_to_id.get(item_name.lower())

    def get_item_icon_path(self, item_id: int) -> Optional[str]:
        """Get local path to cached item icon. Downloads if not cached."""
        if not self.version or item_id == 0:
            return None

        items_dir = os.path.join(CACHE_DIR, 'items')
        os.makedirs(items_dir, exist_ok=True)

        icon_path = os.path.join(items_dir, f'{item_id}.png')
        if os.path.exists(icon_path):
            return icon_path

        url = f"{self.cdn_url}/{self.version}/img/item/{item_id}.png"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                with open(icon_path, 'wb') as f:
                    f.write(response.content)
                return icon_path
        except Exception:
            pass
        return None

    def get_item_icon_path_by_name(self, item_name: str) -> Optional[str]:
        """Get item icon path by item name (case insensitive)."""
        item_id = self.get_item_id_by_name(item_name)
        if item_id:
            return self.get_item_icon_path(int(item_id))
        return None

    def get_summoner_spell_icon_path(self, spell_name: str) -> Optional[str]:
        """Get local path to cached summoner spell icon. Downloads if not cached.

        spell_name examples: 'Flash', 'Ignite', 'Smite', 'Teleport'
        """
        if not self.version:
            return None

        spells_dir = os.path.join(CACHE_DIR, 'spells')
        os.makedirs(spells_dir, exist_ok=True)

        # Find spell key (e.g., 'SummonerFlash' for 'Flash')
        spell_key = None
        for key, data in self.summoner_spells.items():
            if data.get('name', '').lower() == spell_name.lower():
                spell_key = key
                break

        if not spell_key:
            return None

        icon_path = os.path.join(spells_dir, f'{spell_key}.png')
        if os.path.exists(icon_path):
            return icon_path

        # Try to get image filename from spell data
        spell_data = self.summoner_spells.get(spell_key, {})
        image_filename = spell_data.get('image', {}).get('full', f'{spell_key}.png')

        url = f"{self.cdn_url}/{self.version}/img/spell/{image_filename}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                with open(icon_path, 'wb') as f:
                    f.write(response.content)
                return icon_path
        except Exception:
            pass
        return None

    def get_rune_icon_path(self, rune_name: str) -> Optional[str]:
        """Get local path to cached rune icon. Downloads if not cached.

        rune_name examples: 'Electrocute', 'Press the Attack', 'Triumph'
        """
        if not self.version:
            return None

        runes_dir = os.path.join(CACHE_DIR, 'runes')
        os.makedirs(runes_dir, exist_ok=True)

        # Find rune in runes_reforged data
        rune_id = None
        icon_rel_path = None

        for tree in self.runes_reforged:
            # Check keystone slots
            for slot in tree.get('slots', []):
                for rune in slot.get('runes', []):
                    if rune.get('name', '').lower() == rune_name.lower():
                        rune_id = rune.get('id')
                        icon_rel_path = rune.get('icon')
                        break
                if rune_id:
                    break
            if rune_id:
                break

        if not rune_id or not icon_rel_path:
            return None

        icon_path = os.path.join(runes_dir, f'{rune_id}.png')
        if os.path.exists(icon_path):
            return icon_path

        # icon_rel_path looks like "perk-images/Styles/Domination/Electrocute/Electrocute.png"
        url = f"{self.cdn_url}/img/{icon_rel_path}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                with open(icon_path, 'wb') as f:
                    f.write(response.content)
                return icon_path
        except Exception:
            pass
        return None

    def get_champion_icon_path(self, champion_name: str) -> Optional[str]:
        """Get local path to cached champion icon. Downloads if not cached.

        Handles display name -> DD key mapping (e.g. Bel'Veth -> Belveth,
        Wukong -> MonkeyKing, Cho'Gath -> Chogath, etc.)
        """
        if not self.version:
            return None

        icons_dir = os.path.join(CACHE_DIR, 'icons')
        os.makedirs(icons_dir, exist_ok=True)

        # Resolve display name to Data Dragon key
        dd_key = self._resolve_champion_key(champion_name)

        icon_path = os.path.join(icons_dir, f'{dd_key}.png')
        if os.path.exists(icon_path):
            return icon_path

        url = f"{self.cdn_url}/{self.version}/img/champion/{dd_key}.png"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                with open(icon_path, 'wb') as f:
                    f.write(response.content)
                return icon_path
        except Exception:
            pass
        return None

    def _resolve_champion_key(self, champion_name: str) -> str:
        """Resolve a champion display name to its Data Dragon key.

        E.g. "Bel'Veth" -> "Belveth", "Wukong" -> "MonkeyKing",
             "Cho'Gath" -> "Chogath", "Kai'Sa" -> "Kaisa"
        """
        # First check if it's already a valid DD key
        if champion_name in self.champions:
            return champion_name

        # Search by display name in champion data
        for champ_key, champ_data in self.champions.items():
            if champ_data['name'] == champion_name:
                return champ_key

        # Fallback: return as-is (might work for simple names)
        return champion_name

    def get_champion_by_id(self, champion_id: int) -> Optional[Dict]:
        """Get champion data by ID"""
        champ_key = self.champion_id_map.get(champion_id)
        if champ_key:
            return self.champions.get(champ_key)
        return None

    def get_champion_by_key(self, champion_key: str) -> Optional[Dict]:
        """Get champion data by key (e.g., 'Aatrox')"""
        return self.champions.get(champion_key)

    def get_champion_name(self, champion_id: int) -> str:
        """Get champion name by ID"""
        champ = self.get_champion_by_id(champion_id)
        if champ:
            return champ['name']
        return f"Unknown Champion ({champion_id})"

    def get_champion_icon_url(self, champion_id: int) -> Optional[str]:
        """Get champion icon URL"""
        if not self.version:
            return None

        champ = self.get_champion_by_id(champion_id)
        if champ:
            champion_key = champ['id']
            return f"{self.cdn_url}/{self.version}/img/champion/{champion_key}.png"
        return None

    def get_all_champions(self) -> Dict:
        """Get all champions data"""
        return self.champions

    def get_champion_list(self) -> List[Dict]:
        """Get list of all champions with basic info"""
        champion_list = []
        for champ_key, champ_data in self.champions.items():
            champion_list.append({
                'id': int(champ_data['key']),
                'key': champ_key,
                'name': champ_data['name'],
                'title': champ_data['title'],
                'tags': champ_data['tags']  # Roles: Fighter, Tank, Mage, etc.
            })
        return sorted(champion_list, key=lambda x: x['name'])

    def search_champions(self, query: str) -> List[Dict]:
        """Search champions by name"""
        query_lower = query.lower()
        results = []

        for champ_key, champ_data in self.champions.items():
            if query_lower in champ_data['name'].lower():
                results.append({
                    'id': int(champ_data['key']),
                    'key': champ_key,
                    'name': champ_data['name'],
                    'title': champ_data['title'],
                    'tags': champ_data['tags']
                })

        return sorted(results, key=lambda x: x['name'])

    def get_champions_by_role(self, role: str) -> List[Dict]:
        """
        Get champions by role
        Roles: Fighter, Tank, Mage, Assassin, Marksman, Support
        """
        role_champions = []

        for champ_key, champ_data in self.champions.items():
            if role in champ_data.get('tags', []):
                role_champions.append({
                    'id': int(champ_data['key']),
                    'key': champ_key,
                    'name': champ_data['name'],
                    'tags': champ_data['tags']
                })

        return sorted(role_champions, key=lambda x: x['name'])

    def download_champion_icon(self, champion_id: int, save_path: str) -> bool:
        """Download champion icon image"""
        icon_url = self.get_champion_icon_url(champion_id)

        if not icon_url:
            return False

        try:
            response = requests.get(icon_url, timeout=10)
            if response.status_code == 200:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                print(f"Failed to download icon: {response.status_code}")
                return False
        except Exception as e:
            print(f"Error downloading champion icon: {e}")
            return False

    def get_splash_art_url(self, champion_id: int, skin_num: int = 0) -> Optional[str]:
        """Get champion splash art URL (skin_num=0 for default)"""
        champ = self.get_champion_by_id(champion_id)
        if champ:
            champion_key = champ['id']
            return f"{self.cdn_url}/img/champion/splash/{champion_key}_{skin_num}.jpg"
        return None
