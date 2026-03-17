import pandas as pd
from typing import Optional
from models.report import MomentumSignal, TradeRecommendation, SpreadInsight


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


def _classify_trend(ma_7: float, ma_30: float, ma_90: float) -> str:
    """
    Returns:
        STRONG_BULL
        BULL
        STRONG_BEAR
        BEAR
        NEUTRAL
    """
    if ma_7 > ma_30 > ma_90:
        return "STRONG_BULL"
    if ma_7 > ma_30 and ma_30 >= ma_90:
        return "BULL"
    if ma_7 < ma_30 < ma_90:
        return "STRONG_BEAR"
    if ma_7 < ma_30 and ma_30 <= ma_90:
        return "BEAR"
    return "NEUTRAL"


def _classify_stretch(z_score: float, rsi_val: Optional[float]) -> str:
    """
    Captures whether price is stretched or washed out.
    Returns:
        OVERBOUGHT
        OVERSOLD
        NEAR_FAIR
        NEUTRAL
    """
    if z_score >= 1.5 or (rsi_val is not None and rsi_val >= 70):
        return "OVERBOUGHT"
    if z_score <= -1.5 or (rsi_val is not None and rsi_val <= 30):
        return "OVERSOLD"
    if -0.75 <= z_score <= 0.75:
        return "NEAR_FAIR"
    return "NEUTRAL"


def _classify_spread(spread: Optional[SpreadInsight]) -> str:
    """
    Returns:
        VERY_CHEAP_LOCAL
        CHEAP_LOCAL
        VERY_RICH_LOCAL
        RICH_LOCAL
        NORMAL
        UNKNOWN
    """
    if spread is None or spread.z_score_30d is None:
        return "UNKNOWN"

    s_z = float(spread.z_score_30d)

    if s_z <= -2.0:
        return "VERY_CHEAP_LOCAL"
    if s_z <= -1.0:
        return "CHEAP_LOCAL"
    if s_z >= 2.0:
        return "VERY_RICH_LOCAL"
    if s_z >= 1.0:
        return "RICH_LOCAL"
    return "NORMAL"


def _build_reason(
    trend_state: str,
    stretch_state: str,
    spread_state: str,
    spread: Optional[SpreadInsight],
) -> str:
    parts = []

    trend_reason_map = {
        "STRONG_BULL": "Bullish alignment across short, medium, and long-term moving averages",
        "BULL": "Short-term momentum is positive and medium-term trend remains supportive",
        "STRONG_BEAR": "Bearish alignment across short, medium, and long-term moving averages",
        "BEAR": "Short-term weakness is developing against a soft medium-term trend",
        "NEUTRAL": "Trend signals are mixed across timeframes",
    }

    stretch_reason_map = {
        "OVERBOUGHT": "price looks somewhat stretched",
        "OVERSOLD": "price looks washed out",
        "NEAR_FAIR": "price is trading near its recent average",
        "NEUTRAL": "",
    }

    spread_reason_map = {
        "VERY_CHEAP_LOCAL": "local price is at an unusually wide discount to global pricing",
        "CHEAP_LOCAL": "local price is modestly discounted versus global pricing",
        "VERY_RICH_LOCAL": "local price is at an unusually high premium to global pricing",
        "RICH_LOCAL": "local price is somewhat rich versus global pricing",
        "NORMAL": "",
        "UNKNOWN": "",
    }

    parts.append(trend_reason_map[trend_state])

    stretch_text = stretch_reason_map[stretch_state]
    if stretch_text:
        parts.append(stretch_text)

    spread_text = spread_reason_map[spread_state]
    if spread_text:
        if spread is not None and spread.current_spread_pct is not None:
            parts.append(f"{spread_text} ({spread.current_spread_pct:.2f}%)")
        else:
            parts.append(spread_text)

    return "; ".join(parts)


