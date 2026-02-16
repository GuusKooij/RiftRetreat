"""
DraftHelper: Analyzes team composition in champion select.

Checks damage type balance (AD vs AP), crowd control density,
engage potential, and suggests picks that complement the team.
"""


# Simplified champion damage type classification
# These are the most common picks; Data Dragon tags help for the rest
AP_CHAMPIONS = {
    'Ahri', 'Akali', 'Anivia', 'Annie', 'Aurelion Sol', 'Aurora', 'Azir',
    'Brand', 'Cassiopeia', 'Diana', 'Ekko', 'Elise', 'Evelynn', 'Fiddlesticks',
    'Fizz', 'Galio', 'Gragas', 'Heimerdinger', 'Hwei', 'Karma', 'Karthus',
    'Kassadin', 'Katarina', 'Kayle', 'Kennen', 'LeBlanc', 'Lillia', 'Lissandra',
    'Lulu', 'Lux', 'Malzahar', 'Milio', 'Morgana', 'Nami', 'Neeko', 'Nidalee',
    'Orianna', 'Rumble', 'Ryze', 'Seraphine', 'Shaco', 'Singed', 'Sona',
    'Soraka', 'Swain', 'Sylas', 'Syndra', 'Taliyah', 'Teemo', 'Twisted Fate',
    'Veigar', 'Vel\'Koz', 'Vex', 'Viktor', 'Vladimir', 'Xerath', 'Ziggs',
    'Zilean', 'Zoe', 'Zyra', 'Smolder', 'Mel', 'Ambessa',
}

# Champions that deal primarily physical damage
AD_CHAMPIONS = {
    'Aatrox', 'Aphelios', 'Ashe', 'Caitlyn', 'Camille', 'Darius', 'Draven',
    'Ezreal', 'Fiora', 'Gangplank', 'Garen', 'Graves', 'Hecarim', 'Illaoi',
    'Irelia', 'Jax', 'Jayce', 'Jhin', 'Jinx', 'Kai\'Sa', 'Kalista', 'Kayn',
    'Kha\'Zix', 'Kindred', 'Kled', 'Lee Sin', 'Lucian', 'Master Yi',
    'Miss Fortune', 'Naafiri', 'Nasus', 'Nocturne', 'Olaf', 'Pantheon',
    'Pyke', 'Qiyana', 'Quinn', 'Rakan', 'Rek\'Sai', 'Renekton', 'Rengar',
    'Riven', 'Samira', 'Senna', 'Sett', 'Sivir', 'Talon', 'Thresh',
    'Tristana', 'Trundle', 'Tryndamere', 'Twitch', 'Udyr', 'Urgot',
    'Varus', 'Vayne', 'Vi', 'Viego', 'Wukong', 'Xayah', 'Xin Zhao',
    'Yasuo', 'Yone', 'Yorick', 'Zed', 'Zeri',
}

# Champions with strong engage tools
ENGAGE_CHAMPIONS = {
    'Aatrox', 'Alistar', 'Amumu', 'Camille', 'Diana', 'Galio', 'Gnar',
    'Gragas', 'Hecarim', 'Jarvan IV', 'Kennen', 'Leona', 'Malphite',
    'Maokai', 'Nautilus', 'Ornn', 'Rakan', 'Rell', 'Sejuani', 'Sion',
    'Thresh', 'Vi', 'Wukong', 'Zac',
}


class DraftHelper:
    def __init__(self, data_dragon=None):
        self.dd = data_dragon

    def analyze_team(self, champion_names: list[str]) -> dict:
        """Analyze a team composition for balance."""
        if not champion_names:
            return {}

        ad_count = 0
        ap_count = 0
        mixed_count = 0
        engage_count = 0

        for name in champion_names:
            if not name:
                continue
            is_ad = name in AD_CHAMPIONS
            is_ap = name in AP_CHAMPIONS

            if is_ad and not is_ap:
                ad_count += 1
            elif is_ap and not is_ad:
                ap_count += 1
            else:
                mixed_count += 1

            if name in ENGAGE_CHAMPIONS:
                engage_count += 1

        total = ad_count + ap_count + mixed_count
        warnings = []

        if ad_count >= 4:
            warnings.append("Full AD team -- enemy can stack armor!")
        elif ap_count >= 4:
            warnings.append("Full AP team -- enemy can stack MR!")
        elif ad_count == 0 and total >= 3:
            warnings.append("No AD damage -- consider an AD pick")
        elif ap_count == 0 and total >= 3:
            warnings.append("No AP damage -- consider an AP pick")

        if engage_count == 0 and total >= 3:
            warnings.append("No engage -- team may struggle to start fights")

        return {
            'ad_count': ad_count,
            'ap_count': ap_count,
            'mixed_count': mixed_count,
            'engage_count': engage_count,
            'total_picked': total,
            'damage_balance': 'balanced' if abs(ad_count - ap_count) <= 1 else (
                'AD heavy' if ad_count > ap_count else 'AP heavy'
            ),
            'warnings': warnings,
        }

    def suggest_damage_type(self, team_champion_names: list[str]) -> str:
        """Suggest what damage type to pick based on team comp."""
        analysis = self.analyze_team(team_champion_names)
        if analysis.get('ad_count', 0) > analysis.get('ap_count', 0) + 1:
            return 'AP'
        elif analysis.get('ap_count', 0) > analysis.get('ad_count', 0) + 1:
            return 'AD'
        return 'either'
