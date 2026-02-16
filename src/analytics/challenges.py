"""
ChallengeAnalyzer: Challenge progress tracking, champion recommendations,
and in-game tips for progressing challenges.
"""

import time
from collections import defaultdict

# Tier thresholds for key challenges (from Riot API config)
TIER_ORDER = ['IRON', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'DIAMOND', 'MASTER', 'GRANDMASTER', 'CHALLENGER']

# In-game tips mapped to challenge categories/types
IN_GAME_TIPS = {
    # Champion diversity
    'jack_of_all_champs': "Win on a new champion to progress this challenge",
    'invincible': "Go deathless this game! Play safe and avoid risky fights",
    'perfectionist': "Aim for an S+ grade -- high CS, vision, low deaths, and KP",

    # Mastery
    'mastery_milestone': "You need an S- or higher grade for your next mastery mark",
    'master_yourself': "Get this champion to Mastery 5 to progress",
    'master_the_enemy': "Get this champion to Mastery 10 to progress",

    # Objectives
    'soul_sweep': "Focus drakes! Contest every dragon spawn, pick champs with drake control",
    'draconic_extinction': "Kill a dragon this game to progress with this champion",
    'baron_power_play': "If you get baron, push to end -- baron + win = challenge progress",
    'uninhibited': "Destroy inhibitors when you get the chance",

    # Combat
    'unkillable': "Stay alive! Low deaths with high KP is the goal",
    'double_trouble': "Look for 2v2 or teamfight situations to get double kills",
    'penta_kills': "In teamfights, try to clean up for the penta",
}


