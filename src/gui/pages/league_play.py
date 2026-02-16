"""LeaguePlay page: All fun League features in one scrollable page with icons."""

import random
import time

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QLineEdit, QComboBox, QGridLayout,
    QTextEdit, QCheckBox, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QPixmap, QFont

from src.gui.theme import COLORS

# ── Data ─────────────────────────────────────────────────────────────────────

CHAMP_LIST = [
    "Aatrox", "Ahri", "Akali", "Akshan", "Alistar", "Ambessa", "Amumu", "Anivia", "Annie", "Aphelios",
    "Ashe", "Aurelion Sol", "Aurora", "Azir", "Bard", "Bel'Veth", "Blitzcrank", "Brand", "Braum", "Briar",
    "Caitlyn", "Camille", "Cassiopeia", "Cho'Gath", "Corki", "Darius", "Diana", "Dr. Mundo", "Draven",
    "Ekko", "Elise", "Evelynn", "Ezreal", "Fiddlesticks", "Fiora", "Fizz", "Galio", "Gangplank", "Garen",
    "Gnar", "Gragas", "Graves", "Gwen", "Hecarim", "Heimerdinger", "Hwei", "Illaoi", "Irelia", "Ivern",
    "Janna", "Jarvan IV", "Jax", "Jayce", "Jhin", "Jinx", "K'Sante", "Kai'Sa", "Kalista", "Karma",
    "Karthus", "Kassadin", "Katarina", "Kayle", "Kayn", "Kennen", "Kha'Zix", "Kindred", "Kled", "Kog'Maw",
    "LeBlanc", "Lee Sin", "Leona", "Lillia", "Lissandra", "Lucian", "Lulu", "Lux", "Malphite", "Malzahar",
    "Maokai", "Master Yi", "Mel", "Milio", "Miss Fortune", "Mordekaiser", "Morgana", "Naafiri", "Nami",
    "Nasus", "Nautilus", "Neeko", "Nidalee", "Nilah", "Nocturne", "Nunu & Willump", "Olaf", "Orianna",
    "Ornn", "Pantheon", "Poppy", "Pyke", "Qiyana", "Quinn", "Rakan", "Rammus", "Rek'Sai", "Rell",
    "Renata Glasc", "Renekton", "Rengar", "Riven", "Rumble", "Ryze", "Samira", "Sejuani", "Senna",
    "Seraphine", "Sett", "Shaco", "Shen", "Shyvana", "Singed", "Sion", "Sivir", "Skarner", "Smolder",
    "Sona", "Soraka", "Swain", "Sylas", "Syndra", "Tahm Kench", "Taliyah", "Talon", "Taric", "Teemo",
    "Thresh", "Tristana", "Trundle", "Tryndamere", "Twisted Fate", "Twitch", "Udyr", "Urgot", "Varus",
    "Vayne", "Veigar", "Vel'Koz", "Vex", "Vi", "Viego", "Viktor", "Vladimir", "Volibear", "Warwick",
    "Wukong", "Xayah", "Xerath", "Xin Zhao", "Yasuo", "Yone", "Yorick", "Yuumi", "Yunara", "Zaahen",
    "Zac", "Zed", "Zeri", "Ziggs", "Zilean", "Zoe", "Zyra",
]

ROLES = ["Top", "Jungle", "Mid", "Bot", "Support"]

KEYSTONES = [
    "Press The Attack", "Fleet Footwork", "Lethal Tempo", "Conqueror",
    "Electrocute", "Dark Harvest", "Hail Of Blades",
    "Summon Aery", "Arcane Comet", "Phase Rush",
    "Grasp Of The Undying", "Aftershock", "Guardian",
    "Glacial Augment", "Unsealed Spellbook", "First Strike",
]

KEYSTONE_TREE = {
    "Press The Attack": 0, "Fleet Footwork": 0, "Lethal Tempo": 0, "Conqueror": 0,
    "Electrocute": 1, "Dark Harvest": 1, "Hail Of Blades": 1,
    "Summon Aery": 2, "Arcane Comet": 2, "Phase Rush": 2,
    "Grasp Of The Undying": 3, "Aftershock": 3, "Guardian": 3,
    "Glacial Augment": 4, "Unsealed Spellbook": 4, "First Strike": 4,
}

TREE_NAMES = ["Precision", "Domination", "Sorcery", "Resolve", "Inspiration"]

RUNE_TREES = {
    0: [  # Precision
        ["Absorb Life", "Triumph", "Presence of Mind"],
        ["Legend: Alacrity", "Legend: Haste", "Legend: Bloodline"],
        ["Coup de Grace", "Cut Down", "Last Stand"],
    ],
    1: [  # Domination
        ["Cheap Shot", "Taste of Blood", "Sudden Impact"],
        ["Sixth Sense", "Grisly Mementos", "Deep Ward"],
        ["Treasure Hunter", "Relentless Hunter", "Ultimate Hunter"],
    ],
    2: [  # Sorcery
        ["Axiom Arcanist", "Manaflow Band", "Nimbus Cloak"],
        ["Transcendence", "Celerity", "Absolute Focus"],
        ["Scorch", "Waterwalking", "Gathering Storm"],
    ],
    3: [  # Resolve
        ["Demolish", "Font of Life", "Shield Bash"],
        ["Conditioning", "Second Wind", "Bone Plating"],
        ["Overgrowth", "Revitalize", "Unflinching"],
    ],
    4: [  # Inspiration
        ["Hextech Flashtraption", "Magical Footwear", "Cash Back"],
        ["Triple Tonic", "Time Warp Tonic", "Biscuit Delivery"],
        ["Cosmic Insight", "Approach Velocity", "Jack of All Trades"],
    ],
}

PLAYSTYLES = [
    "Full AD", "Full AP", "Full Tank", "Full Crit", "Lethality", "On-Hit",
    "Lifesteal", "Attack Speed", "Full Health", "Active Items", "Slow Items",
    "Scaling Items", "Full Ability Haste", "AD Bruiser", "AP Bruiser", "Hybrid",
    "Support Items", "One-Shot", "Over-Time Damage", "Maximum Healing",
    "Movement Speed", "Split Push", "Wave Clear", "Maximum Mana", "Full Armor",
    "Full Magic Resist", "Shields", "No Boots", "Health Regen", "Mana Regen",
    "AOE", "Anti-Tank", "Anti-Heal", "Heartsteel Stacking", "AP + Attack Speed",
]

SUMMONER_SPELLS = ["Ghost", "Heal", "Barrier", "Exhaust", "Flash", "Teleport", "Cleanse", "Ignite", "Smite"]

BOOTS = [
    "Berserker's Greaves", "Boots of Swiftness", "Ionian Boots of Lucidity",
    "Mercury's Treads", "Plated Steelcaps", "Sorcerer's Shoes",
]

SKILL_ORDERS = ["Q > W > E", "Q > E > W", "W > Q > E", "W > E > Q", "E > Q > W", "E > W > Q"]

DORAN_ITEMS = ["Doran's Blade", "Doran's Ring", "Doran's Shield", "Dark Seal", "Cull", "Tear of the Goddess"]
COMPONENT_ITEMS = ["Ruby Crystal", "Long Sword", "Amplifying Tome", "Cloth Armor", "Null-Magic Mantle", "Sapphire Crystal"]
JUNGLE_START = ["Gustwalker Hatchling", "Mosstomper Seedling", "Scorchclaw Pup"]
SUPPORT_QUEST = ["Solstice Sleigh", "Bloodsong", "Zaz'Zak's Realmspike", "Dream Maker", "Celestial Opposition"]

