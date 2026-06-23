# 📊 AI Stock Screener - Intelligent Stock Analysis Platform

An advanced stock screening platform powered by AI that enables users to analyze stocks using natural language queries, manage portfolios, and set up intelligent metric alerts with in-app notifications.

## 🎯 Project Overview

AI Stock Screener is a comprehensive stock analysis platform that combines the power of artificial intelligence with traditional financial analysis. Users can screen stocks using natural language queries like "Technology stocks with PE less than 20" or "Large cap stocks with positive profit for last 4 quarters", manage multiple portfolios, and check alerts when stored stock metrics meet specified conditions.

## 🧱 Technology Stack

### Backend
- **FastAPI**: High-performance Python web framework for building APIs
- **MySQL**: Robust relational database for storing stock data, user information, and portfolios
- **Redis**: In-memory caching for improved query performance (optional)
- **OpenRouter (OpenAI-compatible API)**: Natural language processing for query understanding
- **JWT Authentication**: Secure user authentication and authorization

### Frontend
- **Streamlit**: Interactive Python-based web interface
- **Pandas**: Data manipulation and analysis
- **Requests**: HTTP client for API communication

### Data Ingestion
- **yfinance**: Stock data ingestion from Yahoo Finance (sole data source)
- **TiDB Cloud**: Serverless MySQL-compatible cloud database for production storage
- **GitHub Actions**: Automated scheduled ingestion (daily + monthly)
- **Python Scripts**: Modular ingestion pipeline

### Caching
- **Upstash Redis** (Singapore ap-southeast-1): Cloud Redis with TLS — same region as TiDB for minimal latency
- **REDIS_URL**: Standard `rediss://` URL — works with any Redis-compatible server
- **Graceful fallback**: App runs normally if cache is unavailable

## ⚙️ Core Features

### 1. AI-Powered Stock Screening
- **Natural Language Queries**: Ask questions in plain English
- **Sector Filtering**: Query by sector — `"tech stocks"`, `"healthcare stocks"`, `"energy stocks"` etc.
- **Country & ADR Filtering**: `"Indian stocks"`, `"Chinese ADRs"`, `"US large cap stocks"`
- **Intelligent Query Parsing**: AI converts natural language to structured SQL via DSL
- **Multi-Criteria Filtering**: Combine sector, PE, market cap, ROE, dividend yield and more
- **Quarterly Financial Analysis**: Revenue, EBITDA, and net profit trends — shown **only when the query asks for quarterly data**
- **Analyst Recommendations**: View target prices and upside potential
- **Redis Caching**: Lightning-fast responses for repeated queries (10-minute cache)

### 2. Portfolio Management
- **Multiple Portfolios**: Create and manage unlimited portfolios
- **Add Holdings**: Search stocks by symbol and add to portfolio with auto-filled current price
- **Edit Holdings**: Update quantity and purchase price for any holding
- **Delete Holdings**: Remove individual holdings from portfolios
- **Holdings Tracking**: Track quantity, average price, and current value
- **Gain/Loss Analysis**: Profit/loss calculations using the latest prices stored in the database
- **Portfolio Summary**: Overview of total invested amount and current value
- **Stock-Level Details**: Detailed breakdown of each holding's performance
- **Portfolio Deletion**: Delete entire portfolios with confirmation

### 3. Intelligent Price Alerts
- **Multi-Metric Monitoring**: Track price, PE ratio, market cap, EPS, ROE, dividend yield
- **Flexible Conditions**: Set alerts with operators (>, <, >=, <=, =)
- **In-App Notifications**: Compact notification bell with badge counter
- **Alert Management**: Bulk operations (activate, deactivate, delete)
- **Trigger History**: View when and why alerts were triggered
- **Manual Refresh**: On-demand alert checking with one click
- **Smart Deduplication**: Shows only most recent trigger per alert

### 4. Redis Caching System (Upstash)
- **Cloud Redis**: Upstash Redis in Singapore — same region as TiDB for lowest latency
- **Graceful Fallback**: Works seamlessly without cache if `REDIS_URL` is not set
- **Cache impact**: First query hits TiDB (~1-2s); same query again served in ~50ms (20-40x faster)
- **Screener TTL**: 10 minutes per query
- **Cache Management**: `/health`, `/cache/stats`, `/cache/clear` endpoints

