"""QThread workers for running API calls without blocking the GUI."""

from PyQt6.QtCore import QThread, pyqtSignal

from src.data.data_manager import DataManager
from src.analytics.stats import StatsAnalyzer
from src.analytics.tilt import TiltDetector
from src.analytics.champions import ChampionAnalyzer
from src.analytics.challenges import ChallengeAnalyzer
from src.analytics.achievements import AchievementTracker


class FetchDataWorker(QThread):
    """Worker thread for fetching all data from Riot API."""
    progress = pyqtSignal(int, int, str)  # current, total, message
    finished = pyqtSignal(bool)           # success

    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.dm = data_manager

    def run(self):
        def on_progress(current, total, message):
            self.progress.emit(current, total, message)

        success = self.dm.fetch_all(progress_callback=on_progress)

        # Reload data from disk after fetching (still in worker thread)
        if success:
            self.dm.load_all()

        self.finished.emit(success)


class FetchMatchesWorker(QThread):
    """Worker thread for incrementally fetching new matches."""
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(bool)

    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.dm = data_manager

    def run(self):
        def on_progress(current, total, message):
            self.progress.emit(current, total, message)

        self.dm.fetch_matches(progress_callback=on_progress)

        # Reload data from disk after fetching (still in worker thread)
        self.dm.load_all()

        self.finished.emit(True)


class ScoutingWorker(QThread):
    """Worker thread for fetching player ranks during in-game via Riot API."""
    player_ready = pyqtSignal(str, dict)  # puuid, rank_data
    finished = pyqtSignal(dict)           # all results {puuid: rank_data}
    error = pyqtSignal(str)

    def __init__(self, riot_api, players: list[dict]):
        """
        Args:
            riot_api: RiotAPI instance
            players: list of dicts with 'puuid' and 'summoner_name' keys
        """
        super().__init__()
        self.api = riot_api
        self.players = players
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        results = {}
        for player in self.players:
            if self._cancelled:
                break

            puuid = player.get('puuid', '')
            if not puuid:
                continue

            try:
                entries = self.api.get_league_entries_by_puuid(puuid)
                rank_data = {'summoner_name': player.get('summoner_name', '')}

                if entries:
                    # Find solo queue entry
                    for entry in entries:
                        if entry.get('queueType') == 'RANKED_SOLO_5x5':
                            rank_data.update({
                                'tier': entry.get('tier', ''),
                                'rank': entry.get('rank', ''),
                                'lp': entry.get('leaguePoints', 0),
                                'wins': entry.get('wins', 0),
                                'losses': entry.get('losses', 0),
                            })
                            break

                if 'tier' not in rank_data:
                    rank_data['tier'] = ''
                    rank_data['rank'] = ''
                    rank_data['lp'] = 0
                    rank_data['wins'] = 0
                    rank_data['losses'] = 0

                # Calculate WR
                total = rank_data['wins'] + rank_data['losses']
                rank_data['winrate'] = round(rank_data['wins'] / max(total, 1) * 100, 1) if total else 0
                rank_data['total_games'] = total

                results[puuid] = rank_data
                self.player_ready.emit(puuid, rank_data)

            except Exception as e:
                print(f"Scouting error for {player.get('summoner_name', '?')}: {e}")

        self.finished.emit(results)


class AnalyticsWorker(QThread):
    """Worker thread for creating all analytics objects."""
    progress = pyqtSignal(int, int, str)  # current, total, message
    finished = pyqtSignal(dict)           # analyzers dict
    error = pyqtSignal(str)               # error message

    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.dm = data_manager

    def run(self):
        """Create all analyzers in background thread."""
        try:
            from concurrent.futures import ThreadPoolExecutor
            import time

            # Create analyzers in parallel where possible
            self.progress.emit(1, 6, "Analyzing performance stats...")
            start = time.time()
            stats = StatsAnalyzer(self.dm.matches)
            print(f"Stats: {time.time() - start:.2f}s")

            self.progress.emit(2, 6, "Analyzing performance trends...")
            start = time.time()
            tilt = TiltDetector(self.dm.matches)
            print(f"Tilt: {time.time() - start:.2f}s")

            self.progress.emit(3, 6, "Analyzing champions...")
            start = time.time()
            champ_analyzer = ChampionAnalyzer(self.dm.matches, self.dm.mastery, self.dm.dd)
            print(f"Champions: {time.time() - start:.2f}s")

            self.progress.emit(4, 6, "Processing challenges...")
            start = time.time()
            challenge_analyzer = ChallengeAnalyzer(
                self.dm.challenges, self.dm.challenges_config,
                self.dm.matches, self.dm.mastery, self.dm.dd
            )
            print(f"Challenges: {time.time() - start:.2f}s")

            self.progress.emit(5, 6, "Computing achievements...")
            start = time.time()
            achievement_tracker = AchievementTracker(self.dm.matches, tilt)
            print(f"Achievements: {time.time() - start:.2f}s")

            self.progress.emit(6, 7, "Analyzing season stats...")
            start = time.time()
            season_matches = self.dm.get_season_matches()
            season_stats = StatsAnalyzer(season_matches)
            season_tilt = TiltDetector(season_matches)
            print(f"Season stats: {time.time() - start:.2f}s ({len(season_matches)} season matches / {len(self.dm.matches)} total)")

            self.progress.emit(7, 7, "Finalizing...")

            # Return all analyzers
            analyzers = {
                'stats': stats,
                'tilt': tilt,
                'season_stats': season_stats,
                'season_tilt': season_tilt,
                'season_matches': season_matches,
                'champ_analyzer': champ_analyzer,
                'challenge_analyzer': challenge_analyzer,
                'achievement_tracker': achievement_tracker
            }

            self.finished.emit(analyzers)
        except Exception as e:
            import traceback
            error_msg = f"Error in analytics: {str(e)}\n{traceback.format_exc()}"
            self.error.emit(error_msg)
