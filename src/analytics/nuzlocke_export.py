"""Nuzlocke run export to HTML."""

import os
from datetime import datetime
from typing import Dict, Any


class NuzlockeExporter:
    """Export Nuzlocke run data to HTML format."""

    def __init__(self, run_stats: Dict[str, Any]):
        """Initialize with run statistics dict."""
        self.stats = run_stats

    def export_to_html(self, output_path: str) -> str:
        """Generate a styled HTML report of the run.

        Args:
            output_path: Path to save HTML file

        Returns:
            Path to generated HTML file
        """
        html = self._generate_html()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return output_path

    def _generate_html(self) -> str:
        """Generate HTML content for the run."""
        started = self.stats['started'][:10]
        ended = self.stats.get('ended', 'Active')[:10] if self.stats.get('ended') else 'Active'
        status = "✓ Completed" if not self.stats['active'] else "● Active"

        wr = 0
        if self.stats['total_games'] > 0:
            wr = round(self.stats['total_wins'] / self.stats['total_games'] * 100)

        # Calculate impressive stats
        has_resurrections = len(self.stats.get('resurrections', [])) > 0
        survived_count = self.stats['survived_count']
        eliminated_count = self.stats['eliminated_count']
        total_games = self.stats['total_games']
        total_wins = self.stats['total_wins']

        # Generate highlights section
        highlights = []
        if wr >= 60:
            highlights.append(f"🔥 Dominant {wr}% Win Rate!")
        if wr >= 70:
            highlights.append(f"⚡ Incredible {wr}% Win Rate!")
        if survived_count >= 20:
            highlights.append(f"💪 {survived_count} Champions Survived!")
        if survived_count >= 50:
            highlights.append(f"🏆 Legendary {survived_count} Champions Survived!")
        if total_wins >= 50:
            highlights.append(f"✨ {total_wins} Total Victories!")
        if total_wins >= 100:
            highlights.append(f"👑 Century Club: {total_wins} Wins!")
        if has_resurrections:
            res_count = len(self.stats.get('resurrections', []))
            highlights.append(f"🎰 {res_count} Clutch Resurrection{'s' if res_count > 1 else ''}!")

        # Look for winning streak in history
        max_streak = 0
        if self.stats['history']:
            current_streak = 0
            for game in reversed(self.stats['history']):
                if game['win']:
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 0
            if max_streak >= 5:
                highlights.append(f"🔥 {max_streak} Game Win Streak!")

        # Quick elimination stats
        if eliminated_count > 0 and total_games > 0:
            elimination_rate = round((eliminated_count / total_games) * 100)
            if elimination_rate <= 10:
                highlights.append(f"🛡️ Only {elimination_rate}% Elimination Rate!")

        highlights_html = ""
        if highlights:
            highlight_items = "".join([f"<div class='highlight-item'>{h}</div>" for h in highlights])
            highlights_html = f"""
            <div class="highlights-section">
                <h2>🎯 Highlights</h2>
                <div class="highlights-grid">
                    {highlight_items}
                </div>
            </div>
            """

        # Generate survived list
        survived_html = ""
        if self.stats['survived']:
            survived_items = "".join([f"<li>{c}</li>" for c in sorted(self.stats['survived'])])
            survived_html = f"""
            <div class="section">
                <h2>✅ Survived Champions ({self.stats['survived_count']})</h2>
                <ul class="champion-list survived">{survived_items}</ul>
            </div>
            """

        # Generate eliminated list
        eliminated_html = ""
        if self.stats['eliminated']:
            eliminated_items = "".join([f"<li>💀 {c}</li>" for c in sorted(self.stats['eliminated'])])
            eliminated_html = f"""
            <div class="section">
                <h2>💀 Eliminated Champions ({self.stats['eliminated_count']})</h2>
                <ul class="champion-list eliminated">{eliminated_items}</ul>
            </div>
            """

        # Generate resurrection list
        resurrection_html = ""
        if self.stats.get('resurrections'):
            res_items = "".join([
                f"<li>🎰 <b>{r['champion']}</b> <span class='date'>({r['date']})</span></li>"
                for r in self.stats['resurrections']
            ])
            resurrection_html = f"""
            <div class="section resurrection-section">
                <h2>🎰 Resurrections Used ({self.stats['tokens_used']}/{self.stats.get('tokens_earned', 0)})</h2>
                <ul class="champion-list resurrection">{res_items}</ul>
            </div>
            """

        # Generate match history
        history_html = ""
        if self.stats['history']:
            history_rows = ""
            for h in reversed(self.stats['history'][-20:]):
                result = "W" if h['win'] else "L"
                result_class = "win" if h['win'] else "loss"
                status_text = "SURVIVED" if h['win'] else "ELIMINATED"
                history_rows += f"""
                <tr>
                    <td class="result {result_class}">{result}</td>
                    <td>{h['champion']}</td>
                    <td class="{result_class}">{status_text}</td>
                    <td class="date">{h.get('date', '')}</td>
                </tr>
                """

            history_html = f"""
            <div class="section">
                <h2>Recent Match History</h2>
                <table class="history-table">
                    <thead>
                        <tr>
                            <th>Result</th>
                            <th>Champion</th>
                            <th>Status</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {history_rows}
                    </tbody>
                </table>
            </div>
            """

        # Generate best champions
        best_html = ""
        if self.stats.get('best_champs'):
            best_rows = ""
            for champ, stats in self.stats['best_champs']:
                games = stats['games']
                wins = stats['wins']
                champ_wr = round(wins / games * 100) if games > 0 else 0
                best_rows += f"""
                <tr>
                    <td>{champ}</td>
                    <td>{games}</td>
                    <td>{wins}</td>
                    <td>{champ_wr}%</td>
                </tr>
                """

            best_html = f"""
            <div class="section">
                <h2>Top Performing Champions</h2>
                <table class="stats-table">
                    <thead>
                        <tr>
                            <th>Champion</th>
                            <th>Games</th>
                            <th>Wins</th>
                            <th>Win Rate</th>
                        </tr>
                    </thead>
                    <tbody>
                        {best_rows}
                    </tbody>
                </table>
            </div>
            """

        # Token info
        token_html = ""
        if 'tokens_remaining' in self.stats:
            next_token_wins = 10 - (self.stats['total_wins'] % 10) if self.stats['total_wins'] else 10
            token_html = f"""
            <div class="stat-box">
                <div class="stat-label">Resurrection Tokens ({next_token_wins} wins to next)</div>
                <div class="stat-value">{self.stats['tokens_remaining']}</div>
            </div>
            """

        # Generate social summary
        social_summary = f"🎮 {total_wins} Wins | {survived_count} Survived | {wr}% Win Rate"
        if max_streak >= 5:
            social_summary += f" | 🔥 {max_streak} Win Streak"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nuzlocke Run #{self.stats['id']} - LoL Companion</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #0A1428 0%, #1E2328 50%, #0F2027 100%);
            color: #E4E4E4;
            padding: 40px 20px;
            line-height: 1.6;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(30, 35, 40, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 48px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(200, 155, 60, 0.1);
            border: 1px solid rgba(60, 60, 65, 0.5);
        }}

        h1 {{
            color: #C89B3C;
            text-align: center;
            font-size: 42px;
            font-weight: 700;
            margin-bottom: 12px;
            text-shadow: 0 3px 8px rgba(200, 155, 60, 0.4), 0 0 20px rgba(200, 155, 60, 0.2);
            letter-spacing: 1px;
        }}

        .subtitle {{
            text-align: center;
            color: #A89968;
            font-size: 20px;
            font-weight: 500;
            margin-bottom: 48px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .stat-box {{
            background: linear-gradient(135deg, rgba(10, 20, 40, 0.9) 0%, rgba(20, 28, 38, 0.7) 100%);
            border: 2px solid rgba(60, 60, 65, 0.6);
            border-radius: 12px;
            padding: 24px 20px;
            text-align: center;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }}

        .stat-box:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
        }}

        .stat-label {{
            color: #5B5A56;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}

        .stat-value {{
            color: #F0F0F0;
            font-size: 42px;
            font-weight: 700;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            line-height: 1.1;
        }}

        .stat-value.green {{
            color: #00E676;
            text-shadow: 0 0 16px rgba(0, 230, 118, 0.5), 0 2px 4px rgba(0, 0, 0, 0.3);
        }}
        .stat-value.red {{
            color: #FF1744;
            text-shadow: 0 0 16px rgba(255, 23, 68, 0.5), 0 2px 4px rgba(0, 0, 0, 0.3);
        }}
        .stat-value.gold {{
            color: #E6B84E;
            text-shadow: 0 0 16px rgba(230, 184, 78, 0.5), 0 2px 4px rgba(0, 0, 0, 0.3);
        }}

        .section {{
            margin: 48px 0;
            padding: 32px;
            background: linear-gradient(135deg, rgba(10, 20, 40, 0.6) 0%, rgba(15, 25, 35, 0.4) 100%);
            border-radius: 12px;
            border: 1px solid rgba(60, 60, 65, 0.5);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        }}

        h2 {{
            color: #0AC8B9;
            font-size: 30px;
            font-weight: 700;
            margin-bottom: 24px;
            border-bottom: 3px solid rgba(10, 200, 185, 0.4);
            padding-bottom: 12px;
            text-shadow: 0 2px 10px rgba(10, 200, 185, 0.3);
            letter-spacing: 0.5px;
        }}

        .champion-list {{
            list-style: none;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 10px;
        }}

        .champion-list li {{
            padding: 10px 16px;
            background: rgba(30, 35, 40, 0.6);
            border-radius: 6px;
            border-left: 4px solid #3C3C41;
            font-weight: 500;
            transition: all 0.2s ease;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
        }}

        .champion-list li:hover {{
            transform: translateX(4px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        }}

        .champion-list.survived li {{
            border-left-color: #00E676;
            background: rgba(0, 230, 118, 0.08);
            color: #00E676;
            font-weight: 600;
        }}

        .champion-list.survived li:hover {{
            background: rgba(0, 230, 118, 0.15);
            border-left-width: 6px;
        }}

        .champion-list.eliminated li {{
            border-left-color: #FF1744;
            background: rgba(255, 23, 68, 0.08);
            text-decoration: line-through;
            opacity: 0.7;
            color: #FF6B6B;
        }}

        .champion-list.eliminated li:hover {{
            opacity: 0.9;
            background: rgba(255, 23, 68, 0.12);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}

        th {{
            background: linear-gradient(135deg, rgba(10, 20, 40, 0.9) 0%, rgba(15, 25, 35, 0.7) 100%);
            color: #C89B3C;
            padding: 16px 12px;
            text-align: left;
            font-weight: 700;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 1px;
            border-bottom: 3px solid rgba(200, 155, 60, 0.3);
        }}

        td {{
            padding: 14px 12px;
            border-bottom: 1px solid rgba(60, 60, 65, 0.4);
            background: rgba(0, 0, 0, 0.1);
        }}

        tr:nth-child(even) td {{
            background: rgba(0, 0, 0, 0.2);
        }}

        tr:hover td {{
            background: rgba(10, 200, 185, 0.08);
            transition: background 0.2s ease;
        }}

        .result {{
            font-weight: 700;
            font-size: 20px;
            text-align: center;
            width: 40px;
            height: 40px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
        }}

        .result.win {{
            color: #00E676;
            background: rgba(0, 230, 118, 0.15);
            text-shadow: 0 0 8px rgba(0, 230, 118, 0.3);
        }}
        .result.loss {{
            color: #FF1744;
            background: rgba(255, 23, 68, 0.15);
            text-shadow: 0 0 8px rgba(255, 23, 68, 0.3);
        }}

        .date {{
            color: #5B5A56;
            font-size: 12px;
        }}

        .header-banner {{
            background: linear-gradient(135deg, rgba(200, 155, 60, 0.15) 0%, rgba(10, 200, 185, 0.1) 100%);
            border: 2px solid rgba(200, 155, 60, 0.3);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 40px;
            text-align: center;
        }}

        .header-banner .emoji {{
            font-size: 48px;
            margin-bottom: 12px;
        }}

        .highlights-section {{
            background: linear-gradient(135deg, rgba(200, 155, 60, 0.2) 0%, rgba(10, 200, 185, 0.15) 100%);
            border: 2px solid rgba(200, 155, 60, 0.4);
            border-radius: 12px;
            padding: 32px;
            margin-bottom: 40px;
        }}

        .highlights-section h2 {{
            color: #E6B84E;
            font-size: 28px;
            margin-bottom: 24px;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 2px;
            text-shadow: 0 2px 12px rgba(230, 184, 78, 0.4);
        }}

        .highlights-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
        }}

        .highlight-item {{
            background: linear-gradient(135deg, rgba(0, 230, 118, 0.1) 0%, rgba(10, 200, 185, 0.1) 100%);
            border: 2px solid rgba(0, 230, 118, 0.3);
            border-radius: 10px;
            padding: 20px 24px;
            font-size: 18px;
            font-weight: 700;
            color: #00E676;
            text-align: center;
            text-shadow: 0 2px 10px rgba(0, 230, 118, 0.3);
            transition: all 0.3s ease;
            animation: glow 2s ease-in-out infinite;
        }}

        @keyframes glow {{
            0%, 100% {{ box-shadow: 0 0 15px rgba(0, 230, 118, 0.3); }}
            50% {{ box-shadow: 0 0 25px rgba(0, 230, 118, 0.5); }}
        }}

        .highlight-item:hover {{
            transform: translateY(-4px);
            border-color: rgba(0, 230, 118, 0.6);
            box-shadow: 0 8px 30px rgba(0, 230, 118, 0.4);
        }}

        .resurrection-section {{
            background: linear-gradient(135deg, rgba(138, 43, 226, 0.1) 0%, rgba(75, 0, 130, 0.1) 100%);
            border: 2px solid rgba(138, 43, 226, 0.3);
            border-radius: 12px;
            padding: 24px;
        }}

        .resurrection-section h2 {{
            color: #DA70D6;
            text-shadow: 0 2px 10px rgba(218, 112, 214, 0.3);
        }}

        .resurrection {{
            color: #DA70D6;
        }}

        .footer {{
            text-align: center;
            margin-top: 80px;
            padding-top: 32px;
            border-top: 2px solid rgba(60, 60, 65, 0.4);
            color: #7B7B7B;
            font-size: 13px;
        }}

        .footer a {{
            color: #C89B3C;
            text-decoration: none;
            transition: color 0.2s ease;
        }}

        .footer a:hover {{
            color: #E6B84E;
        }}

        @media print {{
            body {{
                background: white;
                color: black;
            }}
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header-banner">
            <div class="emoji">🏆⚔️🎮</div>
            <h1>LoL Nuzlocke Challenge</h1>
            <div class="subtitle">Run #{self.stats['id']} — {status}</div>
            <div class="subtitle" style="margin-top: 12px; font-size: 16px; color: #00E676;">{social_summary}</div>
        </div>

        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-label">Started</div>
                <div class="stat-value">{started}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Ended</div>
                <div class="stat-value">{ended}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Total Games</div>
                <div class="stat-value">{self.stats['total_games']}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Total Wins</div>
                <div class="stat-value green">{self.stats['total_wins']}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Win Rate</div>
                <div class="stat-value {'green' if wr >= 50 else 'red'}">{wr}%</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Survived</div>
                <div class="stat-value gold">{self.stats['survived_count']}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Eliminated</div>
                <div class="stat-value red">{self.stats['eliminated_count']}</div>
            </div>
            {token_html}
        </div>

        {highlights_html}
        {resurrection_html}
        {best_html}
        {survived_html}
        {eliminated_html}
        {history_html}

        <div class="footer">
            © RiftRetreat | Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>"""

        return html