## 🚧 Problems Solved

### Traditional Stock Screening Challenges

- **Complex Query Syntax**: Traditional screeners require learning complex filter interfaces
  - ✅ **Solution**: Natural language queries - just ask in plain English
  
- **Manual Portfolio Tracking**: Spreadsheets and manual calculations are error-prone
  - ✅ **Solution**: Automated portfolio calculations using stored market data
  
- **Missed Opportunities**: Constantly checking stock prices is time-consuming
  - ✅ **Solution**: Metric alerts with in-app notifications when alert checks run
  
- **Slow Performance**: Repeated database queries slow down analysis
  - ✅ **Solution**: Redis caching for instant responses
  
- **Data Overload**: Too much information makes decision-making difficult
  - ✅ **Solution**: Focused, essential metrics with clean UI

## ✅ Key Benefits

- **Centralized Platform**: All stock analysis tools in one place
- **Better Communication**: In-app alert results keep you informed when checks run
- **Higher Engagement**: Interactive UI makes analysis enjoyable
- **Streamlined Operations**: Automated calculations and data updates
- **Scalability**: Handles growing data and users efficiently
- **Security**: JWT authentication and encrypted passwords

## 🏗️ System Architecture

### Modular Design
```
┌─────────────────┐
│   Streamlit UI  │ ← User Interface Layer
└────────┬────────┘
         │
┌────────▼────────┐
│   FastAPI       │ ← API Layer (REST endpoints)
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼──┐
│ MySQL │ │Redis│ ← Data Layer
└───────┘ └─────┘
```

### Key Components

1. **AI Engine** (`backend/ai/`)
   - `llm_parser.py`: Converts natural language to DSL
   - `validator.py`: Validates query structure and constraints
   - `compiler.py`: Compiles DSL to SQL and executes queries
   - `engine.py`: Orchestrates the AI pipeline

2. **Authentication** (`backend/auth.py`)
   - JWT token-based authentication
   - Password hashing with a per-password salt and SHA-256
   - User registration and login

3. **Portfolio System** (`backend/portfolio.py`)
   - CRUD operations for portfolios and holdings
   - Real-time gain/loss calculations
   - Portfolio summary statistics

4. **Alert System** (`backend/alerts.py`, `backend/alert_checker.py`)
   - Alert creation and management
   - On-demand alert checking
   - Event tracking and notifications

5. **Caching Layer** (`backend/cache.py`)
   - Redis integration with fallback
   - Performance monitoring

6. **Data Ingestion** (`ingestion/`)
   - **yfinance only** — no third-party API keys required
   - 170+ stocks across US Tech, Finance, Healthcare, Consumer, Energy, Industrials, Real Estate, Utilities, and International ADRs (India, China, Europe, Asia-Pacific)
   - Fundamental metrics, quarterly financials (up to 5 years / 20 quarters), analyst targets
   - TiDB Cloud as production target via `.env.tidb` + SSL cert
   - GitHub Actions for automated scheduled refreshes

## 📊 Database Schema

### Core Tables
- **users**: User accounts and authentication
- **stocks**: 170+ stock symbols, company info, sector, country, ADR flag
- **fundamentals**: Current metrics (PE, EPS, market cap, ROE, price …)
- **quarterly_finance**: Up to 20 quarters (5 years) of revenue / EBITDA / net profit per stock
- **analyst_targets**: Analyst recommendations and target prices
- **portfolio**: User portfolios
- **portfolio_holdings**: Stock holdings in portfolios
- **alerts**: User-defined metric alerts
- **alert_event**: Alert trigger history

### Cloud Database
Production data is stored on **TiDB Cloud** (serverless MySQL-compatible).  
Connection config lives in `.env.tidb` (gitignored).  
The CA certificate is stored at `.certs/isrgrootx1.pem` (gitignored).

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- MySQL 8.0+ **or** TiDB Cloud account (for production)
- Redis (optional, for caching)

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd Stock-Screener
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Database Setup
```bash
# Login to MySQL
mysql -u root -p

# Run schema
source schema.sql

# (Optional) Add indexes for better performance
source add_indexes.sql
```

