"""Settings page: Riot ID, region, API key, data refresh, export."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QLineEdit, QComboBox, QPushButton, QProgressBar, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt

from config import RIOT_REGIONS, RIOT_API_KEY, APP_VERSION
from src.gui.theme import COLORS


class SettingsPage(QWidget):
    def __init__(self, app_settings: dict = None):
        super().__init__()
        self._app_settings = app_settings or {}
        self.on_refresh = None  # callback
        self.on_export = None   # callback for CSV export
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # --- Account Information (Read-only) ---
        card, card_layout = self._card("Account Information")

        # Riot ID (read-only)
        id_layout = QHBoxLayout()
        id_label = QLabel("Riot ID:")
        id_label.setFixedWidth(100)
        id_label.setStyleSheet("border: none;")
        id_layout.addWidget(id_label)

        game_name = self._app_settings.get('game_name', '')
        tag_line = self._app_settings.get('tag_line', '')
        riot_id_display = QLabel(f"<b>{game_name}</b><span style='color: {COLORS['gold']};'> #{tag_line}</span>")
        riot_id_display.setStyleSheet(f"color: {COLORS['text_bright']}; font-size: 14px; border: none;")
        riot_id_display.setTextFormat(Qt.TextFormat.RichText)
        id_layout.addWidget(riot_id_display)
        id_layout.addStretch()
        card_layout.addLayout(id_layout)

        # Region (read-only)
        region_layout = QHBoxLayout()
        region_label = QLabel("Region:")
        region_label.setFixedWidth(100)
        region_label.setStyleSheet("border: none;")
        region_layout.addWidget(region_label)

        region_display = QLabel(self._app_settings.get('region', 'EUW'))
        region_display.setStyleSheet(f"color: {COLORS['text_bright']}; font-size: 14px; border: none;")
        region_layout.addWidget(region_display)
        region_layout.addStretch()
        card_layout.addLayout(region_layout)

        layout.addWidget(card)

        # --- Data Management ---
        data_card, data_layout = self._card("Data Management")

        self.last_updated_label = QLabel("Last updated: Never")
        self.last_updated_label.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
        data_layout.addWidget(self.last_updated_label)

        self.data_stats_label = QLabel("")
        self.data_stats_label.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
        data_layout.addWidget(self.data_stats_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(20)
        data_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none;")
        self.progress_label.setVisible(False)
        data_layout.addWidget(self.progress_label)

        # Buttons
        btn_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("Refresh All Data")
        self.refresh_btn.setStyleSheet(f"""
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
            QPushButton:disabled {{
                background-color: {COLORS['border']};
                color: {COLORS['text_dim']};
            }}
        """)
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)
        btn_layout.addWidget(self.refresh_btn)

        self.update_matches_btn = QPushButton("Update New Matches Only")
        self.update_matches_btn.clicked.connect(self._on_update_matches_clicked)
        btn_layout.addWidget(self.update_matches_btn)

        btn_layout.addStretch()
        data_layout.addLayout(btn_layout)

        layout.addWidget(data_card)

        # --- Export ---
        export_card, export_layout = self._card("Data Export")

        export_desc = QLabel("Export your match history as a CSV file for external analysis.")
        export_desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none;")
        export_layout.addWidget(export_desc)

        self.export_btn = QPushButton("Export Match History to CSV")
        self.export_btn.clicked.connect(self._on_export_clicked)
        export_layout.addWidget(self.export_btn)

        self.export_status = QLabel("")
        self.export_status.setStyleSheet(f"color: {COLORS['green']}; font-size: 12px; border: none;")
        export_layout.addWidget(self.export_status)

        layout.addWidget(export_card)

        # API Key is now stored securely in .env file and not exposed in UI
        # See config.py for RIOT_API_KEY loaded from environment

        # --- About ---
        about_card, about_layout = self._card("About RiftRetreat")

        app_info = QLabel(
            "<b>RiftRetreat</b><br>"
            "League of Legends Companion App<br><br>"
            f"Version {APP_VERSION}<br><br>"
            "<i>© 2026 Treatey (Retreat#EUW)<br>"
            "All rights reserved.</i><br><br>"
            "RiftRetreat is an independent tool and is not affiliated with,<br>"
            "endorsed by, or sponsored by Riot Games, Inc.<br><br>"
            "League of Legends and Riot Games are trademarks or<br>"
            "registered trademarks of Riot Games, Inc."
        )
        app_info.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none;")
        app_info.setWordWrap(True)
        app_info.setTextFormat(Qt.TextFormat.RichText)
        about_layout.addWidget(app_info)

        # GitHub link
        github_link = QLabel(
            "<a href='https://github.com/GuusKooij/RiftRetreat' style='color: " + COLORS['blue'] + ";'>"
            "🔗 View on GitHub</a>"
        )
        github_link.setStyleSheet(f"font-size: 12px; border: none;")
        github_link.setTextFormat(Qt.TextFormat.RichText)
        github_link.setOpenExternalLinks(True)
        github_link.setCursor(Qt.CursorShape.PointingHandCursor)
        about_layout.addWidget(github_link)

        layout.addWidget(about_card)

        layout.addStretch()

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _card(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {COLORS['gold']}; font-size: 16px; font-weight: bold; border: none;")
        layout.addWidget(title_label)

        return card, layout

    def get_config(self) -> dict:
        """Return the stored app settings (account info is now read-only)."""
        return {
            'game_name': self._app_settings.get('game_name', ''),
            'tag_line': self._app_settings.get('tag_line', ''),
            'region': self._app_settings.get('region', 'EUW'),
            # API key no longer configurable in UI - stored securely in .env
        }

    def update_stats(self, profile: dict, match_count: int, mastery_count: int, challenge_count: int):
        last_updated = profile.get('last_updated', 'Never')
        self.last_updated_label.setText(f"Last updated: {last_updated}")
        self.data_stats_label.setText(
            f"Matches: {match_count}  |  Mastery: {mastery_count} champions  |  "
            f"Challenges: {challenge_count} progressed"
        )

    def show_progress(self, current: int, total: int, message: str):
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_label.setText(message)

        if total > 0:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(current)
        else:
            self.progress_bar.setRange(0, 0)  # Indeterminate

    def hide_progress(self):
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.refresh_btn.setEnabled(True)
        self.update_matches_btn.setEnabled(True)

    def _on_refresh_clicked(self):
        self.refresh_btn.setEnabled(False)
        self.update_matches_btn.setEnabled(False)
        if self.on_refresh:
            self.on_refresh('full')

    def _on_update_matches_clicked(self):
        self.refresh_btn.setEnabled(False)
        self.update_matches_btn.setEnabled(False)
        if self.on_refresh:
            self.on_refresh('matches')

    def _on_export_clicked(self):
        if self.on_export:
            filepath = self.on_export()
            if filepath:
                self.export_status.setText(f"Exported to: {filepath}")
