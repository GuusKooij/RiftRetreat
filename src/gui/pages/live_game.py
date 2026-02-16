"""Live Game page: LCU polling, champion select detection, scouting, draft helper, game plan tips."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer

from src.api.lcu_api import LCUApi
from src.analytics.draft import DraftHelper
from src.gui.theme import COLORS


class LiveGamePage(QWidget):
    def __init__(self):
        super().__init__()
        self.lcu = LCUApi()
        self.challenge_analyzer = None
        self.champion_analyzer = None
        self.data_dragon = None
        self.draft_helper = DraftHelper()

        self._setup_ui()
        self._setup_polling()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        self.layout_main = QVBoxLayout(container)
        self.layout_main.setSpacing(16)
        self.layout_main.setContentsMargins(24, 24, 24, 24)

        # Status header
        self.status_frame = QFrame()
        self.status_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        status_layout = QVBoxLayout(self.status_frame)
        status_layout.setContentsMargins(16, 16, 16, 16)

        self.status_label = QLabel("Checking League Client connection...")
        self.status_label.setStyleSheet(f"color: {COLORS['text']}; font-size: 16px; font-weight: bold; border: none;")
        status_layout.addWidget(self.status_label)

        self.status_detail = QLabel("")
        self.status_detail.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none;")
        status_layout.addWidget(self.status_detail)

        self.layout_main.addWidget(self.status_frame)

        # Content area (populated dynamically)
        self.content_area = QVBoxLayout()
        self.layout_main.addLayout(self.content_area)

        self.layout_main.addStretch()

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _setup_polling(self):
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self._poll_lcu)
        self.poll_timer.start(3000)  # Poll every 3 seconds

    def set_analyzers(self, challenge_analyzer, champion_analyzer, data_dragon):
        self.challenge_analyzer = challenge_analyzer
        self.champion_analyzer = champion_analyzer
        self.data_dragon = data_dragon

    def _clear_content(self):
        while self.content_area.count():
            child = self.content_area.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

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

    def _poll_lcu(self):
        try:
            connected = self.lcu.connect()
        except Exception:
            connected = False

        if not connected:
            self.status_label.setText("League Client not detected")
            self.status_label.setStyleSheet(f"color: {COLORS['red']}; font-size: 16px; font-weight: bold; border: none;")
            self.status_detail.setText("Start League of Legends to enable live features")
            self._clear_content()
            return

        if self.lcu.is_in_champ_select():
            self.status_label.setText("In Champion Select!")
            self.status_label.setStyleSheet(f"color: {COLORS['green']}; font-size: 16px; font-weight: bold; border: none;")
            self.status_detail.setText("Live data from champion select")
            self._show_champ_select()
        else:
            self.status_label.setText("League Client connected")
            self.status_label.setStyleSheet(f"color: {COLORS['blue']}; font-size: 16px; font-weight: bold; border: none;")
            self.status_detail.setText("Waiting for champion select...")
            self._clear_content()
            self._show_idle_suggestions()

    def _show_champ_select(self):
        self._clear_content()

        session = self.lcu.get_champ_select_info()
        if not session:
            return

        # Show teams
        card, layout = self._card("Champion Select")

        my_team = session.get('my_team', [])
        their_team = session.get('their_team', [])

        if my_team:
            team_label = QLabel("Your Team:")
            team_label.setStyleSheet(f"color: {COLORS['blue']}; font-weight: bold; border: none;")
            layout.addWidget(team_label)

            for player in my_team:
                champ_id = player.get('championId', 0)
                if champ_id and self.data_dragon:
                    name = self.data_dragon.get_champion_name(champ_id)
                    p_label = QLabel(f"  {name}")
                else:
                    p_label = QLabel("  Picking...")
                p_label.setStyleSheet(f"color: {COLORS['text']}; border: none;")
                layout.addWidget(p_label)

        if their_team:
            enemy_label = QLabel("Enemy Team:")
            enemy_label.setStyleSheet(f"color: {COLORS['red']}; font-weight: bold; border: none;")
            layout.addWidget(enemy_label)

            for player in their_team:
                champ_id = player.get('championId', 0)
                if champ_id and self.data_dragon:
                    name = self.data_dragon.get_champion_name(champ_id)
                    p_label = QLabel(f"  {name}")
                else:
                    p_label = QLabel("  Picking...")
                p_label.setStyleSheet(f"color: {COLORS['text']}; border: none;")
                layout.addWidget(p_label)

        self.content_area.addWidget(card)

        # Draft analysis
        team_names = []
        for player in my_team:
            champ_id = player.get('championId', 0)
            if champ_id and self.data_dragon:
                team_names.append(self.data_dragon.get_champion_name(champ_id))

        if team_names:
            self._show_draft_analysis(team_names)

        # Game plan tips
        self._show_game_plan_tips()

    def _show_idle_suggestions(self):
        """Show champion suggestions when not in champ select."""
        if not self.challenge_analyzer:
            return

        card, layout = self._card("Suggested Champions for Next Game")

        recs = self.challenge_analyzer.champion_recommendations()[:5]
        for r in recs:
            row = QHBoxLayout()

            name = QLabel(r['champion'])
            name.setFixedWidth(120)
            name_color = COLORS['green'] if r['new_win'] else COLORS['text']
            name.setStyleSheet(f"color: {name_color}; font-weight: bold; border: none;")
            row.addWidget(name)

            roles = QLabel(f"{' / '.join(r['suggested_roles'])}")
            roles.setFixedWidth(150)
            roles.setStyleSheet(f"color: {COLORS['blue']}; border: none;")
            row.addWidget(roles)

            reasons = QLabel(" | ".join(r['reasons'][:2]))
            reasons.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
            row.addWidget(reasons)

            row.addStretch()
            layout.addLayout(row)

        self.content_area.addWidget(card)

        # Always show in-game tips
        self._show_game_plan_tips()

    def _show_draft_analysis(self, team_names: list[str]):
        analysis = self.draft_helper.analyze_team(team_names)
        if not analysis:
            return

        card, layout = self._card("Draft Analysis")

        balance_label = QLabel(
            f"Damage: {analysis['damage_balance']}  "
            f"(AD: {analysis['ad_count']}  AP: {analysis['ap_count']}  Mixed: {analysis['mixed_count']})  |  "
            f"Engage: {analysis['engage_count']}"
        )
        balance_label.setStyleSheet(f"color: {COLORS['text']}; border: none;")
        layout.addWidget(balance_label)

        for warning in analysis.get('warnings', []):
            warn = QLabel(f"!! {warning}")
            warn.setStyleSheet(f"color: {COLORS['red']}; font-weight: bold; border: none;")
            layout.addWidget(warn)

        suggestion = self.draft_helper.suggest_damage_type(team_names)
        if suggestion != 'either':
            suggest_label = QLabel(f"Consider picking {suggestion} damage to balance the comp")
            suggest_label.setStyleSheet(f"color: {COLORS['orange']}; font-style: italic; border: none;")
            layout.addWidget(suggest_label)

        self.content_area.addWidget(card)

    def _show_game_plan_tips(self):
        if not self.challenge_analyzer:
            return

        tips = self.challenge_analyzer.get_in_game_tips()
        if not tips:
            return

        card, layout = self._card("Game Plan - Challenge Tips")

        for tip in tips[:6]:
            tip_frame = QFrame()
            tip_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_main']};
                    border-left: 3px solid {COLORS['gold']};
                    border-radius: 4px;
                    padding: 2px;
                }}
            """)
            tip_layout = QVBoxLayout(tip_frame)
            tip_layout.setContentsMargins(12, 6, 12, 6)
            tip_layout.setSpacing(2)

            header = QHBoxLayout()
            name = QLabel(tip['challenge_name'])
            name.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; font-size: 12px; border: none;")
            header.addWidget(name)

            progress = QLabel(tip['progress'])
            progress.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; border: none;")
            header.addWidget(progress)

            header.addStretch()
            tip_layout.addLayout(header)

            tip_text = QLabel(tip['tip'])
            tip_text.setStyleSheet(f"color: {COLORS['text']}; font-size: 12px; border: none;")
            tip_text.setWordWrap(True)
            tip_layout.addWidget(tip_text)

            layout.addWidget(tip_frame)

        self.content_area.addWidget(card)

    def stop_polling(self):
        self.poll_timer.stop()