def _decide_signal(
    trend_state: str,
    stretch_state: str,
    spread_state: str,
) -> tuple[str, str]:
    """
    Final signal policy:
    - BUY when trend is supportive and valuation/dislocation is favorable
    - SELL when trend is poor and/or local premium is extreme
    - HOLD otherwise

    We keep output shape compatible with MomentumSignal.
    """

    # 1) Strong bullish trend + not overbought
    if trend_state == "STRONG_BULL":
        if spread_state == "VERY_RICH_LOCAL":
            return "HOLD", "Strong trend, but local premium is too rich to chase"
        if stretch_state == "OVERBOUGHT" and spread_state in {"RICH_LOCAL", "VERY_RICH_LOCAL"}:
            return "HOLD", "Trend is strong, but both momentum and local premium look stretched"
        return "BUY", "Trend is strong and conditions are still supportive for adding"

    # 2) Bullish / supportive trend with local discount
    if trend_state == "BULL":
        if spread_state in {"VERY_CHEAP_LOCAL", "CHEAP_LOCAL"}:
            return "BUY", "Trend is supportive and local pricing is favorable"
        if stretch_state == "OVERSOLD":
            return "BUY", "Short-term pullback within a supportive broader trend"
        if spread_state == "VERY_RICH_LOCAL":
            return "HOLD", "Trend is positive, but local premium is extreme"
        return "HOLD", "Trend is mildly positive, but edge is not strong enough yet"

    # 3) Neutral trend can still buy on meaningful local discount
    if trend_state == "NEUTRAL":
        if spread_state == "VERY_CHEAP_LOCAL" and stretch_state != "OVERBOUGHT":
            return "BUY", "Trend is mixed, but local discount is unusually attractive"
        if spread_state == "VERY_RICH_LOCAL":
            return "HOLD", "Trend is mixed and local premium is too high to add"
        return "HOLD", "No strong directional edge"

    # 4) Bearish trend
    if trend_state == "BEAR":
        if spread_state == "VERY_RICH_LOCAL":
            return "SELL", "Weak trend and local premium remains unusually high"
        if stretch_state == "OVERBOUGHT":
            return "SELL", "Weak trend with limited reward-to-risk"
        return "HOLD", "Trend is soft, but not weak enough for a firm exit signal"

    # 5) Strong bearish trend
    if trend_state == "STRONG_BEAR":
        if spread_state in {"RICH_LOCAL", "VERY_RICH_LOCAL"}:
            return "SELL", "Bearish trend with unfavorable local pricing"
        if stretch_state in {"NEUTRAL", "OVERBOUGHT"}:
            return "SELL", "Broad trend breakdown across timeframes"
        if stretch_state == "OVERSOLD":
            return "HOLD", "Trend is bearish, but price already looks quite washed out"
        return "SELL", "Broad trend breakdown across timeframes"

    return "HOLD", "No strong directional edge"


def _signal_conviction(sig: MomentumSignal) -> float:
    score = 0.0
    rsi_val = _safe_rsi(sig.rsi_14)

    if sig.ma_30 and sig.ma_30 != 0:
        ma_gap_pct = abs(sig.ma_7 - sig.ma_30) / sig.ma_30
        score += min(ma_gap_pct / 0.03, 0.25)

    if sig.ma_90 and sig.ma_90 != 0:
        regime_gap_pct = abs(sig.ma_30 - sig.ma_90) / sig.ma_90
        score += min(regime_gap_pct / 0.05, 0.20)

    score += min(abs(sig.z_score) / 3.0, 0.25)

    if rsi_val is not None:
        if rsi_val > 70:
            score += min((rsi_val - 70) / 30, 0.10)
        elif rsi_val < 30:
            score += min((30 - rsi_val) / 30, 0.10)

    if sig.spread_z is not None:
        score += min(abs(sig.spread_z) / 4.0, 0.10)

    if sig.signal in {"BUY", "SELL"}:
        score += 0.15

    return round(min(score, 1.0), 3)


