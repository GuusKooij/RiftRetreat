import requests
import base64
import psutil
import os
import json
from typing import Optional, Dict


class LCUApi:
    """
    League Client Update (LCU) API wrapper
    Connects to the local League client to get real-time champion select data
    """

    def __init__(self):
        self.port = None
        self.token = None
        self.base_url = None
        self.headers = None
        self.session = requests.Session()
        self.session.verify = False  # LCU uses self-signed certificate

        # Suppress SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def connect(self) -> bool:
        """Connect to the League client by reading lockfile"""
        lockfile_path = self._find_lockfile()

        if not lockfile_path:
            print("League client not running or lockfile not found")
            return False

        try:
            with open(lockfile_path, 'r') as f:
                data = f.read().split(':')
                self.port = data[2]
                self.token = data[3]

            self.base_url = f"https://127.0.0.1:{self.port}"

            # Create authorization header
            auth_string = f"riot:{self.token}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')

            self.headers = {
                'Authorization': f'Basic {auth_b64}',
                'Content-Type': 'application/json'
            }

            # Test connection
            response = self.session.get(f"{self.base_url}/lol-summoner/v1/current-summoner",
                                        headers=self.headers, timeout=5)

            if response.status_code == 200:
                print("Successfully connected to League client")
                return True
            else:
                print(f"Failed to connect: {response.status_code}")
                return False

        except Exception as e:
            print(f"Error connecting to League client: {e}")
            return False

    def _find_lockfile(self) -> Optional[str]:
        """Find the League client lockfile"""
        # Common League of Legends installation paths
        possible_paths = [
            os.path.join(os.getenv('LOCALAPPDATA', ''), 'Riot Games', 'League of Legends', 'lockfile'),
            'C:\\Riot Games\\League of Legends\\lockfile',
            'D:\\Riot Games\\League of Legends\\lockfile',
        ]

        # Check common paths first
        for path in possible_paths:
            if os.path.exists(path):
                return path

        # Try to find via running process
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                if proc.info['name'] == 'LeagueClientUx.exe':
                    exe_path = proc.info['exe']
                    if exe_path:
                        lockfile_path = os.path.join(os.path.dirname(exe_path), 'lockfile')
                        if os.path.exists(lockfile_path):
                            return lockfile_path
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return None

    def _make_request(self, endpoint: str, method: str = 'GET', data: Optional[Dict] = None) -> Optional[Dict]:
        """Make request to LCU API"""
        if not self.base_url or not self.headers:
            if not self.connect():
                return None

        url = f"{self.base_url}{endpoint}"

        try:
            if method == 'GET':
                response = self.session.get(url, headers=self.headers, timeout=5)
            elif method == 'POST':
                response = self.session.post(url, headers=self.headers, json=data, timeout=5)
            else:
                print(f"Unsupported method: {method}")
                return None

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                print(f"LCU request error {response.status_code}: {endpoint}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"LCU request failed: {e}")
            return None

    def get_current_summoner(self) -> Optional[Dict]:
        """Get current logged-in summoner"""
        return self._make_request('/lol-summoner/v1/current-summoner')

    def get_champ_select_session(self) -> Optional[Dict]:
        """Get current champion select session"""
        return self._make_request('/lol-champ-select/v1/session')

    def is_in_champ_select(self) -> bool:
        """Check if currently in champion select"""
        session = self.get_champ_select_session()
        return session is not None

    def get_champ_select_info(self) -> Optional[Dict]:
        """Get detailed champion select information"""
        session = self.get_champ_select_session()

        if not session:
            return None

        return {
            'my_team': [action for action in session.get('myTeam', [])],
            'their_team': [action for action in session.get('theirTeam', [])],
            'local_player_cell_id': session.get('localPlayerCellId'),
            'timer': session.get('timer', {}),
            'phase': session.get('timer', {}).get('phase', 'Unknown')
        }
