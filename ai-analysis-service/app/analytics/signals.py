from __future__ import annotations

import pandas as pd
from pydantic import BaseModel
from analytics.metrics import PortfolioMetricsEngine
from models.report import MomentumSignal


class AssetView(BaseModel):
    asset: str
    price: float
    ma_7: float
    ma_30: float
    ma_gap_pct: float
    z_score: float
    rsi_14: float | None
    volatility_annualized: float
    trend: str
    state_flags: list[str]
    signal_score: float
    conviction: str


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def build_asset_views(prices_df: pd.DataFrame) -> list[AssetView]:
    engine = PortfolioMetricsEngine(prices_df)
    views: list[AssetView] = []

    for asset in prices_df.columns:
        px = prices_df[asset].dropna()
        if len(px) < 30:
            continue

        price = float(px.iloc[-1])
        ma_7 = float(px.rolling(7).mean().iloc[-1])
        ma_30 = float(px.rolling(30).mean().iloc[-1])
        std_30 = float(px.rolling(30).std().iloc[-1])

        z_score = (price - ma_30) / std_30 if std_30 > 0 else 0.0
        ma_gap_pct = ((ma_7 - ma_30) / ma_30) * 100 if ma_30 != 0 else 0.0
        rsi_val = engine.rsi(asset)
        vol = float(engine.volatility(asset))

        if ma_7 > ma_30:
            trend = "up"
        elif ma_7 < ma_30:
            trend = "down"
        else:
            trend = "flat"

        flags: list[str] = []

        if trend == "up":
            flags.append("trend_up")
        elif trend == "down":
            flags.append("trend_down")

        if z_score >= 2:
            flags.append("stretched_high")
        elif z_score <= -2:
            flags.append("stretched_low")

        if rsi_val is not None and rsi_val > 70:
            flags.append("overbought")
        elif rsi_val is not None and rsi_val < 30:
            flags.append("oversold")

        if vol > 0.4:
            flags.append("high_volatility")

        # --- Composite score ---
        # Trend component: MA gap matters more than simple above/below
        trend_score = _clamp(ma_gap_pct / 2.0, -2.0, 2.0)

        # Stretch component: being too far above trend is bearish, too far below is bullish
        stretch_score = _clamp(-z_score / 2.0, -1.5, 1.5)

        # RSI component: overbought bearish, oversold bullish
        rsi_score = 0.0
        if rsi_val is not None:
            rsi_score = _clamp((50.0 - rsi_val) / 20.0, -1.5, 1.5)

        # Volatility penalty reduces conviction, not direction
        vol_penalty = min(vol, 1.0) * 0.75

        raw_score = trend_score + stretch_score + rsi_score
        signal_score = raw_score - (vol_penalty if raw_score > 0 else -vol_penalty * 0.5)

        abs_score = abs(signal_score)
        if abs_score >= 2.0:
            conviction = "high"
        elif abs_score >= 1.0:
            conviction = "medium"
        else:
            conviction = "low"

        views.append(
            AssetView(
                asset=asset,
                price=round(price, 2),
                ma_7=round(ma_7, 2),
                ma_30=round(ma_30, 2),
                ma_gap_pct=round(ma_gap_pct, 4),
                z_score=round(z_score, 3),
                rsi_14=round(rsi_val, 2) if rsi_val is not None else None,
                volatility_annualized=round(vol, 6),
                trend=trend,
                state_flags=flags,
                signal_score=round(signal_score, 3),
                conviction=conviction,
            )
        )

    return views


def generate_signals(prices_df: pd.DataFrame) -> list[MomentumSignal]:
    """
    Backward-compatible signal generation using a composite score.
    """
    views = build_asset_views(prices_df)
    signals: list[MomentumSignal] = []

    for view in views:
        score = view.signal_score
        flags = set(view.state_flags)

        if score >= 1.5:
            signal = "BUY"
            reason = "Trend and momentum setup look favorable"
        elif score >= 0.5:
            signal = "HOLD"
            reason = "Mildly supportive conditions, but not strong enough to add aggressively"
        elif score > -0.5:
            signal = "HOLD"
            reason = "Mixed or neutral conditions"
        elif score > -1.5:
            signal = "HOLD"
            reason = "Conditions are weakening, but not enough to justify trimming"
        else:
            signal = "REDUCE"
            reason = "Weak trend and/or overextended conditions raise pullback risk"

        # Improve explanation with context
        reason_bits: list[str] = []
        if "trend_up" in flags:
            reason_bits.append("short-term trend is up")
        elif "trend_down" in flags:
            reason_bits.append("short-term trend is down")

        if "overbought" in flags:
            reason_bits.append("RSI is overbought")
        elif "oversold" in flags:
            reason_bits.append("RSI is oversold")

        if "stretched_high" in flags:
            reason_bits.append("price is stretched above its 30-day mean")
        elif "stretched_low" in flags:
            reason_bits.append("price is stretched below its 30-day mean")

        if "high_volatility" in flags:
            reason_bits.append("volatility is elevated")

        if reason_bits:
            reason = f"{reason}. " + "; ".join(reason_bits).capitalize()

        signals.append(
            MomentumSignal(
                asset=view.asset,
                signal=signal,
                reason=reason,
                ma_7=view.ma_7,
                ma_30=view.ma_30,
                z_score=view.z_score,
                rsi_14=view.rsi_14,
            )
        )

    return signals