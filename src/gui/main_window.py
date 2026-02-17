"""Main application window with sidebar navigation."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QMessageBox,
    QDialog, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap

from config import RIOT_REGIONS, load_app_settings, save_app_settings
from src.gui.theme import STYLESHEET, COLORS
from src.gui.workers import FetchDataWorker, FetchMatchesWorker, AnalyticsWorker
from src.gui.pages.dashboard import DashboardPage
from src.gui.pages.champions import ChampionsPage
from src.gui.pages.challenges import ChallengesPage
from src.gui.pages.match_history import MatchHistoryPage
from src.gui.pages.live_game import LiveGamePage
from src.gui.pages.settings import SettingsPage
from src.gui.pages.records import RecordsPage
from src.gui.pages.nuzlocke import NuzlockePage
from src.gui.pages.league_play import LeaguePlayPage
from src.gui.pages.rank_predictor import RankPredictorPage
from src.gui.pages.stat_cards import StatCardsPage
from src.gui.pages.kryptonite import KryptonitePage
from src.gui.pages.item_builds import ItemBuildsPage
from src.gui.pages.friend_compare import FriendComparePage
from src.gui.pages.coaching_report import CoachingReportPage

from src.data.data_manager import DataManager


class FirstRunDialog(QDialog):
    """Dialog shown on first startup to configure account."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to RiftRetreat")
        self.setFixedSize(420, 280)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_card']};
            }}
            QLabel {{
                color: {COLORS['text']};
            }}
            QLineEdit, QComboBox {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 6px;
                font-size: 14px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Welcome to RiftRetreat!")
        title.setStyleSheet(f"color: {COLORS['gold']}; font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        desc = QLabel("Enter your Riot ID to get started.\nYou can change this later in Settings.")
        desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        # Riot ID row
        id_layout = QHBoxLayout()
        id_label = QLabel("Riot ID:")
        id_label.setFixedWidth(70)
        id_layout.addWidget(id_label)

        self.game_name_input = QLineEdit()
        self.game_name_input.setPlaceholderText("Game Name")
        id_layout.addWidget(self.game_name_input)

        hash_label = QLabel("#")
        hash_label.setFixedWidth(15)
        hash_label.setStyleSheet(f"color: {COLORS['gold']}; font-size: 16px; font-weight: bold;")
        id_layout.addWidget(hash_label)

        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Tag")
        self.tag_input.setFixedWidth(80)
        id_layout.addWidget(self.tag_input)

        layout.addLayout(id_layout)

        # Region row
        region_layout = QHBoxLayout()
        region_label = QLabel("Region:")
        region_label.setFixedWidth(70)
        region_layout.addWidget(region_label)

        self.region_combo = QComboBox()
        self.region_combo.addItems(sorted(RIOT_REGIONS.keys()))
        self.region_combo.setCurrentText("EUW")
        region_layout.addWidget(self.region_combo)
        region_layout.addStretch()

        layout.addLayout(region_layout)
        layout.addStretch()

        # Confirm button
        self.confirm_btn = QPushButton("Get Started")
        self.confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['gold_dark']};
                color: {COLORS['text_bright']};
                font-weight: bold;
                padding: 10px 24px;
                border-radius: 6px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['gold']};
                color: {COLORS['bg_dark']};
            }}
        """)
        self.confirm_btn.clicked.connect(self._on_confirm)
        layout.addWidget(self.confirm_btn)

    def _on_confirm(self):
        if not self.game_name_input.text().strip():
            self.game_name_input.setPlaceholderText("Required!")
            self.game_name_input.setStyleSheet(
                self.game_name_input.styleSheet() + f"border-color: {COLORS['red']};"
            )
            return
        if not self.tag_input.text().strip():
            self.tag_input.setPlaceholderText("Required!")
            return
        self.accept()

    def get_settings(self) -> dict:
        return {
            'game_name': self.game_name_input.text().strip(),
            'tag_line': self.tag_input.text().strip(),
            'region': self.region_combo.currentText(),
        }


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RiftRetreat")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # Set window icon (custom RiftRetreat icon - no copyright)
        import os
        import sys

        # Handle development, --onefile, and --onedir PyInstaller paths
        icon_paths = []
        if getattr(sys, 'frozen', False):
            # PyInstaller: try exe directory first (--onedir), then _MEIPASS (--onefile)
            icon_paths.append(os.path.join(os.path.dirname(sys.executable), "riftretreat_icon.ico"))
            icon_paths.append(os.path.join(sys._MEIPASS, "riftretreat_icon.ico"))
        else:
            icon_paths.append(os.path.join(os.path.abspath("."), "riftretreat_icon.ico"))

        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                self.setWindowIcon(icon)
                from PyQt6.QtWidgets import QApplication
                QApplication.instance().setWindowIcon(icon)
                break

        self.setStyleSheet(STYLESHEET)

        # Load persistent settings or show first-run dialog
        self._app_settings = load_app_settings()
        self._first_run_refresh = False  # Flag for auto-refresh on first run
        if not self._app_settings.get('game_name'):
            self._show_first_run()

        game_name = self._app_settings.get('game_name', 'Retreat')
        tag_line = self._app_settings.get('tag_line', 'EUW')
        region = self._app_settings.get('region', 'EUW')
        api_key = self._app_settings.get('api_key')

        # Data manager
        self.dm = DataManager(game_name, tag_line, region=region, api_key=api_key)

        # Pages
        self.dashboard_page = DashboardPage()
        self.champions_page = ChampionsPage()
        self.challenges_page = ChallengesPage()
        self.match_history_page = MatchHistoryPage()
        self.live_game_page = LiveGamePage()
        self.records_page = RecordsPage()
        self.nuzlocke_page = NuzlockePage()
        self.league_play_page = LeaguePlayPage()
        self.rank_predictor_page = RankPredictorPage()
        self.stat_cards_page = StatCardsPage()
        self.kryptonite_page = KryptonitePage()
        self.item_builds_page = ItemBuildsPage()
        self.friend_compare_page = FriendComparePage()
        self.coaching_report_page = CoachingReportPage()
        self.settings_page = SettingsPage(self._app_settings)

        self.settings_page.on_refresh = self._on_refresh
        self.settings_page.on_export = self._on_export

        self._setup_ui()
        self._load_data()

        # Auto-refresh data after first-run setup
        if self._first_run_refresh:
            # Use QTimer to trigger after UI is fully loaded
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(500, lambda: self._on_refresh('full'))

    def _show_first_run(self):
        """Show first-run setup dialog."""
        dialog = FirstRunDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._app_settings = dialog.get_settings()
            save_app_settings(self._app_settings)
            # Flag to trigger auto-refresh after UI is set up
            self._first_run_refresh = True
        else:
            # User closed without configuring — use defaults
            self._app_settings = {'game_name': '', 'tag_line': '', 'region': 'EUW'}
            self._first_run_refresh = False

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Sidebar ---
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_sidebar']};
                border-right: 1px solid {COLORS['border']};
            }}
        """)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # App title
        title = QLabel("LoL Companion")
        title.setStyleSheet(f"""
            color: {COLORS['gold']};
            font-size: 18px;
            font-weight: bold;
            padding: 20px;
            background: transparent;
        """)
        sidebar_layout.addWidget(title)

        # Nav buttons with icons
        self.nav_buttons = []
        pages = [
            ("📊 Dashboard", 0),
            ("⚔️ Champions", 1),
            ("🏆 Challenges", 2),
            ("📜 Match History", 3),
            ("🔴 Live Game", 4),
            ("📈 Records", 5),
            ("💀 Nuzlocke", 6),
            ("🎮 LeaguePlay", 7),
            ("🏅 Rank Predictor", 8),
            ("📸 Stat Cards", 9),
            ("🛡️ Kryptonite", 10),
            ("🔧 Item Builds", 11),
            ("👥 Friend Compare", 12),
            ("📋 Coaching Report", 13),
            ("⚙️ Settings", 14),
        ]

        for name, index in pages:
            btn = QPushButton(name)
            btn.setObjectName("nav_button")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=index: self._switch_page(i))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # Version
        version = QLabel("v1.2.0")
        version.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; padding: 12px; background: transparent;")
        sidebar_layout.addWidget(version)

        main_layout.addWidget(sidebar)

        # --- Content area ---
        self.stack = QStackedWidget()
        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.champions_page)
        self.stack.addWidget(self.challenges_page)
        self.stack.addWidget(self.match_history_page)
        self.stack.addWidget(self.live_game_page)
        self.stack.addWidget(self.records_page)
        self.stack.addWidget(self.nuzlocke_page)
        self.stack.addWidget(self.league_play_page)
        self.stack.addWidget(self.rank_predictor_page)
        self.stack.addWidget(self.stat_cards_page)
        self.stack.addWidget(self.kryptonite_page)
        self.stack.addWidget(self.item_builds_page)
        self.stack.addWidget(self.friend_compare_page)
        self.stack.addWidget(self.coaching_report_page)
        self.stack.addWidget(self.settings_page)

        main_layout.addWidget(self.stack)

        # Start on dashboard
        self._switch_page(0)

    def _switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setProperty("active", "true" if i == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _load_data(self):
        """Load saved data and populate pages."""
        has_data = self.dm.load_all()

        if has_data and self.dm.matches:
            # Defer heavy analytics until after window is shown
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, self._refresh_pages)
        else:
            # No data — switch to settings and prompt refresh
            self._switch_page(14)

    def _refresh_pages(self):
        """Refresh all page content with current data."""
        from src.gui.loading_dialog import LoadingDialog
        from src.gui.workers import AnalyticsWorker

        # Show modal loading dialog
        self._loading_dialog = LoadingDialog(self)
        self._loading_dialog.show()

        # Run analytics in background thread (avoids main thread slowdown)
        self._analytics_worker = AnalyticsWorker(self.dm)
        self._analytics_worker.progress.connect(self._on_analytics_progress)
        self._analytics_worker.finished.connect(self._on_analytics_finished)
        self._analytics_worker.error.connect(self._on_analytics_error)
        self._analytics_worker.start()

    def _on_analytics_progress(self, current: int, total: int, message: str):
        """Update loading dialog progress during analytics."""
        if hasattr(self, '_loading_dialog'):
            self._loading_dialog.update_progress(current, total, message)

    def _on_analytics_error(self, error_msg: str):
        """Handle analytics error."""
        if hasattr(self, '_loading_dialog'):
            self._loading_dialog.close()
        QMessageBox.critical(self, "Analytics Error", f"Failed to process data:\n\n{error_msg}")
        self._switch_page(14)

    def _on_analytics_finished(self, analyzers: dict):
        """Handle analytics completion and update pages."""
        # Store analyzers
        self._pending_analyzers = analyzers

        # Start page updates via timer
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, lambda: self._update_pages_stage1(self._loading_dialog))


    def _update_pages_stage1(self, loading_dialog):
        """Update dashboard and champions (stage 1 of 3)."""
        stats = self._pending_analyzers['stats']
        tilt = self._pending_analyzers['tilt']
        season_stats = self._pending_analyzers['season_stats']
        season_tilt = self._pending_analyzers['season_tilt']
        champ_analyzer = self._pending_analyzers['champ_analyzer']

        self.dashboard_page.update_data(
            self.dm.profile, self.dm.ranked_stats, stats, tilt, self.dm.climb_history,
            season_stats=season_stats, season_tilt=season_tilt
        )
        self.champions_page.update_data(champ_analyzer, stats_analyzer=stats)

        # Continue to next stage
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, lambda: self._update_pages_stage2(loading_dialog))

    def _update_pages_stage2(self, loading_dialog):
        """Update challenges, match history, records (stage 2 of 3)."""
        stats = self._pending_analyzers['stats']
        challenge_analyzer = self._pending_analyzers['challenge_analyzer']
        achievement_tracker = self._pending_analyzers['achievement_tracker']
        champ_analyzer = self._pending_analyzers['champ_analyzer']

        self.challenges_page.update_data(challenge_analyzer)
        self.match_history_page.update_data(self.dm.matches, data_dragon=self.dm.dd)
        self.records_page.update_data(stats, achievement_tracker, challenge_analyzer=challenge_analyzer)

        # Continue to next stage
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, lambda: self._update_pages_stage3(loading_dialog))

    def _update_pages_stage3(self, loading_dialog):
        """Update remaining pages and finish (stage 3 of 3)."""
        stats = self._pending_analyzers['stats']
        tilt = self._pending_analyzers['tilt']
        champ_analyzer = self._pending_analyzers['champ_analyzer']
        challenge_analyzer = self._pending_analyzers['challenge_analyzer']

        self.live_game_page.set_analyzers(
            challenge_analyzer, champ_analyzer, self.dm.dd,
            stats_analyzer=stats, riot_api=self.dm.api, matches=self.dm.matches
        )
        self.nuzlocke_page.update_data(self.dm.matches, data_dragon=self.dm.dd)
        self.league_play_page.set_data_dragon(self.dm.dd)

        # Get current rank for rank predictor
        current_rank = None
        ranked_entry = self.dm.get_ranked_entry('RANKED_SOLO_5x5')
        if ranked_entry:
            current_rank = ranked_entry.get('tier')

        season_matches = self._pending_analyzers['season_matches']
        self.rank_predictor_page.update_data(season_matches, current_rank=current_rank)
        self.stat_cards_page.update_data(stats, tilt, champ_analyzer, matches=self.dm.matches, data_dragon=self.dm.dd)

        # New v1.2.0 pages
        self.kryptonite_page.update_data(self.dm.matches, data_dragon=self.dm.dd)
        self.item_builds_page.update_data(self.dm.matches, data_dragon=self.dm.dd)
        self.coaching_report_page.update_data(
            self.dm.matches, stats, tilt, champ_analyzer,
            current_rank=current_rank, data_dragon=self.dm.dd
        )

        # Friend compare: pass riot_api and user's ranked entries
        user_name = self.dm.profile.get('gameName', 'You') if self.dm.profile else 'You'
        self.friend_compare_page.set_data(self.dm.api, self.dm.ranked_stats, user_name=user_name)

        self.settings_page.update_stats(
            self.dm.profile,
            len(self.dm.matches),
            len(self.dm.mastery),
            len(self.dm.challenges.get('challenges', []))
        )

        # Clean up and finish
        self._pending_analyzers = None

        # Hide progress bar
        if hasattr(self, 'settings_page'):
            self.settings_page.hide_progress()

        # Close loading dialog
        loading_dialog.close()

        # Go to dashboard
        self._switch_page(0)

    def _on_refresh(self, mode: str):
        """Handle data refresh from settings page."""
        config = self.settings_page.get_config()

        # Save settings persistently
        self._app_settings.update({
            'game_name': config['game_name'],
            'tag_line': config['tag_line'],
            'region': config['region'],
            'api_key': config.get('api_key'),
        })
        save_app_settings(self._app_settings)

        # Update data manager with current settings
        self.dm = DataManager(
            config['game_name'], config['tag_line'],
            region=config['region'], api_key=config.get('api_key')
        )
        # Don't load old data - let the worker fetch fresh data for the new account

        if mode == 'full':
            self.worker = FetchDataWorker(self.dm)
        else:
            self.worker = FetchMatchesWorker(self.dm)

        self.worker.progress.connect(self._on_fetch_progress)
        self.worker.finished.connect(self._on_fetch_finished)
        self.worker.start()

    def _on_export(self) -> str:
        """Handle CSV export from settings page."""
        return self.dm.export_matches_csv()

    def _on_fetch_progress(self, current: int, total: int, message: str):
        # Show progress bar if settings page is available
        if hasattr(self, 'settings_page'):
            self.settings_page.show_progress(current, total, message)

    def _on_fetch_finished(self, success: bool):
        if success:
            # Show "Processing data..." message
            if hasattr(self, 'settings_page'):
                self.settings_page.show_progress(0, 0, "Processing data...")

            # Use QTimer to let UI update before starting heavy analytics
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, self._finish_refresh)
        else:
            # Hide progress bar
            if hasattr(self, 'settings_page'):
                self.settings_page.hide_progress()

            QMessageBox.warning(
                self, "Error",
                "Failed to fetch data. Check your API key and try again."
            )

    def _finish_refresh(self):
        """Complete the refresh by running analytics and updating pages."""
        # Hide progress bar - analytics will show loading dialog
        if hasattr(self, 'settings_page'):
            self.settings_page.hide_progress()

        # Data already reloaded in worker thread
        # _refresh_pages() now handles showing loading dialog and switching pages
        self._refresh_pages()

    def closeEvent(self, event):
        self.live_game_page.stop_polling()
        super().closeEvent(event)
