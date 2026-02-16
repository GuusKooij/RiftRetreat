"""Coaching Report page: improvement areas, off-meta index, tilt assessment, vision, champion pool."""

import os
import webbrowser

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QPushButton, QProgressBar
)
from PyQt6.QtCore import Qt

from src.analytics.coaching_report import CoachingReportGenerator
from src.gui.theme import COLORS


class CoachingReportPage(QWidget):
    def __init__(self):
        super().__init__()
        self.report_gen = None
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
        title = QLabel("Coaching Report")
        title.setStyleSheet(f"color: {COLORS['gold']}; font-size: 22px; font-weight: bold;")
        self.layout_main.addWidget(title)

        subtitle = QLabel("Personalized improvement areas and assessments based on your match data")
        subtitle.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px;")
        self.layout_main.addWidget(subtitle)

        # Export button
        self.export_btn = QPushButton("Export as HTML")
        self.export_btn.setFixedWidth(160)
        self.export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['gold_dark']};
                color: {COLORS['text_bright']};
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['gold']};
                color: {COLORS['bg_dark']};
            }}
        """)
        self.export_btn.clicked.connect(self._on_export)
        self.layout_main.addWidget(self.export_btn)

        # Content area
        self.content_area = QVBoxLayout()
        self.layout_main.addLayout(self.content_area)

        # Placeholder
        placeholder = QLabel("Load your data from Settings to generate your coaching report")
        placeholder.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 14px;")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_area.addWidget(placeholder)

        self.layout_main.addStretch()

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def update_data(self, matches, stats_analyzer, tilt_detector, champion_analyzer,
                    current_rank=None, data_dragon=None):
        self.report_gen = CoachingReportGenerator(
            matches, stats_analyzer, tilt_detector, champion_analyzer,
            current_rank=current_rank, data_dragon=data_dragon
        )
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

    def _populate(self):
        self._clear_content()

        if not self.report_gen:
            return

        # ---- Top Improvement Areas ----
        improvements = self.report_gen.get_improvement_areas()
        card, layout = self._card("Top Improvement Areas")

        if improvements:
            for i, imp in enumerate(improvements, 1):
                imp_frame = QFrame()
                imp_frame.setStyleSheet(f"""
                    QFrame {{
                        background-color: {COLORS['bg_main']};
                        border-left: 3px solid {COLORS['red']};
                        border-radius: 4px;
                        padding: 2px;
                    }}
                """)
                imp_layout = QVBoxLayout(imp_frame)
                imp_layout.setContentsMargins(12, 8, 12, 8)
                imp_layout.setSpacing(4)

                header = QHBoxLayout()
                stat_label = QLabel(f"#{i} {imp['stat']}")
                stat_label.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold; border: none;")
                header.addWidget(stat_label)

                gap_color = COLORS['red'] if imp['gap_percent'] < 0 else COLORS['green']
                gap_label = QLabel(f"{imp['player_value']} vs {imp['rank_average']} ({imp['gap_percent']:+.0f}%)")
                gap_label.setStyleSheet(f"color: {gap_color}; font-size: 11px; border: none;")
                header.addWidget(gap_label)

                header.addStretch()
                imp_layout.addLayout(header)

                rec = QLabel(imp['recommendation'])
                rec.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
                rec.setWordWrap(True)
                imp_layout.addWidget(rec)

                layout.addWidget(imp_frame)
        else:
            good = QLabel("No major weaknesses! You're performing at or above your rank.")
            good.setStyleSheet(f"color: {COLORS['green']}; font-weight: bold; border: none;")
            layout.addWidget(good)

        self.content_area.addWidget(card)

        # ---- Off-Meta Index ----
        off_meta = self.report_gen.get_off_meta_index()
        card, layout = self._card("Off-Meta Index")

        index_row = QHBoxLayout()
        index_val = QLabel(f"{off_meta['index']}%")
        idx_color = COLORS['green'] if off_meta['index'] <= 15 else (COLORS['orange'] if off_meta['index'] <= 30 else COLORS['red'])
        index_val.setStyleSheet(f"color: {idx_color}; font-size: 24px; font-weight: bold; border: none;")
        index_row.addWidget(index_val)

        index_desc = QLabel(f"of games on sub-48% WR champions ({off_meta['off_meta_games']}/{off_meta['total_games']})")
        index_desc.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
        index_row.addWidget(index_desc)
        index_row.addStretch()
        layout.addLayout(index_row)

        assessment = QLabel(off_meta['assessment'])
        assessment.setStyleSheet(f"color: {COLORS['text']}; border: none;")
        assessment.setWordWrap(True)
        layout.addWidget(assessment)

        self.content_area.addWidget(card)

        # ---- Champion Pool ----
        champ_pool = self.report_gen.get_champion_pool_assessment()
        if champ_pool:
            card, layout = self._card("Champion Pool Assessment")

            diversity = QLabel(f"Pool Type: {champ_pool['diversity']}")
            diversity.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold; border: none;")
            layout.addWidget(diversity)

            stats_text = (
                f"Unique champions: {champ_pool['unique_champions']} | "
                f"Main champions (5+G): {champ_pool['main_champions']} | "
                f"Main avg WR: {champ_pool['avg_main_winrate']}%"
            )
            stats_label = QLabel(stats_text)
            stats_label.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
            layout.addWidget(stats_label)

            top = QLabel(f"Most played: {champ_pool['top_champion']} ({champ_pool['top_champion_share']}% of games)")
            top.setStyleSheet(f"color: {COLORS['text']}; border: none;")
            layout.addWidget(top)

            advice = QLabel(champ_pool['advice'])
            advice.setStyleSheet(f"color: {COLORS['orange']}; font-style: italic; border: none;")
            advice.setWordWrap(True)
            layout.addWidget(advice)

            self.content_area.addWidget(card)

        # ---- Vision Assessment ----
        vision = self.report_gen.get_vision_assessment()
        if vision:
            card, layout = self._card("Vision Assessment")

            vision_row = QHBoxLayout()
            for label, value in [
                ("Vision/min", f"{vision['vision_per_min']}"),
                ("Rank avg", f"{vision['rank_average']}"),
                ("Wards/game", f"{vision['avg_wards_placed']}"),
                ("Control Wards", f"{vision['avg_control_wards']}"),
                ("Wards Killed", f"{vision['avg_wards_killed']}"),
            ]:
                col = QVBoxLayout()
                val = QLabel(str(value))
                val.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold; font-size: 14px; border: none;")
                val.setAlignment(Qt.AlignmentFlag.AlignCenter)
                col.addWidget(val)

                desc = QLabel(label)
                desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; border: none;")
                desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
                col.addWidget(desc)

                vision_row.addLayout(col)

            vision_row.addStretch()
            layout.addLayout(vision_row)

            for tip in vision.get('tips', []):
                tip_label = QLabel(f"  {tip}")
                tip_label.setStyleSheet(f"color: {COLORS['orange']}; font-size: 11px; border: none;")
                tip_label.setWordWrap(True)
                layout.addWidget(tip_label)

            self.content_area.addWidget(card)

        # ---- Tilt Assessment ----
        tilt = self.report_gen.get_tilt_assessment()
        if tilt:
            card, layout = self._card("Tilt Assessment")

            tilt_row = QHBoxLayout()
            for label, value in [
                ("Losing Streaks", str(tilt.get('losing_streaks', 0))),
                ("Avg Session", f"{tilt.get('avg_session_length', 0)} games"),
                ("Longest Session", f"{tilt.get('worst_session_length', 0)} games"),
            ]:
                col = QVBoxLayout()
                val = QLabel(str(value))
                val.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold; font-size: 14px; border: none;")
                val.setAlignment(Qt.AlignmentFlag.AlignCenter)
                col.addWidget(val)

                desc = QLabel(label)
                desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; border: none;")
                desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
                col.addWidget(desc)

                tilt_row.addLayout(col)

            tilt_row.addStretch()
            layout.addLayout(tilt_row)

            if tilt.get('best_time'):
                best = QLabel(f"Best time to play: {tilt['best_time']}")
                best.setStyleSheet(f"color: {COLORS['green']}; border: none;")
                layout.addWidget(best)

            if tilt.get('worst_time'):
                worst = QLabel(f"Worst time to play: {tilt['worst_time']}")
                worst.setStyleSheet(f"color: {COLORS['red']}; border: none;")
                layout.addWidget(worst)

            for tip in tilt.get('tips', []):
                tip_label = QLabel(f"  {tip}")
                tip_label.setStyleSheet(f"color: {COLORS['orange']}; font-size: 11px; border: none;")
                tip_label.setWordWrap(True)
                layout.addWidget(tip_label)

            self.content_area.addWidget(card)

    def _on_export(self):
        if not self.report_gen:
            return

        path = self.report_gen.export_html()
        if os.path.exists(path):
            webbrowser.open(f'file://{os.path.abspath(path)}')
