<p align="center">
  <h1 align="center">🛡️ Aegis AI — Investment Operating System</h1>
  <p align="center">
    <strong>A full-stack personal investment platform with deterministic financial engines, multi-agent AI advisory consensus, and a premium glassmorphic dashboard.</strong>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" />
    <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white" />
    <img src="https://img.shields.io/badge/Next.js-16.2-000000?logo=nextdotjs&logoColor=white" />
    <img src="https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&logoColor=white" />
    <img src="https://img.shields.io/badge/SQLite-SQLAlchemy_2.0-003B57?logo=sqlite&logoColor=white" />
    <img src="https://img.shields.io/badge/Tests-32_Passing-10B981?logo=pytest&logoColor=white" />
  </p>
</p>

---

## 📖 What Is Aegis AI?

Aegis AI is a **personal investment operating system** designed to manage a real portfolio like a professional fund. It is not a toy demo — it is an integrated platform that connects live market data, deterministic portfolio accounting, quantitative strategy backtesting, and a multi-agent AI advisory pipeline into a single system.

The platform is split into two major layers:

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Python + FastAPI + SQLite | Financial engine, data collection, AI pipeline, REST API |
| **Frontend** | Next.js + TypeScript + Vanilla CSS | Premium dark-mode dashboard with interactive charts |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 16)                     │
│  Dashboard │ Asset Universe │ Backtest & Sim │ AI Terminal   │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API (HTTP)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND (Python)                   │
│                                                             │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────────┐│
│  │ Routers  │  │   Engines    │  │     AI Pipeline        ││
│  │          │  │              │  │                        ││
│  │ /assets  │  │ Portfolio    │  │ Sentiment Agent        ││
│  │ /portfolio│ │ Backtester   │  │ Fundamentals Agent     ││
│  │ /simulation│ │ Monte Carlo │  │ Macro Agent            ││
│  │ /ai      │  │ Features     │  │ Portfolio Agent        ││
│  └──────────┘  └──────────────┘  │ Decision Auditor      ││
│                                  └────────────────────────┘│
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────────┐│
│  │ Plugins  │  │ Knowledge    │  │   Infrastructure       ││
│  │          │  │ Engine       │  │                        ││
│  │ Yahoo    │  │ Normalizer   │  │ Event Bus              ││
│  │ Finance  │  │ Resolver     │  │ Scheduler Daemon       ││
│  │ FRED     │  │ Relationship │  │ Notification Broker    ││
│  │          │  │ Tagger       │  │ Cache Manager          ││
│  └──────────┘  └──────────────┘  └────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              SQLite Database (18 Tables)                 ││
│  │  Assets │ Prices │ Financials │ Portfolio │ Transactions ││
│  │  News │ Sentiment │ Signals │ Theses │ Agent Logs       ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Core Features

### 1. Portfolio Management Engine
The portfolio engine is **deterministic** — no AI involved. It uses exact arithmetic to track:

- **Transaction Ledger**: Records every BUY, SELL, DEPOSIT, and WITHDRAW with timestamps, prices, commissions
- **Position Tracking**: Maintains current shares, average cost basis, and portfolio weights per asset
- **Performance Metrics**: Calculates Time-Weighted Return (TWRR), Money-Weighted Return (MWRR), Sharpe Ratio, Beta, and Max Drawdown
- **Dividend Forecasting**: Projects annual dividend income and portfolio-level yield

### 2. Live Market Data Pipeline
Real market data flows into the system automatically:

- **Yahoo Finance Plugin** → Daily OHLCV prices, corporate financial statements (Revenue, Net Income, EPS, Cash Flow, Debt)
- **FRED Plugin** → Macroeconomic yields, Treasury rates, CPI inflation data
- **Filesystem Cache** → SHA-256 hashed request caching to prevent API rate-limiting
- **Scheduler Daemon** → Background thread that auto-refreshes prices daily and yields weekly

### 3. Quantitative Backtesting & Simulation

#### Strategy Backtester
An event-driven backtesting engine that replays historical price data through trading strategies:

| Strategy | Logic |
|----------|-------|
| `sma_cross` | Dual Simple Moving Average crossover (short MA crosses above/below long MA) |
| `rsi_bounds` | RSI overbought/oversold boundaries trigger entries and exits |

Output includes: ending equity, cumulative return, Sharpe ratio, max drawdown, trade count, and an equity curve.

#### Monte Carlo Random Walk Simulator
Projects future portfolio value using geometric Brownian motion:
- Runs **100+ simulation paths** using historical mean returns and volatility
- Returns confidence intervals: **p5** (worst case), **p50** (median), **p95** (best case)
- Visualized as shaded area charts on the frontend

### 4. Multi-Agent AI Advisory Pipeline

This is the intelligence layer. Instead of asking a single AI model "should I buy?", Aegis runs a **5-agent consensus pipeline**:

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────┐
│ Sentiment Agent │───▶│ Fundamentals     │───▶│ Macro Agent  │
│                 │    │ Agent            │    │              │
│ Analyzes news   │    │ Analyzes balance │    │ Evaluates    │
│ sentiment scores│    │ sheets & ratios  │    │ yield curves │
│ (-1.0 to +1.0)  │    │ (FCF, debt, EPS) │    │ & risk score │
└─────────────────┘    └──────────────────┘    └──────┬───────┘
                                                      │
                                                      ▼
                       ┌──────────────────┐    ┌──────────────┐
                       │ Decision Auditor │◀───│ Portfolio    │
                       │                  │    │ Agent        │
                       │ Synthesizes all  │    │              │
                       │ evidence into    │    │ Recommends   │
                       │ BUY/SELL/HOLD    │    │ rebalancing  │
                       │ + evidence panel │    │ & allocations│
                       └──────────────────┘    └──────────────┘
