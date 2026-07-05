"use client";

import React from "react";

interface SimulationCardProps {
  projections: {
    "5_years": number;
    "10_years": number;
    "20_years": number;
  };
  riskMetrics: {
    expected_return: number;
    volatility: number;
    sharpe_ratio: number;
    max_drawdown: number;
  };
}

export function SimulationCard({ projections, riskMetrics }: SimulationCardProps) {
  const formatLakh = (n: number) => {
    if (n >= 100000) return `₹${(n / 100000).toFixed(1)}L`;
    return `₹${n.toLocaleString()}`;
  };

  return (
    <div className="sim-card">
      <div style={{ fontSize: "14px", fontWeight: 600, marginBottom: "4px" }}>
        📈 If you invest consistently...
      </div>
      <div style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "16px" }}>
        These are estimates based on historical averages. Markets can do better or worse.
      </div>
      <div className="sim-grid">
        <div className="sim-cell">
          <div className="sim-value" style={{ color: "var(--text)" }}>
            {formatLakh(projections["5_years"])}
          </div>
          <div className="sim-label">After 5 years</div>
        </div>
        <div className="sim-cell">
          <div className="sim-value" style={{ color: "var(--accent)" }}>
            {formatLakh(projections["10_years"])}
          </div>
          <div className="sim-label">After 10 years</div>
        </div>
        <div className="sim-cell">
          <div className="sim-value" style={{ color: "var(--success)" }}>
            {formatLakh(projections["20_years"])}
          </div>
          <div className="sim-label">After 20 years</div>
        </div>
      </div>
      <div style={{ marginTop: "16px", paddingTop: "16px", borderTop: "1px solid var(--border)", fontSize: "12px", color: "var(--text-muted)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
          <span>Expected Return:</span>
          <span>{riskMetrics.expected_return}%/year</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
          <span>Volatility:</span>
          <span>{riskMetrics.volatility}%/year</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
          <span>Sharpe Ratio:</span>
          <span>{riskMetrics.sharpe_ratio}</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span>Max Drawdown (historical):</span>
          <span style={{ color: "var(--danger)" }}>{riskMetrics.max_drawdown}%</span>
        </div>
      </div>
    </div>
  );
}
