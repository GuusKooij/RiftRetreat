"""
CoachingReportGenerator: Identifies top improvement areas, off-meta assessment,
tilt assessment, vision assessment, and champion pool assessment.
Exportable as HTML.
"""

import os
from collections import defaultdict
from datetime import datetime

from src.analytics.rank_predictor import RANK_AVERAGES, RANK_ORDER


class CoachingReportGenerator:
    def __init__(self, matches, stats_analyzer, tilt_detector, champion_analyzer,
                 current_rank=None, data_dragon=None):
        self.matches = matches
        self.stats = stats_analyzer
        self.tilt = tilt_detector
        self.champ_analyzer = champion_analyzer
        self.current_rank = current_rank or 'Gold'
        self.dd = data_dragon

    def _get_rank_averages(self) -> dict:
        """Get averages for current rank."""
        return RANK_AVERAGES.get(self.current_rank.capitalize(), RANK_AVERAGES.get('Gold', {}))

    def get_improvement_areas(self, top_n: int = 5) -> list[dict]:
        """Stats where player underperforms vs rank average, with recommendations."""
        if not self.matches:
            return []

        rank_avg = self._get_rank_averages()
        overall = self.stats.overall()

        # Map stat names to readable names and calculate diffs
        stat_mapping = [
            ('cs_per_min', 'avg_cs_per_min', 'CS/min', False),
            ('vision_score_per_min', None, 'Vision/min', False),  # Need to compute
            ('kill_participation', 'avg_kp', 'Kill Participation', False),
            ('damage_per_min', None, 'Damage/min', False),  # Need to compute
            ('kda', 'avg_kda', 'KDA', False),
        ]

        # Compute additional stats
        avg_duration = sum(m['game_duration_min'] for m in self.matches) / max(len(self.matches), 1)
        vision_per_min = overall['avg_vision_score'] / max(avg_duration, 1)
        damage_per_min = overall['avg_damage'] / max(avg_duration, 1)

        improvements = []

        for rank_key, overall_key, display_name, lower_better in stat_mapping:
            rank_val = rank_avg.get(rank_key, 0)
            if not rank_val:
                continue

            if overall_key:
                player_val = overall.get(overall_key, 0)
            elif rank_key == 'vision_score_per_min':
                player_val = vision_per_min
            elif rank_key == 'damage_per_min':
                player_val = damage_per_min
            else:
                continue

            # Calculate gap as percentage
            gap_pct = round((player_val - rank_val) / max(rank_val, 0.1) * 100, 1)

            # Only show areas below rank average
            if gap_pct >= 0:
                continue

            recommendation = self._get_recommendation(rank_key, gap_pct, player_val, rank_val)

            improvements.append({
                'stat': display_name,
                'player_value': round(player_val, 1),
                'rank_average': round(rank_val, 1),
                'gap_percent': gap_pct,
                'recommendation': recommendation,
                'priority': abs(gap_pct),
            })

        improvements.sort(key=lambda x: x['priority'], reverse=True)
        return improvements[:top_n]

    def _get_recommendation(self, stat_key: str, gap_pct: float, player_val: float, rank_val: float) -> str:
        """Generate specific recommendation for a stat gap."""
        recommendations = {
            'cs_per_min': f"Practice last-hitting in Practice Tool. Aim for {rank_val:.1f} CS/min. "
                         f"Focus on not missing cannon minions and catching side waves.",
            'vision_score_per_min': f"Place more wards! Buy Control Wards on every back. "
                                    f"Target: {rank_val:.1f} vision/min.",
            'kill_participation': f"Roam more and join team fights. Your KP is {player_val:.0f}% vs "
                                 f"the {self.current_rank} average of {rank_val:.0f}%. "
                                 f"Look at the map every 5 seconds.",
            'damage_per_min': f"Trade more aggressively in lane and participate in fights. "
                             f"Your damage output is {abs(gap_pct):.0f}% below {self.current_rank} average.",
            'kda': f"Focus on dying less. Each death gives the enemy gold and map pressure. "
                  f"Your KDA is {player_val:.1f} vs {self.current_rank} average of {rank_val:.1f}.",
        }
        return recommendations.get(stat_key, f"This stat is {abs(gap_pct):.0f}% below {self.current_rank} average.")

    def get_off_meta_index(self) -> dict:
        """Calculate what % of games are on sub-50% WR champions."""
        if not self.matches:
            return {'index': 0, 'off_meta_games': 0, 'total_games': 0, 'assessment': ''}

        pool = self.champ_analyzer.champion_pool()
        champ_wr = {c['champion']: c['winrate'] for c in pool if c['games'] >= 3}

        off_meta = 0
        total_with_data = 0
        for m in self.matches:
            wr = champ_wr.get(m['champion'])
            if wr is not None:
                total_with_data += 1
                if wr < 48:
                    off_meta += 1

        index = round(off_meta / max(total_with_data, 1) * 100, 1)

        if index <= 10:
            assessment = "Sticking to your strengths - great discipline!"
        elif index <= 25:
            assessment = "Moderate off-meta play - consider focusing on your best picks"
        else:
            assessment = "High off-meta play - you'd climb faster sticking to your best champions"

        return {
            'index': index,
            'off_meta_games': off_meta,
            'total_games': total_with_data,
            'assessment': assessment,
        }

    def get_tilt_assessment(self) -> dict:
        """Assess tilt patterns from match data."""
        if not self.tilt:
            return {}

        sessions = self.tilt.detect_sessions()
        all_streaks = self.tilt.detect_streaks()
        streaks = [s for s in all_streaks if s['type'] == 'loss']
        time_analysis = self.tilt.time_of_day_analysis()

        worst_session_len = 0
        avg_session_len = 0
        if sessions:
            session_lengths = [s['games'] for s in sessions]
            worst_session_len = max(session_lengths)
            avg_session_len = round(sum(session_lengths) / len(session_lengths), 1)

        # Find best and worst hours
        best_hour = None
        worst_hour = None
        if time_analysis:
            hour_data = [(h['hour'], h['winrate'], h['games']) for h in time_analysis if h['games'] >= 3]
            if hour_data:
                best = max(hour_data, key=lambda x: x[1])
                worst = min(hour_data, key=lambda x: x[1])
                best_hour = f"{best[0]}:00 ({best[1]}% WR, {best[2]} games)"
                worst_hour = f"{worst[0]}:00 ({worst[1]}% WR, {worst[2]} games)"

        assessment = []
        if len(streaks) > 3:
            assessment.append(f"You've had {len(streaks)} losing streaks of 3+ games. Consider taking breaks.")
        if worst_session_len > 8:
            assessment.append(f"Your longest session was {worst_session_len} games. Shorter sessions may improve focus.")
        if avg_session_len > 5:
            assessment.append(f"Average session length: {avg_session_len} games. Consider capping at 4-5.")

        return {
            'losing_streaks': len(streaks),
            'worst_session_length': worst_session_len,
            'avg_session_length': avg_session_len,
            'total_sessions': len(sessions),
            'best_time': best_hour,
            'worst_time': worst_hour,
            'tips': assessment,
        }

    def get_champion_pool_assessment(self) -> dict:
        """Assess champion pool diversity and one-trick risk."""
        pool = self.champ_analyzer.champion_pool()
        total_games = len(self.matches)

        if not pool or not total_games:
            return {}

        # Top champion share
        top_champ = pool[0]
        top_share = round(top_champ['games'] / total_games * 100, 1)

        # Champions with 5+ games
        main_champs = [c for c in pool if c['games'] >= 5]
        avg_wr = round(sum(c['winrate'] for c in main_champs) / max(len(main_champs), 1), 1) if main_champs else 0

        # Assessment
        if top_share > 50:
            diversity = "One-trick"
            advice = "Consider adding 1-2 backup picks for when your main is banned."
        elif top_share > 30:
            diversity = "Focused"
            advice = "Good focus! Make sure you have at least one backup per role."
        elif len(main_champs) > 8:
            diversity = "Wide"
            advice = "You play many champions. Consider narrowing to your top 3-4 for faster climbing."
        else:
            diversity = "Balanced"
            advice = "Healthy champion pool size for climbing."

        return {
            'unique_champions': len(pool),
            'main_champions': len(main_champs),
            'top_champion': top_champ['champion'],
            'top_champion_share': top_share,
            'avg_main_winrate': avg_wr,
            'diversity': diversity,
            'advice': advice,
        }

    def get_vision_assessment(self) -> dict:
        """Assess vision performance vs rank average."""
        if not self.matches:
            return {}

        rank_avg = self._get_rank_averages()
        overall = self.stats.overall()
        avg_duration = sum(m['game_duration_min'] for m in self.matches) / max(len(self.matches), 1)

        vision_per_min = overall['avg_vision_score'] / max(avg_duration, 1)
        rank_vision = rank_avg.get('vision_score_per_min', 1.0)

        gap = round((vision_per_min - rank_vision) / max(rank_vision, 0.1) * 100, 1)

        avg_wards = round(sum(m['wards_placed'] for m in self.matches) / max(len(self.matches), 1), 1)
        avg_control = round(sum(m['control_wards'] for m in self.matches) / max(len(self.matches), 1), 1)
        avg_killed = round(sum(m['wards_killed'] for m in self.matches) / max(len(self.matches), 1), 1)

        tips = []
        if vision_per_min < rank_vision:
            tips.append(f"Your vision/min ({vision_per_min:.2f}) is below {self.current_rank} average ({rank_vision:.2f})")
        if avg_control < 1.5:
            tips.append(f"Buy more Control Wards (avg: {avg_control:.1f}/game)")
        if avg_killed < 2:
            tips.append(f"Destroy more enemy wards (avg: {avg_killed:.1f}/game)")

        return {
            'vision_per_min': round(vision_per_min, 2),
            'rank_average': rank_vision,
            'gap_percent': gap,
            'avg_wards_placed': avg_wards,
            'avg_control_wards': avg_control,
            'avg_wards_killed': avg_killed,
            'tips': tips,
        }

    def export_html(self, output_path: str = None) -> str:
        """Export coaching report as styled HTML."""
        if output_path is None:
            from config import DATA_DIR
            output_path = os.path.join(DATA_DIR, 'coaching_report.html')

        improvements = self.get_improvement_areas()
        off_meta = self.get_off_meta_index()
        tilt = self.get_tilt_assessment()
        vision = self.get_vision_assessment()
        champ_pool = self.get_champion_pool_assessment()

        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>RiftRetreat Coaching Report</title>
