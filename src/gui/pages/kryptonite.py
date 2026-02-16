"""Kryptonite page: enemy matchup analysis, ban suggestions, frequent opponents."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from src.analytics.kryptonite import KryptoniteAnalyzer
from src.analytics.rival_tracker import RivalTracker
from src.gui.theme import COLORS


class KryptonitePage(QWidget):
    def __init__(self):
        super().__init__()
        self.data_dragon = None
        self.kryptonite = None
        self.rival_tracker = None
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        self.layout_main = QVBoxLayout(container)
        self.layout_main.setSpacing(16)
        self.layout_main.setContentsMargins(24, 24, 24, 24)

        # Title
        title = QLabel("Kryptonite - Enemy Matchup Analysis")
        title.setStyleSheet(f"color: {COLORS['gold']}; font-size: 22px; font-weight: bold;")
        self.layout_main.addWidget(title)

        subtitle = QLabel("Your win rates against enemy champions and ban suggestions based on your match history")
        subtitle.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px;")
        self.layout_main.addWidget(subtitle)

        # Content area
        self.content_area = QVBoxLayout()
        self.layout_main.addLayout(self.content_area)

        # Placeholder
        self.placeholder = QLabel("Load your data from Settings to see matchup analysis")
        self.placeholder.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 14px;")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_area.addWidget(self.placeholder)

        self.layout_main.addStretch()

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def update_data(self, matches: list, data_dragon=None):
        self.data_dragon = data_dragon
        self.kryptonite = KryptoniteAnalyzer(matches, min_games=2)
        self.rival_tracker = RivalTracker(matches)
        self._populate()

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

    def _champion_icon(self, champion_name: str, size: int = 24) -> QLabel:
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

    def _populate(self):
        self._clear_content()

        if not self.kryptonite:
            return

        # ---- Suggested Bans ----
        bans = self.kryptonite.suggested_bans(count=5)
        if bans:
            card, layout = self._card("Suggested Bans")
            desc = QLabel("Based on champions you lose to most frequently")
            desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
            layout.addWidget(desc)

            for i, ban in enumerate(bans, 1):
                row = QHBoxLayout()
                row.setSpacing(8)

                rank_label = QLabel(f"#{i}")
                rank_label.setFixedWidth(24)
                rank_label.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; border: none;")
                row.addWidget(rank_label)

                row.addWidget(self._champion_icon(ban['enemy_champion'], 28))

                name = QLabel(ban['enemy_champion'])
                name.setFixedWidth(110)
                name.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold; border: none;")
                row.addWidget(name)

                record = QLabel(f"{ban['wins']}W - {ban['losses']}L")
                record.setFixedWidth(70)
                record.setStyleSheet(f"color: {COLORS['text']}; border: none;")
                row.addWidget(record)

                wr_color = COLORS['green'] if ban['winrate'] >= 50 else COLORS['red']
                wr = QLabel(f"{ban['winrate']}%")
                wr.setFixedWidth(50)
                wr.setStyleSheet(f"color: {wr_color}; font-weight: bold; border: none;")
                row.addWidget(wr)

                priority = QLabel(f"Priority: {ban['ban_priority']}")
                priority.setStyleSheet(f"color: {COLORS['orange']}; font-size: 11px; border: none;")
                row.addWidget(priority)

                row.addStretch()
                layout.addLayout(row)

            self.content_area.addWidget(card)

        # ---- Worst Matchups ----
        worst = self.kryptonite.worst_matchups(count=10)
        if worst:
            card, layout = self._card("Worst Matchups")
            self._matchup_table(layout, worst)
            self.content_area.addWidget(card)

        # ---- Best Matchups ----
        best = self.kryptonite.best_matchups(count=10)
        if best:
            card, layout = self._card("Best Matchups")
            self._matchup_table(layout, best)
            self.content_area.addWidget(card)

        # ---- Per-Role Breakdown ----
        by_role = self.kryptonite.matchups_by_role()
        if by_role:
            card, layout = self._card("Matchups by Role")

            role_order = ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'SUPPORT']
            for role in role_order:
                if role not in by_role:
                    continue

                matchups = by_role[role]
                if not matchups:
                    continue

                role_header = QLabel(role.capitalize())
                role_header.setStyleSheet(f"color: {COLORS['blue']}; font-weight: bold; font-size: 13px; border: none;")
                layout.addWidget(role_header)

                # Show top 5 worst for this role
                filtered = [m for m in matchups if m['games'] >= 2]
                filtered.sort(key=lambda x: x['winrate'])
                for m in filtered[:5]:
                    row = QHBoxLayout()
                    row.setSpacing(8)

                    row.addWidget(self._champion_icon(m['enemy_champion'], 22))

                    name = QLabel(m['enemy_champion'])
                    name.setFixedWidth(110)
                    name.setStyleSheet(f"color: {COLORS['text']}; border: none;")
                    row.addWidget(name)

                    record = QLabel(f"{m['wins']}W-{m['losses']}L")
                    record.setFixedWidth(60)
                    record.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
                    row.addWidget(record)

                    wr_color = COLORS['green'] if m['winrate'] >= 50 else COLORS['red']
                    wr = QLabel(f"{m['winrate']}%")
                    wr.setStyleSheet(f"color: {wr_color}; font-weight: bold; border: none;")
                    row.addWidget(wr)

                    row.addStretch()
                    layout.addLayout(row)

            self.content_area.addWidget(card)

        # ---- Frequent Enemy Champions ----
        if self.rival_tracker:
            freq_champs = self.rival_tracker.frequent_enemy_champions(min_games=3)
            if freq_champs:
                card, layout = self._card("Most Faced Enemy Champions")

                for champ in freq_champs[:15]:
                    row = QHBoxLayout()
                    row.setSpacing(8)

                    row.addWidget(self._champion_icon(champ['champion'], 24))

                    name = QLabel(champ['champion'])
                    name.setFixedWidth(110)
                    name.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold; border: none;")
                    row.addWidget(name)

                    games = QLabel(f"{champ['games']} games")
                    games.setFixedWidth(70)
                    games.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
                    row.addWidget(games)

                    record = QLabel(f"{champ['wins']}W-{champ['losses']}L")
                    record.setFixedWidth(60)
                    record.setStyleSheet(f"color: {COLORS['text']}; border: none;")
                    row.addWidget(record)

                    wr_color = COLORS['green'] if champ['winrate'] >= 50 else COLORS['red']
                    wr = QLabel(f"{champ['winrate']}%")
                    wr.setStyleSheet(f"color: {wr_color}; font-weight: bold; border: none;")
                    row.addWidget(wr)

                    row.addStretch()
                    layout.addLayout(row)

                self.content_area.addWidget(card)

            # Frequent enemy players (requires PUUIDs)
            freq_players = self.rival_tracker.frequent_enemy_players(min_games=2)
            if freq_players:
                card, layout = self._card("Recurring Opponents")
                desc = QLabel("Players you've faced multiple times")
                desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
                layout.addWidget(desc)

                for player in freq_players[:10]:
                    row = QHBoxLayout()
                    row.setSpacing(8)

                    if player.get('most_played'):
                        row.addWidget(self._champion_icon(player['most_played'], 24))

                    name_text = player['summoner_name']
                    if player['tag_line']:
                        name_text += f"#{player['tag_line']}"
                    name = QLabel(name_text)
                    name.setFixedWidth(180)
                    name.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold; border: none;")
                    row.addWidget(name)

                    games = QLabel(f"{player['games']} games")
                    games.setFixedWidth(70)
                    games.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
                    row.addWidget(games)

                    record = QLabel(f"{player['wins']}W-{player['losses']}L")
                    record.setFixedWidth(60)
                    record.setStyleSheet(f"color: {COLORS['text']}; border: none;")
                    row.addWidget(record)

                    wr_color = COLORS['green'] if player['winrate'] >= 50 else COLORS['red']
                    wr = QLabel(f"{player['winrate']}%")
                    wr.setFixedWidth(50)
                    wr.setStyleSheet(f"color: {wr_color}; font-weight: bold; border: none;")
                    row.addWidget(wr)

                    most = QLabel(f"Most played: {player['most_played']}")
                    most.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
                    row.addWidget(most)

                    row.addStretch()
                    layout.addLayout(row)

                self.content_area.addWidget(card)
            else:
                card, layout = self._card("Recurring Opponents")
                hint = QLabel("No recurring opponents found. Do a full refresh in Settings "
                              "to update match data with opponent info.")
                hint.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none;")
                hint.setWordWrap(True)
                layout.addWidget(hint)
                self.content_area.addWidget(card)

    def _matchup_table(self, layout: QVBoxLayout, matchups: list[dict]):
        """Add matchup rows to a card layout."""
        for m in matchups:
            row = QHBoxLayout()
            row.setSpacing(8)

            row.addWidget(self._champion_icon(m['enemy_champion'], 24))

            name = QLabel(m['enemy_champion'])
            name.setFixedWidth(110)
            name.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold; border: none;")
            row.addWidget(name)

            games = QLabel(f"{m['games']} games")
            games.setFixedWidth(70)
            games.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
            row.addWidget(games)

            record = QLabel(f"{m['wins']}W - {m['losses']}L")
            record.setFixedWidth(80)
            record.setStyleSheet(f"color: {COLORS['text']}; border: none;")
            row.addWidget(record)

            wr_color = COLORS['green'] if m['winrate'] >= 50 else COLORS['red']
            wr = QLabel(f"{m['winrate']}%")
            wr.setStyleSheet(f"color: {wr_color}; font-weight: bold; border: none;")
            row.addWidget(wr)

            row.addStretch()
            layout.addLayout(row)