```

**Each agent** receives structured data from the database, formulates an analytical prompt, sends it to an LLM, and returns structured JSON.

**The Decision Auditor** collects all agent evidence and produces:
- `final_decision`: BUY / SELL / HOLD / NO_ACTION
- `reasoning_summary`: Aggregated analytical reasoning
- `recommendation_details`: Actionable 1-sentence instruction
- `evidence_breakdown`: Structured takeaways from each specialist agent

#### AI Provider Fallback Chain
The AI Manager automatically routes through available LLM providers:

```
Gemini → Groq → OpenRouter → Ollama (local) → Mock Fallback
```

If one provider fails, the next is tried automatically. Every prompt and response is logged to the database for full auditability.

### 5. Investment Thesis Tracker
A long-term accountability system:
- Create investment theses with success criteria (e.g., "MSFT will reach $500 by Q4 due to cloud growth")
- Set review dates for automated boundary checks
- Track thesis status: `active` → `fulfilled` / `failed` / `abandoned`
- The AI Decision Agent can evaluate theses against current market conditions

### 6. Knowledge Engine
A data quality layer that preprocesses raw information:

| Component | Purpose |
|-----------|---------|
| **Normalizer** | Standardizes company names, removes noise characters |
| **Resolver** | Deduplicates entity references (e.g., "Apple" = "Apple Inc." = "AAPL") |
| **Relationship Builder** | Maps connections between entities (sector peers, supply chains) |
| **Tagger** | Classifies news and data records by topic, sector, and relevance |

### 7. Event Bus & Notifications
- **Event Bus**: Publish/subscribe pattern for system-wide event coordination (`price.updated`, `thesis.review_due`)
- **Notification Broker**: Monitors price movements and alerts on extreme day-over-day moves (>5%)
- **Signal System**: Database-persisted signals with severity levels (`info`, `warning`, `critical`)

---

## 🖥️ Frontend Dashboard

The frontend is a premium, dark-mode single-page application built with Next.js 16 and vanilla CSS.

### Dashboard Summary Tab
- **Metric Cards**: NAV, Cash Balance, TWRR, MWRR, Sharpe Ratio, Beta, Projected Dividend Yield
- **Holdings Table**: Current stock positions with shares, average cost, and portfolio weights
- **Transaction Form**: Log BUY/SELL/DEPOSIT/WITHDRAW transactions with real-time portfolio recalculation

### Asset Universe Tab
- **Searchable Asset Index**: Filter through all tracked stocks, ETFs, crypto, and indices
- **Interactive Price Chart**: Last 60 days of daily close prices rendered with Recharts
- **Financial Statements Matrix**: Annual revenue, net income, EPS, operating cash flow, total liabilities
- **News Sentiment Feed**: Recent articles with sentiment scores (-1.0 to +1.0) and AI-generated summaries

### Backtest & Simulation Tab
- **Strategy Backtester**: Configure ticker, date range, strategy (SMA Cross / RSI), and initial capital
- **Backtest Results**: Ending equity, cumulative return, Sharpe ratio, max drawdown, trade log
- **Monte Carlo Projector**: Run random walk simulations with p5/p50/p95 confidence interval area charts

### AI Advisor Terminal Tab
- **Multi-Agent Advisory**: Select a ticker, ask an investment question, and trigger the 5-agent consensus pipeline
- **Consensus Result Panel**: BUY/SELL/HOLD badge, reasoning summary, recommendation details
- **Evidence Breakdown Grid**: 4-card panel showing specific evidence from Sentiment, Fundamentals, Macro, and Portfolio agents
- **Consensus Flow Graph**: Visual pipeline showing the agent execution order
- **Investment Theses**: Create, track, and delete long-term investment theses
- **Token & Prompt Audit**: Scrollable console log of all AI prompts, responses, and token counts

---

## 📁 Project Structure

```
finance/
├── backend/
│   ├── ai/
│   │   ├── agents/
│   │   │   ├── sentiment_agent.py    # Agent 1: News sentiment scoring
│   │   │   ├── fundamentals_agent.py # Agent 2: Balance sheet analysis
│   │   │   ├── macro_agent.py        # Agent 3: Macroeconomic outlook
│   │   │   └── portfolio_agent.py    # Agent 4: Portfolio optimization
│   │   ├── decision.py               # Agent 5: Decision auditor & consensus
│   │   └── manager.py               # Multi-provider LLM router
│   ├── cache/
│   │   └── manager.py               # SHA-256 filesystem cache layer
│   ├── config/
│   │   └── settings.py              # Pydantic environment configuration
│   ├── database/
│   │   ├── connection.py            # SQLAlchemy engine & session factory
│   │   ├── init_db.py               # Database bootstrap with seed data
│   │   └── models.py               # 18-table SQLAlchemy ORM definitions
│   ├── knowledge/
│   │   ├── normalizer.py            # Text standardization
│   │   ├── resolver.py              # Entity deduplication
│   │   ├── relationship.py          # Entity linking
│   │   └── tagger.py                # Topic classification
│   ├── plugins/
│   │   ├── base.py                  # Abstract plugin interface
│   │   ├── yahoo.py                 # Yahoo Finance data collector
│   │   └── fred.py                  # FRED macroeconomic data collector
│   ├── portfolio/
│   │   ├── tracker.py               # Position & cash balance management
│   │   ├── performance.py           # TWRR, MWRR, Sharpe, Beta calculations
│   │   ├── features.py              # Quantitative feature store
│   │   └── dividends.py             # Dividend tracking & yield projection
│   ├── routers/
│   │   ├── assets.py                # /api/assets/* endpoints
│   │   ├── portfolio.py             # /api/portfolio/* endpoints
│   │   ├── simulation.py            # /api/simulation/* endpoints
│   │   └── ai.py                    # /api/ai/* endpoints
│   ├── simulation/
│   │   ├── backtester.py            # Event-driven strategy backtester
│   │   └── monte_carlo.py           # Geometric Brownian motion simulator
│   ├── tests/
│   │   ├── test_ai.py               # AI pipeline tests (7 tests)
│   │   ├── test_api.py              # API endpoint tests (5 tests)
│   │   ├── test_collectors.py       # Data collector tests (5 tests)
│   │   ├── test_db.py               # Database tests (3 tests)
│   │   ├── test_knowledge.py        # Knowledge engine tests (6 tests)
│   │   ├── test_portfolio.py        # Portfolio engine tests (2 tests)
│   │   ├── test_scheduler.py        # Scheduler tests (2 tests)
│   │   └── test_simulation.py       # Simulation engine tests (2 tests)
│   ├── event_bus.py                 # Pub/sub event coordination
│   ├── scheduler.py                 # Background job daemon
│   ├── notifications.py             # Price alert broker
│   ├── main.py                      # FastAPI application entry point
│   ├── verify_backend.py            # End-to-end integration test
│   └── requirements.txt             # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx             # Main application & tab router
│   │   │   ├── layout.tsx           # Root layout & metadata
│   │   │   └── globals.css          # Design system (1,400+ lines)
│   │   └── components/
│   │       ├── DashboardTab.tsx      # Portfolio dashboard view
│   │       ├── AssetsTab.tsx         # Asset universe browser
│   │       ├── SimulationTab.tsx     # Backtest & Monte Carlo view
│   │       ├── AITerminalTab.tsx     # AI advisory terminal
│   │       └── Sidebar.tsx          # Collapsible navigation
│   ├── package.json
│   └── tsconfig.json
│
├── .env.example                     # Environment variable template
├── .gitignore
└── README.md
```

---

## 🗄️ Database Schema (18 Tables)

| # | Table | Purpose |
|---|-------|---------|
| 1 | `assets` | Tracked stocks, ETFs, crypto, indices with metadata |
| 2 | `price_history` | Daily OHLCV price records per asset |
| 3 | `financial_statements` | Annual/quarterly income, balance sheet, cash flow |
| 4 | `news` | Raw news articles linked to assets |
| 5 | `news_summaries` | AI-generated summaries with sentiment scores |
| 6 | `economic_events` | FRED macro data (CPI, Treasury yields, rates) |
| 7 | `ai_reports` | Generated analytical reports (monthly, quarterly) |
| 8 | `decision_sessions` | Multi-agent consensus session logs |
| 9 | `portfolio` | Portfolio profiles with cash balances |
| 10 | `portfolio_positions` | Current holdings (shares, average cost) |
| 11 | `transactions` | Buy/sell/deposit/withdraw ledger |
| 12 | `watchlist` | Assets being monitored |
| 13 | `sentiment` | Aggregated sentiment scores per asset per source |
| 14 | `historical_backtests` | Saved backtest results and equity curves |
| 15 | `signals` | System-generated alerts (price moves, macro risks) |
| 16 | `agent_logs` | Every AI prompt, response, and token count |
| 17 | `system_logs` | Application-level diagnostic logs |
| 18 | `investment_theses` | Long-term thesis tracking with success criteria |

---

## 🔌 API Endpoints

### Assets (`/api/assets`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/assets/` | List all active assets in the universe |
| GET | `/assets/{ticker}/prices` | Get historical price data for a ticker |
| GET | `/assets/{ticker}/news` | Get news articles and sentiment for a ticker |
| GET | `/assets/{ticker}/financials` | Get financial statement data |
| POST | `/assets/collect/{ticker}` | Trigger manual data collection for a ticker |