<style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #0A0A0F; color: #CDDCFE; margin: 0; padding: 40px; }}
    .container {{ max-width: 800px; margin: 0 auto; }}
    h1 {{ color: #C8AA6E; font-size: 28px; }}
    h2 {{ color: #C8AA6E; font-size: 20px; margin-top: 30px; }}
    .card {{ background: #1A1B26; border: 1px solid #2A2B3D; border-radius: 8px; padding: 20px; margin: 15px 0; }}
    .good {{ color: #00C853; }}
    .bad {{ color: #E84057; }}
    .warn {{ color: #FF9800; }}
    .dim {{ color: #7B818C; }}
    .stat-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #2A2B3D; }}
    .footer {{ text-align: center; margin-top: 40px; color: #7B818C; font-size: 12px; }}
</style>
</head>
<body>
<div class="container">
    <h1>RiftRetreat Coaching Report</h1>
    <p class="dim">Generated {datetime.now().strftime('%B %d, %Y')} | Current Rank: {self.current_rank}</p>

    <h2>Top Improvement Areas</h2>
    <div class="card">
"""
        if improvements:
            for imp in improvements:
                html += f"""
        <div class="stat-row">
            <div>
                <strong>{imp['stat']}</strong><br>
                <span class="dim">{imp['recommendation']}</span>
            </div>
            <div style="text-align: right;">
                <span class="bad">{imp['player_value']}</span> vs <span class="good">{imp['rank_average']}</span><br>
                <span class="bad">{imp['gap_percent']:+.0f}%</span>
            </div>
        </div>"""
        else:
            html += '<p class="good">No major weaknesses detected! You\'re performing at or above your rank.</p>'

        html += f"""
    </div>

    <h2>Off-Meta Index</h2>
    <div class="card">
        <p>Off-Meta Games: <strong>{off_meta['off_meta_games']}</strong> / {off_meta['total_games']} ({off_meta['index']}%)</p>
        <p class="{'warn' if off_meta['index'] > 25 else 'good'}">{off_meta['assessment']}</p>
    </div>

    <h2>Champion Pool</h2>
    <div class="card">
        <p>Diversity: <strong>{champ_pool.get('diversity', 'N/A')}</strong></p>
        <p>Unique Champions: {champ_pool.get('unique_champions', 0)} | Main Champions (5+ games): {champ_pool.get('main_champions', 0)}</p>
        <p>Top Champion: <strong>{champ_pool.get('top_champion', 'N/A')}</strong> ({champ_pool.get('top_champion_share', 0)}% of games)</p>
        <p>{champ_pool.get('advice', '')}</p>
    </div>

    <h2>Vision</h2>
    <div class="card">
        <p>Vision/min: <strong>{vision.get('vision_per_min', 0)}</strong> (Rank avg: {vision.get('rank_average', 0)})</p>
        <p>Wards Placed: {vision.get('avg_wards_placed', 0)}/game | Control Wards: {vision.get('avg_control_wards', 0)}/game | Wards Killed: {vision.get('avg_wards_killed', 0)}/game</p>
"""
        for tip in vision.get('tips', []):
            html += f'<p class="warn">{tip}</p>\n'

        html += f"""
    </div>

    <h2>Tilt Assessment</h2>
    <div class="card">
        <p>Losing Streaks (3+): <strong>{tilt.get('losing_streaks', 0)}</strong></p>
        <p>Average Session: <strong>{tilt.get('avg_session_length', 0)}</strong> games | Longest: {tilt.get('worst_session_length', 0)} games</p>
"""
        if tilt.get('best_time'):
            html += f'<p class="good">Best Time: {tilt["best_time"]}</p>\n'
        if tilt.get('worst_time'):
            html += f'<p class="bad">Worst Time: {tilt["worst_time"]}</p>\n'
        for tip in tilt.get('tips', []):
            html += f'<p class="warn">{tip}</p>\n'

        html += """
    </div>

    <div class="footer">
        <p>RiftRetreat Coaching Report &copy; 2026</p>
    </div>
</div>
</body>
</html>"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return output_path
