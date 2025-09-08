#!/usr/bin/env python3
"""
Fantasy Hockey CausalBot Testing Script

This script tests the causal analysis system before building the UI.
It validates:
1. Data integration between NHL and Fantasy databases
2. Causal discovery algorithms
3. Weight optimization methods
4. HRM training preparation
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from database.connection import get_session
from database.fantasy_connection import get_fantasy_session
from database.models import Player, PlayerGameStats, Game, Team, PlayerGameAdvancedMetricsFlat
from database.fantasy_models_v2 import FantasyPlayer, FantasyTeam, FantasyLeague

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FantasyHockeyCausalBotTester:
    """Test suite for Fantasy Hockey CausalBot"""
    
    def __init__(self):
        self.nhl_session = None
        self.fantasy_session = None
        self.test_results = {}
        
    def setup_connections(self):
        """Establish database connections"""
        try:
            self.nhl_session = get_session()
            self.fantasy_session = get_fantasy_session()
            logger.info("✅ Database connections established")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to establish database connections: {e}")
            return False
    
    def test_data_availability(self) -> Dict:
        """Test 1: Check data availability and quality"""
        logger.info("🧪 Testing Data Availability...")
        
        results = {
            'nhl_data': {},
            'fantasy_data': {},
            'integration': {},
            'overall': 'PASS'
        }
        
        try:
            # Test NHL data
            nhl_players = self.nhl_session.query(Player).count()
            nhl_games = self.nhl_session.query(Game).count()
            nhl_stats = self.nhl_session.query(PlayerGameStats).count()
            nhl_advanced = self.nhl_session.query(PlayerGameAdvancedMetricsFlat).count()
            
            results['nhl_data'] = {
                'players': nhl_players,
                'games': nhl_games,
                'game_stats': nhl_stats,
                'advanced_metrics': nhl_advanced,
                'status': 'PASS' if nhl_players > 0 and nhl_games > 0 else 'FAIL'
            }
            
            # Test Fantasy data
            fantasy_players = self.fantasy_session.query(FantasyPlayer).count()
            fantasy_teams = self.fantasy_session.query(FantasyTeam).count()
            fantasy_leagues = self.fantasy_session.query(FantasyLeague).count()
            
            results['fantasy_data'] = {
                'players': fantasy_players,
                'teams': fantasy_teams,
                'leagues': fantasy_leagues,
                'status': 'PASS' if fantasy_players > 0 else 'FAIL'
            }
            
            # Test data integration
            integrated_players = self.fantasy_session.query(FantasyPlayer).filter(
                FantasyPlayer.nhl_player_id.isnot(None)
            ).count()
            
            results['integration'] = {
                'integrated_players': integrated_players,
                'integration_rate': integrated_players / max(fantasy_players, 1) * 100,
                'status': 'PASS' if integrated_players > 0 else 'FAIL'
            }
            
            # Overall status
            if any(r['status'] == 'FAIL' for r in [results['nhl_data'], results['fantasy_data'], results['integration']]):
                results['overall'] = 'FAIL'
            
            logger.info(f"✅ Data availability test completed: {results['overall']}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Data availability test failed: {e}")
            results['overall'] = 'FAIL'
            return results
    
    def test_causal_discovery_data_prep(self) -> Dict:
        """Test 2: Prepare data for causal discovery"""
        logger.info("🧪 Testing Causal Discovery Data Preparation...")
        
        try:
            # Get sample player data for testing
            sample_player = self.nhl_session.query(Player).filter(
                Player.position_code.in_(['C', 'LW', 'RW', 'D'])
            ).first()
            
            if not sample_player:
                logger.error("❌ No sample player found for testing")
                return {'status': 'FAIL', 'error': 'No sample player'}
            
            # Get player's game data
            player_games = self.nhl_session.query(PlayerGameStats).filter(
                PlayerGameStats.player_id == sample_player.id
            ).limit(50).all()
            
            # Get advanced metrics
            advanced_metrics = self.nhl_session.query(PlayerGameAdvancedMetricsFlat).filter(
                PlayerGameAdvancedMetricsFlat.player_id == sample_player.id
            ).limit(50).all()
            
            # Create feature matrix for causal analysis
            features = []
            for game in player_games:
                # Find corresponding advanced metrics
                adv_metric = next((m for m in advanced_metrics if m.game_id == game.game_id), None)
                
                feature_vector = {
                    'player_id': game.player_id,
                    'game_id': game.game_id,
                    'goals': game.goals,
                    'assists': game.assists,
                    'points': game.points,
                    'plus_minus': game.plus_minus,
                    'shots': game.shots,
                    'pim': game.pim,
                    'power_play_points': game.power_play_points,
                    'time_on_ice_minutes': self._parse_toi(game.toi) if game.toi else 0,
                    'shifts': game.shifts,
                    # Advanced metrics
                    'corsi_for': adv_metric.CF if adv_metric else 0,
                    'corsi_against': adv_metric.CA if adv_metric else 0,
                    'corsi_percentage': adv_metric.CF_pct if adv_metric else 0,
                    'fenwick_for': adv_metric.FF if adv_metric else 0,
                    'fenwick_against': adv_metric.FA if adv_metric else 0,
                    'fenwick_percentage': adv_metric.FF_pct if adv_metric else 0,
                    'shots_for': adv_metric.SF if adv_metric else 0,
                    'shots_against': adv_metric.SA if adv_metric else 0,
                    'goals_for': adv_metric.GF if adv_metric else 0,
                    'goals_against': adv_metric.GA if adv_metric else 0,
                    'pdo': adv_metric.PDO if adv_metric else 0,
                    'toi_seconds': adv_metric.TOI_seconds if adv_metric else 0,
                }
                features.append(feature_vector)
            
            # Convert to DataFrame
            df = pd.DataFrame(features)
            
            # Calculate fantasy points (example scoring system)
            df['fantasy_points'] = (
                df['goals'] * 3 +
                df['assists'] * 2 +
                df['plus_minus'] * 1 +
                df['shots'] * 0.1 +
                df['power_play_points'] * 1
            )
            
            results = {
                'status': 'PASS',
                'sample_player': sample_player.full_name,
                'games_analyzed': len(df),
                'features_created': len(df.columns),
                'fantasy_points_range': (df['fantasy_points'].min(), df['fantasy_points'].max()),
                'data_quality': {
                    'missing_values': df.isnull().sum().sum(),
                    'completeness': (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
                }
            }
            
            logger.info(f"✅ Causal discovery data prep completed: {results['status']}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Causal discovery data prep failed: {e}")
            return {'status': 'FAIL', 'error': str(e)}
    
    def test_causal_factor_identification(self, sample_data: pd.DataFrame) -> Dict:
        """Test 3: Identify potential causal factors"""
        logger.info("🧪 Testing Causal Factor Identification...")
        
        try:
            # Define potential causal factors
            causal_factors = {
                'offensive_factors': ['goals', 'assists', 'points', 'shots', 'power_play_points'],
                'possession_factors': ['corsi_for', 'corsi_against', 'corsi_percentage', 'fenwick_percentage'],
                'time_factors': ['time_on_ice_minutes', 'shifts', 'toi_seconds'],
                'defensive_factors': ['plus_minus', 'goals_against', 'shots_against'],
                'efficiency_factors': ['pdo', 'fenwick_percentage']
            }
            
            # Calculate correlations with fantasy points
            correlations = {}
            for category, factors in causal_factors.items():
                category_correlations = {}
                for factor in factors:
                    if factor in sample_data.columns:
                        corr = sample_data[factor].corr(sample_data['fantasy_points'])
                        category_correlations[factor] = corr
                correlations[category] = category_correlations
            
            # Identify top causal factors
            all_correlations = {}
            for category_corrs in correlations.values():
                all_correlations.update(category_corrs)
            
            top_factors = sorted(all_correlations.items(), key=lambda x: abs(x[1]), reverse=True)[:10]
            
            results = {
                'status': 'PASS',
                'causal_factors_identified': len(all_correlations),
                'top_factors': top_factors,
                'factor_categories': list(causal_factors.keys()),
                'correlation_analysis': correlations
            }
            
            logger.info(f"✅ Causal factor identification completed: {results['status']}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Causal factor identification failed: {e}")
            return {'status': 'FAIL', 'error': str(e)}
    
    def test_weight_optimization_simulation(self, sample_data: pd.DataFrame, top_factors: List[Tuple]) -> Dict:
        """Test 4: Simulate weight optimization"""
        logger.info("🧪 Testing Weight Optimization Simulation...")
        
        try:
            # Extract top factor names
            factor_names = [factor[0] for factor in top_factors[:5]]
            
            # Create feature matrix
            X = sample_data[factor_names].fillna(0)
            y = sample_data['fantasy_points']
            
            # Simulate weight optimization using linear regression
            from sklearn.linear_model import LinearRegression
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import r2_score, mean_squared_error
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
            
            # Fit model
            model = LinearRegression()
            model.fit(X_train, y_train)
            
            # Predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            r2 = r2_score(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            
            # Get feature importance (coefficients)
            feature_importance = dict(zip(factor_names, model.coef_))
            
            # Normalize weights to sum to 1
            total_weight = sum(abs(w) for w in model.coef_)
            normalized_weights = {factor: abs(weight) / total_weight for factor, weight in feature_importance.items()}
            
            results = {
                'status': 'PASS',
                'model_performance': {
                    'r2_score': r2,
                    'rmse': rmse,
                    'prediction_accuracy': 'GOOD' if r2 > 0.6 else 'FAIR' if r2 > 0.4 else 'POOR'
                },
                'optimized_weights': normalized_weights,
                'feature_importance': feature_importance,
                'factors_used': factor_names,
                'training_samples': len(X_train),
                'testing_samples': len(X_test)
            }
            
            logger.info(f"✅ Weight optimization simulation completed: {results['status']}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Weight optimization simulation failed: {e}")
            return {'status': 'FAIL', 'error': str(e)}
    
    def test_hrm_training_preparation(self, optimized_weights: Dict, sample_data: pd.DataFrame) -> Dict:
        """Test 5: Prepare data for HRM training"""
        logger.info("🧪 Testing HRM Training Preparation...")
        
        try:
            # Create decision scenarios for HRM training
            decision_scenarios = []
            
            # Sample different game scenarios
            for _, game in sample_data.iterrows():
                # Create draft decision scenario
                draft_scenario = {
                    'scenario_type': 'draft',
                    'player_id': game['player_id'],
                    'available_players': ['player_a', 'player_b', 'player_c'],
                    'causal_factors': {factor: game[factor] for factor in optimized_weights.keys() if factor in game},
                    'optimal_weights': optimized_weights,
                    'recommended_action': 'draft' if game['fantasy_points'] > sample_data['fantasy_points'].median() else 'pass',
                    'confidence': min(abs(game['fantasy_points'] - sample_data['fantasy_points'].mean()) / sample_data['fantasy_points'].std(), 1.0)
                }
                
                # Create lineup decision scenario
                lineup_scenario = {
                    'scenario_type': 'lineup',
                    'player_id': game['player_id'],
                    'current_roster': ['player_1', 'player_2', 'player_3'],
                    'causal_factors': {factor: game[factor] for factor in optimized_weights.keys() if factor in game},
                    'optimal_weights': optimized_weights,
                    'recommended_action': 'start' if game['fantasy_points'] > sample_data['fantasy_points'].quantile(0.7) else 'bench',
                    'confidence': min(abs(game['fantasy_points'] - sample_data['fantasy_points'].mean()) / sample_data['fantasy_points'].std(), 1.0)
                }
                
                decision_scenarios.extend([draft_scenario, lineup_scenario])
            
            # Calculate training metrics
            total_scenarios = len(decision_scenarios)
            draft_scenarios = len([s for s in decision_scenarios if s['scenario_type'] == 'draft'])
            lineup_scenarios = len([s for s in decision_scenarios if s['scenario_type'] == 'lineup'])
            
            avg_confidence = np.mean([s['confidence'] for s in decision_scenarios])
            
            results = {
                'status': 'PASS',
                'training_scenarios_created': total_scenarios,
                'scenario_breakdown': {
                    'draft_scenarios': draft_scenarios,
                    'lineup_scenarios': lineup_scenarios
                },
                'training_quality': {
                    'average_confidence': avg_confidence,
                    'confidence_distribution': {
                        'high': len([s for s in decision_scenarios if s['confidence'] > 0.7]),
                        'medium': len([s for s in decision_scenarios if 0.4 <= s['confidence'] <= 0.7]),
                        'low': len([s for s in decision_scenarios if s['confidence'] < 0.4])
                    }
                },
                'hrm_ready': total_scenarios > 100 and avg_confidence > 0.5
            }
            
            logger.info(f"✅ HRM training preparation completed: {results['status']}")
            return results
            
        except Exception as e:
            logger.error(f"❌ HRM training preparation failed: {e}")
            return {'status': 'FAIL', 'error': str(e)}
    
    def generate_test_report(self) -> Dict:
        """Generate comprehensive test report"""
        logger.info("📊 Generating Test Report...")
        
        report = {
            'test_timestamp': datetime.now().isoformat(),
            'overall_status': 'PASS',
            'test_results': self.test_results,
            'recommendations': [],
            'next_steps': []
        }
        
        # Check overall status
        failed_tests = [name for name, result in self.test_results.items() if result.get('status') == 'FAIL']
        if failed_tests:
            report['overall_status'] = 'FAIL'
            report['recommendations'].append(f"Fix failed tests: {', '.join(failed_tests)}")
        
        # Generate recommendations
        if self.test_results.get('data_availability', {}).get('overall') == 'PASS':
            report['recommendations'].append("✅ Data integration is ready for causal analysis")
        
        if self.test_results.get('causal_discovery', {}).get('status') == 'PASS':
            report['recommendations'].append("✅ Causal discovery pipeline is functional")
        
        if self.test_results.get('weight_optimization', {}).get('status') == 'PASS':
            report['recommendations'].append("✅ Weight optimization is working correctly")
        
        if self.test_results.get('hrm_preparation', {}).get('status') == 'PASS':
            report['recommendations'].append("✅ HRM training data is ready")
        
        # Next steps
        if report['overall_status'] == 'PASS':
            report['next_steps'].extend([
                "🚀 Proceed with UI development",
                "🎯 Implement real-time causal analysis",
                "🤖 Begin HRM model training",
                "📊 Create visualization components"
            ])
        else:
            report['next_steps'].extend([
                "🔧 Fix identified issues",
                "📊 Improve data quality",
                "🧪 Re-run tests after fixes"
            ])
        
        return report
    
    def _parse_toi(self, toi_str: str) -> float:
        """Parse time on ice string to minutes"""
        if not toi_str:
            return 0.0
        try:
            parts = toi_str.split(':')
            minutes = int(parts[0])
            seconds = int(parts[1])
            return minutes + seconds / 60.0
        except:
            return 0.0
    
    def run_all_tests(self) -> Dict:
        """Run complete test suite"""
        logger.info("🧪 Starting Fantasy Hockey CausalBot Test Suite...")
        
        # Test 1: Data availability
        self.test_results['data_availability'] = self.test_data_availability()
        
        if self.test_results['data_availability']['overall'] == 'FAIL':
            logger.error("❌ Data availability test failed. Stopping tests.")
            return self.generate_test_report()
        
        # Test 2: Causal discovery data preparation
        self.test_results['causal_discovery'] = self.test_causal_discovery_data_prep()
        
        if self.test_results['causal_discovery']['status'] == 'FAIL':
            logger.error("❌ Causal discovery test failed. Stopping tests.")
            return self.generate_test_report()
        
        # Get sample data for remaining tests
        sample_data = self._get_sample_data()
        
        # Test 3: Causal factor identification
        self.test_results['factor_identification'] = self.test_causal_factor_identification(sample_data)
        
        # Test 4: Weight optimization
        top_factors = self.test_results['factor_identification'].get('top_factors', [])
        self.test_results['weight_optimization'] = self.test_weight_optimization_simulation(sample_data, top_factors)
        
        # Test 5: HRM preparation
        optimized_weights = self.test_results['weight_optimization'].get('optimized_weights', {})
        self.test_results['hrm_preparation'] = self.test_hrm_training_preparation(optimized_weights, sample_data)
        
        # Generate final report
        return self.generate_test_report()
    
    def _get_sample_data(self) -> pd.DataFrame:
        """Get sample data for testing"""
        # This would be populated from the causal discovery test
        # For now, return empty DataFrame
        return pd.DataFrame()

def main():
    """Main test execution"""
    print("🏒 Fantasy Hockey CausalBot Test Suite")
    print("=" * 50)
    
    tester = FantasyHockeyCausalBotTester()
    
    # Setup connections
    if not tester.setup_connections():
        print("❌ Failed to setup database connections")
        return
    
    # Run all tests
    report = tester.run_all_tests()
    
    # Print results
    print(f"\n📊 Test Results: {report['overall_status']}")
    print("=" * 50)
    
    for test_name, result in report['test_results'].items():
        status = result.get('status', 'UNKNOWN')
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n💡 Recommendations:")
    for rec in report['recommendations']:
        print(f"  {rec}")
    
    print(f"\n🚀 Next Steps:")
    for step in report['next_steps']:
        print(f"  {step}")
    
    print(f"\n📅 Test completed at: {report['test_timestamp']}")

if __name__ == "__main__":
    main() 