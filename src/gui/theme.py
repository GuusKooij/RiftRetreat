"""Dark theme styling for the LoL Companion app."""

# Colors inspired by League client
COLORS = {
    'bg_dark': '#0A0A0F',
    'bg_main': '#0F1018',
    'bg_card': '#1A1B26',
    'bg_card_hover': '#22233A',
    'bg_sidebar': '#0D0E16',
    'bg_input': '#13141F',

    'gold': '#C8AA6E',
    'gold_light': '#E8D5A3',
    'gold_dark': '#8B7437',
    'blue': '#0AC8B9',
    'blue_dark': '#005A53',
    'red': '#E84057',
    'green': '#00C853',
    'orange': '#FF9800',
    'purple': '#9C6ADE',

    'text': '#CDDCFE',
    'text_dim': '#7B818C',
    'text_bright': '#FFFFFF',

    'border': '#2A2B3D',
    'border_gold': '#463714',

    # Rank colors
    'iron': '#6B6B6B',
    'bronze': '#8B6914',
    'silver': '#8B9BB4',
    'gold_rank': '#FFD700',
    'platinum': '#00C9A7',
    'emerald': '#00A36C',
    'diamond': '#576BCE',
    'master': '#9D48E0',
    'grandmaster': '#EF4444',
    'challenger': '#F4C874',

    # Rating colors
    'strong': '#00C853',
    'weak': '#E84057',
    'average': '#C8AA6E',
    'small_sample': '#7B818C',
}

RANK_COLORS = {
    'IRON': COLORS['iron'],
    'BRONZE': COLORS['bronze'],
    'SILVER': COLORS['silver'],
    'GOLD': COLORS['gold_rank'],
    'PLATINUM': COLORS['platinum'],
    'EMERALD': COLORS['emerald'],
    'DIAMOND': COLORS['diamond'],
    'MASTER': COLORS['master'],
    'GRANDMASTER': COLORS['grandmaster'],
    'CHALLENGER': COLORS['challenger'],
}


STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {COLORS['bg_main']};
    color: {COLORS['text']};
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 13px;
}}

QLabel {{
    color: {COLORS['text']};
    background: transparent;
}}

QPushButton {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 8px 16px;
    font-size: 13px;
}}

QPushButton:hover {{
    background-color: {COLORS['bg_card_hover']};
    border-color: {COLORS['gold_dark']};
}}

QPushButton:pressed {{
    background-color: {COLORS['bg_dark']};
}}

QPushButton#nav_button {{
    background: transparent;
    border: none;
    border-radius: 0;
    padding: 12px 20px;
    text-align: left;
    font-size: 14px;
    color: {COLORS['text_dim']};
}}

QPushButton#nav_button:hover {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text']};
}}

QPushButton#nav_button[active="true"] {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['gold']};
    border-left: 3px solid {COLORS['gold']};
}}

QLineEdit {{
    background-color: {COLORS['bg_input']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 8px;
    font-size: 13px;
}}

QLineEdit:focus {{
    border-color: {COLORS['gold_dark']};
}}

QComboBox {{
    background-color: {COLORS['bg_input']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 8px;
}}

QScrollArea {{
    border: none;
    background: transparent;
}}

QScrollBar:vertical {{
    background: {COLORS['bg_dark']};
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS['text_dim']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QProgressBar {{
    background-color: {COLORS['bg_dark']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    text-align: center;
    color: {COLORS['text']};
    font-size: 11px;
    height: 18px;
}}

QProgressBar::chunk {{
    background-color: {COLORS['gold']};
    border-radius: 3px;
}}

QTableWidget {{
    background-color: {COLORS['bg_card']};
    alternate-background-color: {COLORS['bg_main']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    gridline-color: {COLORS['border']};
}}

QTableWidget::item {{
    padding: 6px;
}}

QTableWidget::item:selected {{
    background-color: {COLORS['bg_card_hover']};
    color: {COLORS['gold']};
}}

QHeaderView::section {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['gold']};
    border: 1px solid {COLORS['border']};
    padding: 6px;
    font-weight: bold;
}}
"""
