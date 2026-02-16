import requests
import time
from typing import Optional, Dict, List, Any
from urllib.parse import quote
from config import RIOT_API_KEY, RIOT_REGIONS, RIOT_REGIONAL_ENDPOINTS


class RiotAPI:
    """Wrapper for Riot Games API"""

    def __init__(self, api_key: str = RIOT_API_KEY, region: str = 'EUW'):
        self.api_key = api_key
        self.region = region
        self.base_url = f"https://{RIOT_REGIONS[region]}"
        self.headers = {
            'X-Riot-Token': self.api_key
        }

        # Rate limiting tracking
        self.last_request_time = 0
        self.request_count_1s = 0
        self.request_count_2m = 0
        self.request_times = []

    def _rate_limit_check(self):
        """Simple rate limiting: 20 req/s, 100 req/2min for development key"""
        current_time = time.time()

        # Remove requests older than 2 minutes
        self.request_times = [t for t in self.request_times if current_time - t < 120]

        # Check 2-minute limit (100 requests)
        if len(self.request_times) >= 100:
            sleep_time = 120 - (current_time - self.request_times[0])
            if sleep_time > 0:
                print(f"Rate limit: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
                self.request_times.pop(0)

        # Check 1-second limit (20 requests)
        recent_requests = [t for t in self.request_times if current_time - t < 1]
        if len(recent_requests) >= 20:
            time.sleep(0.1)

        self.request_times.append(current_time)

    def _make_request(self, endpoint: str) -> Optional[Dict]:
        """Make API request with rate limiting and error handling"""
        self._rate_limit_check()

        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 1))
                print(f"Rate limited! Retrying after {retry_after}s")
                time.sleep(retry_after)
                return self._make_request(endpoint)
            elif response.status_code == 404:
                print(f"Resource not found: {endpoint}")
                return None
            else:
                print(f"Error {response.status_code}: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def get_summoner_by_name(self, summoner_name: str) -> Optional[Dict]:
        """Get summoner data by summoner name"""
        endpoint = f"/lol/summoner/v4/summoners/by-name/{summoner_name}"
        return self._make_request(endpoint)

    def get_summoner_by_puuid(self, puuid: str) -> Optional[Dict]:
        """Get summoner data by PUUID"""
        endpoint = f"/lol/summoner/v4/summoners/by-puuid/{puuid}"
        return self._make_request(endpoint)

    def get_account_by_riot_id(self, game_name: str, tag_line: str) -> Optional[Dict]:
        """Get account by Riot ID (game name + tagline)"""
        # URL encode the game name and tag to handle special characters
        game_name_encoded = quote(game_name, safe='')
        tag_line_encoded = quote(tag_line, safe='')

        # This uses regional routing
        region_routing = 'europe' if self.region in ['EUW', 'EUNE', 'TR', 'RU'] else 'americas'
        base_url = f"https://{RIOT_REGIONAL_ENDPOINTS[region_routing.upper()]}"
        endpoint = f"/riot/account/v1/accounts/by-riot-id/{game_name_encoded}/{tag_line_encoded}"

        url = f"{base_url}{endpoint}"

        # Apply rate limiting
        self._rate_limit_check()

        try:
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 1))
                print(f"Rate limited! Retrying after {retry_after}s")
                time.sleep(retry_after)
                return self.get_account_by_riot_id(game_name, tag_line)
            elif response.status_code == 404:
                print(f"Account not found: {game_name}#{tag_line}")
                return None
            else:
                print(f"Error getting account: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Failed to get account: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_champion_mastery(self, puuid: str) -> Optional[List[Dict]]:
        """Get all champion masteries for a player"""
        endpoint = f"/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}"
        return self._make_request(endpoint)

    def get_champion_mastery_top(self, puuid: str, count: int = 10) -> Optional[List[Dict]]:
        """Get top N champion masteries"""
        endpoint = f"/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/top?count={count}"
        return self._make_request(endpoint)

    def get_league_entries(self, summoner_id: str) -> Optional[List[Dict]]:
        """Get ranked league entries for a summoner (legacy - needs summoner ID)"""
        endpoint = f"/lol/league/v4/entries/by-summoner/{summoner_id}"
        return self._make_request(endpoint)

    def get_league_entries_by_puuid(self, puuid: str) -> Optional[List[Dict]]:
        """Get ranked league entries using PUUID"""
        endpoint = f"/lol/league/v4/entries/by-puuid/{puuid}"
        return self._make_request(endpoint)

    def _get_regional_base_url(self) -> str:
        """Get the regional routing base URL for this region"""
        region_routing = 'europe' if self.region in ['EUW', 'EUNE', 'TR', 'RU'] else 'americas'
        return f"https://{RIOT_REGIONAL_ENDPOINTS[region_routing.upper()]}"

    def _make_regional_request(self, endpoint: str) -> Optional[Any]:
        """Make API request to regional endpoint with rate limiting and error handling"""
        self._rate_limit_check()

        url = f"{self._get_regional_base_url()}{endpoint}"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 1))
                print(f"Rate limited! Retrying after {retry_after}s")
                time.sleep(retry_after)
                return self._make_regional_request(endpoint)
            elif response.status_code == 404:
                print(f"Resource not found: {endpoint}")
                return None
            else:
                print(f"Error {response.status_code}: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def get_match_history(self, puuid: str, count: int = 20, queue: Optional[int] = None,
                          start: int = 0, start_time: Optional[int] = None,
                          end_time: Optional[int] = None) -> Optional[List[str]]:
        """Get match history (returns list of match IDs)

        Args:
            puuid: Player PUUID
            count: Number of matches to return (max 100)
            queue: Queue type filter (420=Solo/Duo, 440=Flex)
            start: Start index for pagination
            start_time: Epoch timestamp in seconds - only matches after this time
            end_time: Epoch timestamp in seconds - only matches before this time
        """
        params = f"start={start}&count={count}"
        if queue is not None:
            params += f"&queue={queue}"
        if start_time is not None:
            params += f"&startTime={start_time}"
        if end_time is not None:
            params += f"&endTime={end_time}"

        endpoint = f"/lol/match/v5/matches/by-puuid/{puuid}/ids?{params}"
        return self._make_regional_request(endpoint)

    def get_all_match_ids(self, puuid: str, queue: Optional[int] = None,
                          start_time: Optional[int] = None,
                          end_time: Optional[int] = None) -> List[str]:
        """Fetch ALL match IDs by paginating through the match history API.

        Args:
            puuid: Player PUUID
            queue: Queue type filter (420=Solo/Duo, 440=Flex)
            start_time: Epoch timestamp in seconds - only matches after this time
            end_time: Epoch timestamp in seconds - only matches before this time

        Returns:
            Complete list of match ID strings
        """
        all_ids = []
        start = 0
        batch_size = 100

        while True:
            batch = self.get_match_history(puuid, count=batch_size, queue=queue,
                                           start=start, start_time=start_time,
                                           end_time=end_time)
            if batch is None:
                print(f"Error fetching matches at offset {start}, stopping.")
                break

            all_ids.extend(batch)
            print(f"  Fetched {len(batch)} match IDs (total: {len(all_ids)})")

            if len(batch) < batch_size:
                break  # No more matches

            start += batch_size

        return all_ids

    def get_match(self, match_id: str) -> Optional[Dict]:
        """Get detailed match data"""
        endpoint = f"/lol/match/v5/matches/{match_id}"
        return self._make_regional_request(endpoint)

    # --- Challenges API ---

    def get_challenges_config(self) -> Optional[List[Dict]]:
        """Get all challenge configurations (names, descriptions, thresholds)"""
        endpoint = "/lol/challenges/v1/challenges/config"
        return self._make_request(endpoint)

    def get_challenges_by_puuid(self, puuid: str) -> Optional[Dict]:
        """Get player's challenge progress (all challenges with current values and tiers)"""
        endpoint = f"/lol/challenges/v1/player-data/{puuid}"
        return self._make_request(endpoint)

    def get_challenges_percentiles(self) -> Optional[Dict]:
        """Get percentile distributions for all challenges"""
        endpoint = "/lol/challenges/v1/challenges/percentiles"
        return self._make_request(endpoint)
