// Honest Beginner Onboarding — No BUY/SELL/HOLD badges
"use client";

import React, { useState } from "react";
import "./beginner.css";
import { AITutorSidebar } from "@/components/AITutorSidebar";
import { ValuationLab } from "@/components/ValuationLab";
import { PortfolioVisualizer } from "@/components/PortfolioVisualizer";
import { RiskSlider } from "@/components/RiskSlider";
import { SimulationCard } from "@/components/SimulationCard";
import { ActionPlan } from "@/components/ActionPlan";

interface Allocation {
  ticker: string;
  name: string;
  category: string;
  percentage: number;
  monthly_amount: number;
  icon: string;
  why: string;
}

interface PortfolioData {
  allocations: Allocation[];
  risk_metrics: {
    expected_return: number;
    volatility: number;
    sharpe_ratio: number;
    max_drawdown: number;
  };
  projections: {
    "5_years": number;
    "10_years": number;
    "20_years": number;
  };
  ai_rationale: string;
  warning: string;
}

export default function BeginnerOnboarding() {
  const [step, setStep] = useState(1);
  const [goal, setGoal] = useState<string | null>(null);
  const [risk, setRisk] = useState(5);
  const [monthly, setMonthly] = useState(5000);
  const [years, setYears] = useState(10);
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [loading, setLoading] = useState(false);
  const [showValuation, setShowValuation] = useState(false);

  const totalSteps = 5;

  const buildPortfolio = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/honest/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          risk_tolerance: risk,
          monthly_investment: monthly,
          goal: goal || "wealth",
          years: years,
        }),
      });
      const data = await res.json();
      setPortfolio(data);
      setStep(4);
    } catch (e) {
      console.error("Failed to build portfolio:", e);
      alert("Backend not running? Start it with: uvicorn backend.main:app --reload");
    } finally {
      setLoading(false);
    }
  };

  const getStepLabel = (n: number) => {
    const labels = ["Welcome", "Goals", "Risk", "Portfolio", "Start"];
    return labels[n - 1] || "";
  };

  return (
    <div className="aegis-beginner">
      {/* Header */}
      <header className="beginner-header">
        <div className="logo">
          <span className="shield">🛡️</span>
          <span>Aegis AI</span>
        </div>
        <div className="mode-badge">🌱 Beginner Mode</div>
      </header>

      <div className="beginner-layout">
        {/* Main Content */}
        <main className="beginner-main">
          {/* Progress Bar */}
          <div className="steps-nav">
            {Array.from({ length: totalSteps }, (_, i) => (
              <div
                key={i}
                className={`step-dot ${
                  i + 1 === step ? "active" : i + 1 < step ? "completed" : ""
                }`}
              >
                <span className="step-label">{getStepLabel(i + 1)}</span>
              </div>
            ))}
          </div>

          {/* Step 1: Welcome */}
          {step === 1 && (
            <div className="card">
              <h1 className="card-title">👋 Welcome to Investing</h1>
              <p className="card-subtitle">
                You don't need to be a stock market expert to build wealth. Aegis
                will help you create a simple, diversified portfolio that matches{" "}
                <strong>your</strong> comfort level. No jargon. No guessing. Just
                smart math.
              </p>

              <div className="feature-list">
                {[
                  "Learn your risk comfort level (2 min)",
                  "Build a diversified portfolio automatically",
                  "See exactly how much to invest each month",
                  "Understand why every choice was made",
                ].map((item, i) => (
                  <div key={i} className="feature-item">
                    <span className="check">✓</span>
                    <span>{item}</span>
                  </div>
                ))}
              </div>

              <div className="btn-row">
                <button className="btn btn-primary" onClick={() => setStep(2)}>
                  Start My Journey →
                </button>
              </div>
            </div>
          )}

          {/* Step 2: Goals */}
          {step === 2 && (
            <div className="card">
              <h1 className="card-title">🎯 What are you investing for?</h1>
              <p className="card-subtitle">
                Your goal changes how we build your portfolio. Don't worry — you
                can change this anytime.
              </p>

              {[
                {
                  id: "wealth",
                  title: "Build Long-Term Wealth",
                  desc: "I want to grow my money over 10+ years. I'm okay with ups and downs along the way.",
                },
                {
                  id: "house",
                  title: "Save for a Big Purchase",
                  desc: "House, car, or education in 5-7 years. I need growth but can't afford a huge crash right before I need the money.",
                },
                {
                  id: "income",
                  title: "Generate Monthly Income",
                  desc: "I want regular dividends/returns. Lower growth, but more predictable cash flow.",
                },
              ].map((option) => (
                <div
                  key={option.id}
                  className={`question-card ${goal === option.id ? "selected" : ""}`}
                  onClick={() => setGoal(option.id)}
                >
                  <div className="q-radio">
                    {goal === option.id && <div className="q-radio-inner" />}
                  </div>
                  <div className="q-text">
                    <strong>{option.title}</strong>
                    <span>{option.desc}</span>
                  </div>
                </div>
              ))}

              <div className="btn-row">
                <button className="btn btn-secondary" onClick={() => setStep(1)}>
                  ← Back
                </button>
                <button
                  className="btn btn-primary"
                  onClick={() => setStep(3)}
                  disabled={!goal}
                >
                  Continue →
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Risk + Monthly Amount */}
          {step === 3 && (
            <div className="card">
              <h1 className="card-title">⚖️ How much risk can you handle?</h1>
              <p className="card-subtitle">
                This isn't about bravery — it's about sleep. If your portfolio
                drops 30%, will you panic and sell, or stay calm?
              </p>

              <RiskSlider value={risk} onChange={setRisk} />

              <div className="monthly-input">
                <label>Monthly Investment (₹)</label>
                <input
                  type="number"
                  value={monthly}
                  onChange={(e) => setMonthly(Number(e.target.value))}
                  min={1000}
                  step={500}
                />
              </div>

              <div className="years-input">
                <label>Investment Horizon (years)</label>
                <input
                  type="range"
                  min={1}
                  max={40}
                  value={years}
                  onChange={(e) => setYears(Number(e.target.value))}
                />
                <span>{years} years</span>
              </div>

              <div className="risk-explanation">
                <p>
                  With a <strong>{risk}/10</strong> risk profile, you might see
                  your money go up <strong className="green">+20%</strong> in a
                  good year, and down{" "}
                  <strong className="red">-15%</strong> in a bad year. Over{" "}
                  {years} years, this usually beats a savings account.
                </p>
              </div>

              <div className="btn-row">
                <button className="btn btn-secondary" onClick={() => setStep(2)}>
                  ← Back
                </button>
                <button
                  className="btn btn-primary"
                  onClick={buildPortfolio}
                  disabled={loading}
                >
                  {loading ? "Building..." : "Build My Portfolio →"}
                </button>
              </div>
            </div>
          )}

          {/* Step 4: Portfolio Result */}
          {step === 4 && portfolio && (
            <div className="card">
              <h1 className="card-title">📊 Your Personalized Portfolio</h1>
              <p className="card-subtitle">
                Based on your goal and risk level, here's what the math
                recommends. Remember: this spreads your money across many
                companies so one bad stock can't ruin you.
              </p>

              <PortfolioVisualizer allocations={portfolio.allocations} />

              <SimulationCard
                projections={portfolio.projections}
                riskMetrics={portfolio.risk_metrics}
              />

              <div className="rationale-box">
                <h3>🧠 Why This Allocation?</h3>
                <div className="rationale-text">
                  {portfolio.ai_rationale.split("\n").map((line, i) => (
                    <p key={i}>{line}</p>
                  ))}
                </div>
              </div>

              <div className="warning-box">
                <span>⚠️</span> {portfolio.warning}
              </div>

              <div className="btn-row">
                <button className="btn btn-secondary" onClick={() => setStep(3)}>
                  ← Adjust Risk
                </button>
                <button className="btn btn-primary" onClick={() => setStep(5)}>
                  Looks Good, Let's Start →
                </button>
              </div>
            </div>
          )}

          {/* Step 5: Action Plan + Valuation Lab Link */}
          {step === 5 && portfolio && (
            <div className="card">
              <h1 className="card-title">🚀 You're Ready</h1>
              <p className="card-subtitle">
                Here's your simple monthly plan. You don't need to watch the
                market every day. Just invest consistently and let time do the
                work.
              </p>

              <ActionPlan allocations={portfolio.allocations} />

              <div className="beginner-warning">
                <strong>⚠️ Important:</strong> This is a long-term game. Don't
                check your portfolio every day. Don't sell when the market drops.
                The biggest mistake beginners make is panic-selling during a
                crash. Your AI tutor will remind you of this every month.
              </div>

              <div className="valuation-cta">
                <h3>🔬 Want to learn more?</h3>
                <p>
                  Try the <strong>Valuation Lab</strong> to understand how to read
                  company financials. No stock picking — just education.
                </p>
                <button
                  className="btn btn-secondary"
                  onClick={() => setShowValuation(true)}
                >
                  Open Valuation Lab →
                </button>
              </div>

              <div className="btn-row">
                <button className="btn btn-secondary" onClick={() => setStep(4)}>
                  ← Review Portfolio
                </button>
                <button className="btn btn-primary" onClick={() => window.location.href = "/"}>
                  Go to My Dashboard 🎉
                </button>
              </div>
            </div>
          )}

          {/* Valuation Lab Modal */}
          {showValuation && (
            <div className="modal-overlay" onClick={() => setShowValuation(false)}>
              <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <ValuationLab />
                <button className="modal-close" onClick={() => setShowValuation(false)}>
                  ✕ Close
                </button>
              </div>
            </div>
          )}
        </main>

        {/* AI Tutor Sidebar */}
        <AITutorSidebar
          step={step}
          goal={goal}
          risk={risk}
          monthly={monthly}
        />
      </div>
    </div>
  );
}
