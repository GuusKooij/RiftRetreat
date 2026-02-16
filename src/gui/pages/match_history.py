"""Match History page: Scrollable list of matches with expandable details."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QComboBox, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from src.gui.theme import COLORS


class MatchHistoryPage(QWidget):
    def __init__(self):
        super().__init__()
        self.all_matches = []
        self.dd = None  # DataDragon for item names
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # Filters
        filter_layout = QHBoxLayout()

        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold;")
        filter_layout.addWidget(filter_label)

        self.queue_filter = QComboBox()
        self.queue_filter.addItems(["All Queues", "Solo/Duo", "Flex"])
        self.queue_filter.currentIndexChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.queue_filter)

        self.result_filter = QComboBox()
        self.result_filter.addItems(["All Results", "Wins", "Losses"])
        self.result_filter.currentIndexChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.result_filter)

        self.role_filter = QComboBox()
        self.role_filter.addItems(["All Roles", "TOP", "JUNGLE", "MIDDLE", "BOTTOM", "SUPPORT"])
        self.role_filter.currentIndexChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.role_filter)

        self.champ_filter = QComboBox()
        self.champ_filter.addItems(["All Champions"])
        self.champ_filter.currentIndexChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.champ_filter)

        filter_layout.addStretch()

        self.count_label = QLabel()
        self.count_label.setStyleSheet(f"color: {COLORS['text_dim']};")
        filter_layout.addWidget(self.count_label)

        layout.addLayout(filter_layout)

        # Scroll area for matches
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.match_container = QWidget()
        self.match_layout = QVBoxLayout(self.match_container)
        self.match_layout.setSpacing(4)
        self.match_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll.setWidget(self.match_container)
        layout.addWidget(self.scroll)

    def update_data(self, matches: list[dict], data_dragon=None):
        self.all_matches = sorted(matches, key=lambda m: m['game_start'], reverse=True)
        if data_dragon:
            self.dd = data_dragon

        # Populate champion filter
        champs = sorted({m.get('champion', '?') for m in matches})
        self.champ_filter.blockSignals(True)
        self.champ_filter.clear()
        self.champ_filter.addItems(["All Champions"] + champs)
        self.champ_filter.blockSignals(False)

        self._apply_filters()

    def _apply_filters(self):
        filtered = self.all_matches

        queue_idx = self.queue_filter.currentIndex()
        if queue_idx == 1:
            filtered = [m for m in filtered if m['queue_id'] == 420]
        elif queue_idx == 2:
            filtered = [m for m in filtered if m['queue_id'] == 440]

        result_idx = self.result_filter.currentIndex()
        if result_idx == 1:
            filtered = [m for m in filtered if m['win']]
        elif result_idx == 2:
            filtered = [m for m in filtered if not m['win']]

        role_text = self.role_filter.currentText()
        if role_text != "All Roles":
            # Match data stores UTILITY for support
            match_role = 'UTILITY' if role_text == 'SUPPORT' else role_text
            filtered = [m for m in filtered if m.get('role') == match_role]

        champ_text = self.champ_filter.currentText()
        if champ_text != "All Champions":
            filtered = [m for m in filtered if m.get('champion') == champ_text]

        self.count_label.setText(f"{len(filtered)} matches")
        self._render_matches(filtered)

    def _render_matches(self, matches):
        while self.match_layout.count():
            child = self.match_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for m in matches:
            self.match_layout.addWidget(self._create_match_widget(m))

        self.match_layout.addStretch()

    def _create_match_widget(self, m: dict) -> QFrame:
        """Create a match row with a clickable header and expandable details."""
        container = QFrame()
        border_color = COLORS['green'] if m['win'] else COLORS['red']
        container.setStyleSheet(f"""
            QFrame#match_container {{
                background-color: {COLORS['bg_card']};
                border-left: 4px solid {border_color};
                border-radius: 4px;
            }}
        """)
        container.setObjectName("match_container")

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # --- Header row (always visible) ---
        header = QWidget()
        header.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(16)

        # Result
        result = QLabel("W" if m['win'] else "L")
        result.setFixedWidth(24)
        result.setStyleSheet(f"color: {border_color}; font-weight: bold; font-size: 16px;")
        header_layout.addWidget(result)

        # Champion icon
        champ_name = m.get('champion', '?')
        icon_label = QLabel()
        icon_label.setFixedSize(32, 32)
        if self.dd:
            icon_path = self.dd.get_champion_icon_path(champ_name)
            if icon_path:
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    icon_label.setPixmap(pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        icon_label.setStyleSheet("border-radius: 4px;")
        header_layout.addWidget(icon_label)

        # Champion name
        champ = QLabel(champ_name)
        champ.setFixedWidth(100)
        champ.setStyleSheet("font-weight: bold; font-size: 13px;")
        header_layout.addWidget(champ)

        # Role
        role_text_val = m.get('role', '')
        role_display = 'SUPPORT' if role_text_val == 'UTILITY' else role_text_val
        role = QLabel(role_display)
        role.setFixedWidth(70)
        role.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px;")
        header_layout.addWidget(role)

        # KDA
        k, d, a = m['kills'], m['deaths'], m['assists']
        kda_ratio = round((k + a) / max(d, 1), 1)
        kda = QLabel(f"{k}/{d}/{a}  ({kda_ratio})")
        kda.setFixedWidth(110)
        kda_color = COLORS['green'] if kda_ratio >= 3 else (COLORS['red'] if kda_ratio < 2 else COLORS['text'])
        kda.setStyleSheet(f"color: {kda_color}; font-weight: bold;")
        header_layout.addWidget(kda)

        # CS
        cs = QLabel(f"{m['cs']} CS ({m['cs_per_min']}/m)")
        cs.setFixedWidth(110)
        cs.setStyleSheet(f"color: {COLORS['gold']}; font-size: 12px;")
        header_layout.addWidget(cs)

        # Damage
        dmg = QLabel(f"{m['total_damage_dealt']:,} dmg")
        dmg.setFixedWidth(90)
        dmg.setStyleSheet(f"color: {COLORS['orange']}; font-size: 12px;")
        header_layout.addWidget(dmg)

        # Vision
        vis = QLabel(f"VS {m['vision_score']}")
        vis.setFixedWidth(50)
        vis.setStyleSheet(f"color: {COLORS['purple']}; font-size: 12px;")
        header_layout.addWidget(vis)

        # KP
        kp = QLabel(f"{m['kill_participation']}% KP")
        kp.setFixedWidth(60)
        kp.setStyleSheet(f"color: {COLORS['blue']}; font-size: 12px;")
        header_layout.addWidget(kp)

        # Duration
        dur = QLabel(f"{m['game_duration_min']}m")
        dur.setFixedWidth(40)
        dur.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px;")
        header_layout.addWidget(dur)

        # Date
        date = QLabel(m['game_start'][:10])
        date.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px;")
        header_layout.addWidget(date)

        # Queue
        queue = QLabel("Solo" if m['queue_id'] == 420 else "Flex")
        queue.setFixedWidth(35)
        queue.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px;")
        header_layout.addWidget(queue)

        # Expand indicator
        expand_icon = QLabel("+")
        expand_icon.setFixedWidth(16)
        expand_icon.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 14px; font-weight: bold;")
        header_layout.addWidget(expand_icon)

        container_layout.addWidget(header)

        # --- Detail panel (hidden by default) ---
        detail = QFrame()
        detail.setObjectName("match_detail")
        detail.setVisible(False)
        detail.setStyleSheet(f"""
            QFrame#match_detail {{
                background-color: {COLORS['bg_dark']};
                border-top: 1px solid {COLORS['border']};
            }}
        """)

        detail_layout = QVBoxLayout(detail)
        detail_layout.setContentsMargins(16, 12, 16, 12)
        detail_layout.setSpacing(10)

        self._build_detail_content(detail_layout, m)

        container_layout.addWidget(detail)

        # Click to toggle
        def toggle(event, d=detail, icon=expand_icon):
            d.setVisible(not d.isVisible())
            icon.setText("-" if d.isVisible() else "+")

        header.mousePressEvent = toggle

        return container

    def _build_detail_content(self, layout: QVBoxLayout, m: dict):
        """Build the expanded detail content for a match."""

        # --- Items ---
        items = m.get('items', [])
        if items and any(i != 0 for i in items):
            items_row = QHBoxLayout()
            items_label = QLabel("Items:")
            items_label.setFixedWidth(60)
            items_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-weight: bold; font-size: 11px;")
            items_row.addWidget(items_label)

            for item_id in items:
                if item_id == 0:
                    continue
                name = self.dd.get_item_name(item_id) if self.dd else f"Item {item_id}"

                item_widget = QWidget()
                item_lay = QHBoxLayout(item_widget)
                item_lay.setContentsMargins(3, 2, 6, 2)
                item_lay.setSpacing(4)
                item_widget.setStyleSheet(f"""
                    background-color: {COLORS['bg_card']};
                    border-radius: 3px;
                    border: 1px solid {COLORS['border']};
                """)

                if self.dd:
                    icon_path = self.dd.get_item_icon_path(item_id)
                    if icon_path:
                        icon = QLabel()
                        icon.setFixedSize(24, 24)
                        px = QPixmap(icon_path)
                        if not px.isNull():
                            icon.setPixmap(px.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                        icon.setStyleSheet("border: none;")
                        item_lay.addWidget(icon)

                item_name = QLabel(name)
                item_name.setStyleSheet(f"color: {COLORS['text']}; font-size: 10px; border: none;")
                item_lay.addWidget(item_name)

                items_row.addWidget(item_widget)

            items_row.addStretch()
            layout.addLayout(items_row)

        # --- Extended stats ---
        stats_grid = QGridLayout()
        stats_grid.setSpacing(12)

        stat_items = [
            ('Physical Dmg', f"{m.get('physical_damage', 0):,}", COLORS['orange']),
            ('Magic Dmg', f"{m.get('magic_damage', 0):,}", COLORS['purple']),
            ('Dmg Taken', f"{m.get('damage_taken', 0):,}", COLORS['red']),
            ('Gold', f"{m.get('gold_earned', 0):,}", COLORS['gold']),
            ('Wards Placed', str(m.get('wards_placed', 0)), COLORS['blue']),
            ('Wards Killed', str(m.get('wards_killed', 0)), COLORS['blue']),
            ('Control Wards', str(m.get('control_wards', 0)), COLORS['blue']),
            ('Turrets', str(m.get('turret_kills', 0)), COLORS['text']),
            ('Dragons', str(m.get('dragon_kills', 0)), COLORS['text']),
            ('Barons', str(m.get('baron_kills', 0)), COLORS['text']),
        ]

        # Multi-kills
        multis = []
        if m.get('penta_kills', 0):
            multis.append(f"{m['penta_kills']} Penta")
        if m.get('quadra_kills', 0):
            multis.append(f"{m['quadra_kills']} Quadra")
        if m.get('triple_kills', 0):
            multis.append(f"{m['triple_kills']} Triple")
        if m.get('double_kills', 0):
            multis.append(f"{m['double_kills']} Double")
        if multis:
            stat_items.append(('Multi-Kills', ', '.join(multis), COLORS['gold']))

        if m.get('first_blood'):
            stat_items.append(('First Blood', 'Yes', COLORS['red']))

        gold_diff = m.get('game_end_gold_diff')
        if gold_diff is not None:
            color = COLORS['green'] if gold_diff > 0 else COLORS['red']
            stat_items.append(('Gold Diff', f"{gold_diff:+,}", color))

        for i, (label, value, color) in enumerate(stat_items):
            col = i % 4
            row = i // 4

            w = QWidget()
            wl = QVBoxLayout(w)
            wl.setContentsMargins(0, 0, 0, 0)
            wl.setSpacing(1)

            val = QLabel(value)
            val.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px;")
            wl.addWidget(val)

            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px;")
            wl.addWidget(lbl)

            stats_grid.addWidget(w, row, col)

        layout.addLayout(stats_grid)

        # --- Teammates ---
        teammates = m.get('teammates', [])
        if teammates:
            tm_label = QLabel("Your Team:")
            tm_label.setStyleSheet(f"color: {COLORS['green']}; font-weight: bold; font-size: 11px;")
            layout.addWidget(tm_label)

            tm_row = QHBoxLayout()
            for t in teammates:
                name = t.get('summoner_name', '?')
                champ = t.get('champion', '?')
                role = 'SUPPORT' if t.get('role', '') == 'UTILITY' else t.get('role', '')
                tag = t.get('tag_line', '')
                display = f"{name}#{tag}" if tag else name

                card = QWidget()
                card_layout = QHBoxLayout(card)
                card_layout.setContentsMargins(4, 4, 8, 4)
                card_layout.setSpacing(6)
                card.setStyleSheet(f"""
                    background-color: {COLORS['bg_card']};
                    border-radius: 4px;
                    border: 1px solid {COLORS['border']};
                """)

                icon = QLabel()
                icon.setFixedSize(24, 24)
                if self.dd:
                    icon_path = self.dd.get_champion_icon_path(champ)
                    if icon_path:
                        px = QPixmap(icon_path)
                        if not px.isNull():
                            icon.setPixmap(px.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                icon.setStyleSheet("border: none;")
                card_layout.addWidget(icon)

                info = QLabel(f"{champ} ({role})\n{display}")
                info.setStyleSheet(f"color: {COLORS['text']}; font-size: 10px; border: none;")
                card_layout.addWidget(info)

                card.setFixedWidth(170)
                tm_row.addWidget(card)

            tm_row.addStretch()
            layout.addLayout(tm_row)

        # --- Opponents ---
        opponents = m.get('opponents', [])
        if opponents:
            opp_label = QLabel("Enemy Team:")
            opp_label.setStyleSheet(f"color: {COLORS['red']}; font-weight: bold; font-size: 11px;")
            layout.addWidget(opp_label)

            opp_row = QHBoxLayout()
            for o in opponents:
                champ = o.get('champion', '?')
                role = 'SUPPORT' if o.get('role', '') == 'UTILITY' else o.get('role', '')

                card = QWidget()
                card_layout = QHBoxLayout(card)
                card_layout.setContentsMargins(4, 4, 8, 4)
                card_layout.setSpacing(6)
                card.setStyleSheet(f"""
                    background-color: {COLORS['bg_card']};
                    border-radius: 4px;
                    border: 1px solid {COLORS['red']};
                """)

                icon = QLabel()
                icon.setFixedSize(24, 24)
                if self.dd:
                    icon_path = self.dd.get_champion_icon_path(champ)
                    if icon_path:
                        px = QPixmap(icon_path)
                        if not px.isNull():
                            icon.setPixmap(px.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                icon.setStyleSheet("border: none;")
                card_layout.addWidget(icon)

                info = QLabel(f"{champ} ({role})")
                info.setStyleSheet(f"color: {COLORS['text']}; font-size: 10px; border: none;")
                card_layout.addWidget(info)

                card.setFixedWidth(140)
                opp_row.addWidget(card)

            opp_row.addStretch()
            layout.addLayout(opp_row)

        # Match ID
        match_id = QLabel(f"Match: {m.get('match_id', '')}")
        match_id.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 9px;")
        layout.addWidget(match_id)
