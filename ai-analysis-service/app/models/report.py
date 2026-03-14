from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AllocationItem(BaseModel):
    asset: str
    weight: float
    value_vnd: float
    quantity: float
    unit_symbol: str


class PerformanceItem(BaseModel):
    asset: str
    entry_price: Optional[float]
    current_price: float
    pnl: float
    return_pct: float


class RiskMetrics(BaseModel):
    volatility_annualized: float
    var_95_1day: float
    sharpe_ratio: Optional[float]
    max_drawdown: float
    correlation_matrix: dict[str, dict[str, float]]


class MomentumSignal(BaseModel):
    asset: str
    signal: str          # BUY | SELL | HOLD
    reason: str
    ma_7: float
    ma_30: float
    z_score: float
    rsi_14: Optional[float]


class TradeRecommendation(BaseModel):
    asset: str
    action: str
    urgency: str
    size_band: Optional[str] = None
    size_hint: Optional[str] = None
    estimated_pct_range: Optional[str] = None
    value_vnd_range: Optional[str] = None
    rationale: str
    conviction: float


class PortfolioReport(BaseModel):
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: str

    portfolio_value_vnd: float
    allocation: list[AllocationItem]

    performance: list[PerformanceItem]
    total_return_pct: float
    best_performer: str
    worst_performer: str

    risk: RiskMetrics
    diversification_score: float

    signals: list[MomentumSignal]
    trade_recommendations: list[TradeRecommendation]

    alerts: list[str]
    explanation: str = ""
    recommendation_summary: str = ""