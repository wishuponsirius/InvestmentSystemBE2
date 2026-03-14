from typing import Optional
from models.report import MomentumSignal, TradeRecommendation


def _safe_rsi(rsi_val: Optional[float]) -> Optional[float]:
    return None if rsi_val is None else float(rsi_val)


def _compute_portfolio_value(
    portfolio: dict[str, dict],
    current_prices: dict[str, float],
) -> float:
    total = 0.0
    for asset, pos in portfolio.items():
        if asset not in current_prices:
            continue
        qty = float(pos["quantity"])
        factor = float(pos.get("to_gram_factor", 1.0))
        px = float(current_prices[asset])
        total += qty * factor * px
    return total


def _compute_asset_weight(
    asset: str,
    portfolio: dict[str, dict],
    current_prices: dict[str, float],
    total_value: float,
) -> float:
    if total_value <= 0 or asset not in portfolio or asset not in current_prices:
        return 0.0

    qty = float(portfolio[asset]["quantity"])
    factor = float(portfolio[asset].get("to_gram_factor", 1.0))
    px = float(current_prices[asset])
    asset_value = qty * factor * px
    return asset_value / total_value


def _signal_conviction(sig: MomentumSignal) -> float:
    """
    Returns a coarse conviction score in [0, 1].
    Higher = stronger signal / more confidence in action.
    """
    score = 0.0
    rsi_val = _safe_rsi(sig.rsi_14)

    # Trend component
    ma_gap_pct = 0.0
    if sig.ma_30 and sig.ma_30 != 0:
        ma_gap_pct = abs(sig.ma_7 - sig.ma_30) / sig.ma_30

    score += min(ma_gap_pct / 0.03, 0.35)  # cap at 0.35

    # Z-score component
    score += min(abs(sig.z_score) / 3.0, 0.35)  # cap at 0.35

    # RSI component
    if rsi_val is not None:
        if rsi_val > 70:
            score += min((rsi_val - 70) / 30, 0.15)
        elif rsi_val < 30:
            score += min((30 - rsi_val) / 30, 0.15)

    # Small boost if signal is not HOLD
    if sig.signal in {"BUY", "SELL"}:
        score += 0.10

    return round(min(score, 1.0), 3)


def _score_reduce_strength(sig: MomentumSignal, asset_weight: float) -> float:
    """
    Strength score for SELL/REDUCE actions.
    Rough scale: 0 to ~4
    """
    score = 0.0
    rsi_val = _safe_rsi(sig.rsi_14)

    # Trend weakness
    if sig.ma_7 < sig.ma_30:
        score += 1.0

    # Price weakness / deviation
    if sig.z_score <= -1.0:
        score += 0.75
    if sig.z_score <= -2.0:
        score += 0.75

    # Overbought can also justify profit taking
    if rsi_val is not None and rsi_val > 70:
        score += 0.5

    # Concentration risk matters a lot
    if asset_weight > 0.50:
        score += 1.0
    elif asset_weight > 0.30:
        score += 0.5

    return round(score, 2)


def _score_buy_strength(sig: MomentumSignal, asset_weight: float) -> float:
    """
    Strength score for BUY actions.
    Rough scale: 0 to ~3
    Penalize high concentration so we don't keep adding to already huge positions.
    """
    score = 0.0
    rsi_val = _safe_rsi(sig.rsi_14)

    # Trend strength
    if sig.ma_7 > sig.ma_30:
        score += 1.0

    # Positive but not crazy extension
    if 0.0 <= sig.z_score <= 1.5:
        score += 0.75
    elif -1.5 <= sig.z_score < 0:
        score += 0.5  # mild dip buy

    # Oversold rebound setup
    if rsi_val is not None and rsi_val < 30:
        score += 0.75

    # Avoid encouraging adds to already concentrated assets
    if asset_weight > 0.50:
        score -= 0.75
    elif asset_weight > 0.30:
        score -= 0.35

    return round(max(score, 0.0), 2)


def _map_reduce_size_band(score: float) -> tuple[str, str, str]:
    """
    Returns:
      size_band, estimated_pct_range, size_hint
    """
    if score >= 2.75:
        return (
            "STRONG",
            "30-40%",
            "Consider a meaningful reduction to lock in gains and lower concentration risk."
        )
    elif score >= 1.75:
        return (
            "MODERATE",
            "15-25%",
            "Consider trimming part of the position."
        )
    elif score >= 1.0:
        return (
            "LIGHT",
            "5-10%",
            "Consider a light reduction if you want to derisk."
        )
    else:
        return (
            "LIGHT",
            "0-5%",
            "Only a small trim is justified, if any."
        )


def _map_buy_size_band(score: float) -> tuple[str, str, str]:
    if score >= 2.0:
        return (
            "MODERATE",
            "10-20%",
            "Consider a moderate addition."
        )
    elif score >= 1.0:
        return (
            "LIGHT",
            "5-10%",
            "Consider a small addition."
        )
    else:
        return (
            "LIGHT",
            "0-5%",
            "Only a very small addition is justified, if any."
        )