ALL_ITEMS = [
    "Bloodthirster", "Blade of the Ruined King", "Black Cleaver", "Death's Dance", "Edge of Night",
    "Essence Reaver", "Guardian Angel", "Hubris", "Infinity Edge", "Lord Dominik's Regards",
    "Maw of Malmortius", "Mercurial Scimitar", "Mortal Reminder", "Opportunity", "Phantom Dancer",
    "Profane Hydra", "Rapid Firecannon", "Ravenous Hydra", "Runaan's Hurricane", "Serylda's Grudge",
    "Spear of Shojin", "Sterak's Gage", "Stridebreaker", "Sundered Sky", "The Collector",
    "Titanic Hydra", "Trinity Force", "Umbral Glaive", "Voltaic Cyclosword", "Wit's End",
    "Youmuu's Ghostblade", "Eclipse", "Axiom Arc", "Experimental Hexplate", "Chempunk Chainsword",
    "Silvermere Dawn", "Hullbreaker", "Terminus", "Stormrazor", "Bastionbreaker", "Hexoptics C44",
    "Endless Hunger", "Archangel's Staff", "Banshee's Veil", "Cosmic Drive", "Cryptbloom",
    "Hextech Rocketbelt", "Lich Bane", "Liandry's Torment", "Luden's Echo", "Nashor's Tooth",
    "Rabadon's Deathcap", "Riftmaker", "Rod of Ages", "Rylai's Crystal Scepter", "Shadowflame",
    "Void Staff", "Zhonya's Hourglass", "Morellonomicon", "Hextech Gunblade", "Dusk and Dawn",
    "Actualizer", "Abyssal Mask", "Dead Man's Plate", "Force of Nature", "Frozen Heart",
    "Gargoyle Stoneplate", "Heartsteel", "Iceborn Gauntlet", "Jak'Sho, The Protean",
    "Kaenic Rookern", "Overlord's Bloodmail", "Randuin's Omen", "Spirit Visage", "Sunfire Aegis",
    "Thornmail", "Unending Despair", "Warmog's Armor", "Shurelya's Battlesong",
    "Locket of the Iron Solari", "Moonstone Renewer", "Echoes of Helia", "Imperial Mandate",
    "Redemption", "Knight's Vow", "Mikael's Blessing", "Staff of Flowing Water", "Bandlepipes",
    "Ardent Censer", "Zeke's Convergence", "Diadem of Songs",
]

SUPPORT_ITEMS = [
    "Shurelya's Battlesong", "Locket of the Iron Solari", "Moonstone Renewer", "Echoes of Helia",
    "Imperial Mandate", "Redemption", "Knight's Vow", "Mikael's Blessing", "Staff of Flowing Water",
    "Bandlepipes", "Ardent Censer", "Zeke's Convergence", "Diadem of Songs",
    "Zhonya's Hourglass", "Banshee's Veil", "Frozen Heart", "Spirit Visage", "Warmog's Armor",
]

ADC_ITEMS = [
    "Infinity Edge", "Bloodthirster", "Lord Dominik's Regards", "Mortal Reminder", "Phantom Dancer",
    "Rapid Firecannon", "Runaan's Hurricane", "Stormrazor", "The Collector", "Essence Reaver",
    "Blade of the Ruined King", "Guardian Angel", "Mercurial Scimitar", "Hexoptics C44",
    "Wit's End", "Maw of Malmortius", "Terminus",
]

NORMAL_DARES = [
    "Lucky you! No dare this time :)", "Free pass! Keep playing normally",
    "Use a summoner spell within 10 seconds", "Use your ultimate within 30 seconds",
    "Don't use your Q for 20 seconds", "Don't use your W for 20 seconds", "Don't use your E for 20 seconds",
    "Only use Q for 30 seconds", "Only use W for 30 seconds", "Only use E for 30 seconds",
    "Use all 3 basic abilities in the next 5 seconds", "Don't use any abilities for 15 seconds",
    "Play with locked screen for 30 seconds", "Play with unlocked screen for 30 seconds",
    "Don't touch your mouse for 5 seconds", "Don't touch your keyboard for 10 seconds",
    "Close your eyes for 5 seconds", "Look away from screen for 3 seconds",
    "Zoom all the way in for 15 seconds", "Zoom all the way out for 15 seconds",
    "Walk to river and back", "Walk in a circle for 5 seconds", "Spin your champion around 5 times",
    "Stay in a bush for 10 seconds", "Stay under tower for 20 seconds", "Don't move for 5 seconds",
    "Only walk backwards for 15 seconds", "Follow a teammate for 15 seconds",
    "Roam to another lane", "Visit every lane once",
    "Don't attack minions for 15 seconds", "Only attack minions for 15 seconds",
    "Let the next cannon minion die", "Only last hit with auto attacks for 30 seconds",
    "Kill 3 minions in a row without missing", "Place a ward within 10 seconds",
    "Buy a Control Ward on next back", "Place a ward in an unusual spot",
    "Clear an enemy ward if you can find one", "Type something nice about a teammate",
    "Type your favorite food in chat", "Type your champion's name in chat", "Say 'glhf' in all chat",
    "Type 'I believe in you' to jungler", "Compliment an enemy in all chat",
    "Type a random fact in chat", "Tell a joke in team chat", "Give your support a compliment",
    "Thank your jungler in chat", "Apologize to your team for nothing",
    "Predict the next kill in chat", "Type what you had for breakfast",
    "Share your favorite champion in chat", "Type 'gg' even though game isn't over",
    "Say 'sorry' to the next enemy you kill", "Dance in a bush for 5 seconds",
    "Use an emote right now", "Emote after your next kill", "Wave at your screen",
    "Do the thumbs up emote", "Laugh emote 3 times", "Use your mastery emote",
    "Ping 'On My Way' to mid lane", "Ping your ultimate cooldown", "Ping 'missing' on yourself",
    "Ping 'danger' on your ADC", "Question mark ping a random spot",
    "Recall to base immediately", "Check the scoreboard for 5 seconds",
    "Check the shop but don't buy anything", "Sell a potion (if you have one)",
    "Do 5 push-ups right now", "Do 10 sit-ups right now", "Do 3 jumping jacks",
    "Take a drink of water", "Stretch your arms for 10 seconds", "Stand up and sit back down",
    "Touch your toes", "Roll your shoulders 5 times", "Crack your knuckles (if you do that)",
    "Take a deep breath and hold for 5 seconds", "Count to 10 out loud",
    "Say your champion's name out loud", "Hum your champion's theme song",
    "Say 'pew pew' when you auto attack for 10 seconds", "Narrate your next kill",
    "Say 'oof' every time you take damage for 20 seconds", "Only use auto attacks for 15 seconds",
    "Land your next skill shot or do 5 push-ups", "Get an assist in the next minute",
    "Don't die for 2 minutes", "Poke an enemy champion within 15 seconds",
    "Play with only one finger on each hand for 15 seconds", "Hum a random tune while playing",
    "Think of your champion's backstory", "Make up a nickname for an enemy champion",
]

HARD_DARES = [
    "Lucky you! No dare this time :)", "Free pass - you earned it!",
    "Don't use your ultimate for 3 minutes", "Only last hit with abilities for 1 minute",
    "Don't use your main damage ability for 1 minute", "Use abilities in alphabetical order only",
    "Don't use your passive ability for 2 minutes", "Cast every ability once in the next 3 seconds",
    "Don't use abilities that cost mana for 30 seconds", "Use Flash aggressively in 30 seconds",
    "Don't use Flash for 3 minutes", "Flash for absolutely no reason", "Use Heal/Barrier at full HP",
    "Tower dive an enemy (or attempt to)", "Give first blood (or try to trade)",
    "1v1 the next enemy you see", "Let enemy hit you 3 times free",
    "Miss the next 3 skill shots on purpose", "Only attack the enemy with highest HP",
    "Fight the next enemy without using ult", "Win a fight using only auto attacks",
    "Engage the next fight", "Don't fight anyone for 2 minutes",
    "Stay in enemy jungle for 30 seconds", "Don't leave your lane for 3 minutes",
    "Stand still for 5 seconds in lane", "Walk through enemy tower range (don't attack)",
    "Go to Baron/Dragon pit and dance", "Stand in the river for 20 seconds",
    "Walk to enemy fountain and back (as far as safe)", "Don't retreat for 1 minute - only forward",
    "Play with locked screen for 2 minutes", "Play with one hand for 30 seconds",
    "Close your eyes for 10 seconds", "Don't use your mouse for 10 seconds",
    "Don't use your keyboard for 20 seconds", "Play with brightness at minimum 30s",
    "Switch mouse to your other hand 30s", "Don't look at minimap for 1 minute",
    "Only look at minimap for 30 seconds", "Spin your champion around 15 times",
    "Only move in zigzag patterns for 30 seconds", "Don't walk in straight lines for 1 minute",
    "Buy 3 Faerie Charms", "Buy wrong boots for your champion",
    "Build the most expensive item next", "Buy a component you don't need",
    "Don't recall - walk back to base", "Sit in fountain for 15 seconds before leaving",
    "Don't kill minions - only assist damage", "Only farm under tower for 2 minutes",
    "Let 5 minions die without touching them", "Kill minions only with abilities for 1 minute",
    "Narrate your gameplay out loud", "Only communicate with pings 2 minutes",
    "Give a compliment to every teammate", "Type a haiku about your champion",
    "Type 'sorry for what I'm about to do'", "Explain your build in chat",
    "Give shot calling for 1 minute", "Do 15 push-ups right now", "Do 20 sit-ups right now",
    "Do 10 squats right now", "Do jumping jacks until you get a kill",
    "Plank until the next minion wave", "Wall sit for 20 seconds", "Hold your arms up for 30 seconds",
    "Play rest of game with no sound", "Do a victory dance IRL after kills",
    "Play standing up for 2 minutes", "Take a selfie with your screen",
    "Sing your champion's theme", "Commentate like an esports caster for 1 minute",
    "Make sound effects for your abilities", "Talk in an accent for 2 minutes",
    "Follow jungler for their next 2 camps", "Follow your ADC everywhere for 1 minute",
    "Shadow the enemy jungler", "Ult the minion wave", "Dive tower at full HP",
    "Ult for a kill even if not needed", "Save ult for only teamfights",
    "Play without any items on your item slots for 30s", "Type with one hand while playing with other",
    "Count enemy abilities out loud", "Predict every team fight outcome before it happens",
]

