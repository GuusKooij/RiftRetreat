"""Rank prediction based on player stats compared to rank averages."""

from typing import Dict, List, Any, Optional


# Average stats per rank (based on League of Legends community data 2026)
# Format: {rank: {stat: value}}
# Sources: OP.GG, LeagueOfGraphs, community benchmarks
# Updated: February 2026
# NOTE: These are cross-role averages. Actual performance varies significantly by role.
# For example: Support CS/min is naturally lower, ADC CS/min should be higher.
RANK_AVERAGES = {
    'Iron': {
        'kda': 1.5,  # Iron players average ~1.5 KDA
        'cs_per_min': 3.2,  # ~3-4 CS/min typical for Iron
        'vision_score_per_min': 0.4,  # Minimal warding
        'damage_per_min': 280,  # Lower damage output
        'gold_per_min': 240,  # ~14-15k gold per game
        'kill_participation': 38.0,  # stored as percentage
    },
    'Bronze': {
        'kda': 1.8,  # Bronze ~1.8 KDA
        'cs_per_min': 3.8,  # ~4 CS/min benchmark
        'vision_score_per_min': 0.6,
        'damage_per_min': 340,
        'gold_per_min': 270,  # ~16k gold per game
        'kill_participation': 42.0,
    },
    'Silver': {
        'kda': 2.2,  # Silver average rank, ~2.2 KDA
        'cs_per_min': 4.5,  # ~4.5-5 CS/min
        'vision_score_per_min': 0.8,
        'damage_per_min': 400,
        'gold_per_min': 300,  # ~18k gold per game
        'kill_participation': 46.0,
    },
    'Gold': {
        'kda': 2.6,  # Gold ~2.6 KDA
        'cs_per_min': 5.2,  # ~5-6 CS/min
        'vision_score_per_min': 1.0,
        'damage_per_min': 470,
        'gold_per_min': 330,  # ~20k gold per game
        'kill_participation': 50.0,
    },
    'Platinum': {
        'kda': 2.9,  # Plat ~2.9 KDA
        'cs_per_min': 5.8,  # ~6 CS/min, approaching 8 CS/min goal
        'vision_score_per_min': 1.2,
        'damage_per_min': 530,
        'gold_per_min': 360,  # ~22k gold per game
        'kill_participation': 53.0,
    },
    'Emerald': {
        'kda': 3.2,  # Emerald ~3.2 KDA
        'cs_per_min': 6.5,  # ~6.5-7 CS/min, close to 8 CS/min benchmark
        'vision_score_per_min': 1.4,
        'damage_per_min': 590,
        'gold_per_min': 390,  # ~23k gold per game
        'kill_participation': 56.0,
    },
    'Diamond': {
        'kda': 3.5,  # Diamond ~3.5 KDA
        'cs_per_min': 7.2,  # ~7-8 CS/min
        'vision_score_per_min': 1.6,
        'damage_per_min': 650,
        'gold_per_min': 420,  # ~25k gold per game
        'kill_participation': 59.0,
    },
    'Master+': {
        'kda': 4.0,  # Master+ ~4.0+ KDA
        'cs_per_min': 8.0,  # 8+ CS/min standard
        'vision_score_per_min': 1.9,
        'damage_per_min': 720,
        'gold_per_min': 460,  # ~27k+ gold per game
        'kill_participation': 62.0,
    },
}

RANK_ORDER = ['Iron', 'Bronze', 'Silver', 'Gold', 'Platinum', 'Emerald', 'Diamond', 'Master+']


