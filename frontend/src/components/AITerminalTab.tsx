"use client";

import React, { useState, useEffect } from "react";
import { 
  Brain, 
  PlusCircle, 
  RefreshCw, 
  Trash2, 
  Play, 
  Terminal, 
  CheckCircle,
  XCircle,
  HelpCircle,
  Activity,
  TrendingUp,
  BookOpen,
  Globe,
  DollarSign
} from "lucide-react";

interface AITerminalTabProps {
  portfolioId: number;
}

export default function AITerminalTab({ portfolioId }: AITerminalTabProps) {
  const [theses, setTheses] = useState<any[]>([]);
  const [logs, setLogs] = useState<any[]>([]);
  const [assets, setAssets] = useState<any[]>([]);
  
  const [loading, setLoading] = useState(false);
  const [advisoryLoading, setAdvisoryLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Thesis Form States
  const [newThesisTicker, setNewThesisTicker] = useState("AAPL");
  const [thesisText, setThesisText] = useState("");
  const [successCriteria, setSuccessCriteria] = useState("");
  const [reviewDate, setReviewDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 30); // Default 30 days from now
    return d.toISOString().split("T")[0];
  });

  // Decision Session Form States
  const [sessionTicker, setSessionTicker] = useState("AAPL");
  const [question, setQuestion] = useState("");
  const [sessionResult, setSessionResult] = useState<any>(null);

  // Active sub-section (Advisory Session vs Active Theses vs Prompt Audit)
  const [activeSubTab, setActiveSubTab] = useState("advisory");

  // Load initial data
  useEffect(() => {
    loadInitialData();
  }, []);

  async function loadInitialData() {
    try {
      // Load assets
      const assetsRes = await fetch("http://127.0.0.1:8000/api/assets/");
      const assetsData = await assetsRes.json();
      setAssets(assetsData);

      // Load theses
      const thesesRes = await fetch("http://127.0.0.1:8000/api/ai/theses");
      const thesesData = await thesesRes.json();
      setTheses(thesesData);

      // Load logs
      const logsRes = await fetch("http://127.0.0.1:8000/api/ai/logs?limit=30");
      const logsData = await logsRes.json();
      setLogs(logsData);
    } catch (err) {
      console.error("Failed to load initial advisory terminal data:", err);
    }
  }

  // Create new thesis
  const handleCreateThesis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!thesisText || !successCriteria) return;

    try {
      const res = await fetch("http://127.0.0.1:8000/api/ai/thesis", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          asset_ticker: newThesisTicker,
          thesis_text: thesisText,
          success_criteria_json: successCriteria,
          review_date: reviewDate
        })
      });

      if (!res.ok) throw new Error("Failed to store thesis.");

      setThesisText("");
      setSuccessCriteria("");
      loadInitialData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  // Evaluate thesis
  const handleEvaluateThesis = async (thesisId: number) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/ai/evaluate-thesis", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ thesis_id: thesisId })
      });

      if (!res.ok) throw new Error("Boundary audit evaluation failed.");
      
      loadInitialData();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Delete thesis
  const handleDeleteThesis = async (thesisId: number) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/ai/thesis/${thesisId}`, {
        method: "DELETE"
      });
      if (res.ok) loadInitialData();
    } catch (err) {
      console.error(err);
    }
  };

  // Run decision consensus session
  const handleRunAdvisory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question) return;

    setAdvisoryLoading(true);
    setSessionResult(null);
    setError(null);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/ai/decision-session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          portfolio_id: portfolioId,
          question: question,
          asset_ticker: sessionTicker
        })
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Consensus routing error.");
      }

      const data = await res.json();
      setSessionResult(data);
      
      // Refresh prompt logs in background
      loadInitialData();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setAdvisoryLoading(false);
    }
  };

  return (
    <div className="simulation-container fade-in">
      {/* Subtabs header */}
      <div className="subtabs-bar">
        <button 
          className={`subtab-btn ${activeSubTab === "advisory" ? "active" : ""}`}
          onClick={() => { setActiveSubTab("advisory"); setError(null); }}
        >
          <Brain size={16} />
          Multi-Agent Advisory
        </button>
        <button 
          className={`subtab-btn ${activeSubTab === "theses" ? "active" : ""}`}
          onClick={() => { setActiveSubTab("theses"); setError(null); }}
        >
          <CheckCircle size={16} />
          Investment Theses
        </button>
        <button 
          className={`subtab-btn ${activeSubTab === "audit" ? "active" : ""}`}
          onClick={() => { setActiveSubTab("audit"); setError(null); }}
        >
          <Terminal size={16} />
          Token & Prompt Audit
        </button>
      </div>

      {error && (
        <div className="error-panel glass-panel">
          <XCircle className="text-error" size={24} />
          <p>{error}</p>
        </div>
      )}

      {/* --- 1. MULTI-AGENT ADVISORY --- */}
      {activeSubTab === "advisory" && (
        <div className="sim-split-layout">
          {/* Form */}
          <div className="sim-controls glass-panel">
            <h3>Advisory Prompt</h3>
            <form onSubmit={handleRunAdvisory} className="sim-form">
              <div className="form-group">
                <label>Select Target Ticker</label>
                <select className="form-input" value={sessionTicker} onChange={(e) => setSessionTicker(e.target.value)}>
                  {assets.map((a) => (
                    <option key={a.id} value={a.ticker}>{a.ticker} - {a.name}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Investment Question</label>
                <textarea 
                  className="form-input" 
                  rows={4}
                  placeholder="Should we accumulate this asset given macro regimes and technical crossovers?"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                />
              </div>

              <button type="submit" className="btn-primary" disabled={advisoryLoading}>
                <Play size={16} /> {advisoryLoading ? "Routing Multi-Agent Pipeline..." : "Convene Advisory Session"}
              </button>
            </form>
          </div>

          {/* Results Display */}
          <div className="sim-display glass-panel">
            {!sessionResult && !advisoryLoading && (
              <div className="empty-sim-state">
                <Brain size={48} className="text-muted" />
                <h4>Advisory Consensus Offline</h4>
                <p>Pose a question to aggregate sentiment, fundamental, macro, and portfolio reviews.</p>
              </div>
            )}

            {advisoryLoading && (
              <div className="loading-state flex flex-col gap-2">
                <Activity size={32} className="text-gradient-cyan animate-pulse" />
                <span>{"Running Sentiment -> Fundamentals -> Macro -> Portfolio consensus validations..."}</span>
              </div>
            )}

            {sessionResult && (
              <div className="advisory-result fade-in">
                <div className="advisory-outcome-header">
                  <h4>Advisory Board Consensus Result</h4>
                  <span className={`decision-badge badge-${sessionResult.final_decision.toLowerCase()}`}>
                    {sessionResult.final_decision}
                  </span>
                </div>

                <div className="advisory-detail-box">
                  <h5>Audit Reasoning Summary</h5>
                  <p>{sessionResult.reasoning_summary}</p>
                </div>

                <div className="advisory-detail-box">
                  <h5>Recommendation Details</h5>
                  <p className="recommendation-text">{sessionResult.recommendation_details}</p>
                </div>

                {sessionResult.evidence_breakdown && (
                  <div className="evidence-panel-container">
                    <div className="advisory-detail-box">
                      <h5 style={{ marginBottom: "1rem" }}>Advisory Board Evidence Breakdown</h5>
                      <div className="evidence-grid">
                        <div className="evidence-card">
                          <div className="evidence-card-header">
                            <TrendingUp size={16} className="text-accent-cyan" />
                            <span>News Sentiment</span>
                          </div>
                          <p>{sessionResult.evidence_breakdown.sentiment}</p>
                        </div>

                        <div className="evidence-card">
                          <div className="evidence-card-header">
                            <BookOpen size={16} className="text-accent-blue" />
                            <span>Fundamentals</span>
                          </div>
                          <p>{sessionResult.evidence_breakdown.fundamentals}</p>
                        </div>

                        <div className="evidence-card">
                          <div className="evidence-card-header">
                            <Globe size={16} className="text-accent-purple" />
                            <span>Macro Outlook</span>
                          </div>
                          <p>{sessionResult.evidence_breakdown.macro}</p>
                        </div>

                        <div className="evidence-card">
                          <div className="evidence-card-header">
                            <DollarSign size={16} className="text-accent-success" />
                            <span>Portfolio Weights</span>
                          </div>
                          <p>{sessionResult.evidence_breakdown.portfolio}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                <div className="advisory-flow-graph">
                  <h5>Consensus Resolution Order</h5>
                  <div className="flow-steps">
                    <span className="step-node">Sentiment Agent</span>
                    <span className="step-arrow">&rarr;</span>
                    <span className="step-node">Fundamentals Agent</span>
                    <span className="step-arrow">&rarr;</span>
                    <span className="step-node">Macro Agent</span>
                    <span className="step-arrow">&rarr;</span>
                    <span className="step-node">Portfolio Agent</span>
                    <span className="step-arrow">&rarr;</span>
                    <span className="step-node final">Decision Auditor</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* --- 2. INVESTMENT THESES TRACKER --- */}
      {activeSubTab === "theses" && (
        <div className="sim-split-layout">
          {/* Create Thesis Form */}
          <div className="sim-controls glass-panel">
            <h3>New Investment Thesis</h3>
            <form onSubmit={handleCreateThesis} className="sim-form">
              <div className="form-group">
                <label>Ticker</label>
                <select className="form-input" value={newThesisTicker} onChange={(e) => setNewThesisTicker(e.target.value)}>
                  {assets.map((a) => (
                    <option key={a.id} value={a.ticker}>{a.ticker} - {a.name}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Thesis Statement</label>
                <textarea 
                  className="form-input" 
                  rows={3}
                  placeholder="e.g. MSFT will outperform due to 20% cloud growth margins."
                  value={thesisText}
                  onChange={(e) => setThesisText(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>Success Thresholds (JSON / Text)</label>
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder='e.g. {"price_target": 450, "crossover": "bullish"}'
                  value={successCriteria}
                  onChange={(e) => setSuccessCriteria(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>Target Review Date</label>
                <input 
                  type="date" 
                  className="form-input" 
                  value={reviewDate} 
                  onChange={(e) => setReviewDate(e.target.value)} 
                />
              </div>

              <button type="submit" className="btn-primary">
                <PlusCircle size={16} /> Log Active Thesis
              </button>
            </form>
          </div>

          {/* List Theses */}
          <div className="sim-display glass-panel">
            <h3 style={{ marginBottom: "1rem" }}>Active & Evaluated Theses</h3>
            {loading && <div className="loading-state">Evaluating bounds...</div>}

            {theses.length === 0 ? (
              <div className="empty-sim-state">
                <HelpCircle size={48} className="text-muted" />
                <h4>No Theses Logged</h4>
                <p>Use the form to log long-term investment boundaries and track automated target review states.</p>
              </div>
            ) : (
              <div className="theses-cards-list">
                {theses.map((t) => (
                  <div key={t.id} className="thesis-card glass-panel">
                    <div className="thesis-card-header">
                      <span className="thesis-ticker">{t.asset_ticker}</span>
                      <span className={`status-badge badge-${t.status.toLowerCase()}`}>{t.status}</span>
                    </div>
                    <p className="thesis-body-text"><strong>Thesis:</strong> {t.thesis_text}</p>
                    <p className="thesis-body-text"><strong>Success Targets:</strong> <code>{t.success_criteria_json}</code></p>
                    <p className="thesis-body-text"><strong>Review Date:</strong> {t.review_date}</p>
                    
                    {t.outcome_text && (
                      <div className="thesis-outcome-alert">
                        <strong>Outcome:</strong> {t.outcome_text}
                      </div>
                    )}

                    <div className="thesis-card-actions">
                      <button 
                        className="btn-secondary btn-sm" 
                        onClick={() => handleEvaluateThesis(t.id)}
                        disabled={loading}
                        style={{ padding: "0.4rem 0.8rem", fontSize: "0.8rem" }}
                      >
                        <RefreshCw size={12} /> Evaluate Boundary
                      </button>
                      <button 
                        className="btn-delete" 
                        onClick={() => handleDeleteThesis(t.id)}
                        title="Delete Thesis"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* --- 3. TOKEN & PROMPT AUDIT CONSOLE --- */}
      {activeSubTab === "audit" && (
        <div className="console-panel glass-panel">
          <div className="panel-title flex-row-center" style={{ justifyContent: "space-between" }}>
            <div className="flex-row-center">
              <Terminal size={20} className="text-gradient-cyan" />
              <h2>LLM Manager Execution Logs</h2>
            </div>
            <button className="btn-secondary btn-sm" onClick={loadInitialData}>
              <RefreshCw size={14} /> Refresh Logs
            </button>
          </div>

          <div className="logs-scroller">
            {logs.length === 0 ? (
              <p className="text-muted text-center" style={{ padding: "2rem" }}>No AI Agent prompts logged in SQLite database yet.</p>
            ) : (
              <div className="console-logs-list">
                {logs.map((log) => (
                  <div key={log.id} className="console-log-row">
                    <div className="log-row-header">
                      <span className="log-agent">{log.agent_name}</span>
                      <span className="log-tokens">
                        Tokens: {log.prompt_tokens ?? 0} (Prompt) / {log.completion_tokens ?? 0} (Completion)
                      </span>
                      <span className="log-time">{new Date(log.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <div className="log-details">
                      <div className="log-detail-block">
                        <strong>Prompt Payload:</strong>
                        <pre>{log.prompt_content.substring(0, 300)}...</pre>
                      </div>
                      <div className="log-detail-block">
                        <strong>Model Output:</strong>
                        <pre>{log.completion_content}</pre>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
