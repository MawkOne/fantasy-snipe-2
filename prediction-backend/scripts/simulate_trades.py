"""
Simulate realistic trades on markets using LMSR AMM math.

Following the LMSR formula:
- Cost function: C(q) = b * ln(sum(exp(q_i / b)))
- Price: p_i = exp(q_i / b) / sum(exp(q_j / b))

Simulation strategy:
- Each market gets 10-50 trades
- Mix of buy/sell, varying sizes
- Prices evolve organically based on LMSR
- Different activity levels based on player popularity and timeframe
"""

import os
import sys
import random
import uuid
import math
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Tuple


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


def lmsr_cost(q: List[float], b: float) -> float:
    """
    LMSR cost function: C(q) = b * ln(sum(exp(q_i / b)))
    """
    return b * math.log(sum(math.exp(q_i / b) for q_i in q))


def lmsr_prices(q: List[float], b: float) -> List[float]:
    """
    LMSR price function (softmax): p_i = exp(q_i / b) / sum(exp(q_j / b))
    """
    exp_vals = [math.exp(q_i / b) for q_i in q]
    total = sum(exp_vals)
    return [exp_val / total for exp_val in exp_vals]


def quote_trade(q: List[float], b: float, outcome_index: int, delta: float) -> Tuple[float, List[float]]:
    """
    Quote a trade: return cost and new prices.
    
    Returns:
        (cost, new_prices)
    """
    # Current cost
    cost_before = lmsr_cost(q, b)
    
    # New q after trade
    q_after = q.copy()
    q_after[outcome_index] += delta
    
    # New cost
    cost_after = lmsr_cost(q_after, b)
    
    # Cost of trade
    cost = cost_after - cost_before
    
    # New prices
    new_prices = lmsr_prices(q_after, b)
    
    return cost, new_prices


def get_markets(cur) -> List[Dict]:
    """Get all open markets."""
    cur.execute(
        """
        SELECT id, slug, player_name, metric, threshold, b, timeframe, category
        FROM markets
        WHERE status = 'open'
        ORDER BY RANDOM()
        """
    )
    return cur.fetchall()


def get_market_state(cur, market_id: str) -> Tuple[float, List[float]]:
    """
    Get current b and q (inventory) for a market.
    
    Returns:
        (b, [q_yes, q_no])
    """
    # Get b
    cur.execute("SELECT b FROM markets WHERE id = %s", (market_id,))
    b = float(cur.fetchone()['b'])
    
    # Get inventory (q)
    cur.execute(
        """
        SELECT outcome, shares
        FROM amm_inventory
        WHERE market_id = %s
        ORDER BY outcome
        """,
        (market_id,)
    )
    inventory = cur.fetchall()
    
    # Ensure we have yes/no in order
    q = [0.0, 0.0]
    for inv in inventory:
        if inv['outcome'] == 'no':
            q[0] = float(inv['shares'])
        else:  # yes
            q[1] = float(inv['shares'])
    
    return b, q


def execute_trade(
    cur,
    market_id: str,
    user_id: str,
    outcome: str,  # 'yes' or 'no'
    delta: float,
    b: float,
    q: List[float]
) -> Tuple[float, List[float]]:
    """
    Execute a trade and update database state.
    
    Returns:
        (cost, new_prices)
    """
    # Determine outcome index (no=0, yes=1)
    outcome_index = 0 if outcome == 'no' else 1
    
    # Quote the trade
    cost, new_prices = quote_trade(q, b, outcome_index, delta)
    
    # Update inventory
    new_q = q.copy()
    new_q[outcome_index] += delta
    
    cur.execute(
        """
        UPDATE amm_inventory
        SET shares = %s
        WHERE market_id = %s AND outcome = %s
        """,
        (new_q[outcome_index], market_id, outcome)
    )
    
    # Update market volume
    cur.execute(
        """
        UPDATE markets
        SET volume_total = COALESCE(volume_total, 0) + %s
        WHERE id = %s
        """,
        (abs(cost), market_id)
    )
    
    # Record trade
    side = 'buy' if delta > 0 else 'sell'
    price_at_trade = new_prices[outcome_index]
    
    cur.execute(
        """
        INSERT INTO trades (
            id, market_id, user_id, side, outcome,
            shares, price, cost, created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """,
        (
            str(uuid.uuid4()),
            market_id,
            user_id,
            side,
            outcome,
            abs(delta),
            price_at_trade,
            abs(cost)
        )
    )
    
    return cost, new_prices


def determine_trade_count(player_name: str, timeframe: str, threshold: float) -> int:
    """
    Determine how many trades this market should have based on characteristics.
    
    High-profile players and season-long markets get more trades.
    """
    # Base count by timeframe
    if timeframe == 'Season':
        base = random.randint(25, 50)
    elif timeframe == 'Monthly':
        base = random.randint(15, 35)
    else:  # Weekly
        base = random.randint(8, 20)
    
    # Boost for elite players (high thresholds typically = elite)
    if threshold > 100:  # Elite scorer
        base = int(base * 1.4)
    elif threshold > 75:
        base = int(base * 1.2)
    
    # Superstar names (rough heuristic)
    superstars = ['McDavid', 'MacKinnon', 'Kucherov', 'Matthews', 'Draisaitl', 'Pastrnak']
    if any(star in player_name for star in superstars):
        base = int(base * 1.3)
    
    return base


