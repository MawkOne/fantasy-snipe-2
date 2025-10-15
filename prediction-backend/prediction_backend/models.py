from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class MarketCreate(BaseModel):
    slug: str
    title: str
    description: Optional[str] = None
    b: float = Field(gt=0)


class MarketResponse(BaseModel):
    id: str
    slug: str
    title: str
    description: Optional[str] = None
    outcome_type: str
    status: str
    b: float
    created_at: str
    outcomes: List[str]
    inventory: Dict[str, float]
    prices: Dict[str, float]


class QuoteRequest(BaseModel):
    outcome: str  # 'yes' | 'no'
    delta: float  # positive to buy shares


class QuoteResponse(BaseModel):
    cost: float
    price_after: float
    prices_after: Dict[str, float]


class TradeRequest(BaseModel):
    user_id: str
    outcome: str
    shares: float  # positive to buy


class TradeResponse(BaseModel):
    cost: float
    price_after: float
    user_vc_balance: float


