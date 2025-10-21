from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class MarketCreate(BaseModel):
    slug: str
    title: str
    description: Optional[str] = None
    b: float = Field(gt=0)
    player_name: Optional[str] = None
    metric: Optional[str] = None
    threshold: Optional[float] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    timeframe: Optional[str] = None  # Season | Monthly | Weekly
    team: Optional[str] = None
    volume_total: Optional[float] = None


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
    player_name: Optional[str] = None
    metric: Optional[str] = None
    threshold: Optional[float] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    timeframe: Optional[str] = None
    team: Optional[str] = None
    volume_total: Optional[float] = None
    landing_url: Optional[str] = None
    landing: Optional[Dict[str, Any]] = None
    player_projection: Optional[Dict[str, Any]] = None
    game_log: Optional[List[Dict[str, Any]]] = None


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