### Step 4: Environment Configuration

**Local MySQL** — create `.env` in the root:
```env
# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=stock_user
DB_PASSWORD=your_database_password
DB_NAME=stock_db

# JWT
JWT_SECRET_KEY=your_secret_key_here

# AI
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Redis (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
CACHE_TTL=3600

# API
API_URL=http://127.0.0.1:8001
```

**TiDB Cloud** — create `.env.tidb` in the root (used by ingestion scripts only):
```env
DB_TARGET=tidb
TIDB_HOST=gateway01.ap-southeast-1.prod.aws.tidbcloud.com
TIDB_PORT=4000
TIDB_USER=your_tidb_user
TIDB_PASSWORD=your_tidb_password
TIDB_DB=stock_db
TIDB_CA=.certs/isrgrootx1.pem
```
Download the ISRG Root X1 CA cert from [letsencrypt.org](https://letsencrypt.org/certs/isrgrootx1.pem) and place it at `.certs/isrgrootx1.pem`.

### Step 5: Data Ingestion

All ingestion uses **yfinance only** — no API keys required.

```bash
cd ingestion
python run_all.py          # runs all 4 steps
```

Or run individual steps:
```bash
python ingest_stocks.py             # Step 1 — stock symbols & company info
python ingest_fundamentals.py       # Step 2 — PE, price, ROE, EPS …
python ingest_quarterly_financials.py  # Step 3 — up to 20 quarters per stock
python ingest_analyst_targets.py    # Step 4 — analyst targets (derived from fundamentals)
```

Resume from a specific step (useful after a partial run):
```bash
python run_all.py --from 2    # skip stocks, start at fundamentals
```

**Target: TiDB Cloud** — ingestion scripts read from `.env.tidb` automatically.

### Step 6: Start Redis (Optional)
```bash
# Linux/macOS
redis-server

# Windows WSL
sudo service redis-server start

# Docker
docker run -d -p 6379:6379 --name redis redis:latest
```

### Step 7: Start Backend Server
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload
```

You should see:
```
[cache] Redis enabled at localhost:6379
INFO:     Uvicorn running on http://127.0.0.1:8001
```

### Step 8: Start Frontend
```bash
streamlit run streamlit_app.py
```

The application will open in your browser at `http://localhost:8501`

## 📖 Usage Guide

### Getting Started

1. **Sign Up**: Create a new account with your name, email, and password
2. **Login**: Access the platform with your credentials
3. **Explore**: Navigate through three main tabs:
   - 📊 Stock Screener
   - 💼 My Portfolios
   - 🔔 Price Alerts

### Stock Screening Examples

```
# Basic metric filters
"PE ratio > 15"
"Dividend yield > 2%"
"Large cap stocks with ROE > 15%"

# Sector filters
"Tech stocks with PE < 25"
"Healthcare stocks with profit margin > 10%"
"Finance stocks with ROE > 15%"
"Energy stocks with upside > 20%"

# Country / ADR filters
"Indian ADR stocks"
"Chinese stocks with market cap > 10B"
"US large cap stocks with dividend yield > 2%"

# Quarterly analysis (quarterly data shown only for these queries)
"Tech stocks with positive profit last 4 quarters"
"Companies with positive net profit for last 8 quarters"
"Healthcare stocks profitable last 4 quarters"

# Combined
"Large cap finance stocks with ROE > 15% and PE < 20"
"Tech ADR stocks with dividend yield > 1%"
```

### Portfolio Management

1. **Create Portfolio**: Click "Create New Portfolio" and enter a name
2. **Add Holdings**:
   - Enter stock symbol (e.g., AAPL, MSFT, GOOGL) and click "Search"
   - System fetches stock details and current market price from database
   - Enter quantity and purchase price (auto-filled with current price)
   - Click "Add to Portfolio"
3. **Edit Holdings**: Click ✏️ button next to any holding to update quantity or price
4. **Delete Holdings**: Click 🗑️ button to remove a holding from portfolio
5. **View Performance**: See gain/loss for each holding using the latest price stored in the database
6. **Track Summary**: Monitor total invested vs current value across all portfolios
7. **Delete Portfolio**: Click "Delete Portfolio" button with confirmation to remove entire portfolio

### Setting Up Alerts

1. **Navigate to Price Alerts tab**
2. **Click "Create New Alert"**
3. **Enter Details**:
   - Stock Symbol (e.g., AAPL, TSLA)
   - Metric (price, PE ratio, market cap, etc.)
   - Operator (>, <, >=, <=, =)
   - Threshold value
   - Select portfolio
4. **Click "Create Alert"**
5. **Monitor**: Run an alert check and use the notification bell to view triggered alerts

### Alert Management

- **Bulk Operations**: Select multiple alerts using checkboxes
- **Delete Selected**: Remove multiple alerts at once
- **Activate/Deactivate**: Toggle alert status in bulk
- **Manual Check**: Click "🔄 Check Alerts Now" to trigger immediate check
- **View History**: See recent triggers in the "Recent Alert Triggers" section

## 🔧 API Documentation

### Authentication Endpoints

#### POST `/auth/signup`
Register a new user
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepassword"
}
```

#### POST `/auth/login`
Login and get JWT token
```json
{
  "email": "john@example.com",
  "password": "securepassword"
}
```

### Screener Endpoints

#### POST `/ai/screener`
Run AI-powered stock screening
```
Query Parameter: query="PE ratio > 15"
Headers: Authorization: Bearer <token>
```

### Portfolio Endpoints

#### GET `/portfolio/`
Get all user portfolios

#### POST `/portfolio/`
Create new portfolio
```json
{
  "name": "Tech Portfolio"
}
```

#### GET `/portfolio/{portfolio_id}/holdings`
Get holdings for a specific portfolio

#### POST `/portfolio/{portfolio_id}/holdings`
Add a new holding to portfolio
```json
{
  "stock_id": 1,
  "quantity": 10,
  "avg_price": 150.50
}
```

#### PUT `/portfolio/{portfolio_id}/holdings/{holding_id}`
Update an existing holding
```json
{
  "stock_id": 1,
  "quantity": 15,
  "avg_price": 145.00
}
```

#### DELETE `/portfolio/{portfolio_id}/holdings/{holding_id}`
Delete a holding from portfolio

#### DELETE `/portfolio/{portfolio_id}`
Delete a portfolio and all its holdings

#### GET `/portfolio/stocks/search`
Search for a stock by symbol
```
Query Parameter: symbol="AAPL"
Headers: Authorization: Bearer <token>

