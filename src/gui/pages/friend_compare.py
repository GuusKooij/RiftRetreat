"""Friend Comparison page: side-by-side rank/WR comparison with another player."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QLineEdit, QPushButton
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from src.analytics.friend_compare import FriendComparer
from src.gui.theme import COLORS, RANK_COLORS


class FriendFetchWorker(QThread):
    """Fetch friend's ranked data (2 API calls: account lookup + league entries)."""
    finished = pyqtSignal(dict)  # {name, tag, entries, error}

    def __init__(self, riot_api, game_name: str, tag_line: str):
        super().__init__()
        self.api = riot_api
        self.game_name = game_name
        self.tag_line = tag_line

    def run(self):
        try:
            # Look up account
            account = self.api.get_account_by_riot_id(self.game_name, self.tag_line)
            if not account:
                self.finished.emit({'error': f"Account not found: {self.game_name}#{self.tag_line}"})
                return

            puuid = account['puuid']
            display_name = account.get('gameName', self.game_name)
            display_tag = account.get('tagLine', self.tag_line)

            # Get ranked entries
            entries = self.api.get_league_entries_by_puuid(puuid)
            if entries is None:
                entries = []

            self.finished.emit({
                'name': display_name,
                'tag': display_tag,
                'entries': entries,
                'error': None,
            })
        except Exception as e:
            self.finished.emit({'error': str(e)})


