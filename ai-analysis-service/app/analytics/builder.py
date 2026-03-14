import asyncpg

from models.report import (
    PortfolioReport,
    AllocationItem,
    PerformanceItem,
    RiskMetrics,
)
from analytics.metrics import PortfolioMetricsEngine
from analytics.signals import generate_signals 
# generate_trade_recommendations
from db.price_repo import fetch_price_matrix, fetch_latest_prices
from db.portfolio_repo import fetch_portfolio, fetch_asset_ids
from ai.gemini import explain_report


async def build_portfolio_report(
    user_id: str,
    conn: asyncpg.Connection,
) -> PortfolioReport:
    asset_ids = await fetch_asset_ids(conn, user_id)
    if not asset_ids:
        raise ValueError(f"No portfolio found for user {user_id}")

    portfolio = await fetch_portfolio(conn, user_id)
    prices_df = await fetch_price_matrix(conn, asset_ids)
    current_prices = await fetch_latest_prices(conn, asset_ids)

    if prices_df.empty:
        raise ValueError("No price data available for this portfolio")

    engine = PortfolioMetricsEngine(prices_df)

    # Current total value
    total_value = 0.0
    for asset, info in portfolio.items():
        if asset not in current_prices:
            continue
        total_value += info["quantity"] * info["to_gram_factor"] * current_prices[asset]

    if total_value <= 0:
        raise ValueError("Portfolio value is zero or invalid")

    # Weights
    weights: dict[str, float] = {}
    for asset, info in portfolio.items():
        if asset not in current_prices:
            continue
        value = info["quantity"] * info["to_gram_factor"] * current_prices[asset]
        weights[asset] = value / total_value

    # Allocation
    allocation = []
    for asset, info in portfolio.items():
        if asset not in current_prices:
            continue
        value_vnd = info["quantity"] * info["to_gram_factor"] * current_prices[asset]
        allocation.append(
            AllocationItem(
                asset=asset,
                weight=round(weights.get(asset, 0.0), 6),
                value_vnd=round(value_vnd, 2),
                quantity=info["quantity"],
                unit_symbol=info["unit_symbol"],
            )
        )

    # Performance + portfolio return
    performance = []
    cost_basis = 0.0
    current_total_from_perf = 0.0

    for asset, info in portfolio.items():
        if asset not in current_prices:
            continue

        cp = current_prices[asset]  # per gram
        ep = info["entry_price"]    # assumed original unit total price
        factor = info["to_gram_factor"]
        qty = info["quantity"]

        ep_per_gram = (ep / factor) if ep else None

        current_value = qty * factor * cp
        current_total_from_perf += current_value

        asset_cost = qty * ep if ep else 0.0
        cost_basis += asset_cost

        pnl = ((cp - ep_per_gram) * qty * factor) if ep_per_gram else 0.0
        ret = ((cp - ep_per_gram) / ep_per_gram) if ep_per_gram else 0.0

        performance.append(
            PerformanceItem(
                asset=asset,
                entry_price=round(ep_per_gram, 6) if ep_per_gram is not None else None,
                current_price=round(cp, 6),
                pnl=round(pnl, 2),
                return_pct=round(ret * 100, 4),
            )
        )

    total_return_pct = round(
        ((current_total_from_perf - cost_basis) / cost_basis) * 100, 4
    ) if cost_basis > 0 else 0.0

    best = max(performance, key=lambda x: x.return_pct).asset if performance else ""
    worst = min(performance, key=lambda x: x.return_pct).asset if performance else ""

    # Risk
    corr = engine.correlation_matrix()
    portfolio_vol = engine.portfolio_volatility(weights)
    portfolio_var = engine.portfolio_var_95(weights, total_value)
    portfolio_sharpe = engine.portfolio_sharpe_ratio(weights)
    portfolio_drawdown = engine.portfolio_max_drawdown(weights)

    risk = RiskMetrics(
        volatility_annualized=round(portfolio_vol, 6),
        var_95_1day=round(portfolio_var, 2),
        sharpe_ratio=portfolio_sharpe,
        max_drawdown=round(portfolio_drawdown, 6),
        correlation_matrix=corr,
    )

    # Signals + trade recommendations
    signals = generate_signals(prices_df)
    # trade_recs = generate_trade_recommendations(
    #     signals=signals,
    #     portfolio=portfolio,
    #     current_prices=current_prices,
    # )

    # Simple equal-weight rebalance target
    n = len(weights)
    rebalance_targets = {asset: round(1 / n, 6) for asset in weights} if n > 0 else {}

    # Alerts
    alerts = []
    div_score = engine.diversification_score(weights)

    if div_score < 0.4:
        alerts.append("Portfolio is dangerously concentrated (diversification score < 0.4)")

    if total_value > 0 and abs(portfolio_var) / total_value > 0.03:
        alerts.append("1-day VaR exceeds 3% of total portfolio value")

    for p in performance:
        if p.return_pct < -20:
            alerts.append(f"{p.asset} is down more than 20% from entry price")

    report = PortfolioReport(
        user_id=user_id,
        portfolio_value_vnd=round(total_value, 2),
        allocation=allocation,
        performance=performance,
        total_return_pct=total_return_pct,
        best_performer=best,
        worst_performer=worst,
        risk=risk,
        diversification_score=div_score,
        signals=signals,
        rebalance_target_weights=rebalance_targets,
        alerts=alerts,
    )

    try:
        explanation, summary = await explain_report(report)
        report.explanation = explanation or ""
        report.recommendation_summary = summary or ""
    except Exception:
        report.explanation = ""
        report.recommendation_summary = ""

    return report