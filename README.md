# 📊 AI Stock Screener - Intelligent Stock Analysis Platform

An advanced stock screening platform powered by AI that enables users to analyze stocks using natural language queries, manage portfolios, and set up intelligent price alerts with real-time notifications.

## 🎯 Project Overview

AI Stock Screener is a comprehensive stock analysis platform that combines the power of artificial intelligence with traditional financial analysis. Users can screen stocks using natural language queries like "Technology stocks with PE less than 20" or "Large cap stocks with positive profit for last 4 quarters", manage multiple portfolios, and receive real-time alerts when stock metrics meet specified conditions.

## 🧱 Technology Stack

### Backend
- **FastAPI**: High-performance Python web framework for building APIs
- **MySQL**: Robust relational database for storing stock data, user information, and portfolios
- **Redis**: In-memory caching for improved query performance (optional)
- **OpenAI**: Natural language processing for query understanding
- **JWT Authentication**: Secure user authentication and authorization

### Frontend
- **Streamlit**: Interactive Python-based web interface
- **Pandas**: Data manipulation and analysis
- **Requests**: HTTP client for API communication

### Data Ingestion
- **yfinance**: Real-time stock data fetching from Yahoo Finance
- **Python Scripts**: Automated data ingestion pipelines

## ⚙️ Core Features

### 1. AI-Powered Stock Screening
- **Natural Language Queries**: Ask questions in plain English
- **Intelligent Query Parsing**: AI converts natural language to structured queries
- **Multi-Criteria Filtering**: Combine multiple conditions (PE ratio, market cap, profitability, etc.)
- **Quarterly Financial Analysis**: Analyze revenue, EBITDA, and net profit trends
- **Analyst Recommendations**: View target prices and upside potential
- **Redis Caching**: Lightning-fast responses for repeated queries (10-minute cache)

### 2. Portfolio Management
- **Multiple Portfolios**: Create and manage unlimited portfolios
- **Add Holdings**: Search stocks by symbol and add to portfolio with auto-filled current price
- **Edit Holdings**: Update quantity and purchase price for any holding
- **Delete Holdings**: Remove individual holdings from portfolios
- **Holdings Tracking**: Track quantity, average price, and current value
- **Gain/Loss Analysis**: Real-time profit/loss calculations with percentage changes
- **Portfolio Summary**: Overview of total invested amount and current value
- **Stock-Level Details**: Detailed breakdown of each holding's performance
- **Portfolio Deletion**: Delete entire portfolios with confirmation

### 3. Intelligent Price Alerts
- **Multi-Metric Monitoring**: Track price, PE ratio, market cap, EPS, ROE, dividend yield
- **Flexible Conditions**: Set alerts with operators (>, <, >=, <=, =)
- **Real-Time Notifications**: Compact notification bell with badge counter
- **Alert Management**: Bulk operations (activate, deactivate, delete)
- **Trigger History**: View when and why alerts were triggered
- **Manual Refresh**: On-demand alert checking with one click
- **Smart Deduplication**: Shows only most recent trigger per alert

### 4. Redis Caching System
- **Graceful Fallback**: Works seamlessly with or without Redis
- **Performance Boost**: 30-40% faster query responses
- **Configurable TTL**: Customizable cache expiration times
- **Cache Management**: Health checks, statistics, and manual clearing
- **Monitoring Tools**: Built-in cache viewer utility

## 🚧 Problems Solved

### Traditional Stock Screening Challenges

- **Complex Query Syntax**: Traditional screeners require learning complex filter interfaces
  - ✅ **Solution**: Natural language queries - just ask in plain English
  
- **Manual Portfolio Tracking**: Spreadsheets and manual calculations are error-prone
  - ✅ **Solution**: Automated portfolio management with real-time calculations
  
- **Missed Opportunities**: Constantly checking stock prices is time-consuming
  - ✅ **Solution**: Intelligent alerts with real-time notifications
  
- **Slow Performance**: Repeated database queries slow down analysis
  - ✅ **Solution**: Redis caching for instant responses
  
- **Data Overload**: Too much information makes decision-making difficult
  - ✅ **Solution**: Focused, essential metrics with clean UI

## ✅ Key Benefits

- **Centralized Platform**: All stock analysis tools in one place
- **Better Communication**: Real-time alerts keep you informed
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
   - Password hashing with bcrypt
   - User registration and login

3. **Portfolio System** (`backend/portfolio.py`)
   - CRUD operations for portfolios and holdings
   - Real-time gain/loss calculations
   - Portfolio summary statistics

4. **Alert System** (`backend/alerts.py`, `backend/alert_checker.py`)
   - Alert creation and management
   - Background alert monitoring
   - Event tracking and notifications

5. **Caching Layer** (`backend/cache.py`)
   - Redis integration with fallback
   - Automatic cache invalidation
   - Performance monitoring

6. **Data Ingestion** (`ingestion/`)
   - Stock data fetching from Yahoo Finance
   - Fundamental metrics ingestion
   - Quarterly financial data
   - Analyst targets and recommendations

## 📊 Database Schema