### Portfolio (`/api/portfolio`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/portfolio/{id}` | Get portfolio summary (NAV, cash, metrics) |
| GET | `/portfolio/{id}/holdings` | Get current positions |
| GET | `/portfolio/{id}/transactions` | Get transaction history |
| POST | `/portfolio/{id}/transaction` | Log a new transaction |
| GET | `/portfolio/{id}/performance` | Get TWRR, MWRR, Sharpe, Beta |
| GET | `/portfolio/{id}/dividends` | Get projected dividend income |

### Simulation (`/api/simulation`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/simulation/backtest` | Run a strategy backtest |
| POST | `/simulation/monte-carlo` | Run Monte Carlo projection |

### AI (`/api/ai`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ai/decision-session` | Run multi-agent consensus session |
| POST | `/ai/evaluate-thesis` | Evaluate an investment thesis |
| GET | `/ai/theses` | List all investment theses |
| POST | `/ai/thesis` | Create a new thesis |
| PUT | `/ai/thesis/{id}` | Update a thesis |
| DELETE | `/ai/thesis/{id}` | Delete a thesis |
| GET | `/ai/logs` | Get AI prompt/response audit logs |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/pranavadhithya33/Aegis-AI-Investment-OS.git
cd Aegis-AI-Investment-OS
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Mac/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp ../.env.example ../.env
# Edit .env with your API keys (optional — system works without them using mock responses)