def _score_reduce_strength(sig: MomentumSignal, asset_weight: float) -> float:
    score = 0.0
    rsi_val = _safe_rsi(sig.rsi_14)

    # Trend deterioration
    if sig.ma_7 < sig.ma_30:
        score += 0.75
    if sig.ma_30 < sig.ma_90:
        score += 1.00
    if sig.ma_7 < sig.ma_30 < sig.ma_90:
        score += 0.50

    # Downside breakdown
    if sig.z_score <= -1.0:
        score += 0.50
    if sig.z_score <= -2.0:
        score += 0.50

    # Trim-on-richness
    if sig.z_score >= 1.5:
        score += 0.50
    if rsi_val is not None and rsi_val >= 70:
        score += 0.50

    # Local richness
    if sig.spread_z is not None:
        if sig.spread_z >= 2.0:
            score += 1.00
        elif sig.spread_z >= 1.0:
            score += 0.50

    # Portfolio concentration
    if asset_weight > 0.50:
        score += 1.00
    elif asset_weight > 0.30:
        score += 0.50

    return round(score, 2)


def _score_buy_strength(sig: MomentumSignal, asset_weight: float) -> float:
    score = 0.0
    rsi_val = _safe_rsi(sig.rsi_14)

    if sig.ma_7 > sig.ma_30:
        score += 0.75
    if sig.ma_30 > sig.ma_90:
        score += 0.75
    if sig.ma_7 > sig.ma_30 > sig.ma_90:
        score += 0.50

    if -1.0 <= sig.z_score <= 1.0:
        score += 0.50
    elif sig.z_score < -1.0:
        score += 0.50

    if rsi_val is not None and rsi_val <= 30:
        score += 0.50

    if sig.spread_z is not None:
        if sig.spread_z <= -2.0:
            score += 1.00
        elif sig.spread_z <= -1.0:
            score += 0.50
        elif sig.spread_z >= 2.0:
            score -= 1.00
        elif sig.spread_z >= 1.0:
            score -= 0.50

    if asset_weight > 0.50:
        score -= 0.75
    elif asset_weight > 0.30:
        score -= 0.35

    return round(max(score, 0.0), 2)


def _map_reduce_size_band(score: float) -> tuple[str, str, str]:
    if score >= 3.0:
        return ("STRONG", "30-40%", "Consider a meaningful reduction to lock in gains or reduce risk.")
    elif score >= 1.75:
        return ("MODERATE", "15-25%", "Consider trimming part of the position.")
    elif score >= 1.0:
        return ("LIGHT", "5-10%", "Consider a light reduction if you want to derisk.")
    return ("LIGHT", "0-5%", "Only a small trim is justified, if any.")


def _map_buy_size_band(score: float) -> tuple[str, str, str]:
    if score >= 2.0:
        return ("MODERATE", "10-20%", "Consider a moderate addition.")
    elif score >= 1.0:
        return ("LIGHT", "5-10%", "Consider a small addition.")
    return ("LIGHT", "0-5%", "Only a very small addition is justified, if any.")


def _estimate_value_range(asset, portfolio, current_prices, pct_range) -> Optional[str]:
    if not pct_range or asset not in portfolio or asset not in current_prices:
        return None

    try:
        low_p, high_p = [float(x) / 100 for x in pct_range.replace("%", "").split("-")]
        pos_val = (
            float(portfolio[asset]["quantity"])
            * float(portfolio[asset].get("to_gram_factor", 1.0))
            * float(current_prices[asset])
        )
        low_vnd = round((pos_val * low_p) / 100_000) * 100_000
        high_vnd = round((pos_val * high_p) / 100_000) * 100_000
        return f"{int(low_vnd):,}-{int(high_vnd):,} VND"
    except Exception:
        return None