def _estimate_value_range(
    asset: str,
    portfolio: dict[str, dict],
    current_prices: dict[str, float],
    pct_range: str,
) -> Optional[str]:
    """
    Converts a percentage range like '15-25%' into approximate VND range.
    Keeps it coarse and rounded.
    """
    if asset not in portfolio or asset not in current_prices:
        return None

    try:
        low_str, high_str = pct_range.replace("%", "").split("-")
        low = float(low_str) / 100.0
        high = float(high_str) / 100.0
    except Exception:
        return None

    qty = float(portfolio[asset]["quantity"])
    factor = float(portfolio[asset].get("to_gram_factor", 1.0))
    px = float(current_prices[asset])

    position_value = qty * factor * px
    low_vnd = position_value * low
    high_vnd = position_value * high

    # round to nearest 100,000 VND for coarse guidance
    low_vnd = round(low_vnd / 100_000) * 100_000
    high_vnd = round(high_vnd / 100_000) * 100_000

    return f"{int(low_vnd):,}-{int(high_vnd):,} VND"


def generate_trade_recommendations(
    signals: list[MomentumSignal],
    portfolio: dict[str, dict],
    current_prices: dict[str, float],
) -> list[TradeRecommendation]:
    recs = []
    total_value = _compute_portfolio_value(portfolio, current_prices)

    for sig in signals:
        asset = sig.asset
        if asset not in portfolio or asset not in current_prices:
            continue

        asset_weight = _compute_asset_weight(asset, portfolio, current_prices, total_value)
        conviction = _signal_conviction(sig)

        if sig.signal == "BUY":
            action = "BUY"
            urgency = "MEDIUM"

            buy_score = _score_buy_strength(sig, asset_weight)
            size_band, pct_range, size_hint = _map_buy_size_band(buy_score)

            # If already very concentrated, soften the buy recommendation
            if asset_weight > 0.50:
                action = "HOLD"
                urgency = "LOW"
                size_band = None
                pct_range = None
                size_hint = "Momentum is positive, but the position is already highly concentrated."
                value_range = None
            else:
                value_range = _estimate_value_range(asset, portfolio, current_prices, pct_range)

            rationale = sig.reason
            if asset_weight > 0.30:
                rationale += "; portfolio concentration tempers further buying"

        elif sig.signal == "SELL":
            reduce_score = _score_reduce_strength(sig, asset_weight)

            # Escalate to SELL only if the signal is very strong
            if reduce_score >= 3.25 and sig.z_score <= -2.0:
                action = "SELL"
                urgency = "HIGH"
            else:
                action = "REDUCE"
                urgency = "HIGH" if reduce_score >= 2.75 else "MEDIUM"

            size_band, pct_range, size_hint = _map_reduce_size_band(reduce_score)
            value_range = _estimate_value_range(asset, portfolio, current_prices, pct_range)

            rationale = sig.reason
            if asset_weight > 0.30:
                rationale += "; position size is adding concentration risk"

        else:
            action = "HOLD"
            urgency = "LOW"
            size_band = None
            pct_range = None
            value_range = None
            size_hint = "No action needed unless you are rebalancing for risk reasons."
            rationale = sig.reason

        recs.append(TradeRecommendation(
            asset=asset,
            action=action,
            urgency=urgency,
            size_band=size_band,
            size_hint=size_hint,
            estimated_pct_range=pct_range,
            value_vnd_range=value_range,
            rationale=rationale,
            conviction=conviction,
        ))

    return recs

def generate_signals(prices_df: pd.DataFrame) -> list[MomentumSignal]:
    from analytics.metrics import PortfolioMetricsEngine

    engine = PortfolioMetricsEngine(prices_df)
    signals = []

    for asset in prices_df.columns:
        px = prices_df[asset].dropna()
        if len(px) < 30:
            continue

        ma_7 = float(px.rolling(7).mean().iloc[-1])
        ma_30 = float(px.rolling(30).mean().iloc[-1])
        std30 = float(px.rolling(30).std().iloc[-1])
        z_score = round((px.iloc[-1] - ma_30) / std30, 3) if std30 > 0 else 0.0
        rsi_val = engine.rsi(asset)

        if rsi_val is not None and rsi_val > 80:
            signal, reason = "HOLD", f"Uptrend remains intact, but RSI is extremely elevated at {round(rsi_val, 2)}"
        elif ma_7 > ma_30 and z_score < 1.5:
            signal, reason = "BUY", "MA7 above MA30, not overextended"
        elif ma_7 < ma_30 and z_score < -1.0:
            signal, reason = "SELL", "MA7 below MA30, price below 30d mean"
        elif z_score > 2.0:
            signal, reason = "SELL", "Price is well above its 30d average"
        elif rsi_val is not None and rsi_val > 70:
            signal, reason = "SELL", f"RSI overbought at {round(rsi_val, 2)}"
        elif rsi_val is not None and rsi_val < 30:
            signal, reason = "BUY", f"RSI oversold at {round(rsi_val, 2)}"
        else:
            signal, reason = "HOLD", "No strong directional signal"

        signals.append(MomentumSignal(
            asset=asset,
            signal=signal,
            reason=reason,
            ma_7=round(ma_7, 2),
            ma_30=round(ma_30, 2),
            z_score=z_score,
            rsi_14=round(rsi_val, 2) if rsi_val is not None else None,
        ))

    return signals