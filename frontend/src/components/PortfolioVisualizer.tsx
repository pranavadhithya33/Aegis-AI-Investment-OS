"use client";

import React from "react";

interface Allocation {
  ticker: string;
  name: string;
  percentage: number;
  monthly_amount: number;
  icon: string;
  why: string;
}

interface PortfolioVisualizerProps {
  allocations: Allocation[];
}

export function PortfolioVisualizer({ allocations }: PortfolioVisualizerProps) {
  return (
    <div className="portfolio-grid">
      {allocations.map((a) => (
        <div key={a.ticker} className="asset-bucket">
          <div className="bucket-icon">{a.icon}</div>
          <div className="bucket-name">{a.name}</div>
          <div className="bucket-pct">{a.percentage}%</div>
          <div className="bucket-desc">{a.why}</div>
          <div className="bucket-amount">₹{a.monthly_amount}/mo</div>
        </div>
      ))}
    </div>
  );
}
