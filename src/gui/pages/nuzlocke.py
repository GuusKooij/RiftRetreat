"""Nuzlocke page: Manual champion elimination challenge mode tracker."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QGridLayout, QMessageBox,
    QLineEdit, QComboBox, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QPixmap, QIcon

import random

from src.gui.theme import COLORS
from src.analytics.nuzlocke import NuzlockeTracker


class NuzlockePage(QWidget):
    def __init__(self):
        super().__init__()
        self.tracker = NuzlockeTracker()
        self.matches = []
        self.dd = None
        self.selected_champion = None  # Currently selected champ name
        self.floating_panel = None  # Floating action panel for quick win/loss
        self.champion_widgets = {}  # Map champion name -> widget for animations
        self._setup_ui()

    def _setup_ui(self):
        self.scroll_area = QScrollArea()  # Store reference for scroll position management
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        self.layout_main = QVBoxLayout(container)
        self.layout_main.setSpacing(16)
        self.layout_main.setContentsMargins(24, 24, 24, 24)

        self.scroll_area.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Sticky header for quick actions (WIN/LOSS buttons)
        self.sticky_header = QFrame()
        self.sticky_header.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_dark']};
                border-bottom: 2px solid {COLORS['border']};
                padding: 12px 24px;
            }}
        """)
        self.sticky_header_layout = QHBoxLayout(self.sticky_header)
        self.sticky_header_layout.setContentsMargins(12, 8, 12, 8)
        self.sticky_header_layout.setSpacing(12)

        # Initially hidden until champion selected
        self.sticky_header.setVisible(False)

        outer.addWidget(self.sticky_header)
        outer.addWidget(self.scroll_area)

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

    def update_data(self, matches: list[dict], data_dragon=None):
        self.matches = matches
        if data_dragon:
            self.dd = data_dragon
        self._refresh_ui()

    def _refresh_ui(self):
        while self.layout_main.count():
            child = self.layout_main.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self._add_explanation()
        self._add_controls()

        active = self.tracker.get_active_run()
        if active:
            self._active_run = active  # Store for streak/MVP lookups
            stats = self.tracker.get_run_stats(active)
            self._add_active_run(stats)
            self._add_champion_grid(stats)
            self._add_graveyard_visual(stats)
            self._add_all_games(stats)

        # Past runs
        all_runs = self.tracker.get_all_runs()
        past = [r for r in all_runs if not r['active']]
        if past:
            self._add_past_runs(past)

        self.layout_main.addStretch()

    def _add_explanation(self):
        card, layout = self._card("LoL Nuzlocke Challenge")

        rules = QLabel(
            "Rules:\n"
            "- Start a new run to begin tracking\n"
            "- Click a champion, then click Win or Loss to record the result\n"
            "- WIN = champion survives (you keep them)\n"
            "- LOSE = champion is ELIMINATED (can't play them again)\n"
            "- Goal: survive as long as possible!\n\n"
            "Streaks:\n"
            "- Every 5 consecutive wins: earn a bonus Resurrection Token!\n"
            "- Every 5 consecutive losses: a random alive champion is eliminated!\n"
            "- Streaks stack (10, 15, 20...) so stay hot and avoid cold streaks!\n\n"
            "Penalties:\n"
            "- Playing an eliminated champion: a random alive champion is eliminated!\n"
            "  (This breaks win streaks but does NOT add to loss streaks)\n\n"
            "Tokens:\n"
            "- Earn 1 Resurrection Token every 10 wins + bonus tokens from win streaks\n"
            "- Use tokens to resurrect a random eliminated champion (gambling wheel)\n\n"
            "Ending a run is PERMANENT -- it cannot be restarted."
        )
        rules.setStyleSheet(f"color: {COLORS['text']}; font-size: 13px; border: none;")
        rules.setWordWrap(True)
        layout.addWidget(rules)

        self.layout_main.addWidget(card)

    def _add_controls(self):
        card, layout = self._card("Controls")

        btn_layout = QHBoxLayout()
        active = self.tracker.get_active_run()

        if not active:
            start_btn = QPushButton("Start New Nuzlocke Run")
            start_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['green']};
                    color: white;
                    font-weight: bold;
                    padding: 10px 24px;
                    border-radius: 6px;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: #00E676;
                }}
            """)
            start_btn.clicked.connect(self._start_run)
            btn_layout.addWidget(start_btn)
        else:
            # Record buttons
            self.win_btn = QPushButton("Record WIN")
            self.win_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['green']};
                    color: white;
                    font-weight: bold;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-size: 13px;
                }}
                QPushButton:hover {{ background-color: #00E676; }}
                QPushButton:disabled {{ background-color: {COLORS['border']}; color: {COLORS['text_dim']}; }}
            """)
            self.win_btn.setEnabled(False)
            self.win_btn.clicked.connect(lambda: self._record_result(True))
            btn_layout.addWidget(self.win_btn)

            self.loss_btn = QPushButton("Record LOSS")
            self.loss_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['red']};
                    color: white;
                    font-weight: bold;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-size: 13px;
                }}
                QPushButton:hover {{ background-color: #FF1744; }}
                QPushButton:disabled {{ background-color: {COLORS['border']}; color: {COLORS['text_dim']}; }}
            """)
            self.loss_btn.setEnabled(False)
            self.loss_btn.clicked.connect(lambda: self._record_result(False))
            btn_layout.addWidget(self.loss_btn)

            self.selected_label = QLabel("Select a champion below")
            self.selected_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-style: italic; border: none;")
            btn_layout.addWidget(self.selected_label)

            btn_layout.addStretch()

            # Resurrection button (gambling wheel)
            stats = self.tracker.get_run_stats(active)
            if stats.get('tokens_remaining', 0) > 0 and stats.get('eliminated'):
                resurrect_btn = QPushButton(f"🎰 Resurrection Wheel ({stats['tokens_remaining']} tokens)")
                resurrect_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['purple']};
                        color: white;
                        font-weight: bold;
                        padding: 10px 20px;
                        border-radius: 6px;
                        font-size: 13px;
                    }}
                    QPushButton:hover {{ background-color: #9C27B0; }}
                """)
                resurrect_btn.clicked.connect(self._spin_resurrection_wheel)
                btn_layout.addWidget(resurrect_btn)

            # Played eliminated champion penalty button
            if stats.get('eliminated') and stats.get('survived'):
                played_elim_btn = QPushButton("⚠️ Played Eliminated Champ")
                played_elim_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['orange']};
                        color: white;
                        font-weight: bold;
                        padding: 10px 20px;
                        border-radius: 6px;
                        font-size: 13px;
                    }}
                    QPushButton:hover {{ background-color: #FFA726; }}
                """)
                played_elim_btn.clicked.connect(self._played_eliminated_champion)
                btn_layout.addWidget(played_elim_btn)

            # Export buttons
            export_html_btn = QPushButton("📄 Export HTML")
            export_html_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['blue']};
                    color: white;
                    padding: 10px 16px;
                    border-radius: 6px;
                    font-size: 12px;
                }}
                QPushButton:hover {{ background-color: #1976D2; }}
            """)
            export_html_btn.clicked.connect(self._export_html)
            btn_layout.addWidget(export_html_btn)

            end_btn = QPushButton("End Run")
            end_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['border']};
                    color: {COLORS['text']};
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-size: 12px;
                }}
                QPushButton:hover {{ background-color: {COLORS['red']}; color: white; }}
            """)
            end_btn.clicked.connect(self._end_run)
            btn_layout.addWidget(end_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.layout_main.addWidget(card)

    def _add_active_run(self, stats):
        started = stats['started'][:10]
        card, layout = self._card(f"Active Run #{stats['id']} (Started: {started})")

        wr = round(stats['total_wins'] / max(stats['total_games'], 1) * 100)
        wr_color = COLORS['green'] if wr >= 50 else COLORS['red']

        stats_layout = QHBoxLayout()
        stats_items = [
            ('Games Played', str(stats['total_games']), COLORS['blue']),
            ('Wins', str(stats['total_wins']), COLORS['green']),
            ('Win Rate', f"{wr}%", wr_color),
            ('Survived', str(stats['survived_count']), COLORS['gold']),
            ('Eliminated', str(stats['eliminated_count']), COLORS['red']),
        ]

        # Add tokens (earned every 10 wins)
        if 'tokens_remaining' in stats:
            tokens_color = COLORS['purple'] if stats['tokens_remaining'] > 0 else COLORS['text_dim']
            next_token_wins = 10 - (stats['total_wins'] % 10)
            tokens_label = f"Tokens ({next_token_wins} wins to next)"
            stats_items.append((tokens_label, str(stats['tokens_remaining']), tokens_color))

        for label, value, color in stats_items:
            w = QWidget()
            l = QVBoxLayout(w)
            l.setContentsMargins(0, 0, 0, 0)
            l.setSpacing(2)
            val = QLabel(value)
            val.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color};")
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(val)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"font-size: 11px; color: {COLORS['text_dim']};")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(lbl)
            stats_layout.addWidget(w)

        layout.addLayout(stats_layout)

        # Streak notification bar
        active_run = getattr(self, '_active_run', None)
        streak = self.tracker.get_current_streak(active_run)
        if streak['count'] > 0:
            streak_frame = QFrame()
            streak_frame.setStyleSheet(f"border: none;")
            streak_layout = QHBoxLayout(streak_frame)
            streak_layout.setContentsMargins(0, 4, 0, 4)

            if streak['type'] == 'win':
                next_milestone = 5 - (streak['count'] % 5)
                if next_milestone == 5 and streak['count'] % 5 == 0:
                    streak_text = f"🔥 {streak['count']} consecutive wins — STREAK BONUS earned!"
                else:
                    streak_text = f"🔥 {streak['count']} consecutive wins — {next_milestone} more for bonus token!"
                streak_color = COLORS['green']
            else:
                next_milestone = 5 - (streak['count'] % 5)
                if next_milestone == 5 and streak['count'] % 5 == 0:
                    streak_text = f"⚠️ {streak['count']} consecutive losses — random champion eliminated!"
                else:
                    streak_text = f"⚠️ {streak['count']} consecutive losses — {next_milestone} more until random champion dies!"
                streak_color = COLORS['red']

            streak_label = QLabel(streak_text)
            streak_label.setStyleSheet(f"color: {streak_color}; font-weight: bold; font-size: 13px; border: none;")
            streak_layout.addWidget(streak_label)
            streak_layout.addStretch()
            layout.addWidget(streak_frame)

        # MVP champion
        mvp = self.tracker.get_mvp_champion(active_run)
        if mvp and mvp['streak'] >= 2:
            mvp_frame = QFrame()
            mvp_frame.setStyleSheet(f"border: none;")
            mvp_layout = QHBoxLayout(mvp_frame)
            mvp_layout.setContentsMargins(0, 4, 0, 4)

            mvp_text = f"👑 MVP: {mvp['champion']} ({mvp['streak']} game win streak, {mvp['wins']}W / {mvp['losses']}L)"
            mvp_label = QLabel(mvp_text)
            mvp_label.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; font-size: 13px; border: none;")
            mvp_layout.addWidget(mvp_label)
            mvp_layout.addStretch()
            layout.addWidget(mvp_frame)

        # Resurrection history
        if stats.get('resurrections'):
            res_label = QLabel("🎰 Resurrection History:")
            res_label.setStyleSheet(f"color: {COLORS['purple']}; font-weight: bold; margin-top: 12px; border: none;")
            layout.addWidget(res_label)

            for res in stats['resurrections']:
                was_random = res.get('was_random', False)
                prefix = "🎲" if was_random else "💜"
                res_row = QLabel(f"  {prefix} {res['champion']} - {res['date']}")
                res_row.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none;")
                layout.addWidget(res_row)

        # Recent history (last 5 games)
        if stats['history']:
            history_label = QLabel("Recent Games (Last 5):")
            history_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-weight: bold; margin-top: 8px; border: none;")
            layout.addWidget(history_label)

            for h in reversed(stats['history'][-5:]):
                row = QHBoxLayout()

                result = QLabel("W" if h['win'] else "X")
                result.setFixedWidth(24)
                color = COLORS['green'] if h['win'] else COLORS['red']
                result.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px; border: none;")
                row.addWidget(result)

                icon = QLabel()
                icon.setFixedSize(20, 20)
                if self.dd:
                    icon_path = self.dd.get_champion_icon_path(h['champion'])
                    if icon_path:
                        px = QPixmap(icon_path)
                        if not px.isNull():
                            icon.setPixmap(px.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                row.addWidget(icon)

                champ = QLabel(h['champion'])
                champ.setFixedWidth(120)
                champ.setStyleSheet(f"font-weight: bold; border: none;")
                row.addWidget(champ)

                status = QLabel("SURVIVED" if h['win'] else "ELIMINATED")
                status.setStyleSheet(f"color: {color}; font-size: 11px; border: none;")
                row.addWidget(status)

                date = QLabel(h.get('date', ''))
                date.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
                row.addWidget(date)

                row.addStretch()
                layout.addLayout(row)

        self.layout_main.addWidget(card)

    def _add_champion_grid(self, stats):
        """Show ALL champions in a grid. Click to select, then Win/Loss to record."""
        if not self.dd:
            return

        all_champs = self.dd.get_champion_list()
        if not all_champs:
            return

        survived = set(stats.get('survived', []))
        eliminated = set(stats.get('eliminated', []))

        champ_wins = {}
        for h in stats.get('history', []):
            name = h['champion']
            if name not in champ_wins:
                champ_wins[name] = {'wins': 0, 'games': 0}
            champ_wins[name]['games'] += 1
            if h['win']:
                champ_wins[name]['wins'] += 1

        # Store for filtering
        self._grid_all_champs = all_champs
        self._grid_survived = survived
        self._grid_eliminated = eliminated
        self._grid_champ_wins = champ_wins
        self._grid_stats = stats

        card, layout = self._card(
            f"Champion Roster -- Click to select, then Win/Loss above "
            f"({len(survived)} alive / {len(eliminated)} eliminated / "
            f"{len(all_champs) - len(survived) - len(eliminated)} unplayed)"
        )

        # Filter row
        filter_row = QHBoxLayout()

        search = QLineEdit()
        search.setPlaceholderText("Search champion...")
        search.setFixedWidth(180)
        search.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                color: {COLORS['text']};
                padding: 4px 8px;
                font-size: 12px;
            }}
        """)
        self._grid_search = search
        filter_row.addWidget(search)

        role_filter = QComboBox()
        role_filter.addItems(["All Roles", "Top", "Jungle", "Mid", "Bot", "Support"])
        role_filter.setFixedWidth(120)
        role_filter.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                color: {COLORS['text']};
                padding: 4px 8px;
                font-size: 12px;
            }}
        """)
        self._grid_role_filter = role_filter
        filter_row.addWidget(role_filter)

        status_filter = QComboBox()
        status_filter.addItems(["All", "Alive", "Eliminated", "Unplayed"])
        status_filter.setFixedWidth(120)
        status_filter.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                color: {COLORS['text']};
                padding: 4px 8px;
                font-size: 12px;
            }}
        """)
        self._grid_status_filter = status_filter
        filter_row.addWidget(status_filter)

        filter_row.addStretch()
        layout.addLayout(filter_row)

        # Grid container (replaced on filter)
        self._grid_container = QWidget()
        self._grid_container_layout = QVBoxLayout(self._grid_container)
        self._grid_container_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._grid_container)

        # Connect filters
        search.textChanged.connect(lambda: self._rebuild_grid())
        role_filter.currentIndexChanged.connect(lambda: self._rebuild_grid())
        status_filter.currentIndexChanged.connect(lambda: self._rebuild_grid())

        self._rebuild_grid()

        self.layout_main.addWidget(card)

    # Roles each champion can be played in (broad/lenient for Nuzlocke)
    # Every champion lists all roles where they can reasonably be picked,
    # even off-meta — in a Nuzlocke you play whatever you have available.
    CHAMP_ROLES = {
        'Aatrox': ['Top', 'Mid', 'Jungle'], 'Ahri': ['Mid', 'Support'],
        'Akali': ['Mid', 'Top'], 'Akshan': ['Mid', 'Top', 'Bot'],
        'Alistar': ['Support', 'Top', 'Jungle'], 'Ambessa': ['Top', 'Jungle', 'Mid'],
        'Amumu': ['Jungle', 'Support', 'Top'], 'Anivia': ['Mid', 'Support'],
        'Annie': ['Mid', 'Support'], 'Aphelios': ['Bot'],
        'Ashe': ['Bot', 'Support'], 'Aurelion Sol': ['Mid'],
        'Aurora': ['Mid', 'Top', 'Jungle'], 'Azir': ['Mid'],
        'Bard': ['Support'], "Bel'Veth": ['Jungle', 'Top'],
        'Blitzcrank': ['Support', 'Jungle'], 'Brand': ['Support', 'Mid', 'Jungle'],
        'Braum': ['Support'], 'Briar': ['Jungle', 'Top'],
        'Caitlyn': ['Bot', 'Mid'], 'Camille': ['Top', 'Jungle', 'Mid'],
        'Cassiopeia': ['Mid', 'Top', 'Bot'], "Cho'Gath": ['Top', 'Jungle', 'Mid'],
        'Corki': ['Mid', 'Bot'], 'Darius': ['Top', 'Jungle'],
        'Diana': ['Jungle', 'Mid', 'Top'], 'Dr. Mundo': ['Top', 'Jungle'],
        'Draven': ['Bot', 'Mid'], 'Ekko': ['Jungle', 'Mid', 'Top'],
        'Elise': ['Jungle', 'Support'], 'Evelynn': ['Jungle', 'Mid'],
        'Ezreal': ['Bot', 'Mid'], 'Fiddlesticks': ['Jungle', 'Support', 'Mid'],
        'Fiora': ['Top', 'Mid'], 'Fizz': ['Mid', 'Jungle', 'Top'],
        'Galio': ['Mid', 'Support', 'Top'], 'Gangplank': ['Top', 'Mid'],
        'Garen': ['Top', 'Mid'], 'Gnar': ['Top'],
        'Gragas': ['Jungle', 'Top', 'Mid', 'Support'],
        'Graves': ['Jungle', 'Top', 'Mid'], 'Gwen': ['Top', 'Jungle'],
        'Hecarim': ['Jungle', 'Top'], 'Heimerdinger': ['Mid', 'Bot', 'Support', 'Top'],
        'Hwei': ['Mid', 'Support', 'Bot'], 'Illaoi': ['Top'],
        'Irelia': ['Top', 'Mid'], 'Ivern': ['Jungle', 'Support'],
        'Janna': ['Support', 'Mid'], 'Jarvan IV': ['Jungle', 'Top', 'Mid', 'Support'],
        'Jax': ['Top', 'Jungle', 'Mid'], 'Jayce': ['Top', 'Mid'],
        'Jhin': ['Bot', 'Mid'], 'Jinx': ['Bot'],
        "Kai'Sa": ['Bot', 'Mid'], 'Kalista': ['Bot', 'Top'],
        'Karma': ['Support', 'Mid', 'Top'], 'Karthus': ['Jungle', 'Mid', 'Bot'],
        'Kassadin': ['Mid', 'Top'], 'Katarina': ['Mid', 'Bot'],
        'Kayle': ['Top', 'Mid', 'Bot'], 'Kayn': ['Jungle', 'Top', 'Mid'],
        'Kennen': ['Top', 'Mid', 'Bot'], "Kha'Zix": ['Jungle', 'Mid'],
        'Kindred': ['Jungle', 'Bot'], 'Kled': ['Top', 'Jungle'],
        "Kog'Maw": ['Bot', 'Mid'], "K'Sante": ['Top'],
        'LeBlanc': ['Mid', 'Support'], 'Lee Sin': ['Jungle', 'Top', 'Mid'],
        'Leona': ['Support', 'Jungle'], 'Lillia': ['Jungle', 'Top', 'Mid'],
        'Lissandra': ['Mid', 'Top', 'Support'], 'Lucian': ['Bot', 'Mid', 'Top'],
        'Lulu': ['Support', 'Mid'], 'Lux': ['Support', 'Mid', 'Bot'],
        'Malphite': ['Top', 'Support', 'Jungle', 'Mid'],
        'Malzahar': ['Mid', 'Support'], 'Maokai': ['Jungle', 'Support', 'Top'],
        'Master Yi': ['Jungle', 'Mid'], 'Mel': ['Mid', 'Support'],
        'Milio': ['Support'], 'Miss Fortune': ['Bot', 'Support', 'Mid'],
        'Mordekaiser': ['Top', 'Jungle', 'Mid', 'Bot'],
        'Morgana': ['Support', 'Jungle', 'Mid'],
        'Naafiri': ['Mid', 'Jungle', 'Top'], 'Nami': ['Support'],
        'Nasus': ['Top', 'Jungle'], 'Nautilus': ['Support', 'Top', 'Jungle'],
        'Neeko': ['Mid', 'Support', 'Top', 'Bot', 'Jungle'],
        'Nidalee': ['Jungle', 'Mid', 'Support'], 'Nilah': ['Bot'],
        'Nocturne': ['Jungle', 'Top', 'Mid'], 'Nunu & Willump': ['Jungle', 'Mid'],
        'Olaf': ['Top', 'Jungle'], 'Orianna': ['Mid', 'Support'],
        'Ornn': ['Top', 'Support'],
        'Pantheon': ['Top', 'Support', 'Mid', 'Jungle'],
        'Poppy': ['Jungle', 'Top', 'Support'], 'Pyke': ['Support', 'Mid'],
        'Qiyana': ['Mid', 'Jungle'], 'Quinn': ['Top', 'Mid', 'Bot'],
        'Rakan': ['Support', 'Mid'], 'Rammus': ['Jungle', 'Top'],
        "Rek'Sai": ['Jungle', 'Top'], 'Rell': ['Support', 'Jungle'],
        'Renata Glasc': ['Support'], 'Renekton': ['Top', 'Mid'],
        'Rengar': ['Jungle', 'Top'], 'Riven': ['Top', 'Mid'],
        'Rumble': ['Top', 'Jungle', 'Mid'], 'Ryze': ['Mid', 'Top'],
        'Samira': ['Bot', 'Mid', 'Jungle'], 'Sejuani': ['Jungle', 'Top', 'Support'],
        'Senna': ['Support', 'Bot', 'Top'], 'Seraphine': ['Support', 'Mid', 'Bot'],
        'Sett': ['Top', 'Support', 'Jungle', 'Mid'],
        'Shaco': ['Jungle', 'Support'], 'Shen': ['Top', 'Support', 'Jungle'],
        'Shyvana': ['Jungle', 'Top'], 'Singed': ['Top', 'Jungle', 'Support'],
        'Sion': ['Top', 'Support', 'Jungle', 'Mid'],
        'Sivir': ['Bot', 'Mid'], 'Skarner': ['Jungle', 'Top'],
        'Smolder': ['Bot', 'Mid', 'Top'], 'Sona': ['Support', 'Bot'],
        'Soraka': ['Support', 'Top', 'Mid'], 'Swain': ['Support', 'Mid', 'Bot', 'Top'],
        'Sylas': ['Mid', 'Jungle', 'Top'], 'Syndra': ['Mid', 'Support'],
        'Tahm Kench': ['Top', 'Support'], 'Taliyah': ['Mid', 'Jungle', 'Support'],
        'Talon': ['Mid', 'Jungle'], 'Taric': ['Support', 'Top'],
        'Teemo': ['Top', 'Support', 'Jungle', 'Mid'],
        'Thresh': ['Support'], 'Tristana': ['Bot', 'Mid', 'Top'],
        'Trundle': ['Top', 'Jungle', 'Support'], 'Tryndamere': ['Top', 'Mid'],
        'Twisted Fate': ['Mid', 'Bot', 'Support'], 'Twitch': ['Bot', 'Support', 'Jungle'],
        'Udyr': ['Jungle', 'Top'], 'Urgot': ['Top', 'Mid'],
        'Varus': ['Bot', 'Mid'], 'Vayne': ['Bot', 'Top'],
        'Veigar': ['Mid', 'Bot', 'Support'],
        "Vel'Koz": ['Mid', 'Support'], 'Vex': ['Mid', 'Support'],
        'Vi': ['Jungle', 'Top'], 'Viego': ['Jungle', 'Top', 'Mid'],
        'Viktor': ['Mid', 'Top'], 'Vladimir': ['Mid', 'Top'],
        'Volibear': ['Top', 'Jungle'], 'Warwick': ['Jungle', 'Top'],
        'Wukong': ['Top', 'Jungle', 'Mid'], 'Xayah': ['Bot'],
        'Xerath': ['Mid', 'Support'], 'Xin Zhao': ['Jungle', 'Top'],
        'Yasuo': ['Mid', 'Top', 'Bot'], 'Yone': ['Mid', 'Top'],
        'Yorick': ['Top', 'Jungle'], 'Yuumi': ['Support'],
        'Zac': ['Jungle', 'Top', 'Support'], 'Zed': ['Mid', 'Jungle'],
        'Zeri': ['Bot', 'Mid'], 'Ziggs': ['Mid', 'Bot', 'Support'],
        'Zilean': ['Support', 'Mid'], 'Zoe': ['Mid', 'Support'],
        'Zyra': ['Support', 'Mid', 'Jungle'],
    }

    def _get_champion_roles(self, name: str, tags: list[str]) -> list[str]:
        """Get all viable roles for a champion. Uses curated mapping, falls back to tags.

        Broad/lenient — for Nuzlocke context where you play whatever's available.
        """
        roles = self.CHAMP_ROLES.get(name)
        if roles:
            return roles
        # Fallback: assign broadly based on tags
        fallback = set()
        if 'Marksman' in tags:
            fallback.update(['Bot', 'Mid'])
        if 'Support' in tags:
            fallback.add('Support')
        if 'Assassin' in tags:
            fallback.update(['Mid', 'Jungle'])
        if 'Fighter' in tags:
            fallback.update(['Top', 'Jungle'])
        if 'Tank' in tags:
            fallback.update(['Top', 'Jungle', 'Support'])
        if 'Mage' in tags:
            fallback.update(['Mid', 'Support'])
        return list(fallback) or ['Top', 'Mid', 'Bot', 'Jungle', 'Support']

    def _rebuild_grid(self):
        """Rebuild champion grid with current filters applied."""
        # Clear existing grid
        while self._grid_container_layout.count():
            child = self._grid_container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        search_text = self._grid_search.text().lower().strip()
        role_text = self._grid_role_filter.currentText()
        status_text = self._grid_status_filter.currentText()

        survived = self._grid_survived
        eliminated = self._grid_eliminated
        champ_wins = self._grid_champ_wins

        # Filter champions
        filtered = []
        for champ in self._grid_all_champs:
            name = champ['name']

            # Search filter
            if search_text and search_text not in name.lower():
                continue

            # Role filter
            if role_text != "All Roles":
                champ_roles = self._get_champion_roles(name, champ.get('tags', []))
                if role_text not in champ_roles:
                    continue

            # Status filter
            if status_text == "Alive" and name in eliminated:
                continue
            elif status_text == "Eliminated" and name not in eliminated:
                continue
            elif status_text == "Unplayed" and (name in survived or name in eliminated):
                continue

            filtered.append(champ)

        grid = QGridLayout()
        grid.setSpacing(4)
        cols = 10

        # Get MVP and streak info for indicators
        active_run = getattr(self, '_active_run', None)
        mvp = self.tracker.get_mvp_champion(active_run) if active_run else None
        mvp_name = mvp['champion'] if mvp and mvp['streak'] >= 2 else None

        # Track which champions are currently on a win streak (consecutive recent wins)
        champ_on_streak = set()
        if active_run:
            streak_info = self.tracker.get_current_streak(active_run)
            if streak_info['type'] == 'win' and streak_info['count'] >= 2:
                # The last N games were all wins — find which champs are in that streak
                for h in reversed(active_run.get('history', [])):
                    if h['win']:
                        champ_on_streak.add(h['champion'])
                    else:
                        break

        for i, champ in enumerate(filtered):
            name = champ['name']
            row_idx = i // cols
            col_idx = i % cols

            is_eliminated = name in eliminated

            # Container widget with icon on top, name below
            cell = QWidget()
            cell.setFixedSize(80, 80)
            cell_layout = QVBoxLayout(cell)
            cell_layout.setContentsMargins(2, 2, 2, 2)
            cell_layout.setSpacing(1)

            if name in survived:
                bg = '#1B5E20'
                border = COLORS['green']
                text_color = 'white'
            elif is_eliminated:
                bg = '#B71C1C'
                border = COLORS['red']
                text_color = '#FF8A80'
            else:
                bg = COLORS['bg_dark']
                border = COLORS['border']
                text_color = COLORS['text_dim']

            selected_border = ""
            if name == self.selected_champion:
                border = COLORS['gold']
                selected_border = "border-width: 2px;"

            cell.setStyleSheet(f"""
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 4px;
                {selected_border}
            """)

            # Indicator (crown for MVP, flame for streak)
            indicator = ""
            if name == mvp_name:
                indicator = "👑"
            elif name in champ_on_streak and name in survived:
                indicator = "🔥"

            # Icon
            icon = QLabel()
            icon.setFixedSize(40, 40)
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon.setStyleSheet("border: none;")
            if self.dd:
                icon_path = self.dd.get_champion_icon_path(name)
                if icon_path:
                    px = QPixmap(icon_path)
                    if not px.isNull():
                        icon.setPixmap(px.scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            cell_layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)

            # Name + stats + indicator
            win_data = champ_wins.get(name)
            if win_data:
                label_text = f"{indicator}{name}\n{win_data['wins']}W/{win_data['games']}G"
            else:
                label_text = f"{indicator}{name}" if indicator else name

            name_lbl = QLabel(label_text)
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_lbl.setStyleSheet(f"color: {text_color}; font-size: 8px; font-weight: bold; border: none;")
            cell_layout.addWidget(name_lbl)

            # Make clickable
            if not is_eliminated:
                cell.setCursor(Qt.CursorShape.PointingHandCursor)
                cell.mousePressEvent = lambda event, n=name: self._select_champion(n)
            else:
                cell.setEnabled(False)

            # Store reference for animations
            self.champion_widgets[name] = cell

            grid.addWidget(cell, row_idx, col_idx)

        grid_widget = QWidget()
        grid_widget.setLayout(grid)
        self._grid_container_layout.addWidget(grid_widget)

    def _add_past_runs(self, runs):
        card, layout = self._card(f"Past Runs ({len(runs)})")

        for r in reversed(runs):
            # Expandable run container
            run_frame = QFrame()
            run_frame.setStyleSheet(f"""
                QFrame#run_container {{
                    background-color: {COLORS['bg_dark']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 4px;
                }}
            """)
            run_frame.setObjectName("run_container")
            run_layout = QVBoxLayout(run_frame)
            run_layout.setContentsMargins(0, 0, 0, 0)
            run_layout.setSpacing(0)

            # Header (clickable)
            header = QWidget()
            header.setCursor(Qt.CursorShape.PointingHandCursor)
            header_layout = QHBoxLayout(header)
            header_layout.setContentsMargins(12, 8, 12, 8)

            run_label = QLabel(f"Run #{r['id']}")
            run_label.setFixedWidth(60)
            run_label.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; border: none;")
            header_layout.addWidget(run_label)

            started = r.get('started', '')[:10]
            ended = r.get('ended', '')[:10] if r.get('ended') else '?'
            dates = QLabel(f"{started} -- {ended}")
            dates.setFixedWidth(180)
            dates.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
            header_layout.addWidget(dates)

            games = QLabel(f"{r['total_games']}G")
            games.setFixedWidth(40)
            games.setStyleSheet(f"color: {COLORS['blue']}; border: none;")
            header_layout.addWidget(games)

            wins = QLabel(f"{r['total_wins']}W")
            wins.setFixedWidth(40)
            wins.setStyleSheet(f"color: {COLORS['green']}; border: none;")
            header_layout.addWidget(wins)

            past_wr = round(r['total_wins'] / max(r['total_games'], 1) * 100)
            past_wr_color = COLORS['green'] if past_wr >= 50 else COLORS['red']
            wr_lbl = QLabel(f"{past_wr}% WR")
            wr_lbl.setFixedWidth(60)
            wr_lbl.setStyleSheet(f"color: {past_wr_color}; font-weight: bold; border: none;")
            header_layout.addWidget(wr_lbl)

            survived_lbl = QLabel(f"{r['survived_count']} survived")
            survived_lbl.setFixedWidth(100)
            survived_lbl.setStyleSheet(f"color: {COLORS['text']}; border: none;")
            header_layout.addWidget(survived_lbl)

            eliminated_lbl = QLabel(f"{r['eliminated_count']} eliminated")
            eliminated_lbl.setFixedWidth(100)
            eliminated_lbl.setStyleSheet(f"color: {COLORS['red']}; border: none;")
            header_layout.addWidget(eliminated_lbl)

            expand_icon = QLabel("+")
            expand_icon.setFixedWidth(16)
            expand_icon.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 14px; font-weight: bold; border: none;")
            header_layout.addWidget(expand_icon)

            header_layout.addStretch()

            # Delete button
            del_btn = QPushButton("Delete")
            del_btn.setFixedWidth(60)
            del_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLORS['red']};
                    font-size: 11px;
                    border: 1px solid {COLORS['red']};
                    border-radius: 3px;
                    padding: 2px 8px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['red']};
                    color: white;
                }}
            """)
            del_btn.clicked.connect(lambda checked, rid=r['id']: self._delete_run(rid))
            header_layout.addWidget(del_btn)

            run_layout.addWidget(header)

            # Detail panel (hidden by default)
            detail = QFrame()
            detail.setVisible(False)
            detail.setStyleSheet(f"border-top: 1px solid {COLORS['border']};")
            detail_layout = QVBoxLayout(detail)
            detail_layout.setContentsMargins(16, 12, 16, 12)
            detail_layout.setSpacing(8)

            self._build_past_run_detail(detail_layout, r)

            run_layout.addWidget(detail)

            def toggle(event, d=detail, icon=expand_icon):
                d.setVisible(not d.isVisible())
                icon.setText("-" if d.isVisible() else "+")

            header.mousePressEvent = toggle

            layout.addWidget(run_frame)

        self.layout_main.addWidget(card)

    def _build_past_run_detail(self, layout, run_stats):
        """Build expanded detail for a past run."""
        # Best champions
        best = run_stats.get('best_champs', [])
        if best:
            best_label = QLabel("Top Champions:")
            best_label.setStyleSheet(f"color: {COLORS['green']}; font-weight: bold; font-size: 12px; border: none;")
            layout.addWidget(best_label)

            for champ_name, data in best:
                row = QHBoxLayout()

                icon = QLabel()
                icon.setFixedSize(20, 20)
                if self.dd:
                    icon_path = self.dd.get_champion_icon_path(champ_name)
                    if icon_path:
                        px = QPixmap(icon_path)
                        if not px.isNull():
                            icon.setPixmap(px.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                icon.setStyleSheet("border: none;")
                row.addWidget(icon)

                name = QLabel(champ_name)
                name.setFixedWidth(120)
                name.setStyleSheet(f"font-weight: bold; border: none;")
                row.addWidget(name)

                wr = round(data['wins'] / max(data['games'], 1) * 100)
                wr_color = COLORS['green'] if wr >= 50 else COLORS['red']
                stats_lbl = QLabel(f"{data['wins']}W {data['losses']}L ({wr}% WR)")
                stats_lbl.setStyleSheet(f"color: {wr_color}; font-size: 11px; border: none;")
                row.addWidget(stats_lbl)

                row.addStretch()
                layout.addLayout(row)

        # Eliminated champions list
        eliminated = run_stats.get('eliminated', [])
        if eliminated:
            elim_label = QLabel(f"Eliminated ({len(eliminated)}):")
            elim_label.setStyleSheet(f"color: {COLORS['red']}; font-weight: bold; font-size: 12px; margin-top: 4px; border: none;")
            layout.addWidget(elim_label)

            # Find elimination dates from history
            elim_dates = {}
            for h in run_stats.get('history', []):
                if not h['win']:
                    elim_dates[h['champion']] = h.get('date', '')

            elim_grid = QGridLayout()
            elim_grid.setSpacing(4)
            for i, champ in enumerate(eliminated):
                col = i % 5
                row_idx = i // 5
                date = elim_dates.get(champ, '')
                lbl = QLabel(f"{champ} ({date})")
                lbl.setStyleSheet(f"color: {COLORS['red']}; font-size: 10px; border: none;")
                elim_grid.addWidget(lbl, row_idx, col)
            layout.addLayout(elim_grid)

        # Survived champions list
        survived = run_stats.get('survived', [])
        if survived:
            surv_label = QLabel(f"Survived ({len(survived)}):")
            surv_label.setStyleSheet(f"color: {COLORS['green']}; font-weight: bold; font-size: 12px; margin-top: 4px; border: none;")
            layout.addWidget(surv_label)

            surv_grid = QGridLayout()
            surv_grid.setSpacing(4)
            for i, champ in enumerate(survived):
                col = i % 5
                row_idx = i // 5
                lbl = QLabel(champ)
                lbl.setStyleSheet(f"color: {COLORS['green']}; font-size: 10px; border: none;")
                surv_grid.addWidget(lbl, row_idx, col)
            layout.addLayout(surv_grid)

        # Full game history
        history = run_stats.get('history', [])
        if history:
            hist_label = QLabel(f"Full History ({len(history)} games):")
            hist_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-weight: bold; font-size: 12px; margin-top: 4px; border: none;")
            layout.addWidget(hist_label)

            for h in reversed(history[-20:]):
                row = QHBoxLayout()
                result = QLabel("W" if h['win'] else "X")
                result.setFixedWidth(16)
                color = COLORS['green'] if h['win'] else COLORS['red']
                result.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 11px; border: none;")
                row.addWidget(result)

                champ = QLabel(h['champion'])
                champ.setFixedWidth(120)
                champ.setStyleSheet(f"font-size: 11px; border: none;")
                row.addWidget(champ)

                status = QLabel("survived" if h['win'] else "ELIMINATED")
                status.setStyleSheet(f"color: {color}; font-size: 10px; border: none;")
                row.addWidget(status)

                date = QLabel(h.get('date', ''))
                date.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; border: none;")
                row.addWidget(date)

                row.addStretch()
                layout.addLayout(row)

        # Export buttons for past runs
        export_row = QHBoxLayout()
        export_row.addStretch()

        export_html_btn = QPushButton("📄 Export HTML")
        export_html_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['blue']};
                color: white;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 11px;
            }}
            QPushButton:hover {{ background-color: #1976D2; }}
        """)
        export_html_btn.clicked.connect(lambda: self._export_past_run_html(run_stats))
        export_row.addWidget(export_html_btn)

        layout.addLayout(export_row)

    def _select_champion(self, champion_name: str):
        self.selected_champion = champion_name

        # Clear and populate sticky header
        while self.sticky_header_layout.count():
            child = self.sticky_header_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Champion icon
        icon_label = QLabel()
        icon_label.setFixedSize(52, 52)
        icon_label.setStyleSheet(f"""
            border: 2px solid {COLORS['gold']};
            border-radius: 6px;
            background-color: {COLORS['bg_dark']};
            padding: 2px;
        """)
        if self.dd:
            icon_path = self.dd.get_champion_icon_path(champion_name)
            if icon_path:
                px = QPixmap(icon_path)
                if not px.isNull():
                    scaled_px = px.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    icon_label.setPixmap(scaled_px)
                    icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sticky_header_layout.addWidget(icon_label)

        # Champion name
        name_label = QLabel(f"Selected: {champion_name}")
        name_label.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; font-size: 16px;")
        self.sticky_header_layout.addWidget(name_label)

        self.sticky_header_layout.addStretch()

        # WIN button
        win_btn = QPushButton(f"✓ WIN")
        win_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['green']};
                color: white;
                font-weight: bold;
                padding: 12px 32px;
                border-radius: 6px;
                font-size: 15px;
                border: 2px solid {COLORS['gold']};
            }}
            QPushButton:hover {{ background-color: #00E676; }}
        """)
        win_btn.clicked.connect(lambda: self._record_result_sticky(True))
        self.sticky_header_layout.addWidget(win_btn)

        # LOSS button
        loss_btn = QPushButton(f"✗ LOSS")
        loss_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['red']};
                color: white;
                font-weight: bold;
                padding: 12px 32px;
                border-radius: 6px;
                font-size: 15px;
                border: 2px solid {COLORS['gold']};
            }}
            QPushButton:hover {{ background-color: #FF1744; }}
        """)
        loss_btn.clicked.connect(lambda: self._record_result_sticky(False))
        self.sticky_header_layout.addWidget(loss_btn)

        # Cancel button
        cancel_btn = QPushButton("✕")
        cancel_btn.setFixedSize(40, 40)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_dim']};
                font-weight: bold;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['border']};
                color: {COLORS['text']};
            }}
        """)
        cancel_btn.clicked.connect(self._deselect_champion)
        self.sticky_header_layout.addWidget(cancel_btn)

        # Show sticky header
        self.sticky_header.setVisible(True)

        # Also update the in-page selected label and buttons if they exist
        if hasattr(self, 'selected_label'):
            self.selected_label.setText(f"Selected: {champion_name}")
            self.selected_label.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; font-size: 14px; border: none;")
        if hasattr(self, 'win_btn'):
            self.win_btn.setEnabled(True)
            self.win_btn.setText(f"✓ WIN - {champion_name}")
            self.win_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['green']};
                    color: white;
                    font-weight: bold;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-size: 14px;
                    border: 2px solid {COLORS['gold']};
                }}
                QPushButton:hover {{ background-color: #00E676; }}
            """)
        if hasattr(self, 'loss_btn'):
            self.loss_btn.setEnabled(True)
            self.loss_btn.setText(f"✗ LOSS - {champion_name}")
            self.loss_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['red']};
                    color: white;
                    font-weight: bold;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-size: 14px;
                    border: 2px solid {COLORS['gold']};
                }}
                QPushButton:hover {{ background-color: #FF1744; }}
            """)

    def _deselect_champion(self):
        """Clear champion selection and hide sticky header."""
        self.selected_champion = None
        self.sticky_header.setVisible(False)
        # Reset in-page buttons if they exist
        if hasattr(self, 'win_btn'):
            self.win_btn.setEnabled(False)
            self.win_btn.setText("Record WIN")
            self.win_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['green']};
                    color: white;
                    font-weight: bold;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-size: 13px;
                }}
                QPushButton:hover {{ background-color: #00E676; }}
                QPushButton:disabled {{ background-color: {COLORS['border']}; color: {COLORS['text_dim']}; }}
            """)
        if hasattr(self, 'loss_btn'):
            self.loss_btn.setEnabled(False)
            self.loss_btn.setText("Record LOSS")
            self.loss_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['red']};
                    color: white;
                    font-weight: bold;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-size: 13px;
                }}
                QPushButton:hover {{ background-color: #FF1744; }}
                QPushButton:disabled {{ background-color: {COLORS['border']}; color: {COLORS['text_dim']}; }}
            """)
        if hasattr(self, 'selected_label'):
            self.selected_label.setText("Select a champion below")
            self.selected_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-style: italic; border: none;")
        # Hide floating panel if it exists
        if self.floating_panel:
            self.floating_panel.deleteLater()
            self.floating_panel = None
        # Rebuild grid to clear selection highlight
        if hasattr(self, '_rebuild_grid'):
            self._rebuild_grid()

    def _play_death_animation(self, champion_name: str, callback):
        """Play death animation for eliminated champion."""
        widget = self.champion_widgets.get(champion_name)
        if not widget:
            callback()
            return

        # Store original position for shake animation
        original_pos = widget.pos()

        # Phase 1: Shake animation (200ms)
        shake_distance = 8
        shake_positions = [
            original_pos,
            original_pos + QPoint(shake_distance, 0),
            original_pos - QPoint(shake_distance, 0),
            original_pos + QPoint(shake_distance, 0),
            original_pos
        ]

        shake_timings = [0, 50, 100, 150, 200]
        for timing, pos in zip(shake_timings, shake_positions):
            QTimer.singleShot(timing, lambda p=pos: widget.move(p))

        # Phase 2: Flash red effect (100ms) starting at 200ms
        def flash_red():
            widget.setStyleSheet(widget.styleSheet() + f"; background-color: {COLORS['red']};")
        QTimer.singleShot(200, flash_red)

        # Phase 3: Fade to darker red with crack overlay (400ms) starting at 300ms
        def apply_death_style():
            # Add opacity effect for fade
            opacity_effect = QGraphicsOpacityEffect()
            widget.setGraphicsEffect(opacity_effect)

            # Fade animation
            fade_anim = QPropertyAnimation(opacity_effect, b"opacity")
            fade_anim.setDuration(400)
            fade_anim.setStartValue(1.0)
            fade_anim.setEndValue(0.5)
            fade_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

            # Final red styling
            widget.setStyleSheet(f"""
                background-color: {COLORS['red']};
                border: 2px solid {COLORS['red']};
                border-radius: 4px;
            """)

            fade_anim.start()
            # Store animation to prevent garbage collection
            widget._fade_animation = fade_anim

        QTimer.singleShot(300, apply_death_style)

        # Phase 4: Callback after animation completes (total: 700ms)
        QTimer.singleShot(700, callback)

    def _record_result_sticky(self, win: bool):
        """Record result from sticky header."""
        if not self.selected_champion:
            return

        # Save current scroll position
        scroll_value = self.scroll_area.verticalScrollBar().value()
        champion_name = self.selected_champion

        # If it's a loss, play death animation first
        if not win:
            def after_animation():
                streak_event = self.tracker.record_result(champion_name, win)
                self._deselect_champion()
                self._refresh_ui()
                # Restore scroll position with delay to ensure UI is fully rebuilt
                QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(scroll_value))
                # Handle streak events after UI refresh
                if streak_event:
                    QTimer.singleShot(200, lambda: self._handle_streak_event(streak_event))

            self._play_death_animation(champion_name, after_animation)
        else:
            # Win - no animation, just record
            streak_event = self.tracker.record_result(champion_name, win)
            self._deselect_champion()
            self._refresh_ui()
            # Restore scroll position with delay to ensure UI is fully rebuilt
            QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(scroll_value))
            # Handle streak events after UI refresh
            if streak_event:
                QTimer.singleShot(200, lambda: self._handle_streak_event(streak_event))

    def _record_result(self, win: bool):
        """Record result from in-page buttons."""
        if not self.selected_champion:
            return
        streak_event = self.tracker.record_result(self.selected_champion, win)
        self._deselect_champion()
        # Reset button styles
        if hasattr(self, 'win_btn'):
            self.win_btn.setEnabled(False)
            self.win_btn.setText("Record WIN")
            self.win_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['green']};
                    color: white;
                    font-weight: bold;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-size: 13px;
                }}
                QPushButton:hover {{ background-color: #00E676; }}
                QPushButton:disabled {{ background-color: {COLORS['border']}; color: {COLORS['text_dim']}; }}
            """)
        if hasattr(self, 'loss_btn'):
            self.loss_btn.setEnabled(False)
            self.loss_btn.setText("Record LOSS")
            self.loss_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['red']};
                    color: white;
                    font-weight: bold;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-size: 13px;
                }}
                QPushButton:hover {{ background-color: #FF1744; }}
                QPushButton:disabled {{ background-color: {COLORS['border']}; color: {COLORS['text_dim']}; }}
            """)
        if hasattr(self, 'selected_label'):
            self.selected_label.setText("Select a champion below")
            self.selected_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-style: italic; border: none;")
        self._refresh_ui()

    def _start_run(self):
        self.tracker.start_new_run()
        self._refresh_ui()

    def _end_run(self):
        reply = QMessageBox.question(
            self, "End Run",
            "Are you sure you want to end this run?\nThis is PERMANENT and cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.tracker.end_run()
            self._refresh_ui()

    def _played_eliminated_champion(self):
        """Handle the penalty for playing an eliminated champion in a real game."""
        active = self.tracker.get_active_run()
        if not active:
            return

        eliminated = active.get('eliminated', [])
        survived = active.get('survived', [])

        if not eliminated or not survived:
            QMessageBox.information(
                self, "Cannot Apply Penalty",
                "No eliminated champions or no alive champions to penalize."
            )
            return

        # Ask which eliminated champion was played
        from PyQt6.QtWidgets import QInputDialog
        champ, ok = QInputDialog.getItem(
            self, "Which Eliminated Champion?",
            "Select the eliminated champion you played:",
            sorted(eliminated), 0, False
        )
        if not ok or not champ:
            return

        # Confirm
        reply = QMessageBox.question(
            self, "⚠️ Played Eliminated Champion",
            f"You played {champ} who is ELIMINATED.\n\n"
            f"Penalty: A random alive champion will be eliminated!\n\n"
            f"Proceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Execute penalty
        success, victim = self.tracker.penalize_played_eliminated(champ)
        if success:
            # Build wheel pool from all non-eliminated champions (after penalty)
            new_eliminated = set(active.get('eliminated', []))
            if hasattr(self, '_grid_all_champs') and self._grid_all_champs:
                wheel_pool = [c['name'] for c in self._grid_all_champs if c['name'] not in new_eliminated]
            else:
                wheel_pool = list(survived)
            random.shuffle(wheel_pool)
            self._show_played_elim_penalty_wheel(champ, victim, wheel_pool)
        else:
            QMessageBox.warning(self, "Penalty Failed", victim)

    def _show_played_elim_penalty_wheel(self, trigger_champ: str, victim: str, pool: list):
        """Show spinning wheel for played-eliminated penalty."""
        if len(pool) < 2:
            self._show_played_elim_penalty_result(trigger_champ, victim)
            return

        self.pe_overlay = QLabel(
            f"⚠️ PLAYED {trigger_champ.upper()}!\n\n"
            f"(ELIMINATED CHAMPION)\n\n???", self
        )
        self.pe_overlay.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(139, 69, 0, 240);
                color: white;
                font-size: 28px;
                font-weight: bold;
                padding: 50px 80px;
                border-radius: 16px;
                border: 4px solid {COLORS['orange']};
            }}
        """)
        self.pe_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pe_overlay.adjustSize()
        self.pe_overlay.move(
            (self.width() - self.pe_overlay.width()) // 2,
            (self.height() - self.pe_overlay.height()) // 2
        )
        self.pe_overlay.show()

        self._pe_pool = pool
        self._pe_victim = victim
        self._pe_trigger = trigger_champ
        self._pe_index = 0
        self._pe_cycles = 0
        self._pe_max_cycles = 15

        def cycle():
            if self._pe_cycles < self._pe_max_cycles:
                champ = self._pe_pool[self._pe_index % len(self._pe_pool)]
                self.pe_overlay.setText(
                    f"⚠️ PLAYED {self._pe_trigger.upper()}!\n\n"
                    f"(ELIMINATED CHAMPION)\n\n{champ}"
                )
                self.pe_overlay.adjustSize()
                self.pe_overlay.move(
                    (self.width() - self.pe_overlay.width()) // 2,
                    (self.height() - self.pe_overlay.height()) // 2
                )
                self._pe_index += 1
                self._pe_cycles += 1
                QTimer.singleShot(100, cycle)
            else:
                self._show_played_elim_penalty_result(self._pe_trigger, self._pe_victim)

        cycle()

    def _show_played_elim_penalty_result(self, trigger_champ: str, victim: str):
        """Show final result of played-eliminated penalty wheel."""
        if hasattr(self, 'pe_overlay') and self.pe_overlay:
            self.pe_overlay.deleteLater()

        result_overlay = QLabel(
            f"⚠️ PENALTY!\n\nYou played {trigger_champ} (eliminated)\n\n"
            f"💀 {victim}\n\nELIMINATED!", self
        )
        result_overlay.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(139, 69, 0, 240);
                color: white;
                font-size: 28px;
                font-weight: bold;
                padding: 50px 80px;
                border-radius: 16px;
                border: 4px solid {COLORS['red']};
            }}
        """)
        result_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        result_overlay.adjustSize()
        result_overlay.move(
            (self.width() - result_overlay.width()) // 2,
            (self.height() - result_overlay.height()) // 2
        )
        result_overlay.show()

        def cleanup():
            result_overlay.deleteLater()
            self._refresh_ui()

        QTimer.singleShot(2500, cleanup)

    def _spin_resurrection_wheel(self):
        """Spin the gambling wheel to resurrect a random eliminated champion."""
        from PyQt6.QtCore import QTimer
        import random

        active = self.tracker.get_active_run()
        if not active:
            QMessageBox.information(self, "No Active Run", "There is no active run.")
            return

        stats = self.tracker.get_run_stats(active)
        eliminated = stats.get('eliminated', [])
        tokens_left = stats.get('tokens_remaining', 0)

        # Edge case: no tokens
        if tokens_left <= 0:
            next_token_wins = 10 - (stats['total_wins'] % 10)
            QMessageBox.information(
                self,
                "No Tokens Available",
                f"You have no resurrection tokens remaining.\n\n"
                f"Earn 1 token every 10 wins.\n"
                f"Next token in {next_token_wins} wins!"
            )
            return

        # Edge case: no eliminated champions
        if not eliminated:
            QMessageBox.information(
                self,
                "No Eliminated Champions",
                "You have no eliminated champions to resurrect.\nKeep playing and stay alive!"
            )
            return

        # Confirm spin
        reply = QMessageBox.question(
            self,
            "🎰 Resurrection Wheel",
            f"Spin the wheel to revive a RANDOM eliminated champion?\n\n"
            f"You have {tokens_left} token(s) remaining.\n"
            f"{len(eliminated)} champion(s) in the graveyard.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Show spinning animation with champion names cycling (shuffled)
        shuffled = list(eliminated)
        random.shuffle(shuffled)
        self._show_spinning_wheel(shuffled)

    def _show_spinning_wheel(self, eliminated: list):
        """Show spinning wheel animation cycling through eliminated champions."""
        from PyQt6.QtCore import QTimer
        import random

        # Create overlay
        self.wheel_overlay = QLabel("🎰\n\n???", self)
        self.wheel_overlay.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(20, 20, 30, 240);
                color: {COLORS['gold']};
                font-size: 28px;
                font-weight: bold;
                padding: 50px 80px;
                border-radius: 16px;
                border: 4px solid {COLORS['purple']};
            }}
        """)
        self.wheel_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wheel_overlay.adjustSize()

        # Center the overlay
        self.wheel_overlay.move(
            (self.width() - self.wheel_overlay.width()) // 2,
            (self.height() - self.wheel_overlay.height()) // 2
        )
        self.wheel_overlay.show()

        # Cycle through champions
        self.wheel_index = 0
        self.wheel_eliminated = eliminated
        self.wheel_cycles = 0
        self.wheel_max_cycles = 15  # Speed up after 15 cycles

        def cycle():
            if self.wheel_cycles < self.wheel_max_cycles:
                # Fast spinning
                champ = self.wheel_eliminated[self.wheel_index % len(self.wheel_eliminated)]
                self.wheel_overlay.setText(f"🎰\n\n{champ}")
                self.wheel_overlay.adjustSize()
                self.wheel_overlay.move(
                    (self.width() - self.wheel_overlay.width()) // 2,
                    (self.height() - self.wheel_overlay.height()) // 2
                )
                self.wheel_index += 1
                self.wheel_cycles += 1
                QTimer.singleShot(100, cycle)
            else:
                # Finish: pick winner and call backend
                success, result = self.tracker.resurrect_random_champion()
                if success:
                    self._show_resurrection_result(result)
                else:
                    self.wheel_overlay.deleteLater()
                    QMessageBox.warning(self, "Error", f"Failed to resurrect: {result}")

        cycle()

    def _show_resurrection_result(self, champion: str):
        """Show the final result of the resurrection wheel."""
        from PyQt6.QtCore import QTimer

        # Update overlay to show winner
        self.wheel_overlay.setText(f"✨🎲✨\n\n{champion}\n\nREVIVED!")
        self.wheel_overlay.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(156, 39, 176, 240);
                color: white;
                font-size: 32px;
                font-weight: bold;
                padding: 50px 80px;
                border-radius: 16px;
                border: 4px solid {COLORS['gold']};
            }}
        """)
        self.wheel_overlay.adjustSize()
        self.wheel_overlay.move(
            (self.width() - self.wheel_overlay.width()) // 2,
            (self.height() - self.wheel_overlay.height()) // 2
        )

        # Auto-hide and refresh
        QTimer.singleShot(2500, lambda: [self.wheel_overlay.deleteLater(), self._refresh_ui()])

    def _handle_streak_event(self, event: dict):
        """Handle a streak milestone event (bonus token or penalty elimination)."""
        if event['type'] == 'win_bonus':
            self._show_streak_bonus_notification(event['streak'])
        elif event['type'] == 'loss_penalty':
            # Build wheel pool from ALL non-eliminated champions (not just survived)
            eliminated = set()
            active = self.tracker.get_active_run()
            if active:
                eliminated = set(active.get('eliminated', []))
            if hasattr(self, '_grid_all_champs') and self._grid_all_champs:
                wheel_pool = [c['name'] for c in self._grid_all_champs if c['name'] not in eliminated]
            else:
                wheel_pool = list(event.get('pool', []))
            random.shuffle(wheel_pool)
            self._show_streak_penalty_wheel(
                event['streak'],
                event.get('champion', ''),
                wheel_pool
            )

    def _show_streak_bonus_notification(self, streak_count: int):
        """Show green overlay for streak bonus token."""
        overlay = QLabel(f"🔥 STREAK BONUS!\n\n{streak_count} Wins in a Row\n+1 Resurrection Token!", self)
        overlay.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(0, 100, 0, 240);
                color: {COLORS['gold']};
                font-size: 28px;
                font-weight: bold;
                padding: 50px 80px;
                border-radius: 16px;
                border: 4px solid {COLORS['green']};
            }}
        """)
        overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay.adjustSize()
        overlay.move(
            (self.width() - overlay.width()) // 2,
            (self.height() - overlay.height()) // 2
        )
        overlay.show()
        QTimer.singleShot(2500, lambda: overlay.deleteLater())

    def _show_streak_penalty_wheel(self, streak_count: int, champion: str, pool: list):
        """Show red-themed spinning wheel for loss streak penalty elimination."""
        if not champion:
            return

        # Use the pool (survived champions before elimination) for the wheel
        # If pool is empty or too small, just show the result directly
        if len(pool) < 2:
            self._show_streak_penalty_result(streak_count, champion)
            return

        # Create red-themed spinning overlay
        self.penalty_overlay = QLabel(f"⚠️ LOSS STREAK PENALTY!\n\n{streak_count} Losses in a Row\n\n???", self)
        self.penalty_overlay.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(139, 0, 0, 240);
                color: white;
                font-size: 28px;
                font-weight: bold;
                padding: 50px 80px;
                border-radius: 16px;
                border: 4px solid {COLORS['red']};
            }}
        """)
        self.penalty_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.penalty_overlay.adjustSize()
        self.penalty_overlay.move(
            (self.width() - self.penalty_overlay.width()) // 2,
            (self.height() - self.penalty_overlay.height()) // 2
        )
        self.penalty_overlay.show()

        # Spin through survived champions, then land on the chosen one
        self._penalty_pool = pool
        self._penalty_champion = champion
        self._penalty_streak = streak_count
        self._penalty_index = 0
        self._penalty_cycles = 0
        self._penalty_max_cycles = 15

        def cycle():
            if self._penalty_cycles < self._penalty_max_cycles:
                champ = self._penalty_pool[self._penalty_index % len(self._penalty_pool)]
                self.penalty_overlay.setText(
                    f"⚠️ LOSS STREAK PENALTY!\n\n{self._penalty_streak} Losses in a Row\n\n{champ}"
                )
                self.penalty_overlay.adjustSize()
                self.penalty_overlay.move(
                    (self.width() - self.penalty_overlay.width()) // 2,
                    (self.height() - self.penalty_overlay.height()) // 2
                )
                self._penalty_index += 1
                self._penalty_cycles += 1
                QTimer.singleShot(100, cycle)
            else:
                # Land on the actual chosen champion
                self._show_streak_penalty_result(self._penalty_streak, self._penalty_champion)

        cycle()

    def _show_streak_penalty_result(self, streak_count: int, champion: str):
        """Show final result of the penalty wheel."""
        # Clean up spinning overlay if it exists
        if hasattr(self, 'penalty_overlay') and self.penalty_overlay:
            self.penalty_overlay.deleteLater()

        result_overlay = QLabel(
            f"💀💀💀\n\n{champion}\n\nELIMINATED!\n\n"
            f"({streak_count} loss streak penalty)",
            self
        )
        result_overlay.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(139, 0, 0, 240);
                color: white;
                font-size: 32px;
                font-weight: bold;
                padding: 50px 80px;
                border-radius: 16px;
                border: 4px solid {COLORS['red']};
            }}
        """)
        result_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        result_overlay.adjustSize()
        result_overlay.move(
            (self.width() - result_overlay.width()) // 2,
            (self.height() - result_overlay.height()) // 2
        )
        result_overlay.show()

        def cleanup():
            result_overlay.deleteLater()
            self._refresh_ui()

        QTimer.singleShot(2500, cleanup)

    def _export_html(self):
        """Export current run to HTML."""
        from PyQt6.QtWidgets import QFileDialog
        from src.analytics.nuzlocke_export import NuzlockeExporter
        import os

        active = self.tracker.get_active_run()
        if not active:
            QMessageBox.information(self, "No Active Run", "There is no active run to export.")
            return

        stats = self.tracker.get_run_stats(active)

        # Ask where to save
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Nuzlocke Run to HTML",
            f"nuzlocke_run_{stats['id']}.html",
            "HTML Files (*.html)"
        )

        if not file_path:
            return

        try:
            exporter = NuzlockeExporter(stats)
            output = exporter.export_to_html(file_path)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Run exported successfully to:\n{output}"
            )

            # Open in browser
            import webbrowser
            webbrowser.open(f"file://{os.path.abspath(output)}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export run:\n{str(e)}"
            )


    def _export_past_run_html(self, run_stats):
        """Export a past run to HTML."""
        from PyQt6.QtWidgets import QFileDialog
        from src.analytics.nuzlocke_export import NuzlockeExporter

        # Ask where to save
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Past Run to HTML",
            f"nuzlocke_run_{run_stats['id']}.html",
            "HTML Files (*.html)"
        )

        if not file_path:
            return

        try:
            exporter = NuzlockeExporter(run_stats)
            output = exporter.export_to_html(file_path)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Run #{run_stats['id']} exported successfully to:\n{output}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export run:\n{str(e)}"
            )


    def _add_graveyard_visual(self, stats):
        """Show eliminated champions as a graveyard with tombstones, sorted by saddest deaths."""
        eliminated = stats.get('eliminated', [])
        if not eliminated:
            return

        card, layout = self._card(f"⚰️ Graveyard ({len(eliminated)} Fallen Champions)")

        desc = QLabel("Sorted by saddest deaths first (most wins before falling).")
        desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; font-style: italic; border: none;")
        layout.addWidget(desc)

        # Get enhanced graveyard stats (sorted saddest first)
        active_run = getattr(self, '_active_run', None)
        graveyard = self.tracker.get_graveyard_stats(active_run)

        # Grid of tombstones
        grid = QGridLayout()
        grid.setSpacing(12)

        for i, entry in enumerate(graveyard):
            champ = entry['champion']
            wins_before = entry['wins_before_death']
            game_num = entry['game_number']
            row = i // 6
            col = i % 6

            tomb_widget = QWidget()
            tomb_layout = QVBoxLayout(tomb_widget)
            tomb_layout.setContentsMargins(8, 6, 8, 6)
            tomb_layout.setSpacing(2)

            # Champion icon with red overlay
            if self.dd:
                icon_label = QLabel()
                icon_label.setFixedSize(64, 64)
                icon_path = self.dd.get_champion_icon_path(champ)
                if icon_path:
                    px = QPixmap(icon_path)
                    if not px.isNull():
                        icon_label.setPixmap(px.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                        icon_label.setStyleSheet("border: 3px solid #FF1744; border-radius: 4px; opacity: 0.6;")
                tomb_layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)

            # Champion name
            name_label = QLabel(champ)
            name_label.setStyleSheet(f"color: {COLORS['red']}; font-size: 11px; font-weight: bold; border: none;")
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setWordWrap(True)
            tomb_layout.addWidget(name_label)

            # Death info: wins before death + game number + cause
            death_cause = entry.get('death_cause', 'loss')
            trigger = entry.get('trigger_champion', '')
            if death_cause == 'played_eliminated':
                if wins_before > 0:
                    death_info = QLabel(f"{wins_before}W before fall\nPlayed {trigger}")
                else:
                    death_info = QLabel(f"Played {trigger}")
            elif death_cause == 'streak_penalty' or (entry.get('was_penalty', False) and death_cause != 'loss'):
                if wins_before > 0:
                    death_info = QLabel(f"{wins_before}W before fall\nStreak penalty")
                else:
                    death_info = QLabel(f"Streak penalty")
            elif wins_before > 0:
                death_info = QLabel(f"{wins_before}W before fall\nGame #{game_num}")
            else:
                death_info = QLabel(f"Fell on Game #{game_num}")
            death_info.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 9px; border: none;")
            death_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tomb_layout.addWidget(death_info)

            # Tombstone emoji
            tomb_emoji = QLabel("🪦")
            tomb_emoji.setStyleSheet(f"font-size: 16px; border: none;")
            tomb_emoji.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tomb_layout.addWidget(tomb_emoji)

            tomb_widget.setStyleSheet(f"""
                QWidget {{
                    background-color: {COLORS['bg_dark']};
                    border: 2px solid {COLORS['red']};
                    border-radius: 8px;
                }}
            """)
            tomb_widget.setFixedSize(100, 160)

            grid.addWidget(tomb_widget, row, col)

        layout.addLayout(grid)
        self.layout_main.addWidget(card)

    def _add_all_games(self, stats):
        """Show complete match history for the current run."""
        if not stats.get('history'):
            return

        card, layout = self._card(f"All Games ({len(stats['history'])} total)")

        # Scrollable area for all games
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setMaximumHeight(400)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(6)
        container_layout.setContentsMargins(0, 0, 0, 0)

        for h in reversed(stats['history']):
            row = QHBoxLayout()

            result = QLabel("W" if h['win'] else "L")
            result.setFixedWidth(24)
            color = COLORS['green'] if h['win'] else COLORS['red']
            result.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px; border: none;")
            row.addWidget(result)

            icon = QLabel()
            icon.setFixedSize(20, 20)
            if self.dd:
                icon_path = self.dd.get_champion_icon_path(h['champion'])
                if icon_path:
                    px = QPixmap(icon_path)
                    if not px.isNull():
                        icon.setPixmap(px.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            row.addWidget(icon)

            champ = QLabel(h['champion'])
            champ.setFixedWidth(120)
            champ.setStyleSheet(f"font-weight: bold; border: none;")
            row.addWidget(champ)

            status = QLabel("SURVIVED" if h['win'] else "ELIMINATED")
            status.setStyleSheet(f"color: {color}; font-size: 11px; border: none;")
            row.addWidget(status)

            date = QLabel(h.get('date', ''))
            date.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
            row.addWidget(date)

            row.addStretch()
            container_layout.addLayout(row)

        scroll.setWidget(container)
        layout.addWidget(scroll)
        self.layout_main.addWidget(card)

    def _show_floating_panel(self, champion_name: str):
        """Show floating action panel at bottom-right for quick win/loss recording."""
        # Remove old panel if exists
        if self.floating_panel:
            self.floating_panel.deleteLater()

        # Create floating panel
        self.floating_panel = QFrame(self)
        self.floating_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 3px solid {COLORS['gold']};
                border-radius: 12px;
            }}
        """)
        self.floating_panel.setFixedSize(280, 160)

        layout = QVBoxLayout(self.floating_panel)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Title
        title = QLabel("Quick Actions")
        title.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; font-size: 13px; border: none;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Champion info
        champ_row = QHBoxLayout()
        if self.dd:
            icon_label = QLabel()
            icon_label.setFixedSize(40, 40)
            icon_path = self.dd.get_champion_icon_path(champion_name)
            if icon_path:
                px = QPixmap(icon_path)
                if not px.isNull():
                    icon_label.setPixmap(px.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            champ_row.addWidget(icon_label)

        champ_label = QLabel(champion_name)
        champ_label.setStyleSheet(f"color: {COLORS['text_bright']}; font-weight: bold; font-size: 14px; border: none;")
        champ_row.addWidget(champ_label)
        champ_row.addStretch()
        layout.addLayout(champ_row)

        # Win button
        win_btn = QPushButton("✓ WIN")
        win_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['green']};
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 6px;
                font-size: 13px;
            }}
            QPushButton:hover {{ background-color: #00E676; }}
        """)
        win_btn.clicked.connect(lambda: self._record_result(True))
        layout.addWidget(win_btn)

        # Loss button
        loss_btn = QPushButton("✗ LOSS")
        loss_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['red']};
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 6px;
                font-size: 13px;
            }}
            QPushButton:hover {{ background-color: #FF1744; }}
        """)
        loss_btn.clicked.connect(lambda: self._record_result(False))
        layout.addWidget(loss_btn)

        # Deselect button
        deselect_btn = QPushButton("Cancel")
        deselect_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_dim']};
                padding: 4px;
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                border-color: {COLORS['text']};
                color: {COLORS['text']};
            }}
        """)
        deselect_btn.clicked.connect(self._deselect_champion)
        layout.addWidget(deselect_btn)

        # Position at bottom-right
        self.floating_panel.show()
        self.floating_panel.raise_()
        self._position_floating_panel()

    def _hide_floating_panel(self):
        """Hide and remove floating panel."""
        if self.floating_panel:
            self.floating_panel.deleteLater()
            self.floating_panel = None

    def _position_floating_panel(self):
        """Position floating panel at bottom-right corner."""
        if not self.floating_panel:
            return

        # Position 20px from right, 20px from bottom
        x = self.width() - self.floating_panel.width() - 20
        y = self.height() - self.floating_panel.height() - 20
        self.floating_panel.move(x, y)

    def resizeEvent(self, event):
        """Reposition floating panel on window resize."""
        super().resizeEvent(event)
        self._position_floating_panel()

    def _delete_run(self, run_id: int):
        reply = QMessageBox.question(
            self, "Delete Run",
            f"Are you sure you want to delete Run #{run_id}?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.tracker.delete_run(run_id)
            self._refresh_ui()
