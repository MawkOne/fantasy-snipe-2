#!/usr/bin/env python3
"""
Create BigQuery Schema for David Foster Forecasting Model

This script creates the necessary BigQuery tables and schemas
for implementing David Foster's forecasting method.
"""

from google.cloud import bigquery
import json

def create_foster_model_schema():
    """Create the BigQuery schema for the Foster forecasting model."""
    
    print("🏒 Creating BigQuery Schema for David Foster Forecasting Model")
    print("=" * 70)
    
    # Initialize BigQuery client
    client = bigquery.Client()
    dataset_id = "fantasy-snipe-ai.nhl_projections"
    
    # Create dataset if it doesn't exist
    try:
        dataset = client.get_dataset(dataset_id)
        print(f"✅ Dataset {dataset_id} already exists")
    except Exception:
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "US"
        dataset = client.create_dataset(dataset, timeout=30)
        print(f"✅ Created dataset {dataset_id}")
    
    # Define table schemas
    schemas = {
        "team_context": {
            "description": "Team-level context data for forecasting",
            "schema": [
                bigquery.SchemaField("team_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("team_name", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("season", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("cf_total", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("ca_total", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("cf_pct", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("goals_for", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("goals_against", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("goal_pct", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("pim_for", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("pim_against", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("gf_ga_differential", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("win_pct", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED")
            ]
        },
        
        "toi_profiles_by_role": {
            "description": "Historical TOI profiles by line role and position",
            "schema": [
                bigquery.SchemaField("role", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("position", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("age_group", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("season", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("avg_toi_ev", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("avg_toi_pp", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("avg_toi_pk", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("avg_toi_total", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("sample_size", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED")
            ]
        },
        
        "player_archetypes": {
            "description": "Player archetype classifications and thresholds",
            "schema": [
                bigquery.SchemaField("player_id", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("season", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("primary_archetype", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("secondary_archetype", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("archetype_score", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("age", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("cf_pct", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("gf60", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("pts_conversion", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("toi_avg", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED")
            ]
        },
        
        "line_assignments": {
            "description": "Player line assignments and roles",
            "schema": [
                bigquery.SchemaField("player_id", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("team_id", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("season", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("line_role", "STRING", mode="REQUIRED"),  # 1L, 2L, 3L, 4L, 1D, 2D, 3D
                bigquery.SchemaField("pp_role", "STRING", mode="NULLABLE"),    # PP1, PP2, None
                bigquery.SchemaField("pk_role", "STRING", mode="NULLABLE"),    # PK1, PK2, None
                bigquery.SchemaField("toi_ev", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("toi_pp", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("toi_pk", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("toi_total", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("confidence", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("source", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED")
            ]
        },
        
        "age_curve_adjustments": {
            "description": "Age curve adjustments for player performance",
            "schema": [
                bigquery.SchemaField("age", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("position", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("metric", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("adjustment_factor", "FLOAT64", mode="REQUIRED"),
                bigquery.SchemaField("sample_size", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("confidence", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED")
            ]
        },
        
        "player_input_templates": {
            "description": "Player input templates for forecasting",
            "schema": [
                bigquery.SchemaField("player_id", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("season", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("player_name", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("position", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("position_group", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("team_id", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("age", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("gp_3yr_avg", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("gp_3yr_total", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("toi_ev_avg", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("ecf60", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("eca60", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("pts_conversion", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("gf60", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("ga60", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED")
            ]
        },
        
        "line_forecasts": {
            "description": "Line-level forecasting results",
            "schema": [
                bigquery.SchemaField("team_id", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("season", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("line_role", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("line_type", "STRING", mode="REQUIRED"),  # EV, PP, PK
                bigquery.SchemaField("cf_forecast", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("ca_forecast", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("gf_forecast", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("ga_forecast", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("toi_forecast", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED")
            ]
        },
        
        "player_forecasts": {
            "description": "Individual player forecasting results",
            "schema": [
                bigquery.SchemaField("player_id", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("season", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("line_role", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("gp_forecast", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("goals_forecast", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("assists_forecast", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("points_forecast", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("plus_minus_forecast", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("pim_forecast", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("ppg_forecast", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("shg_forecast", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("sog_forecast", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("toi_forecast", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("fpts_forecast", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("confidence", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED")
            ]
        },
        
        "goalie_forecasts": {
            "description": "Goalie forecasting results with GSAA integration",
            "schema": [
                bigquery.SchemaField("player_id", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("season", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("gp_forecast", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("wins_forecast", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("losses_forecast", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("ot_losses_forecast", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("shutouts_forecast", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("gaa_forecast", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("sv_pct_forecast", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("saves_forecast", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("gsaa_forecast", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("fpts_forecast", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("confidence", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED")
            ]
        },
        
        "validation_flags": {
            "description": "Validation flags and quality control issues",
            "schema": [
                bigquery.SchemaField("flag_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("player_id", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("team_id", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("season", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("flag_type", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("flag_severity", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("description", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("metric", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("expected_value", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("actual_value", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("variance", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("resolved_by", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("resolved_at", "TIMESTAMP", mode="NULLABLE"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED")
            ]
        },
        
        "manual_adjustments": {
            "description": "Manual adjustments and overrides",
            "schema": [
                bigquery.SchemaField("adjustment_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("player_id", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("season", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("metric", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("original_value", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("adjusted_value", "FLOAT64", mode="REQUIRED"),
                bigquery.SchemaField("adjustment_reason", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("adjusted_by", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("confidence", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED")
            ]
        }
    }
    
    # Create tables
    for table_name, table_config in schemas.items():
        table_id = f"{dataset_id}.{table_name}"
        
        try:
            table = client.get_table(table_id)
            print(f"✅ Table {table_name} already exists")
        except Exception:
            schema = table_config["schema"]
            table = bigquery.Table(table_id, schema=schema)
            table.description = table_config["description"]
            table = client.create_table(table)
            print(f"✅ Created table {table_name}")
    
    print(f"\n🎯 Schema creation complete!")
    print(f"Dataset: {dataset_id}")
    print(f"Tables created: {len(schemas)}")
    
    # Create views for common queries
    create_forecasting_views(client, dataset_id)
    
    return schemas

def create_forecasting_views(client, dataset_id):
    """Create useful views for forecasting queries."""
    
    print("\n📊 Creating forecasting views...")
    
    views = {
        "current_player_forecasts": {
            "query": f"""
            SELECT 
                pf.player_id,
                pf.season,
                pit.player_name,
                pit.position,
                pit.team_id,
                pf.line_role,
                pf.gp_forecast,
                pf.goals_forecast,
                pf.assists_forecast,
                pf.points_forecast,
                pf.fpts_forecast,
                pf.confidence,
                pa.primary_archetype,
                pa.secondary_archetype
            FROM `{dataset_id}.player_forecasts` pf
            JOIN `{dataset_id}.player_input_templates` pit
                ON pf.player_id = pit.player_id 
                AND pf.season = pit.season
            LEFT JOIN `{dataset_id}.player_archetypes` pa
                ON pf.player_id = pa.player_id 
                AND pf.season = pa.season
            WHERE pf.season = CAST(EXTRACT(YEAR FROM CURRENT_DATE()) AS INT64)
            ORDER BY pf.fpts_forecast DESC
            """,
            "description": "Current season player forecasts with archetype info"
        },
        
        "team_forecast_summary": {
            "query": f"""
            SELECT 
                t.team_id,
                t.team_name,
                pf.season,
                COUNT(DISTINCT pf.player_id) as player_count,
                SUM(pf.fpts_forecast) as total_fpts,
                AVG(pf.fpts_forecast) as avg_fpts_per_player,
                MAX(pf.fpts_forecast) as top_player_fpts,
                COUNT(CASE WHEN pf.fpts_forecast > 200 THEN 1 END) as elite_players,
                COUNT(CASE WHEN pf.fpts_forecast BETWEEN 150 AND 200 THEN 1 END) as good_players
            FROM `{dataset_id}.player_forecasts` pf
            JOIN `{dataset_id}.player_input_templates` pit
                ON pf.player_id = pit.player_id 
                AND pf.season = pit.season
            JOIN `{dataset_id}.team_context` t
                ON pit.team_id = t.team_id 
                AND pf.season = t.season
            WHERE pf.season = CAST(EXTRACT(YEAR FROM CURRENT_DATE()) AS INT64)
            GROUP BY t.team_id, t.team_name, pf.season
            ORDER BY total_fpts DESC
            """,
            "description": "Team-level forecast summary"
        },
        
        "validation_summary": {
            "query": f"""
            SELECT 
                flag_type,
                flag_severity,
                COUNT(*) as flag_count,
                COUNT(CASE WHEN status = 'RESOLVED' THEN 1 END) as resolved_count,
                COUNT(CASE WHEN status = 'PENDING' THEN 1 END) as pending_count
            FROM `{dataset_id}.validation_flags`
            WHERE season = EXTRACT(YEAR FROM CURRENT_DATE())
            GROUP BY flag_type, flag_severity
            ORDER BY flag_count DESC
            """,
            "description": "Validation flags summary"
        }
    }
    
    for view_name, view_config in views.items():
        view_id = f"{dataset_id}.{view_name}"
        
        try:
            view = client.get_table(view_id)
            print(f"✅ View {view_name} already exists")
        except Exception:
            view = bigquery.Table(view_id)
            view.view_query = view_config["query"]
            view.description = view_config["description"]
            view = client.create_table(view)
            print(f"✅ Created view {view_name}")

if __name__ == "__main__":
    create_foster_model_schema()
