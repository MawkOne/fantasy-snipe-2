#!/usr/bin/env python3
"""
Demonstrate Player Impact Analysis Capabilities
Based on the Oilers Nation McDavid article analysis
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple

def create_mock_mcdavid_data() -> pd.DataFrame:
    """
    Create mock data to demonstrate the McDavid impact analysis
    Based on typical NHL performance patterns
    """
    data = {
        'season': ['2020-21', '2021-22', '2022-23', '2023-24', '2024-25'],
        'on_ice_goal_diff_60': [2.1, 2.8, 2.5, 2.9, 2.7],  # McDavid's on-ice performance
        'off_ice_expected_goal_diff_60': [-0.3, -0.1, 0.2, 0.1, 0.3],  # Expected team performance without him
        'off_ice_actual_goal_diff_60': [-0.8, -0.5, -0.2, -0.1, 0.1],  # Actual team performance without him
        'team_avg_goal_diff_60': [0.5, 0.8, 0.9, 1.2, 1.1],  # Team average
        'mcdavid_toi_per_game': [22.1, 22.3, 22.0, 21.8, 21.9],  # McDavid's ice time
        'games_played': [56, 80, 76, 76, 75]  # Games played
    }
    
    return pd.DataFrame(data)

def create_impact_visualization(df: pd.DataFrame) -> None:
    """
    Create a visualization similar to the Oilers Nation article
    """
    # Create the plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot 1: Team performance without McDavid (similar to article)
    seasons = df['season']
    
    ax1.bar([x - 0.2 for x in range(len(seasons))], df['off_ice_expected_goal_diff_60'], 
            alpha=0.7, color='orange', label='Expected Goal Diff (Off-Ice)', width=0.4)
    ax1.bar([x + 0.2 for x in range(len(seasons))], df['off_ice_actual_goal_diff_60'], 
            alpha=0.7, color='blue', label='Actual Goal Diff (Off-Ice)', width=0.4)
    
    ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax1.set_xlabel('Season')
    ax1.set_ylabel('Goal Differential per 60 Minutes')
    ax1.set_title('Edmonton Oilers - Performance Without McDavid On Ice\\nExpected vs Actual Goal Differential')
    ax1.set_xticks(range(len(seasons)))
    ax1.set_xticklabels(seasons)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for i, (exp, act) in enumerate(zip(df['off_ice_expected_goal_diff_60'], df['off_ice_actual_goal_diff_60'])):
        ax1.text(i - 0.2, exp + (0.1 if exp >= 0 else -0.1), f'{exp:.1f}', 
                ha='center', va='bottom' if exp >= 0 else 'top', fontsize=9)
        ax1.text(i + 0.2, act + (0.1 if act >= 0 else -0.1), f'{act:.1f}', 
                ha='center', va='bottom' if act >= 0 else 'top', fontsize=9)
    
    # Plot 2: McDavid's individual impact
    mcdavid_impact = df['on_ice_goal_diff_60'] - df['off_ice_actual_goal_diff_60']
    
    bars = ax2.bar(seasons, mcdavid_impact, 
                   alpha=0.7, color='purple', label="McDavid's Impact")
    
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax2.set_xlabel('Season')
    ax2.set_ylabel('Impact per 60 Minutes')
    ax2.set_title("Connor McDavid - Individual Impact Analysis")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Color bars based on positive/negative impact
    for i, bar in enumerate(bars):
        if mcdavid_impact.iloc[i] > 0:
            bar.set_color('green')
        else:
            bar.set_color('red')
    
    # Add value labels
    for i, impact in enumerate(mcdavid_impact):
        ax2.text(i, impact + (0.1 if impact >= 0 else -0.1), f'{impact:.1f}', 
                ha='center', va='bottom' if impact >= 0 else 'top', fontsize=9)
    
    plt.tight_layout()
    plt.show()

def demonstrate_analysis_capabilities() -> None:
    """
    Demonstrate what we can do with player impact analysis
    """
    print("=" * 80)
    print("PLAYER IMPACT ANALYSIS CAPABILITIES")
    print("=" * 80)
    print()
    print("Based on the Oilers Nation McDavid article analysis, we can replicate:")
    print()
    print("1. ON-ICE vs OFF-ICE GOAL DIFFERENTIAL ANALYSIS")
    print("   - Team performance when player is on ice")
    print("   - Team performance when player is off ice")
    print("   - Expected vs actual goal differential")
    print()
    print("2. PLAYER IMPACT METRICS")
    print("   - Individual player contribution to team success")
    print("   - Comparison with team average performance")
    print("   - Historical trend analysis")
    print()
    print("3. DATA REQUIREMENTS")
    print("   - Shift-level data (on-ice/off-ice events)")
    print("   - Team performance metrics")
    print("   - Player deployment patterns")
    print()
    print("4. AVAILABLE DATA IN OUR SYSTEM")
    print("   - Player shift metrics (player_shift_metrics table)")
    print("   - Game events (goals, shots, attempts)")
    print("   - Team performance data")
    print("   - Player deployment (TOI, strength states)")
    print()
    print("5. ANALYSIS FRAMEWORK")
    print("   - Calculate team performance with player on ice")
    print("   - Calculate team performance with player off ice")
    print("   - Compare expected vs actual performance")
    print("   - Identify player impact and value")
    print()

def create_elite_player_comparison() -> None:
    """
    Create a comparison of elite player impacts
    """
    # Mock data for elite players
    elite_data = {
        'player': ['McDavid', 'MacKinnon', 'Matthews', 'Draisaitl', 'Hughes'],
        'avg_impact_60': [2.9, 2.1, 1.8, 2.3, 1.9],
        'on_ice_goal_diff_60': [2.7, 2.2, 1.9, 2.1, 1.8],
        'off_ice_goal_diff_60': [-0.2, 0.1, 0.1, -0.2, -0.1]
    }
    
    df = pd.DataFrame(elite_data)
    
    # Create comparison visualization
    fig, ax = plt.subplots(figsize=(12, 8))
    
    x = np.arange(len(df['player']))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, df['on_ice_goal_diff_60'], width, 
                   label='On-Ice Goal Diff/60', alpha=0.7, color='green')
    bars2 = ax.bar(x + width/2, df['off_ice_goal_diff_60'], width, 
                   label='Off-Ice Goal Diff/60', alpha=0.7, color='red')
    
    ax.set_xlabel('Player')
    ax.set_ylabel('Goal Differential per 60 Minutes')
    ax.set_title('Elite Player Impact Comparison\\nOn-Ice vs Off-Ice Performance')
    ax.set_xticks(x)
    ax.set_xticklabels(df['player'])
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + (0.1 if height >= 0 else -0.1),
                   f'{height:.1f}', ha='center', va='bottom' if height >= 0 else 'top', fontsize=9)
    
    plt.tight_layout()
    plt.show()

def main():
    """
    Main function to demonstrate player impact analysis
    """
    print("CONNOR MCDAVID IMPACT ANALYSIS DEMONSTRATION")
    print("Replicating the Oilers Nation Article Analysis")
    print("=" * 80)
    
    # Demonstrate analysis capabilities
    demonstrate_analysis_capabilities()
    
    # Create mock data and visualization
    print("Creating McDavid Impact Analysis Visualization...")
    mcdavid_df = create_mock_mcdavid_data()
    create_impact_visualization(mcdavid_df)
    
    # Show the data
    print("\\nMcDavid Impact Data (Mock Data for Demonstration):")
    print("=" * 60)
    print(mcdavid_df.to_string(index=False))
    
    # Create elite player comparison
    print("\\nCreating Elite Player Impact Comparison...")
    create_elite_player_comparison()
    
    print("\\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print()
    print("This demonstration shows how we can replicate the Oilers Nation")
    print("McDavid analysis using our NHL data infrastructure.")
    print()
    print("Key Insights from the Analysis:")
    print("- McDavid has consistently positive impact on team performance")
    print("- Team performs worse without him on ice (negative off-ice goal diff)")
    print("- His impact has remained consistently high across seasons")
    print("- Elite players show similar patterns of positive team impact")
    print()
    print("With our shift-level data, we can perform this analysis for any player")
    print("and compare their impact across different teams and seasons.")

if __name__ == "__main__":
    main()
