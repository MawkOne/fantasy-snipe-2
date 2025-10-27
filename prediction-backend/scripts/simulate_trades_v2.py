"""
Simulate realistic trades on markets using LMSR AMM math - Optimized version.

Processes markets in batches with progress reporting.
"""

import os
import sys
import random
import uuid
import math
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Tuple
from datetime import datetime, timedelta


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
    """LMSR cost function: C(q) = b * ln(sum(exp(q_i / b)))"""
    try:
        return b * math.log(sum(math.exp(q_i / b) for q_i in q))
    except OverflowError:
        # Handle large values
        max_q = max(q)
        return b * (max_q / b + math.log(sum(math.exp((q_i - max_q) / b) for q_i in q)))


def lmsr_prices(q: List[float], b: float) -> List[float]:
    """LMSR price function (softmax)"""
    try:
        exp_vals = [math.exp(q_i / b) for q_i in q]
        total = sum(exp_vals)
        return [exp_val / total for exp_val in exp_vals]
    except OverflowError:
        # Handle large values with log-sum-exp trick
        max_q = max(q)
        exp_vals = [math.exp((q_i - max_q) / b) for q_i in q]
        total = sum(exp_vals)
        return [exp_val / total for exp_val in exp_vals]


def quote_trade(q: List[float], b: float, outcome_index: int, delta: float) -> Tuple[float, List[float]]:
    """Quote a trade"""
    cost_before = lmsr_cost(q, b)
    q_after = q.copy()
    q_after[outcome_index] += delta
    cost_after = lmsr_cost(q_after, b)
    cost = cost_after - cost_before
    new_prices = lmsr_prices(q_after, b)
    return cost, new_prices