Response:
{
  "stock_id": 1,
  "symbol": "AAPL",
  "company_name": "Apple Inc.",
  "current_price": 175.50
}
```

#### GET `/portfolio/summary`
Get portfolio summary statistics

### Alert Endpoints

#### GET `/alerts/`
Get all user alerts

#### POST `/alerts/`
Create new alert
```json
{
  "stock_id": 1,
  "portfolio_id": 1,
  "metric": "price",
  "operator": ">",
  "threshold": 150.00
}
```

#### DELETE `/alerts/{alert_id}`
Delete an alert

#### PATCH `/alerts/{alert_id}/toggle`
Toggle alert active status

#### POST `/alerts/check`
Manually trigger alert checking

#### GET `/alerts/notifications`
Get recent alert notifications

#### GET `/alerts/events`
Get alert trigger history

### Cache Endpoints

#### GET `/health`
Check system and cache health

#### GET `/cache/stats`
Get cache statistics

#### POST `/cache/clear`
Clear all cache

## 🛠️ Utility Scripts

### view_cache.py
Monitor and manage Redis cache
```bash
# List all cached keys
python view_cache.py list

# View specific key content
python view_cache.py view "screener:*"

# Search for keys
python view_cache.py search "screener:pe*"

# Get Redis statistics
python view_cache.py stats

# Delete keys
python view_cache.py delete "screener:*"

# Clear all cache
python view_cache.py clear

