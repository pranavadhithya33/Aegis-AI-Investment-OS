"use client";

import React, { useState, useEffect } from "react";
import { 
  LayoutDashboard, 
  Coins, 
  BarChart3, 
  Terminal, 
  Menu, 
  ChevronLeft, 
  ChevronRight,
  TrendingUp,
  Activity,
  Cpu
} from "lucide-react";

import DashboardTab from "@/components/DashboardTab";
import AssetsTab from "@/components/AssetsTab";
import SimulationTab from "@/components/SimulationTab";
import AITerminalTab from "@/components/AITerminalTab";

export default function Home() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [portfolioId, setPortfolioId] = useState<number>(1);
  const [portfolios, setPortfolios] = useState<any[]>([]);
  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);

  // Fetch available portfolios
  useEffect(() => {
    async function fetchPortfolios() {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/portfolio/");
        const data = await res.json();
        setPortfolios(data);
        if (data.length > 0) {
          setPortfolioId(data[0].id);
        }
      } catch (err) {
        console.error("Failed to load portfolios:", err);
      }
    }
    fetchPortfolios();
  }, []);

  const navItems = [
    { id: "dashboard", label: "Dashboard Summary", icon: LayoutDashboard },
    { id: "assets", label: "Asset Universe", icon: Coins },
    { id: "simulation", label: "Backtest & Sim", icon: BarChart3 },
    { id: "ai_terminal", label: "AI Advisor Terminal", icon: Terminal },
  ];

  return (
    <div className="app-container">
      {/* Mobile Top Navbar */}
      <header className="mobile-header">
        <span className="logo-text title-gradient">AEGIS AI</span>
        <button className="mobile-toggle" onClick={() => setMobileOpen(!mobileOpen)}>
          <Menu size={24} />
        </button>
      </header>

      {/* Sidebar Navigation */}
      <aside className={`sidebar ${sidebarCollapsed ? "collapsed" : ""} ${mobileOpen ? "mobile-open" : ""}`}>
        <div className="sidebar-header">
          {!sidebarCollapsed ? (
            <span className="sidebar-logo title-gradient">AEGIS AI</span>
          ) : (
            <span className="sidebar-logo-collapsed text-gradient-cyan">Æ</span>
          )}
          <button 
            className="collapse-btn" 
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            title={sidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          >
            {sidebarCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
          </button>
        </div>

        {/* Real-time System Engine Status */}
        <div className="status-container">
          <span className="pulse-indicator"></span>
          {!sidebarCollapsed && <span className="status-text">Engine Online</span>}
        </div>

        {/* Navigation List */}
        <nav className="sidebar-nav">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                className={`nav-item ${isActive ? "active" : ""}`}
                onClick={() => {
                  setActiveTab(item.id);
                  setMobileOpen(false);
                }}
              >
                <Icon size={18} className="nav-icon" />
                {!sidebarCollapsed && <span className="nav-label">{item.label}</span>}
              </button>
            );
          })}
        </nav>

        {/* Sidebar Footer metadata */}
        <div className="sidebar-footer">
          {portfolios.length > 1 && !sidebarCollapsed && (
            <div className="portfolio-switcher" style={{ marginBottom: "0.5rem" }}>
              <label style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 600 }}>ACTIVE PROFILE</label>
              <select 
                className="form-input" 
                style={{ padding: "0.4rem 0.6rem", fontSize: "0.85rem", marginTop: "0.2rem" }}
                value={portfolioId} 
                onChange={(e) => setPortfolioId(Number(e.target.value))}
              >
                {portfolios.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
          )}

          <div className="footer-item">
            <Cpu size={14} className="footer-icon" />
            {!sidebarCollapsed && <span className="footer-text">v2.4.0-cons</span>}
          </div>
          <div className="footer-item">
            <Activity size={14} className="footer-icon" />
            {!sidebarCollapsed && <span className="footer-text">SQLite Active</span>}
          </div>
        </div>
      </aside>

      <main className="main-content">
        {activeTab === "dashboard" && (
          <DashboardTab 
            portfolioId={portfolioId} 
            refreshTrigger={refreshTrigger} 
            setRefreshTrigger={setRefreshTrigger} 
          />
        )}
        {activeTab === "assets" && <AssetsTab />}
        {activeTab === "simulation" && <SimulationTab portfolioId={portfolioId} />}
        {activeTab === "ai_terminal" && <AITerminalTab portfolioId={portfolioId} />}
      </main>
    </div>
  );
}