EXTREME_DARES = [
    "Lucky you! No dare this time :)", "Miracle! You're spared!",
    "Int into the enemy (die once on purpose)", "Run it down mid once (controlled int)",
    "Give away your blue/red buff", "Give every kill to teammates this fight",
    "Let yourself get solo killed", "Walk into 3 enemies and try to escape",
    "Don't use ANY abilities for 1 minute", "Only use your ultimate - nothing else for 30s",
    "Use all abilities on cooldown for 1 minute", "Don't auto attack for 1 minute - only abilities",
    "Don't use your passive for 2 minutes", "Use all summoner spells RIGHT NOW",
    "Flash + Ult into nothing", "Flash into a wall 3 times",
    "Use both summoner spells on cooldown", "Go 1v5 (attempt to fight all enemies)",
    "Fight Baron/Dragon without team", "1v1 their most fed player",
    "Dive their fountain and survive", "Fight every enemy you see for 2 minutes",
    "Let the enemy push to your inhib tower", "Stand in enemy fountain for 3 seconds",
    "Play with monitor off for 10 seconds", "Play with inverted mouse for 30 seconds",
    "Close your eyes until you hear danger", "Play with only keyboard (no mouse) for 15s",
    "Play with only mouse (no keyboard) for 15s", "Unplug your mouse for 10 seconds",
    "Cover half your screen for 30 seconds", "Play looking only at minimap for 20 seconds",
    "Sell an item and rebuy it", "Build full AP on an AD champion",
    "Build full AD on an AP champion", "Don't buy items for 3 minutes", "Build 6 boots",
    "Buy only the cheapest items for your next 1000g", "Sell your most expensive item",
    "Buy Mejai's (even if you don't stack it)", "Only move using attack-move for 1 min",
    "Walk to enemy fountain", "Take the longest path everywhere for 2 minutes",
    "Don't use any movement abilities for 2 minutes", "Only move forward - no retreating for 1 minute",
    "Miss every CS for 30 seconds", "Take every jungle camp you see",
    "Steal your jungler's camps", "Only farm enemy jungle for 1 minute",
    "Type your life story in chat", "Type 'I am the greatest' after dying",
    "Predict match outcome wrong on purpose", "Apologize in all chat for everything you do",
    "Give enemy tips on how to beat you", "Flame yourself in chat (jokingly)",
    "Type 'calculated' after every death", "Interview your teammates in chat",
    "Do 30 push-ups right now", "Do 30 sit-ups right now", "Do 20 squats right now",
    "Plank for 30 seconds", "Do burpees until next kill/death",
    "Run in place for 1 minute", "Do wall sit until next objective",
    "Hold a push-up position for 20 seconds", "Sing Happy Birthday in voice chat",
    "Do a dramatic reading of abilities", "Speak only in third person for 2 min",
    "Speak in a funny accent for 2 minutes", "Do your best champion impression",
    "Yell your ultimate name when casting", "Narrate in Morgan Freeman's voice",
    "Speak only in questions for 2 minutes", "Rap about your current game",
    "Make up a song about your lane opponent", "Spam laugh emote for 30 seconds",
    "Dance on enemy corpse for 5 seconds", "Mastery emote after every CS for 30 seconds",
    "Emote before every ability for 1 minute", "Follow enemy jungler around",
    "Try to steal every enemy camp", "Become the enemy ADC's shadow",
    "Play the rest of the game with no items (sell all)", "Don't level up an ability for 2 minutes",
    "Only use even-numbered abilities (W and R)", "Switch roles with a teammate (in spirit)",
    "Play like you're in a Bronze tutorial video", "Pretend you're lagging with delayed reactions",
    "Act like it's your first time playing this champ", "Play like you're in slow motion for 30 seconds",
]

