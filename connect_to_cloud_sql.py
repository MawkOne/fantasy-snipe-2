#!/usr/bin/env python3
"""
Connect to Cloud SQL and explore NHL data
"""

from sqlalchemy import create_engine, text, inspect
import pandas as pd

# Connection string (using public IP with SSL)
DATABASE_URL = "postgresql://postgres:123-new-password@34.47.23.137:5432/postgres?sslmode=require"

print("=" * 100)
print("  🔌 CONNECTING TO CLOUD SQL - NHL DATABASE")
print("=" * 100)

try:
    engine = create_engine(DATABASE_URL, echo=False)
    
    print("\n✅ Connecting to Cloud SQL...")
    
    with engine.connect() as conn:
        print("✅ Connected successfully!\n")
        
        # Get all tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print("=" * 100)
        print(f"  📊 FOUND {len(tables)} TABLES")
        print("=" * 100)
        
        if tables:
            print("\nTables in database:\n")
            for i, table in enumerate(sorted(tables), 1):
                # Get row count
                try:
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = count_result.scalar()
                    print(f"  {i:3}. {table:<40} ({count:,} rows)")
                except Exception as e:
                    print(f"  {i:3}. {table:<40} (error getting count)")
        else:
            print("\n⚠️  No tables found in 'postgres' database")
            print("   Checking for other databases...")
            
            # List all databases
            dbs_result = conn.execute(text("SELECT datname FROM pg_database WHERE datistemplate = false"))
            databases = [row[0] for row in dbs_result]
            print(f"\n   Available databases: {databases}")
            print("\n   💡 You might need to connect to 'nhl_api' database instead of 'postgres'")
        
        # If we have tables, show sample data
        if 'players' in tables:
            print("\n" + "=" * 100)
            print("  🏒 PLAYERS TABLE - SAMPLE DATA")
            print("=" * 100)
            
            players_df = pd.read_sql_query(
                text("SELECT * FROM players ORDER BY id LIMIT 10"),
                conn
            )
            print(players_df.to_string())
            
            # Search for Darnell Nurse
            print("\n" + "=" * 100)
            print("  🔎 SEARCHING FOR DARNELL NURSE (ID: 8477498)")
            print("=" * 100)
            
            nurse_df = pd.read_sql_query(
                text("SELECT * FROM players WHERE id = 8477498 OR name ILIKE '%nurse%'"),
                conn
            )
            
            if not nurse_df.empty:
                print("\n✅ Found Darnell Nurse:")
                print(nurse_df.to_string())
            else:
                print("\n❌ Darnell Nurse not found")
        
        if 'games' in tables:
            print("\n" + "=" * 100)
            print("  🏒 GAMES TABLE - RECENT GAMES")
            print("=" * 100)
            
            games_df = pd.read_sql_query(
                text("SELECT * FROM games ORDER BY game_date DESC LIMIT 5"),
                conn
            )
            print(games_df.to_string())
        
        print("\n" + "=" * 100)
        print("  ✅ DATABASE EXPLORATION COMPLETE")
        print("=" * 100)
        
except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    print("\nTrying alternate database 'nhl_api'...")
    
    try:
        # Try nhl_api database
        alt_url = "postgresql://postgres:123-new-password@34.47.23.137:5432/nhl_api?sslmode=require"
        engine = create_engine(alt_url, echo=False)
        
        with engine.connect() as conn:
            print("✅ Connected to 'nhl_api' database!\n")
            
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            print("=" * 100)
            print(f"  📊 FOUND {len(tables)} TABLES IN 'nhl_api'")
            print("=" * 100)
            
            for i, table in enumerate(sorted(tables)[:20], 1):
                try:
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = count_result.scalar()
                    print(f"  {i:3}. {table:<40} ({count:,} rows)")
                except:
                    print(f"  {i:3}. {table:<40}")
            
            if len(tables) > 20:
                print(f"\n  ... and {len(tables) - 20} more tables")
                
    except Exception as e2:
        print(f"❌ Also failed: {e2}")

