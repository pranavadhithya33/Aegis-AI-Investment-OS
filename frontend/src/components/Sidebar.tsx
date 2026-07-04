"use client";

import React from "react";
import { 
  Home, 
  TrendingUp, 
  Brain, 
  Briefcase, 
  Cpu, 
  ChevronLeft, 
  ChevronRight,
  Database,
  Menu,
  X
} from "lucide-react";

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  backendHealthy: boolean;
}

export default function Sidebar({ activeTab, setActiveTab, backendHealthy }: SidebarProps) {
  const [collapsed, setCollapsed] = React.useState(false);
  const [mobileOpen, setMobileOpen] = React.useState(false);

  const menuItems = [
    { id: "dashboard", label: "Dashboard", icon: Home },
    { id: "simulation", label: "Simulations", icon: TrendingUp },
    { id: "ai", label: "AI Terminal", icon: Brain },
    { id: "assets", label: "Asset Universe", icon: Briefcase },
  ];

  return (
    <>
      {/* Mobile Toggle Bar */}
      <div className="mobile-header">
        <span className="logo-text title-gradient">AEGIS AI</span>
        <button className="mobile-toggle" onClick={() => setMobileOpen(!mobileOpen)}>
          {mobileOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Sidebar Container */}
      <aside className={`sidebar ${collapsed ? "collapsed" : ""} ${mobileOpen ? "mobile-open" : ""}`}>
        {/* Header */}
        <div className="sidebar-header">
          {!collapsed && <span className="sidebar-logo title-gradient">AEGIS AI</span>}
          {collapsed && <span className="sidebar-logo-collapsed text-gradient-cyan">Æ</span>}
          <button className="collapse-btn" onClick={() => setCollapsed(!collapsed)}>
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>

        {/* Connection status */}
        <div className="status-container">
          <span className="pulse-indicator" style={{ backgroundColor: backendHealthy ? "#10b981" : "#ef4444" }}></span>
          {!collapsed && (
            <span className="status-text">
              {backendHealthy ? "System Online" : "System Offline"}
            </span>
          )}
        </div>

        {/* Navigation Menu */}
        <nav className="sidebar-nav">
          {menuItems.map((item) => {
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
                title={item.label}
              >
                <Icon size={20} className="nav-icon" />
                {!collapsed && <span className="nav-label">{item.label}</span>}
              </button>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="sidebar-footer">
          <div className="footer-item">
            <Cpu size={16} className="footer-icon" />
            {!collapsed && <span className="footer-text">Gemini / Groq</span>}
          </div>
          <div className="footer-item">
            <Database size={16} className="footer-icon" />
            {!collapsed && <span className="footer-text">SQLite Active</span>}
          </div>
        </div>
      </aside>
    </>
  );
}
