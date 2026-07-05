"use client";

import React from "react";

interface RiskSliderProps {
  value: number;
  onChange: (val: number) => void;
}

export function RiskSlider({ value, onChange }: RiskSliderProps) {
  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const pct = Math.max(0, Math.min(100, (x / rect.width) * 100));
    const newVal = Math.max(1, Math.min(10, Math.round(pct / 10)));
    onChange(newVal);
  };

  const pct = (value / 10) * 100;

  const labels: Record<number, string> = {
    1: "Very Safe", 2: "Conservative", 3: "Cautious", 4: "Moderate", 5: "Balanced",
    6: "Growth", 7: "Aggressive", 8: "Very Aggressive", 9: "Speculative", 10: "Maximum Risk"
  };

  return (
    <div className="risk-slider-container">
      <div className="risk-labels">
        <span>🐢 Safe</span>
        <span>🐆 Balanced</span>
        <span>🚀 Aggressive</span>
      </div>
      <div className="risk-track" onClick={handleClick}>
        <div className="risk-fill" style={{ width: `${pct}%` }} />
        <div className="risk-thumb" style={{ left: `${pct}%` }} />
      </div>
      <div className="risk-value">{value}</div>
      <div className="risk-desc">{labels[value] || "Balanced"}</div>
    </div>
  );
}