class RankPredictor:
    """Predicts player rank based on performance stats."""

    def __init__(self, matches: List[Dict[str, Any]], current_rank: Optional[str] = None):
        """Initialize with player match data and optional current rank."""
        self.matches = matches
        self.current_rank = current_rank  # Player's actual ranked tier (e.g., "GOLD", "EMERALD")
        self.MIN_GAMES_PER_ROLE = 5  # Minimum games needed to show role prediction

    def calculate_player_averages_by_role(self) -> Dict[str, Dict[str, float]]:
        """Calculate player's average stats grouped by role."""
        if not self.matches:
            return {}

        role_stats = {}
        role_matches = {}

        for match in self.matches:
            role = match.get('role', match.get('individual_position', 'UNKNOWN'))

            # Normalize role names
            role_map = {
                'BOTTOM': 'BOT',
                'UTILITY': 'SUPPORT',
                'MIDDLE': 'MID',
                'TOP': 'TOP',
                'JUNGLE': 'JUNGLE',
            }
            role = role_map.get(role, role)

            if role not in role_matches:
                role_matches[role] = []
            role_matches[role].append(match)

        # Calculate averages per role
        for role, matches in role_matches.items():
            if len(matches) < self.MIN_GAMES_PER_ROLE:
                continue  # Skip roles with too few games

            total_kills = 0
            total_deaths = 0
            total_assists = 0
            total_cs = 0
            total_game_duration = 0
            total_vision_score = 0
            total_damage = 0
            total_gold = 0
            total_kp = 0

            for match in matches:
                kills = match.get('kills', 0)
                deaths = match.get('deaths', 0)
                assists = match.get('assists', 0)
                duration_min = match.get('game_duration_min', match.get('game_duration', 0) / 60 if match.get('game_duration') else 0)

                total_kills += kills
                total_deaths += max(deaths, 1)
                total_assists += assists
                total_cs += match.get('cs', match.get('total_minions_killed', 0))
                total_game_duration += duration_min
                total_vision_score += match.get('vision_score', 0)
                total_damage += match.get('total_damage_dealt', 0)
                total_gold += match.get('gold_earned', 0)
                total_kp += match.get('kp', match.get('kill_participation', match.get('challenges', {}).get('killParticipation', 0)))

            num_games = len(matches)

            role_stats[role] = {
                'games': num_games,
                'kda': (total_kills + total_assists) / total_deaths if total_deaths > 0 else 0,
                'cs_per_min': total_cs / total_game_duration if total_game_duration > 0 else 0,
                'vision_score_per_min': total_vision_score / total_game_duration if total_game_duration > 0 else 0,
                'damage_per_min': total_damage / total_game_duration if total_game_duration > 0 else 0,
                'gold_per_min': total_gold / total_game_duration if total_game_duration > 0 else 0,
                'kill_participation': total_kp / num_games if num_games > 0 else 0,
            }

        return role_stats

    def calculate_player_averages(self) -> Dict[str, float]:
        """Calculate player's average stats across all matches."""
        if not self.matches:
            return {}

        total_kills = 0
        total_deaths = 0
        total_assists = 0
        total_cs = 0
        total_game_duration = 0
        total_vision_score = 0
        total_damage = 0
        total_gold = 0
        total_kp = 0

        for match in self.matches:
            kills = match.get('kills', 0)
            deaths = match.get('deaths', 0)
            assists = match.get('assists', 0)
            duration_min = match.get('game_duration_min', match.get('game_duration', 0) / 60 if match.get('game_duration') else 0)

            total_kills += kills
            total_deaths += max(deaths, 1)  # Count for KDA calc, min 1 to avoid div by zero
            total_assists += assists
            total_cs += match.get('cs', match.get('total_minions_killed', 0))
            total_game_duration += duration_min
            total_vision_score += match.get('vision_score', 0)
            total_damage += match.get('total_damage_dealt', 0)
            total_gold += match.get('gold_earned', 0)
            total_kp += match.get('kp', match.get('kill_participation', match.get('challenges', {}).get('killParticipation', 0)))

        num_games = len(self.matches)

        return {
            'kda': (total_kills + total_assists) / total_deaths if total_deaths > 0 else 0,
            'cs_per_min': total_cs / total_game_duration if total_game_duration > 0 else 0,
            'vision_score_per_min': total_vision_score / total_game_duration if total_game_duration > 0 else 0,
            'damage_per_min': total_damage / total_game_duration if total_game_duration > 0 else 0,
            'gold_per_min': total_gold / total_game_duration if total_game_duration > 0 else 0,
            'kill_participation': total_kp / num_games if num_games > 0 else 0,
        }

    def predict_rank_for_stat(self, stat_name: str, stat_value: float) -> str:
        """Predict rank for a single stat.

        NEW LOGIC (context-aware):
        - If current_rank is provided, anchor predictions to that rank
        - Compare player's stat to their current rank's average
        - Only predict higher/lower if significantly different from current rank

        OLD LOGIC (absolute comparison):
        - Compare to all ranks from Iron upward
        - Return highest rank where stat exceeds average
        """
        if stat_value is None or stat_value == 0:
            return 'Unknown'

        # Context-aware prediction: anchor to current rank
        if self.current_rank:
            current_normalized = self.current_rank.upper().capitalize()

            if current_normalized in RANK_ORDER:
                current_idx = RANK_ORDER.index(current_normalized)
                current_avg = RANK_AVERAGES[current_normalized].get(stat_name, 0)

                if current_avg == 0:
                    # Fallback to absolute comparison if stat not available
                    return self._absolute_rank_prediction(stat_name, stat_value)

                # Calculate percentage difference from current rank average
                diff_pct = ((stat_value - current_avg) / current_avg) * 100

                # Define thresholds for rank changes (more forgiving)
                # Need to significantly outperform to predict higher rank
                UPGRADE_THRESHOLD = 12.0  # +12% above current rank average
                DOWNGRADE_THRESHOLD = -12.0  # -12% below current rank average

                if diff_pct >= UPGRADE_THRESHOLD:
                    # Significantly above current rank - check how far
                    # Look upward through ranks to find best fit
                    for i in range(current_idx + 1, len(RANK_ORDER)):
                        next_rank = RANK_ORDER[i]
                        next_avg = RANK_AVERAGES[next_rank].get(stat_name, 0)

                        if next_avg == 0:
                            continue

                        # If stat is close to or exceeds next rank average, keep checking
                        if stat_value >= next_avg * 0.92:  # Within 8% of next rank
                            continue
                        else:
                            # Found the rank we can't quite reach - previous one is prediction
                            return RANK_ORDER[i - 1] if i > 0 else next_rank

                    # If we made it through all ranks, return highest
                    return RANK_ORDER[-1]

                elif diff_pct <= DOWNGRADE_THRESHOLD:
                    # Significantly below current rank - check how far
                    # Look downward through ranks to find best fit
                    for i in range(current_idx - 1, -1, -1):
                        lower_rank = RANK_ORDER[i]
                        lower_avg = RANK_AVERAGES[lower_rank].get(stat_name, 0)

                        if lower_avg == 0:
                            continue

                        # If stat is above lower rank average, that's our prediction
                        if stat_value >= lower_avg:
                            return lower_rank

                    # If below all ranks, return Iron
                    return 'Iron'
                else:
                    # Within threshold of current rank - return current rank
                    return current_normalized

        # No current rank provided - use absolute comparison (old logic)
        return self._absolute_rank_prediction(stat_name, stat_value)

    def _absolute_rank_prediction(self, stat_name: str, stat_value: float) -> str:
        """Absolute rank prediction: find highest rank where stat exceeds average."""
        predicted_rank = 'Iron'
        for rank in RANK_ORDER:
            rank_avg = RANK_AVERAGES[rank].get(stat_name, 0)
            if stat_value >= rank_avg:
                predicted_rank = rank
            else:
                break
        return predicted_rank

    def get_rank_predictions_by_role(self) -> Dict[str, Any]:
        """Get rank predictions for each role separately (min 5 games per role).

        Returns:
            Dict containing:
            - role_predictions: Dict mapping role name to predicted rank
            - role_stats: Dict mapping role to stats dict
            - best_role: Role with highest predicted rank
            - role_games: Number of games per role
        """
        role_stats = self.calculate_player_averages_by_role()

        if not role_stats:
            return {
                'role_predictions': {},
                'role_stats': {},
                'best_role': None,
                'role_games': {},
            }

        role_predictions = {}
        role_games = {}

        # Role-specific stat weights (what matters most for each role)
        role_specific_weights = {
            'TOP': {
                'kda': 2.0,
                'cs_per_min': 1.8,  # Farming very important
                'damage_per_min': 1.6,
                'gold_per_min': 1.5,
                'kill_participation': 0.8,
                'vision_score_per_min': 0.8,  # Less important for top
            },
            'JUNGLE': {
                'kda': 1.8,
                'kill_participation': 2.2,  # Map presence critical
                'vision_score_per_min': 1.8,  # Vision control key
                'gold_per_min': 1.4,
                'damage_per_min': 1.2,
                'cs_per_min': 0.7,  # Less CS due to camp farming
            },
            'MID': {
                'kda': 2.0,
                'damage_per_min': 1.9,  # Damage dealers
                'cs_per_min': 1.7,
                'gold_per_min': 1.6,
                'kill_participation': 1.5,
                'vision_score_per_min': 1.0,
            },
            'BOT': {
                'kda': 1.9,
                'cs_per_min': 2.2,  # Most CS-dependent role
                'damage_per_min': 2.0,  # Primary damage dealer
                'gold_per_min': 1.8,
                'kill_participation': 1.2,
                'vision_score_per_min': 0.6,  # Least important
            },
            'SUPPORT': {
                'kda': 1.5,  # Deaths less punishing
                'vision_score_per_min': 2.5,  # Most important stat
                'kill_participation': 2.0,  # Roaming/assisting key
                'gold_per_min': 0.8,  # Low income expected
                'damage_per_min': 0.7,
                'cs_per_min': 0.3,  # Almost irrelevant
            },
        }

        for role, stats in role_stats.items():
            role_games[role] = stats.pop('games', 0)

            # Get role-specific weights, fallback to default if role not found
            stat_weights = role_specific_weights.get(role, {
                'kda': 2.0,
                'damage_per_min': 1.5,
                'gold_per_min': 1.5,
                'kill_participation': 1.3,
                'vision_score_per_min': 1.2,
                'cs_per_min': 1.0,
            })

            weighted_rank_sum = 0.0
            total_weight = 0.0

            for stat_name, stat_value in stats.items():
                # Skip stats that are 0 or very low (e.g., CS/min < 1.0 for supports)
                if stat_value == 0 or (stat_name == 'cs_per_min' and stat_value < 1.0):
                    continue

                predicted_rank = self.predict_rank_for_stat(stat_name, stat_value)

                if predicted_rank in RANK_ORDER:
                    rank_idx = RANK_ORDER.index(predicted_rank)
                    weight = stat_weights.get(stat_name, 1.0)
                    weighted_rank_sum += rank_idx * weight
                    total_weight += weight

            # Overall prediction for this role using weighted average
            if total_weight > 0:
                avg_rank_idx = int(round(weighted_rank_sum / total_weight))
                avg_rank_idx = max(0, min(avg_rank_idx, len(RANK_ORDER) - 1))
                role_predictions[role] = RANK_ORDER[avg_rank_idx]
            else:
                role_predictions[role] = 'Unknown'

        # Find best role
        best_role = None
        best_rank_idx = -1
        for role, rank in role_predictions.items():
            if rank in RANK_ORDER:
                rank_idx = RANK_ORDER.index(rank)
                if rank_idx > best_rank_idx:
                    best_rank_idx = rank_idx
                    best_role = role

        return {
            'role_predictions': role_predictions,
            'role_stats': role_stats,
            'best_role': best_role,
            'role_games': role_games,
        }

    def get_rank_prediction(self) -> Dict[str, Any]:
        """Get comprehensive rank prediction analysis.

        Returns:
            Dict containing:
            - player_stats: Dict of player's average stats
            - stat_predictions: Dict mapping stat name to predicted rank
            - overall_prediction: Most common predicted rank
            - rank_breakdown: Count of predictions per rank
            - insights: List of notable insights
            - role_predictions: Dict mapping role to predicted rank (NEW)
        """
        player_stats = self.calculate_player_averages()

        if not player_stats:
            return {
                'player_stats': {},
                'stat_predictions': {},
                'overall_prediction': 'Unknown',
                'rank_breakdown': {},
                'insights': ['Not enough data to make prediction'],
                'role_predictions': {},
            }

        # Predict rank for each stat
        stat_predictions = {}
        rank_counts = {rank: 0 for rank in RANK_ORDER}
        rank_counts['Unknown'] = 0  # Add Unknown to handle cases with no data

        for stat_name, stat_value in player_stats.items():
            # Skip stats that are 0 or very low (likely incomplete data)
            if stat_value == 0 or (stat_name == 'cs_per_min' and stat_value < 1.0):
                continue

            predicted_rank = self.predict_rank_for_stat(stat_name, stat_value)
            stat_predictions[stat_name] = predicted_rank
            if predicted_rank != 'Unknown':
                rank_counts[predicted_rank] += 1

        # Overall prediction: weighted average of rank indices
        # Weight important stats more (KDA, Gold/min, Damage/min > CS/min for support)
        stat_weights = {
            'kda': 2.0,
            'damage_per_min': 1.5,
            'gold_per_min': 1.5,
            'kill_participation': 1.3,
            'vision_score_per_min': 1.2,
            'cs_per_min': 1.0,  # Lower weight since not all roles farm
        }

        weighted_rank_sum = 0.0
        total_weight = 0.0

        for stat_name, predicted_rank in stat_predictions.items():
            if predicted_rank in RANK_ORDER:
                rank_idx = RANK_ORDER.index(predicted_rank)
                weight = stat_weights.get(stat_name, 1.0)
                weighted_rank_sum += rank_idx * weight
                total_weight += weight

        if total_weight > 0:
            avg_rank_idx = int(round(weighted_rank_sum / total_weight))
            avg_rank_idx = max(0, min(avg_rank_idx, len(RANK_ORDER) - 1))
            overall_prediction = RANK_ORDER[avg_rank_idx]
        else:
            overall_prediction = 'Unknown'

        # Generate insights
        insights = self._generate_insights(stat_predictions, player_stats, overall_prediction)

        # Get per-role predictions
        role_data = self.get_rank_predictions_by_role()

        return {
            'player_stats': player_stats,
            'stat_predictions': stat_predictions,
            'overall_prediction': overall_prediction,
            'rank_breakdown': rank_counts,
            'insights': insights,
            'role_predictions': role_data.get('role_predictions', {}),
            'role_games': role_data.get('role_games', {}),
            'best_role': role_data.get('best_role'),
        }

    def _generate_insights(self, stat_predictions: Dict[str, str],
                          player_stats: Dict[str, float],
                          overall_prediction: str) -> List[str]:
        """Generate human-readable insights from predictions."""
        insights = []

        # Handle Unknown overall prediction
        if overall_prediction == 'Unknown':
            return ['Not enough data to generate insights']

        # Find strengths (stats above overall prediction)
        strengths = []
        weaknesses = []

        overall_rank_idx = RANK_ORDER.index(overall_prediction)

        for stat_name, predicted_rank in stat_predictions.items():
            if predicted_rank == 'Unknown':
                continue  # Skip stats with unknown rank

            predicted_rank_idx = RANK_ORDER.index(predicted_rank)

            if predicted_rank_idx > overall_rank_idx:
                # This stat is better than overall
                stat_display = self._format_stat_name(stat_name)
                strengths.append(f"{stat_display} ({predicted_rank})")
            elif predicted_rank_idx < overall_rank_idx:
                # This stat is worse than overall
                stat_display = self._format_stat_name(stat_name)
                weaknesses.append(f"{stat_display} ({predicted_rank})")

        if strengths:
            insights.append(f"✨ Strengths: {', '.join(strengths)}")

        if weaknesses:
            insights.append(f"⚠️ Areas to improve: {', '.join(weaknesses)}")

        # Specific stat callouts
        kda_rank = stat_predictions.get('kda', 'Unknown')
        cs_rank = stat_predictions.get('cs_per_min', 'Unknown')
        vision_rank = stat_predictions.get('vision_score_per_min', 'Unknown')

        if (kda_rank != 'Unknown' and cs_rank != 'Unknown' and
            kda_rank != cs_rank and abs(RANK_ORDER.index(kda_rank) - RANK_ORDER.index(cs_rank)) >= 2):
            insights.append(f"📊 You fight like {kda_rank} but farm like {cs_rank}")

        if vision_rank == 'Iron' or vision_rank == 'Bronze':
            insights.append("👁️ Your vision control needs significant improvement!")

        # Overall assessment with current rank comparison
        if self.current_rank:
            # Normalize current rank to match prediction format
            current_normalized = self.current_rank.upper().capitalize()

            if current_normalized in RANK_ORDER and overall_prediction in RANK_ORDER:
                current_idx = RANK_ORDER.index(current_normalized)
                predicted_idx = RANK_ORDER.index(overall_prediction)

                if predicted_idx > current_idx + 1:  # 2+ ranks above
                    insights.append(f"🚀 You're {current_normalized} but performing like {overall_prediction}! You should climb soon!")
                elif predicted_idx > current_idx:  # 1 rank above
                    insights.append(f"📈 You're {current_normalized} but stats show {overall_prediction} level - keep it up!")
                elif predicted_idx < current_idx - 1:  # 2+ ranks below
                    insights.append(f"⚠️ You're {current_normalized} but stats suggest {overall_prediction} - focus on consistency!")
                elif predicted_idx < current_idx:  # 1 rank below
                    insights.append(f"🎯 You're {current_normalized}, stats show {overall_prediction} - room for improvement!")
                else:
                    insights.append(f"✅ You're {current_normalized} and playing at that level - consistent performance!")
            else:
                # Fallback if rank format doesn't match
                if overall_prediction in ['Diamond', 'Master+']:
                    insights.append(f"🏆 Your stats suggest you're performing at {overall_prediction} level!")
                elif overall_prediction in ['Platinum', 'Emerald']:
                    insights.append(f"💎 You're playing at {overall_prediction} level - keep climbing!")
                elif overall_prediction in ['Gold', 'Silver']:
                    insights.append(f"📈 You're playing at {overall_prediction} level - room to grow!")
                else:
                    insights.append(f"🎯 Focus on fundamentals to climb from {overall_prediction}")
        else:
            # No current rank provided
            if overall_prediction in ['Diamond', 'Master+']:
                insights.append(f"🏆 Your stats suggest you're performing at {overall_prediction} level!")
            elif overall_prediction in ['Platinum', 'Emerald']:
                insights.append(f"💎 You're playing at {overall_prediction} level - keep climbing!")
            elif overall_prediction in ['Gold', 'Silver']:
                insights.append(f"📈 You're playing at {overall_prediction} level - room to grow!")
            else:
                insights.append(f"🎯 Focus on fundamentals to climb from {overall_prediction}")

        return insights

    def _format_stat_name(self, stat_name: str) -> str:
        """Format stat names for display."""
        name_map = {
            'kda': 'KDA',
            'cs_per_min': 'CS/min',
            'vision_score_per_min': 'Vision',
            'damage_per_min': 'Damage',
            'gold_per_min': 'Gold',
            'kill_participation': 'Kill Participation',
        }
        return name_map.get(stat_name, stat_name)

    def compare_to_rank(self, target_rank: str) -> Dict[str, Any]:
        """Compare player stats to a specific rank's averages.

        Args:
            target_rank: Rank to compare against

        Returns:
            Dict with stat comparisons and percentage differences
        """
        if target_rank not in RANK_AVERAGES:
            return {}

        player_stats = self.calculate_player_averages()
        target_stats = RANK_AVERAGES[target_rank]

        comparisons = {}
        for stat_name, player_value in player_stats.items():
            target_value = target_stats.get(stat_name, 0)
            if target_value > 0:
                diff_pct = ((player_value - target_value) / target_value) * 100
                comparisons[stat_name] = {
                    'player': player_value,
                    'target': target_value,
                    'diff_pct': round(diff_pct, 1),
                    'meets_target': player_value >= target_value,
                }

        return comparisons
