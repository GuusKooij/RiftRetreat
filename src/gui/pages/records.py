"""Records & Achievements page: Personal bests, milestones, multi-kill tracker."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QProgressBar, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt

from src.gui.theme import COLORS


class RecordsPage(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        self.layout_main = QVBoxLayout(container)
        self.layout_main.setSpacing(16)
        self.layout_main.setContentsMargins(24, 24, 24, 24)

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

    def update_data(self, stats_analyzer, achievement_tracker, challenge_analyzer=None):
        while self.layout_main.count():
            child = self.layout_main.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Achievement badges
        self._add_achievements(achievement_tracker)

        # Secret achievements
        self._add_secret_achievements(achievement_tracker)

        # Personal records
        self._add_personal_records(stats_analyzer)

        # All-time pentakills from challenge data
        if challenge_analyzer:
            self._add_alltime_pentakills(challenge_analyzer, stats_analyzer)

        # Multi-kill summary (this season)
        self._add_multi_kills(stats_analyzer)

        # Comeback / throw stats
        self._add_comeback_throw(stats_analyzer)

        # Game timing analysis
        self._add_game_timing(stats_analyzer)

        self.layout_main.addStretch()

    def _add_achievements(self, at):
        progress = at.progress_all()
        earned = [a for a in progress if a['earned']]
        not_earned = [a for a in progress if not a['earned']]

        card, layout = self._card(f"Achievements ({len(earned)} / {len(progress)} earned)")

        # Earned achievements
        if earned:
            earned_label = QLabel("Earned:")
            earned_label.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; font-size: 13px; border: none;")
            layout.addWidget(earned_label)

            grid = QGridLayout()
            grid.setSpacing(8)

            for i, a in enumerate(earned):
                rarity_color = a.get('rarity_color', COLORS['gold'])
                rarity_name = a.get('rarity', 'Common')

                badge = QFrame()
                badge.setStyleSheet(f"""
                    QFrame {{
                        background-color: {COLORS['bg_dark']};
                        border: 2px solid {rarity_color};
                        border-radius: 8px;
                    }}
                """)
                badge_layout = QVBoxLayout(badge)
                badge_layout.setContentsMargins(10, 6, 10, 8)
                badge_layout.setSpacing(2)

                # Rarity label
                rarity_lbl = QLabel(rarity_name.upper())
                rarity_lbl.setStyleSheet(f"color: {rarity_color}; font-size: 8px; font-weight: bold; border: none;")
                rarity_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                badge_layout.addWidget(rarity_lbl)

                name = QLabel(a['name'])
                name.setStyleSheet(f"color: {rarity_color}; font-weight: bold; font-size: 12px; border: none;")
                name.setAlignment(Qt.AlignmentFlag.AlignCenter)
                badge_layout.addWidget(name)

                desc = QLabel(a['description'])
                desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; border: none;")
                desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
                desc.setWordWrap(True)
                badge_layout.addWidget(desc)

                grid.addWidget(badge, i // 4, i % 4)

            layout.addLayout(grid)

        # In-progress achievements
        if not_earned:
            in_progress_label = QLabel("In Progress:")
            in_progress_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-weight: bold; font-size: 13px; margin-top: 12px; border: none;")
            layout.addWidget(in_progress_label)

            for a in not_earned[:8]:
                rarity_color = a.get('rarity_color', COLORS['text'])
                row = QHBoxLayout()

                name = QLabel(a['name'])
                name.setFixedWidth(160)
                name.setStyleSheet(f"color: {rarity_color}; border: none;")
                row.addWidget(name)

                bar = QProgressBar()
                bar.setRange(0, a['target'])
                bar.setValue(min(a['current'], a['target']))
                bar.setFormat(f"{a['current']}/{a['target']} ({a['progress_pct']:.0f}%)")
                bar.setFixedHeight(18)
                bar.setStyleSheet(f"""
                    QProgressBar {{
                        background-color: {COLORS['bg_dark']};
                        border: 1px solid {COLORS['border']};
                        border-radius: 4px;
                        text-align: center;
                        color: {COLORS['text']};
                        font-size: 10px;
                    }}
                    QProgressBar::chunk {{
                        background-color: {COLORS['gold_dark']};
                        border-radius: 3px;
                    }}
                """)
                row.addWidget(bar)

                desc = QLabel(a['description'])
                desc.setFixedWidth(200)
                desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
                row.addWidget(desc)

                layout.addLayout(row)

        self.layout_main.addWidget(card)

    def _add_secret_achievements(self, at):
        """Add secret achievements section — earned show full details, locked show ???."""
        secrets = at.progress_secrets()
        earned = [s for s in secrets if s['earned']]
        locked = [s for s in secrets if not s['earned']]

        card, layout = self._card(f"Secret Achievements ({len(earned)} discovered)")

        if earned:
            earned_label = QLabel("Unlocked:")
            earned_label.setStyleSheet(f"color: {COLORS['purple']}; font-weight: bold; font-size: 13px; border: none;")
            layout.addWidget(earned_label)

            grid = QGridLayout()
            grid.setSpacing(8)

            for i, a in enumerate(earned):
                badge = QFrame()
                badge.setStyleSheet(f"""
                    QFrame {{
                        background-color: {COLORS['bg_dark']};
                        border: 2px solid {COLORS['purple']};
                        border-radius: 8px;
                    }}
                """)
                badge_layout = QVBoxLayout(badge)
                badge_layout.setContentsMargins(10, 6, 10, 8)
                badge_layout.setSpacing(2)

                icon_lbl = QLabel("SECRET")
                icon_lbl.setStyleSheet(f"color: {COLORS['purple']}; font-size: 8px; font-weight: bold; border: none;")
                icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                badge_layout.addWidget(icon_lbl)

                name = QLabel(a['name'])
                name.setStyleSheet(f"color: {COLORS['purple']}; font-weight: bold; font-size: 12px; border: none;")
                name.setAlignment(Qt.AlignmentFlag.AlignCenter)
                badge_layout.addWidget(name)

                desc = QLabel(a['description'])
                desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; border: none;")
                desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
                desc.setWordWrap(True)
                badge_layout.addWidget(desc)

                grid.addWidget(badge, i // 4, i % 4)

            layout.addLayout(grid)

        # Show up to 8 locked placeholders
        if locked:
            locked_label = QLabel("Undiscovered:")
            locked_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-weight: bold; font-size: 13px; margin-top: 12px; border: none;")
            layout.addWidget(locked_label)

            grid = QGridLayout()
            grid.setSpacing(8)

            shown = min(len(locked), 8)
            for i in range(shown):
                badge = QFrame()
                badge.setStyleSheet(f"""
                    QFrame {{
                        background-color: {COLORS['bg_dark']};
                        border: 2px solid {COLORS['border']};
                        border-radius: 8px;
                    }}
                """)
                badge_layout = QVBoxLayout(badge)
                badge_layout.setContentsMargins(10, 8, 10, 8)
                badge_layout.setSpacing(4)

                lock_icon = QLabel("🔒")
                lock_icon.setStyleSheet("font-size: 18px; border: none;")
                lock_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
                badge_layout.addWidget(lock_icon)

                name = QLabel("???")
                name.setStyleSheet(f"color: {COLORS['text_dim']}; font-weight: bold; font-size: 12px; border: none;")
                name.setAlignment(Qt.AlignmentFlag.AlignCenter)
                badge_layout.addWidget(name)

                grid.addWidget(badge, i // 4, i % 4)

            layout.addLayout(grid)

            remaining = len(locked) - shown
            if remaining > 0:
                more_label = QLabel(f"...and {remaining} more secrets to discover")
                more_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; font-style: italic; border: none;")
                layout.addWidget(more_label)

        self.layout_main.addWidget(card)

    def _add_personal_records(self, stats):
        records = stats.personal_records()
        if not records:
            return

        card, layout = self._card("Hall of Fame - Personal Records")

        for r in records:
            row = QHBoxLayout()

            record_name = QLabel(r['record'])
            record_name.setFixedWidth(180)
            record_name.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; border: none;")
            row.addWidget(record_name)

            value = QLabel(str(r['value']))
            value.setFixedWidth(200)
            value.setStyleSheet(f"color: {COLORS['text_bright']}; font-weight: bold; font-size: 14px; border: none;")
            row.addWidget(value)

            champ = QLabel(r['champion'])
            champ.setFixedWidth(100)
            champ.setStyleSheet(f"color: {COLORS['blue']}; border: none;")
            row.addWidget(champ)

            result_color = COLORS['green'] if r['win'] else COLORS['red']
            result = QLabel("W" if r['win'] else "L")
            result.setFixedWidth(20)
            result.setStyleSheet(f"color: {result_color}; font-weight: bold; border: none;")
            row.addWidget(result)

            date = QLabel(r['date'])
            date.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
            row.addWidget(date)

            row.addStretch()
            layout.addLayout(row)

        self.layout_main.addWidget(card)

    def _add_alltime_pentakills(self, ca, stats):
        # Challenge 402106 = PENTAKIIIIIIIIL!! (lifetime penta count)
        # Challenge 210002 = Same Penta, Different Champ (unique champs with pentas)
        penta_info = ca.get_challenge_info(402106)
        unique_info = ca.get_challenge_info(210002)

        total_pentas = int(penta_info.get('current_value', 0))
        unique_champs = int(unique_info.get('current_value', 0))

        if total_pentas == 0:
            return

        card, layout = self._card("Pentakills (All Seasons)")

        grid = QGridLayout()
        grid.setSpacing(16)

        # This season pentas from match data
        mk = stats.multi_kill_summary()
        this_season = mk.get('penta_kills', 0)
        previous_seasons = max(total_pentas - this_season, 0)

        data = [
            ('All-Time', str(total_pentas), 'Total across all seasons', COLORS['gold']),
            ('This Season', str(this_season), 'From match history', COLORS['green']),
            ('Past Seasons', str(previous_seasons), 'Before this season', COLORS['blue']),
            ('Unique Champs', str(unique_champs), 'Different champs with pentas', COLORS['purple']),
        ]

        for col, (label, value, desc, color) in enumerate(data):
            w = QWidget()
            l = QVBoxLayout(w)
            l.setContentsMargins(0, 0, 0, 0)
            l.setSpacing(2)

            val = QLabel(value)
            val.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color};")
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(val)

            lbl = QLabel(label)
            lbl.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {COLORS['text']};")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(lbl)

            d = QLabel(desc)
            d.setStyleSheet(f"font-size: 10px; color: {COLORS['text_dim']};")
            d.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(d)

            grid.addWidget(w, 0, col)

        layout.addLayout(grid)

        note = QLabel("Note: Per-season breakdown not available from Riot API. Only lifetime total + current season from match data.")
        note.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; font-style: italic; border: none;")
        note.setWordWrap(True)
        layout.addWidget(note)

        self.layout_main.addWidget(card)

    def _add_multi_kills(self, stats):
        mk = stats.multi_kill_summary()

        card, layout = self._card("Multi-Kill Tracker")

        grid = QGridLayout()
        grid.setSpacing(16)

        kills_data = [
            ('Double Kills', mk['double_kills'], COLORS['blue']),
            ('Triple Kills', mk['triple_kills'], COLORS['green']),
            ('Quadra Kills', mk['quadra_kills'], COLORS['orange']),
            ('Penta Kills', mk['penta_kills'], COLORS['gold']),
        ]

        for col, (label, count, color) in enumerate(kills_data):
            w = QWidget()
            l = QVBoxLayout(w)
            l.setContentsMargins(0, 0, 0, 0)
            l.setSpacing(2)

            val = QLabel(str(count))
            val.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color};")
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(val)

            lbl = QLabel(label)
            lbl.setStyleSheet(f"font-size: 11px; color: {COLORS['text_dim']};")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(lbl)

            grid.addWidget(w, 0, col)

        layout.addLayout(grid)
        self.layout_main.addWidget(card)

    def _add_comeback_throw(self, stats):
        ct = stats.comeback_throw_analysis()

        # Check if any matches have gold diff data
        has_data = ct['comebacks'] + ct['throws'] + ct['stomps'] > 0 or ct.get('games_with_data', 0) > 0

        card, layout = self._card("Comeback & Throw Analysis")

        if not has_data:
            note = QLabel(
                "No gold diff data yet. Delete data/matches.json and do a full refresh "
                "to re-fetch all matches with team gold data."
            )
            note.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none;")
            note.setWordWrap(True)
            layout.addWidget(note)
            self.layout_main.addWidget(card)
            return

        grid = QGridLayout()
        grid.setSpacing(16)

        data = [
            ('Comebacks', str(ct['comebacks']), f"{ct['comeback_rate']}% of games", COLORS['green']),
            ('Throws', str(ct['throws']), f"{ct['throw_rate']}% of games", COLORS['red']),
            ('Stomps', str(ct['stomps']), "Won with 5k+ gold lead", COLORS['blue']),
        ]

        for col, (label, value, desc, color) in enumerate(data):
            w = QWidget()
            l = QVBoxLayout(w)
            l.setContentsMargins(0, 0, 0, 0)
            l.setSpacing(2)

            val = QLabel(value)
            val.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(val)

            lbl = QLabel(label)
            lbl.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {COLORS['text']};")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(lbl)

            d = QLabel(desc)
            d.setStyleSheet(f"font-size: 10px; color: {COLORS['text_dim']};")
            d.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(d)

            grid.addWidget(w, 0, col)

        layout.addLayout(grid)

        explanation = QLabel(
            f"Based on {ct.get('games_with_data', 0)} games with gold data. "
            "Comeback = won while 2k+ gold behind. Throw = lost while 2k+ gold ahead. "
            "0 is real -- you either win cleanly or lose when behind!"
        )
        explanation.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; font-style: italic; border: none;")
        explanation.setWordWrap(True)
        layout.addWidget(explanation)

        self.layout_main.addWidget(card)

    def _add_game_timing(self, stats):
        timing = stats.game_timing_analysis()

        card, layout = self._card("Game Timing")

        grid = QGridLayout()
        grid.setSpacing(16)

        data = [
            ('Win Duration', f"{timing['avg_duration_wins']}m", COLORS['green']),
            ('Loss Duration', f"{timing['avg_duration_losses']}m", COLORS['red']),
            ('First Blood Rate', f"{timing['first_blood_rate']}%", COLORS['orange']),
            ('FB Win Rate', f"{timing['first_blood_wr']}%", COLORS['gold']),
        ]

        for col, (label, value, color) in enumerate(data):
            w = QWidget()
            l = QVBoxLayout(w)
            l.setContentsMargins(0, 0, 0, 0)
            l.setSpacing(2)

            val = QLabel(value)
            val.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {color};")
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(val)

            lbl = QLabel(label)
            lbl.setStyleSheet(f"font-size: 11px; color: {COLORS['text_dim']};")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(lbl)

            grid.addWidget(w, 0, col)

        layout.addLayout(grid)

        # Objective stats
        obj_label = QLabel(
            f"Avg Dragons: {timing['avg_dragon_kills']}  |  "
            f"Avg Barons: {timing['avg_baron_kills']}  |  "
            f"Avg Turrets: {timing['avg_turret_kills']}"
        )
        obj_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none;")
        layout.addWidget(obj_label)

        self.layout_main.addWidget(card)