def generate_trade_pattern(num_trades: int) -> List[Dict]:
    """
    Generate a realistic pattern of trades.
    
    Returns list of trade specs: [{'outcome': 'yes'|'no', 'delta': float}, ...]
    """
    trades = []
    
    # Start with slight bias toward one side (simulates early consensus)
    initial_bias = random.choice(['yes', 'no'])
    bias_strength = random.uniform(0.55, 0.7)  # 55-70% of early trades
    
    for i in range(num_trades):
        # Gradually reduce bias over time (market discovers true probability)
        current_bias = bias_strength - (i / num_trades) * 0.2
        current_bias = max(0.5, current_bias)
        
        # Determine outcome
        if random.random() < current_bias and i < num_trades * 0.6:
            outcome = initial_bias
        else:
            outcome = random.choice(['yes', 'no'])
        
        # Determine size (most trades are small, some are large)
        size_type = random.random()
        if size_type < 0.6:  # 60% small trades
            delta = random.uniform(0.5, 3.0)
        elif size_type < 0.9:  # 30% medium trades
            delta = random.uniform(3.0, 8.0)
        else:  # 10% large trades
            delta = random.uniform(8.0, 15.0)
        
        # Occasionally have sells (negative delta) to add realism
        if random.random() < 0.15 and i > 5:  # 15% are sells, but not at start
            delta = -delta * 0.6  # Sells tend to be smaller
        
        trades.append({
            'outcome': outcome,
            'delta': delta
        })
    
    return trades


def simulate_market(cur, market: Dict):
    """Simulate trades for a single market."""
    market_id = market['id']
    player_name = market['player_name']
    timeframe = market['timeframe']
    threshold = float(market['threshold'])
    
    # Determine number of trades
    num_trades = determine_trade_count(player_name, timeframe, threshold)
    
    # Get current state
    b, q = get_market_state(cur, market_id)
    
    # Generate trade pattern
    trade_pattern = generate_trade_pattern(num_trades)
    
    # Execute trades
    total_volume = 0
    user_id = str(uuid.uuid4())  # Simulate different users
    
    for i, trade_spec in enumerate(trade_pattern):
        # Occasionally switch user (simulates multiple traders)
        if i % 7 == 0:
            user_id = str(uuid.uuid4())
        
        outcome = trade_spec['outcome']
        delta = trade_spec['delta']
        
        # Execute trade
        try:
            cost, new_prices = execute_trade(cur, market_id, user_id, outcome, delta, b, q)
            total_volume += abs(cost)
            
            # Update q for next iteration
            outcome_index = 0 if outcome == 'no' else 1
            q[outcome_index] += delta
            
        except Exception as e:
            print(f"    ⚠️  Trade failed: {e}")
            continue
    
    # Get final prices
    final_prices = lmsr_prices(q, b)
    
    print(f"  ✅ {player_name:25s} {timeframe:8s} - {num_trades:3d} trades, ${total_volume:8,.2f} volume, YES:{final_prices[1]:.1%}")


def main():
    """Simulate trades across all markets."""
    conn = psycopg2.connect(get_db_url(), cursor_factory=RealDictCursor)
    
    try:
        with conn:
            with conn.cursor() as cur:
                print("🎲 Simulating Trades Using LMSR")
                print("=" * 80)
                
                # Get all markets
                markets = get_markets(cur)
                print(f"\nFound {len(markets)} open markets\n")
                
                # Group by position (check for -f or -d at end of slug)
                forwards = [m for m in markets if m['category'] == 'Players' and m['slug'].endswith('-f')]
                defence = [m for m in markets if m['category'] == 'Players' and m['slug'].endswith('-d')]
                
                print(f"📊 Simulating {len(forwards)} Forward markets...")
                for market in forwards:
                    simulate_market(cur, market)
                
                print(f"\n📊 Simulating {len(defence)} Defence markets...")
                for market in defence:
                    simulate_market(cur, market)
                
                # Summary stats
                cur.execute(
                    """
                    SELECT 
                        COUNT(*) as market_count,
                        SUM(volume_total) as total_volume,
                        AVG(volume_total) as avg_volume,
                        MIN(volume_total) as min_volume,
                        MAX(volume_total) as max_volume
                    FROM markets
                    WHERE status = 'open'
                    """
                )
                stats = cur.fetchone()
                
                print("\n" + "=" * 80)
                print("📈 SIMULATION SUMMARY")
                print("-" * 80)
                print(f"Markets simulated:  {stats['market_count']}")
                print(f"Total volume:       ${stats['total_volume']:,.2f}")
                print(f"Average volume:     ${stats['avg_volume']:,.2f}")
                print(f"Volume range:       ${stats['min_volume']:,.2f} - ${stats['max_volume']:,.2f}")
                
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()

