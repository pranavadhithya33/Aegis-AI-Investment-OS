"use client";

import React, { useState, useEffect } from "react";
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid, 
  ResponsiveContainer 
} from "recharts";
import { 
  Search, 
  TrendingUp, 
  BookOpen, 
  Newspaper,
  ChevronRight,
  TrendingDown,
  AlertCircle
} from "lucide-react";

export default function AssetsTab() {
  const [assets, setAssets] = useState<any[]>([]);
  const [selectedTicker, setSelectedTicker] = useState("AAPL");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Loaded Details
  const [meta, setMeta] = useState<any>(null);
  const [priceHistory, setPriceHistory] = useState<any[]>([]);
  const [financials, setFinancials] = useState<any[]>([]);
  const [news, setNews] = useState<any[]>([]);

  // Search filter
  const [search, setSearch] = useState("");

  // Fetch asset universe
  useEffect(() => {
    async function loadAssets() {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/assets/");
        const data = await res.json();
        setAssets(data);
      } catch (err) {
        console.error(err);
      }
    }
    loadAssets();
  }, []);

  // Fetch detailed asset parameters on selected ticker change
  useEffect(() => {
    if (!selectedTicker) return;
    
    async function loadAssetDetails() {
      setLoading(true);
      setError(null);
      try {
        // Fetch metadata
        const metaRes = await fetch(`http://127.0.0.1:8000/api/assets/${selectedTicker}`);
        const metaData = await metaRes.json();
        setMeta(metaData);

        // Fetch prices
        const priceRes = await fetch(`http://127.0.0.1:8000/api/assets/${selectedTicker}/price?limit=60`);
        const priceData = await priceRes.json();
        setPriceHistory(priceData);

        // Fetch financials
        const finRes = await fetch(`http://127.0.0.1:8000/api/assets/${selectedTicker}/financials`);
        const finData = await finRes.json();
        setFinancials(finData);

        // Fetch news
        const newsRes = await fetch(`http://127.0.0.1:8000/api/assets/${selectedTicker}/news`);
        const newsData = await newsRes.json();
        setNews(newsData);
      } catch (err) {
        console.error(err);
        setError(`Failed to retrieve data series for ticker ${selectedTicker}`);
      } finally {
        setLoading(false);
      }
    }

    loadAssetDetails();
  }, [selectedTicker]);

  const filteredAssets = assets.filter(
    (a) => a.ticker.toLowerCase().includes(search.toLowerCase()) || 
           a.name.toLowerCase().includes(search.toLowerCase())
  );

  const latestPrice = priceHistory.length > 0 ? priceHistory[priceHistory.length - 1].close : 0;
  const previousPrice = priceHistory.length > 1 ? priceHistory[priceHistory.length - 2].close : latestPrice;
  const priceChange = latestPrice - previousPrice;
  const priceChangePct = previousPrice > 0 ? (priceChange / previousPrice) * 100 : 0;

  return (
    <div className="assets-tab-container fade-in">
      {/* 1. Left Sidebar: Assets list */}
      <div className="assets-list-sidebar glass-panel">
        <div className="search-bar-container">
          <Search size={16} className="text-muted" />
          <input 
            type="text" 
            placeholder="Search universe..." 
            className="form-input search-input"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="assets-scroller">
          {filteredAssets.map((asset) => (
            <button
              key={asset.id}
              className={`asset-list-item ${selectedTicker === asset.ticker ? "active" : ""}`}
              onClick={() => setSelectedTicker(asset.ticker)}
            >
              <div>
                <span className="asset-list-ticker">{asset.ticker}</span>
                <span className="asset-list-name">{asset.name}</span>
              </div>
              <ChevronRight size={16} className="item-arrow" />
            </button>
          ))}
        </div>
      </div>

      {/* 2. Right Workspace: Selected Asset Details */}
      <div className="asset-workspace">
        {loading && <div className="loading-state">Syncing yFinance datasets...</div>}

        {error && (
          <div className="error-panel glass-panel">
            <AlertCircle className="text-error" size={24} />
            <p>{error}</p>
          </div>
        )}

        {!loading && meta && (
          <div className="asset-details-grid">
            {/* Header Quote Block */}
            <div className="asset-quote-header glass-panel">
              <div>
                <span className="quote-asset-type">{meta.asset_type.toUpperCase()} &bull; {meta.sector || "General"}</span>
                <h2>{meta.name} ({meta.ticker})</h2>
              </div>
              <div className="quote-price-block">
                <span className="quote-price">${latestPrice.toFixed(2)}</span>
                <span className={`quote-change ${priceChange >= 0 ? "text-success" : "text-error"}`}>
                  {priceChange >= 0 ? "+" : ""}{priceChange.toFixed(2)} ({priceChangePct.toFixed(2)}%)
                </span>
              </div>
            </div>

            {/* Price Chart */}
            <div className="asset-chart-panel glass-panel">
              <div className="panel-title flex-row-center">
                <TrendingUp size={18} className="text-gradient-cyan" />
                <h3>Historical Quote (Last 60 Days)</h3>
              </div>
              <div style={{ width: "100%", height: 260 }}>
                <ResponsiveContainer>
                  <LineChart data={priceHistory} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={10} tickLine={false} />
                    <YAxis stroke="var(--text-muted)" fontSize={10} domain={["auto", "auto"]} tickLine={false} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: "#0d1321", borderColor: "var(--border-color)", color: "#fff" }}
                      labelStyle={{ color: "var(--accent-cyan)", fontWeight: 700 }}
                    />
                    <Line type="monotone" dataKey="close" stroke="var(--accent-cyan)" strokeWidth={2.5} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Financial Statements */}
            <div className="asset-financials-panel glass-panel">
              <div className="panel-title flex-row-center">
                <BookOpen size={18} className="text-gradient-cyan" />
                <h3>Corporate Financial Statements</h3>
              </div>
              {financials.length === 0 ? (
                <div className="empty-state">No corporate statements stored in database.</div>
              ) : (
                <div className="table-responsive">
                  <table className="holdings-table">
                    <thead>
                      <tr>
                        <th>Period</th>
                        <th>Revenue</th>
                        <th>Net Income</th>
                        <th>Operating Cash Flow</th>
                        <th>Total Liabilities</th>
                        <th>EPS</th>
                      </tr>
                    </thead>
                    <tbody>
                      {financials.map((fin, idx) => (
                        <tr key={idx}>
                          <td style={{ fontWeight: 700 }}>{fin.period}</td>
                          <td>{fin.revenue ? `$${(fin.revenue / 1e6).toFixed(1)}M` : "N/A"}</td>
                          <td>{fin.net_income ? `$${(fin.net_income / 1e6).toFixed(1)}M` : "N/A"}</td>
                          <td>{fin.operating_cash_flow ? `$${(fin.operating_cash_flow / 1e6).toFixed(1)}M` : "N/A"}</td>
                          <td>{fin.total_liabilities ? `$${(fin.total_liabilities / 1e6).toFixed(1)}M` : "N/A"}</td>
                          <td>{fin.eps ? `$${fin.eps.toFixed(2)}` : "N/A"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* News and Sentiment */}
            <div className="asset-news-panel glass-panel">
              <div className="panel-title flex-row-center">
                <Newspaper size={18} className="text-gradient-cyan" />
                <h3>Recent News Sentiment Audit</h3>
              </div>
              {news.length === 0 ? (
                <div className="empty-state">No news signals scanned for this ticker.</div>
              ) : (
                <div className="news-signals-list">
                  {news.map((item) => (
                    <div key={item.id} className="news-signal-item">
                      <div className="news-item-top">
                        <a href={item.url} target="_blank" rel="noopener noreferrer" className="news-title-link">
                          {item.title}
                        </a>
                        <span className={`sentiment-score-badge ${item.sentiment_score >= 0.1 ? "pos" : item.sentiment_score <= -0.1 ? "neg" : "neu"}`}>
                          {(item.sentiment_score ?? 0).toFixed(2)} Sentiment
                        </span>
                      </div>
                      <span className="news-meta">{item.source} &bull; {new Date(item.published_at).toLocaleDateString()}</span>
                      {item.summary && (
                        <p className="news-summary-text">{item.summary}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
