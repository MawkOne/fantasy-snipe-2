import math
from typing import Dict, List


def cost_lmsr(q: List[float], b: float) -> float:
    # C(q) = b * ln(sum_i exp(q_i / b))
    if b <= 0:
        raise ValueError("b must be > 0")
    exps = [math.exp(qi / b) for qi in q]
    return b * math.log(sum(exps))


def prices_lmsr(q: List[float], b: float) -> List[float]:
    # p_i = exp(q_i / b) / sum_j exp(q_j / b)
    if b <= 0:
        raise ValueError("b must be > 0")
    exps = [math.exp(qi / b) for qi in q]
    denom = sum(exps)
    return [ei / denom for ei in exps]


def quote_delta(q: List[float], b: float, outcome_index: int, delta: float) -> Dict[str, float]:
    """Compute cost and prices after applying delta to outcome_index.

    Returns { cost, price_after } where price_after is the price of the traded outcome after the trade.
    """
    if outcome_index < 0 or outcome_index >= len(q):
        raise ValueError("invalid outcome_index")
    c_before = cost_lmsr(q, b)
    q_after = list(q)
    q_after[outcome_index] = q_after[outcome_index] + float(delta)
    c_after = cost_lmsr(q_after, b)
    cost = c_after - c_before
    prices_after = prices_lmsr(q_after, b)
    return {"cost": cost, "price_after": prices_after[outcome_index], "prices_after": prices_after}


