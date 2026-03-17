import asyncpg
from models.report import (
    PortfolioReport, AllocationItem, PerformanceItem, RiskMetrics,
)
from analytics.metrics import PortfolioMetricsEngine
from analytics.signals import generate_signals, generate_trade_recommendations
from db.price_repo import fetch_price_matrix, fetch_latest_prices
from db.portfolio_repo import fetch_portfolio, fetch_asset_ids, fetch_asset_name_id_map
from ai.gemini import explain_report
from analytics.spread_insight import build_metal_spread_insight

async def build_portfolio_report(
    user_id: str,
    conn: asyncpg.Connection,
) -> PortfolioReport:

    # 1. Fetch raw data
    asset_ids = await fetch_asset_ids(conn, user_id)
    if not asset_ids:
        raise ValueError(f"No portfolio found for user {user_id}")
    asset_name_id_map = await fetch_asset_name_id_map(conn, user_id)
    portfolio = await fetch_portfolio(conn, user_id)
    prices_df = await fetch_price_matrix(conn, asset_ids)
    current_prices = await fetch_latest_prices(conn, asset_ids)

    if prices_df.empty:
        raise ValueError("No price data available for this portfolio")

    # 2. Metrics engine
    engine = PortfolioMetricsEngine(prices_df)

    # 3. Portfolio valuation
    total_value = sum(
        portfolio[a]["quantity"] * portfolio[a]["to_gram_factor"] * current_prices.get(a, 0)
        for a in portfolio
    )
    weights = {
        a: (portfolio[a]["quantity"] * portfolio[a]["to_gram_factor"] * current_prices.get(a, 0)) / total_value
        for a in portfolio
        if total_value > 0
    }

    # 4. Allocation
    allocation = [
        AllocationItem(
            asset=a,
            weight=round(weights.get(a, 0), 6),
            value_vnd=round(portfolio[a]["quantity"] * portfolio[a]["to_gram_factor"] * current_prices.get(a, 0), 2),
            quantity=portfolio[a]["quantity"],
            unit_symbol=portfolio[a]["unit_symbol"],
        )
        for a in portfolio
    ]

    # 5. Performance
    performance = []
    for a, info in portfolio.items():
        if a not in current_prices:
            continue

        cp = current_prices[a]          # already per gram in VND
        ep = info["entry_price"]
        factor = info["to_gram_factor"] # e.g. chỉ→gram = 3.75

        # normalize entry_price to per-gram, same unit as current_price
        ep_per_gram = (ep / factor) if ep else None

        pnl = ((cp - ep_per_gram) * info["quantity"] * factor) if ep_per_gram else 0.0
        ret = ((cp - ep_per_gram) / ep_per_gram) if ep_per_gram else 0.0

        performance.append(PerformanceItem(
            asset=a,
            entry_price=ep_per_gram,
            current_price=cp,
            pnl=round(pnl, 2),
            return_pct=round(ret * 100, 4),
        ))

    best  = max(performance, key=lambda x: x.return_pct).asset if performance else ""
    worst = min(performance, key=lambda x: x.return_pct).asset if performance else ""

    # 6. Risk
    corr = engine.correlation_matrix()
    # Use worst single-asset VaR for simplicity; swap for portfolio_var_95 if needed
    total_var = engine.portfolio_var_95(weights, total_value)
    avg_vol = sum(engine.volatility(a) for a in portfolio) / max(len(portfolio), 1)
    avg_sharpe_vals = [engine.sharpe_ratio(a) for a in portfolio]
    avg_sharpe = sum(v for v in avg_sharpe_vals if v is not None) / max(
        len([v for v in avg_sharpe_vals if v is not None]), 1
    )
    avg_drawdown = sum(engine.max_drawdown(a) for a in portfolio) / max(len(portfolio), 1)

    risk = RiskMetrics(
        volatility_annualized=round(avg_vol, 6),
        var_95_1day=round(total_var, 2),
        sharpe_ratio=round(avg_sharpe, 4) if avg_sharpe_vals else None,
        max_drawdown=round(avg_drawdown, 6),
        correlation_matrix=corr,
    )

    
        # 8.2 Spread insights (for metal assets only)
    spread_insights = []

    for asset_name in portfolio.keys():
        normalized = asset_name.lower().strip()
        asset_id = asset_name_id_map.get(asset_name)

        if normalized in {"gold", "silver"} and asset_id is not None:
            insight_dict = await build_metal_spread_insight(
                conn=conn,
                asset_id=asset_id,
                asset_name=asset_name,
                days=365,
            )
            spread_insights.append(insight_dict)

    # 7. Signals & recommendations
    signals = generate_signals(prices_df, spread_insights)
    trade_recs = generate_trade_recommendations(signals, portfolio, current_prices, spread_insights)

    # 8. Alerts
    alerts = []
    div_score = engine.diversification_score(weights)
    if div_score < 0.4:
        alerts.append("Portfolio is dangerously concentrated (diversification score < 0.4)")
    if total_value > 0 and abs(total_var) / total_value > 0.03:
        alerts.append("1-day VaR exceeds 3% of total portfolio value")
    for p in performance:
        if p.return_pct < -20:
            alerts.append(f"{p.asset} is down more than 20% from entry price")


    # 9. Simple equal-weight rebalance target
    n = len(portfolio)
    rebalance_targets = {a: round(1 / n, 6) for a in portfolio} if n > 0 else {}

    # 10. Assemble draft report (no AI text yet)
    report = PortfolioReport(
        user_id=user_id,
        portfolio_value_vnd=round(total_value, 2),
        allocation=allocation,
        performance=performance,
        total_return_pct=round(
            sum(p.return_pct for p in performance) / max(len(performance), 1), 4
        ),
        best_performer=best,
        worst_performer=worst,
        risk=risk,
        diversification_score=div_score,
        signals=signals,
        spread_insights=spread_insights,
        trade_recommendations=trade_recs,
        alerts=alerts,
    )

    # 11. AI explanation (non-fatal if it fails)
    explanation, summary = await explain_report(report)
    report.explanation = explanation
    report.recommendation_summary = summary

    return report