"""Live Game page: LCU polling, champion select detection, scouting, draft helper, game plan tips."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QProgressBar, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap

from src.api.lcu_api import LCUApi
from src.analytics.draft import DraftHelper
from src.analytics.live_game_analyzer import LiveGameAnalyzer
from src.gui.workers import ScoutingWorker
from src.gui.theme import COLORS, RANK_COLORS


class LiveGamePage(QWidget):
    def __init__(self):
        super().__init__()
        self.lcu = LCUApi()
        self.challenge_analyzer = None
        self.champion_analyzer = None
        self.data_dragon = None
        self.draft_helper = DraftHelper()
        self.live_analyzer = None
        self.riot_api = None
        self.matches = None
        self.stats_analyzer = None

        # Phase tracking
        self._current_phase = None
        self._last_game_id = None
        self._scouting_worker = None
        self._scouting_results = {}
        self._lcu_connected = False

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
        self.poll_timer.start(3000)

    def set_analyzers(self, challenge_analyzer, champion_analyzer, data_dragon,
                      stats_analyzer=None, riot_api=None, matches=None):
        self.challenge_analyzer = challenge_analyzer
        self.champion_analyzer = champion_analyzer
        self.data_dragon = data_dragon
        self.stats_analyzer = stats_analyzer
        self.riot_api = riot_api
        self.matches = matches
        if matches:
            self.live_analyzer = LiveGameAnalyzer(matches, champion_analyzer)

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

    def _champion_icon_label(self, champion_name: str, size: int = 32) -> QLabel:
        """Create a QLabel with a champion icon."""
        label = QLabel()
        label.setFixedSize(size, size)
        label.setStyleSheet("border: none; background: transparent;")

        if self.data_dragon and champion_name:
            icon_path = self.data_dragon.get_champion_icon_path(champion_name)
            if icon_path:
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    label.setPixmap(pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                                                  Qt.TransformationMode.SmoothTransformation))
                    return label

        label.setText("?")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(f"border: 1px solid {COLORS['border']}; border-radius: 4px; "
                            f"color: {COLORS['text_dim']}; background: {COLORS['bg_main']};")
        return label

    def _rank_color(self, tier: str) -> str:
        """Get color for a rank tier."""
        return RANK_COLORS.get(tier.upper(), COLORS['text_dim']) if tier else COLORS['text_dim']

    # ---- Polling ----

    def _poll_lcu(self):
        try:
            connected = self.lcu.connect()
        except Exception:
            connected = False

        if not connected:
            self._lcu_connected = False
            if self._current_phase != 'disconnected':
                self._current_phase = 'disconnected'
                self.status_label.setText("League Client not detected")
                self.status_label.setStyleSheet(f"color: {COLORS['red']}; font-size: 16px; font-weight: bold; border: none;")
                self.status_detail.setText("Start League of Legends to enable live features")
                self._clear_content()
                self._cancel_scouting()
            return

        self._lcu_connected = True

        # Use gameflow phase for more granular detection
        phase = self.lcu.get_gameflow_phase()

        if phase == 'ChampSelect':
            if self._current_phase != 'ChampSelect':
                self._current_phase = 'ChampSelect'
                self._cancel_scouting()
                self._scouting_results = {}
            self.status_label.setText("In Champion Select!")
            self.status_label.setStyleSheet(f"color: {COLORS['green']}; font-size: 16px; font-weight: bold; border: none;")
            self.status_detail.setText("Live data from champion select")
            self._show_champ_select()

        elif phase == 'InProgress':
            if self._current_phase != 'InProgress':
                self._current_phase = 'InProgress'
                self._start_in_game_scouting()
            self.status_label.setText("Game In Progress!")
            self.status_label.setStyleSheet(f"color: {COLORS['orange']}; font-size: 16px; font-weight: bold; border: none;")
            self.status_detail.setText("Live game data")
            self._show_in_game()

        else:
            if self._current_phase not in (None, 'idle'):
                self._cancel_scouting()
                self._scouting_results = {}
                self._last_game_id = None
            self._current_phase = 'idle'
            self.status_label.setText("League Client connected")
            self.status_label.setStyleSheet(f"color: {COLORS['blue']}; font-size: 16px; font-weight: bold; border: none;")
            self.status_detail.setText("Waiting for champion select...")
            self._clear_content()
            self._show_idle_suggestions()

    # ---- Scouting ----

    def _cancel_scouting(self):
        if self._scouting_worker and self._scouting_worker.isRunning():
            self._scouting_worker.cancel()
            self._scouting_worker = None

    def _start_in_game_scouting(self):
        """Start background scouting when game begins."""
        if not self.riot_api:
            return

        game_data = self.lcu.get_active_game_data()
        if not game_data:
            return

        game_id = game_data.get('game_id')
        if game_id == self._last_game_id:
            return  # Already scouted this game

        self._last_game_id = game_id
        self._scouting_results = {}

        # Collect all players
        all_players = game_data.get('team_one', []) + game_data.get('team_two', [])
        players_to_scout = [p for p in all_players if p.get('puuid')]

        if not players_to_scout:
            return

        self._cancel_scouting()
        self._scouting_worker = ScoutingWorker(self.riot_api, players_to_scout)
        self._scouting_worker.player_ready.connect(self._on_player_scouted)
        self._scouting_worker.finished.connect(self._on_scouting_finished)
        self._scouting_worker.start()

    def _on_player_scouted(self, puuid: str, rank_data: dict):
        self._scouting_results[puuid] = rank_data
        # Refresh in-game view to show progressively loaded data
        if self._current_phase == 'InProgress':
            self._show_in_game()

    def _on_scouting_finished(self, results: dict):
        self._scouting_results = results

    # ---- Champion Select View ----

    def _show_champ_select(self):
        self._clear_content()

        session = self.lcu.get_champ_select_info()
        if not session:
            return

        my_team = session.get('my_team', [])
        their_team = session.get('their_team', [])
        bans = session.get('bans', [])

        # Get champion names for analysis
        my_team_names = []
        enemy_team_names = []

        for player in my_team:
            champ_id = player.get('championId', 0)
            if champ_id and self.data_dragon:
                my_team_names.append(self.data_dragon.get_champion_name(champ_id))

        for player in their_team:
            champ_id = player.get('championId', 0)
            if champ_id and self.data_dragon:
                enemy_team_names.append(self.data_dragon.get_champion_name(champ_id))

        # ---- Teams Card ----
        self._show_teams_card(my_team, their_team)

        # ---- Bans Card ----
        if bans:
            self._show_bans_card(bans)

        # ---- Your Champion Stats ----
        local_cell = session.get('local_player_cell_id')
        my_champ_name = None
        my_role = None
        for player in my_team:
            if player.get('cellId') == local_cell:
                champ_id = player.get('championId', 0)
                if champ_id and self.data_dragon:
                    my_champ_name = self.data_dragon.get_champion_name(champ_id)
                my_role = player.get('assignedPosition', '').upper()
                break

        if my_champ_name and self.live_analyzer:
            self._show_my_champion_stats(my_champ_name, my_role)

        # ---- Enemy Matchup History ----
        if enemy_team_names and self.live_analyzer:
            self._show_enemy_matchups(enemy_team_names)

        # ---- Ban Suggestions ----
        if self.live_analyzer:
            self._show_ban_suggestions()

        # ---- Counter-pick Suggestions ----
        if enemy_team_names and self.live_analyzer and not my_champ_name:
            self._show_counter_picks(enemy_team_names, my_role)

        # ---- Draft Analysis ----
        if my_team_names:
            self._show_draft_analysis(my_team_names)

        # ---- Role Tips ----
        if my_champ_name and self.live_analyzer:
            tips = self.live_analyzer.get_role_tips(my_champ_name, my_role)
            if tips:
                card, layout = self._card("Tips for This Game")
                for tip in tips:
                    tip_label = QLabel(f"  {tip}")
                    tip_label.setStyleSheet(f"color: {COLORS['text']}; border: none; font-size: 12px;")
                    tip_label.setWordWrap(True)
                    layout.addWidget(tip_label)
                self.content_area.addWidget(card)

        # ---- Challenge Tips ----
        self._show_game_plan_tips()

    def _show_teams_card(self, my_team: list, their_team: list):
        """Show both teams with champion icons."""
        card, layout = self._card("Champion Select")

        # Your team
        if my_team:
            team_header = QLabel("Your Team")
            team_header.setStyleSheet(f"color: {COLORS['blue']}; font-weight: bold; font-size: 14px; border: none;")
            layout.addWidget(team_header)

            for player in my_team:
                row = QHBoxLayout()
                row.setSpacing(8)

                champ_id = player.get('championId', 0)
                champ_name = ""
                if champ_id and self.data_dragon:
                    champ_name = self.data_dragon.get_champion_name(champ_id)
                    row.addWidget(self._champion_icon_label(champ_name, 28))
                    name_label = QLabel(champ_name)
                    name_label.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold; border: none;")
                else:
                    row.addWidget(self._champion_icon_label("", 28))
                    name_label = QLabel("Picking...")
                    name_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-style: italic; border: none;")

                name_label.setFixedWidth(120)
                row.addWidget(name_label)

                # Role
                role = player.get('assignedPosition', '')
                if role:
                    role_label = QLabel(self._format_role(role))
                    role_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
                    role_label.setFixedWidth(70)
                    row.addWidget(role_label)

                # Personal stats on this champ
                if champ_name and self.live_analyzer:
                    stats = self.live_analyzer.get_personal_champion_stats(champ_name)
                    if stats:
                        stat_text = f"{stats['winrate']}% WR ({stats['games']}G)"
                        stat_label = QLabel(stat_text)
                        wr_color = COLORS['green'] if stats['winrate'] >= 50 else COLORS['red']
                        stat_label.setStyleSheet(f"color: {wr_color}; font-size: 11px; border: none;")
                        row.addWidget(stat_label)

                row.addStretch()
                layout.addLayout(row)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {COLORS['border']}; border: none;")
        layout.addWidget(sep)

        # Enemy team
        if their_team:
            enemy_header = QLabel("Enemy Team")
            enemy_header.setStyleSheet(f"color: {COLORS['red']}; font-weight: bold; font-size: 14px; border: none;")
            layout.addWidget(enemy_header)

            for player in their_team:
                row = QHBoxLayout()
                row.setSpacing(8)

                champ_id = player.get('championId', 0)
                champ_name = ""
                if champ_id and self.data_dragon:
                    champ_name = self.data_dragon.get_champion_name(champ_id)
                    row.addWidget(self._champion_icon_label(champ_name, 28))
                    name_label = QLabel(champ_name)
                    name_label.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold; border: none;")
                else:
                    row.addWidget(self._champion_icon_label("", 28))
                    name_label = QLabel("Picking...")
                    name_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-style: italic; border: none;")

                name_label.setFixedWidth(120)
                row.addWidget(name_label)

                # Matchup vs this enemy
                if champ_name and self.live_analyzer:
                    matchup = self.live_analyzer.get_matchup_vs(champ_name)
                    if matchup['games'] > 0:
                        m_text = f"{matchup['wins']}W-{matchup['losses']}L ({matchup['winrate']}%)"
                        m_label = QLabel(m_text)
                        m_color = COLORS['green'] if matchup['winrate'] >= 50 else COLORS['red']
                        m_label.setStyleSheet(f"color: {m_color}; font-size: 11px; border: none;")
                        row.addWidget(m_label)

                row.addStretch()
                layout.addLayout(row)

        self.content_area.addWidget(card)

    def _show_bans_card(self, bans: list):
        """Show banned champions."""
        card, layout = self._card("Bans")
        row = QHBoxLayout()
        row.setSpacing(12)

        ally_bans = [b for b in bans if b.get('is_ally')]
        enemy_bans = [b for b in bans if not b.get('is_ally')]

        # Ally bans
        for ban in ally_bans:
            champ_id = ban.get('champion_id', 0)
            if champ_id and self.data_dragon:
                name = self.data_dragon.get_champion_name(champ_id)
                icon = self._champion_icon_label(name, 24)
                row.addWidget(icon)

        if ally_bans and enemy_bans:
            sep = QLabel("|")
            sep.setStyleSheet(f"color: {COLORS['text_dim']}; border: none; font-size: 16px;")
            row.addWidget(sep)

        # Enemy bans
        for ban in enemy_bans:
            champ_id = ban.get('champion_id', 0)
            if champ_id and self.data_dragon:
                name = self.data_dragon.get_champion_name(champ_id)
                icon = self._champion_icon_label(name, 24)
                row.addWidget(icon)

        row.addStretch()
        layout.addLayout(row)
        self.content_area.addWidget(card)

    def _show_my_champion_stats(self, champ_name: str, role: str = None):
        """Show your personal stats on your selected champion."""
        stats = self.live_analyzer.get_personal_champion_stats(champ_name)
        if not stats:
            card, layout = self._card(f"Your {champ_name}")
            first_time = QLabel(f"First time playing {champ_name} in ranked!")
            first_time.setStyleSheet(f"color: {COLORS['orange']}; font-weight: bold; border: none;")
            layout.addWidget(first_time)
            self.content_area.addWidget(card)
            return

        card, layout = self._card(f"Your {champ_name}")

        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(24)

        wr_color = COLORS['green'] if stats['winrate'] >= 50 else COLORS['red']

        for label, value, color in [
            ("Win Rate", f"{stats['winrate']}%", wr_color),
            ("Games", str(stats['games']), COLORS['text']),
            ("KDA", f"{stats['avg_kills']}/{stats['avg_deaths']}/{stats['avg_assists']}", COLORS['text']),
            ("CS/min", str(stats['avg_cs_per_min']), COLORS['text']),
            ("Damage", f"{int(stats['avg_damage']):,}", COLORS['text']),
        ]:
            stat_widget = QVBoxLayout()
            val_label = QLabel(value)
            val_label.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold; border: none;")
            val_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_widget.addWidget(val_label)

            desc_label = QLabel(label)
            desc_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; border: none;")
            desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_widget.addWidget(desc_label)

            stats_row.addLayout(stat_widget)

        stats_row.addStretch()
        layout.addLayout(stats_row)
        self.content_area.addWidget(card)

    def _show_enemy_matchups(self, enemy_names: list[str]):
        """Show your WR against each visible enemy champion."""
        if not self.live_analyzer:
            return

        matchups_with_data = []
        for name in enemy_names:
            m = self.live_analyzer.get_matchup_vs(name)
            if m['games'] > 0:
                matchups_with_data.append(m)

        if not matchups_with_data:
            return

        card, layout = self._card("Your Matchup History")

        for m in matchups_with_data:
            row = QHBoxLayout()
            row.setSpacing(8)

            row.addWidget(self._champion_icon_label(m['enemy_champion'], 24))

            name_label = QLabel(m['enemy_champion'])
            name_label.setFixedWidth(100)
            name_label.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold; border: none;")
            row.addWidget(name_label)

            record = QLabel(f"{m['wins']}W - {m['losses']}L")
            record.setFixedWidth(80)
            record.setStyleSheet(f"color: {COLORS['text']}; border: none;")
            row.addWidget(record)

            wr_color = COLORS['green'] if m['winrate'] >= 50 else COLORS['red']
            wr_label = QLabel(f"{m['winrate']}%")
            wr_label.setStyleSheet(f"color: {wr_color}; font-weight: bold; border: none;")
            row.addWidget(wr_label)

            row.addStretch()
            layout.addLayout(row)

        self.content_area.addWidget(card)

    def _show_ban_suggestions(self):
        """Show suggested bans based on personal matchup data."""
        bans = self.live_analyzer.suggest_bans(top_n=5)
        if not bans:
            return

        card, layout = self._card("Suggested Bans")

        for ban in bans:
            row = QHBoxLayout()
            row.setSpacing(8)

            row.addWidget(self._champion_icon_label(ban['champion'], 24))

            name_label = QLabel(ban['champion'])
            name_label.setFixedWidth(100)
            name_label.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold; border: none;")
            row.addWidget(name_label)

            reason = QLabel(ban['reason'])
            reason.setStyleSheet(f"color: {COLORS['red']}; font-size: 11px; border: none;")
            row.addWidget(reason)

            row.addStretch()
            layout.addLayout(row)

        self.content_area.addWidget(card)

    def _show_counter_picks(self, enemy_names: list[str], my_role: str = None):
        """Show your champions that do well against visible enemies."""
        suggestions = self.live_analyzer.suggest_counter_picks(enemy_names, my_role)
        if not suggestions:
            return

        card, layout = self._card("Counter-Pick Suggestions")

        for s in suggestions:
            row = QHBoxLayout()
            row.setSpacing(8)

            row.addWidget(self._champion_icon_label(s['champion'], 24))

            name_label = QLabel(s['champion'])
            name_label.setFixedWidth(100)
            name_label.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold; border: none;")
            row.addWidget(name_label)

            overall = QLabel(f"Overall: {s['overall_winrate']}% ({s['overall_games']}G)")
            overall.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
            overall.setFixedWidth(150)
            row.addWidget(overall)

            vs_color = COLORS['green'] if s['vs_winrate'] >= 50 else COLORS['text']
            vs_label = QLabel(f"vs these: {s['vs_winrate']}% ({s['vs_games']}G)")
            vs_label.setStyleSheet(f"color: {vs_color}; font-size: 11px; border: none;")
            row.addWidget(vs_label)

            row.addStretch()
            layout.addLayout(row)

        self.content_area.addWidget(card)

    # ---- In-Game View ----

    def _show_in_game(self):
        self._clear_content()

        game_data = self.lcu.get_active_game_data()
        if not game_data:
            # Fallback: show whatever we have
            self._show_game_plan_tips()
            return

        team_one = game_data.get('team_one', [])
        team_two = game_data.get('team_two', [])

        # Determine which team is ours
        my_puuid = None
        if self.matches:
            # Get our puuid from match data
            first_match = self.matches[0] if self.matches else None
            if first_match:
                my_puuid = first_match.get('match_id', '').split('_')[0]  # fallback

        # Try to find ourselves from LCU
        current_summoner = self.lcu.get_current_summoner()
        if current_summoner:
            my_puuid = current_summoner.get('puuid', '')

        my_team = team_one
        enemy_team = team_two
        if my_puuid:
            for p in team_two:
                if p.get('puuid') == my_puuid:
                    my_team = team_two
                    enemy_team = team_one
                    break

        # ---- Win Prediction ----
        if self._scouting_results:
            self._show_win_prediction(my_team, enemy_team)

        # ---- Teams ----
        self._show_in_game_team("Your Team", my_team, COLORS['blue'])
        self._show_in_game_team("Enemy Team", enemy_team, COLORS['red'])

        # ---- Lane Matchup ----
        if my_puuid:
            self._show_lane_matchup(my_team, enemy_team, my_puuid)

        # ---- Personal Champion Stats ----
        if my_puuid and self.live_analyzer:
            for p in my_team:
                if p.get('puuid') == my_puuid:
                    champ_id = p.get('champion_id', 0)
                    if champ_id and self.data_dragon:
                        champ_name = self.data_dragon.get_champion_name(champ_id)
                        role = p.get('selected_position', '').upper()
                        self._show_my_champion_stats(champ_name, role)

                        # Tips
                        tips = self.live_analyzer.get_role_tips(champ_name, role)
                        if tips:
                            tip_card, tip_layout = self._card("Tips for This Game")
                            for tip in tips:
                                tip_label = QLabel(f"  {tip}")
                                tip_label.setStyleSheet(f"color: {COLORS['text']}; border: none; font-size: 12px;")
                                tip_label.setWordWrap(True)
                                tip_layout.addWidget(tip_label)
                            self.content_area.addWidget(tip_card)
                    break

        # ---- Challenge Tips ----
        self._show_game_plan_tips()

    def _show_win_prediction(self, my_team: list, enemy_team: list):
        """Show win prediction based on team ranks."""
        team_ranks = []
        enemy_ranks = []

        for p in my_team:
            puuid = p.get('puuid', '')
            if puuid in self._scouting_results:
                team_ranks.append(self._scouting_results[puuid])

        for p in enemy_team:
            puuid = p.get('puuid', '')
            if puuid in self._scouting_results:
                enemy_ranks.append(self._scouting_results[puuid])

        if not team_ranks or not enemy_ranks:
            return

        prediction = self.live_analyzer.predict_win(team_ranks, enemy_ranks)

        card, layout = self._card("Win Prediction")

        win_pct = prediction['win_percentage']
        pct_color = COLORS['green'] if win_pct >= 50 else COLORS['red']

        pct_label = QLabel(f"{win_pct}%")
        pct_label.setStyleSheet(f"color: {pct_color}; font-size: 28px; font-weight: bold; border: none;")
        pct_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(pct_label)

        # Progress bar
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(int(win_pct))
        bar.setTextVisible(False)
        bar.setFixedHeight(12)
        bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['red']};
                border: none;
                border-radius: 6px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['blue']};
                border-radius: 6px;
            }}
        """)
        layout.addWidget(bar)

        detail = QLabel(f"Based on team rank averages (Your team avg rank diff: {prediction['rank_diff']:+.1f})")
        detail.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; border: none;")
        detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(detail)

        self.content_area.addWidget(card)

    def _show_in_game_team(self, title: str, team: list, color: str):
        """Show a team's players with icons, names, roles, and ranks."""
        card, layout = self._card(title)

        for player in team:
            row = QHBoxLayout()
            row.setSpacing(8)

            champ_id = player.get('champion_id', 0)
            champ_name = ""
            if champ_id and self.data_dragon:
                champ_name = self.data_dragon.get_champion_name(champ_id)

            # Champion icon
            row.addWidget(self._champion_icon_label(champ_name, 32))

            # Champion name
            name_label = QLabel(champ_name or "Unknown")
            name_label.setFixedWidth(100)
            name_label.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold; border: none;")
            row.addWidget(name_label)

            # Summoner name
            summoner = player.get('summoner_name', '')
            sum_label = QLabel(summoner)
            sum_label.setFixedWidth(120)
            sum_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
            row.addWidget(sum_label)

            # Role
            role = player.get('selected_position', '')
            if role:
                role_label = QLabel(self._format_role(role))
                role_label.setFixedWidth(60)
                role_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
                row.addWidget(role_label)

            # Rank (from scouting)
            puuid = player.get('puuid', '')
            if puuid in self._scouting_results:
                rank_data = self._scouting_results[puuid]
                tier = rank_data.get('tier', '')
                rank = rank_data.get('rank', '')
                rank_display = LiveGameAnalyzer.rank_to_display(tier, rank, rank_data.get('lp', 0))
                rank_label = QLabel(rank_display)
                rank_label.setStyleSheet(
                    f"color: {self._rank_color(tier)}; font-weight: bold; font-size: 11px; border: none;"
                )
                rank_label.setFixedWidth(100)
                row.addWidget(rank_label)

                # WR
                wr = rank_data.get('winrate', 0)
                total = rank_data.get('total_games', 0)
                if total > 0:
                    wr_color = COLORS['green'] if wr >= 50 else COLORS['red']
                    wr_label = QLabel(f"{wr}% ({total}G)")
                    wr_label.setStyleSheet(f"color: {wr_color}; font-size: 11px; border: none;")
                    row.addWidget(wr_label)
            else:
                loading_label = QLabel("Loading...")
                loading_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; font-style: italic; border: none;")
                row.addWidget(loading_label)

            row.addStretch()
            layout.addLayout(row)

        self.content_area.addWidget(card)

    def _show_lane_matchup(self, my_team: list, enemy_team: list, my_puuid: str):
        """Show lane matchup between you and your lane opponent."""
        if not self.live_analyzer or not self.data_dragon:
            return

        # Find my champion and role
        my_champ_name = None
        my_role = None
        for p in my_team:
            if p.get('puuid') == my_puuid:
                champ_id = p.get('champion_id', 0)
                if champ_id:
                    my_champ_name = self.data_dragon.get_champion_name(champ_id)
                my_role = p.get('selected_position', '')
                break

        if not my_champ_name or not my_role:
            return

        # Find lane opponent
        enemy_champ_name = None
        for p in enemy_team:
            if p.get('selected_position', '') == my_role:
                champ_id = p.get('champion_id', 0)
                if champ_id:
                    enemy_champ_name = self.data_dragon.get_champion_name(champ_id)
                break

        if not enemy_champ_name:
            return

        matchup = self.live_analyzer.get_lane_matchup_vs(enemy_champ_name, my_role)

        card, layout = self._card("Lane Matchup")

        # Head to head display
        vs_row = QHBoxLayout()
        vs_row.setSpacing(16)
        vs_row.addStretch()

        # My champion
        my_col = QVBoxLayout()
        my_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        my_col.addWidget(self._champion_icon_label(my_champ_name, 48))
        my_name = QLabel(my_champ_name)
        my_name.setStyleSheet(f"color: {COLORS['blue']}; font-weight: bold; border: none;")
        my_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        my_col.addWidget(my_name)
        vs_row.addLayout(my_col)

        # VS
        vs_label = QLabel("VS")
        vs_label.setStyleSheet(f"color: {COLORS['gold']}; font-size: 20px; font-weight: bold; border: none;")
        vs_row.addWidget(vs_label)

        # Enemy champion
        enemy_col = QVBoxLayout()
        enemy_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        enemy_col.addWidget(self._champion_icon_label(enemy_champ_name, 48))
        enemy_name = QLabel(enemy_champ_name)
        enemy_name.setStyleSheet(f"color: {COLORS['red']}; font-weight: bold; border: none;")
        enemy_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        enemy_col.addWidget(enemy_name)
        vs_row.addLayout(enemy_col)

        vs_row.addStretch()
        layout.addLayout(vs_row)

        # Matchup record
        if matchup['games'] > 0:
            record = QLabel(
                f"Your record vs {enemy_champ_name}: {matchup['wins']}W - {matchup['losses']}L ({matchup['winrate']}%)"
            )
            wr_color = COLORS['green'] if matchup['winrate'] >= 50 else COLORS['red']
            record.setStyleSheet(f"color: {wr_color}; border: none;")
            record.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(record)
        else:
            no_data = QLabel(f"No lane matchup data vs {enemy_champ_name}")
            no_data.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
            no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_data)

        self.content_area.addWidget(card)

    # ---- Idle View ----

    def _show_idle_suggestions(self):
        """Show champion suggestions when not in champ select."""
        if not self.challenge_analyzer:
            return

        card, layout = self._card("Suggested Champions for Next Game")

        recs = self.challenge_analyzer.champion_recommendations()[:5]
        for r in recs:
            row = QHBoxLayout()
            row.setSpacing(8)

            # Champion icon
            row.addWidget(self._champion_icon_label(r['champion'], 28))

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

        # Ban suggestions
        if self.live_analyzer:
            self._show_ban_suggestions()

        # Always show in-game tips
        self._show_game_plan_tips()

    # ---- Shared Components ----

    def _show_draft_analysis(self, team_names: list[str]):
        analysis = self.draft_helper.analyze_team(team_names)
        if not analysis:
            return

        card, layout = self._card("Draft Analysis")

        # AD/AP balance bar
        ad = analysis['ad_count']
        ap = analysis['ap_count']
        mixed = analysis['mixed_count']
        total = ad + ap + mixed

        if total > 0:
            bar_row = QHBoxLayout()
            bar_row.setSpacing(4)

            ad_bar = QProgressBar()
            ad_bar.setRange(0, total)
            ad_bar.setValue(ad)
            ad_bar.setFormat(f"AD: {ad}")
            ad_bar.setFixedHeight(20)
            ad_bar.setStyleSheet(f"""
                QProgressBar {{ background-color: {COLORS['bg_main']}; border: 1px solid {COLORS['border']}; border-radius: 4px; color: {COLORS['text']}; font-size: 10px; }}
                QProgressBar::chunk {{ background-color: {COLORS['red']}; border-radius: 3px; }}
            """)
            bar_row.addWidget(ad_bar)

            ap_bar = QProgressBar()
            ap_bar.setRange(0, total)
            ap_bar.setValue(ap)
            ap_bar.setFormat(f"AP: {ap}")
            ap_bar.setFixedHeight(20)
            ap_bar.setStyleSheet(f"""
                QProgressBar {{ background-color: {COLORS['bg_main']}; border: 1px solid {COLORS['border']}; border-radius: 4px; color: {COLORS['text']}; font-size: 10px; }}
                QProgressBar::chunk {{ background-color: {COLORS['purple']}; border-radius: 3px; }}
            """)
            bar_row.addWidget(ap_bar)

            layout.addLayout(bar_row)

        balance_label = QLabel(
            f"Damage: {analysis['damage_balance']}  "
            f"(AD: {ad}  AP: {ap}  Mixed: {mixed})  |  "
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

    @staticmethod
    def _format_role(role: str) -> str:
        """Format role string for display."""
        role_map = {
            'TOP': 'Top',
            'JUNGLE': 'Jungle',
            'MIDDLE': 'Mid',
            'BOTTOM': 'Bot',
            'UTILITY': 'Support',
            'top': 'Top',
            'jungle': 'Jungle',
            'middle': 'Mid',
            'bottom': 'Bot',
            'utility': 'Support',
        }
        return role_map.get(role, role.capitalize() if role else '')

    def stop_polling(self):
        self._cancel_scouting()
        self.poll_timer.stop()