# Initialize database with seed data
python -c "from backend.database.init_db import initialize_database; initialize_database()"

# Start the API server
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Open the Application
Navigate to **http://localhost:3000** in your browser.

### 5. Run Tests
```bash
cd backend
.venv/Scripts/pytest   # Windows
# or
pytest                  # Mac/Linux
```

---

## 🔑 Environment Variables

Create a `.env` file in the project root (see `.env.example`):

```env
# Required
ENV=development
DATABASE_URL=sqlite:///data/aegis.db

# AI Providers (all optional — system uses mock fallbacks)
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
OPENROUTER_API_KEY=your_openrouter_key
OLLAMA_HOST=http://localhost:11434

# Logging
LOG_LEVEL=INFO
```

> **Note**: The system works fully without any AI API keys. It uses intelligent mock responses that simulate realistic agent outputs. Add real keys to get live LLM-powered analysis.

---

## 🧪 Test Suite

32 automated tests covering all major subsystems:

```
tests/test_ai.py .......              [ 21%]   # AI manager, agents, decision pipeline
tests/test_api.py .....               [ 37%]   # FastAPI endpoint integration
tests/test_collectors.py .....        [ 53%]   # Yahoo Finance & FRED plugins
tests/test_db.py ...                  [ 62%]   # Database CRUD operations
tests/test_knowledge.py ......        [ 81%]   # Normalizer, resolver, tagger
tests/test_portfolio.py ..            [ 87%]   # Portfolio tracker & performance
tests/test_scheduler.py ..            [ 93%]   # Background job scheduling
tests/test_simulation.py ..           [100%]   # Backtester & Monte Carlo

======================= 32 passed in 7.23s ========================
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend Framework | FastAPI 0.110+ |
| Database | SQLite + SQLAlchemy 2.0 (ORM) |
| Frontend Framework | Next.js 16.2 (Turbopack) |
| Language (Backend) | Python 3.11 |
| Language (Frontend) | TypeScript 5.x |
| Styling | Vanilla CSS (dark glassmorphic theme) |
| Charts | Recharts 3.9 |
| Icons | Lucide React |
| Market Data | Yahoo Finance (yfinance) |
| Macro Data | FRED (Federal Reserve Economic Data) |
| AI Providers | Google Gemini, Groq, OpenRouter, Ollama |
| HTTP Client | httpx |
| Testing | pytest |
| Scheduling | APScheduler |

---

## 📊 Design Decisions

### Why Deterministic Financial Engines?
The portfolio tracker, backtester, and Monte Carlo simulator use **exact arithmetic** (Python `Decimal` type), not AI. Financial calculations must be reproducible and auditable. AI is used only for analysis and recommendations — never for accounting.

### Why Multi-Agent Consensus?
A single AI model answering "should I buy?" is unreliable. By splitting the analysis into specialist agents (sentiment, fundamentals, macro, portfolio) and requiring a Decision Auditor to synthesize them, the system produces more balanced recommendations with transparent reasoning.

### Why SQLite?
For a personal investment OS, SQLite provides zero-configuration persistence with full ACID compliance. The 18-table schema supports complex relational queries without the overhead of PostgreSQL or MySQL. The system can be migrated to PostgreSQL by changing one connection string.

### Why Mock Responses?
Every AI agent has a fallback mock response. This ensures the system never crashes if API keys are missing or providers are down. It also enables full test suite execution without incurring API costs.

---

## 🗺️ Future Roadmap

- [ ] PWA support (service worker + install prompt)
- [ ] Watchlist/alert management UI
- [ ] Multi-portfolio support
- [ ] Real-time WebSocket price streaming
- [ ] PDF report generation (monthly/quarterly)
- [ ] Options chain analysis module
- [ ] Risk parity optimization engine

---

## 📝 License

This project is for personal and educational use.

---

<p align="center">
  <strong>Built with 🛡️ by Pranav Adhithya</strong>
</p>