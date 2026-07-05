// Educational valuation analysis. NEVER says BUY/SELL/HOLD.
"use client";

import React, { useState } from "react";

interface ValuationMetric {
  name: string;
  value: number | null;
  industry_avg: number | null;
  explanation: string;
  red_flag: string | null;
  context: string;
}

interface ValuationData {
  ticker: string;
  company_name: string;
  metrics: ValuationMetric[];
  ai_summary: string;
  user_action_prompt: string;
}

export function ValuationLab() {
  const [ticker, setTicker] = useState("");
  const [data, setData] = useState<ValuationData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const analyze = async () => {
    if (!ticker.trim()) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetch("http://127.0.0.1:8000/api/honest/valuation-education", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker: ticker.trim().toUpperCase() }),
      });
      if (!res.ok) throw new Error("Analysis failed");
      const result = await res.json();
      setData(result);
    } catch (e) {
      setError("Could not analyze this ticker. Try TCS.NS, RELIANCE.NS, or INFY.NS");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="valuation-lab">
      <h2>🔬 Valuation Lab</h2>
      <p className="lab-intro">
        Learn how to read company financials. This tool teaches you what the
        numbers mean — it <strong>never</strong> tells you to buy or sell.
      </p>

      <div className="search-box">
        <input
          type="text"
          placeholder="Enter ticker (e.g., TCS.NS, RELIANCE.NS)"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && analyze()}
        />
        <button onClick={analyze} disabled={loading}>
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </div>

      {error && <div className="error-msg">{error}</div>}

      {data && (
        <div className="valuation-result">
          <div className="company-header">
            <h3>{data.company_name}</h3>
            <span className="ticker-tag">{data.ticker}</span>
          </div>

          <div className="metrics-grid">
            {data.metrics.map((m, i) => (
              <div key={i} className={`metric-card ${m.red_flag ? "has-flag" : ""}`}>
                <div className="metric-name">{m.name}</div>
                <div className="metric-value">
                  {m.value !== null ? m.value.toFixed(1) : "N/A"}
                  {m.industry_avg !== null && (
                    <span className="industry-avg">
                      vs {m.industry_avg.toFixed(1)} avg
                    </span>
                  )}
                </div>
                <div className="metric-explanation">{m.explanation}</div>
                <div className="metric-context">{m.context}</div>
                {m.red_flag && (
                  <div className="red-flag">⚠️ {m.red_flag}</div>
                )}
              </div>
            ))}
          </div>

          <div className="ai-summary">
            <h4>🧠 Understanding the Numbers</h4>
            <div className="summary-text">
              {data.ai_summary.split("\n").map((line, i) => (
                <p key={i}>{line}</p>
              ))}
            </div>
          </div>

          <div className="action-prompt">
            <strong>💡 Your Next Step:</strong>
            <p>{data.user_action_prompt}</p>
          </div>

          <div className="valuation-disclaimer">
            <strong>Remember:</strong> These metrics are historical. They tell you
            what the market thought yesterday, not what it will think tomorrow. The
            best investors understand the <em>business</em>, not just the ratios.
          </div>
        </div>
      )}
    </div>
  );
}
