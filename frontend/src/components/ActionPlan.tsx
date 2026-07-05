"use client";

import React from "react";

interface Allocation {
  ticker: string;
  name: string;
  icon: string;
  monthly_amount: number;
  why: string;
}

interface ActionPlanProps {
  allocations: Allocation[];
}

export function ActionPlan({ allocations }: ActionPlanProps) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
      {allocations.map((a) => (
        <div
          key={a.ticker}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            padding: "14px 16px",
            background: "var(--bg)",
            borderRadius: "10px",
            border: "1px solid var(--border)",
          }}
        >
          <div style={{ fontSize: "24px" }}>{a.icon}</div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: "14px", fontWeight: 600 }}>{a.name}</div>
            <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>{a.why}</div>
          </div>
          <div style={{ fontSize: "16px", fontWeight: 700, color: "var(--accent)" }}>
            ₹{a.monthly_amount}
          </div>
        </div>
      ))}
    </div>
  );
}