ROULETTE_PLAYSTYLES = [
    "Aggressive", "Passive", "Roaming", "Split Push", "Team Fight",
    "Poke", "All-In", "Protect Carry", "Assassinate", "Peel",
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _section_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color: {COLORS['gold']}; font-size: 16px; font-weight: bold; border: none;")
    return lbl


def _subsection_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color: {COLORS['gold']}; font-size: 13px; font-weight: bold; border: none;")
    return lbl


def _dim_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
    return lbl


def _create_icon_label(pixmap: QPixmap, size=32) -> QLabel:
    """Create a QLabel with a scaled pixmap icon."""
    lbl = QLabel()
    lbl.setPixmap(pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
    lbl.setFixedSize(size, size)
    lbl.setStyleSheet("border: none;")
    return lbl


def _create_icon_text_row(icon_path: str, text: str, icon_size=28) -> QWidget:
    """Create a row widget with icon on left and text on right."""
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)

    if icon_path:
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            icon_lbl = _create_icon_label(pixmap, icon_size)
            layout.addWidget(icon_lbl)

    text_lbl = QLabel(text)
    text_lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: 12px; border: none;")
    layout.addWidget(text_lbl)
    layout.addStretch()

    return widget


def _separator() -> QFrame:
    """Create a horizontal separator line."""
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    line.setStyleSheet(f"background-color: {COLORS['border']}; border: none; max-height: 1px;")
    return line


# ── Main Page ────────────────────────────────────────────────────────────────

class LeaguePlayPage(QWidget):
    def __init__(self, data_dragon=None):
        super().__init__()
        self._dd = data_dragon
        self._setup_ui()

    def set_data_dragon(self, dd):
        self._dd = dd

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"background: {COLORS['bg_main']}; border: none;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 16, 24, 24)

        # Title
        title = QLabel("LeaguePlay — Fun Game Modes")
        title.setStyleSheet(f"color: {COLORS['gold']}; font-size: 20px; font-weight: bold; border: none;")
        layout.addWidget(title)

        # 1. Ultimate Bravery (moved to top)
        layout.addWidget(self._build_ultimate_bravery())
        layout.addWidget(_separator())

        # 2. Randomizer
        layout.addWidget(self._build_randomizer())
        layout.addWidget(_separator())

        # 3. Team Shuffler
        layout.addWidget(self._build_team_shuffler())
        layout.addWidget(_separator())

        # 4. Roulette
        layout.addWidget(self._build_roulette())
        layout.addWidget(_separator())

        # 5. Tournament
        layout.addWidget(self._build_tournament())
        layout.addWidget(_separator())

        # 6. Role Assign
        layout.addWidget(self._build_role_assign())
        layout.addWidget(_separator())

        # 7. Stopwatch
        layout.addWidget(self._build_stopwatch())
        layout.addWidget(_separator())

        # 8. Team Builder
        layout.addWidget(self._build_team_builder())
        layout.addWidget(_separator())

        # 9. Dare Game
        layout.addWidget(self._build_dare_game())

        layout.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)

    # ── 1. Randomizer ────────────────────────────────────────────────────

    def _build_randomizer(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(_section_title("Randomizer"))
        layout.addWidget(_dim_label("Roll random champion, role, playstyle, runes, spells, items, and more!"))

        # Result container
        self._rand_result_widget = QWidget()
        res_layout = QGridLayout(self._rand_result_widget)
        res_layout.setSpacing(6)
        res_layout.setVerticalSpacing(8)
        res_layout.setContentsMargins(12, 12, 12, 12)
        self._rand_result_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
        """)
        self._rand_result_widget.setVisible(False)

        self._rand_labels = {}
        categories = [
            "Champion", "Role", "Playstyle", "Keystone", "Second Tree",
            "Summoner 1", "Summoner 2", "Start Item", "Skill Order", "Ban", "Boots", "First Item",
        ]

        for i, cat in enumerate(categories):
            lbl = QLabel(f"{cat}:")
            lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none; background: transparent;")
            lbl.setFixedWidth(85)
            lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            res_layout.addWidget(lbl, i, 0)

            # Icon + text container
            result_container = QWidget()
            result_container.setStyleSheet("background: transparent; border: none;")
            result_layout = QHBoxLayout(result_container)
            result_layout.setContentsMargins(0, 0, 0, 0)
            result_layout.setSpacing(8)

            icon_lbl = QLabel()
            icon_lbl.setFixedSize(24, 24)
            icon_lbl.setStyleSheet("border: none; background: transparent;")
            icon_lbl.setScaledContents(False)
            result_layout.addWidget(icon_lbl)

            text_lbl = QLabel("-")
            text_lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: 12px; border: none; background: transparent;")
            text_lbl.setMinimumWidth(180)
            result_layout.addWidget(text_lbl)
            result_layout.addStretch()

            self._rand_labels[cat] = {'icon': icon_lbl, 'text': text_lbl}
            res_layout.addWidget(result_container, i, 1)

            btn = QPushButton("Roll")
            btn.setFixedSize(55, 26)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_card_hover']};
                    color: {COLORS['text']};
                    font-size: 10px;
                    border: 1px solid {COLORS['border']};
                    border-radius: 3px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['gold_dark']};
                    color: {COLORS['text_bright']};
                }}
            """)
            btn.clicked.connect(lambda checked, c=cat: self._roll_randomizer(c))
            res_layout.addWidget(btn, i, 2, Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(self._rand_result_widget)

        gen_btn = QPushButton("GENERATE ALL")
        gen_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['gold_dark']};
                color: {COLORS['text_bright']};
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 5px;
                font-size: 13px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {COLORS['gold']};
                color: {COLORS['bg_dark']};
            }}
        """)
        gen_btn.setFixedHeight(36)
        gen_btn.setFixedWidth(200)
        gen_btn.clicked.connect(self._generate_all_randomizer)
        layout.addWidget(gen_btn)

        return widget

    def _roll_randomizer(self, category: str):
        self._rand_result_widget.setVisible(True)
        r = random.choice
        lbl = self._rand_labels

        result_text = ""
        icon_path = None

        if category == "Champion":
            result_text = r(CHAMP_LIST)
            if self._dd:
                icon_path = self._dd.get_champion_icon_path(result_text)
        elif category == "Role":
            result_text = r(ROLES)
        elif category == "Playstyle":
            result_text = r(PLAYSTYLES)
        elif category == "Keystone":
            result_text = r(KEYSTONES)
            if self._dd:
                icon_path = self._dd.get_rune_icon_path(result_text)
        elif category == "Second Tree":
            ks = lbl["Keystone"]['text'].text()
            exclude = KEYSTONE_TREE.get(ks, -1)
            choices = [t for i, t in enumerate(TREE_NAMES) if i != exclude]
            result_text = r(choices) if choices else r(TREE_NAMES)
        elif category == "Summoner 1":
            result_text = r(SUMMONER_SPELLS)
            if self._dd:
                icon_path = self._dd.get_summoner_spell_icon_path(result_text)
        elif category == "Summoner 2":
            s1 = lbl["Summoner 1"]['text'].text()
            choices = [s for s in SUMMONER_SPELLS if s != s1]
            role = lbl["Role"]['text'].text()
            result_text = r(choices) if choices else r(SUMMONER_SPELLS)
            if role == "Jungle" and result_text != "Smite" and s1 != "Smite":
                result_text = "Smite"
            if self._dd:
                icon_path = self._dd.get_summoner_spell_icon_path(result_text)
        elif category == "Start Item":
            role = lbl["Role"]['text'].text()
            if role == "Jungle":
                result_text = r(JUNGLE_START)
            elif role == "Support":
                result_text = "World Atlas"
            else:
                if random.random() < 0.8:
                    result_text = r(DORAN_ITEMS)
                else:
                    result_text = r(COMPONENT_ITEMS)
            if self._dd:
                icon_path = self._dd.get_item_icon_path_by_name(result_text)
        elif category == "Skill Order":
            result_text = r(SKILL_ORDERS)
        elif category == "Ban":
            result_text = r(CHAMP_LIST)
            if self._dd:
                icon_path = self._dd.get_champion_icon_path(result_text)
        elif category == "Boots":
            result_text = r(BOOTS)
            if self._dd:
                icon_path = self._dd.get_item_icon_path_by_name(result_text)
        elif category == "First Item":
            result_text = r(ALL_ITEMS)
            if self._dd:
                icon_path = self._dd.get_item_icon_path_by_name(result_text)

        lbl[category]['text'].setText(result_text)

        if icon_path:
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                lbl[category]['icon'].setPixmap(pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                lbl[category]['icon'].clear()
        else:
            lbl[category]['icon'].clear()

    def _generate_all_randomizer(self):
        order = ["Champion", "Role", "Playstyle", "Keystone", "Second Tree",
                 "Summoner 1", "Summoner 2", "Start Item", "Skill Order", "Ban", "Boots", "First Item"]
        for cat in order:
            self._roll_randomizer(cat)

    # ── 2. Ultimate Bravery ──────────────────────────────────────────────

    def _build_ultimate_bravery(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(_section_title("Ultimate Bravery"))
        layout.addWidget(_dim_label("Full random build: champion, summoners, complete rune page, boots, and 5 items."))

        # Result container
        self._ub_result_widget = QWidget()
        res_layout = QVBoxLayout(self._ub_result_widget)
        res_layout.setSpacing(10)
        res_layout.setContentsMargins(16, 12, 16, 12)
        self._ub_result_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
        """)
        self._ub_result_widget.setVisible(False)

        # Champion & Role row
        top_row = QHBoxLayout()
        self._ub_champ_icon = QLabel()
        self._ub_champ_icon.setFixedSize(48, 48)
        self._ub_champ_icon.setStyleSheet("border: none;")
        top_row.addWidget(self._ub_champ_icon)

        top_text = QVBoxLayout()
        self._ub_champ_name = QLabel()
        self._ub_champ_name.setStyleSheet(f"color: {COLORS['text_bright']}; font-size: 15px; font-weight: bold; border: none;")
        self._ub_role_label = QLabel()
        self._ub_role_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
        top_text.addWidget(self._ub_champ_name)
        top_text.addWidget(self._ub_role_label)
        top_row.addLayout(top_text)
        top_row.addStretch()

        # Summoners
        self._ub_spell1_icon = QLabel()
        self._ub_spell1_icon.setFixedSize(32, 32)
        self._ub_spell1_icon.setStyleSheet("border: none;")
        self._ub_spell2_icon = QLabel()
        self._ub_spell2_icon.setFixedSize(32, 32)
        self._ub_spell2_icon.setStyleSheet("border: none;")
        top_row.addWidget(self._ub_spell1_icon)
        top_row.addWidget(self._ub_spell2_icon)

        res_layout.addLayout(top_row)

        # Runes section
        runes_row = QHBoxLayout()
        runes_col1 = QVBoxLayout()
        runes_col1.addWidget(_subsection_title("Primary Runes"))
        self._ub_keystone_widget = QWidget()
        self._ub_rune1_widget = QWidget()
        self._ub_rune2_widget = QWidget()
        self._ub_rune3_widget = QWidget()
        runes_col1.addWidget(self._ub_keystone_widget)
        runes_col1.addWidget(self._ub_rune1_widget)
        runes_col1.addWidget(self._ub_rune2_widget)
        runes_col1.addWidget(self._ub_rune3_widget)
        runes_row.addLayout(runes_col1)

        runes_col2 = QVBoxLayout()
        runes_col2.addWidget(_subsection_title("Secondary"))
        self._ub_sec_tree_label = QLabel()
        self._ub_sec_tree_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
        runes_col2.addWidget(self._ub_sec_tree_label)
        self._ub_sec_rune1_widget = QWidget()
        self._ub_sec_rune2_widget = QWidget()
        runes_col2.addWidget(self._ub_sec_rune1_widget)
        runes_col2.addWidget(self._ub_sec_rune2_widget)
        runes_row.addLayout(runes_col2)
        runes_row.addStretch()

        res_layout.addLayout(runes_row)

        # Build section
        res_layout.addWidget(_subsection_title("Build"))
        build_row = QHBoxLayout()
        self._ub_boots_icon = QLabel()
        self._ub_boots_icon.setFixedSize(36, 36)
        self._ub_boots_icon.setStyleSheet("border: none;")
        self._ub_item1_icon = QLabel()
        self._ub_item1_icon.setFixedSize(36, 36)
        self._ub_item1_icon.setStyleSheet("border: none;")
        self._ub_item2_icon = QLabel()
        self._ub_item2_icon.setFixedSize(36, 36)
        self._ub_item2_icon.setStyleSheet("border: none;")
        self._ub_item3_icon = QLabel()
        self._ub_item3_icon.setFixedSize(36, 36)
        self._ub_item3_icon.setStyleSheet("border: none;")
        self._ub_item4_icon = QLabel()
        self._ub_item4_icon.setFixedSize(36, 36)
        self._ub_item4_icon.setStyleSheet("border: none;")
        self._ub_item5_icon = QLabel()
        self._ub_item5_icon.setFixedSize(36, 36)
        self._ub_item5_icon.setStyleSheet("border: none;")

        build_row.addWidget(self._ub_boots_icon)
        build_row.addWidget(self._ub_item1_icon)
        build_row.addWidget(self._ub_item2_icon)
        build_row.addWidget(self._ub_item3_icon)
        build_row.addWidget(self._ub_item4_icon)
        build_row.addWidget(self._ub_item5_icon)
        build_row.addStretch()
        res_layout.addLayout(build_row)

        layout.addWidget(self._ub_result_widget)

        gen_btn = QPushButton("Generate Full Build")
        gen_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['gold_dark']};
                color: {COLORS['text_bright']};
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 5px;
                font-size: 13px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {COLORS['gold']};
                color: {COLORS['bg_dark']};
            }}
        """)
        gen_btn.setFixedHeight(36)
        gen_btn.setFixedWidth(200)
        gen_btn.clicked.connect(self._generate_ultimate_bravery)
        layout.addWidget(gen_btn)

        return widget

    def _generate_ultimate_bravery(self):
        self._ub_result_widget.setVisible(True)
        r = random.choice

        champ = r(CHAMP_LIST)
        role = r(ROLES)
        self._ub_champ_name.setText(champ)
        self._ub_role_label.setText(f"Role: {role}")

        if self._dd:
            icon_path = self._dd.get_champion_icon_path(champ)
            if icon_path:
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    self._ub_champ_icon.setPixmap(pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        # Summoner spells
        if role == "Jungle":
            other = r(["Flash", "Ghost", "Ignite", "Exhaust"])
            spell1, spell2 = ("Smite", other) if other == "Flash" else (other, "Smite")
        else:
            pool = ["Ghost", "Heal", "Barrier", "Exhaust", "Flash", "Teleport", "Cleanse", "Ignite"]
            spell1, spell2 = random.sample(pool, 2)
            if spell1 == "Flash":
                spell1, spell2 = spell2, spell1

        if self._dd:
            for spell, icon_lbl in [(spell1, self._ub_spell1_icon), (spell2, self._ub_spell2_icon)]:
                icon_path = self._dd.get_summoner_spell_icon_path(spell)
                if icon_path:
                    pixmap = QPixmap(icon_path)
                    if not pixmap.isNull():
                        icon_lbl.setPixmap(pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                        icon_lbl.setToolTip(spell)

        # Primary runes
        keystone = r(KEYSTONES)
        primary_tree = KEYSTONE_TREE[keystone]
        tree_runes = RUNE_TREES[primary_tree]
        rune1 = r(tree_runes[0])
        rune2 = r(tree_runes[1])
        rune3 = r(tree_runes[2])

        self._set_rune_widget(self._ub_keystone_widget, keystone)
        self._set_rune_widget(self._ub_rune1_widget, rune1)
        self._set_rune_widget(self._ub_rune2_widget, rune2)
        self._set_rune_widget(self._ub_rune3_widget, rune3)

        # Secondary runes
        sec_tree = random.choice([i for i in range(5) if i != primary_tree])
        self._ub_sec_tree_label.setText(TREE_NAMES[sec_tree])
        sec_runes = RUNE_TREES[sec_tree]
        row1, row2 = random.sample(range(3), 2)
        sec_rune1 = r(sec_runes[row1])
        sec_rune2 = r(sec_runes[row2])

        self._set_rune_widget(self._ub_sec_rune1_widget, sec_rune1)
        self._set_rune_widget(self._ub_sec_rune2_widget, sec_rune2)

        # Boots
        boots = r(BOOTS)
        if self._dd:
            icon_path = self._dd.get_item_icon_path_by_name(boots)
            if icon_path:
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    self._ub_boots_icon.setPixmap(pixmap.scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    self._ub_boots_icon.setToolTip(boots)

        # Items
        used = set()
        item_icons = [self._ub_item1_icon, self._ub_item2_icon, self._ub_item3_icon, self._ub_item4_icon, self._ub_item5_icon]

        if role == "Support":
            quest = r(SUPPORT_QUEST)
            used.add(quest)
            items = [quest] + [self._pick_unique_item(ALL_ITEMS, used) for _ in range(4)]
        else:
            pool = ADC_ITEMS if role == "Bot" else ALL_ITEMS
            items = [self._pick_unique_item(pool, used) for _ in range(5)]

        if self._dd:
            for item_name, icon_lbl in zip(items, item_icons):
                icon_path = self._dd.get_item_icon_path_by_name(item_name)
                if icon_path:
                    pixmap = QPixmap(icon_path)
                    if not pixmap.isNull():
                        icon_lbl.setPixmap(pixmap.scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                        icon_lbl.setToolTip(item_name)

    def _pick_unique_item(self, pool: list, used: set) -> str:
        item = random.choice(pool)
        while item in used and len(used) < len(pool):
            item = random.choice(pool)
        used.add(item)
        return item

    def _set_rune_widget(self, widget: QWidget, rune_name: str):
        """Clear and rebuild a rune widget with icon + text."""
        # Clear existing layout
        if widget.layout():
            while widget.layout().count():
                child = widget.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        else:
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(6)

        layout = widget.layout()

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(22, 22)
        icon_lbl.setStyleSheet("border: none;")

        if self._dd:
            icon_path = self._dd.get_rune_icon_path(rune_name)
            if icon_path:
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    icon_lbl.setPixmap(pixmap.scaled(22, 22, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        text_lbl = QLabel(rune_name)
        text_lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: 11px; border: none;")

        layout.addWidget(icon_lbl)
        layout.addWidget(text_lbl)
        layout.addStretch()

    # ── 3. Team Shuffler ─────────────────────────────────────────────────

    def _build_team_shuffler(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(_section_title("Team Shuffler"))
        layout.addWidget(_dim_label("Enter names (one per line) and shuffle into two random teams."))

        body = QHBoxLayout()

        left = QVBoxLayout()
        left.addWidget(_dim_label("Names (2-10):"))
        self._shuffler_input = QTextEdit()
        self._shuffler_input.setPlaceholderText("Player 1\nPlayer 2\nPlayer 3\nPlayer 4")
        self._shuffler_input.setStyleSheet(f"""
            background-color: {COLORS['bg_input']};
            color: {COLORS['text']};
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            padding: 6px;
            font-size: 12px;
        """)
        self._shuffler_input.setFixedWidth(180)
        self._shuffler_input.setFixedHeight(100)
        left.addWidget(self._shuffler_input)
        body.addLayout(left)

        right = QVBoxLayout()
        right.addWidget(_dim_label("Team 1:"))
        self._team1_label = QLabel()
        self._team1_label.setStyleSheet(f"""
            background-color: {COLORS['bg_input']};
            color: {COLORS['text']};
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            padding: 6px;
            font-size: 12px;
            min-height: 40px;
        """)
        self._team1_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._team1_label.setWordWrap(True)
        right.addWidget(self._team1_label)

        right.addWidget(_dim_label("Team 2:"))
        self._team2_label = QLabel()
        self._team2_label.setStyleSheet(f"""
            background-color: {COLORS['bg_input']};
            color: {COLORS['text']};
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            padding: 6px;
            font-size: 12px;
            min-height: 40px;
        """)
        self._team2_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._team2_label.setWordWrap(True)
        right.addWidget(self._team2_label)

        body.addLayout(right)
        body.addStretch()
        layout.addLayout(body)

        btn = QPushButton("Shuffle Teams")
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['gold_dark']};
                color: {COLORS['text_bright']};
                font-weight: bold;
                padding: 6px 16px;
                border-radius: 5px;
                font-size: 12px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {COLORS['gold']};
                color: {COLORS['bg_dark']};
            }}
        """)
        btn.setFixedHeight(32)
        btn.setFixedWidth(160)
        btn.clicked.connect(self._shuffle_teams)
        layout.addWidget(btn)

        return widget

    def _shuffle_teams(self):
        text = self._shuffler_input.toPlainText()
        names = [n.strip() for n in text.split("\n") if n.strip()]
        if len(names) < 2:
            QMessageBox.warning(self, "Error", "Enter at least 2 names!")
            return
        if len(names) > 10:
            QMessageBox.warning(self, "Error", "Maximum 10 names!")
            return

        random.shuffle(names)
        t1 = [names[i] for i in range(0, len(names), 2)]
        t2 = [names[i] for i in range(1, len(names), 2)]
        self._team1_label.setText("\n".join(t1))
        self._team2_label.setText("\n".join(t2))

    # ── 4. Roulette ──────────────────────────────────────────────────────

    def _build_roulette(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(_section_title("Roulette"))
        layout.addWidget(_dim_label("Spin the wheel for a random result with slot-machine animation!"))

        cat_row = QHBoxLayout()
        cat_row.addWidget(_dim_label("Category:"))
        self._roulette_category = QComboBox()
        self._roulette_category.addItems(["Champion", "Role", "Keystone", "Summoner", "Lane", "Playstyle"])
        self._roulette_category.setFixedWidth(140)
        cat_row.addWidget(self._roulette_category)
        cat_row.addStretch()
        layout.addLayout(cat_row)

        self._roulette_result = QLabel("Click SPIN!")
        self._roulette_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._roulette_result.setFixedHeight(80)
        self._roulette_result.setStyleSheet(f"""
            background-color: {COLORS['bg_input']};
            color: {COLORS['text_bright']};
            border: 2px solid {COLORS['border']};
            border-radius: 6px;
            font-size: 20px;
            font-weight: bold;
        """)
        layout.addWidget(self._roulette_result)

        spin_btn = QPushButton("SPIN!")
        spin_btn.setFixedHeight(50)
        spin_btn.setFixedWidth(180)
        spin_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['green']};
                color: {COLORS['text_bright']};
                font-size: 18px;
                font-weight: bold;
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #00E676;
            }}
        """)
        spin_btn.clicked.connect(self._spin_roulette)
        layout.addWidget(spin_btn)

        self._roulette_timer = QTimer()
        self._roulette_timer.timeout.connect(self._roulette_tick)
        self._roulette_spins = 0
        self._roulette_max = 20

        return widget

    def _get_roulette_options(self) -> list:
        idx = self._roulette_category.currentIndex()
        if idx == 0:
            return CHAMP_LIST
        elif idx == 1:
            return ROLES
        elif idx == 2:
            return KEYSTONES
        elif idx == 3:
            return SUMMONER_SPELLS
        elif idx == 4:
            return ["Top Lane", "Jungle", "Mid Lane", "Bot Lane"]
        elif idx == 5:
            return ROULETTE_PLAYSTYLES
        return CHAMP_LIST

    def _spin_roulette(self):
        self._roulette_spins = 0
        self._roulette_max = random.randint(20, 35)
        self._roulette_timer.setInterval(40)
        self._roulette_result.setStyleSheet(f"""
            background-color: {COLORS['bg_input']};
            color: {COLORS['text_bright']};
            border: 2px solid {COLORS['border']};
            border-radius: 6px;
            font-size: 20px;
            font-weight: bold;
        """)
        self._roulette_timer.start()

    def _roulette_tick(self):
        options = self._get_roulette_options()
        self._roulette_result.setText(random.choice(options))
        self._roulette_spins += 1

        pct = self._roulette_spins / self._roulette_max
        if pct > 0.95:
            self._roulette_timer.setInterval(500)
        elif pct > 0.85:
            self._roulette_timer.setInterval(300)
        elif pct > 0.7:
            self._roulette_timer.setInterval(150)
        elif pct > 0.5:
            self._roulette_timer.setInterval(80)

        if self._roulette_spins >= self._roulette_max:
            self._roulette_timer.stop()
            self._roulette_result.setStyleSheet(f"""
                background-color: {COLORS['bg_input']};
                color: {COLORS['green']};
                border: 2px solid {COLORS['green']};
                border-radius: 6px;
                font-size: 22px;
                font-weight: bold;
            """)

    # ── 5. Tournament ────────────────────────────────────────────────────

    def _build_tournament(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(_section_title("1v1 Tournament"))
        layout.addWidget(_dim_label("Enter 2-8 player names to generate a randomized bracket."))

        body = QHBoxLayout()

        left = QVBoxLayout()
        left.addWidget(_dim_label("Players (2-8):"))
        self._tournament_input = QTextEdit()
        self._tournament_input.setPlaceholderText("Player 1\nPlayer 2\nPlayer 3\nPlayer 4")
        self._tournament_input.setText("Player 1\nPlayer 2\nPlayer 3\nPlayer 4")
        self._tournament_input.setStyleSheet(f"""
            background-color: {COLORS['bg_input']};
            color: {COLORS['text']};
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            padding: 6px;
            font-size: 12px;
        """)
        self._tournament_input.setFixedWidth(150)
        self._tournament_input.setFixedHeight(100)
        left.addWidget(self._tournament_input)
        body.addLayout(left)

        right = QVBoxLayout()
        right.addWidget(_dim_label("Bracket:"))
        self._bracket_display = QTextEdit()
        self._bracket_display.setReadOnly(True)
        self._bracket_display.setStyleSheet(f"""
            background-color: {COLORS['bg_input']};
            color: {COLORS['text']};
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            padding: 6px;
            font-family: 'Consolas', monospace;
            font-size: 11px;
        """)
        self._bracket_display.setFixedHeight(100)
        self._bracket_display.setPlaceholderText("Bracket will appear here...")
        right.addWidget(self._bracket_display)
        body.addLayout(right)

        layout.addLayout(body)

        btn = QPushButton("Generate Bracket")
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['gold_dark']};
                color: {COLORS['text_bright']};
                font-weight: bold;
                padding: 6px 16px;
                border-radius: 5px;
                font-size: 12px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {COLORS['gold']};
                color: {COLORS['bg_dark']};
            }}
        """)
        btn.setFixedHeight(32)
        btn.setFixedWidth(180)
        btn.clicked.connect(self._generate_bracket)
        layout.addWidget(btn)

        return widget

    def _generate_bracket(self):
        text = self._tournament_input.toPlainText()
        names = [n.strip() for n in text.split("\n") if n.strip()]
        if len(names) < 2:
            QMessageBox.warning(self, "Error", "Enter at least 2 players!")
            return
        if len(names) > 8:
            QMessageBox.warning(self, "Error", "Maximum 8 players!")
            return

        random.shuffle(names)

        while len(names) < 4 and len(names) > 2:
            names.append("BYE")
        while len(names) < 8 and len(names) > 4:
            names.append("BYE")

        bracket = ""
        round_num = 1
        current = list(names)

        while len(current) > 1:
            if len(current) == 2:
                rnd_name = "FINALS"
            elif len(current) == 4:
                rnd_name = "SEMIS"
            else:
                rnd_name = f"ROUND {round_num}"

            bracket += f"{rnd_name}:\n"
            next_round = []
            for i in range(0, len(current), 2):
                p1 = current[i]
                p2 = current[i + 1]
                bracket += f"  {p1}  vs  {p2}\n"

                if p2 == "BYE":
                    next_round.append(p1)
                elif p1 == "BYE":
                    next_round.append(p2)
                else:
                    next_round.append(f"W{round_num}.{i // 2 + 1}")

            bracket += "\n"
            current = next_round
            round_num += 1

        self._bracket_display.setText(bracket.rstrip())

    # ── 6. Role Assign ───────────────────────────────────────────────────

    def _build_role_assign(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(_section_title("Role Assign"))
        layout.addWidget(_dim_label("Assign roles to 5 players based on their preferences."))

        body = QHBoxLayout()

        grid = QGridLayout()
        grid.setSpacing(6)

        self._ra_name_inputs = []
        self._ra_checkboxes = []

        for i in range(5):
            header = QLabel(f"Player {i + 1}")
            header.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; font-size: 11px; border: none;")
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(header, 0, i)

            name_input = QLineEdit(f"Name {i + 1}")
            name_input.setFixedWidth(100)
            name_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_input.setStyleSheet(f"font-size: 11px;")
            grid.addWidget(name_input, 1, i)
            self._ra_name_inputs.append(name_input)

            checks = []
            for j, role in enumerate(ROLES):
                cb = QCheckBox(role)
                cb.setChecked(True)
                cb.setStyleSheet(f"color: {COLORS['text']}; font-size: 10px;")
                grid.addWidget(cb, 2 + j, i)
                checks.append(cb)
            self._ra_checkboxes.append(checks)

        body.addLayout(grid)

        res_col = QVBoxLayout()
        res_col.addWidget(_dim_label("Assigned:"))
        self._ra_result = QLabel()
        self._ra_result.setStyleSheet(f"""
            background-color: {COLORS['bg_input']};
            color: {COLORS['text']};
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            padding: 6px;
            font-size: 11px;
            min-width: 150px;
            min-height: 80px;
        """)
        self._ra_result.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._ra_result.setWordWrap(True)
        res_col.addWidget(self._ra_result)
        body.addLayout(res_col)

        body.addStretch()
        layout.addLayout(body)

        btn = QPushButton("Assign Roles")
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['gold_dark']};
                color: {COLORS['text_bright']};
                font-weight: bold;
                padding: 6px 16px;
                border-radius: 5px;
                font-size: 12px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {COLORS['gold']};
                color: {COLORS['bg_dark']};
            }}
        """)
        btn.setFixedHeight(32)
        btn.setFixedWidth(160)
        btn.clicked.connect(self._assign_roles)
        layout.addWidget(btn)

        return widget

    def _assign_roles(self):
        available = []
        for i in range(5):
            roles = []
            for j, role in enumerate(ROLES):
                if self._ra_checkboxes[i][j].isChecked():
                    roles.append(role)
            available.append(roles)

        assigned = [None] * 5
        success = False

        for _ in range(1000):
            assigned = [None] * 5
            used = set()
            ok = True
            order = list(range(5))
            random.shuffle(order)

            for i in order:
                shuffled = list(available[i])
                random.shuffle(shuffled)
                found = False
                for role in shuffled:
                    if role not in used:
                        assigned[i] = role
                        used.add(role)
                        found = True
                        break
                if not found:
                    ok = False
                    break

            if ok:
                success = True
                break

        if not success:
            QMessageBox.warning(self, "Error",
                                "Could not find valid role assignment!\nMake sure each role can be filled.")
            return

        result = ""
        for role in ROLES:
            for i in range(5):
                if assigned[i] == role:
                    result += f"{role}: {self._ra_name_inputs[i].text()}\n"
                    break
        self._ra_result.setText(result.strip())

    # ── 7. Stopwatch ─────────────────────────────────────────────────────

    def _build_stopwatch(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(_section_title("Stopwatch"))

        self._sw_display = QLabel("00:00:00")
        self._sw_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sw_display.setStyleSheet(f"""
            color: {COLORS['text_bright']};
            font-size: 48px;
            font-weight: bold;
            font-family: 'Consolas', monospace;
            border: none;
        """)
        layout.addWidget(self._sw_display)

        btn_row = QHBoxLayout()

        self._sw_start_btn = QPushButton("Start")
        self._sw_start_btn.setFixedSize(100, 50)
        self._sw_start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['green']};
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 6px;
                border: none;
            }}
        """)
        self._sw_start_btn.clicked.connect(self._toggle_stopwatch)
        btn_row.addWidget(self._sw_start_btn)

        self._sw_reset_btn = QPushButton("Reset")
        self._sw_reset_btn.setFixedSize(100, 50)
        self._sw_reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['text_dim']};
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 6px;
                border: none;
            }}
        """)
        self._sw_reset_btn.clicked.connect(self._reset_stopwatch)
        btn_row.addWidget(self._sw_reset_btn)

        layout.addLayout(btn_row)

        self._sw_running = False
        self._sw_start_time = 0.0
        self._sw_elapsed = 0.0
        self._sw_timer = QTimer()
        self._sw_timer.setInterval(100)
        self._sw_timer.timeout.connect(self._stopwatch_tick)

        return widget

    def _toggle_stopwatch(self):
        if self._sw_running:
            self._sw_elapsed += time.time() - self._sw_start_time
            self._sw_timer.stop()
            self._sw_running = False
            self._sw_start_btn.setText("Start")
            self._sw_start_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['green']};
                    color: white; font-size: 16px; font-weight: bold;
                    border-radius: 6px; border: none;
                }}
            """)
        else:
            self._sw_start_time = time.time()
            self._sw_timer.start()
            self._sw_running = True
            self._sw_start_btn.setText("Pause")
            self._sw_start_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['orange']};
                    color: white; font-size: 16px; font-weight: bold;
                    border-radius: 6px; border: none;
                }}
            """)

    def _reset_stopwatch(self):
        self._sw_timer.stop()
        self._sw_running = False
        self._sw_elapsed = 0.0
        self._sw_display.setText("00:00:00")
        self._sw_start_btn.setText("Start")
        self._sw_start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['green']};
                color: white; font-size: 16px; font-weight: bold;
                border-radius: 6px; border: none;
            }}
        """)

    def _stopwatch_tick(self):
        total = self._sw_elapsed + (time.time() - self._sw_start_time)
        h = int(total // 3600)
        m = int((total % 3600) // 60)
        s = int(total % 60)
        self._sw_display.setText(f"{h:02d}:{m:02d}:{s:02d}")

    # ── 8. Dare Game ─────────────────────────────────────────────────────

    def _build_dare_game(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(_section_title("The Dare Game"))
        layout.addWidget(_dim_label("Set a timer and difficulty — random dares appear at each interval!"))

        controls = QHBoxLayout()

        controls.addWidget(_dim_label("Difficulty:"))
        self._dare_difficulty = QComboBox()
        self._dare_difficulty.addItems(["Normal", "Hard", "Extreme"])
        self._dare_difficulty.setFixedWidth(100)
        controls.addWidget(self._dare_difficulty)

        controls.addWidget(_dim_label("Interval:"))
        self._dare_interval = QLineEdit("30")
        self._dare_interval.setFixedWidth(40)
        self._dare_interval.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._dare_interval.setStyleSheet("font-size: 11px;")
        controls.addWidget(self._dare_interval)
        controls.addWidget(_dim_label("sec"))

        self._dare_start_btn = QPushButton("Start")
        self._dare_start_btn.setFixedSize(80, 30)
        self._dare_start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['green']};
                color: white; font-size: 12px; font-weight: bold;
                border-radius: 5px; border: none;
            }}
        """)
        self._dare_start_btn.clicked.connect(self._toggle_dare)
        controls.addWidget(self._dare_start_btn)

        self._dare_timer_label = QLabel("Timer: Off")
        self._dare_timer_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")
        controls.addWidget(self._dare_timer_label)

        controls.addStretch()
        layout.addLayout(controls)

        self._dare_label = QLabel("Press Start to begin the Dare Game!")
        self._dare_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._dare_label.setWordWrap(True)
        self._dare_label.setStyleSheet(f"""
            background-color: {COLORS['bg_input']};
            color: {COLORS['text_bright']};
            border: 2px solid {COLORS['border']};
            border-radius: 6px;
            font-size: 16px;
            padding: 16px;
            min-height: 80px;
        """)
        layout.addWidget(self._dare_label)

        next_btn = QPushButton("Next Dare")
        next_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['gold_dark']};
                color: {COLORS['text_bright']};
                font-weight: bold;
                padding: 6px 16px;
                border-radius: 5px;
                font-size: 12px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {COLORS['gold']};
                color: {COLORS['bg_dark']};
            }}
        """)
        next_btn.setFixedHeight(28)
        next_btn.setFixedWidth(120)
        next_btn.clicked.connect(self._show_next_dare)
        layout.addWidget(next_btn)

        self._dare_timer = QTimer()
        self._dare_timer.timeout.connect(self._dare_tick)

        return widget

    def _toggle_dare(self):
        if self._dare_start_btn.text() == "Start":
            try:
                interval = int(self._dare_interval.text())
                if interval <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Error", "Enter a valid interval!")
                return

            self._dare_timer.setInterval(interval * 1000)
            self._dare_timer.start()
            self._dare_start_btn.setText("Stop")
            self._dare_start_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['red']};
                    color: white; font-size: 12px; font-weight: bold;
                    border-radius: 5px; border: none;
                }}
            """)
            self._dare_timer_label.setText(f"Timer: Running ({interval}s)")
            self._dare_timer_label.setStyleSheet(f"color: {COLORS['green']}; font-size: 11px; border: none;")
            self._dare_tick()
        else:
            self._dare_timer.stop()
            self._dare_start_btn.setText("Start")
            self._dare_start_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['green']};
                    color: white; font-size: 12px; font-weight: bold;
                    border-radius: 5px; border: none;
                }}
            """)
            self._dare_timer_label.setText("Timer: Off")
            self._dare_timer_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; border: none;")

    def _dare_tick(self):
        self._show_next_dare()

    def _show_next_dare(self):
        idx = self._dare_difficulty.currentIndex()
        if idx == 0:
            pool = NORMAL_DARES
        elif idx == 1:
            pool = HARD_DARES
        else:
            pool = EXTREME_DARES

        current = self._dare_label.text()
        dare = random.choice(pool)
        while dare == current and len(pool) > 1:
            dare = random.choice(pool)
        self._dare_label.setText(dare)

    # ── 8. Team Builder ──────────────────────────────────────────────────

    def _build_team_builder(self) -> QWidget:
        """Build a balanced team composition with roles and synergies."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(_section_title("Team Builder"))
        layout.addWidget(_dim_label("Generate a balanced 5-man team composition"))

        # Team display container
        self._team_builder_widget = QWidget()
        team_layout = QVBoxLayout(self._team_builder_widget)
        team_layout.setSpacing(8)
        team_layout.setContentsMargins(16, 16, 16, 16)
        self._team_builder_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
        """)

        # Role labels storage
        self._team_roles = {}
        roles = ["TOP", "JUNGLE", "MID", "ADC", "SUPPORT"]

        for role in roles:
            role_row = QHBoxLayout()

            role_label = QLabel(f"{role}:")
            role_label.setFixedWidth(80)
            role_label.setStyleSheet(f"color: {COLORS['gold']}; font-weight: bold; font-size: 13px; border: none; background: transparent;")
            role_row.addWidget(role_label)

            # Icon + champ container
            champ_container = QWidget()
            champ_container.setStyleSheet("background: transparent; border: none;")
            champ_layout = QHBoxLayout(champ_container)
            champ_layout.setContentsMargins(0, 0, 0, 0)
            champ_layout.setSpacing(8)

            icon_label = QLabel()
            icon_label.setFixedSize(28, 28)
            icon_label.setStyleSheet("border: none; background: transparent;")
            champ_layout.addWidget(icon_label)

            champ_label = QLabel("-")
            champ_label.setStyleSheet(f"color: {COLORS['text']}; font-size: 13px; border: none; background: transparent;")
            champ_label.setMinimumWidth(120)
            champ_layout.addWidget(champ_label)
            champ_layout.addStretch()

            role_row.addWidget(champ_container)
            role_row.addStretch()

            self._team_roles[role] = {'icon': icon_label, 'text': champ_label}
            team_layout.addLayout(role_row)

        layout.addWidget(self._team_builder_widget)

        # Composition type selector
        comp_row = QHBoxLayout()
        comp_label = QLabel("Comp Type:")
        comp_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px;")
        comp_row.addWidget(comp_label)

        self._team_comp_type = QComboBox()
        self._team_comp_type.addItems([
            "Balanced",
            "Poke",
            "Engage",
            "Split Push",
            "Protect the ADC",
            "Full AP",
            "Full AD",
            "All Random"
        ])
        self._team_comp_type.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
            }}
        """)
        comp_row.addWidget(self._team_comp_type)
        comp_row.addStretch()
        layout.addLayout(comp_row)

        # Generate button
        gen_btn = QPushButton("GENERATE TEAM")
        gen_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['gold_dark']};
                color: {COLORS['text_bright']};
                font-size: 12px;
                font-weight: bold;
                padding: 10px 24px;
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {COLORS['gold']};
            }}
        """)
        gen_btn.clicked.connect(self._generate_team)
        layout.addWidget(gen_btn)

        return widget

    def _generate_team(self):
        """Generate a team composition based on selected type."""
        comp_type = self._team_comp_type.currentText()

        # Role-specific champion pools (expanded)
        top_pool = ["Garen", "Darius", "Ornn", "Malphite", "Fiora", "Jax", "Camille", "Sett", "Mordekaiser", "Aatrox",
                    "Renekton", "Shen", "Illaoi", "Volibear", "Nasus", "Cho'Gath", "Gwen", "K'Sante"]
        jungle_pool = ["Lee Sin", "Elise", "Jarvan IV", "Kha'Zix", "Vi", "Hecarim", "Amumu", "Zac", "Kayn", "Viego",
                       "Nocturne", "Shyvana", "Warwick", "Udyr", "Sejuani", "Rek'Sai", "Lillia", "Bel'Veth"]
        mid_pool = ["Ahri", "Syndra", "Orianna", "Zed", "Yasuo", "Lux", "Viktor", "Akali", "Sylas", "LeBlanc",
                    "Katarina", "Fizz", "Vex", "Yone", "Veigar", "Twisted Fate", "Cassiopeia", "Azir"]
        adc_pool = ["Jinx", "Caitlyn", "Kai'Sa", "Ezreal", "Jhin", "Miss Fortune", "Vayne", "Ashe", "Aphelios", "Samira",
                    "Tristana", "Lucian", "Xayah", "Sivir", "Draven", "Twitch", "Kog'Maw", "Zeri"]
        support_pool = ["Thresh", "Nautilus", "Lulu", "Janna", "Leona", "Braum", "Nami", "Morgana", "Blitzcrank", "Soraka",
                        "Rakan", "Alistar", "Bard", "Yuumi", "Senna", "Rell", "Renata Glasc", "Milio"]

        # Modify pools based on comp type
        if comp_type == "Poke":
            top_pool = ["Jayce", "Gnar", "Kennen", "Gangplank", "Vladimir", "Teemo"]
            mid_pool = ["Jayce", "Xerath", "Ziggs", "Vel'Koz", "Zoe", "Lux", "Varus"]
            adc_pool = ["Ezreal", "Varus", "Caitlyn", "Kog'Maw", "Sivir"]
            support_pool = ["Vel'Koz", "Xerath", "Karma", "Lux", "Janna", "Sona"]
        elif comp_type == "Engage":
            top_pool = ["Malphite", "Ornn", "Sion", "Shen", "Cho'Gath", "K'Sante"]
            jungle_pool = ["Jarvan IV", "Zac", "Amumu", "Vi", "Sejuani", "Rek'Sai", "Hecarim"]
            mid_pool = ["Galio", "Twisted Fate", "Lissandra", "Sylas", "Diana"]
            support_pool = ["Leona", "Nautilus", "Rakan", "Alistar", "Thresh", "Rell"]
        elif comp_type == "Split Push":
            top_pool = ["Fiora", "Jax", "Tryndamere", "Camille", "Yorick", "Gwen", "Shen"]
            jungle_pool = ["Master Yi", "Udyr", "Shyvana", "Trundle", "Warwick"]
            mid_pool = ["Zed", "Talon", "Katarina", "Yasuo", "Yone", "Akshan"]
        elif comp_type == "Protect the ADC":
            top_pool = ["Ornn", "Shen", "Maokai", "Sion", "Cho'Gath", "Malphite"]
            jungle_pool = ["Ivern", "Sejuani", "Poppy", "Nunu & Willump", "Maokai"]
            mid_pool = ["Lulu", "Karma", "Orianna", "Zilean", "Seraphine"]
            support_pool = ["Lulu", "Janna", "Yuumi", "Thresh", "Taric", "Braum", "Renata Glasc"]
        elif comp_type == "Full AP":
            top_pool = ["Mordekaiser", "Vladimir", "Rumble", "Teemo", "Gwen", "Kennen", "Gragas"]
            jungle_pool = ["Elise", "Nidalee", "Ekko", "Lillia", "Fiddlesticks", "Shyvana", "Diana"]
            mid_pool = ["Syndra", "Ahri", "Viktor", "Veigar", "Cassiopeia", "Azir", "Vex"]
            adc_pool = ["Ziggs", "Seraphine", "Karthus", "Veigar", "Swain"]
            support_pool = ["Lux", "Brand", "Zyra", "Vel'Koz", "Xerath", "Swain"]
        elif comp_type == "Full AD":
            top_pool = ["Jayce", "Pantheon", "Riven", "Renekton", "Kled", "Urgot"]
            jungle_pool = ["Graves", "Kha'Zix", "Rengar", "Kindred", "Master Yi", "Nocturne"]
            mid_pool = ["Zed", "Talon", "Qiyana", "Yasuo", "Yone", "Jayce", "Lucian"]
            adc_pool = ["Draven", "Jhin", "Caitlyn", "Lucian", "Samira", "Tristana"]
            support_pool = ["Pantheon", "Pyke", "Senna", "Sett", "Blitzcrank"]

        # Select champions with no duplicates
        team = {}
        selected_champs = set()

        for role, pool in [("TOP", top_pool), ("JUNGLE", jungle_pool), ("MID", mid_pool), ("ADC", adc_pool), ("SUPPORT", support_pool)]:
            # Filter out already selected champions
            available = [c for c in pool if c not in selected_champs]
            if available:
                champ = random.choice(available)
                team[role] = champ
                selected_champs.add(champ)
            else:
                # Fallback to any champion from pool if all are taken (shouldn't happen with expanded pools)
                team[role] = random.choice(pool)

        # Update display
        for role, champ in team.items():
            self._team_roles[role]['text'].setText(champ)

            # Set icon if DD available
            if self._dd:
                icon_path = self._dd.get_champion_icon_path(champ)
                if icon_path:
                    pixmap = QPixmap(icon_path)
                    scaled = pixmap.scaled(28, 28, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    self._team_roles[role]['icon'].setPixmap(scaled)
                else:
                    self._team_roles[role]['icon'].clear()
            else:
                self._team_roles[role]['icon'].clear()
