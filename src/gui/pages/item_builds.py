"""Item Builds page: per-champion item win rate analysis."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from src.analytics.item_analysis import ItemBuildAnalyzer
from src.gui.theme import COLORS


class ItemBuildsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.data_dragon = None
        self.analyzer = None
        self._all_data = []
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
        title = QLabel("Item Build Analysis")
        title.setStyleSheet(f"color: {COLORS['gold']}; font-size: 22px; font-weight: bold;")
        self.layout_main.addWidget(title)

        subtitle = QLabel("Which items correlate with wins on each champion")
        subtitle.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px;")
        self.layout_main.addWidget(subtitle)

        # Champion selector
        selector_row = QHBoxLayout()
        selector_label = QLabel("Champion:")
        selector_label.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold;")
        selector_row.addWidget(selector_label)

        self.champ_combo = QComboBox()
        self.champ_combo.setFixedWidth(200)
        self.champ_combo.addItem("All Champions")
        self.champ_combo.currentIndexChanged.connect(self._on_champion_changed)
        selector_row.addWidget(self.champ_combo)

        selector_row.addStretch()
        self.layout_main.addLayout(selector_row)

        # Content area
        self.content_area = QVBoxLayout()
        self.layout_main.addLayout(self.content_area)

        # Placeholder
        self.placeholder = QLabel("Load your data from Settings to see item analysis")
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
        self.analyzer = ItemBuildAnalyzer(matches, data_dragon)
        self._all_data = self.analyzer.items_by_champion(min_games=3)

        # Populate champion selector
        self.champ_combo.blockSignals(True)
        self.champ_combo.clear()
        self.champ_combo.addItem("All Champions")
        for entry in self._all_data:
            self.champ_combo.addItem(entry['champion'])
        self.champ_combo.blockSignals(False)

        self._show_all_champions()

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

    def _item_icon(self, item_id: int, size: int = 24) -> QLabel:
        label = QLabel()
        label.setFixedSize(size, size)
        label.setStyleSheet("border: none; background: transparent;")

        if self.data_dragon and item_id:
            icon_path = self.data_dragon.get_item_icon_path(item_id)
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

    def _champion_icon(self, champion_name: str, size: int = 28) -> QLabel:
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
        return label

    def _on_champion_changed(self, index: int):
        if index == 0:
            self._show_all_champions()
        else:
            champ_name = self.champ_combo.currentText()
            self._show_single_champion(champ_name)

    def _show_all_champions(self):
        """Show overview of all champions' core items."""
        self._clear_content()

        if not self._all_data:
            return

        # Boots analysis
        if self.analyzer:
            boots = self.analyzer.boots_analysis(min_games=3)
            if boots:
                card, layout = self._card("Boots Win Rate")
                for b in boots:
                    row = QHBoxLayout()
                    row.setSpacing(8)

                    row.addWidget(self._item_icon(b['item_id'], 24))

                    name = QLabel(b['item_name'])
                    name.setFixedWidth(160)
                    name.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold; border: none;")
                    row.addWidget(name)

                    games = QLabel(f"{b['games']} games")
                    games.setFixedWidth(70)
                    games.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
                    row.addWidget(games)

                    wr_color = COLORS['green'] if b['winrate'] >= 50 else COLORS['red']
                    wr = QLabel(f"{b['winrate']}%")
                    wr.setStyleSheet(f"color: {wr_color}; font-weight: bold; border: none;")
                    row.addWidget(wr)

                    row.addStretch()
                    layout.addLayout(row)

                self.content_area.addWidget(card)

        # Per-champion item breakdown
        for entry in self._all_data:
            if not entry['core_items']:
                continue

            card, layout = self._card(f"{entry['champion']} ({entry['total_games']}G, {entry['winrate']}% WR)")

            for item in entry['core_items'][:5]:
                row = QHBoxLayout()
                row.setSpacing(8)

                row.addWidget(self._item_icon(item['item_id'], 24))

                name = QLabel(item['item_name'])
                name.setFixedWidth(180)
                name.setStyleSheet(f"color: {COLORS['text']}; border: none;")
                row.addWidget(name)

                games = QLabel(f"{item['games']} games ({item['pick_rate']}%)")
                games.setFixedWidth(120)
                games.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
                row.addWidget(games)

                wr_color = COLORS['green'] if item['winrate'] >= 50 else COLORS['red']
                wr = QLabel(f"{item['winrate']}% WR")
                wr.setStyleSheet(f"color: {wr_color}; font-weight: bold; border: none;")
                row.addWidget(wr)

                row.addStretch()
                layout.addLayout(row)

            self.content_area.addWidget(card)

    def _show_single_champion(self, champion: str):
        """Show detailed item analysis for a single champion."""
        self._clear_content()

        if not self.analyzer:
            return

        # Find this champion in data
        champ_data = None
        for entry in self._all_data:
            if entry['champion'] == champion:
                champ_data = entry
                break

        if not champ_data:
            return

        # Core items card
        if champ_data['core_items']:
            card, layout = self._card(f"Core Items - {champion}")

            header = QLabel(f"{champ_data['total_games']} games, {champ_data['winrate']}% overall WR")
            header.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
            layout.addWidget(header)

            for item in champ_data['core_items']:
                row = QHBoxLayout()
                row.setSpacing(8)

                row.addWidget(self._item_icon(item['item_id'], 28))

                name = QLabel(item['item_name'])
                name.setFixedWidth(180)
                name.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold; border: none;")
                row.addWidget(name)

                games = QLabel(f"{item['games']} games ({item['pick_rate']}% pick rate)")
                games.setFixedWidth(160)
                games.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
                row.addWidget(games)

                record = QLabel(f"{item['wins']}W-{item['losses']}L")
                record.setFixedWidth(60)
                record.setStyleSheet(f"color: {COLORS['text']}; border: none;")
                row.addWidget(record)

                wr_color = COLORS['green'] if item['winrate'] >= 50 else COLORS['red']
                wr = QLabel(f"{item['winrate']}%")
                wr.setStyleSheet(f"color: {wr_color}; font-weight: bold; border: none;")
                row.addWidget(wr)

                # Comparison to overall WR
                diff = item['winrate'] - champ_data['winrate']
                diff_color = COLORS['green'] if diff > 0 else COLORS['red']
                diff_label = QLabel(f"({diff:+.1f}%)")
                diff_label.setStyleSheet(f"color: {diff_color}; font-size: 11px; border: none;")
                row.addWidget(diff_label)

                row.addStretch()
                layout.addLayout(row)

            self.content_area.addWidget(card)

        # First item analysis
        first_items = self.analyzer.first_item_analysis(champion, min_games=2)
        if first_items:
            card, layout = self._card(f"Core Item Comparison - {champion}")
            desc = QLabel("Win rate by most expensive completed item (proxy for first/core item)")
            desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
            layout.addWidget(desc)

            for item in first_items:
                row = QHBoxLayout()
                row.setSpacing(8)

                row.addWidget(self._item_icon(item['item_id'], 28))

                name = QLabel(item['item_name'])
                name.setFixedWidth(180)
                name.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold; border: none;")
                row.addWidget(name)

                games = QLabel(f"{item['games']} games")
                games.setFixedWidth(80)
                games.setStyleSheet(f"color: {COLORS['text_dim']}; border: none;")
                row.addWidget(games)

                wr_color = COLORS['green'] if item['winrate'] >= 50 else COLORS['red']
                wr = QLabel(f"{item['winrate']}% WR")
                wr.setStyleSheet(f"color: {wr_color}; font-weight: bold; border: none;")
                row.addWidget(wr)

                row.addStretch()
                layout.addLayout(row)

            self.content_area.addWidget(card)
