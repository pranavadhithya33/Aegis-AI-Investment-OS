"""
backend/routers/portfolio_honest.py
Honest Portfolio Optimization + Valuation Education
NO stock picking. NO BUY/SELL/HOLD. Math decides. AI explains.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
from pypfopt import EfficientFrontier, risk_models, expected_returns
from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices

router = APIRouter(prefix="/api/honest", tags=["Honest Portfolio"])

# ============================================
# CONFIG: Asset Universe (ETFs only for beginners)
# ============================================
BEGINNER_ASSETS = {
    "NIFTYBEES.NS": {"name": "Nifty 50 ETF", "category": "india_large", "icon": "🇮🇳"},
    "SETFNIF50.NS": {"name": "Nifty Next 50", "category": "india_mid", "icon": "🏭"},
    "GOLDBEES.NS": {"name": "Gold ETF", "category": "gold", "icon": "🥇"},
    "LIQUIDBEES.NS": {"name": "Liquid ETF", "category": "debt", "icon": "💧"},
    "SPY": {"name": "S&P 500 (US)", "category": "us_large", "icon": "🇺🇸"},
    "QQQ": {"name": "Nasdaq 100 (US)", "category": "us_tech", "icon": "🚀"},
}

# ============================================
# SCHEMAS
# ============================================
class RiskProfile(BaseModel):
    risk_tolerance: int = Field(5, ge=1, le=10, description="1=Very Safe, 10=Maximum Risk")
    monthly_investment: int = Field(5000, ge=1000, description="Monthly SIP amount in INR")
    goal: Literal["wealth", "house", "income"] = "wealth"
    years: int = Field(10, ge=1, le=40)

class AssetAllocation(BaseModel):
    ticker: str
    name: str
    category: str
    percentage: float
    monthly_amount: int
    icon: str
    why: str  # Educational explanation

class PortfolioRecommendation(BaseModel):
    allocations: List[AssetAllocation]
    risk_metrics: dict
    projections: dict
    ai_rationale: str
    warning: str

class ValuationRequest(BaseModel):
    ticker: str = Field(..., description="Stock ticker to analyze, e.g., TCS.NS")

class ValuationMetric(BaseModel):
    name: str
    value: Optional[float]
    industry_avg: Optional[float]
    explanation: str
    red_flag: Optional[str] = None
    context: str

class ValuationResponse(BaseModel):
    ticker: str
    company_name: str
    metrics: List[ValuationMetric]
    ai_summary: str
    user_action_prompt: str

# ============================================
# PORTFOLIO OPTIMIZATION (Deterministic)
# ============================================
@router.post("/recommend", response_model=PortfolioRecommendation)
def recommend_portfolio(profile: RiskProfile):
    """
    Generate a mathematically optimal portfolio allocation.
    NO AI prediction. Pure MVO + risk-parity math.
    """
    tickers = list(BEGINNER_ASSETS.keys())

    # Fetch 3 years of data
    end = datetime.today()
    start = end - timedelta(days=365*3)
    prices = yf.download(tickers, start=start, end=end, progress=False)["Close"]
    prices = prices.dropna(axis=1, how="all")

    # Calculate expected returns and covariance
    mu = expected_returns.mean_historical_return(prices)
    S = risk_models.sample_cov(prices)

    # Risk-adjusted optimization
    ef = EfficientFrontier(mu, S)

    if profile.risk_tolerance <= 3:
        ef.min_volatility()  # Conservative
    elif profile.risk_tolerance <= 7:
        ef.max_sharpe()      # Balanced
    else:
        target_vol = 0.15 + (profile.risk_tolerance - 7) * 0.025
        ef.efficient_risk(target_volatility=target_vol)

    weights = ef.clean_weights()
    perf = ef.portfolio_performance(verbose=False)

    # Calculate monthly amounts
    allocations = []
    for ticker, weight in weights.items():
        if weight > 0.001:
            info = BEGINNER_ASSETS.get(ticker, {"name": ticker, "category": "other", "icon": "📊"})
            allocations.append(AssetAllocation(
                ticker=ticker,
                name=info["name"],
                category=info["category"],
                percentage=round(weight * 100, 1),
                monthly_amount=int(round(weight * profile.monthly_investment)),
                icon=info["icon"],
                why=_get_why_text(info["category"], profile.risk_tolerance)
            ))

    # Risk metrics
    returns = prices.pct_change().dropna()
    portfolio_returns = sum(returns[t] * weights[t] for t in weights if t in returns.columns)
    max_dd = _max_drawdown(portfolio_returns)

    # Projections (simple compound interest)
    r = perf[0]  # Expected annual return
    projections = {
        "5_years": int(profile.monthly_investment * 12 * (((1+r)**5 - 1) / r)),
        "10_years": int(profile.monthly_investment * 12 * (((1+r)**10 - 1) / r)),
        "20_years": int(profile.monthly_investment * 12 * (((1+r)**20 - 1) / r)),
    }

    # AI Rationale (educational, not predictive)
    ai_rationale = _generate_rationale(profile, allocations, perf)

    return PortfolioRecommendation(
        allocations=allocations,
        risk_metrics={
            "expected_return": round(perf[0]*100, 1),
            "volatility": round(perf[1]*100, 1),
            "sharpe_ratio": round(perf[2], 2),
            "max_drawdown": round(max_dd*100, 1),
        },
        projections=projections,
        ai_rationale=ai_rationale,
        warning="These are estimates based on historical data. Past performance does not guarantee future results."
    )

def _get_why_text(category: str, risk: int) -> str:
    """Educational explanation for why this asset is included."""
    texts = {
        "india_large": "Owns India's 50 biggest companies. The backbone of the Indian economy.",
        "india_mid": "Smaller, faster-growing Indian companies. Higher risk, higher potential reward.",
        "gold": "Protects your money when the stock market crashes. Acts like insurance.",
        "debt": "Safe, steady returns. The anchor that keeps your portfolio stable.",
        "us_large": "America's biggest 500 companies. Global diversification outside India.",
        "us_tech": "US technology giants. High growth, but volatile. Only for risk-takers.",
    }
    return texts.get(category, "Diversification asset.")

def _max_drawdown(returns: pd.Series) -> float:
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    return drawdown.min()

def _generate_rationale(profile: RiskProfile, allocations: List[AssetAllocation], perf: tuple) -> str:
    """Generate educational rationale. No predictions."""
    risk_label = {1:"Very Safe", 2:"Conservative", 3:"Cautious", 4:"Moderate", 5:"Balanced",
                  6:"Growth", 7:"Aggressive", 8:"Very Aggressive", 9:"Speculative", 10:"Maximum Risk"}.get(profile.risk_tolerance, "Balanced")

    has_gold = any(a.category == "gold" for a in allocations)
    has_debt = any(a.category == "debt" for a in allocations)
    has_us = any(a.category in ["us_large", "us_tech"] for a in allocations)

    parts = [
        f"You chose a **{risk_label}** profile with a **{profile.years}-year** horizon.",
        "",
        "Here's why this allocation makes mathematical sense:",
        "",
        f"• **Expected return:** {perf[0]*100:.1f}% per year (historical average, not a promise).",
        f"• **Volatility:** {perf[1]*100:.1f}% — your portfolio might swing up or down by this much in a year.",
        f"• **Sharpe Ratio:** {perf[2]:.2f} — how much return you get per unit of risk. Above 1.0 is good.",
        "",
    ]

    if has_gold:
        parts.append("• **Gold** is included because it often rises when stocks fall. It won't make you rich, but it helps you sleep.")
    if has_debt:
        parts.append("• **Liquid/Debt** funds act as your emergency reserve within the portfolio. Stable, boring, essential.")
    if has_us:
        parts.append("• **US exposure** protects you if the Indian economy slows down. Currency risk exists, but diversification is worth it.")

    parts.extend([
        "",
        "**The most important number:** If you stay consistent for 20 years, compounding does the heavy lifting.",
        "The AI didn't pick 'winning' stocks. It spread your money so no single company can ruin you.",
    ])

    return "\n".join(parts)

# ============================================
# VALUATION EDUCATION (NOT stock picking)
# ============================================
@router.post("/valuation-education", response_model=ValuationResponse)
def valuation_education(req: ValuationRequest):
    """
    Educational valuation analysis for ANY stock.
    NEVER says BUY/SELL/HOLD. Only teaches metrics.
    """
    ticker = req.ticker.upper()

    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")

        if not info or hist.empty:
            raise HTTPException(404, f"Could not fetch data for {ticker}")

        # Build metrics
        metrics = []

        # P/E Ratio
        pe = info.get("trailingPE")
        sector_pe = _get_sector_avg_pe(info.get("sector", "Unknown"))
        metrics.append(ValuationMetric(
            name="P/E Ratio (Price to Earnings)",
            value=round(pe, 1) if pe else None,
            industry_avg=sector_pe,
            explanation="How much you pay for ₹1 of annual profit. Like paying ₹28 for a company that earns ₹1/year.",
            red_flag="Very high P/E (>40) means investors expect massive growth. If growth slows, the stock can crash." if pe and pe > 40 else None,
            context=f"IT sector average is ~{sector_pe}. This company is {'above' if pe and sector_pe and pe > sector_pe else 'below'} average."
        ))

        # P/B Ratio
        pb = info.get("priceToBook")
        metrics.append(ValuationMetric(
            name="P/B Ratio (Price to Book)",
            value=round(pb, 1) if pb else None,
            industry_avg=3.0,
            explanation="How much you pay for ₹1 of company assets. Useful for banks and manufacturing. Less useful for tech.",
            red_flag="Very low P/B (<1) might mean the market thinks assets are overvalued or the company is in trouble." if pb and pb < 1 else None,
            context="Banks typically trade at 2-3x book. Tech companies often trade at 10x+ because their real assets are people and code, not factories."
        ))

        # ROE
        roe = info.get("returnOnEquity")
        metrics.append(ValuationMetric(
            name="ROE (Return on Equity)",
            value=round(roe*100, 1) if roe else None,
            industry_avg=15.0,
            explanation="How efficiently the company turns shareholder money into profit. ₹100 invested → ₹15 profit = 15% ROE.",
            red_flag="ROE above 25% for non-tech companies might mean high debt is inflating the number." if roe and roe > 0.25 else None,
            context="Above 15% is generally good. Below 10% suggests the company isn't using money efficiently."
        ))

        # Debt/Equity
        de = info.get("debtToEquity")
        metrics.append(ValuationMetric(
            name="Debt-to-Equity Ratio",
            value=round(de, 2) if de else None,
            industry_avg=0.5,
            explanation="How much debt the company has vs. shareholder money. Higher = more risk if interest rates rise.",
            red_flag="D/E above 2.0 is dangerous. The company might struggle to pay debts during a recession." if de and de > 2.0 else None,
            context="Capital-intensive industries (infrastructure, real estate) naturally have higher D/E. Software companies should have very low D/E."
        ))

        # 52-week range
        high = info.get("fiftyTwoWeekHigh")
        low = info.get("fiftyTwoWeekLow")
        current = info.get("currentPrice")
        if high and low and current:
            pct = (current - low) / (high - low) * 100
            metrics.append(ValuationMetric(
                name="52-Week Position",
                value=round(pct, 1),
                industry_avg=None,
                explanation="Where the current price sits between the year's high and low. Not a valuation metric, but useful context.",
                red_flag=None,
                context=f"At {pct:.0f}% of its yearly range. {'Near the top — be cautious of buying at peaks.' if pct > 80 else 'Near the bottom — could be a bargain or a value trap.' if pct < 20 else 'Middle of the range.'}"
            ))

        # AI Summary (educational only)
        ai_summary = _generate_valuation_summary(info, metrics)

        return ValuationResponse(
            ticker=ticker,
            company_name=info.get("longName", ticker),
            metrics=metrics,
            ai_summary=ai_summary,
            user_action_prompt="Use these metrics as ONE piece of your research. Read the annual report, check promoter holdings, and understand the business before investing."
        )

    except Exception as e:
        raise HTTPException(500, f"Error analyzing {ticker}: {str(e)}")

def _get_sector_avg_pe(sector: str) -> float:
    """Rough sector averages for India. Educational only."""
    avgs = {
        "Technology": 25.0,
        "Financial Services": 18.0,
        "Healthcare": 22.0,
        "Consumer Cyclical": 28.0,
        "Energy": 12.0,
        "Industrials": 20.0,
        "Communication Services": 20.0,
    }
    return avgs.get(sector, 20.0)

def _generate_valuation_summary(info: dict, metrics: List[ValuationMetric]) -> str:
    """Educational summary. NEVER says buy/sell."""
    name = info.get("longName", "This company")
    parts = [f"**{name}** — Understanding the Numbers\n\n"]

    parts.append("Valuation metrics are like a health checkup. They tell you what the market *currently* thinks, not what will happen.\n\n")

    red_flags = [m for m in metrics if m.red_flag]
    if red_flags:
        parts.append("**⚠️ Red Flags to Investigate:**\n")
        for m in red_flags:
            parts.append(f"• {m.name}: {m.red_flag}\n")
        parts.append("\n")

    parts.append("**🧠 How to Think About This:**\n")
    parts.append("1. Cheap stocks are often cheap for a reason. The market isn't stupid.\n")
    parts.append("2. Expensive stocks can stay expensive for years if they keep growing.\n")
    parts.append("3. One metric never tells the full story. Look at trends over 5 years, not just today.\n")
    parts.append("4. The best investors spend 80% of their time understanding the BUSINESS, not the ratios.\n\n")

    parts.append("**Remember:** These numbers are historical. The future depends on management decisions, competition, and luck. No AI can predict that.")

    return "\n".join(parts)
