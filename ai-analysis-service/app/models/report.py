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
    action: str          # BUY | SELL | HOLD | REDUCE
    urgency: str         # HIGH | MEDIUM | LOW
    quantity: float
    value_vnd: float
    rationale: str


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

    signals: list[MomentumSignal] = Field(default_factory=list)
    trade_recommendations: list[TradeRecommendation] = Field(default_factory=list)

    alerts: list[str] = Field(default_factory=list)
    explanation: Optional[str] = ""
    recommendation_summary: Optional[str] = ""