### Core Tables
- **users**: User accounts and authentication
- **stocks**: Stock symbols and company information
- **fundamentals**: Current stock metrics (PE, EPS, market cap, etc.)
- **quarterly_finance**: Historical quarterly financial data
- **analyst_targets**: Analyst recommendations and target prices
- **portfolio**: User portfolios
- **portfolio_holdings**: Stock holdings in portfolios
- **alerts**: User-defined price alerts
- **alert_event**: Alert trigger history

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- MySQL 8.0+
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
Create a `.env` file in the root directory:
```env
# Database Configuration
DB_HOST=localhost
DB_USER=stock_user
DB_PASSWORD=Stock@123
DB_NAME=stock_db

# JWT Configuration
JWT_SECRET=your_secret_key_here
JWT_ALGORITHM=HS256

# AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Redis Configuration (Optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
CACHE_TTL=3600

# API Configuration
API_URL=http://127.0.0.1:8001
```

### Step 5: Data Ingestion
```bash
# Run all ingestion scripts
cd ingestion
python run_all.py
```

This will populate your database with:
- Stock symbols and company information
- Fundamental metrics
- Quarterly financial data
- Analyst targets and recommendations

### Step 6: Start Redis (Optional)
```bash
# Linux/macOS
redis-server

# Windows WSL
sudo service redis-server start

# Docker
docker run -d -p 6379:6379 --name redis redis:latest
```

See [REDIS_SETUP.md](REDIS_SETUP.md) for detailed Redis installation instructions.

### Step 7: Start Backend Server
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload
```

You should see:
```
✅ Redis cache enabled at localhost:6379
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
# Basic queries
"PE ratio > 15"
"Technology stocks with market cap > 100B"
"Dividend yield > 2%"

# Complex queries
"PE ratio >= 5 and positive net profit for last 4 quarters"
"Large cap stocks with ROE > 15 and debt to equity < 1"
"Healthcare stocks with EPS > 5 and PE ratio < 25"

# Quarterly analysis
"Stocks with increasing revenue for last 3 quarters"
"Companies with positive profit last 4 quarters"
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
5. **View Performance**: See real-time gain/loss for each holding with percentage changes
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
5. **Monitor**: Check notification bell for triggered alerts

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
- **Stock fundamentals**: 1-hour TTL
- **Automatic invalidation**: On data updates
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
- **Connection pooling** for concurrent requests

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: Bcrypt encryption for passwords
- **SQL Injection Prevention**: Parameterized queries
- **CORS Protection**: Restricted origins
- **Environment Variables**: Sensitive data in `.env` (gitignored)
- **User Isolation**: Users can only access their own data

## 🧪 Testing

### Run Tests
```bash
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

## 👥 Team Members

- **Satyam Mohanty**
- **Jayanth Reddy**
- **Samruddhi Garge**
- **Sahil Tripathy**
- **Abinaya Sri**
- **Srishti Sinha**

## 📁 Project Structure

```
Stock-Screener/
├── backend/
│   ├── ai/
│   │   ├── compiler.py          # SQL query compilation
│   │   ├── engine.py            # AI processing pipeline
│   │   ├── llm_parser.py        # Natural language parser
│   │   ├── routes.py            # AI API endpoints
│   │   └── validator.py         # Query validation
│   ├── alert_checker.py         # Alert monitoring service
│   ├── alerts.py                # Alert API endpoints
│   ├── auth.py                  # Authentication & JWT
│   ├── cache.py                 # Redis caching layer
│   ├── database.py              # Database connection
│   ├── main.py                  # FastAPI application
│   ├── portfolio.py             # Portfolio API endpoints
│   └── stocks.py                # Stock API endpoints
├── ingestion/
│   ├── db.py                    # Database utilities
│   ├── ingest_stocks.py         # Stock data ingestion
│   ├── ingest_fundamentals.py  # Fundamental metrics
│   ├── ingest_quarterly_financials.py  # Quarterly data
│   ├── ingest_analyst_targets.py       # Analyst recommendations
│   └── run_all.py               # Run all ingestion scripts
├── tests/
│   ├── test_validator.py        # Validator tests
│   ├── test_compiler.py         # Compiler tests
│   └── test_api_endpoints.py    # API integration tests
├── img/                         # Screenshots
├── streamlit_app.py             # Frontend application
├── schema.sql                   # Database schema
├── add_indexes.sql              # Performance indexes
├── requirements.txt             # Python dependencies
├── view_cache.py                # Redis cache viewer utility
├── REDIS_SETUP.md               # Redis installation guide
├── .env                         # Environment variables (gitignored)
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
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
- Contact the development team
- Check documentation in `REDIS_SETUP.md` for caching issues

## 🔧 Troubleshooting

### Portfolio Management Issues

**Problem**: "Stock symbol 'AAPL' not found in database"

**Solutions**:
1. Check if stocks are in database:
   ```bash
   python check_stocks.py
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

**Solution**: This is normal if Redis isn't installed. The application works fine without it. See [REDIS_SETUP.md](REDIS_SETUP.md) for installation.

## 🙏 Acknowledgments

- **Yahoo Finance** for stock data
- **Google Gemini AI** for natural language processing
- **FastAPI** for the excellent web framework
- **Streamlit** for the intuitive UI framework
- **Redis** for high-performance caching

---

**Built with ❤️ by the AI Stock Screener Team**

*Making stock analysis accessible to everyone through the power of AI*
#   A I - P o w e r e d - S t o c k - S c r e e n e r - a n d - A d v i s o r y - P l a t f o r m  
 