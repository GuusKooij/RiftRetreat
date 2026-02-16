"""Champions page: Champion pool table, recommender, mastery, matchups, duo, consistency, bingo."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QProgressBar,
    QGridLayout
)
from PyQt6.QtCore import Qt

from src.gui.theme import COLORS

# Bingo status colors
BINGO_COLORS = {
    'mastery_10': '#9D48E0',   # Purple (master)
    'mastery_5': '#576BCE',    # Diamond blue
    'won': '#00C853',          # Green
    'played': '#FF9800',       # Orange
    'owned': '#7B818C',        # Gray
    'never_played': '#1A1B26', # Dark bg
}


class ChampionsPage(QWidget):
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

    def update_data(self, champion_analyzer, stats_analyzer=None):
        while self.layout_main.count():
            child = self.layout_main.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Champion pool analysis (new section)
        self._add_pool_analysis(champion_analyzer)

        # Recommendations
        self._add_recommendations(champion_analyzer)

        # Personal tier list (new section)
        self._add_personal_tier_list(champion_analyzer)

        # Champion pool table
        self._add_pool_table(champion_analyzer)

        # Consistency scores
        self._add_consistency(champion_analyzer)

        # Enemy matchups
        if stats_analyzer:
            self._add_matchups(stats_analyzer)

        # Champion bingo grid
        self._add_bingo(champion_analyzer)

        # Mastery overview
        self._add_mastery_overview(champion_analyzer)

        self.layout_main.addStretch()

    def _add_recommendations(self, ca):
        recs = ca.recommendations()

        if recs['prioritize']:
            card, layout = self._card(f"Prioritize ({len(recs['prioritize'])} champions)")
            desc = QLabel("These champions have 55%+ WR over 3+ games -- your best picks!")
            desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none;")
            layout.addWidget(desc)

            for c in recs['prioritize']:
                row = QHBoxLayout()
                name = QLabel(f"{c['champion']}")
                name.setFixedWidth(120)
                name.setStyleSheet(f"color: {COLORS['green']}; font-weight: bold; font-size: 14px; border: none;")
                row.addWidget(name)

                wr = QLabel(f"{c['winrate']}% WR")
                wr.setFixedWidth(80)
                wr.setStyleSheet(f"color: {COLORS['green']}; border: none;")
                row.addWidget(wr)

                info = QLabel(f"{c['games']}G  KDA {c['avg_kda']}  {c['main_role']}")
                info.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
                row.addWidget(info)

                row.addStretch()
                layout.addLayout(row)

            self.layout_main.addWidget(card)

        if recs['drop']:
            card, layout = self._card(f"Consider Dropping ({len(recs['drop'])} champions)")
            desc = QLabel("These champions have below 45% WR over 3+ games.")
            desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none;")
            layout.addWidget(desc)

            for c in recs['drop']:
                row = QHBoxLayout()
                name = QLabel(f"{c['champion']}")
                name.setFixedWidth(120)
                name.setStyleSheet(f"color: {COLORS['red']}; font-weight: bold; font-size: 14px; border: none;")
                row.addWidget(name)

                wr = QLabel(f"{c['winrate']}% WR")
                wr.setFixedWidth(80)
                wr.setStyleSheet(f"color: {COLORS['red']}; border: none;")
                row.addWidget(wr)

                info = QLabel(f"{c['games']}G  KDA {c['avg_kda']}  {c['main_role']}")
                info.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
                row.addWidget(info)

                row.addStretch()
                layout.addLayout(row)

            self.layout_main.addWidget(card)

    def _add_pool_table(self, ca):
        pool = ca.champion_pool()
        if not pool:
            return

        card, layout = self._card(f"Champion Pool ({len(pool)} champions played)")

        table = QTableWidget()
        table.setAlternatingRowColors(True)
        columns = ['Champion', 'Games', 'WR%', 'KDA', 'CS/min', 'Damage', 'KP%', 'Role', 'Mastery']
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.setRowCount(len(pool))
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSortingEnabled(True)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, len(columns)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        for row, c in enumerate(pool):
            rating_color = COLORS.get(c['rating'], COLORS['text'])

            name_item = QTableWidgetItem(c['champion'])
            name_item.setForeground(Qt.GlobalColor.white)
            table.setItem(row, 0, name_item)

            table.setItem(row, 1, self._num_item(c['games']))

            wr_item = QTableWidgetItem(f"{c['winrate']}%")
            wr_item.setData(Qt.ItemDataRole.UserRole, c['winrate'])
            table.setItem(row, 2, wr_item)

            table.setItem(row, 3, QTableWidgetItem(f"{c['avg_kda']}"))
            table.setItem(row, 4, QTableWidgetItem(f"{c['avg_cs_per_min']}"))
            table.setItem(row, 5, self._num_item(int(c['avg_damage'])))
            table.setItem(row, 6, QTableWidgetItem(f"{c['avg_kp']}%"))
            role_display = 'SUPPORT' if c['main_role'] == 'UTILITY' else c['main_role']
            table.setItem(row, 7, QTableWidgetItem(role_display))
            table.setItem(row, 8, QTableWidgetItem(f"M{c['mastery_level']}"))

        table.setMinimumHeight(min(len(pool) * 30 + 40, 500))
        layout.addWidget(table)
        self.layout_main.addWidget(card)

    def _num_item(self, val) -> QTableWidgetItem:
        item = QTableWidgetItem()
        item.setData(Qt.ItemDataRole.DisplayRole, val)
        return item

    def _add_consistency(self, ca):
        scores = ca.consistency_scores()
        if not scores:
            return

        card, layout = self._card("Consistency Ratings (3+ games)")

        desc = QLabel("Reliable = consistent performance, Coinflip = high variance:")
        desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none;")
        layout.addWidget(desc)

        for s in scores[:12]:
            row = QHBoxLayout()

            name = QLabel(s['champion'])
            name.setFixedWidth(100)
            name.setStyleSheet(f"font-weight: bold; border: none;")
            row.addWidget(name)

            label_colors = {'reliable': COLORS['green'], 'coinflip': COLORS['red'], 'moderate': COLORS['orange']}
            lbl = QLabel(s['label'].upper())
            lbl.setFixedWidth(80)
            lbl.setStyleSheet(f"color: {label_colors.get(s['label'], COLORS['text'])}; font-weight: bold; font-size: 11px; border: none;")
            row.addWidget(lbl)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(s['consistency'])
            bar.setFormat(f"{s['consistency']}%")
            bar.setFixedHeight(16)

            bar_color = label_colors.get(s['label'], COLORS['gold'])
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
                    background-color: {bar_color};
                    border-radius: 2px;
                }}
            """)
            row.addWidget(bar)

            info = QLabel(f"{s['games']}G  {s['winrate']}% WR")
            info.setFixedWidth(100)
            info.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
            row.addWidget(info)

            layout.addLayout(row)

        self.layout_main.addWidget(card)

    def _add_matchups(self, stats):
        by_role = stats.enemy_matchups_by_role()
        if not by_role:
            return

        card, layout = self._card("Matchups by Lane (vs Lane Opponent)")

        role_order = ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'SUPPORT']
        for role in role_order:
            matchups = by_role.get(role, [])
            with_enough = [m for m in matchups if m['games'] >= 2]
            if not with_enough:
                continue

            # Sort by winrate descending
            with_enough.sort(key=lambda x: x['winrate'], reverse=True)

            role_header = QLabel(f"{role}")
            role_header.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; font-size: 13px; margin-top: 6px; border: none;")
            layout.addWidget(role_header)

            for m in with_enough:
                row = QHBoxLayout()
                name = QLabel(f"vs {m['enemy_champion']}")
                name.setFixedWidth(160)
                name.setStyleSheet(f"font-weight: bold; border: none;")
                row.addWidget(name)
                wr = QLabel(f"{m['winrate']}% WR")
                wr.setFixedWidth(80)
                wr_color = COLORS['green'] if m['winrate'] >= 50 else COLORS['red']
                wr.setStyleSheet(f"color: {wr_color}; border: none;")
                row.addWidget(wr)
                games = QLabel(f"({m['wins']}W {m['losses']}L)")
                games.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
                row.addWidget(games)
                row.addStretch()
                layout.addLayout(row)

        self.layout_main.addWidget(card)

    def _add_bingo(self, ca):
        summary = ca.bingo_summary()
        bingo = ca.champion_bingo()

        card, layout = self._card(f"Champion Collection ({summary['collected']}/{summary['total_champions']})")

        # Summary bar
        bar = QProgressBar()
        bar.setRange(0, summary['total_champions'])
        bar.setValue(summary['collected'])
        bar.setFormat(f"{summary['completion_pct']}% collected")
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

        # Breakdown
        breakdown = QLabel(
            f"M10+: {summary['mastery_10']}  |  "
            f"M5+: {summary['mastery_5']}  |  "
            f"Won: {summary['won']}  |  "
            f"Played: {summary['played']}  |  "
            f"Owned: {summary['owned']}  |  "
            f"Never: {summary['never_played']}"
        )
        breakdown.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
        layout.addWidget(breakdown)

        # Legend
        legend = QHBoxLayout()
        for status, color in BINGO_COLORS.items():
            lbl = QLabel(f"  {status.replace('_', ' ').title()}  ")
            lbl.setStyleSheet(f"background-color: {color}; color: white; font-size: 9px; border-radius: 3px; padding: 2px 4px; border: none;")
            legend.addWidget(lbl)
        legend.addStretch()
        layout.addLayout(legend)

        # Grid of champions (compact)
        grid = QGridLayout()
        grid.setSpacing(2)

        cols = 14
        for i, champ in enumerate(bingo):
            col = i % cols
            row_idx = i // cols

            block = QLabel(champ['champion'][:3])
            block.setFixedSize(32, 22)
            block.setAlignment(Qt.AlignmentFlag.AlignCenter)

            bg = BINGO_COLORS.get(champ['status'], COLORS['bg_dark'])
            border = COLORS['border']
            if champ['status'] == 'mastery_10':
                border = '#9D48E0'

            block.setStyleSheet(f"""
                background-color: {bg};
                color: white;
                font-size: 8px;
                font-weight: bold;
                border: 1px solid {border};
                border-radius: 2px;
            """)
            block.setToolTip(f"{champ['champion']} - M{champ['mastery_level']} ({champ['mastery_points']:,} pts) - {champ['status']}")
            grid.addWidget(block, row_idx, col)

        layout.addLayout(grid)
        self.layout_main.addWidget(card)

    def _add_mastery_overview(self, ca):
        mastery = ca.mastery_overview(top_n=15)
        if not mastery:
            return

        card, layout = self._card("Mastery Overview (Top 15)")

        for m in mastery:
            row = QHBoxLayout()

            name = QLabel(f"{m['champion']}")
            name.setFixedWidth(120)
            name.setStyleSheet(f"font-weight: bold; border: none;")
            row.addWidget(name)

            level = QLabel(f"M{m['mastery_level']}")
            level.setFixedWidth(40)
            level.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; border: none;")
            row.addWidget(level)

            points = QLabel(f"{m['mastery_points']:,} pts")
            points.setFixedWidth(100)
            points.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
            row.addWidget(points)

            # Season stats
            if m['season_games'] > 0:
                wr_color = COLORS['green'] if m['season_wr'] >= 50 else COLORS['red']
                season = QLabel(f"{m['season_games']}G {m['season_wr']}% WR")
                season.setStyleSheet(f"color: {wr_color}; border: none;")
            else:
                season = QLabel("Not played")
                season.setStyleSheet(f"color: {COLORS['text_dim']}; font-style: italic; border: none;")
            row.addWidget(season)

            row.addStretch()
            layout.addLayout(row)

        self.layout_main.addWidget(card)

    def _add_pool_analysis(self, ca):
        """Add champion pool analysis: role diversity, one-trick detection, comfort picks."""
        from src.analytics.champion_pool import ChampionPoolAnalyzer

        pool = ChampionPoolAnalyzer(ca.matches)

        card, layout = self._card("Champion Pool Analysis")

        # Role Diversity
        diversity = pool.get_role_diversity_score()
        div_section = QLabel("🎭 Role Diversity")
        div_section.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; font-size: 14px; border: none; margin-top: 4px;")
        layout.addWidget(div_section)

        div_row = QHBoxLayout()

        # Diversity score with color coding
        score_color = COLORS['green'] if diversity['diversity_score'] >= 50 else COLORS['orange'] if diversity['diversity_score'] >= 25 else COLORS['red']
        score_label = QLabel(f"{diversity['diversity_score']:.0f}/100")
        score_label.setStyleSheet(f"color: {score_color}; font-size: 24px; font-weight: bold; border: none;")
        div_row.addWidget(score_label)

        rating_label = QLabel(f"{diversity['rating']}")
        rating_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 14px; border: none;")
        div_row.addWidget(rating_label)

        div_row.addStretch()
        layout.addLayout(div_row)

        # Role distribution
        if diversity['role_distribution']:
            dist_label = QLabel("Role Distribution:")
            dist_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none; margin-top: 4px;")
            layout.addWidget(dist_label)

            dist_row = QHBoxLayout()
            for role, games in sorted(diversity['role_distribution'].items(), key=lambda x: x[1], reverse=True):
                display_role = 'SUPPORT' if role == 'UTILITY' else role
                role_widget = QLabel(f"{display_role}: {games}G")
                role_widget.setStyleSheet(f"color: {COLORS['blue']}; font-size: 11px; border: none;")
                dist_row.addWidget(role_widget)
            dist_row.addStretch()
            layout.addLayout(dist_row)

        # One-Trick Detection
        one_tricks = pool.detect_one_tricks()
        ot_section = QLabel("🎯 One-Trick Status")
        ot_section.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; font-size: 14px; border: none; margin-top: 12px;")
        layout.addWidget(ot_section)

        if one_tricks['is_one_trick']:
            for ot in one_tricks['one_trick_champions']:
                ot_row = QHBoxLayout()

                champ_label = QLabel(f"{ot['champion']}")
                champ_label.setFixedWidth(120)
                champ_label.setStyleSheet(f"color: {COLORS['purple']}; font-weight: bold; font-size: 14px; border: none;")
                ot_row.addWidget(champ_label)

                pick_label = QLabel(f"{ot['pick_rate']:.1f}% pick rate")
                pick_label.setFixedWidth(120)
                pick_label.setStyleSheet(f"color: {COLORS['text']}; border: none;")
                ot_row.addWidget(pick_label)

                wr_color = COLORS['green'] if ot['winrate'] >= 50 else COLORS['red']
                wr_label = QLabel(f"{ot['winrate']}% WR")
                wr_label.setFixedWidth(80)
                wr_label.setStyleSheet(f"color: {wr_color}; border: none;")
                ot_row.addWidget(wr_label)

                games_label = QLabel(f"({ot['games']}G {ot['wins']}W {ot['losses']}L)")
                games_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
                ot_row.addWidget(games_label)

                ot_row.addStretch()
                layout.addLayout(ot_row)
        else:
            no_ot = QLabel("Not a one-trick — you play multiple champions")
            no_ot.setStyleSheet(f"color: {COLORS['text_dim']}; font-style: italic; border: none;")
            layout.addWidget(no_ot)

        # Comfort Picks
        comfort = pool.get_comfort_picks()
        comfort_section = QLabel("✨ Comfort Picks (55%+ WR)")
        comfort_section.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; font-size: 14px; border: none; margin-top: 12px;")
        layout.addWidget(comfort_section)

        if comfort['comfort_picks']:
            for pick in comfort['comfort_picks'][:10]:  # Top 10
                pick_row = QHBoxLayout()

                champ = QLabel(pick['champion'])
                champ.setFixedWidth(120)
                champ.setStyleSheet(f"color: {COLORS['green']}; font-weight: bold; border: none;")
                pick_row.addWidget(champ)

                wr = QLabel(f"{pick['winrate']}% WR")
                wr.setFixedWidth(80)
                wr.setStyleSheet(f"color: {COLORS['green']}; border: none;")
                pick_row.addWidget(wr)

                games = QLabel(f"({pick['games']}G {pick['wins']}W {pick['losses']}L)")
                games.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
                pick_row.addWidget(games)

                pick_row.addStretch()
                layout.addLayout(pick_row)
        else:
            no_comfort = QLabel("No comfort picks yet (need 5+ games with 55%+ WR)")
            no_comfort.setStyleSheet(f"color: {COLORS['text_dim']}; font-style: italic; border: none;")
            layout.addWidget(no_comfort)

        self.layout_main.addWidget(card)

    def _add_personal_tier_list(self, ca):
        """Add personal tier list based on performance."""
        from src.analytics.champion_pool import ChampionPoolAnalyzer

        pool = ChampionPoolAnalyzer(ca.matches)

        tier_data = pool.get_personal_tier_list(min_games=3, mastery_data=ca.mastery, dd=ca.dd, include_unplayed=True)

        card, layout = self._card("Your Personal Tier List")

        desc = QLabel("Based on your performance (min 3 games) + high mastery champions — Your WR | Games | KDA | Mastery")
        desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none;")
        layout.addWidget(desc)

        tier_colors = {
            'S': '#FFD700',  # Gold
            'A': '#00C853',  # Green
            'B': '#0AC8B9',  # Cyan
            'C': '#FF9800',  # Orange
            'D': '#E84057',  # Red
            'Potential': '#9D48E0',  # Purple
        }

        tier_thresholds = {
            'S': '65%+ WR',
            'A': '55-64.9% WR',
            'B': '50-54.9% WR',
            'C': '45-49.9% WR',
            'D': '<45% WR',
            'Potential': 'High mastery (M5+) or <3 games',
        }

        for tier in ['S', 'A', 'B', 'C', 'D', 'Potential']:
            tier_champs = tier_data['tiers'][tier]
            if not tier_champs:
                continue

            tier_label = QLabel(f"Tier {tier} — {tier_thresholds[tier]} ({len(tier_champs)} champions)")
            tier_label.setStyleSheet(f"color: {tier_colors[tier]}; font-weight: bold; font-size: 14px; border: none; margin-top: 8px;")
            layout.addWidget(tier_label)

            # Show champs in rows with more detail
            for champ in tier_champs[:20]:  # Top 20 per tier
                champ_row = QHBoxLayout()

                # Champion name
                name_label = QLabel(champ['champion'])
                name_label.setFixedWidth(120)
                name_label.setStyleSheet(f"color: {COLORS['text_bright']}; font-weight: bold; font-size: 12px; border: none;")
                champ_row.addWidget(name_label)

                # Your WR
                wr_label = QLabel(f"{champ['winrate']}%")
                wr_label.setFixedWidth(50)
                wr_label.setStyleSheet(f"color: {tier_colors[tier]}; font-weight: bold; font-size: 12px; border: none;")
                champ_row.addWidget(wr_label)

                # Games
                games_label = QLabel(f"{champ['games']}G")
                games_label.setFixedWidth(40)
                games_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
                champ_row.addWidget(games_label)

                # KDA
                kda_label = QLabel(f"KDA {champ['kda']}")
                kda_label.setFixedWidth(75)
                kda_label.setStyleSheet(f"color: {COLORS['blue']}; font-size: 11px; border: none;")
                champ_row.addWidget(kda_label)

                # Mastery
                if champ['mastery_level'] > 0:
                    mastery_label = QLabel(f"M{champ['mastery_level']} ({champ['mastery_points']:,})")
                    mastery_label.setStyleSheet(f"color: {COLORS['purple']}; font-size: 11px; border: none;")
                else:
                    mastery_label = QLabel("No mastery")
                    mastery_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-style: italic; font-size: 10px; border: none;")
                champ_row.addWidget(mastery_label)

                champ_row.addStretch()
                layout.addLayout(champ_row)

        self.layout_main.addWidget(card)
