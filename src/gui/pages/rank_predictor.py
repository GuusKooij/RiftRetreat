"""Rank Predictor page: Shows predicted rank based on performance stats."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QProgressBar
)
from PyQt6.QtCore import Qt

from src.gui.theme import COLORS
from src.analytics.rank_predictor import RankPredictor, RANK_ORDER, RANK_AVERAGES


class RankPredictorPage(QWidget):
    def __init__(self):
        super().__init__()
        self.predictor = None
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
        title = QLabel("🏅 Rank Predictor")
        title.setStyleSheet(f"color: {COLORS['gold']}; font-size: 32px; font-weight: bold;")
        self.layout_main.addWidget(title)

        desc = QLabel("Based on your performance stats, here's what rank you play at:")
        desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 14px; margin-bottom: 12px;")
        self.layout_main.addWidget(desc)

        self.layout_main.addStretch()

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def update_data(self, matches: list, current_rank: str = None):
        """Update with new match data and optional current rank."""
        self.predictor = RankPredictor(matches, current_rank=current_rank)
        self._refresh_predictions()

    def _refresh_predictions(self):
        """Refresh the predictions display."""
        # Clear existing content (except title and description)
        while self.layout_main.count() > 3:
            child = self.layout_main.takeAt(3)
            if child.widget():
                child.widget().deleteLater()

        if not self.predictor:
            return

        prediction = self.predictor.get_rank_prediction()

        if not prediction['player_stats']:
            no_data = QLabel("⚠️ No match data available. Refresh your data in Settings.")
            no_data.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 16px;")
            self.layout_main.insertWidget(2, no_data)
            return

        # Per-role predictions (new feature!)
        if prediction.get('role_predictions'):
            self._add_role_predictions(prediction)

        # Overall prediction card
        self._add_overall_prediction(prediction)

        # Stat breakdown
        self._add_stat_breakdown(prediction)

        # Insights
        self._add_insights(prediction)

        # Rank comparison selector would go here
        # For now, just show comparison to predicted rank
        self._add_rank_comparison(prediction['overall_prediction'])

        self.layout_main.addStretch()

    def _add_role_predictions(self, prediction: dict):
        """Add per-role rank predictions."""
        role_predictions = prediction.get('role_predictions', {})
        role_games = prediction.get('role_games', {})
        best_role = prediction.get('best_role')

        if not role_predictions:
            return

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("🎯 Rank by Role (Min. 5 games)")
        title.setStyleSheet(f"color: {COLORS['text']}; font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel("Your predicted rank for each role you've played:")
        desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px;")
        layout.addWidget(desc)

        # Role order for display
        role_order = ['TOP', 'JUNGLE', 'MID', 'BOT', 'SUPPORT']

        # Create horizontal layout for role boxes
        roles_row = QHBoxLayout()
        roles_row.setSpacing(12)

        for role in role_order:
            if role not in role_predictions:
                continue

            predicted_rank = role_predictions[role]
            games = role_games.get(role, 0)
            is_best = (role == best_role)

            # Role box
            role_box = QFrame()
            border_color = COLORS['gold'] if is_best else COLORS['border']
            role_box.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_dark']};
                    border: {'3px' if is_best else '2px'} solid {border_color};
                    border-radius: 8px;
                    padding: 16px 12px;
                }}
            """)

            role_layout = QVBoxLayout(role_box)
            role_layout.setSpacing(8)
            role_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Role name
            role_label = QLabel(role)
            role_label.setStyleSheet(f"color: {COLORS['text']}; font-size: 13px; font-weight: bold;")
            role_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            role_layout.addWidget(role_label)

            # Predicted rank
            rank_label = QLabel(predicted_rank)
            rank_color = self._get_rank_color(predicted_rank)
            rank_label.setStyleSheet(f"color: {rank_color}; font-size: 20px; font-weight: bold;")
            rank_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            role_layout.addWidget(rank_label)

            # Game count
            games_label = QLabel(f"{games} games")
            games_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px;")
            games_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            role_layout.addWidget(games_label)

            # Best role indicator
            if is_best:
                best_label = QLabel("⭐ BEST")
                best_label.setStyleSheet(f"color: {COLORS['gold']}; font-size: 9px; font-weight: bold;")
                best_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                role_layout.addWidget(best_label)

            roles_row.addWidget(role_box)

        roles_row.addStretch()
        layout.addLayout(roles_row)

        self.layout_main.insertWidget(2, card)

    def _add_overall_prediction(self, prediction: dict):
        """Add overall rank prediction card."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['gold']}, stop:1 {COLORS['gold_dark']});
                border-radius: 12px;
                padding: 24px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        title = QLabel("Overall Predicted Rank")
        title.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        rank_label = QLabel(prediction['overall_prediction'])
        rank_label.setStyleSheet("color: white; font-size: 40px; font-weight: bold;")
        rank_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(rank_label)

        subtitle = QLabel("Across all roles")
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 11px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        self.layout_main.insertWidget(2, card)

    def _add_stat_breakdown(self, prediction: dict):
        """Add per-role stat breakdown."""
        # Get role predictions data
        role_predictions = prediction.get('role_predictions', {})
        role_games = prediction.get('role_games', {})

        if not role_predictions:
            return

        # Get per-role stats from predictor
        role_data = self.predictor.get_rank_predictions_by_role()
        role_stats_all = role_data.get('role_stats', {})

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        title = QLabel("📊 Stats by Role")
        title.setStyleSheet(f"color: {COLORS['text']}; font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel("Detailed breakdown of your performance stats for each role (min. 5 games):")
        desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px;")
        layout.addWidget(desc)

        # Role order for display
        role_order = ['TOP', 'JUNGLE', 'MID', 'BOT', 'SUPPORT']

        stat_display_order = [
            ('kda', 'KDA', '%.2f'),
            ('cs_per_min', 'CS/min', '%.1f'),
            ('vision_score_per_min', 'Vision/min', '%.2f'),
            ('damage_per_min', 'Dmg/min', '%.0f'),
            ('gold_per_min', 'Gold/min', '%.0f'),
            ('kill_participation', 'KP', '%.0f%%'),
        ]

        for role in role_order:
            if role not in role_predictions:
                continue

            predicted_rank = role_predictions[role]
            games = role_games.get(role, 0)
            role_stats = role_stats_all.get(role, {})

            # Role header
            role_header = QFrame()
            role_header.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_dark']};
                    border-radius: 6px;
                    padding: 12px;
                    border-left: 4px solid {COLORS['gold']};
                }}
            """)
            role_header_layout = QHBoxLayout(role_header)
            role_header_layout.setContentsMargins(12, 8, 12, 8)

            role_name_label = QLabel(f"{role}")
            role_name_label.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold; font-size: 16px;")
            role_header_layout.addWidget(role_name_label)

            role_rank_label = QLabel(f"{predicted_rank}")
            rank_color = self._get_rank_color(predicted_rank)
            role_rank_label.setStyleSheet(f"color: {rank_color}; font-weight: bold; font-size: 16px;")
            role_header_layout.addWidget(role_rank_label)

            role_games_label = QLabel(f"({games} games)")
            role_games_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px;")
            role_header_layout.addWidget(role_games_label)

            role_header_layout.addStretch()

            layout.addWidget(role_header)

            # Stats for this role
            for stat_key, stat_name, fmt in stat_display_order:
                if stat_key not in role_stats:
                    continue

                stat_value = role_stats[stat_key]

                # Skip CS/min if < 1.0
                if stat_key == 'cs_per_min' and stat_value < 1.0:
                    continue

                # Format value
                if stat_key == 'kill_participation':
                    # KP is already stored as percentage (54.0 = 54%)
                    display_value = fmt % stat_value
                else:
                    display_value = fmt % stat_value

                # Predict rank for this specific stat
                predicted_stat_rank = self.predictor.predict_rank_for_stat(stat_key, stat_value)

                self._add_stat_row_compact(layout, stat_name, display_value, predicted_stat_rank)

        self.layout_main.insertWidget(3, card)

    def _add_stat_row(self, parent_layout: QVBoxLayout, stat_name: str,
                      stat_value: str, predicted_rank: str):
        """Add a single stat row with rank bar."""
        row = QFrame()
        row.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_dark']};
                border-radius: 6px;
                padding: 12px;
            }}
        """)

        row_layout = QVBoxLayout(row)
        row_layout.setSpacing(8)

        # Stat name and value
        top_row = QHBoxLayout()
        name_label = QLabel(stat_name)
        name_label.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold; font-size: 13px;")
        top_row.addWidget(name_label)

        value_label = QLabel(stat_value)
        value_label.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; font-size: 13px;")
        top_row.addWidget(value_label)
        top_row.addStretch()

        rank_label = QLabel(predicted_rank)
        rank_color = self._get_rank_color(predicted_rank)
        rank_label.setStyleSheet(f"color: {rank_color}; font-weight: bold; font-size: 14px;")
        top_row.addWidget(rank_label)

        row_layout.addLayout(top_row)

        # Rank progress bar
        rank_bar = self._create_rank_bar(predicted_rank)
        row_layout.addWidget(rank_bar)

        parent_layout.addWidget(row)

    def _add_stat_row_compact(self, parent_layout: QVBoxLayout, stat_name: str,
                             stat_value: str, predicted_rank: str):
        """Add a compact stat row with rank bar (for per-role view)."""
        row = QFrame()
        row.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(30, 35, 40, 0.5);
                border-radius: 4px;
                padding: 8px 12px;
                margin-left: 20px;
            }}
        """)

        row_layout = QVBoxLayout(row)
        row_layout.setSpacing(6)

        # Stat name and value
        top_row = QHBoxLayout()
        name_label = QLabel(stat_name)
        name_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px;")
        name_label.setFixedWidth(80)
        top_row.addWidget(name_label)

        value_label = QLabel(stat_value)
        value_label.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold; font-size: 12px;")
        value_label.setFixedWidth(70)
        top_row.addWidget(value_label)

        rank_label = QLabel(predicted_rank)
        rank_color = self._get_rank_color(predicted_rank)
        rank_label.setStyleSheet(f"color: {rank_color}; font-weight: bold; font-size: 12px;")
        top_row.addWidget(rank_label)

        top_row.addStretch()

        row_layout.addLayout(top_row)

        # Rank progress bar (smaller)
        rank_bar = self._create_rank_bar(predicted_rank)
        rank_bar.setFixedHeight(4)
        row_layout.addWidget(rank_bar)

        parent_layout.addWidget(row)

    def _create_rank_bar(self, predicted_rank: str) -> QProgressBar:
        """Create a progress bar showing rank position."""
        progress = QProgressBar()
        progress.setTextVisible(False)
        progress.setFixedHeight(8)

        # Calculate position (0-100)
        try:
            rank_idx = RANK_ORDER.index(predicted_rank)
            value = int((rank_idx / (len(RANK_ORDER) - 1)) * 100)
        except ValueError:
            value = 0

        progress.setValue(value)

        rank_color = self._get_rank_color(predicted_rank)
        progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['border']};
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {rank_color};
                border-radius: 4px;
            }}
        """)

        return progress

    def _get_rank_color(self, rank: str) -> str:
        """Get color for rank."""
        color_map = {
            'Iron': '#4D4D4D',
            'Bronze': '#8B4513',
            'Silver': '#C0C0C0',
            'Gold': COLORS['gold'],
            'Platinum': '#00CED1',
            'Emerald': '#50C878',
            'Diamond': '#B9F2FF',
            'Master+': '#9370DB',
        }
        return color_map.get(rank, COLORS['text'])

    def _add_insights(self, prediction: dict):
        """Add insights section."""
        insights = prediction.get('insights', [])
        if not insights:
            return

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("💡 Insights")
        title.setStyleSheet(f"color: {COLORS['text']}; font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        for insight in insights:
            insight_label = QLabel(insight)
            insight_label.setStyleSheet(f"""
                color: {COLORS['text']};
                font-size: 14px;
                padding: 8px;
                background-color: {COLORS['bg_dark']};
                border-radius: 4px;
                border-left: 3px solid {COLORS['gold']};
            """)
            insight_label.setWordWrap(True)
            layout.addWidget(insight_label)

        self.layout_main.insertWidget(4, card)

    def _add_rank_comparison(self, target_rank: str):
        """Add comparison to target rank."""
        if not self.predictor:
            return

        comparison = self.predictor.compare_to_rank(target_rank)
        if not comparison:
            return

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel(f"📈 Comparison to {target_rank} Average")
        title.setStyleSheet(f"color: {COLORS['text']}; font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel(f"How your stats compare to average {target_rank} players:")
        desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px;")
        layout.addWidget(desc)

        # Stats comparison
        for stat_name, comp in comparison.items():
            stat_display = self.predictor._format_stat_name(stat_name)
            diff = comp['diff_pct']

            if diff >= 0:
                diff_color = COLORS['green']
                diff_text = f"+{diff}%"
                icon = "✓"
            else:
                diff_color = COLORS['red']
                diff_text = f"{diff}%"
                icon = "✗"

            row = QHBoxLayout()

            status_label = QLabel(icon)
            status_label.setFixedWidth(20)
            status_label.setStyleSheet(f"color: {diff_color}; font-weight: bold; font-size: 16px;")
            row.addWidget(status_label)

            name_label = QLabel(stat_display)
            name_label.setStyleSheet(f"color: {COLORS['text']}; font-size: 13px;")
            name_label.setFixedWidth(150)
            row.addWidget(name_label)

            diff_label = QLabel(diff_text)
            diff_label.setStyleSheet(f"color: {diff_color}; font-weight: bold; font-size: 13px;")
            diff_label.setFixedWidth(80)
            row.addWidget(diff_label)

            values_label = QLabel(f"({comp['player']:.1f} vs {comp['target']:.1f})")
            values_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px;")
            row.addWidget(values_label)

            row.addStretch()

            layout.addLayout(row)

        self.layout_main.insertWidget(5, card)