# Monitor in real-time
python view_cache.py monitor
```

## 📈 Performance Optimization

### Caching Strategy
- **Screener queries**: 10-minute TTL
- **Graceful fallback**: Direct database queries if Redis unavailable

### Database Indexes
Run `add_indexes.sql` to add performance indexes:
- Stock symbol lookups
- User-specific queries
- Alert filtering
- Portfolio holdings

### Query Optimization
- **DISTINCT** and **GROUP BY** prevent duplicate results
- **LEFT JOIN** for optional data (quarterly financials)
- **Indexed columns** for faster filtering
- **Per-request database connections** are closed after use

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: Per-password salts with SHA-256 hashing
- **SQL Injection Prevention**: Parameterized queries
- **CORS Protection**: Restricted origins
- **Environment Variables**: Sensitive data in `.env` (gitignored)
- **User Isolation**: Users can only access their own data

## 🧪 Testing

### Run Tests
```bash
# Install the test runner (it is not currently listed in requirements.txt)
pip install pytest

# Test validator
python -m pytest tests/test_validator.py

# Test compiler
python -m pytest tests/test_compiler.py

# Test API endpoints
python -m pytest tests/test_api_endpoints.py
```

### Manual Testing
1. **Backend Health**: Visit `http://127.0.0.1:8001/docs` for Swagger UI
2. **Cache Status**: `curl http://127.0.0.1:8001/health`
3. **Alert Checker**: `python backend/alert_checker.py`

## 📸 Screenshots

The application includes three main interfaces:

1. **Stock Screener**: AI-powered natural language stock screening
2. **Portfolio Management**: Track holdings and performance
3. **Price Alerts**: Set up and manage intelligent alerts

Screenshots available in `img/` directory.

## 🔮 Future Enhancements

### Planned Features
- **💳 Payment Integration**: UPI, cards, wallets for premium features
- **📊 Advanced Analytics**: Predictive models and trend analysis
- **🤖 AI Recommendations**: Personalized stock suggestions
- **📱 Mobile App**: iOS and Android applications
- **🔔 Multi-Channel Notifications**: Email, SMS, push notifications
- **📈 Technical Analysis**: Chart patterns and indicators
- **🌐 Multi-Market Support**: International stock exchanges
- **👥 Social Features**: Share portfolios and strategies

## 🤖 Automated Ingestion (GitHub Actions)

Data refreshes automatically via `.github/workflows/ingest.yml`:

| Schedule | Runs | Purpose |
|---|---|---|
| Weekdays Mon–Fri, 6 AM UTC | `fundamentals` + `analyst_targets` | Refresh daily prices & metrics |
| 2nd of every month, 3 AM UTC | All 4 scripts | Full monthly refresh |
| Manual (Actions tab) | Any step: `all / stocks / fundamentals / quarterly / analyst` | On-demand |

### Setup GitHub Secrets
Go to **Repo → Settings → Secrets → Actions** and add:

| Secret | Value |
|---|---|
| `TIDB_HOST` | TiDB Cloud host |
| `TIDB_PORT` | `4000` |
| `TIDB_USER` | TiDB username |
| `TIDB_PASSWORD` | TiDB password |
| `TIDB_DB` | `stock_db` |
| `TIDB_CA_CERT` | Full contents of `.certs/isrgrootx1.pem` |

> `TIDB_CA_CERT` is the **file contents** (paste the PEM text), not a path.

See [INGESTION_SCHEDULE.md](INGESTION_SCHEDULE.md) for full details.

## 📁 Project Structure

