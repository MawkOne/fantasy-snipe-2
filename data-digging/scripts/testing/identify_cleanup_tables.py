#!/usr/bin/env python3

from google.cloud import bigquery
import pandas as pd
from collections import defaultdict
import re

def identify_cleanup_tables():
    """Identify tables that can be removed as they are duplicates or previous versions"""
    
    client = bigquery.Client()
    
    print("="*80)
    print("IDENTIFYING TABLES FOR CLEANUP")
    print("="*80)
    
    # Get all tables from non-raw datasets
    non_raw_datasets = ['nhl_external', 'nhl_processed', 'nhl_projections']
    
    all_tables = []
    for dataset_id in non_raw_datasets:
        try:
            tables = list(client.list_tables(dataset_id))
            for table in tables:
                table_ref = client.get_table(f'{dataset_id}.{table.table_id}')
                all_tables.append({
                    'dataset': dataset_id,
                    'table': table.table_id,
                    'type': 'VIEW' if table_ref.table_type == 'VIEW' else 'TABLE',
                    'created': table_ref.created.strftime('%Y-%m-%d %H:%M') if table_ref.created else 'Unknown',
                    'size_bytes': table_ref.num_bytes if hasattr(table_ref, 'num_bytes') else 0
                })
        except Exception as e:
            print(f"Error accessing {dataset_id}: {e}")
    
    # Group tables by base name (removing suffixes like _clean, _final, _corrected, etc.)
    table_groups = defaultdict(list)
    
    for table_info in all_tables:
        base_name = table_info['table']
        
        # Remove common suffixes
        suffixes_to_remove = [
            '_clean', '_final', '_corrected', '_fixed', '_proper', '_complete', 
            '_deduplicated', '_role_based', '_final_clean', '_final_corrected',
            '_final_fixed', '_final_proper', '_clean_final', '_deduplicated_final'
        ]
        
        for suffix in suffixes_to_remove:
            if base_name.endswith(suffix):
                base_name = base_name[:-len(suffix)]
                break
        
        table_groups[base_name].append(table_info)
    
    print("TABLES GROUPED BY BASE NAME:")
    print("="*80)
    
    cleanup_candidates = []
    
    for base_name, tables in table_groups.items():
        if len(tables) > 1:
            print(f"\n{base_name.upper()} ({len(tables)} variants):")
            print("-" * 60)
            
            # Sort by creation time (newest first)
            tables.sort(key=lambda x: x['created'], reverse=True)
            
            for i, table in enumerate(tables):
                status = "KEEP (LATEST)" if i == 0 else "CLEANUP CANDIDATE"
                print(f"  {status:20} | {table['dataset']:15} | {table['table']:35} | {table['type']:4} | {table['created']}")
                
                if i > 0:  # Not the latest version
                    cleanup_candidates.append(table)
        else:
            # Single table - check if it's a view that might be replaceable
            table = tables[0]
            if table['type'] == 'VIEW' and any(suffix in table['table'] for suffix in ['_corrected', '_final', '_clean']):
                print(f"\n{base_name.upper()} (1 variant - VIEW):")
                print("-" * 60)
                print(f"  REVIEW NEEDED     | {table['dataset']:15} | {table['table']:35} | {table['type']:4} | {table['created']}")
    
    print("\n" + "="*80)
    print("CLEANUP RECOMMENDATIONS")
    print("="*80)
    
    # Categorize cleanup candidates
    by_dataset = defaultdict(list)
    for table in cleanup_candidates:
        by_dataset[table['dataset']].append(table)
    
    total_cleanup = 0
    for dataset, tables in by_dataset.items():
        print(f"\n{dataset.upper()} - {len(tables)} tables to clean up:")
        print("-" * 50)
        for table in sorted(tables, key=lambda x: x['table']):
            print(f"  - {table['table']} ({table['type']}) - Created: {table['created']}")
            total_cleanup += 1
    
    print(f"\nTOTAL CLEANUP CANDIDATES: {total_cleanup}")
    
    # Specific recommendations for nhl_projections (most cluttered)
    print("\n" + "="*80)
    print("SPECIFIC RECOMMENDATIONS FOR NHL_PROJECTIONS")
    print("="*80)
    
    projections_tables = [t for t in all_tables if t['dataset'] == 'nhl_projections']
    
    # Group by functionality
    functionality_groups = {
        'Player Forecasts': [t for t in projections_tables if 'player_forecasts' in t['table']],
        'Line Assignments': [t for t in projections_tables if 'line_assignments' in t['table']],
        'Line Forecasts': [t for t in projections_tables if 'line_forecasts' in t['table']],
        'Player Input Templates': [t for t in projections_tables if 'player_input_templates' in t['table']],
        'Current Player Forecasts': [t for t in projections_tables if 'current_player_forecasts' in t['table']],
        'Validation Flags': [t for t in projections_tables if 'validation_flags' in t['table']],
        'Projected Rosters': [t for t in projections_tables if 'projected_rosters' in t['table']]
    }
    
    for func_name, tables in functionality_groups.items():
        if len(tables) > 1:
            print(f"\n{func_name} ({len(tables)} tables):")
            tables.sort(key=lambda x: x['created'], reverse=True)
            keep_table = tables[0]
            cleanup_tables = tables[1:]
            
            print(f"  KEEP: {keep_table['table']} ({keep_table['type']}) - {keep_table['created']}")
            for table in cleanup_tables:
                print(f"  REMOVE: {table['table']} ({table['type']}) - {table['created']}")
    
    print("\n" + "="*80)
    print("CLEANUP SCRIPT GENERATION")
    print("="*80)
    
    # Generate cleanup script
    cleanup_script = "#!/usr/bin/env python3\n\n"
    cleanup_script += "from google.cloud import bigquery\n\n"
    cleanup_script += "def cleanup_duplicate_tables():\n"
    cleanup_script += "    client = bigquery.Client()\n"
    cleanup_script += "    \n"
    cleanup_script += "    print('Cleaning up duplicate and previous version tables...')\n"
    cleanup_script += "    \n"
    cleanup_script += "    tables_to_delete = [\n"
    
    for table in cleanup_candidates:
        dataset = table["dataset"]
        table_name = table["table"]
        cleanup_script += f"        'fantasy-snipe-ai.{dataset}.{table_name}',\n"
    
    cleanup_script += "    ]\n"
    cleanup_script += "    \n"
    cleanup_script += "    for table_id in tables_to_delete:\n"
    cleanup_script += "        try:\n"
    cleanup_script += "            client.delete_table(table_id, not_found_ok=True)\n"
    cleanup_script += "            print(f'Deleted: {table_id}')\n"
    cleanup_script += "        except Exception as e:\n"
    cleanup_script += "            print(f'Error deleting {table_id}: {e}')\n"
    cleanup_script += "    \n"
    cleanup_script += "    print('Cleanup complete!')\n"
    cleanup_script += "\nif __name__ == '__main__':\n"
    cleanup_script += "    cleanup_duplicate_tables()\n"
    
    with open('scripts/cleanup_duplicate_tables.py', 'w') as f:
        f.write(cleanup_script)
    
    print("Generated cleanup script: scripts/cleanup_duplicate_tables.py")
    print(f"This script will remove {total_cleanup} duplicate/previous version tables")

if __name__ == "__main__":
    identify_cleanup_tables()
