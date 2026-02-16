"""Challenges page: Progress tracking, champion recommendations, in-game tips.

Completionist-focused: progress bars, completion counts, tier progression.
"""

import random

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QProgressBar, QScrollArea, QGridLayout, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from src.gui.theme import COLORS, RANK_COLORS


class ChallengesPage(QWidget):
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

    def update_data(self, challenge_analyzer):
        while self.layout_main.count():
            child = self.layout_main.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Total challenge points
        self._add_total_points(challenge_analyzer)

        # Completion tracker
        self._add_completion_tracker(challenge_analyzer)

        # Challenge roadmap / planner
        self._add_roadmap(challenge_analyzer)

        # Weekly goals
        self._add_weekly_goals(challenge_analyzer)

        # Close to leveling up
        self._add_close_to_leveling(challenge_analyzer)

        # Champion recommendations for challenges
        self._add_champion_recommendations(challenge_analyzer)

        # Champions not won with
        self._add_not_won_with(challenge_analyzer)

        # Premade team comp challenges
        self._add_premade_challenges(challenge_analyzer)

        # In-game tips
        self._add_in_game_tips(challenge_analyzer)

        self.layout_main.addStretch()

    def _add_total_points(self, ca):
        tp = ca.total_points()
        if not tp:
            return

        card, layout = self._card("Challenge Points")

        level = tp.get('level', 'NONE')
        current = tp.get('current', 0)
        maximum = tp.get('max', 1)
        pct = round(current / max(maximum, 1) * 100, 1)

        rank_color = RANK_COLORS.get(level, COLORS['gold'])

        header = QHBoxLayout()
        level_label = QLabel(level)
        level_label.setStyleSheet(f"color: {rank_color}; font-size: 28px; font-weight: bold; border: none;")
        header.addWidget(level_label)

        points_label = QLabel(f"{current:,} / {maximum:,}")
        points_label.setStyleSheet(f"color: {COLORS['text']}; font-size: 18px; border: none;")
        points_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(points_label)

        layout.addLayout(header)

        bar = QProgressBar()
        bar.setRange(0, maximum)
        bar.setValue(current)
        bar.setFormat(f"{pct}%")
        bar.setFixedHeight(24)
        bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['bg_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                text-align: center;
                color: {COLORS['text_bright']};
                font-size: 12px;
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background-color: {rank_color};
                border-radius: 5px;
            }}
        """)
        layout.addWidget(bar)

        # Category breakdown
        categories = ca.category_points()
        if categories:
            cat_layout = QGridLayout()
            cat_layout.setSpacing(8)
            col = 0
            for cat_name, cat_data in categories.items():
                cat_level = cat_data.get('level', 'NONE')
                cat_current = cat_data.get('current', 0)
                cat_max = cat_data.get('max', 1)
                cat_color = RANK_COLORS.get(cat_level, COLORS['text_dim'])

                cat_label = QLabel(f"{cat_name}\n{cat_level} ({cat_current}/{cat_max})")
                cat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cat_label.setStyleSheet(f"color: {cat_color}; font-size: 11px; border: none;")
                cat_layout.addWidget(cat_label, 0, col)
                col += 1

            layout.addLayout(cat_layout)

        self.layout_main.addWidget(card)

    def _add_completion_tracker(self, ca):
        """Show overall completion stats — the completionist view."""
        total_challenges = len(ca.config)
        progressed = len(ca.challenges.get('challenges', []))
        maxed = sum(1 for c in ca.challenges.get('challenges', []) if c.get('level') in ['MASTER', 'GRANDMASTER', 'CHALLENGER'])

        card, layout = self._card("Completion Tracker")

        grid = QGridLayout()
        grid.setSpacing(16)

        # Total progressed
        self._add_completion_stat(grid, 0, 0, str(progressed), f"/ {total_challenges} Challenges", COLORS['blue'])
        self._add_completion_stat(grid, 0, 1, str(maxed), "Mastered+", COLORS['purple'])

        # Count per tier
        tier_counts = {}
        for c in ca.challenges.get('challenges', []):
            tier = c.get('level', 'NONE')
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        col = 2
        for tier in ['CHALLENGER', 'GRANDMASTER', 'MASTER', 'DIAMOND', 'PLATINUM', 'GOLD']:
            count = tier_counts.get(tier, 0)
            if count > 0:
                color = RANK_COLORS.get(tier, COLORS['text'])
                self._add_completion_stat(grid, 0, col, str(count), tier.title(), color)
                col += 1

        layout.addLayout(grid)
        self.layout_main.addWidget(card)

    def _add_completion_stat(self, grid, row, col, value, label, color):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(2)

        val = QLabel(value)
        val.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {color};")
        val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(val)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"font-size: 10px; color: {COLORS['text_dim']};")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(lbl)

        grid.addWidget(w, row, col)

    def _add_close_to_leveling(self, ca):
        close = ca.close_to_leveling(top_n=15)
        if not close:
            return

        card, layout = self._card(f"Almost There! ({len(close)} challenges close to next tier)")

        desc = QLabel("These challenges are closest to reaching the next tier:")
        desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none;")
        layout.addWidget(desc)

        for c in close:
            row = QHBoxLayout()

            name = QLabel(c['name'][:40])
            name.setFixedWidth(240)
            name.setStyleSheet(f"font-weight: bold; border: none;")
            row.addWidget(name)

            current_color = RANK_COLORS.get(c['current_level'], COLORS['text_dim'])
            next_color = RANK_COLORS.get(c['next_tier'], COLORS['text'])

            tier_label = QLabel(f"{c['current_level']}")
            tier_label.setFixedWidth(90)
            tier_label.setStyleSheet(f"color: {current_color}; font-weight: bold; border: none;")
            row.addWidget(tier_label)

            arrow = QLabel("->")
            arrow.setFixedWidth(20)
            arrow.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
            row.addWidget(arrow)

            next_label = QLabel(f"{c['next_tier']}")
            next_label.setFixedWidth(90)
            next_label.setStyleSheet(f"color: {next_color}; font-weight: bold; border: none;")
            row.addWidget(next_label)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(min(int(c['progress_pct']), 100))
            bar.setFormat(f"{c['current_value']:.0f}/{c['next_threshold']:.0f} ({c['progress_pct']:.0f}%)")
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
                    background-color: {next_color};
                    border-radius: 3px;
                }}
            """)
            row.addWidget(bar)

            layout.addLayout(row)

        self.layout_main.addWidget(card)

    def _add_champion_recommendations(self, ca):
        recs = ca.champion_recommendations()[:10]
        if not recs:
            return

        card, layout = self._card("Play These Next (Challenge Optimized)")

        desc = QLabel("Champions that progress MULTIPLE challenges at once:")
        desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none;")
        layout.addWidget(desc)

        for r in recs:
            row_widget = QFrame()
            row_widget.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_main']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 6px;
                    padding: 4px;
                }}
            """)
            row_layout = QVBoxLayout(row_widget)
            row_layout.setContentsMargins(12, 8, 12, 8)
            row_layout.setSpacing(4)

            # Champion name + score + roles
            header = QHBoxLayout()
            name_color = COLORS['green'] if r['new_win'] else COLORS['text']
            name = QLabel(r['champion'])
            name.setStyleSheet(f"color: {name_color}; font-weight: bold; font-size: 14px; border: none;")
            header.addWidget(name)

            if r['new_win']:
                new_badge = QLabel("NO WIN THIS SEASON")
                new_badge.setStyleSheet(f"""
                    background-color: {COLORS['green']};
                    color: white;
                    font-size: 9px;
                    font-weight: bold;
                    padding: 2px 6px;
                    border-radius: 3px;
                    border: none;
                """)
                header.addWidget(new_badge)

            mastery_label = QLabel(f"M{r['mastery_level']}")
            mastery_label.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; border: none;")
            header.addWidget(mastery_label)

            roles = QLabel(f"Play: {' / '.join(r['suggested_roles'])}")
            roles.setStyleSheet(f"color: {COLORS['blue']}; border: none;")
            header.addWidget(roles)

            header.addStretch()

            score = QLabel(f"Score: {r['score']}")
            score.setStyleSheet(f"color: {COLORS['orange']}; font-weight: bold; border: none;")
            header.addWidget(score)

            row_layout.addLayout(header)

            # Reasons
            reasons = QLabel("  |  ".join(r['reasons'][:3]))
            reasons.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
            reasons.setWordWrap(True)
            row_layout.addWidget(reasons)

            layout.addWidget(row_widget)

        self.layout_main.addWidget(card)

    def _add_not_won_with(self, ca):
        # Use REAL API data for Jack of All Champs progress
        jack = ca.jack_of_all_champs_progress()
        won_count = jack['value']  # Real lifetime value from API (e.g. 140)
        total_champs = jack['total_champions'] or 172

        card, layout = self._card(f"Jack of All Champs Progress (Lifetime)")

        # Tier info
        tier_color = RANK_COLORS.get(jack['level'], COLORS['gold'])
        tier_label = QLabel(f"{jack['level']} -- {won_count} / {total_champs} unique champions won with (all-time)")
        tier_label.setStyleSheet(f"color: {tier_color}; font-size: 14px; font-weight: bold; border: none;")
        layout.addWidget(tier_label)

        # Overall progress bar
        bar = QProgressBar()
        bar.setRange(0, total_champs)
        bar.setValue(won_count)
        bar.setFormat(f"{won_count} / {total_champs} ({round(won_count/max(total_champs,1)*100)}%)")
        bar.setFixedHeight(24)
        bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['bg_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                text-align: center;
                color: {COLORS['text_bright']};
                font-size: 12px;
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['blue']};
                border-radius: 5px;
            }}
        """)
        layout.addWidget(bar)

        # Next tier progress
        if jack['next_threshold']:
            remaining = jack['remaining']
            next_bar = QProgressBar()
            next_bar.setRange(0, int(jack['next_threshold']))
            next_bar.setValue(won_count)
            next_tier_color = RANK_COLORS.get(jack['next_tier'], COLORS['gold'])
            next_bar.setFormat(f"Next: {jack['next_tier']} ({won_count}/{int(jack['next_threshold'])} -- {int(remaining)} to go)")
            next_bar.setFixedHeight(18)
            next_bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {COLORS['bg_dark']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 4px;
                    text-align: center;
                    color: {COLORS['text']};
                    font-size: 11px;
                }}
                QProgressBar::chunk {{
                    background-color: {next_tier_color};
                    border-radius: 3px;
                }}
            """)
            layout.addWidget(next_bar)

        # Show champions likely never won with (lifetime) for Jack of All Champs
        not_won = ca.champions_not_won_with_lifetime()
        not_won_count = total_champs - won_count

        if not_won:
            remaining_label = QLabel(
                f"Likely never won with ({not_won_count} champions, "
                f"sorted by lowest mastery -- most likely candidates):"
            )
        else:
            remaining_label = QLabel(f"All {total_champs} champions won with!")
        remaining_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none;")
        remaining_label.setWordWrap(True)
        layout.addWidget(remaining_label)

        for c in not_won[:30]:
            row = QHBoxLayout()

            name = QLabel(c['champion'])
            name.setFixedWidth(120)
            name.setStyleSheet(f"font-weight: bold; border: none;")
            row.addWidget(name)

            level = QLabel(f"M{c['mastery_level']}")
            level.setFixedWidth(40)
            level.setStyleSheet(f"color: {COLORS['gold']}; border: none;")
            row.addWidget(level)

            pts = QLabel(f"{c['mastery_points']:,} pts")
            pts.setFixedWidth(90)
            pts.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
            row.addWidget(pts)

            tags = QLabel(", ".join(c['tags']))
            tags.setStyleSheet(f"color: {COLORS['blue']}; font-size: 11px; border: none;")
            row.addWidget(tags)

            row.addStretch()
            layout.addLayout(row)

        self.layout_main.addWidget(card)

    def _add_roadmap(self, ca):
        roadmap = ca.challenge_roadmap(top_n=8)
        if not roadmap:
            return

        card, layout = self._card("Challenge Roadmap (Fastest Path)")

        desc = QLabel("Easiest challenges to level up next, sorted by effort:")
        desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none;")
        layout.addWidget(desc)

        for c in roadmap:
            row_widget = QFrame()
            row_widget.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_main']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 4px;
                    padding: 2px;
                }}
            """)
            row_layout = QVBoxLayout(row_widget)
            row_layout.setContentsMargins(10, 6, 10, 6)
            row_layout.setSpacing(3)

            current_color = RANK_COLORS.get(c['current_level'], COLORS['text_dim'])
            next_color = RANK_COLORS.get(c['next_tier'], COLORS['gold'])

            top = QHBoxLayout()

            name = QLabel(c['name'][:35])
            name.setFixedWidth(220)
            name.setStyleSheet(f"font-weight: bold; border: none;")
            top.addWidget(name)

            tier = QLabel(f"{c['current_level']} -> {c['next_tier']}")
            tier.setFixedWidth(160)
            tier.setStyleSheet(f"color: {next_color}; font-weight: bold; border: none;")
            top.addWidget(tier)

            remaining = QLabel(f"{int(c['remaining'])} to go")
            remaining.setFixedWidth(80)
            remaining.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
            top.addWidget(remaining)

            points = QLabel(f"+{c['points_gain']}pts")
            points.setFixedWidth(60)
            points.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; font-size: 11px; border: none;")
            top.addWidget(points)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(min(int(c['progress_pct']), 100))
            bar.setFormat(f"{c['progress_pct']:.0f}%")
            bar.setFixedHeight(16)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {COLORS['bg_dark']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 3px;
                    text-align: center;
                    color: {COLORS['text']};
                    font-size: 10px;
                }}
                QProgressBar::chunk {{
                    background-color: {next_color};
                    border-radius: 2px;
                }}
            """)
            top.addWidget(bar)
            row_layout.addLayout(top)

            # Description
            desc_text = c.get('description', '')
            if desc_text:
                desc = QLabel(desc_text)
                desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; border: none;")
                desc.setWordWrap(True)
                row_layout.addWidget(desc)

            layout.addWidget(row_widget)

        self.layout_main.addWidget(card)

    def _add_weekly_goals(self, ca):
        goals = ca.weekly_goals()
        if not goals:
            return

        card, layout = self._card("Weekly Goals")

        urgency_colors = {
            'easy': COLORS['green'],
            'medium': COLORS['orange'],
            'long_term': COLORS['text_dim'],
        }

        for g in goals:
            goal_widget = QVBoxLayout()
            goal_widget.setSpacing(2)

            row = QHBoxLayout()
            urgency_color = urgency_colors.get(g['urgency'], COLORS['text'])
            dot = QLabel("*")
            dot.setFixedWidth(15)
            dot.setStyleSheet(f"color: {urgency_color}; font-size: 20px; font-weight: bold; border: none;")
            row.addWidget(dot)

            name = QLabel(g['challenge'])
            name.setFixedWidth(200)
            name.setStyleSheet(f"font-weight: bold; border: none;")
            row.addWidget(name)

            suggestion = QLabel(g['suggestion'])
            suggestion.setStyleSheet(f"color: {urgency_color}; font-size: 12px; border: none;")
            row.addWidget(suggestion)

            row.addStretch()
            goal_widget.addLayout(row)

            desc_text = g.get('description', '')
            if desc_text:
                desc = QLabel(f"    {desc_text}")
                desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; border: none;")
                desc.setWordWrap(True)
                goal_widget.addWidget(desc)

            layout.addLayout(goal_widget)

        self.layout_main.addWidget(card)

    def _add_premade_challenges(self, ca):
        self._challenge_analyzer = ca  # Store for generate button callbacks
        challenges = ca.premade_team_comp_challenges()
        if not challenges:
            return

        # Split into ability-themed and region-themed
        ability = [c for c in challenges if c['id'] < 303500]
        region = [c for c in challenges if c['id'] >= 303500]

        if ability:
            card, layout = self._card("Premade 5: Ability Themes (Harmony)")

            desc = QLabel("Win as a premade 5 with specific champion ability types:")
            desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none;")
            layout.addWidget(desc)

            for c in ability:
                self._add_premade_row(layout, c)

            self.layout_main.addWidget(card)

        if region:
            card, layout = self._card("Premade 5: Region Teams (Globetrotter)")

            desc = QLabel("Win as a premade 5 with champions from the same region:")
            desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none;")
            layout.addWidget(desc)

            for c in region:
                self._add_premade_row(layout, c)

            self.layout_main.addWidget(card)

    def _add_premade_row(self, layout, c):
        # Challenge frame
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame#premade_row {{
                background-color: {COLORS['bg_main']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
            }}
        """)
        frame.setObjectName("premade_row")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(10, 6, 10, 6)
        frame_layout.setSpacing(4)

        # Header row: tier, name, description, value, progress
        row = QHBoxLayout()

        level = c['current_level']
        level_color = RANK_COLORS.get(level, COLORS['text_dim'])

        tier_lbl = QLabel(level[:3] if level != 'NONE' else '--')
        tier_lbl.setFixedWidth(30)
        tier_lbl.setStyleSheet(f"color: {level_color}; font-weight: bold; font-size: 10px; border: none;")
        row.addWidget(tier_lbl)

        name = QLabel(c['name'])
        name.setFixedWidth(200)
        name.setStyleSheet(f"font-weight: bold; border: none;")
        row.addWidget(name)

        desc = QLabel(c['description'])
        desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
        row.addWidget(desc)

        val = QLabel(f"{c['current_value']}W")
        val.setFixedWidth(40)
        val_color = COLORS['green'] if c['current_value'] > 0 else COLORS['text_dim']
        val.setStyleSheet(f"color: {val_color}; font-weight: bold; border: none;")
        row.addWidget(val)

        if c['next_threshold']:
            bar = QProgressBar()
            bar.setRange(0, int(c['next_threshold']))
            bar.setValue(int(c['current_value']))
            next_color = RANK_COLORS.get(c['next_tier'], COLORS['gold'])
            bar.setFormat(f"{c['current_value']}/{int(c['next_threshold'])} to {c['next_tier']}")
            bar.setFixedHeight(16)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {COLORS['bg_dark']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 3px;
                    text-align: center;
                    color: {COLORS['text']};
                    font-size: 9px;
                }}
                QProgressBar::chunk {{
                    background-color: {next_color};
                    border-radius: 2px;
                }}
            """)
            row.addWidget(bar)
        else:
            maxed = QLabel("MAXED")
            maxed.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; font-size: 10px; border: none;")
            row.addWidget(maxed)

        frame_layout.addLayout(row)

        # Champion pool (collapsed text)
        champions = c.get('champions', [])
        if champions:
            pool_lbl = QLabel(f"Champions: {', '.join(champions)}")
            pool_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; border: none;")
            pool_lbl.setWordWrap(True)
            frame_layout.addWidget(pool_lbl)

        # Generate Comp button + result area
        if champions or c['id'] == 303408:
            gen_btn = QPushButton("Generate Comp")
            gen_btn.setFixedWidth(130)
            gen_btn.setFixedHeight(28)
            gen_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['blue']};
                    color: white;
                    font-weight: bold;
                    font-size: 11px;
                    padding: 4px 12px;
                    border-radius: 4px;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: #5C6BC0;
                }}
            """)
            frame_layout.addWidget(gen_btn)

            # Container for the generated comp display
            comp_container = QWidget()
            comp_container.setVisible(False)
            comp_container_layout = QHBoxLayout(comp_container)
            comp_container_layout.setContentsMargins(0, 4, 0, 0)
            comp_container_layout.setSpacing(12)
            frame_layout.addWidget(comp_container)

            def on_generate(checked, cid=c['id'], container=comp_container, clayout=comp_container_layout):
                if not hasattr(self, '_challenge_analyzer'):
                    return
                comp = self._challenge_analyzer.generate_random_comp(cid)
                if not comp:
                    return

                # Clear previous comp
                while clayout.count():
                    child = clayout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()

                class_label = comp[0].get('label', '') if comp else ''
                if class_label:
                    cls_lbl = QLabel(class_label)
                    cls_lbl.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; font-size: 11px; border: none;")
                    clayout.addWidget(cls_lbl)

                role_order = ['TOP', 'JUNGLE', 'MID', 'BOT', 'SUPPORT']
                comp_by_role = {r['role']: r['champion'] for r in comp}
                dd = self._challenge_analyzer.dd

                for role in role_order:
                    champ_name = comp_by_role.get(role)
                    if not champ_name:
                        continue

                    slot = QVBoxLayout()
                    slot.setSpacing(1)
                    slot.setContentsMargins(0, 0, 0, 0)

                    # Role label
                    role_lbl = QLabel(role)
                    role_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    role_lbl.setStyleSheet(f"color: {COLORS['gold']}; font-size: 9px; font-weight: bold; border: none;")
                    slot.addWidget(role_lbl)

                    # Champion icon
                    icon_lbl = QLabel()
                    icon_lbl.setFixedSize(36, 36)
                    icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    icon_lbl.setStyleSheet("border: none;")
                    if dd:
                        icon_path = dd.get_champion_icon_path(champ_name)
                        if icon_path:
                            px = QPixmap(icon_path)
                            if not px.isNull():
                                icon_lbl.setPixmap(px.scaled(
                                    32, 32,
                                    Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation
                                ))
                    slot.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

                    # Champion name
                    name_lbl = QLabel(champ_name)
                    name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    name_lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: 9px; border: none;")
                    slot.addWidget(name_lbl)

                    slot_widget = QWidget()
                    slot_widget.setLayout(slot)
                    slot_widget.setFixedWidth(70)
                    clayout.addWidget(slot_widget)

                clayout.addStretch()
                container.setVisible(True)

            gen_btn.clicked.connect(on_generate)

        layout.addWidget(frame)

    def _add_in_game_tips(self, ca):
        tips = ca.get_in_game_tips()
        if not tips:
            return

        card, layout = self._card("In-Game Tips")

        desc = QLabel("Keep these in mind during your next game:")
        desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none;")
        layout.addWidget(desc)

        for tip in tips[:10]:
            tip_frame = QFrame()
            tip_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_main']};
                    border-left: 3px solid {COLORS['gold']};
                    border-radius: 4px;
                    padding: 4px;
                }}
            """)
            tip_layout = QVBoxLayout(tip_frame)
            tip_layout.setContentsMargins(12, 8, 12, 8)
            tip_layout.setSpacing(4)

            header = QHBoxLayout()
            name = QLabel(tip['challenge_name'])
            name.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; border: none;")
            header.addWidget(name)

            progress = QLabel(tip['progress'])
            progress.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
            header.addWidget(progress)

            header.addStretch()
            tip_layout.addLayout(header)

            tip_text = QLabel(tip['tip'])
            tip_text.setStyleSheet(f"color: {COLORS['text']}; font-size: 13px; border: none;")
            tip_text.setWordWrap(True)
            tip_layout.addWidget(tip_text)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(min(int(tip['progress_pct']), 100))
            bar.setFixedHeight(12)
            tip_layout.addWidget(bar)

            layout.addWidget(tip_frame)

        self.layout_main.addWidget(card)