class ChallengeAnalyzer:
    def __init__(self, challenges: dict, challenges_config: list[dict],
                 matches: list[dict], mastery: list[dict], data_dragon):
        self.challenges = challenges
        self.config = challenges_config
        self.matches = matches
        self.mastery = mastery
        self.dd = data_dragon

        # Build config lookup by challenge ID
        self.config_by_id = {c['id']: c for c in challenges_config}

        # Build set of retired/archived challenge IDs (not upgradeable anymore)
        now_ms = int(time.time() * 1000)
        self.retired_ids = {
            c['id'] for c in challenges_config
            if c.get('state') == 'ARCHIVED'
            or (c.get('endTimestamp') and c['endTimestamp'] < now_ms)
            or self._is_seasonal_challenge(c)
        }

        # Build player progress lookup
        self.progress = {}
        for c in challenges.get('challenges', []):
            self.progress[c['challengeId']] = c

    @staticmethod
    def _is_seasonal_challenge(config: dict) -> bool:
        """Check if a challenge is a past seasonal challenge (e.g. 2022xxx IDs)."""
        cid = config.get('id', 0)
        # Seasonal challenge IDs start with the year (e.g., 2022000-2022999)
        # Current season challenges should NOT be filtered
        current_year = int(time.strftime('%Y'))
        if 2000000 <= cid <= 2099999:
            challenge_year = cid // 1000
            if challenge_year < current_year:
                return True
        return False

    def get_challenge_info(self, challenge_id: int) -> dict:
        """Get combined config + progress for a challenge."""
        config = self.config_by_id.get(challenge_id, {})
        progress = self.progress.get(challenge_id, {})

        current_value = progress.get('value', 0)
        current_level = progress.get('level', 'NONE')

        # Find next tier threshold
        thresholds = config.get('thresholds', {})
        next_tier = None
        next_threshold = None

        current_idx = TIER_ORDER.index(current_level) if current_level in TIER_ORDER else -1
        for tier in TIER_ORDER[current_idx + 1:]:
            if tier in thresholds:
                next_tier = tier
                next_threshold = thresholds[tier]
                break

        return {
            'id': challenge_id,
            'name': config.get('localizedNames', {}).get('en_US', {}).get('name', f'Challenge {challenge_id}'),
            'description': config.get('localizedNames', {}).get('en_US', {}).get('description', ''),
            'short_description': config.get('localizedNames', {}).get('en_US', {}).get('shortDescription', ''),
            'current_value': current_value,
            'current_level': current_level,
            'next_tier': next_tier,
            'next_threshold': next_threshold,
            'remaining': (next_threshold - current_value) if next_threshold else 0,
            'percentile': progress.get('percentile', 0),
        }

    def tracked_challenges(self) -> list[dict]:
        """Get progress on key trackable challenges, sorted by closest to next tier."""
        # Key challenge IDs to track
        key_challenges = []

        # Find all active challenges close to leveling up (skip retired/archived)
        for c in self.challenges.get('challenges', []):
            cid = c['challengeId']
            if cid in self.retired_ids:
                continue
            info = self.get_challenge_info(cid)

            # Only include challenges with a next tier to reach
            if info['next_threshold'] is not None and info['remaining'] > 0:
                # Calculate progress percentage
                current_tier_threshold = 0
                thresholds = self.config_by_id.get(cid, {}).get('thresholds', {})
                current_level = info['current_level']
                if current_level in thresholds:
                    current_tier_threshold = thresholds[current_level]

                range_total = info['next_threshold'] - current_tier_threshold
                range_done = info['current_value'] - current_tier_threshold
                progress_pct = round(range_done / max(range_total, 1) * 100, 1)

                info['progress_pct'] = progress_pct
                key_challenges.append(info)

        # Sort by progress percentage (closest to completion first)
        key_challenges.sort(key=lambda x: x['progress_pct'], reverse=True)
        return key_challenges

    def close_to_leveling(self, top_n: int = 15) -> list[dict]:
        """Challenges closest to reaching the next tier."""
        tracked = self.tracked_challenges()
        return tracked[:top_n]

    def champions_won_with_this_season(self) -> set[int]:
        """Set of champion IDs the player has won with this season (from match history)."""
        return {m['champion_id'] for m in self.matches if m['win']}

    def jack_of_all_champs_progress(self) -> dict:
        """Get Jack of All Champs (401106) progress from the actual API data.

        Returns real lifetime value, not just this season's match history.
        """
        JACK_ID = 401106
        info = self.get_challenge_info(JACK_ID)
        return {
            'value': int(info['current_value']),  # Real champion count from API
            'level': info['current_level'],
            'next_tier': info['next_tier'],
            'next_threshold': info['next_threshold'],
            'remaining': info['remaining'],
            'total_champions': len(self.dd.get_all_champions()) if self.dd else 0,
        }

    def champions_not_won_with_lifetime(self) -> list[dict]:
        """Champions likely never won with (lifetime), for Jack of All Champs progress.

        Logic: The API tells us HOW MANY champs we've won with (e.g. 140/172),
        but not WHICH ones. We identify the most likely candidates by:
        1. Champions with 0 mastery points = definitely never won with
        2. Champions with very low mastery = likely never won with
        We return (total - won_count) champions, prioritized by lowest mastery.
        """
        jack = self.jack_of_all_champs_progress()
        won_count = jack['value']
        total = jack['total_champions'] or 0
        not_won_count = total - won_count

        if not_won_count <= 0 or not self.dd:
            return []

        all_champs = self.dd.get_champion_list()
        mastery_by_id = {m['championId']: m for m in self.mastery}

        champ_list = []
        for champ in all_champs:
            cid = champ['id']
            m = mastery_by_id.get(cid)
            mastery_points = m.get('championPoints', 0) if m else 0
            mastery_level = m.get('championLevel', 0) if m else 0

            champ_list.append({
                'champion': champ['name'],
                'champion_id': cid,
                'mastery_level': mastery_level,
                'mastery_points': mastery_points,
                'tags': champ.get('tags', []),
            })

        # Sort by mastery points ascending — lowest mastery = most likely never won
        champ_list.sort(key=lambda x: x['mastery_points'])

        # Return exactly not_won_count champions (the bottom N by mastery)
        return champ_list[:not_won_count]

    def champions_not_won_with_this_season(self) -> list[dict]:
        """Champions with mastery but no win this season — good picks for variety.

        Note: This is NOT the same as Jack of All Champs (which tracks lifetime).
        This helps find champions you haven't played recently.
        """
        won_ids = self.champions_won_with_this_season()

        not_won = []
        for m in self.mastery:
            if m['championId'] not in won_ids:
                name = self.dd.get_champion_name(m['championId'])
                champ_data = self.dd.get_champion_by_id(m['championId'])
                tags = champ_data.get('tags', []) if champ_data else []

                not_won.append({
                    'champion': name,
                    'champion_id': m['championId'],
                    'mastery_level': m.get('championLevel', 0),
                    'mastery_points': m.get('championPoints', 0),
                    'tags': tags,
                })

        # Sort by mastery (higher mastery = more comfortable pick)
        not_won.sort(key=lambda x: x['mastery_points'], reverse=True)
        return not_won

    def champion_recommendations(self) -> list[dict]:
        """Recommend champions that progress MULTIPLE challenges at once.

        Considers: Jack of All Champs, class mastery, Catch 'em All,
        mastery milestones, and comfort level.
        """
        won_ids = self.champions_won_with_this_season()
        recommendations = []

        for m in self.mastery:
            champ_id = m['championId']
            name = self.dd.get_champion_name(champ_id)
            champ_data = self.dd.get_champion_by_id(champ_id)
            tags = champ_data.get('tags', []) if champ_data else []

            reasons = []
            score = 0

            # Not won with this season — good for variety / challenge progress
            if champ_id not in won_ids:
                reasons.append("No win this season (variety pick)")
                score += 3

            # Mastery level progression
            mastery_level = m.get('championLevel', 0)
            mastery_points = m.get('championPoints', 0)
            marks_needed = m.get('markRequiredForNextLevel', 0)

            if mastery_level < 5:
                reasons.append(f"Master Yourself (close to M5, currently M{mastery_level})")
                score += 2
            elif mastery_level < 10:
                reasons.append(f"Master the Enemy (close to M10, currently M{mastery_level})")
                score += 2

            if marks_needed and marks_needed <= 2:
                reasons.append(f"Mastery mark needed ({marks_needed} marks to next level)")
                score += 1

            # Class mastery: check per-tag challenges
            for tag in tags:
                reasons.append(f"Master {tag} challenge")
                score += 1

            # Higher mastery = more comfortable = better recommendation
            comfort_bonus = min(mastery_points / 50000, 2)  # Cap at 2 bonus points
            score += comfort_bonus

            if reasons:
                # Suggest best role based on champion tags
                suggested_roles = []
                if 'Marksman' in tags:
                    suggested_roles.append('BOTTOM')
                if 'Support' in tags:
                    suggested_roles.append('SUPPORT')
                if 'Mage' in tags:
                    suggested_roles.extend(['MIDDLE', 'SUPPORT'])
                if 'Assassin' in tags:
                    suggested_roles.append('MIDDLE')
                if 'Fighter' in tags:
                    suggested_roles.append('TOP')
                if 'Tank' in tags:
                    suggested_roles.extend(['TOP', 'SUPPORT'])
                if not suggested_roles:
                    suggested_roles.append('BOTTOM')

                recommendations.append({
                    'champion': name,
                    'champion_id': champ_id,
                    'tags': tags,
                    'mastery_level': mastery_level,
                    'mastery_points': mastery_points,
                    'reasons': reasons,
                    'score': round(score, 1),
                    'suggested_roles': list(dict.fromkeys(suggested_roles)),  # Dedupe, preserve order
                    'new_win': champ_id not in won_ids,
                })

        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations

    def get_in_game_tips(self, champion_name: str = None) -> list[dict]:
        """Get actionable in-game tips based on active challenge progress.

        If champion_name is provided, tailor tips to that specific champion.
        """
        tips = []
        close = self.close_to_leveling(top_n=30)

        for challenge in close:
            name_lower = challenge['name'].lower()
            tip_text = None
            priority = 0

            # Match challenge to tip category
            if 'jack of all' in name_lower:
                tip_text = IN_GAME_TIPS['jack_of_all_champs']
                priority = 3
            elif 'invincible' in name_lower:
                tip_text = IN_GAME_TIPS['invincible']
                priority = 2
            elif 'perfectionist' in name_lower or 's+' in name_lower or 's-' in name_lower:
                tip_text = IN_GAME_TIPS['perfectionist']
                priority = 2
            elif 'soul' in name_lower and 'sweep' in name_lower:
                tip_text = IN_GAME_TIPS['soul_sweep']
                priority = 2
            elif 'dragon' in name_lower or 'draconic' in name_lower:
                tip_text = IN_GAME_TIPS['draconic_extinction']
                priority = 1
            elif 'baron' in name_lower:
                tip_text = IN_GAME_TIPS['baron_power_play']
                priority = 1
            elif 'inhibit' in name_lower:
                tip_text = IN_GAME_TIPS['uninhibited']
                priority = 1
            elif 'unkillable' in name_lower:
                tip_text = IN_GAME_TIPS['unkillable']
                priority = 2
            elif 'double' in name_lower:
                tip_text = IN_GAME_TIPS['double_trouble']
                priority = 1
            elif 'penta' in name_lower:
                tip_text = IN_GAME_TIPS['penta_kills']
                priority = 1
            elif 'master yourself' in name_lower:
                tip_text = IN_GAME_TIPS['master_yourself']
                priority = 1
            elif 'master the enemy' in name_lower or 'master' in name_lower and 'mastery' in challenge.get('description', '').lower():
                tip_text = IN_GAME_TIPS['master_the_enemy']
                priority = 1

            if tip_text:
                remaining = challenge['remaining']
                next_tier = challenge['next_tier']
                progress = challenge.get('progress_pct', 0)

                tips.append({
                    'challenge_name': challenge['name'],
                    'tip': tip_text,
                    'progress': f"{challenge['current_value']:.0f}/{challenge['next_threshold']:.0f} to {next_tier}",
                    'progress_pct': progress,
                    'remaining': remaining,
                    'priority': priority,
                })

        tips.sort(key=lambda x: (-x['priority'], -x['progress_pct']))
        return tips

    def total_points(self) -> dict:
        """Get total challenge points summary."""
        return self.challenges.get('totalPoints', {})

    def category_points(self) -> dict:
        """Get per-category challenge points."""
        return self.challenges.get('categoryPoints', {})

    # --- Challenge Planner / Roadmap ---

    def challenge_roadmap(self, top_n: int = 10) -> list[dict]:
        """Shortest path to next challenge tier — easiest ones to level up.

        Estimates effort based on remaining distance as fraction of threshold.
        """
        tracked = self.tracked_challenges()
        roadmap = []

        for c in tracked[:top_n * 3]:
            remaining = c['remaining']
            if remaining <= 0:
                continue

            effort = remaining / max(c['next_threshold'], 1)
            tier_points = self._tier_to_points(c['next_tier']) - self._tier_to_points(c['current_level'])

            roadmap.append({
                'name': c['name'],
                'description': c.get('description', ''),
                'current_level': c['current_level'],
                'next_tier': c['next_tier'],
                'current_value': c['current_value'],
                'next_threshold': c['next_threshold'],
                'remaining': remaining,
                'progress_pct': c.get('progress_pct', 0),
                'effort': round(effort, 3),
                'points_gain': tier_points,
            })

        roadmap.sort(key=lambda x: (x['effort'], -x['points_gain']))
        return roadmap[:top_n]

    @staticmethod
    def _tier_to_points(tier: str) -> int:
        """Approximate challenge points for reaching a tier."""
        points = {
            'NONE': 0, 'IRON': 5, 'BRONZE': 10, 'SILVER': 15,
            'GOLD': 25, 'PLATINUM': 40, 'DIAMOND': 60,
            'MASTER': 80, 'GRANDMASTER': 100, 'CHALLENGER': 120,
        }
        return points.get(tier, 0)

    # Champion -> common roles mapping for team comp suggestions
    CHAMP_ROLES = {
        # TOP
        'Aatrox': 'TOP', 'Ambessa': 'TOP', 'Camille': 'TOP', 'Cho\'Gath': 'TOP', 'Darius': 'TOP',
        'Dr. Mundo': 'TOP', 'Fiora': 'TOP', 'Gangplank': 'TOP', 'Garen': 'TOP', 'Gnar': 'TOP',
        'Gwen': 'TOP', 'Illaoi': 'TOP', 'Irelia': 'TOP', 'Jax': 'TOP', 'Jayce': 'TOP',
        'K\'Sante': 'TOP', 'Kayle': 'TOP', 'Kennen': 'TOP', 'Kled': 'TOP', 'Malphite': 'TOP',
        'Mordekaiser': 'TOP', 'Nasus': 'TOP', 'Olaf': 'TOP', 'Ornn': 'TOP', 'Pantheon': 'TOP',
        'Quinn': 'TOP', 'Renekton': 'TOP', 'Riven': 'TOP', 'Rumble': 'TOP', 'Sett': 'TOP',
        'Shen': 'TOP', 'Singed': 'TOP', 'Sion': 'TOP', 'Teemo': 'TOP', 'Tahm Kench': 'TOP',
        'Trundle': 'TOP', 'Tryndamere': 'TOP', 'Urgot': 'TOP', 'Volibear': 'TOP', 'Wukong': 'TOP',
        'Yasuo': 'TOP', 'Yone': 'TOP', 'Yorick': 'TOP',
        # JUNGLE
        'Amumu': 'JUNGLE', 'Bel\'Veth': 'JUNGLE', 'Briar': 'JUNGLE', 'Diana': 'JUNGLE',
        'Ekko': 'JUNGLE', 'Elise': 'JUNGLE', 'Evelynn': 'JUNGLE', 'Fiddlesticks': 'JUNGLE',
        'Gragas': 'JUNGLE', 'Graves': 'JUNGLE', 'Hecarim': 'JUNGLE', 'Ivern': 'JUNGLE',
        'Jarvan IV': 'JUNGLE', 'Karthus': 'JUNGLE', 'Kayn': 'JUNGLE', 'Kha\'Zix': 'JUNGLE',
        'Kindred': 'JUNGLE', 'Lee Sin': 'JUNGLE', 'Lillia': 'JUNGLE', 'Master Yi': 'JUNGLE',
        'Maokai': 'JUNGLE', 'Nidalee': 'JUNGLE', 'Nocturne': 'JUNGLE', 'Nunu & Willump': 'JUNGLE',
        'Poppy': 'JUNGLE', 'Rammus': 'JUNGLE', 'Rek\'Sai': 'JUNGLE', 'Rengar': 'JUNGLE',
        'Sejuani': 'JUNGLE', 'Shaco': 'JUNGLE', 'Shyvana': 'JUNGLE', 'Skarner': 'JUNGLE',
        'Udyr': 'JUNGLE', 'Vi': 'JUNGLE', 'Viego': 'JUNGLE', 'Warwick': 'JUNGLE',
        'Xin Zhao': 'JUNGLE', 'Zac': 'JUNGLE',
        # MID
        'Ahri': 'MID', 'Akali': 'MID', 'Anivia': 'MID', 'Annie': 'MID', 'Aurelion Sol': 'MID',
        'Azir': 'MID', 'Cassiopeia': 'MID', 'Corki': 'MID', 'Fizz': 'MID', 'Galio': 'MID',
        'Hwei': 'MID', 'Kassadin': 'MID', 'Katarina': 'MID', 'LeBlanc': 'MID',
        'Lissandra': 'MID', 'Lux': 'MID', 'Malzahar': 'MID', 'Naafiri': 'MID', 'Neeko': 'MID',
        'Orianna': 'MID', 'Qiyana': 'MID', 'Ryze': 'MID', 'Sylas': 'MID', 'Syndra': 'MID',
        'Taliyah': 'MID', 'Talon': 'MID', 'Twisted Fate': 'MID', 'Veigar': 'MID',
        'Vel\'Koz': 'MID', 'Vex': 'MID', 'Viktor': 'MID', 'Vladimir': 'MID', 'Xerath': 'MID',
        'Zed': 'MID', 'Ziggs': 'MID', 'Zoe': 'MID',
        # BOT
        'Aphelios': 'BOT', 'Ashe': 'BOT', 'Caitlyn': 'BOT', 'Draven': 'BOT', 'Ezreal': 'BOT',
        'Jhin': 'BOT', 'Jinx': 'BOT', 'Kai\'Sa': 'BOT', 'Kalista': 'BOT', 'Kog\'Maw': 'BOT',
        'Lucian': 'BOT', 'Miss Fortune': 'BOT', 'Nilah': 'BOT', 'Samira': 'BOT', 'Sivir': 'BOT',
        'Smolder': 'BOT', 'Tristana': 'BOT', 'Twitch': 'BOT', 'Varus': 'BOT', 'Vayne': 'BOT',
        'Xayah': 'BOT', 'Zeri': 'BOT',
        # SUPPORT
        'Alistar': 'SUPPORT', 'Bard': 'SUPPORT', 'Blitzcrank': 'SUPPORT', 'Brand': 'SUPPORT',
        'Braum': 'SUPPORT', 'Janna': 'SUPPORT', 'Karma': 'SUPPORT', 'Leona': 'SUPPORT',
        'Lulu': 'SUPPORT', 'Milio': 'SUPPORT', 'Morgana': 'SUPPORT', 'Nami': 'SUPPORT',
        'Nautilus': 'SUPPORT', 'Pyke': 'SUPPORT', 'Rakan': 'SUPPORT', 'Rell': 'SUPPORT',
        'Renata Glasc': 'SUPPORT', 'Senna': 'SUPPORT', 'Seraphine': 'SUPPORT', 'Sona': 'SUPPORT',
        'Soraka': 'SUPPORT', 'Swain': 'SUPPORT', 'Taric': 'SUPPORT', 'Thresh': 'SUPPORT',
        'Yuumi': 'SUPPORT', 'Zyra': 'SUPPORT', 'Zilean': 'SUPPORT',
    }

    # Region -> Champion mappings (from LoL lore)
    REGION_CHAMPIONS = {
        303501: {  # Bandle City
            'name': 'Bandle City',
            'champions': ['Corki', 'Kennen', 'Lulu', 'Poppy', 'Rumble', 'Teemo', 'Tristana',
                          'Veigar', 'Yuumi', 'Ziggs'],
        },
        303502: {  # Bilgewater
            'name': 'Bilgewater',
            'champions': ['Fizz', 'Gangplank', 'Graves', 'Illaoi', 'Miss Fortune', 'Nautilus',
                          'Nilah', 'Pyke', 'Tahm Kench', 'Twisted Fate'],
        },
        303503: {  # Demacia
            'name': 'Demacia',
            'champions': ['Fiora', 'Galio', 'Garen', 'Jarvan IV', 'Kayle', 'Lucian', 'Lux',
                          'Morgana', 'Poppy', 'Quinn', 'Shyvana', 'Sona', 'Vayne', 'Xin Zhao'],
        },
        303504: {  # Freljord
            'name': 'Freljord',
            'champions': ['Anivia', 'Ashe', 'Braum', 'Gragas', 'Lissandra', 'Nunu & Willump',
                          'Olaf', 'Ornn', 'Sejuani', 'Trundle', 'Tryndamere', 'Udyr', 'Volibear'],
        },
        303505: {  # Ionia
            'name': 'Ionia',
            'champions': ['Ahri', 'Akali', 'Irelia', 'Ivern', 'Jhin', 'Karma', 'Kayn',
                          'Kennen', 'Lee Sin', 'Lillia', 'Master Yi', 'Rakan', 'Sett',
                          'Shen', 'Syndra', 'Varus', 'Wukong', 'Xayah', 'Yasuo', 'Yone', 'Zed'],
        },
        303506: {  # Ixtal
            'name': 'Ixtal',
            'champions': ['Malphite', 'Milio', 'Neeko', 'Nidalee', 'Qiyana', 'Rengar', 'Zyra'],
        },
        303507: {  # Noxus
            'name': 'Noxus',
            'champions': ['Ambessa', 'Cassiopeia', 'Darius', 'Draven', 'Katarina', 'Kled',
                          'LeBlanc', 'Mordekaiser', 'Rell', 'Riven', 'Samira', 'Sion',
                          'Swain', 'Talon', 'Vladimir'],
        },
        303508: {  # Piltover
            'name': 'Piltover',
            'champions': ['Caitlyn', 'Camille', 'Ezreal', 'Heimerdinger', 'Jayce', 'Orianna',
                          'Seraphine', 'Vi'],
        },
        303509: {  # Shadow Isles
            'name': 'Shadow Isles',
            'champions': ['Elise', 'Gwen', 'Hecarim', 'Kalista', 'Karthus', 'Maokai',
                          'Senna', 'Thresh', 'Vex', 'Viego', 'Yorick'],
        },
        303510: {  # Shurima
            'name': 'Shurima',
            'champions': ['Akshan', 'Amumu', 'Azir', 'K\'Sante', 'Nasus', 'Naafiri',
                          'Rammus', 'Renekton', 'Sivir', 'Taliyah', 'Xerath'],
        },
        303511: {  # Targon
            'name': 'Targon',
            'champions': ['Aphelios', 'Aurelion Sol', 'Diana', 'Leona', 'Pantheon', 'Soraka',
                          'Taric', 'Zoe'],
        },
        303512: {  # Void
            'name': 'Void',
            'champions': ['Bel\'Veth', 'Cho\'Gath', 'Kai\'Sa', 'Kassadin', 'Kha\'Zix',
                          'Kog\'Maw', 'Malzahar', 'Rek\'Sai', 'Vel\'Koz'],
        },
        303513: {  # Zaun
            'name': 'Zaun',
            'champions': ['Blitzcrank', 'Dr. Mundo', 'Ekko', 'Janna', 'Jinx', 'Renata Glasc',
                          'Singed', 'Twitch', 'Urgot', 'Viktor', 'Warwick', 'Zac', 'Zeri', 'Ziggs'],
        },
    }

    # Ability theme -> Champion mappings
    ABILITY_CHAMPIONS = {
        303401: {  # Global abilities
            'name': 'Global Abilities',
            'min_required': 3,
            'champions': ['Ashe', 'Draven', 'Ezreal', 'Gangplank', 'Jinx', 'Karthus',
                          'Lux', 'Senna', 'Twisted Fate', 'Nocturne', 'Pantheon',
                          'Rek\'Sai', 'Ryze', 'Shen', 'Soraka', 'Ziggs'],
        },
        303402: {  # Large AOE ult
            'name': 'Large AOE Ult',
            'min_required': 3,
            'champions': ['Amumu', 'Anivia', 'Fiddlesticks', 'Galio', 'Gangplank',
                          'Karthus', 'Kennen', 'Malphite', 'Miss Fortune', 'Morgana',
                          'Neeko', 'Nunu & Willump', 'Orianna', 'Rumble', 'Sejuani',
                          'Zyra', 'Ziggs'],
        },
        303403: {  # Heals/shields
            'name': 'Heals or Shields',
            'min_required': 3,
            'champions': ['Ivern', 'Janna', 'Karma', 'Kayle', 'Lulu', 'Milio',
                          'Nami', 'Nidalee', 'Seraphine', 'Sona', 'Soraka',
                          'Taric', 'Yuumi', 'Zilean', 'Renata Glasc'],
        },
        303404: {  # Defy death
            'name': 'Defy Death',
            'min_required': 3,
            'champions': ['Aatrox', 'Anivia', 'Kindred', 'Sion', 'Tryndamere',
                          'Zilean', 'Zac', 'Kled', 'Kayle'],
        },
        303405: {  # Stealth
            'name': 'Stealth',
            'min_required': 3,
            'champions': ['Akali', 'Evelynn', 'Kha\'Zix', 'Pyke', 'Qiyana', 'Rengar',
                          'Shaco', 'Talon', 'Teemo', 'Twitch', 'Vayne', 'Viego', 'Wukong'],
        },
        303406: {  # Poke
            'name': 'Poke Champs',
            'min_required': 3,
            'champions': ['Caitlyn', 'Ezreal', 'Jayce', 'Kai\'Sa', 'Kog\'Maw', 'Lux',
                          'Nidalee', 'Varus', 'Vel\'Koz', 'Xerath', 'Ziggs', 'Zoe',
                          'Hwei', 'Karma'],
        },
        303407: {  # Summons/Pets
            'name': 'Summons or Pets',
            'min_required': 3,
            'champions': ['Annie', 'Azir', 'Elise', 'Heimerdinger', 'Ivern', 'Malzahar',
                          'Shaco', 'Yorick', 'Zyra', 'Naafiri', 'Bel\'Veth', 'Kindred',
                          'Nidalee'],
        },
        303408: {  # All one class
            'name': 'All One Class',
            'min_required': 5,
            'champions': [],  # Any 5 of the same class — handled dynamically
        },
        303409: {  # Displacements
            'name': 'Displacements',
            'min_required': 3,
            'champions': ['Alistar', 'Blitzcrank', 'Gragas', 'Janna', 'Jayce', 'Lee Sin',
                          'Poppy', 'Singed', 'Syndra', 'Thresh', 'Tristana', 'Vayne',
                          'Volibear', 'Rell', 'Skarner'],
        },
        303410: {  # Traps
            'name': 'Traps',
            'min_required': 3,
            'champions': ['Caitlyn', 'Heimerdinger', 'Jhin', 'Maokai', 'Nidalee', 'Shaco',
                          'Teemo', 'Zyra', 'Jinx', 'Viego'],
        },
        303411: {  # Terrain creation
            'name': 'Terrain Creation',
            'min_required': 3,
            'champions': ['Anivia', 'Azir', 'Jarvan IV', 'Ornn', 'Taliyah', 'Trundle',
                          'Veigar', 'Yorick', 'Bard'],
        },
        303412: {  # 2+ immobilizing spells
            'name': '2+ CC Spells',
            'min_required': 3,
            'champions': ['Alistar', 'Amumu', 'Braum', 'Leona', 'Lissandra', 'Maokai',
                          'Nautilus', 'Rell', 'Sejuani', 'Thresh', 'Zac'],
        },
    }

    def _suggest_team_comps(self, champions: list[str], need_all_5: bool = False) -> list[list[dict]]:
        """Suggest viable team comps from a pool of champions.

        Returns up to 3 comps, each a list of {champion, role} dicts.
        """
        # Assign each champion a primary role
        role_pool = {'TOP': [], 'JUNGLE': [], 'MID': [], 'BOT': [], 'SUPPORT': []}
        for name in champions:
            role = self.CHAMP_ROLES.get(name)
            if role:
                role_pool[role].append(name)
            else:
                # Guess from DD tags
                champ_data = None
                if self.dd:
                    for _, cd in self.dd.champions.items():
                        if cd['name'] == name:
                            champ_data = cd
                            break
                if champ_data:
                    tags = champ_data.get('tags', [])
                    if 'Marksman' in tags:
                        role_pool['BOT'].append(name)
                    elif 'Support' in tags:
                        role_pool['SUPPORT'].append(name)
                    elif 'Assassin' in tags:
                        role_pool['MID'].append(name)
                    elif 'Tank' in tags:
                        role_pool['TOP'].append(name)
                    elif 'Fighter' in tags:
                        role_pool['TOP'].append(name)
                    else:
                        role_pool['MID'].append(name)

        comps = []
        used_sets = set()

        # Try to build up to 3 comps
        for attempt in range(min(3, max(len(v) for v in role_pool.values()) if role_pool else 0)):
            comp = {}
            used = set()
            for role in ['TOP', 'JUNGLE', 'MID', 'BOT', 'SUPPORT']:
                candidates = [c for c in role_pool[role] if c not in used]
                if candidates:
                    pick = candidates[attempt % len(candidates)]
                    comp[role] = pick
                    used.add(pick)

            if need_all_5 and len(comp) < 5:
                # Fill missing roles from remaining pool
                for role in ['TOP', 'JUNGLE', 'MID', 'BOT', 'SUPPORT']:
                    if role not in comp:
                        for name in champions:
                            if name not in used:
                                comp[role] = name
                                used.add(name)
                                break

            if len(comp) >= (5 if need_all_5 else 3):
                comp_key = frozenset(comp.values())
                if comp_key not in used_sets:
                    used_sets.add(comp_key)
                    comps.append([{'champion': v, 'role': k} for k, v in comp.items()])

        return comps[:3]

    def premade_team_comp_challenges(self) -> list[dict]:
        """Get progress on premade 5-man team composition challenges.

        These are the Harmony (ability-themed) and Globetrotter (region-themed)
        challenge groups that require a premade 5 with specific champion types.
        """
        # Harmony group: ability-themed (303401-303412)
        # Globetrotter group: region-themed (303501-303513)
        PREMADE_IDS = [
            # Ability-themed
            303401, 303402, 303403, 303404, 303405, 303406,
            303407, 303408, 303409, 303410, 303411, 303412,
            # Region-themed
            303501, 303502, 303503, 303504, 303505, 303506,
            303507, 303508, 303509, 303510, 303511, 303512, 303513,
        ]

        results = []
        for cid in PREMADE_IDS:
            if cid not in self.config_by_id:
                continue
            info = self.get_challenge_info(cid)

            # Clean HTML tags from description
            desc = info.get('short_description', info.get('description', ''))
            desc = desc.replace('<em>', '').replace('</em>', '').strip()

            # Get champion pool and suggested comps
            champ_data = self.ABILITY_CHAMPIONS.get(cid) or self.REGION_CHAMPIONS.get(cid)
            champions = champ_data.get('champions', []) if champ_data else []
            need_all_5 = cid >= 303500  # Region challenges need all 5 from that region

            # For "All one class" (303408), generate class-based comps dynamically
            if cid == 303408:
                comps = self._all_one_class_comps()
            elif champions:
                comps = self._suggest_team_comps(champions, need_all_5=need_all_5)
            else:
                comps = []

            results.append({
                'id': cid,
                'name': info['name'],
                'description': desc,
                'current_value': int(info['current_value']),
                'current_level': info['current_level'],
                'next_tier': info['next_tier'],
                'next_threshold': info['next_threshold'],
                'remaining': info['remaining'],
                'champions': champions,
                'suggested_comps': comps,
            })

        # Sort: in-progress first (have value > 0), then by name
        results.sort(key=lambda x: (-x['current_value'], x['name']))
        return results

    def _all_one_class_comps(self) -> list[list[dict]]:
        """Generate comps for 'all one class' challenge — 5 fighters, 5 mages, etc."""
        if not self.dd:
            return []
        all_champs = self.dd.get_champion_list()
        class_pools = defaultdict(list)
        for c in all_champs:
            for tag in c.get('tags', []):
                class_pools[tag].append(c['name'])

        comps = []
        for class_name in ['Fighter', 'Mage', 'Tank', 'Assassin', 'Marksman', 'Support']:
            pool = class_pools.get(class_name, [])
            if len(pool) >= 5:
                comp = self._suggest_team_comps(pool, need_all_5=True)
                if comp:
                    comps.append({'class': class_name, 'comp': comp[0]})
        return comps

    def generate_random_comp(self, challenge_id: int) -> list[dict]:
        """Generate a random team comp for a premade challenge.

        Returns a list of {champion, role} dicts for a viable 5-man team.
        """
        import random

        champ_data = self.ABILITY_CHAMPIONS.get(challenge_id) or self.REGION_CHAMPIONS.get(challenge_id)
        if not champ_data:
            # All one class — pick a random class
            if challenge_id == 303408 and self.dd:
                all_champs = self.dd.get_champion_list()
                class_pools = defaultdict(list)
                for c in all_champs:
                    for tag in c.get('tags', []):
                        class_pools[tag].append(c['name'])
                classes = ['Fighter', 'Mage', 'Tank', 'Assassin', 'Marksman', 'Support']
                cls = random.choice(classes)
                champions = class_pools.get(cls, [])
                label = f"All {cls}s"
            else:
                return []
        else:
            champions = champ_data.get('champions', [])
            label = None

        if len(champions) < 3:
            return []

        # Build role assignments with randomization
        role_pool = {'TOP': [], 'JUNGLE': [], 'MID': [], 'BOT': [], 'SUPPORT': []}
        for name in champions:
            role = self.CHAMP_ROLES.get(name)
            if role:
                role_pool[role].append(name)
            elif self.dd:
                for _, cd in self.dd.champions.items():
                    if cd['name'] == name:
                        tags = cd.get('tags', [])
                        if 'Marksman' in tags:
                            role_pool['BOT'].append(name)
                        elif 'Support' in tags:
                            role_pool['SUPPORT'].append(name)
                        elif 'Assassin' in tags:
                            role_pool['MID'].append(name)
                        elif 'Tank' in tags:
                            role_pool['TOP'].append(name)
                        elif 'Fighter' in tags:
                            role_pool['TOP'].append(name)
                        else:
                            role_pool['MID'].append(name)
                        break

        # Shuffle each role pool for randomness
        for role in role_pool:
            random.shuffle(role_pool[role])

        comp = {}
        used = set()
        for role in ['TOP', 'JUNGLE', 'MID', 'BOT', 'SUPPORT']:
            candidates = [c for c in role_pool[role] if c not in used]
            if candidates:
                comp[role] = candidates[0]
                used.add(candidates[0])

        # Fill empty roles from remaining champions
        remaining = [c for c in champions if c not in used]
        random.shuffle(remaining)
        for role in ['TOP', 'JUNGLE', 'MID', 'BOT', 'SUPPORT']:
            if role not in comp and remaining:
                comp[role] = remaining.pop(0)

        result = [{'champion': v, 'role': k} for k, v in comp.items()]
        if label:
            for r in result:
                r['label'] = label
        return result

    def weekly_goals(self) -> list[dict]:
        """Suggest weekly challenge goals based on closest challenges."""
        roadmap = self.challenge_roadmap(top_n=5)
        goals = []

        for c in roadmap:
            if c['remaining'] <= 3:
                urgency = 'easy'
                suggestion = f"Just {int(c['remaining'])} more to reach {c['next_tier']}!"
            elif c['remaining'] <= 10:
                urgency = 'medium'
                suggestion = f"Focus on this -- {int(c['remaining'])} to {c['next_tier']}"
            else:
                urgency = 'long_term'
                suggestion = f"{int(c['remaining'])} remaining to {c['next_tier']}"

            goals.append({
                'challenge': c['name'],
                'description': c.get('description', ''),
                'urgency': urgency,
                'suggestion': suggestion,
                'remaining': c['remaining'],
                'next_tier': c['next_tier'],
                'progress_pct': c['progress_pct'],
            })

        return goals
