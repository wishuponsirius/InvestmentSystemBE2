import pandas as pd
from typing import Any

from db.spread_repo import (
    fetch_latest_metal_spread,
    fetch_metal_spread_history,
)
from models.report import SpreadInsight


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        if pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def _safe_std(series: pd.Series) -> float | None:
    if series.empty:
        return None
    value = series.std()
    if pd.isna(value):
        return None
    return float(value)


async def build_metal_spread_insight(
    conn,
    asset_id: int,
    asset_name: str,
    days: int = 365,
) -> SpreadInsight:
    hist = await fetch_metal_spread_history(conn=conn, asset_id=asset_id, days=days)
    latest = await fetch_latest_metal_spread(conn=conn, asset_id=asset_id)

    if hist.empty:
        return SpreadInsight(
            asset_id=asset_id,
            asset_name=asset_name,
            current_spread_pct=None,
            mean_spread_pct_30d=None,
            z_score_30d=None,
            signal="NO_DATA",
            summary=f"Not enough spread data for {asset_name}.",
            recommendation_hint="Do not use spread as a decision factor.",
        )

    hist = hist.copy()
    hist["spread_pct"] = pd.to_numeric(hist["spread_pct"], errors="coerce")
    hist = hist.dropna(subset=["spread_pct"])

    if hist.empty:
        return SpreadInsight(
            asset_id=asset_id,
            asset_name=asset_name,
            current_spread_pct=None,
            mean_spread_pct_30d=None,
            z_score_30d=None,
            signal="NO_DATA",
            summary=f"Spread data for {asset_name} is incomplete.",
            recommendation_hint="Do not use spread as a decision factor.",
        )

    current_spread_pct = _safe_float(latest.get("spread_pct"))

    last_30 = hist.tail(30)
    mean_30 = _safe_float(last_30["spread_pct"].mean()) if not last_30.empty else None
    std_30 = _safe_std(last_30["spread_pct"]) if not last_30.empty else None

    z_score_30d = None
    if (
        current_spread_pct is not None
        and mean_30 is not None
        and std_30 is not None
        and std_30 > 0
    ):
        z_score_30d = (current_spread_pct - mean_30) / std_30

    signal = "NEUTRAL"
    summary = f"The local-vs-global spread for {asset_name} looks normal."
    recommendation_hint = (
        "Spread does not strongly support either aggressive buying or selling."
    )

    if current_spread_pct is None:
        signal = "NO_DATA"
        summary = f"Could not calculate the current spread for {asset_name}."
        recommendation_hint = "Ignore spread in the recommendation."
    else:
        if z_score_30d is not None:
            if z_score_30d >= 2:
                signal = "LOCAL_PREMIUM_VERY_HIGH"
                summary = (
                    f"Local {asset_name} price is trading far above global reference "
                    f"({current_spread_pct:.2f}% premium, unusually high vs the last 30 days)."
                )
                recommendation_hint = (
                    "If the user already holds this asset, consider partial profit-taking "
                    "or avoid chasing new buys at current local premium."
                )
            elif z_score_30d >= 1:
                signal = "LOCAL_PREMIUM_HIGH"
                summary = (
                    f"Local {asset_name} price is above global reference "
                    f"({current_spread_pct:.2f}% premium), higher than usual recently."
                )
                recommendation_hint = (
                    "Slight caution for new buying; stronger support for hold than aggressive buy."
                )
            elif z_score_30d <= -2:
                signal = "LOCAL_DISCOUNT_VERY_HIGH"
                summary = (
                    f"Local {asset_name} price is well below its usual premium relative to global price "
                    f"({current_spread_pct:.2f}%)."
                )
                recommendation_hint = (
                    "This may support accumulation if other indicators are also favorable."
                )
            elif z_score_30d <= -1:
                signal = "LOCAL_DISCOUNT"
                summary = (
                    f"Local {asset_name} premium versus global price is lower than usual "
                    f"({current_spread_pct:.2f}%)."
                )
                recommendation_hint = (
                    "This can modestly support buy/hold decisions if trend conditions are healthy."
                )
        else:
            if current_spread_pct >= 5:
                signal = "LOCAL_PREMIUM_HIGH"
                summary = (
                    f"Local {asset_name} trades at a notable premium to global price "
                    f"({current_spread_pct:.2f}%)."
                )
                recommendation_hint = (
                    "Use caution when recommending new buys based only on momentum."
                )
            elif current_spread_pct <= 0:
                signal = "LOCAL_DISCOUNT"
                summary = (
                    f"Local {asset_name} is at or below global reference "
                    f"({current_spread_pct:.2f}%)."
                )
                recommendation_hint = (
                    "This may slightly favor accumulation over profit-taking."
                )

    return SpreadInsight(
        asset_id=asset_id,
        asset_name=asset_name,
        current_spread_pct=current_spread_pct,
        mean_spread_pct_30d=mean_30,
        z_score_30d=z_score_30d,
        signal=signal,
        summary=summary,
        recommendation_hint=recommendation_hint,
    )