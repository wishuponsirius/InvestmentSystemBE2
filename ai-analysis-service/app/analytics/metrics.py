import numpy as np
import pandas as pd
from scipy import stats
from typing import Optional


RISK_FREE_RATE = 0.045
TRADING_DAYS = 252


class PortfolioMetricsEngine:
    def __init__(self, prices_df: pd.DataFrame):
        """
        prices_df:
          index   = datetime (daily)
          columns = asset names
          values  = price per gram in VND (or other canonical unit)
        """
        self.prices = prices_df.sort_index()
        self.returns = self.prices.pct_change().dropna()

    def current_prices(self) -> dict[str, float]:
        if self.prices.empty:
            return {}
        return self.prices.iloc[-1].to_dict()

    def volatility(self, asset: str) -> float:
        if asset not in self.returns.columns or len(self.returns[asset].dropna()) < 2:
            return 0.0
        return float(self.returns[asset].std() * np.sqrt(TRADING_DAYS))

    def var_95(self, asset: str, value_vnd: float) -> float:
        if asset not in self.returns.columns or value_vnd <= 0:
            return 0.0
        daily_vol = self.returns[asset].std()
        return float(value_vnd * stats.norm.ppf(0.05) * daily_vol)

    def sharpe_ratio(self, asset: str) -> Optional[float]:
        if asset not in self.returns.columns or len(self.returns[asset].dropna()) < 30:
            return None
        ann_return = float(self.returns[asset].mean() * TRADING_DAYS)
        ann_vol = self.volatility(asset)
        if ann_vol == 0:
            return None
        return round((ann_return - RISK_FREE_RATE) / ann_vol, 4)

    def max_drawdown(self, asset: str) -> float:
        if asset not in self.prices.columns:
            return 0.0
        px = self.prices[asset].dropna()
        if len(px) < 2:
            return 0.0
        roll_max = px.cummax()
        drawdown = (px / roll_max) - 1
        return round(float(drawdown.min()), 6)

    def correlation_matrix(self) -> dict[str, dict[str, float]]:
        if self.returns.empty or len(self.returns.columns) < 2:
            return {}
        return self.returns.corr().round(4).to_dict()

    def diversification_score(self, weights: dict[str, float]) -> float:
        if not weights:
            return 0.0
        w = np.array(list(weights.values()), dtype=float)
        return round(float(1 - np.sum(w ** 2)), 4)

    def rsi(self, asset: str, period: int = 14) -> Optional[float]:
        if asset not in self.prices.columns:
            return None

        px = self.prices[asset].dropna()
        if len(px) < period + 1:
            return None

        delta = px.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()

        last_gain = avg_gain.iloc[-1]
        last_loss = avg_loss.iloc[-1]

        if pd.isna(last_gain) or pd.isna(last_loss):
            return None
        if last_loss == 0 and last_gain > 0:
            return 100.0
        if last_gain == 0 and last_loss > 0:
            return 0.0
        if last_gain == 0 and last_loss == 0:
            return 50.0

        rs = last_gain / last_loss
        rsi = 100 - (100 / (1 + rs))
        return round(float(rsi), 2)

    def portfolio_returns(self, weights: dict[str, float]) -> pd.Series:
        if not weights:
            return pd.Series(dtype=float)

        assets = [a for a in weights if a in self.returns.columns]
        if not assets:
            return pd.Series(dtype=float)

        aligned = self.returns[assets].dropna()
        if aligned.empty:
            return pd.Series(dtype=float)

        weight_vector = np.array([weights[a] for a in assets], dtype=float)
        return aligned.mul(weight_vector, axis=1).sum(axis=1)

    def portfolio_volatility(self, weights: dict[str, float]) -> float:
        pr = self.portfolio_returns(weights)
        if len(pr) < 2:
            return 0.0
        return float(pr.std() * np.sqrt(TRADING_DAYS))

    def portfolio_sharpe_ratio(self, weights: dict[str, float]) -> Optional[float]:
        pr = self.portfolio_returns(weights)
        if len(pr) < 30:
            return None

        ann_return = float(pr.mean() * TRADING_DAYS)
        ann_vol = float(pr.std() * np.sqrt(TRADING_DAYS))
        if ann_vol == 0:
            return None

        return round((ann_return - RISK_FREE_RATE) / ann_vol, 4)

    def portfolio_max_drawdown(self, weights: dict[str, float]) -> float:
        pr = self.portfolio_returns(weights)
        if pr.empty:
            return 0.0

        curve = (1 + pr).cumprod()
        drawdown = (curve / curve.cummax()) - 1
        return round(float(drawdown.min()), 6)

    def portfolio_var_95(self, weights: dict[str, float], total_value: float) -> float:
        assets = [a for a in weights if a in self.returns.columns]
        if not assets or total_value <= 0:
            return 0.0

        if len(assets) == 1:
            return self.var_95(assets[0], total_value)

        w = np.array([weights[a] for a in assets], dtype=float)
        cov_daily = self.returns[assets].cov().values
        port_daily_vol = float(np.sqrt(w @ cov_daily @ w))
        return float(total_value * stats.norm.ppf(0.05) * port_daily_vol)