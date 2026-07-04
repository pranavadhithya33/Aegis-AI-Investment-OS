"use client";

import React, { useState, useEffect } from "react";
import { 
  Play, 
  TrendingUp, 
  BarChart, 
  Calendar,
  AlertCircle,
  HelpCircle
} from "lucide-react";
import { 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid,
  AreaChart,
  Area
} from "recharts";

interface SimulationTabProps {
  portfolioId: number;
}

export default function SimulationTab({ portfolioId }: SimulationTabProps) {
  const [activeSubTab, setActiveSubTab] = useState("backtest");
  const [assets, setAssets] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Backtest form states
  const [backtestTicker, setBacktestTicker] = useState("AAPL");
  const [strategy, setStrategy] = useState("sma_cross");
  const [initialCash, setInitialCash] = useState("10000");
  const [startDate, setStartDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 365); // Default 1 year ago
    return d.toISOString().split("T")[0];
  });
  const [endDate, setEndDate] = useState(() => new Date().toISOString().split("T")[0]);
  const [backtestResults, setBacktestResults] = useState<any>(null);

  // Monte Carlo form states
  const [projectionDays, setProjectionDays] = useState("60");
  const [numSims, setNumSims] = useState("100");
  const [mcResults, setMcResults] = useState<any>(null);

  // Load assets list
  useEffect(() => {
    async function loadAssets() {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/assets/");
        const data = await res.json();
        setAssets(data);
      } catch (err) {
        console.error("Failed to load assets universe:", err);
      }
    }
    loadAssets();
  }, []);

  // Run backtest
  const runBacktest = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setBacktestResults(null);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/simulation/backtest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker: backtestTicker,
          strategy_name: strategy,
          start_date: startDate,
          end_date: endDate,
          initial_cash: parseFloat(initialCash)
        })
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Backtest computation failed.");
      }

      const data = await res.json();
      setBacktestResults(data);
    } catch (err: any) {
      setError(err.message || "Network connection error.");
    } finally {
      setLoading(false);
    }
  };

  // Run Monte Carlo
  const runMonteCarlo = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setMcResults(null);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/simulation/monte-carlo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          portfolio_id: portfolioId,
          projection_days: parseInt(projectionDays),
          num_simulations: parseInt(numSims)
        })
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Monte Carlo simulation failed.");
      }

      const data = await res.json();
      
      // Reshape data for Recharts (aligning days index)
      const reshaped = data.p50.map((_: any, idx: number) => ({
        day: `Day ${idx}`,
        p5: Math.round(data.p5[idx]),
        p50: Math.round(data.p50[idx]),
        p95: Math.round(data.p95[idx]),
      }));
      
      setMcResults(reshaped);
    } catch (err: any) {
      setError(err.message || "Failed to project portfolio path.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="simulation-container fade-in">
      {/* Tab Switcher */}
      <div className="subtabs-bar">
        <button 
          className={`subtab-btn ${activeSubTab === "backtest" ? "active" : ""}`}
          onClick={() => { setActiveSubTab("backtest"); setError(null); }}
        >
          <BarChart size={16} />
          Historical Backtester
        </button>
        <button 
          className={`subtab-btn ${activeSubTab === "montecarlo" ? "active" : ""}`}
          onClick={() => { setActiveSubTab("montecarlo"); setError(null); }}
        >
          <TrendingUp size={16} />
          Monte Carlo Random Walk
        </button>
      </div>

      {error && (
        <div className="error-panel glass-panel">
          <AlertCircle className="text-error" size={24} />
          <p>{error}</p>
        </div>
      )}

      {/* --- 1. HISTORICAL BACKTEST TAB --- */}
      {activeSubTab === "backtest" && (
        <div className="sim-split-layout">
          {/* Controls Panel */}
          <div className="sim-controls glass-panel">
            <h3>Backtest Parameters</h3>
            <form onSubmit={runBacktest} className="sim-form">
              <div className="form-group">
                <label>Select Security</label>
                <select className="form-input" value={backtestTicker} onChange={(e) => setBacktestTicker(e.target.value)}>
                  {assets.map((a) => (
                    <option key={a.id} value={a.ticker}>{a.ticker} - {a.name}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Strategy Rule</label>
                <select className="form-input" value={strategy} onChange={(e) => setStrategy(e.target.value)}>
                  <option value="sma_cross">SMA Double Crossover (10 / 30 day)</option>
                  <option value="rsi_bounds">RSI Bound Oscillators (30 / 70 day)</option>
                </select>
              </div>

              <div className="form-group">
                <label>Initial Investment ($)</label>
                <input 
                  type="number" 
                  className="form-input" 
                  value={initialCash}
                  onChange={(e) => setInitialCash(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>Start Date</label>
                <input 
                  type="date" 
                  className="form-input" 
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>End Date</label>
                <input 
                  type="date" 
                  className="form-input" 
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </div>

              <button type="submit" className="btn-primary" disabled={loading}>
                <Play size={16} /> {loading ? "Computing Paths..." : "Execute Simulation"}
              </button>
            </form>
          </div>

          {/* Results Output */}
          <div className="sim-display glass-panel">
            {!backtestResults && !loading && (
              <div className="empty-sim-state">
                <HelpCircle size={48} className="text-muted" />
                <h4>No Backtest Executed</h4>
                <p>Configure strategy variables and click execute to query historical curves.</p>
              </div>
            )}
            
            {loading && <div className="loading-state">Solving historical ordinary differential equations...</div>}

            {backtestResults && (
              <div className="sim-results-wrapper">
                {/* Backtest Statistics Grid */}
                <div className="sim-stats-grid">
                  <div className="sim-stat-box">
                    <span className="stat-label">Ending Equity</span>
                    <span className="stat-val">${backtestResults.final_value.toLocaleString("en-US", { maximumFractionDigits: 2 })}</span>
                  </div>
                  <div className="sim-stat-box">
                    <span className="stat-label">Cumulative Return</span>
                    <span className={`stat-val ${(backtestResults.cumulative_return ?? 0) >= 0 ? "text-success" : "text-error"}`}>
                      {((backtestResults.cumulative_return ?? 0) * 100).toFixed(2)}%
                    </span>
                  </div>
                  <div className="sim-stat-box">
                    <span className="stat-label">Sharpe Ratio</span>
                    <span className="stat-val text-warning">{(backtestResults.sharpe_ratio ?? 0).toFixed(2)}</span>
                  </div>
                  <div className="sim-stat-box">
                    <span className="stat-label">Max Drawdown</span>
                    <span className="stat-val text-error">{((backtestResults.max_drawdown ?? 0) * 100).toFixed(2)}%</span>
                  </div>
                </div>

                {/* Backtest Chart */}
                <div className="sim-chart-container">
                  <h4>Equity Growth Path (USD)</h4>
                  <div style={{ width: "100%", height: 300 }}>
                    <ResponsiveContainer>
                      <LineChart data={backtestResults.equity_curve} margin={{ top: 10, right: 10, left: 10, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                        <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={11} tickLine={false} />
                        <YAxis stroke="var(--text-muted)" fontSize={11} domain={["auto", "auto"]} tickLine={false} />
                        <Tooltip 
                          contentStyle={{ backgroundColor: "#0d1321", borderColor: "var(--border-color)", color: "#fff" }}
                          labelStyle={{ color: "var(--accent-cyan)", fontWeight: 700 }}
                        />
                        <Line type="monotone" dataKey="value" stroke="var(--accent-blue)" strokeWidth={2} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Trades Listing */}
                <div className="sim-trades-list">
                  <h4>Executed Trade Ledger ({backtestResults.trades_count} trades)</h4>
                  {backtestResults.trades.length === 0 ? (
                    <p className="text-secondary" style={{ fontSize: "0.9rem" }}>No trades executed in this period.</p>
                  ) : (
                    <div className="table-responsive">
                      <table className="holdings-table">
                        <thead>
                          <tr>
                            <th>Date</th>
                            <th>Action</th>
                            <th>Execution Price</th>
                            <th>Shares</th>
                            <th>Commission</th>
                          </tr>
                        </thead>
                        <tbody>
                          {backtestResults.trades.map((t: any, idx: number) => (
                            <tr key={idx}>
                              <td>{t.date}</td>
                              <td className={t.type === "BUY" ? "text-success" : "text-error"} style={{ fontWeight: 700 }}>{t.type}</td>
                              <td>${t.price.toFixed(2)}</td>
                              <td>{t.shares.toFixed(2)}</td>
                              <td>${t.commission.toFixed(2)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* --- 2. MONTE CARLO PROJECTION TAB --- */}
      {activeSubTab === "montecarlo" && (
        <div className="sim-split-layout">
          {/* Controls */}
          <div className="sim-controls glass-panel">
            <h3>Monte Carlo Parameters</h3>
            <form onSubmit={runMonteCarlo} className="sim-form">
              <div className="form-group">
                <label>Projection Window (Days)</label>
                <input 
                  type="number" 
                  className="form-input" 
                  value={projectionDays} 
                  onChange={(e) => setProjectionDays(e.target.value)} 
                />
              </div>

              <div className="form-group">
                <label>Paths to Simulate</label>
                <select className="form-input" value={numSims} onChange={(e) => setNumSims(e.target.value)}>
                  <option value="50">50 Random Walks</option>
                  <option value="100">100 Random Walks</option>
                  <option value="250">250 Random Walks</option>
                </select>
              </div>

              <button type="submit" className="btn-primary" disabled={loading}>
                <Play size={16} /> {loading ? "Generating Random Walks..." : "Launch Projection"}
              </button>
            </form>
          </div>

          {/* Display */}
          <div className="sim-display glass-panel">
            {!mcResults && !loading && (
              <div className="empty-sim-state">
                <TrendingUp size={48} className="text-muted" />
                <h4>No Monte Carlo Projection Run</h4>
                <p>Run simulated futures using current asset covariance matrices.</p>
              </div>
            )}

            {loading && <div className="loading-state">Simulating Gaussian random walk valuations...</div>}

            {mcResults && (
              <div className="sim-results-wrapper">
                <h4>Portfolio Future Value Path Projections (USD)</h4>
                <p className="text-secondary" style={{ fontSize: "0.85rem", marginBottom: "1rem" }}>
                  Random walk projections using the daily covariance matrix of active stock holdings.
                </p>

                {/* MC Chart */}
                <div style={{ width: "100%", height: 320 }}>
                  <ResponsiveContainer>
                    <AreaChart data={mcResults} margin={{ top: 10, right: 10, left: 10, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="day" stroke="var(--text-muted)" fontSize={11} tickLine={false} />
                      <YAxis stroke="var(--text-muted)" fontSize={11} domain={["auto", "auto"]} tickLine={false} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: "#0d1321", borderColor: "var(--border-color)", color: "#fff" }}
                      />
                      {/* confidence bounds shaded */}
                      <Area type="monotone" dataKey="p95" stroke="none" fill="rgba(16, 185, 129, 0.05)" />
                      <Area type="monotone" dataKey="p5" stroke="none" fill="rgba(16, 185, 129, 0.05)" />
                      <Line type="monotone" dataKey="p50" stroke="var(--status-success)" strokeWidth={2} dot={false} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>

                <div className="mc-legend-panel">
                  <div className="legend-item">
                    <span className="legend-indicator" style={{ backgroundColor: "var(--status-success)" }}></span>
                    <div>
                      <strong>P50 Midpoint Value:</strong>
                      <span className="text-secondary"> ${mcResults[mcResults.length - 1].p50.toLocaleString()}</span>
                    </div>
                  </div>
                  <div className="legend-item">
                    <span className="legend-indicator" style={{ backgroundColor: "rgba(16, 185, 129, 0.2)" }}></span>
                    <div>
                      <strong>Confidence Interval (P5 - P95):</strong>
                      <span className="text-secondary"> ${mcResults[mcResults.length - 1].p5.toLocaleString()} to ${mcResults[mcResults.length - 1].p95.toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
