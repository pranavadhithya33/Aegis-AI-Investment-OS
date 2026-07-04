"use client";

import React, { useState, useEffect } from "react";
import { 
  DollarSign, 
  Percent, 
  PlusCircle, 
  Briefcase, 
  TrendingUp,
  AlertCircle
} from "lucide-react";

interface DashboardTabProps {
  portfolioId: number;
  refreshTrigger: number;
  setRefreshTrigger: React.Dispatch<React.SetStateAction<number>>;
}

export default function DashboardTab({ portfolioId, refreshTrigger, setRefreshTrigger }: DashboardTabProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // States for API data
  const [perfMetrics, setPerfMetrics] = useState<any>(null);
  const [holdings, setHoldings] = useState<any[]>([]);
  const [dividends, setDividends] = useState<any>(null);
  const [assets, setAssets] = useState<any[]>([]);

  // Transaction form states
  const [txType, setTxType] = useState("DEPOSIT");
  const [ticker, setTicker] = useState("AAPL");
  const [size, setSize] = useState("");
  const [price, setPrice] = useState("");
  const [commission, setCommission] = useState("5.00");
  const [formMsg, setFormMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Fetch all portfolio and asset data
  useEffect(() => {
    async function fetchData() {
      if (!portfolioId) return;
      setLoading(true);
      setError(null);
      try {
        // Fetch performance metrics
        const perfRes = await fetch(`http://127.0.0.1:8000/api/portfolio/${portfolioId}/performance`);
        const perfData = await perfRes.json();
        
        // Fetch holdings
        const holdingsRes = await fetch(`http://127.0.0.1:8000/api/portfolio/${portfolioId}/holdings`);
        const holdingsData = await holdingsRes.json();

        // Fetch dividends
        const divRes = await fetch(`http://127.0.0.1:8000/api/portfolio/${portfolioId}/dividends`);
        const divData = await divRes.json();

        // Fetch active asset universe for dropdown selection
        const assetsRes = await fetch("http://127.0.0.1:8000/api/assets/");
        const assetsData = await assetsRes.json();

        setPerfMetrics(perfData);
        setHoldings(holdingsData);
        setDividends(divData);
        setAssets(assetsData);
      } catch (err: any) {
        console.error(err);
        setError("Failed to query portfolio metrics from Aegis API.");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [portfolioId, refreshTrigger]);

  // Handle transaction submit
  const handleAddTransaction = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormMsg(null);

    const payload: any = {
      transaction_type: txType,
      size: parseFloat(size),
      commission: parseFloat(commission),
    };

    if (txType === "BUY" || txType === "SELL") {
      payload.asset_ticker = ticker;
      payload.price = parseFloat(price);
      if (isNaN(payload.price) || payload.price <= 0) {
        setFormMsg({ type: "error", text: "Please enter a valid price." });
        return;
      }
    }

    if (isNaN(payload.size) || payload.size <= 0) {
      setFormMsg({ type: "error", text: "Please enter a valid size." });
      return;
    }

    try {
      const res = await fetch(`http://127.0.0.1:8000/api/portfolio/${portfolioId}/transaction`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Transaction submission failed.");
      }

      setFormMsg({ type: "success", text: "Transaction successfully logged and portfolio rebalanced." });
      setSize("");
      setPrice("");
      setRefreshTrigger(prev => prev + 1);
    } catch (err: any) {
      setFormMsg({ type: "error", text: err.message || "Network error." });
    }
  };

  if (loading && holdings.length === 0) {
    return <div className="loading-state">Syncing Aegis Portfolio Engine...</div>;
  }

  if (error) {
    return (
      <div className="error-panel glass-panel">
        <AlertCircle className="text-error" size={32} />
        <div>
          <h3>System Alert</h3>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  const twrr = perfMetrics?.twrr ? perfMetrics.twrr * 100 : 0.0;
  const mwrr = perfMetrics?.mwrr ? perfMetrics.mwrr * 100 : 0.0;
  const sharpe = perfMetrics?.sharpe_ratio ?? 0.0;
  const beta = perfMetrics?.beta ?? 1.0;
  const totalValue = perfMetrics?.total_value ?? 100000.00;
  const cashBalance = perfMetrics?.cash_balance ?? 100000.00;

  return (
    <div className="dashboard-grid fade-in">
      {/* 1. KEY METRICS PANEL */}
      <div className="metrics-row">
        {/* NAV Card */}
        <div className="metric-card glass-panel glass-panel-hover">
          <div className="metric-header">
            <span className="metric-title">Net Asset Value (NAV)</span>
            <DollarSign size={20} className="text-gradient-cyan" />
          </div>
          <span className="metric-value">${totalValue.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
          <div className="metric-subtext">
            <span className="text-secondary">Cash: ${cashBalance.toLocaleString("en-US", { minimumFractionDigits: 2 })}</span>
          </div>
        </div>

        {/* Returns Card */}
        <div className="metric-card glass-panel glass-panel-hover">
          <div className="metric-header">
            <span className="metric-title">TWRR / MWRR Returns</span>
            <Percent size={20} className="text-success" />
          </div>
          <div className="metric-double-row">
            <div>
              <span className="metric-label">TWRR</span>
              <span className={`metric-subvalue ${twrr >= 0 ? "text-success" : "text-error"}`}>
                {twrr >= 0 ? "+" : ""}{twrr.toFixed(2)}%
              </span>
            </div>
            <div>
              <span className="metric-label">MWRR</span>
              <span className={`metric-subvalue ${mwrr >= 0 ? "text-success" : "text-error"}`}>
                {mwrr >= 0 ? "+" : ""}{mwrr.toFixed(2)}%
              </span>
            </div>
          </div>
        </div>

        {/* Risk Card */}
        <div className="metric-card glass-panel glass-panel-hover">
          <div className="metric-header">
            <span className="metric-title">Risk Metrics</span>
            <TrendingUp size={20} className="text-warning" />
          </div>
          <div className="metric-double-row">
            <div>
              <span className="metric-label">Sharpe Ratio</span>
              <span className="metric-subvalue text-warning">{sharpe.toFixed(2)}</span>
            </div>
            <div>
              <span className="metric-label">Portfolio Beta</span>
              <span className="metric-subvalue text-warning">{beta.toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Dividend Card */}
        <div className="metric-card glass-panel glass-panel-hover">
          <div className="metric-header">
            <span className="metric-title">Projected Dividend Yield</span>
            <DollarSign size={20} className="text-success" />
          </div>
          <span className="metric-value">
            ${(dividends?.projected_annual_income ?? 0.00).toFixed(2)}
          </span>
          <div className="metric-subtext">
            <span className="text-secondary">Yield: {((dividends?.portfolio_dividend_yield ?? 0.00) * 100).toFixed(2)}%</span>
          </div>
        </div>
      </div>

      {/* 2. HOLDINGS GRID & TRANSACTION FORM */}
      <div className="dashboard-content-split">
        {/* Holdings Table */}
        <div className="holdings-container glass-panel">
          <div className="panel-title flex-row-center">
            <Briefcase size={20} className="text-gradient-cyan" />
            <h2>Current Holdings</h2>
          </div>
          {holdings.length === 0 ? (
            <div className="empty-state">No active stock holdings. Seed portfolio cash and log buy transactions.</div>
          ) : (
            <div className="table-responsive">
              <table className="holdings-table">
                <thead>
                  <tr>
                    <th>Ticker</th>
                    <th>Shares</th>
                    <th>Average Cost</th>
                    <th>Current Price</th>
                    <th>Market Value</th>
                    <th>Weight</th>
                  </tr>
                </thead>
                <tbody>
                  {holdings.map((h, i) => {
                    const weight = totalValue > 0 ? (h.market_value / totalValue) * 100 : 0.0;
                    return (
                      <tr key={i}>
                        <td className="ticker-cell">{h.ticker || "AAPL"}</td>
                        <td>{h.shares.toLocaleString()}</td>
                        <td>${h.average_cost.toFixed(2)}</td>
                        <td>${h.current_price.toFixed(2)}</td>
                        <td>${h.market_value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                        <td className="weight-cell">{weight.toFixed(1)}%</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Transaction Panel */}
        <div className="tx-form-container glass-panel">
          <div className="panel-title flex-row-center">
            <PlusCircle size={20} className="text-gradient-cyan" />
            <h2>Log Transaction</h2>
          </div>
          
          <form onSubmit={handleAddTransaction} className="tx-form">
            <div className="form-group">
              <label>Transaction Type</label>
              <select className="form-input" value={txType} onChange={(e) => setTxType(e.target.value)}>
                <option value="DEPOSIT">Cash Deposit (+)</option>
                <option value="WITHDRAW">Cash Withdrawal (-)</option>
                <option value="BUY">Asset Buy</option>
                <option value="SELL">Asset Sell</option>
              </select>
            </div>

            {(txType === "BUY" || txType === "SELL") && (
              <>
                <div className="form-group">
                  <label>Select Ticker</label>
                  <select className="form-input" value={ticker} onChange={(e) => setTicker(e.target.value)}>
                    {assets.map((asset, idx) => (
                      <option key={idx} value={asset.ticker}>{asset.ticker} - {asset.name}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>Share Price (USD)</label>
                  <input 
                    type="number" 
                    step="0.01" 
                    placeholder="0.00" 
                    className="form-input"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                  />
                </div>
              </>
            )}

            <div className="form-group">
              <label>{txType === "DEPOSIT" || txType === "WITHDRAW" ? "Amount (USD)" : "Number of Shares"}</label>
              <input 
                type="number" 
                step="0.0001" 
                placeholder="0" 
                className="form-input"
                value={size}
                onChange={(e) => setSize(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Broker Commission (USD)</label>
              <input 
                type="number" 
                step="0.01" 
                className="form-input"
                value={commission}
                onChange={(e) => setCommission(e.target.value)}
              />
            </div>

            <button type="submit" className="btn-primary" style={{ width: "100%", marginTop: "1rem" }}>
              Submit Ledger Transaction
            </button>

            {formMsg && (
              <div className={`form-message ${formMsg.type === "success" ? "msg-success" : "msg-error"}`}>
                {formMsg.text}
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}