class FriendComparePage(QWidget):
    def __init__(self):
        super().__init__()
        self.riot_api = None
        self.user_entries = []
        self.user_name = ""
        self._worker = None
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
        title = QLabel("Friend Comparison")
        title.setStyleSheet(f"color: {COLORS['gold']}; font-size: 22px; font-weight: bold;")
        self.layout_main.addWidget(title)

        subtitle = QLabel("Compare your ranked stats with another player")
        subtitle.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px;")
        self.layout_main.addWidget(subtitle)

        # Input section
        input_frame = QFrame()
        input_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(16, 12, 16, 12)
        input_layout.setSpacing(8)

        label = QLabel("Riot ID:")
        label.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold; border: none;")
        input_layout.addWidget(label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Game Name")
        self.name_input.setFixedWidth(150)
        input_layout.addWidget(self.name_input)

        hash_label = QLabel("#")
        hash_label.setStyleSheet(f"color: {COLORS['gold']}; font-size: 16px; font-weight: bold; border: none;")
        input_layout.addWidget(hash_label)

        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Tag")
        self.tag_input.setFixedWidth(80)
        input_layout.addWidget(self.tag_input)

        self.compare_btn = QPushButton("Compare")
        self.compare_btn.setStyleSheet(f"""
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
            QPushButton:disabled {{
                background-color: {COLORS['border']};
                color: {COLORS['text_dim']};
            }}
        """)
        self.compare_btn.clicked.connect(self._on_compare)
        input_layout.addWidget(self.compare_btn)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
        input_layout.addWidget(self.status_label)

        input_layout.addStretch()
        self.layout_main.addWidget(input_frame)

        # Results area
        self.content_area = QVBoxLayout()
        self.layout_main.addLayout(self.content_area)

        self.layout_main.addStretch()

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def set_data(self, riot_api, user_entries: list, user_name: str = "You"):
        self.riot_api = riot_api
        self.user_entries = user_entries
        self.user_name = user_name

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

    def _rank_color(self, tier: str) -> str:
        return RANK_COLORS.get(tier.upper(), COLORS['text_dim']) if tier else COLORS['text_dim']

    def _on_compare(self):
        game_name = self.name_input.text().strip()
        tag_line = self.tag_input.text().strip()

        if not game_name or not tag_line:
            self.status_label.setText("Enter a valid Riot ID")
            self.status_label.setStyleSheet(f"color: {COLORS['red']}; font-size: 11px; border: none;")
            return

        if not self.riot_api:
            self.status_label.setText("No API key configured")
            self.status_label.setStyleSheet(f"color: {COLORS['red']}; font-size: 11px; border: none;")
            return

        self.compare_btn.setEnabled(False)
        self.status_label.setText("Looking up player...")
        self.status_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")

        self._worker = FriendFetchWorker(self.riot_api, game_name, tag_line)
        self._worker.finished.connect(self._on_friend_fetched)
        self._worker.start()

    def _on_friend_fetched(self, result: dict):
        self.compare_btn.setEnabled(True)

        if result.get('error'):
            self.status_label.setText(result['error'])
            self.status_label.setStyleSheet(f"color: {COLORS['red']}; font-size: 11px; border: none;")
            return

        self.status_label.setText("")
        friend_name = f"{result['name']}#{result['tag']}"
        self.friend_name = result['name']

        comparer = FriendComparer(
            self.user_entries, result['entries'],
            user_name=self.user_name, friend_name=result['name']
        )

        summary = comparer.summary()
        self._show_comparison(summary, friend_name)

    def _show_comparison(self, summary: dict, friend_name: str):
        self._clear_content()

        # Verdict card
        card, layout = self._card("Comparison Result")
        verdict = QLabel(summary['verdict'])
        verdict.setStyleSheet(f"color: {COLORS['gold']}; font-size: 18px; font-weight: bold; border: none;")
        verdict.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(verdict)
        self.content_area.addWidget(card)

        # Solo/Duo comparison
        self._show_queue_comparison(summary['solo'])

        # Flex comparison
        self._show_queue_comparison(summary['flex'])

    def _show_queue_comparison(self, comp: dict):
        """Show side-by-side comparison for a queue."""
        if not comp['user']['games'] and not comp['friend']['games']:
            return

        card, layout = self._card(comp['queue'])

        # Header row
        header_row = QHBoxLayout()
        header_row.addStretch()
        user_header = QLabel(self.user_name)
        user_header.setFixedWidth(150)
        user_header.setStyleSheet(f"color: {COLORS['blue']}; font-weight: bold; font-size: 14px; border: none;")
        user_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_row.addWidget(user_header)

        vs = QLabel("VS")
        vs.setFixedWidth(40)
        vs.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; border: none;")
        vs.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_row.addWidget(vs)

        friend_header = QLabel(getattr(self, 'friend_name', '') or "Friend")
        friend_header.setFixedWidth(150)
        friend_header.setStyleSheet(f"color: {COLORS['red']}; font-weight: bold; font-size: 14px; border: none;")
        friend_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_row.addWidget(friend_header)
        header_row.addStretch()
        layout.addLayout(header_row)

        # Stats rows
        stats = [
            ("Rank", comp['user']['rank_display'], comp['friend']['rank_display'],
             self._rank_color(comp['user']['tier']), self._rank_color(comp['friend']['tier'])),
            ("Win Rate", f"{comp['user']['winrate']}%", f"{comp['friend']['winrate']}%",
             COLORS['green'] if comp['user']['winrate'] >= comp['friend']['winrate'] else COLORS['text'],
             COLORS['green'] if comp['friend']['winrate'] >= comp['user']['winrate'] else COLORS['text']),
            ("Games", str(comp['user']['games']), str(comp['friend']['games']),
             COLORS['text'], COLORS['text']),
            ("Wins", str(comp['user']['wins']), str(comp['friend']['wins']),
             COLORS['text'], COLORS['text']),
            ("Losses", str(comp['user']['losses']), str(comp['friend']['losses']),
             COLORS['text'], COLORS['text']),
        ]

        for label, user_val, friend_val, user_color, friend_color in stats:
            row = QHBoxLayout()
            row.addStretch()

            u_label = QLabel(user_val)
            u_label.setFixedWidth(150)
            u_label.setStyleSheet(f"color: {user_color}; font-weight: bold; border: none;")
            u_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row.addWidget(u_label)

            stat_name = QLabel(label)
            stat_name.setFixedWidth(80)
            stat_name.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
            stat_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row.addWidget(stat_name)

            f_label = QLabel(friend_val)
            f_label.setFixedWidth(150)
            f_label.setStyleSheet(f"color: {friend_color}; font-weight: bold; border: none;")
            f_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row.addWidget(f_label)

            row.addStretch()
            layout.addLayout(row)

        self.content_area.addWidget(card)
