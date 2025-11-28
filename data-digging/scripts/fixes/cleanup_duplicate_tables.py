#!/usr/bin/env python3

from google.cloud import bigquery

def cleanup_duplicate_tables():
    client = bigquery.Client()
    
    print('Cleaning up duplicate and previous version tables...')
    
    tables_to_delete = [
        'fantasy-snipe-ai.nhl_processed.player_individual_scoring_corrected',
        'fantasy-snipe-ai.nhl_processed.player_season_totals',
        'fantasy-snipe-ai.nhl_projections.current_player_forecasts_final',
        'fantasy-snipe-ai.nhl_projections.current_player_forecasts_corrected',
        'fantasy-snipe-ai.nhl_projections.current_player_forecasts_complete',
        'fantasy-snipe-ai.nhl_projections.current_player_forecasts_clean',
        'fantasy-snipe-ai.nhl_projections.current_player_forecasts_fixed',
        'fantasy-snipe-ai.nhl_projections.current_player_forecasts',
        'fantasy-snipe-ai.nhl_projections.current_player_forecasts_final_fixed',
        'fantasy-snipe-ai.nhl_projections.current_player_forecasts_final_corrected',
        'fantasy-snipe-ai.nhl_projections.current_player_forecasts_final_clean',
        'fantasy-snipe-ai.nhl_projections.line_assignments_complete',
        'fantasy-snipe-ai.nhl_projections.line_assignments_clean',
        'fantasy-snipe-ai.nhl_projections.line_assignments_proper',
        'fantasy-snipe-ai.nhl_projections.line_assignments_fixed',
        'fantasy-snipe-ai.nhl_projections.line_assignments_corrected',
        'fantasy-snipe-ai.nhl_projections.line_assignments',
        'fantasy-snipe-ai.nhl_projections.line_forecasts_final',
        'fantasy-snipe-ai.nhl_projections.line_forecasts_proper',
        'fantasy-snipe-ai.nhl_projections.line_forecasts_fixed',
        'fantasy-snipe-ai.nhl_projections.line_forecasts_corrected',
        'fantasy-snipe-ai.nhl_projections.line_forecasts',
        'fantasy-snipe-ai.nhl_projections.player_forecasts_final',
        'fantasy-snipe-ai.nhl_projections.player_forecasts_corrected',
        'fantasy-snipe-ai.nhl_projections.player_forecasts_complete',
        'fantasy-snipe-ai.nhl_projections.player_forecasts_clean',
        'fantasy-snipe-ai.nhl_projections.player_forecasts_proper',
        'fantasy-snipe-ai.nhl_projections.player_forecasts_fixed',
        'fantasy-snipe-ai.nhl_projections.player_forecasts',
        'fantasy-snipe-ai.nhl_projections.player_input_templates_deduplicated',
        'fantasy-snipe-ai.nhl_projections.player_input_templates_final',
        'fantasy-snipe-ai.nhl_projections.player_input_templates_corrected',
        'fantasy-snipe-ai.nhl_projections.player_input_templates_clean',
        'fantasy-snipe-ai.nhl_projections.player_input_templates_fixed',
        'fantasy-snipe-ai.nhl_projections.player_input_templates',
        'fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26_deduplicated',
        'fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26_corrected',
        'fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26',
        'fantasy-snipe-ai.nhl_projections.validation_flags_fixed',
        'fantasy-snipe-ai.nhl_projections.validation_flags',
    ]
    
    for table_id in tables_to_delete:
        try:
            client.delete_table(table_id, not_found_ok=True)
            print(f'Deleted: {table_id}')
        except Exception as e:
            print(f'Error deleting {table_id}: {e}')
    
    print('Cleanup complete!')

if __name__ == '__main__':
    cleanup_duplicate_tables()