```
Stock-Screener/
├── .github/
│   └── workflows/
│       └── ingest.yml           # Automated ingestion schedule
├── backend/
│   ├── ai/
│   │   ├── compiler.py          # DSL → SQL compilation
│   │   ├── engine.py            # AI processing pipeline
│   │   ├── llm_parser.py        # Natural language → DSL parser
│   │   ├── routes.py            # AI API endpoints
│   │   └── validator.py         # Query validation
│   ├── alert_checker.py         # Alert monitoring service
│   ├── alerts.py                # Alert API endpoints
│   ├── auth.py                  # Authentication & JWT
│   ├── cache.py                 # Redis caching layer
│   ├── database.py              # Database connection (local/TiDB)
│   ├── main.py                  # FastAPI application
│   ├── portfolio.py             # Portfolio API endpoints
│   └── stocks.py                # Stock API endpoints
├── ingestion/
│   ├── db.py                    # TiDB Cloud connection (reads .env.tidb)
│   ├── ingest_stocks.py         # Step 1 — stock symbols & sectors
│   ├── ingest_fundamentals.py   # Step 2 — PE, price, ROE, EPS …
│   ├── ingest_quarterly_financials.py  # Step 3 — up to 20 quarters
│   ├── ingest_analyst_targets.py       # Step 4 — analyst targets
│   └── run_all.py               # Pipeline runner (supports --from N)
├── tests/
│   ├── test_validator.py
│   ├── test_compiler.py
│   └── test_api_endpoints.py
├── img/                         # Screenshots
├── streamlit_app.py             # Frontend application
├── schema.sql                   # Database schema
├── add_indexes.sql              # Performance indexes
├── requirements.txt             # Python dependencies
├── view_cache.py                # Redis cache viewer utility
├── INGESTION_SCHEDULE.md        # GitHub Actions setup guide
├── .env                         # Local env (gitignored)
├── .env.tidb                    # TiDB Cloud env (gitignored)
├── .certs/                      # TiDB SSL cert (gitignored)
├── .gitignore
└── README.md
```

## ⚠️ Disclaimers

### General Disclaimer
This application is for educational and informational purposes only. The data, analysis, and recommendations provided should not be considered as financial advice. Always consult with a qualified financial advisor before making investment decisions.

### Stock Screener Disclaimer
The screening results are based on historical data and should not be considered as investment recommendations. Past performance does not guarantee future results. Always conduct your own research before making investment decisions.

### Portfolio Disclaimer
Portfolio tracking is for educational and informational purposes only. The values shown are based on current market data and may not reflect actual trading prices. This tool does not provide investment advice or recommendations.

### Price Alerts Disclaimer
Price alerts are for informational purposes only and should not be considered as trading signals or investment advice. Alert triggers are based on available market data and may have delays. Always verify information independently before making any investment decisions.

## 📄 License

This project is for educational purposes. Please ensure compliance with data provider terms of service when using financial data APIs.

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Include relevant logs and setup details, but never include credentials

## 🔧 Troubleshooting

### Portfolio Management Issues

**Problem**: "Stock symbol 'AAPL' not found in database"

**Solutions**:
1. Check whether the `stocks` table contains data in MySQL:
   ```bash
   mysql -u stock_user -p stock_db -e "SELECT COUNT(*) AS stock_count FROM stocks;"
   ```

2. If no stocks found, run data ingestion:
   ```bash
   cd ingestion
   python run_all.py
   ```

3. Restart backend server after adding new endpoints:
   ```bash
   # Stop current server (Ctrl+C)
   uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload
   ```

**Problem**: Holdings not showing current price

**Solution**: Run fundamentals ingestion to populate current prices:
```bash
cd ingestion
python ingest_fundamentals.py
```

**Problem**: Cannot add holdings - 404 error

**Solution**: 
1. Ensure backend server is running
2. Check API URL in `.env` file: `API_URL=http://127.0.0.1:8001`
3. Restart backend server to register new routes

### Alert System Issues

**Problem**: Alerts not triggering

**Solution**: 
1. Manually check alerts: Click "🔄 Check Alerts Now" button
2. Verify stock has current price in fundamentals table
3. Check alert conditions are correct

### Cache Issues

**Problem**: Redis connection failed

**Solution**: This is normal if Redis isn't installed. The application continues without caching. Start Redis using one of the commands in the setup section if caching is required.

## 🙏 Acknowledgments

- **Yahoo Finance** for stock data
- **Openrouter AI** for natural language processing
- **FastAPI** for the excellent web framework
- **Streamlit** for the intuitive UI framework
- **Redis** for high-performance caching

---

**Built with ❤️ by the AI Stock Screener Team**

*Making stock analysis accessible to everyone through the power of AI*
