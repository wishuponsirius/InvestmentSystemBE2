import pandas as pd
from models.report import MomentumSignal, TradeRecommendation


def generate_signals(prices_df: pd.DataFrame) -> list[MomentumSignal]:
    from analytics.metrics import PortfolioMetricsEngine
    engine = PortfolioMetricsEngine(prices_df)
    signals = []

    for asset in prices_df.columns:
        px = prices_df[asset].dropna()
        if len(px) < 30:
            continue

        ma_7  = float(px.rolling(7).mean().iloc[-1])
        ma_30 = float(px.rolling(30).mean().iloc[-1])
        std30 = float(px.rolling(30).std().iloc[-1])
        z_score = round((px.iloc[-1] - ma_30) / std30, 3) if std30 > 0 else 0.0
        rsi_val = engine.rsi(asset)

        if ma_7 > ma_30 and z_score < 1.5:
            signal, reason = "BUY", "MA7 above MA30, not overextended"
        elif ma_7 < ma_30 and z_score < -1.0:
            signal, reason = "SELL", "MA7 below MA30, price below 30d mean"
        elif z_score > 2.0:
            signal, reason = "SELL", "Price >2 std devs above 30d mean"
        elif rsi_val and rsi_val > 70:
            signal, reason = "SELL", f"RSI overbought at {rsi_val}"
        elif rsi_val and rsi_val < 30:
            signal, reason = "BUY", f"RSI oversold at {rsi_val}"
        else:
            signal, reason = "HOLD", "No strong directional signal"

        signals.append(MomentumSignal(
            asset=asset,
            signal=signal,
            reason=reason,
            ma_7=round(ma_7, 2),
            ma_30=round(ma_30, 2),
            z_score=z_score,
            rsi_14=rsi_val,
        ))

    return signals


def generate_trade_recommendations(
    signals: list[MomentumSignal],
    portfolio: dict[str, dict],
    current_prices: dict[str, float],
) -> list[TradeRecommendation]:
    recs = []
    for sig in signals:
        asset = sig.asset
        if asset not in portfolio or asset not in current_prices:
            continue

        qty = portfolio[asset]["quantity"]
        price = current_prices[asset]
        factor = portfolio[asset]["to_gram_factor"]

        if sig.signal == "BUY":
            action, urgency = "BUY", "MEDIUM"
            suggested_qty = round(qty * 0.25, 6)  # suggest adding 25%
            rationale = sig.reason
        elif sig.signal == "SELL":
            action = "REDUCE" if sig.z_score < 3.0 else "SELL"
            urgency = "HIGH" if sig.z_score > 2.5 else "MEDIUM"
            suggested_qty = round(qty * 0.5, 6)   # suggest trimming 50%
            rationale = sig.reason
        else:
            action, urgency, suggested_qty = "HOLD", "LOW", 0.0
            rationale = sig.reason

        recs.append(TradeRecommendation(
            asset=asset,
            action=action,
            urgency=urgency,
            quantity=suggested_qty,
            value_vnd=round(suggested_qty * factor * price, 2),
            rationale=rationale,
        ))

    return recs