"""
Generate realistic trade volumes for all markets.

Volume distribution strategy:
- Top-ranked players (rank 1-5) get highest volumes ($8k-$15k)
- Mid-tier players (rank 6-12) get moderate volumes ($3k-$8k)
- Lower-tier players (rank 13-20) get lower volumes ($500-$3k)
- Points markets slightly more popular than Goals, which are slightly more than Assists
- Add randomness to make it realistic
"""

import os
import sys
import random
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


def extract_rank_from_slug(slug: str) -> int:
    """Extract rank number from slug like 'pts-r1-connor-mcdavid'"""
    try:
        parts = slug.split("-")
        for part in parts:
            if part.startswith("r") and part[1:].isdigit():
                return int(part[1:])
    except:
        pass
    return 999  # Default high rank if can't parse


def generate_volume(rank: int, metric: str) -> float:
    """
    Generate realistic trade volume based on rank and metric type.
    
    Args:
        rank: Player ranking (1-20, lower is better)
        metric: 'PTS', 'G', or 'A'
    
    Returns:
        Volume in dollars
    """
    # Metric multiplier (Points slightly more popular)
    metric_multipliers = {
        "PTS": 1.0,
        "G": 0.92,
        "A": 0.85,
    }
    metric_mult = metric_multipliers.get(metric, 1.0)
    
    # Rank-based base volume (exponential decay)
    # Top players get much more volume
    if rank <= 3:
        base_min, base_max = 10000, 15000
    elif rank <= 7:
        base_min, base_max = 6000, 10000
    elif rank <= 12:
        base_min, base_max = 3500, 6500
    elif rank <= 16:
        base_min, base_max = 1500, 3500
    else:
        base_min, base_max = 500, 2000
    
    # Generate base volume with some randomness
    base_volume = random.uniform(base_min, base_max)
    
    # Apply metric multiplier
    volume = base_volume * metric_mult
    
    # Add small random variation (±15%)
    variation = random.uniform(0.85, 1.15)
    volume *= variation
    
    # Round to nearest 50
    volume = round(volume / 50) * 50
    
    return max(100, volume)  # Minimum $100


def seed_volumes():
    """Update all markets with realistic trade volumes."""
    conn = psycopg2.connect(get_db_url(), cursor_factory=RealDictCursor)
    
    try:
        with conn:
            with conn.cursor() as cur:
                # Fetch all markets
                cur.execute(
                    """
                    SELECT id, slug, player_name, metric, threshold
                    FROM markets
                    ORDER BY threshold DESC
                    """
                )
                markets = cur.fetchall()
                
                print(f"Found {len(markets)} markets")
                
                updated_count = 0
                total_volume = 0
                
                for market in markets:
                    market_id = market["id"]
                    slug = market["slug"]
                    player = market["player_name"]
                    metric = market["metric"]
                    
                    # Extract rank from slug
                    rank = extract_rank_from_slug(slug)
                    
                    # Generate volume
                    volume = generate_volume(rank, metric)
                    total_volume += volume
                    
                    # Update market
                    cur.execute(
                        """
                        UPDATE markets
                        SET volume_total = %s
                        WHERE id = %s
                        """,
                        (volume, market_id),
                    )
                    
                    updated_count += 1
                    print(f"  {player:20s} {metric:3s} (rank {rank:2d}): ${volume:,.0f}")
                
                print(f"\nUpdated {updated_count} markets")
                print(f"Total volume across all markets: ${total_volume:,.0f}")
                print(f"Average volume per market: ${total_volume/updated_count:,.0f}")
                
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    seed_volumes()