def simulate_market_trades(cur, market_id: str, b: float, num_trades: int, timeframe: str = 'Season', verbose: bool = False) -> float:
    """
    Simulate trades for a single market and return total volume.
    Spreads trades over time based on timeframe.
    """
    # Start with neutral inventory
    q = [0.0, 0.0]  # [no, yes]
    
    total_volume = 0.0
    user_id = str(uuid.uuid4())
    
    # Generate trade pattern (biased initially, then converges)
    initial_bias_yes = random.random() > 0.5
    
    # Determine time range based on timeframe
    now = datetime.utcnow()
    if timeframe == 'Season':
        days_back = 30
    elif timeframe == 'Monthly':
        days_back = 14
    else:  # Weekly
        days_back = 7
    
    # Generate timestamps (more recent = more trades)
    trade_timestamps = []
    for i in range(num_trades):
        # Weight towards more recent dates (exponential distribution)
        random_factor = random.betavariate(2, 5)  # Skewed towards recent
        days_ago = days_back * random_factor
        trade_time = now - timedelta(days=days_ago)
        trade_timestamps.append(trade_time)
    
    # Sort timestamps chronologically (oldest first)
    trade_timestamps.sort()
    
    if verbose:
        print(f"      Starting with {num_trades} trades over {days_back} days...", end='', flush=True)
    
    for i in range(num_trades):
        # Occasionally switch user
        if i % 7 == 0:
            user_id = str(uuid.uuid4())
        
        # Determine outcome (starts biased, becomes more random)
        bias = 0.65 - (i / num_trades) * 0.15
        if random.random() < bias and i < num_trades * 0.6:
            outcome_index = 1 if initial_bias_yes else 0
        else:
            outcome_index = random.randint(0, 1)
        
        outcome = 'yes' if outcome_index == 1 else 'no'
        
        # Determine size (mostly small, some large)
        r = random.random()
        if r < 0.6:
            delta = random.uniform(0.5, 3.0)
        elif r < 0.9:
            delta = random.uniform(3.0, 8.0)
        else:
            delta = random.uniform(8.0, 15.0)
        
        # Occasionally sell (but not at start)
        if random.random() < 0.15 and i > 5:
            delta = -delta * 0.6
        
        # Quote and execute
        try:
            cost, new_prices = quote_trade(q, b, outcome_index, delta)
            
            # Update q
            q[outcome_index] += delta
            
            # Track volume
            total_volume += abs(cost)
            
            # Write to database with timestamp
            side = 'buy' if delta > 0 else 'sell'
            cur.execute(
                """
                INSERT INTO trades (id, market_id, user_id, side, outcome, shares, price, cost, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (str(uuid.uuid4()), market_id, user_id, side, outcome, abs(delta), new_prices[outcome_index], abs(cost), trade_timestamps[i])
            )
            
        except Exception as e:
            if verbose:
                print(f" ⚠️ Trade error: {e}")
            continue
    
    # Update market inventory and volume
    cur.execute(
        "UPDATE amm_inventory SET shares = %s WHERE market_id = %s AND outcome = 'no'",
        (q[0], market_id)
    )
    cur.execute(
        "UPDATE amm_inventory SET shares = %s WHERE market_id = %s AND outcome = 'yes'",
        (q[1], market_id)
    )
    cur.execute(
        "UPDATE markets SET volume_total = %s WHERE id = %s",
        (total_volume, market_id)
    )
    
    if verbose:
        final_prices = lmsr_prices(q, b)
        print(f" Done! Volume: ${total_volume:.2f}, YES price: {final_prices[1]:.1%}")
    
    return total_volume


def main():
    """Simulate trades across all new markets."""
    conn = psycopg2.connect(get_db_url(), cursor_factory=RealDictCursor)
    
    try:
        with conn:
            with conn.cursor() as cur:
                print("🎲 Simulating Trades Using LMSR (Optimized)")
                print("=" * 80)
                
                # Get only the new markets (with timeframe set)
                cur.execute(
                    """
                    SELECT id, slug, player_name, b, timeframe, threshold
                    FROM markets
                    WHERE status = 'open' AND timeframe IS NOT NULL
                    ORDER BY timeframe, threshold DESC
                    """
                )
                markets = cur.fetchall()
                
                print(f"\nFound {len(markets)} markets to simulate\n")
                
                total_volume = 0.0
                processed = 0
                
                print("📊 Starting trade simulation...\n")
                
                for market in markets:
                    market_id = market['id']
                    player = market['player_name']
                    timeframe = market['timeframe']
                    threshold = float(market['threshold'])
                    b = float(market['b'])
                    
                    # Show current market
                    print(f"  [{processed+1}/{len(markets)}] {player:30s} {timeframe:8s} (t={threshold:5.1f}, b={b:5.1f})", end='', flush=True)
                    
                    # Determine trade count based on characteristics
                    if timeframe == 'Season':
                        num_trades = random.randint(25, 50)
                        if threshold > 100:
                            num_trades = int(num_trades * 1.4)
                    elif timeframe == 'Monthly':
                        num_trades = random.randint(15, 35)
                    else:  # Weekly
                        num_trades = random.randint(8, 20)
                    
                    # Simulate trades with verbose output for first few
                    verbose = processed < 3
                    volume = simulate_market_trades(cur, market_id, b, num_trades, timeframe, verbose)
                    total_volume += volume
                    processed += 1
                    
                    # Show result
                    if not verbose:
                        print(f" → {num_trades:2d} trades, ${volume:8,.2f} vol")
                    
                    # Commit every 10 markets
                    if processed % 10 == 0:
                        conn.commit()
                        print(f"  ✅ Committed batch (total volume so far: ${total_volume:,.2f})\n")
                
                conn.commit()  # Final commit
                
                print("\n" + "=" * 80)
                print("📈 SIMULATION SUMMARY")
                print("-" * 80)
                print(f"Markets simulated:  {processed}")
                print(f"Total volume:       ${total_volume:,.2f}")
                print(f"Average volume:     ${total_volume/processed:,.2f}")
                
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()

