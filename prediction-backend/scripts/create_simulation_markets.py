"""
Create prediction markets for top players by position and timeframe.

Markets:
- 30 Forwards (C/LW/RW) x 3 timeframes (Season, Monthly, Weekly) = 90 markets
- 30 Defence (D) x 3 timeframes (Season, Monthly, Weekly) = 90 markets
Total: 180 markets
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor


def get_db_url() -> str:
    db_url = (
        os.environ.get("MARKET_DATABASE_URL")
        or os.environ.get("NHL_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
    )
    if not db_url:
        print("Set DATABASE_URL or MARKET_DATABASE_URL in env.", file=sys.stderr)
        sys.exit(1)
    return db_url


def get_top_players(cur, position_filter: str, limit: int = 30):
    """
    Get top players by projected points.
    
    Args:
        position_filter: 'F' for forwards (C/LW/RW) or 'D' for defence
        limit: Number of players to return
    """
    if position_filter == 'F':
        # Forwards: C, LW, RW
        position_clause = "position IN ('C', 'LW', 'RW')"
    else:
        # Defence
        position_clause = "position = 'D'"
    
    cur.execute(
        f"""
        SELECT 
            player_name,
            position,
            team,
            nhl_player_id,
            metrics
        FROM fantasy_player_projections
        WHERE season = 2025
            AND source = 'DFO_skaters'
            AND {position_clause}
            AND (metrics->>'Points') IS NOT NULL
        ORDER BY (metrics->>'Points')::numeric DESC
        LIMIT %s
        """,
        (limit,)
    )
    return cur.fetchall()


def calculate_threshold(stat_value: float, timeframe: str) -> float:
    """
    Calculate appropriate threshold based on timeframe.
    
    Season: full season projection
    Monthly: ~1/6 of season (assuming ~6 months)
    Weekly: ~1/24 of season (assuming ~24 weeks)
    """
    if timeframe == 'Season':
        # Use full season projection, add 0.5 for binary threshold
        return round(stat_value) + 0.5
    elif timeframe == 'Monthly':
        # ~1/6 of season
        monthly = stat_value / 6.0
        return round(monthly * 2) / 2  # Round to nearest 0.5
    elif timeframe == 'Weekly':
        # ~1/24 of season
        weekly = stat_value / 24.0
        return round(weekly * 2) / 2  # Round to nearest 0.5
    return stat_value + 0.5


def calculate_b_parameter(threshold: float, timeframe: str) -> float:
    """
    Calculate liquidity parameter b based on expected activity.
    
    Following config: b ≈ 5-15% of expected per-market active VC
    Assuming typical market might see $1000-5000 in active trading
    """
    if timeframe == 'Season':
        # Season-long markets get more liquidity
        base_b = 75.0
    elif timeframe == 'Monthly':
        # Monthly markets moderate liquidity
        base_b = 40.0
    else:  # Weekly
        # Weekly markets lower liquidity
        base_b = 25.0
    
    # Scale slightly by threshold (higher stakes = more liquidity)
    if threshold > 100:
        base_b *= 1.3
    elif threshold > 50:
        base_b *= 1.15
    
    return round(base_b, 2)


def create_market(cur, player, timeframe: str, metric: str = 'PTS'):
    """Create a single market for a player."""
    player_name = player['player_name']
    position = player['position']
    team = player['team']
    nhl_player_id = player['nhl_player_id']
    metrics = player['metrics']
    
    # Get stat value
    stat_key = 'Points' if metric == 'PTS' else 'Goals' if metric == 'G' else 'Assists'
    if stat_key not in metrics:
        print(f"  ⚠️  Skipping {player_name} - no {stat_key} data")
        return None
    
    stat_value = float(metrics[stat_key])
    
    # Calculate threshold and b
    threshold = calculate_threshold(stat_value, timeframe)
    b = calculate_b_parameter(threshold, timeframe)
    
    # Create slug
    position_abbr = 'F' if position in ('C', 'LW', 'RW') else 'D'
    slug = f"{player_name.lower().replace(' ', '-')}-{metric.lower()}-{timeframe.lower()}-{position_abbr.lower()}"
    
    # Create title
    title = f"{player_name} {metric} - {timeframe}"
    
    # Description
    description = f"Will {player_name} ({position}, {team}) score Over {threshold} {metric} in {timeframe}?"
    
    # Category and sub_category
    category = "Players"
    sub_category = f"{timeframe} {metric}"
    
    # Check if market already exists
    cur.execute("SELECT id FROM markets WHERE slug = %s", (slug,))
    if cur.fetchone():
        print(f"  ⚠️  Market already exists: {slug}")
        return None
    
    # Create market
    cur.execute(
        """
        INSERT INTO markets (
            slug, title, description, outcome_type, status, b,
            player_name, metric, threshold, category, sub_category,
            timeframe, team, volume_total
        )
        VALUES (%s, %s, %s, 'binary', 'open', %s, %s, %s, %s, %s, %s, %s, %s, 0)
        RETURNING id
        """,
        (
            slug, title, description, b,
            player_name, metric, threshold, category, sub_category,
            timeframe, team
        )
    )
    market_id = cur.fetchone()['id']
    
    # Create outcomes
    cur.execute(
        "INSERT INTO market_outcomes (market_id, outcome) VALUES (%s, 'yes'), (%s, 'no')",
        (market_id, market_id)
    )
    
    # Create AMM inventory
    cur.execute(
        "INSERT INTO amm_inventory (market_id, outcome, shares) VALUES (%s, 'yes', 0), (%s, 'no', 0)",
        (market_id, market_id)
    )
    
    print(f"  ✅ Created: {player_name} {metric} {timeframe} (threshold={threshold}, b={b})")
    return market_id


def main():
    """Generate all markets."""
    conn = psycopg2.connect(get_db_url(), cursor_factory=RealDictCursor)
    
    try:
        with conn:
            with conn.cursor() as cur:
                print("🏒 Creating Prediction Markets")
                print("=" * 60)
                
                # Timeframes
                timeframes = ['Season', 'Monthly', 'Weekly']
                
                # Metrics to track
                metrics = ['PTS', 'G', 'A']
                
                total_created = 0
                
                # 1. Forwards Markets
                print("\n📊 FORWARDS MARKETS")
                print("-" * 60)
                forwards = get_top_players(cur, 'F', limit=30)
                print(f"Found {len(forwards)} top forwards\n")
                
                for timeframe in timeframes:
                    print(f"\n{timeframe} Markets:")
                    for player in forwards:
                        # Create market for primary metric (PTS)
                        market_id = create_market(cur, player, timeframe, 'PTS')
                        if market_id:
                            total_created += 1
                
                # 2. Defence Markets
                print("\n\n📊 DEFENCE MARKETS")
                print("-" * 60)
                defence = get_top_players(cur, 'D', limit=30)
                print(f"Found {len(defence)} top defencemen\n")
                
                for timeframe in timeframes:
                    print(f"\n{timeframe} Markets:")
                    for player in defence:
                        # Create market for primary metric (PTS)
                        market_id = create_market(cur, player, timeframe, 'PTS')
                        if market_id:
                            total_created += 1
                
                print("\n" + "=" * 60)
                print(f"✅ Total markets created: {total_created}")
                print(f"📋 Expected: {len(forwards) * 3 + len(defence) * 3} (30F×3 + 30D×3)")
                
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()