def generate_trade_recommendations(
    signals: list[MomentumSignal],
    portfolio: dict[str, dict],
    current_prices: dict[str, float],
    spread_insights: list[SpreadInsight] = None,
) -> list[TradeRecommendation]:
    recs = []
    total_value = _compute_portfolio_value(portfolio, current_prices)
    spread_map = {s.asset_name: s for s in (spread_insights or [])}

    for sig in signals:
        asset = sig.asset
        if asset not in portfolio or asset not in current_prices:
            continue

        asset_weight = _compute_asset_weight(asset, portfolio, current_prices, total_value)
        conviction = _signal_conviction(sig)
        spread_info = spread_map.get(asset)

        if sig.signal == "BUY":
            buy_score = _score_buy_strength(sig, asset_weight)
            action, urgency = "BUY", "MEDIUM"
            size_band, pct_range, size_hint = _map_buy_size_band(buy_score)

            if asset_weight > 0.50:
                action, urgency, size_band, pct_range = "HOLD", "LOW", None, None
                size_hint = "Signal is constructive, but the position is already highly concentrated."

            value_range = _estimate_value_range(asset, portfolio, current_prices, pct_range)
            rationale = sig.reason + (f"; {spread_info.recommendation_hint}" if spread_info else "")

        elif sig.signal == "SELL":
            reduce_score = _score_reduce_strength(sig, asset_weight)

            if reduce_score >= 3.0:
                action, urgency = "SELL", "HIGH"
            else:
                action = "REDUCE"
                urgency = "HIGH" if reduce_score >= 2.0 else "MEDIUM"

            size_band, pct_range, size_hint = _map_reduce_size_band(reduce_score)
            value_range = _estimate_value_range(asset, portfolio, current_prices, pct_range)
            rationale = sig.reason + (f"; {spread_info.recommendation_hint}" if spread_info else "")

        else:
            action, urgency, size_band, pct_range, value_range = "HOLD", "LOW", None, None, None
            size_hint = "No action needed unless you are rebalancing for risk reasons."
            rationale = sig.reason + (f"; {spread_info.recommendation_hint}" if spread_info else "")

        recs.append(
            TradeRecommendation(
                asset=asset,
                action=action,
                urgency=urgency,
                size_band=size_band,
                size_hint=size_hint,
                estimated_pct_range=pct_range,
                value_vnd_range=value_range,
                rationale=rationale,
                conviction=conviction,
            )
        )

    return recs


def generate_signals(
    prices_df: pd.DataFrame,
    spread_insights: list[SpreadInsight] = None,
) -> list[MomentumSignal]:
    from analytics.metrics import PortfolioMetricsEngine

    engine = PortfolioMetricsEngine(prices_df)
    signals = []
    spread_map = {s.asset_name: s for s in (spread_insights or [])}

    for asset in prices_df.columns:
        px = prices_df[asset].dropna()
        if len(px) < 90:
            continue

        ma_7 = float(px.rolling(7).mean().iloc[-1])
        ma_30 = float(px.rolling(30).mean().iloc[-1])
        ma_90 = float(px.rolling(90).mean().iloc[-1])
        std30 = float(px.rolling(30).std().iloc[-1])

        z_score = round((px.iloc[-1] - ma_30) / std30, 3) if std30 > 0 else 0.0
        rsi_val = engine.rsi(asset)
        rsi_safe = _safe_rsi(rsi_val)

        spread = spread_map.get(asset)
        spread_z = float(spread.z_score_30d) if spread and spread.z_score_30d is not None else None

        trend_state = _classify_trend(ma_7, ma_30, ma_90)
        stretch_state = _classify_stretch(z_score, rsi_safe)
        spread_state = _classify_spread(spread)

        signal, policy_reason = _decide_signal(
            trend_state=trend_state,
            stretch_state=stretch_state,
            spread_state=spread_state,
        )

        detail_reason = _build_reason(
            trend_state=trend_state,
            stretch_state=stretch_state,
            spread_state=spread_state,
            spread=spread,
        )

        reason = f"{policy_reason}; {detail_reason}"

        signals.append(
            MomentumSignal(
                asset=asset,
                signal=signal,
                reason=reason,
                ma_7=round(ma_7, 2),
                ma_30=round(ma_30, 2),
                ma_90=round(ma_90, 2),
                z_score=z_score,
                rsi_14=round(rsi_safe, 2) if rsi_safe is not None else None,
                spread_z=spread_z,
                spread_signal=spread.signal if spread else None,
            )
        )

    return signals