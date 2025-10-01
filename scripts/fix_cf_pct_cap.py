#!/usr/bin/env python3

from google.cloud import bigquery

def fix_cf_pct_cap():
    """Fix CF% values that exceed 100% by capping them at 100%"""
    
    client = bigquery.Client()
    
    print("="*60)
    print("FIXING CF% VALUES OVER 100%")
    print("="*60)
    
    # First, let's see how many players have CF% > 100%
    count_query = """
    SELECT 
        COUNT(*) as players_over_100_cf,
        COUNT(CASE WHEN cf_pct_weighted > 100 THEN 1 END) as cf_over_100,
        COUNT(CASE WHEN cf_pct_weighted > 150 THEN 1 END) as cf_over_150,
        MAX(cf_pct_weighted) as max_cf_pct
    FROM `fantasy-snipe-ai.nhl_processed.player_season_totals`
    WHERE season = 20242025 AND game_type = 2
    """
    
    count_results = client.query(count_query).to_dataframe()
    print("CF% Data Quality Issues:")
    print(f"  Total players: {count_results['players_over_100_cf'].iloc[0]}")
    print(f"  CF% > 100%: {count_results['cf_over_100'].iloc[0]}")
    print(f"  CF% > 150%: {count_results['cf_over_150'].iloc[0]}")
    print(f"  Max CF%: {count_results['max_cf_pct'].iloc[0]:.2f}%")
    
    # Create a corrected view with CF% capped at 100%
    print("\nCreating corrected view with CF% capped at 100%...")
    
    corrected_view_query = """
    CREATE OR REPLACE VIEW `fantasy-snipe-ai.nhl_processed.player_season_totals_corrected` AS
    SELECT 
        * EXCEPT(cf_pct_weighted),
        LEAST(cf_pct_weighted, 100.0) as cf_pct_weighted
    FROM `fantasy-snipe-ai.nhl_processed.player_season_totals`
    """
    
    client.query(corrected_view_query).result()
    print("✅ Created corrected view with CF% capped at 100%")
    
    # Now recalculate team strength with corrected CF%
    print("\nRecalculating team strength with corrected CF%...")
    
    team_strength_query = """
    WITH team_performance AS (
        SELECT 
            t.tri_code as team,
            ROUND((AVG(LEAST(pst.cf_pct_weighted, 100.0)) * 0.3 + AVG(pst.gf60) * 0.4 + AVG(CASE WHEN pst.toi_minutes / pst.games_played >= 18 THEN pst.toi_minutes / pst.games_played END) * 0.3), 1) as team_strength,
            AVG(LEAST(pst.cf_pct_weighted, 100.0)) as avg_cf_pct_corrected,
            AVG(pst.gf60) as avg_gf60,
            AVG(CASE WHEN pst.toi_minutes / pst.games_played >= 18 THEN pst.toi_minutes / pst.games_played END) as avg_core_toi,
            COUNT(CASE WHEN pst.toi_minutes / pst.games_played >= 18 THEN 1 END) as core_players
        FROM `fantasy-snipe-ai.nhl_processed.player_season_totals` pst 
        JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON pst.team_id = t.id 
        JOIN `fantasy-snipe-ai.nhl_raw.players` p ON pst.player_id = p.player_id 
        WHERE pst.season = 20242025 
        AND pst.game_type = 2 
        AND pst.games_played >= 20 
        AND p.position != "G"
        GROUP BY t.tri_code
    )
    SELECT 
        team,
        team_strength,
        avg_cf_pct_corrected,
        avg_gf60,
        avg_core_toi,
        core_players,
        CASE 
            WHEN team_strength >= 40 THEN "Win Now"
            WHEN team_strength >= 37 THEN "Window Closing" 
            WHEN team_strength >= 34 THEN "Window Soon"
            ELSE "Rebuilding"
        END as cycle_stage
    FROM team_performance
    WHERE team IN ('SJS', 'CHI', 'EDM', 'COL', 'DAL', 'FLA')
    ORDER BY team_strength DESC
    """
    
    corrected_results = client.query(team_strength_query).to_dataframe()
    
    print("\nCorrected Team Strength Analysis:")
    print("Team | Strength | CF% (Corrected) | GF/60 | Core TOI | Core Players | Stage")
    print("-" * 80)
    for _, row in corrected_results.iterrows():
        print(f"{row.team:4} | {row.team_strength:8} | {row.avg_cf_pct_corrected:13.1f} | {row.avg_gf60:5.1f} | {row.avg_core_toi:8.1f} | {row.core_players:12} | {row.cycle_stage}")
    
    # Show the impact on SJS vs CHI
    sjs_row = corrected_results[corrected_results['team'] == 'SJS'].iloc[0]
    chi_row = corrected_results[corrected_results['team'] == 'CHI'].iloc[0]
    
    print(f"\nSJS vs CHI Comparison:")
    print(f"  SJS: {sjs_row.team_strength} strength ({sjs_row.cycle_stage}) - CF%: {sjs_row.avg_cf_pct_corrected:.1f}%")
    print(f"  CHI: {chi_row.team_strength} strength ({chi_row.cycle_stage}) - CF%: {chi_row.avg_cf_pct_corrected:.1f}%")
    
    if sjs_row.team_strength > chi_row.team_strength:
        print(f"  ✅ SJS is still stronger than CHI by {sjs_row.team_strength - chi_row.team_strength:.1f} points")
    else:
        print(f"  ✅ CHI is now stronger than SJS by {chi_row.team_strength - sjs_row.team_strength:.1f} points")
    
    print(f"\n✅ CF% correction complete! Use the corrected view for future analysis.")

if __name__ == "__main__":
    fix_cf_pct_cap()
