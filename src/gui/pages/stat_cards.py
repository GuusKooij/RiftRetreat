"""Stat Cards page: Generate shareable social media stat graphics."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QComboBox, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor, QLinearGradient, QPen, QBrush

from src.gui.theme import COLORS
from src.analytics.stats import StatsAnalyzer
from src.analytics.tilt import TiltDetector
from src.analytics.champions import ChampionAnalyzer
from config import SEASON_START_TIMESTAMP


class StatCardsPage(QWidget):
    """Generate and export shareable stat cards for social media."""

    def __init__(self):
        super().__init__()
        self.stats = None
        self.tilt = None
        self.champ_analyzer = None
        self.all_matches = []  # Store all matches for filtering
        self.dd = None  # Data Dragon for champion icons
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
        title = QLabel("📸 Stat Cards")
        title.setStyleSheet(f"color: {COLORS['gold']}; font-size: 32px; font-weight: bold;")
        self.layout_main.addWidget(title)

        desc = QLabel("Generate shareable stat cards for Instagram, Twitter, and Discord")
        desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 14px; margin-bottom: 12px;")
        self.layout_main.addWidget(desc)

        # Card type selector - compact
        selector_card = QFrame()
        selector_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        selector_layout = QHBoxLayout(selector_card)
        selector_layout.setSpacing(12)

        selector_title = QLabel("📅 2026 - Create:")
        selector_title.setStyleSheet(f"color: {COLORS['text']}; font-size: 14px; font-weight: bold;")
        selector_layout.addWidget(selector_title)

        self.card_type_combo = QComboBox()
        self.card_type_combo.addItems([
            "Season Wrapped",
            "Best Champion Showcase",
            "Personal Records",
            "Winrate Highlights",
            "KDA Showcase",
            "Champion Pool Overview",
        ])
        self.card_type_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_dark']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 13px;
                min-width: 220px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {COLORS['text']};
                margin-right: 8px;
            }}
        """)
        self.card_type_combo.currentIndexChanged.connect(self._on_card_type_changed)
        selector_layout.addWidget(self.card_type_combo)
        selector_layout.addStretch()

        self.layout_main.addWidget(selector_card)

        # Preview area - more compact
        self.preview_label = QLabel("Click 'Generate Preview' to see your stat card")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet(f"""
            background-color: {COLORS['bg_dark']};
            border: 2px dashed {COLORS['border']};
            border-radius: 8px;
            padding: 20px;
            color: {COLORS['text_dim']};
            font-size: 14px;
        """)
        self.preview_label.setFixedHeight(450)
        self.layout_main.addWidget(self.preview_label)

        # Export buttons
        btn_layout = QHBoxLayout()

        generate_btn = QPushButton("Generate Preview")
        generate_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['gold_dark']};
                color: white;
                font-weight: bold;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['gold']};
            }}
        """)
        generate_btn.clicked.connect(self._generate_preview)
        btn_layout.addWidget(generate_btn)

        export_btn = QPushButton("Export as PNG")
        export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['green']};
                color: white;
                font-weight: bold;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #00E676;
            }}
        """)
        export_btn.clicked.connect(self._export_card)
        btn_layout.addWidget(export_btn)

        btn_layout.addStretch()
        self.layout_main.addLayout(btn_layout)

        self.layout_main.addStretch()

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def update_data(self, stats, tilt, champ_analyzer, matches=None, data_dragon=None):
        """Update with analytics data."""
        self.stats = stats
        self.tilt = tilt
        self.champ_analyzer = champ_analyzer  # Keep original for champion data
        self.original_champ_analyzer = champ_analyzer  # Store original
        self.dd = data_dragon  # Store DataDragon instance
        if matches:
            self.all_matches = matches
            # Apply initial season filter
            self._filter_by_season()

    def _on_card_type_changed(self, index):
        """Clear preview when card type changes."""
        self.preview_label.setPixmap(QPixmap())
        self.preview_label.setText("Click 'Generate Preview' to see your stat card")

    def _draw_champion_icon(self, painter: QPainter, champion_name: str, x: int, y: int, size: int = 120):
        """Draw a champion icon at the specified position."""
        if not self.dd:
            return

        icon_path = self.dd.get_champion_icon_path(champion_name)
        if icon_path:
            icon_pixmap = QPixmap(icon_path)
            if not icon_pixmap.isNull():
                # Scale and draw
                scaled_icon = icon_pixmap.scaled(
                    size, size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                painter.drawPixmap(x - size // 2, y, scaled_icon)


    def _filter_by_season(self):
        """Filter matches by selected season and regenerate analyzers."""
        if not self.all_matches:
            return

        from datetime import datetime

        # Season 2025 (current season) - filter by game_start field
        # Convert game_start ISO string to timestamp for comparison
        filtered_matches = []
        for m in self.all_matches:
            try:
                game_start_str = m.get('game_start', '')
                if game_start_str:
                    game_timestamp = int(datetime.fromisoformat(game_start_str).timestamp())
                    if game_timestamp >= SEASON_START_TIMESTAMP:
                        filtered_matches.append(m)
            except (ValueError, KeyError):
                # Skip matches with invalid dates
                continue

        # Regenerate analyzers with filtered data
        if filtered_matches:
            self.stats = StatsAnalyzer(filtered_matches)
            self.tilt = TiltDetector(filtered_matches)
            # Keep original champ_analyzer (uses all-time mastery data, not season-filtered)
            self.champ_analyzer = self.original_champ_analyzer
        else:
            # No matches in season - use all matches as fallback
            self.stats = StatsAnalyzer(self.all_matches)
            self.tilt = TiltDetector(self.all_matches)
            self.champ_analyzer = self.original_champ_analyzer

    def _generate_preview(self):
        """Generate card preview."""
        if not self.stats:
            QMessageBox.warning(self, "No Data", "Please refresh your data in Settings first.")
            return

        card_type = self.card_type_combo.currentIndex()

        if card_type == 0:
            pixmap = self._create_season_wrapped_card()
        elif card_type == 1:
            pixmap = self._create_best_champion_card()
        elif card_type == 2:
            pixmap = self._create_records_card()
        elif card_type == 3:
            pixmap = self._create_winrate_card()
        elif card_type == 4:
            pixmap = self._create_kda_card()
        elif card_type == 5:
            pixmap = self._create_champion_pool_card()
        else:
            pixmap = QPixmap(1080, 1080)
            pixmap.fill(QColor(COLORS['bg_dark']))

        # Scale to fit preview (smaller for compact layout)
        scaled = pixmap.scaled(
            400,  # Fixed width for consistency
            400,  # Fixed height
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.preview_label.setPixmap(scaled)
        self.preview_label.setText("")
        self.current_pixmap = pixmap  # Store for export

    def _create_season_wrapped_card(self) -> QPixmap:
        """Create Season Wrapped card (1080x1080 Instagram square)."""
        pixmap = QPixmap(1080, 1080)
        pixmap.fill(QColor("#0A1428"))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background gradient
        gradient = QLinearGradient(0, 0, 1080, 1080)
        gradient.setColorAt(0, QColor("#0A1428"))
        gradient.setColorAt(0.5, QColor("#1E2328"))
        gradient.setColorAt(1, QColor("#0F2027"))
        painter.fillRect(0, 0, 1080, 1080, QBrush(gradient))

        # Title - Season 2026
        painter.setFont(QFont("Arial", 72, QFont.Weight.Bold))
        painter.setPen(QColor(COLORS['gold']))
        painter.drawText(0, 150, 1080, 100, Qt.AlignmentFlag.AlignCenter, "SEASON 2026")

        painter.setFont(QFont("Arial", 48))
        painter.setPen(QColor("#A89968"))
        painter.drawText(0, 220, 1080, 80, Qt.AlignmentFlag.AlignCenter, "YOUR WRAPPED")

        # Stats boxes
        try:
            overall = self.stats.overall()
            y_offset = 380

            stat_items = [
                ("GAMES PLAYED", str(overall.get('games', 0)), COLORS['text_bright']),
                ("WIN RATE", f"{overall.get('winrate', 0):.0f}%", COLORS['green'] if overall.get('winrate', 0) >= 50 else COLORS['red']),
                ("AVG KDA", f"{overall.get('avg_kda', 0):.1f}", COLORS['gold']),
                ("AVG CS/MIN", f"{overall.get('avg_cs_per_min', 0):.1f}", COLORS['text_bright']),
            ]
        except (AttributeError, KeyError, TypeError) as e:
            painter.setFont(QFont("Arial", 32))
            painter.setPen(QColor(COLORS['text']))
            painter.drawText(0, 500, 1080, 100, Qt.AlignmentFlag.AlignCenter, f"Stats unavailable")
            painter.end()
            return pixmap

        for label, value, color in stat_items:
            # Label
            painter.setFont(QFont("Arial", 24))
            painter.setPen(QColor("#5B5A56"))
            painter.drawText(0, y_offset, 1080, 40, Qt.AlignmentFlag.AlignCenter, label)

            # Value
            painter.setFont(QFont("Arial", 64, QFont.Weight.Bold))
            painter.setPen(QColor(color))
            painter.drawText(0, y_offset + 40, 1080, 80, Qt.AlignmentFlag.AlignCenter, value)

            y_offset += 150

        # Footer
        painter.setFont(QFont("Arial", 18))
        painter.setPen(QColor("#5B5A56"))
        painter.drawText(0, 1020, 1080, 40, Qt.AlignmentFlag.AlignCenter, "© RiftRetreat")

        painter.end()
        return pixmap

    def _create_best_champion_card(self) -> QPixmap:
        """Create Best Champion showcase card."""
        pixmap = QPixmap(1080, 1080)
        pixmap.fill(QColor("#0A1428"))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        gradient = QLinearGradient(0, 0, 1080, 1080)
        gradient.setColorAt(0, QColor("#1E2328"))
        gradient.setColorAt(1, QColor("#0A1428"))
        painter.fillRect(0, 0, 1080, 1080, QBrush(gradient))

        # Get best champion
        try:
            if not self.champ_analyzer:
                raise ValueError("No champion analyzer")
            champs_by_wr = self.champ_analyzer.get_champions_by_winrate(min_games=3)
            if not champs_by_wr:
                raise ValueError("No champions found")
            best_champ = champs_by_wr[0]
        except (AttributeError, ValueError, IndexError) as e:
            painter.setFont(QFont("Arial", 32))
            painter.setPen(QColor(COLORS['text']))
            painter.drawText(0, 500, 1080, 100, Qt.AlignmentFlag.AlignCenter, "No champion data available")
            painter.end()
            return pixmap

        # Title
        painter.setFont(QFont("Arial", 56, QFont.Weight.Bold))
        painter.setPen(QColor(COLORS['gold']))
        painter.drawText(0, 120, 1080, 80, Qt.AlignmentFlag.AlignCenter, "MY BEST CHAMPION")

        # Large champion icon centered
        self._draw_champion_icon(painter, best_champ['champion'], 540, 250, size=200)

        # Champion name below icon
        painter.setFont(QFont("Arial", 64, QFont.Weight.Bold))
        painter.setPen(QColor(COLORS['text_bright']))
        painter.drawText(0, 480, 1080, 80, Qt.AlignmentFlag.AlignCenter, best_champ['champion'])

        # Stats
        y = 600
        stats = [
            (f"{best_champ.get('games', 0)} GAMES", 32),
            (f"{best_champ.get('winrate', best_champ.get('win_rate', 0)):.0f}% WIN RATE", 56),
            (f"{best_champ.get('avg_kda', best_champ.get('kda', 0)):.2f} KDA", 44),
            (f"{best_champ.get('avg_cs_per_min', best_champ.get('cs_per_min', 0)):.1f} CS/MIN", 32),
        ]

        for text, size in stats:
            painter.setFont(QFont("Arial", size, QFont.Weight.Bold if size > 40 else QFont.Weight.Normal))
            wr = best_champ.get('winrate', best_champ.get('win_rate', 0))
            color = COLORS['green'] if "WIN RATE" in text and wr >= 60 else COLORS['text']
            painter.setPen(QColor(color))
            painter.drawText(0, y, 1080, size + 20, Qt.AlignmentFlag.AlignCenter, text)
            y += size + 35

        # Footer
        painter.setFont(QFont("Arial", 18))
        painter.setPen(QColor("#5B5A56"))
        painter.drawText(0, 1020, 1080, 40, Qt.AlignmentFlag.AlignCenter, "© RiftRetreat")

        painter.end()
        return pixmap

    def _create_winrate_card(self) -> QPixmap:
        """Create winrate highlight card - shows top 3 champions by WR."""
        pixmap = QPixmap(1080, 1080)
        pixmap.fill(QColor("#0A1428"))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        gradient = QLinearGradient(0, 0, 1080, 1080)
        gradient.setColorAt(0, QColor("#1E2328"))
        gradient.setColorAt(1, QColor("#0A1428"))
        painter.fillRect(0, 0, 1080, 1080, QBrush(gradient))

        # Title
        painter.setFont(QFont("Arial", 56, QFont.Weight.Bold))
        painter.setPen(QColor(COLORS['gold']))
        painter.drawText(0, 120, 1080, 80, Qt.AlignmentFlag.AlignCenter, "TOP WINRATE")

        painter.setFont(QFont("Arial", 32))
        painter.setPen(QColor("#A89968"))
        painter.drawText(0, 190, 1080, 50, Qt.AlignmentFlag.AlignCenter, "🏆 Season 2026 🏆")

        try:
            if not self.champ_analyzer:
                raise ValueError("No champion analyzer")
            top_champs = self.champ_analyzer.get_champions_by_winrate(min_games=3)
            if not top_champs:
                raise ValueError("No champions found")

            # Show top 3 - tighter spacing to fit footer
            y = 290
            medals = ["🥇", "🥈", "🥉"]
            for i, champ in enumerate(top_champs[:3]):
                # Champion icon (centered)
                self._draw_champion_icon(painter, champ['champion'], 540, y, size=110)

                # Medal (top-left of icon)
                painter.setFont(QFont("Arial", 38))
                painter.setPen(QColor(COLORS['gold']))
                painter.drawText(435, y + 12, 65, 45, Qt.AlignmentFlag.AlignCenter, medals[i])

                # Champion name
                painter.setFont(QFont("Arial", 34, QFont.Weight.Bold))
                painter.setPen(QColor(COLORS['text_bright']))
                painter.drawText(0, y + 130, 1080, 42, Qt.AlignmentFlag.AlignCenter, champ['champion'])

                # WR + games
                wr = champ.get('winrate', champ.get('win_rate', 0))
                games = champ.get('games', 0)
                painter.setFont(QFont("Arial", 46, QFont.Weight.Bold))
                painter.setPen(QColor(COLORS['green']))
                painter.drawText(0, y + 172, 1080, 56, Qt.AlignmentFlag.AlignCenter, f"{wr:.0f}%")

                painter.setFont(QFont("Arial", 19))
                painter.setPen(QColor("#5B5A56"))
                painter.drawText(0, y + 228, 1080, 28, Qt.AlignmentFlag.AlignCenter, f"{games} games")

                y += 245

        except (AttributeError, ValueError, IndexError):
            painter.setFont(QFont("Arial", 32))
            painter.setPen(QColor(COLORS['text']))
            painter.drawText(0, 500, 1080, 100, Qt.AlignmentFlag.AlignCenter, "No champion data available")

        # Footer
        painter.setFont(QFont("Arial", 18))
        painter.setPen(QColor("#5B5A56"))
        painter.drawText(0, 1020, 1080, 40, Qt.AlignmentFlag.AlignCenter, "© RiftRetreat")

        painter.end()
        return pixmap

    def _create_kda_card(self) -> QPixmap:
        """Create KDA showcase card - shows best KDA champions."""
        pixmap = QPixmap(1080, 1080)
        pixmap.fill(QColor("#0A1428"))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        gradient = QLinearGradient(0, 0, 1080, 1080)
        gradient.setColorAt(0, QColor("#1E2328"))
        gradient.setColorAt(1, QColor("#0A1428"))
        painter.fillRect(0, 0, 1080, 1080, QBrush(gradient))

        # Title
        painter.setFont(QFont("Arial", 56, QFont.Weight.Bold))
        painter.setPen(QColor(COLORS['gold']))
        painter.drawText(0, 120, 1080, 80, Qt.AlignmentFlag.AlignCenter, "BEST KDA")

        painter.setFont(QFont("Arial", 32))
        painter.setPen(QColor("#A89968"))
        painter.drawText(0, 190, 1080, 50, Qt.AlignmentFlag.AlignCenter, "🎯 Season 2026 🎯")

        try:
            if not self.champ_analyzer:
                raise ValueError("No champion analyzer")
            pool = self.champ_analyzer.champion_pool()
            # Filter min 3 games and sort by KDA
            valid = [c for c in pool if c['games'] >= 3]
            if not valid:
                raise ValueError("No champions found")
            valid.sort(key=lambda x: x['avg_kda'], reverse=True)

            # Show top 3 - tighter spacing to fit footer
            y = 290
            for i, champ in enumerate(valid[:3]):
                # Champion icon (centered)
                self._draw_champion_icon(painter, champ['champion'], 540, y, size=105)

                # Rank badge (top-left of icon)
                painter.setFont(QFont("Arial", 34, QFont.Weight.Bold))
                painter.setPen(QColor("#5B5A56"))
                painter.drawText(440, y + 10, 55, 42, Qt.AlignmentFlag.AlignCenter, f"#{i+1}")

                # Champion name
                painter.setFont(QFont("Arial", 32, QFont.Weight.Bold))
                painter.setPen(QColor(COLORS['text_bright']))
                painter.drawText(0, y + 125, 1080, 42, Qt.AlignmentFlag.AlignCenter, champ['champion'])

                # KDA
                kda = champ.get('avg_kda', 0)
                painter.setFont(QFont("Arial", 48, QFont.Weight.Bold))
                painter.setPen(QColor(COLORS['gold']))
                painter.drawText(0, y + 167, 1080, 60, Qt.AlignmentFlag.AlignCenter, f"{kda:.2f} KDA")

                # K/D/A breakdown
                k = champ.get('avg_kills', 0)
                d = champ.get('avg_deaths', 0)
                a = champ.get('avg_assists', 0)
                painter.setFont(QFont("Arial", 19))
                painter.setPen(QColor("#5B5A56"))
                painter.drawText(0, y + 227, 1080, 28, Qt.AlignmentFlag.AlignCenter, f"{k:.1f} / {d:.1f} / {a:.1f}")

                y += 245

        except (AttributeError, ValueError, IndexError):
            painter.setFont(QFont("Arial", 32))
            painter.setPen(QColor(COLORS['text']))
            painter.drawText(0, 500, 1080, 100, Qt.AlignmentFlag.AlignCenter, "No champion data available")

        # Footer
        painter.setFont(QFont("Arial", 18))
        painter.setPen(QColor("#5B5A56"))
        painter.drawText(0, 1020, 1080, 40, Qt.AlignmentFlag.AlignCenter, "© RiftRetreat")

        painter.end()
        return pixmap

    def _create_champion_pool_card(self) -> QPixmap:
        """Create champion pool overview card - shows pool stats."""
        pixmap = QPixmap(1080, 1080)
        pixmap.fill(QColor("#0A1428"))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        gradient = QLinearGradient(0, 0, 1080, 1080)
        gradient.setColorAt(0, QColor("#1E2328"))
        gradient.setColorAt(1, QColor("#0A1428"))
        painter.fillRect(0, 0, 1080, 1080, QBrush(gradient))

        # Title
        painter.setFont(QFont("Arial", 56, QFont.Weight.Bold))
        painter.setPen(QColor(COLORS['gold']))
        painter.drawText(0, 120, 1080, 80, Qt.AlignmentFlag.AlignCenter, "CHAMPION POOL")

        painter.setFont(QFont("Arial", 32))
        painter.setPen(QColor("#A89968"))
        painter.drawText(0, 190, 1080, 50, Qt.AlignmentFlag.AlignCenter, "📊 Season 2026 📊")

        try:
            if not self.champ_analyzer:
                raise ValueError("No champion analyzer")
            pool = self.champ_analyzer.champion_pool()
            recs = self.champ_analyzer.recommendations()

            total_champs = len(pool)
            strong = len(recs.get('prioritize', []))
            weak = len(recs.get('drop', []))
            avg = len(recs.get('average', []))
            total_games = sum(c['games'] for c in pool)

            # Stats
            y = 300
            stat_items = [
                ("CHAMPIONS PLAYED", str(total_champs), COLORS['text_bright']),
                ("TOTAL GAMES", str(total_games), COLORS['text_bright']),
                ("STRONG PICKS", f"{strong}", COLORS['green']),
                ("WEAK PICKS", f"{weak}", COLORS['red']),
                ("AVERAGE PICKS", f"{avg}", COLORS['text']),
            ]

            for label, value, color in stat_items:
                # Label
                painter.setFont(QFont("Arial", 24))
                painter.setPen(QColor("#5B5A56"))
                painter.drawText(0, y, 1080, 40, Qt.AlignmentFlag.AlignCenter, label)

                # Value
                painter.setFont(QFont("Arial", 56, QFont.Weight.Bold))
                painter.setPen(QColor(color))
                painter.drawText(0, y + 40, 1080, 70, Qt.AlignmentFlag.AlignCenter, value)

                y += 140

        except (AttributeError, ValueError, IndexError):
            painter.setFont(QFont("Arial", 32))
            painter.setPen(QColor(COLORS['text']))
            painter.drawText(0, 500, 1080, 100, Qt.AlignmentFlag.AlignCenter, "No champion data available")

        # Footer
        painter.setFont(QFont("Arial", 18))
        painter.setPen(QColor("#5B5A56"))
        painter.drawText(0, 1020, 1080, 40, Qt.AlignmentFlag.AlignCenter, "© RiftRetreat")

        painter.end()
        return pixmap

    def _create_records_card(self) -> QPixmap:
        """Create personal records card."""
        pixmap = QPixmap(1080, 1080)
        pixmap.fill(QColor("#0A1428"))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        gradient = QLinearGradient(0, 0, 1080, 1080)
        gradient.setColorAt(0, QColor("#1E2328"))
        gradient.setColorAt(1, QColor("#0A1428"))
        painter.fillRect(0, 0, 1080, 1080, QBrush(gradient))

        # Title
        painter.setFont(QFont("Arial", 56, QFont.Weight.Bold))
        painter.setPen(QColor(COLORS['gold']))
        painter.drawText(0, 120, 1080, 80, Qt.AlignmentFlag.AlignCenter, "PERSONAL RECORDS")

        # Season subtitle
        painter.setFont(QFont("Arial", 32))
        painter.setPen(QColor("#A89968"))
        painter.drawText(0, 190, 1080, 50, Qt.AlignmentFlag.AlignCenter, "🏆 Season 2026 🏆")

        # Get personal records - it returns a list
        try:
            records_list = self.stats.personal_records()
            if not records_list:
                raise ValueError("No records")

            # Emoji mapping
            emoji_map = {
                'Best KDA': '🎯',
                'Most Kills': '⚔️',
                'Most Assists': '🤝',
                'Most CS': '💰',
                'Best CS/min': '📈',
                'Most Damage': '💥',
                'Best Vision Score': '👁️',
                'Highest Kill Participation': '🎪',
                'Most Gold Earned': '💎',
                'Fastest Win': '⚡',
                'Best Deathless Game': '🛡️',
            }

            # Show exactly these 5 records in order
            priority_records = ['Best CS/min', 'Fastest Win', 'Most Damage', 'Best Vision Score', 'Best KDA']

            # Filter to get only the priority records
            records_to_show = []
            for priority_name in priority_records:
                for record in records_list:
                    if record['record'] == priority_name:
                        records_to_show.append(record)
                        break

            # Single column layout with clean spacing
            x_center = 540
            card_width = 700
            y_start = 270
            row_height = 155

            for i, record in enumerate(records_to_show):
                record_name = record['record']
                value = record['value']
                champion = record['champion']
                emoji = emoji_map.get(record_name, '🏆')

                y = y_start + (i * row_height)

                # Emoji
                painter.setFont(QFont("Arial", 36))
                painter.setPen(QColor(COLORS['gold']))
                painter.drawText(x_center - card_width//2, y, card_width, 45, Qt.AlignmentFlag.AlignCenter, emoji)

                # Record name
                painter.setFont(QFont("Arial", 18, QFont.Weight.Bold))
                painter.setPen(QColor("#5B5A56"))
                painter.drawText(x_center - card_width//2, y + 45, card_width, 28, Qt.AlignmentFlag.AlignCenter, record_name.upper())

                # Value - format KDA specially
                if record_name == 'Best KDA' and '(' in value:
                    # Split "28.0 (12/0/16)" into main KDA and breakdown
                    main_kda = value.split('(')[0].strip()
                    breakdown = value.split('(')[1].replace(')', '').strip()

                    painter.setFont(QFont("Arial", 40, QFont.Weight.Bold))
                    painter.setPen(QColor(COLORS['text_bright']))
                    painter.drawText(x_center - card_width//2, y + 73, card_width, 48, Qt.AlignmentFlag.AlignCenter, main_kda)

                    # Breakdown
                    painter.setFont(QFont("Arial", 16))
                    painter.setPen(QColor("#5B5A56"))
                    painter.drawText(x_center - card_width//2, y + 115, card_width, 24, Qt.AlignmentFlag.AlignCenter, breakdown)
                else:
                    painter.setFont(QFont("Arial", 40, QFont.Weight.Bold))
                    painter.setPen(QColor(COLORS['text_bright']))
                    painter.drawText(x_center - card_width//2, y + 73, card_width, 48, Qt.AlignmentFlag.AlignCenter, value)

                # Champion name
                painter.setFont(QFont("Arial", 16))
                painter.setPen(QColor("#A89968"))
                painter.drawText(x_center - card_width//2, y + 121, card_width, 24, Qt.AlignmentFlag.AlignCenter, f"on {champion}")

        except (AttributeError, KeyError, TypeError, ValueError) as e:
            painter.setFont(QFont("Arial", 32))
            painter.setPen(QColor(COLORS['text']))
            painter.drawText(0, 500, 1080, 100, Qt.AlignmentFlag.AlignCenter, "Records unavailable")

        # Footer
        painter.setFont(QFont("Arial", 18))
        painter.setPen(QColor("#5B5A56"))
        painter.drawText(0, 1020, 1080, 40, Qt.AlignmentFlag.AlignCenter, "© RiftRetreat")

        painter.end()
        return pixmap

    def _export_card(self):
        """Export current card as PNG."""
        if not hasattr(self, 'current_pixmap'):
            QMessageBox.warning(self, "No Preview", "Please generate a preview first.")
            return

        card_type = self.card_type_combo.currentText().replace(" - ", "_").replace(" ", "_")
        default_name = f"LoL_Stat_Card_{card_type}.png"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Stat Card",
            default_name,
            "PNG Image (*.png)"
        )

        if file_path:
            try:
                self.current_pixmap.save(file_path, "PNG")
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Stat card exported to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    f"Failed to export card:\n{str(e)}"
                )
