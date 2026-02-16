"""Dashboard page: Profile, key stats, win conditions, recent form, tilt indicator."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QProgressBar, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from src.gui.theme import COLORS, RANK_COLORS


class DashboardPage(QWidget):
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

    def update_data(self, profile, ranked_stats, stats_analyzer, tilt_detector, climb_history,
                    season_stats=None, season_tilt=None):
        # Use season stats where available, fall back to all-time
        s_stats = season_stats or stats_analyzer
        s_tilt = season_tilt or tilt_detector

        # Clear existing widgets
        while self.layout_main.count():
            child = self.layout_main.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # --- Profile Header ---
        self._add_profile_header(profile, ranked_stats)

        # --- Season Stats ---
        self._add_stat_cards(s_stats, title="Season Overview")

        # --- All-Time Stats ---
        if season_stats and stats_analyzer.overall()['games'] != s_stats.overall()['games']:
            self._add_stat_cards(stats_analyzer, title="All-Time Overview")

        # --- Advanced Stats (season) ---
        self._add_advanced_stats(s_stats, ranked_stats)

        # --- Win Rate Calendar (season) ---
        self._add_win_rate_calendar(s_stats)

        # --- Win Conditions (season) ---
        self._add_win_conditions(s_stats)

        # --- Role Breakdown (season) ---
        self._add_role_breakdown(s_stats)

        # --- Duo Partners (all-time - more data = better) ---
        self._add_duo_partners(stats_analyzer)

        # --- Recent Form (season) ---
        self._add_recent_form(s_stats, s_tilt)

        # --- Tilt Analysis (season) ---
        self._add_tilt_analysis(s_tilt)

        # --- Climb Progress ---
        if climb_history:
            self._add_climb_progress(climb_history)

        self.layout_main.addStretch()

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

    def _stat_label(self, value, label, color=None) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(2)

        val = QLabel(str(value))
        val.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color or COLORS['text_bright']};")
        val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(val)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"font-size: 11px; color: {COLORS['text_dim']};")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(lbl)

        return w

    def _add_profile_header(self, profile, ranked_stats):
        card, layout = self._card(f"{profile.get('game_name', '?')}#{profile.get('tag_line', '?')}")

        info = QHBoxLayout()
        info.addWidget(self._stat_label(profile.get('summoner_level', 0), "Level"))

        for entry in ranked_stats:
            queue = "Solo/Duo" if entry['queueType'] == 'RANKED_SOLO_5x5' else "Flex"
            tier = entry.get('tier', '')
            rank = entry.get('rank', '')
            lp = entry.get('leaguePoints', 0)
            wins = entry.get('wins', 0)
            losses = entry.get('losses', 0)
            wr = round(wins / max(wins + losses, 1) * 100, 1)

            rank_color = RANK_COLORS.get(tier, COLORS['text'])
            info.addWidget(self._stat_label(
                f"{tier} {rank}", f"{queue} | {lp}LP | {wr}% WR", rank_color
            ))

        layout.addLayout(info)
        self.layout_main.addWidget(card)

    def _add_stat_cards(self, stats, title="Season Overview"):
        overall = stats.overall()

        card, layout = self._card(title)

        grid = QGridLayout()
        grid.setSpacing(12)

        wr_color = COLORS['green'] if overall['winrate'] >= 50 else COLORS['red']
        grid.addWidget(self._stat_label(f"{overall['winrate']}%", f"Winrate ({overall['wins']}W {overall['losses']}L)", wr_color), 0, 0)
        grid.addWidget(self._stat_label(f"{overall['avg_kda']}", f"KDA ({overall['avg_kills']}/{overall['avg_deaths']}/{overall['avg_assists']})", COLORS['blue']), 0, 1)
        grid.addWidget(self._stat_label(f"{overall['avg_cs_per_min']}", "CS/min", COLORS['gold']), 0, 2)
        grid.addWidget(self._stat_label(f"{overall['avg_vision_score']}", "Vision Score", COLORS['purple']), 0, 3)
        grid.addWidget(self._stat_label(f"{overall['avg_kp']}%", "Kill Participation", COLORS['orange']), 0, 4)
        grid.addWidget(self._stat_label(f"{overall['games']}", "Total Games"), 0, 5)

        layout.addLayout(grid)

        # Queue comparison
        queues = stats.by_queue()
        q_layout = QHBoxLayout()
        for name, data in queues.items():
            if data['games']:
                label = "Solo/Duo" if name == 'solo_duo' else "Flex"
                wr_color = COLORS['green'] if data['winrate'] >= 50 else COLORS['red']
                q_layout.addWidget(self._stat_label(
                    f"{data['winrate']}%",
                    f"{label} ({data['games']}G, KDA {data['avg_kda']})",
                    wr_color
                ))
        layout.addLayout(q_layout)

        self.layout_main.addWidget(card)

    def _add_advanced_stats(self, stats, ranked_stats):
        """Display advanced statistics: first blood, KP%, GPM/CSPM, damage, comebacks, promotion."""
        from PyQt6.QtWidgets import QPushButton
        from src.analytics.advanced_stats import AdvancedStatsAnalyzer

        adv = AdvancedStatsAnalyzer(stats.matches)

        card, layout = self._card("Advanced Statistics")

        # Add expand/collapse button
        toggle_btn = QPushButton("▼ Show Details")
        toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_card_hover']};
                color: {COLORS['gold']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {COLORS['gold_dark']};
                color: {COLORS['text_bright']};
            }}
        """)
        layout.addWidget(toggle_btn)

        # Create collapsible content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 8, 0, 0)
        content_layout.setSpacing(8)
        content_widget.setVisible(False)  # Hidden by default

        # Toggle function
        def toggle_details():
            is_visible = content_widget.isVisible()
            content_widget.setVisible(not is_visible)
            toggle_btn.setText("▲ Hide Details" if not is_visible else "▼ Show Details")

        toggle_btn.clicked.connect(toggle_details)

        # --- First Blood Stats ---
        fb_stats = adv.get_first_blood_stats()
        if fb_stats['total_games'] > 0:
            fb_section = QLabel("📍 First Blood Statistics")
            fb_section.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; font-size: 14px; border: none; margin-top: 8px;")
            content_layout.addWidget(fb_section)

            fb_row = QHBoxLayout()
            fb_row.addWidget(self._stat_label(
                f"{fb_stats['first_blood_rate']:.1f}%",
                f"First Blood Rate ({fb_stats['first_blood_count']}/{fb_stats['total_games']})",
                COLORS['red']
            ))
            fb_row.addWidget(self._stat_label(
                f"{fb_stats['first_blood_winrate']:.1f}%",
                "WR when getting FB",
                COLORS['green'] if fb_stats['first_blood_winrate'] >= 50 else COLORS['red']
            ))
            content_layout.addLayout(fb_row)

        # --- Kill Participation Stats ---
        kp_stats = adv.get_kp_stats()
        if kp_stats['average_kp'] > 0:
            kp_section = QLabel("🎯 Kill Participation (KP%)")
            kp_section.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; font-size: 14px; border: none; margin-top: 12px;")
            content_layout.addWidget(kp_section)

            kp_row = QHBoxLayout()
            kp_row.addWidget(self._stat_label(
                f"{kp_stats['average_kp']:.1f}%",
                "Average KP%",
                COLORS['orange']
            ))
            kp_row.addWidget(self._stat_label(
                f"{kp_stats['max_kp']:.1f}%",
                "Highest KP%",
                COLORS['green']
            ))
            kp_row.addWidget(self._stat_label(
                f"{kp_stats['min_kp']:.1f}%",
                "Lowest KP%",
                COLORS['text_dim']
            ))
            content_layout.addLayout(kp_row)

            # KP by role
            kp_by_role = adv.get_kp_by_role()
            if kp_by_role:
                role_label = QLabel("KP% by Role:")
                role_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none; margin-top: 4px;")
                content_layout.addWidget(role_label)

                role_grid = QHBoxLayout()
                for role, kp in sorted(kp_by_role.items(), key=lambda x: x[1], reverse=True):
                    display_role = 'SUPPORT' if role == 'UTILITY' else role
                    role_grid.addWidget(self._stat_label(
                        f"{kp:.1f}%",
                        display_role,
                        COLORS['blue']
                    ))
                content_layout.addLayout(role_grid)

        # --- Gold Efficiency Stats ---
        gold_stats = adv.get_gold_efficiency_stats()
        if gold_stats['average_gpm'] > 0:
            gold_section = QLabel("💰 Gold Efficiency")
            gold_section.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; font-size: 14px; border: none; margin-top: 12px;")
            content_layout.addWidget(gold_section)

            gold_row = QHBoxLayout()
            gold_row.addWidget(self._stat_label(
                f"{gold_stats['average_gpm']:.0f}",
                "Average GPM",
                COLORS['gold']
            ))
            gold_row.addWidget(self._stat_label(
                f"{gold_stats['best_gpm']:.0f}",
                "Best GPM",
                COLORS['gold_light']
            ))
            gold_row.addWidget(self._stat_label(
                f"{gold_stats['average_cspm']:.1f}",
                "Average CSPM",
                COLORS['gold']
            ))
            gold_row.addWidget(self._stat_label(
                f"{gold_stats['best_cspm']:.1f}",
                "Best CSPM",
                COLORS['gold_light']
            ))
            content_layout.addLayout(gold_row)

        # --- Damage Share Stats ---
        dmg_stats = adv.get_damage_share_stats()
        if dmg_stats['average_damage'] > 0:
            dmg_section = QLabel("⚔️ Damage Statistics")
            dmg_section.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; font-size: 14px; border: none; margin-top: 12px;")
            content_layout.addWidget(dmg_section)

            dmg_row = QHBoxLayout()
            dmg_row.addWidget(self._stat_label(
                f"{dmg_stats['average_damage']:,.0f}",
                "Avg Damage/Game",
                COLORS['red']
            ))
            dmg_row.addWidget(self._stat_label(
                f"{dmg_stats['average_damage_per_min']:.0f}",
                "Damage per Min",
                COLORS['red']
            ))
            dmg_row.addWidget(self._stat_label(
                f"{dmg_stats['max_damage']:,.0f}",
                "Highest Damage",
                COLORS['red']
            ))
            content_layout.addLayout(dmg_row)

        # --- Comeback Stats ---
        comeback_stats = adv.get_comeback_stats()
        if comeback_stats['total_wins'] > 0:
            comeback_section = QLabel("🔄 Comeback Victories")
            comeback_section.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; font-size: 14px; border: none; margin-top: 12px;")
            content_layout.addWidget(comeback_section)

            comeback_row = QHBoxLayout()
            comeback_row.addWidget(self._stat_label(
                comeback_stats['comeback_wins'],
                f"Close Wins (<3k gold diff)",
                COLORS['green']
            ))
            comeback_row.addWidget(self._stat_label(
                f"{comeback_stats['comeback_winrate']:.1f}%",
                "% of Total Wins",
                COLORS['purple']
            ))
            content_layout.addLayout(comeback_row)

            # Show up to 3 recent comeback games
            if comeback_stats['comeback_games']:
                comeback_label = QLabel("Recent Comebacks:")
                comeback_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none; margin-top: 4px;")
                content_layout.addWidget(comeback_label)

                for game in comeback_stats['comeback_games'][:3]:
                    game_row = QLabel(
                        f"  • {game['champion']}: {game['kda']} | "
                        f"{game['duration']:.1f}min | Gold diff: {game['gold_diff']:+,}"
                    )
                    game_row.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
                    content_layout.addWidget(game_row)

        # --- Promotion Predictor ---
        if ranked_stats:
            promo_section = QLabel("🎖️ Promotion Predictor")
            promo_section.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; font-size: 14px; border: none; margin-top: 12px;")
            content_layout.addWidget(promo_section)

            for entry in ranked_stats:
                queue = "Solo/Duo" if entry['queueType'] == 'RANKED_SOLO_5x5' else "Flex"
                lp = entry.get('leaguePoints', 0)
                wins = entry.get('wins', 0)
                losses = entry.get('losses', 0)

                prediction = adv.get_promotion_prediction(lp, wins, losses)

                if prediction['promo_ready']:
                    promo_msg = QLabel(f"  {queue}: ✅ Ready for promos! (100 LP)")
                    promo_msg.setStyleSheet(f"color: {COLORS['green']}; font-weight: bold; border: none;")
                    content_layout.addWidget(promo_msg)
                else:
                    promo_row = QHBoxLayout()
                    promo_row.addWidget(QLabel(f"  {queue}:"))

                    if prediction['avg_lp_per_game'] > 0:
                        promo_row.addWidget(self._stat_label(
                            prediction['games_to_promos'],
                            f"Games to promos (~{prediction['lp_needed']} LP)",
                            COLORS['blue']
                        ))
                        promo_row.addWidget(self._stat_label(
                            f"{prediction['avg_lp_per_game']:+.1f}",
                            "LP/game",
                            COLORS['green'] if prediction['avg_lp_per_game'] > 0 else COLORS['red']
                        ))
                        promo_row.addWidget(self._stat_label(
                            f"{prediction['recent_winrate']:.0f}%",
                            f"Recent WR ({prediction['confidence']} confidence)",
                            COLORS['green'] if prediction['recent_winrate'] >= 50 else COLORS['red']
                        ))
                    else:
                        promo_row.addWidget(QLabel(
                            "Not currently gaining LP - focus on improving recent performance"
                        ))

                    content_layout.addLayout(promo_row)

        # --- Vision Score Analysis ---
        from src.analytics.vision_analysis import VisionAnalyzer
        vision_analyzer = VisionAnalyzer(stats.matches)
        vision_stats = vision_analyzer.get_vision_stats()

        if vision_stats['average_vision'] > 0:
            vision_section = QLabel("👁️ Vision Score Analysis")
            vision_section.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; font-size: 14px; border: none; margin-top: 12px;")
            content_layout.addWidget(vision_section)

            # Overall vision stats
            vision_row = QHBoxLayout()
            vision_row.addWidget(self._stat_label(
                f"{vision_stats['average_vision']:.1f}",
                "Average Vision",
                COLORS['purple']
            ))
            vision_row.addWidget(self._stat_label(
                f"{vision_stats['max_vision']:.0f}",
                "Best Vision",
                COLORS['purple']
            ))
            vision_row.addWidget(self._stat_label(
                f"{vision_stats['control_wards_placed']:.1f}",
                "Control Wards/Game",
                COLORS['red']
            ))
            vision_row.addWidget(self._stat_label(
                f"{vision_stats['wards_destroyed']:.1f}",
                "Wards Killed/Game",
                COLORS['orange']
            ))
            content_layout.addLayout(vision_row)

            # Win vs Loss comparison
            vision_diff = vision_stats['vision_in_wins'] - vision_stats['vision_in_losses']
            vision_comparison = QLabel(
                f"Vision in wins: {vision_stats['vision_in_wins']:.1f} | "
                f"in losses: {vision_stats['vision_in_losses']:.1f} "
                f"({vision_diff:+.1f} difference)"
            )
            vision_comparison.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none; margin-top: 4px;")
            content_layout.addWidget(vision_comparison)

            # Vision by role
            if vision_stats['vision_by_role']:
                role_vision_label = QLabel("Vision by Role:")
                role_vision_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none; margin-top: 4px;")
                content_layout.addWidget(role_vision_label)

                role_vision_grid = QHBoxLayout()
                for role, vision in sorted(vision_stats['vision_by_role'].items(), key=lambda x: x[1], reverse=True):
                    display_role = 'SUPPORT' if role == 'UTILITY' else role
                    rating = vision_analyzer.get_vision_rating(vision, role)
                    rating_color = {
                        'Excellent': COLORS['green'],
                        'Good': COLORS['blue'],
                        'Average': COLORS['text'],
                        'Needs Improvement': COLORS['red']
                    }.get(rating, COLORS['text'])

                    role_vision_grid.addWidget(self._stat_label(
                        f"{vision:.1f}",
                        f"{display_role} ({rating})",
                        rating_color
                    ))
                content_layout.addLayout(role_vision_grid)

        # Add content widget to main layout
        layout.addWidget(content_widget)
        self.layout_main.addWidget(card)

    def _add_win_conditions(self, stats):
        conditions = stats.win_conditions()
        if not conditions:
            return

        card, layout = self._card("Your Win Conditions")

        desc = QLabel("Stats with the biggest gap between your wins and losses:")
        desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none;")
        layout.addWidget(desc)

        for i, wc in enumerate(conditions[:5]):
            row = QHBoxLayout()

            rank = QLabel(f"#{i+1}")
            rank.setFixedWidth(30)
            rank.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; font-size: 14px; border: none;")
            row.addWidget(rank)

            name = QLabel(wc['label'])
            name.setFixedWidth(140)
            name.setStyleSheet(f"font-weight: bold; border: none;")
            row.addWidget(name)

            win_val = QLabel(f"{wc['win_avg']}{wc['suffix']}")
            win_val.setFixedWidth(80)
            win_val.setStyleSheet(f"color: {COLORS['green']}; border: none;")
            row.addWidget(win_val)

            vs = QLabel("vs")
            vs.setFixedWidth(20)
            vs.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
            row.addWidget(vs)

            loss_val = QLabel(f"{wc['loss_avg']}{wc['suffix']}")
            loss_val.setFixedWidth(80)
            loss_val.setStyleSheet(f"color: {COLORS['red']}; border: none;")
            row.addWidget(loss_val)

            gap = QLabel(f"({wc['gap_pct']}% gap)")
            gap.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
            row.addWidget(gap)

            row.addStretch()
            layout.addLayout(row)

        self.layout_main.addWidget(card)

    def _add_role_breakdown(self, stats):
        roles = stats.by_role()
        if not roles:
            return

        card, layout = self._card("Role Performance")

        for role_data in roles:
            role = 'SUPPORT' if role_data['role'] == 'UTILITY' else role_data['role']
            games = role_data['games']
            wr = role_data['winrate']
            kda = role_data['avg_kda']

            row = QHBoxLayout()

            role_label = QLabel(role)
            role_label.setFixedWidth(80)
            role_label.setStyleSheet(f"font-weight: bold; border: none;")
            row.addWidget(role_label)

            games_label = QLabel(f"{games}G")
            games_label.setFixedWidth(40)
            games_label.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
            row.addWidget(games_label)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(int(wr))
            bar.setFormat(f"{wr}% WR")
            bar.setFixedHeight(20)

            bar_color = COLORS['green'] if wr >= 50 else COLORS['red']
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {COLORS['bg_dark']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 4px;
                    text-align: center;
                    color: {COLORS['text']};
                    font-size: 11px;
                }}
                QProgressBar::chunk {{
                    background-color: {bar_color};
                    border-radius: 3px;
                }}
            """)
            row.addWidget(bar)

            kda_label = QLabel(f"KDA {kda}")
            kda_label.setFixedWidth(80)
            kda_label.setStyleSheet(f"color: {COLORS['blue']}; border: none;")
            row.addWidget(kda_label)

            layout.addLayout(row)

        self.layout_main.addWidget(card)

    def _add_duo_partners(self, stats):
        import os
        from pathlib import Path

        partners = stats.duo_partner_analysis()
        if not partners:
            return

        card, layout = self._card(f"Duo Partners ({len(partners)} recurring teammates)")

        for p in partners[:10]:
            row = QHBoxLayout()

            name = QLabel(f"{p['summoner_name']}#{p['tag_line']}" if p['tag_line'] else p['summoner_name'])
            name.setFixedWidth(200)
            name.setStyleSheet(f"font-weight: bold; border: none;")
            row.addWidget(name)

            wr_color = COLORS['green'] if p['winrate'] >= 50 else COLORS['red']
            wr = QLabel(f"{p['winrate']}% WR")
            wr.setFixedWidth(80)
            wr.setStyleSheet(f"color: {wr_color}; font-weight: bold; border: none;")
            row.addWidget(wr)

            games = QLabel(f"{p['games']}G ({p['wins']}W {p['losses']}L)")
            games.setFixedWidth(120)
            games.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
            row.addWidget(games)

            # Show top 5 champions as icons
            champs_label = QLabel("Plays:")
            champs_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
            row.addWidget(champs_label)

            # Try to find cache directory (either relative or in exe directory)
            cache_dir = Path("cache/icons")
            if not cache_dir.exists():
                # Try in parent directory (for exe builds)
                cache_dir = Path("../cache/icons")

            for champ_name in p.get('top_champions', []):
                # Create icon label with champion icon
                icon_label = QLabel()

                # Try to load champion icon from cache
                icon_path = cache_dir / f"{champ_name}.png"
                if icon_path.exists():
                    pixmap = QPixmap(str(icon_path))
                    if not pixmap.isNull():
                        # Scale to 24x24 for compact display
                        scaled_pixmap = pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        icon_label.setPixmap(scaled_pixmap)
                        icon_label.setFixedSize(24, 24)
                        icon_label.setToolTip(champ_name)
                        icon_label.setStyleSheet("border: 1px solid #3C3C3C; border-radius: 4px; margin-left: 2px;")
                    else:
                        # Fallback to text if pixmap failed
                        icon_label.setText(champ_name)
                        icon_label.setStyleSheet(f"color: {COLORS['blue']}; font-size: 11px; border: none; margin-left: 4px;")
                else:
                    # Fallback to text if icon not found
                    icon_label.setText(champ_name)
                    icon_label.setStyleSheet(f"color: {COLORS['blue']}; font-size: 11px; border: none; margin-left: 4px;")

                row.addWidget(icon_label)

            row.addStretch()
            layout.addLayout(row)

        self.layout_main.addWidget(card)

    def _add_recent_form(self, stats, tilt_detector):
        recent = stats.recent_form(20)
        if not recent:
            return

        card, layout = self._card("Recent Form (Last 20 Games)")

        streak = tilt_detector.current_streak()
        streak_color = COLORS['green'] if streak['type'] == 'win' else COLORS['red']
        streak_label = QLabel(f"Current: {streak['count']} game {streak['type']} streak")
        streak_label.setStyleSheet(f"color: {streak_color}; font-weight: bold; font-size: 14px; border: none;")
        layout.addWidget(streak_label)

        # Win/loss blocks
        form_layout = QHBoxLayout()
        for m in recent:
            block = QLabel("W" if m['win'] else "L")
            block.setFixedSize(28, 28)
            block.setAlignment(Qt.AlignmentFlag.AlignCenter)
            bg = COLORS['green'] if m['win'] else COLORS['red']
            block.setStyleSheet(f"""
                background-color: {bg};
                color: white;
                font-weight: bold;
                font-size: 11px;
                border-radius: 4px;
                border: none;
            """)
            block.setToolTip(f"{m['champion']} {m['kills']}/{m['deaths']}/{m['assists']}")
            form_layout.addWidget(block)

        form_layout.addStretch()
        layout.addLayout(form_layout)

        self.layout_main.addWidget(card)

    def _add_tilt_analysis(self, tilt_detector):
        card, layout = self._card("Tilt Analysis")

        # Session dropoff
        dropoff = tilt_detector.session_dropoff()
        if dropoff['sessions_analyzed'] > 0:
            drop_color = COLORS['red'] if dropoff['dropoff'] > 5 else COLORS['green']
            drop_label = QLabel(
                f"Session Dropoff: {dropoff['dropoff']}% "
                f"(Early: {dropoff['early_wr']}% -> Late: {dropoff['late_wr']}%)"
            )
            drop_label.setStyleSheet(f"color: {drop_color}; font-weight: bold; border: none;")
            layout.addWidget(drop_label)

        # Time of day
        tod = tilt_detector.time_of_day_analysis()
        if tod:
            tod_label = QLabel("Win Rate by Hour:")
            tod_label.setStyleSheet(f"color: {COLORS['text_dim']}; margin-top: 8px; border: none;")
            layout.addWidget(tod_label)

            for t in tod:
                if t['games'] >= 3:
                    row = QHBoxLayout()

                    hour = QLabel(t['hour_label'])
                    hour.setFixedWidth(50)
                    hour.setStyleSheet("border: none;")
                    row.addWidget(hour)

                    bar = QProgressBar()
                    bar.setRange(0, 100)
                    bar.setValue(int(t['winrate']))
                    bar.setFormat(f"{t['winrate']}% ({t['games']}G)")
                    bar.setFixedHeight(18)

                    bar_color = COLORS['green'] if t['winrate'] >= 50 else COLORS['red']
                    bar.setStyleSheet(f"""
                        QProgressBar {{
                            background-color: {COLORS['bg_dark']};
                            border: 1px solid {COLORS['border']};
                            border-radius: 4px;
                            text-align: center;
                            color: {COLORS['text']};
                            font-size: 11px;
                        }}
                        QProgressBar::chunk {{
                            background-color: {bar_color};
                            border-radius: 3px;
                        }}
                    """)
                    row.addWidget(bar)

                    layout.addLayout(row)

        self.layout_main.addWidget(card)

    def _add_climb_progress(self, climb_history):
        card, layout = self._card("Climb History")

        # Deduplicate: keep only the latest entry per (date, queue_type)
        seen = {}
        for snap in climb_history:
            key = (snap['timestamp'][:10], snap['queue_type'])
            seen[key] = snap  # Later entries overwrite earlier ones
        unique = sorted(seen.values(), key=lambda s: s['timestamp'], reverse=True)

        # Show last 10 unique snapshots in a grid
        grid = QGridLayout()
        grid.setSpacing(8)

        # Headers
        for col, header in enumerate(["Date", "Queue", "Rank", "LP", "W/L"]):
            lbl = QLabel(header)
            lbl.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; font-size: 11px; border: none;")
            grid.addWidget(lbl, 0, col)

        for row_idx, snap in enumerate(unique[:10], 1):
            queue = "Solo" if snap['queue_type'] == 'RANKED_SOLO_5x5' else "Flex"
            tier = snap.get('tier', '')
            rank_val = snap.get('rank', '')
            color = RANK_COLORS.get(tier, COLORS['text'])

            date_lbl = QLabel(snap['timestamp'][:10])
            date_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none;")
            grid.addWidget(date_lbl, row_idx, 0)

            queue_lbl = QLabel(queue)
            queue_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none;")
            grid.addWidget(queue_lbl, row_idx, 1)

            rank_lbl = QLabel(f"{tier} {rank_val}")
            rank_lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 13px; border: none;")
            grid.addWidget(rank_lbl, row_idx, 2)

            lp_lbl = QLabel(f"{snap.get('lp', 0)} LP")
            lp_lbl.setStyleSheet(f"color: {COLORS['text_bright']}; font-weight: bold; font-size: 12px; border: none;")
            grid.addWidget(lp_lbl, row_idx, 3)

            wl_lbl = QLabel(f"{snap.get('wins', 0)}W {snap.get('losses', 0)}L")
            wl_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none;")
            grid.addWidget(wl_lbl, row_idx, 4)

        layout.addLayout(grid)
        self.layout_main.addWidget(card)

    def _add_win_rate_calendar(self, stats):
        from datetime import datetime, timedelta

        calendar = stats.win_rate_calendar()
        if not calendar:
            return

        card, layout = self._card("Win Rate Calendar")

        desc = QLabel("Daily win rate heatmap (green = positive, red = negative):")
        desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; border: none;")
        layout.addWidget(desc)

        grid = QGridLayout()
        grid.setSpacing(3)

        # Day name headers (Mon-Sun)
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for col, name in enumerate(day_names):
            lbl = QLabel(name)
            lbl.setFixedSize(36, 18)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"color: {COLORS['gold']}; font-size: 10px; font-weight: bold; border: none;")
            grid.addWidget(lbl, 0, col)

        # Build lookup of date -> data
        cal_map = {d['date']: d for d in calendar}

        # Find the range: last 6 weeks ending today
        today = datetime.now().date()
        # Go back to find the Monday 5 weeks ago
        days_since_monday = today.weekday()  # 0=Mon
        last_monday = today - timedelta(days=days_since_monday + 5 * 7)

        row_idx = 1
        current = last_monday
        while current <= today:
            col = current.weekday()  # 0=Mon, 6=Sun
            date_str = current.strftime('%Y-%m-%d')
            day_data = cal_map.get(date_str)

            if day_data:
                block = QLabel(f"{day_data['net']:+d}" if day_data['net'] != 0 else "0")
                if day_data['winrate'] >= 60:
                    bg = '#1B5E20'
                elif day_data['winrate'] >= 50:
                    bg = '#2E7D32'
                elif day_data['winrate'] == 50:
                    bg = COLORS['bg_dark']
                elif day_data['winrate'] >= 40:
                    bg = '#C62828'
                else:
                    bg = '#B71C1C'
                tooltip = f"{day_data['date']}: {day_data['wins']}W {day_data['losses']}L ({day_data['winrate']}%)"
            else:
                block = QLabel("")
                bg = COLORS['bg_dark']
                tooltip = f"{date_str}: No games"

            block.setFixedSize(36, 36)
            block.setAlignment(Qt.AlignmentFlag.AlignCenter)
            block.setStyleSheet(f"""
                background-color: {bg};
                color: white;
                font-weight: bold;
                font-size: 10px;
                border-radius: 4px;
                border: 1px solid {COLORS['border']};
            """)
            block.setToolTip(tooltip)
            grid.addWidget(block, row_idx, col)

            # Move to next row after Sunday
            if col == 6:
                row_idx += 1
            current += timedelta(days=1)

        layout.addLayout(grid)

        # Summary
        total_days = len(calendar)
        positive_days = sum(1 for d in calendar if d['winrate'] > 50)
        negative_days = sum(1 for d in calendar if d['winrate'] < 50)
        summary = QLabel(f"{total_days} days played  |  {positive_days} positive days  |  {negative_days} negative days")
        summary.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
        layout.addWidget(summary)

        self.layout_main.addWidget(card)
