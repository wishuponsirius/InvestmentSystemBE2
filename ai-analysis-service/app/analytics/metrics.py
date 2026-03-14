import numpy as np
import pandas as pd
from scipy import stats
from typing import Optional


RISK_FREE_RATE = 0.045  # Vietnamese gov bond ~4.5%
TRADING_DAYS = 252


class PortfolioMetricsEngine:

    def __init__(self, prices_df: pd.DataFrame):
        """
        prices_df: wide DataFrame
          index   = datetime (daily)
          columns = asset names
          values  = sell_price_vnd
        """
        self.prices = prices_df.sort_index()
        self.returns = prices_df.pct_change().dropna()

    def current_prices(self) -> dict[str, float]:
        return self.prices.iloc[-1].to_dict()

    def volatility(self, asset: str) -> float:
        """Annualized volatility from daily returns."""
        if asset not in self.returns or len(self.returns[asset]) < 2:
            return 0.0
        return float(self.returns[asset].std() * np.sqrt(TRADING_DAYS))

    def var_95(self, asset: str, value_vnd: float) -> float:
        """Parametric 1-day 95% VaR in VND (negative = loss)."""
        if asset not in self.returns:
            return 0.0
        daily_vol = self.returns[asset].std()
        return float(value_vnd * stats.norm.ppf(0.05) * daily_vol)

    def sharpe_ratio(self, asset: str) -> Optional[float]:
        """Annualized Sharpe ratio. None if insufficient data."""
        if asset not in self.returns or len(self.returns[asset]) < 30:
            return None
        ann_return = float(self.returns[asset].mean() * TRADING_DAYS)
        ann_vol = self.volatility(asset)
        if ann_vol == 0:
            return None
        return round((ann_return - RISK_FREE_RATE) / ann_vol, 4)

    def max_drawdown(self, asset: str) -> float:
        """Peak-to-trough drawdown over full price history."""
        if asset not in self.prices:
            return 0.0
        px = self.prices[asset].dropna()
        if len(px) < 2:
            return 0.0
        roll_max = px.cummax()
        drawdown = (px - roll_max) / roll_max
        return round(float(drawdown.min()), 6)

    def correlation_matrix(self) -> dict[str, dict[str, float]]:
        if self.returns.empty or len(self.returns.columns) < 2:
            return {}
        corr = self.returns.corr().round(4)
        return corr.to_dict()

    def portfolio_var_95(self, weights: dict[str, float], total_value: float) -> float:
        """Portfolio-level VaR accounting for correlations."""
        assets = list(weights.keys())
        if len(assets) < 2:
            asset = assets[0] if assets else None
            return self.var_95(asset, total_value) if asset else 0.0

        w = np.array([weights[a] for a in assets])
        cov = self.returns[assets].cov().values * TRADING_DAYS
        port_vol = float(np.sqrt(w @ cov @ w))
        return float(total_value * stats.norm.ppf(0.05) * port_vol / np.sqrt(TRADING_DAYS))

    def diversification_score(self, weights: dict[str, float]) -> float:
        """1 - HHI. Ranges 0 (fully concentrated) to 1 (perfectly spread)."""
        w = np.array(list(weights.values()))
        return round(float(1 - np.sum(w ** 2)), 4)

    def rsi(self, asset: str, period: int = 14) -> Optional[float]:
        if asset not in self.prices:
            return None
        px = self.prices[asset].dropna()
        if len(px) < period + 1:
            return None
        delta = px.diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = (-delta.clip(upper=0)).rolling(period).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi_series = 100 - (100 / (1 + rs))
        return round(float(rsi_series.iloc[-1]), 2)