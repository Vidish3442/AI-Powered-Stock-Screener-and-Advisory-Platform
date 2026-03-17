USE stock_db;

CREATE INDEX idx_stocks_sector ON stocks(sector);
CREATE INDEX idx_stocks_industry ON stocks(industry);
CREATE INDEX idx_stocks_country ON stocks(country);
CREATE INDEX idx_stocks_market_cap_category ON stocks(market_cap_category);
CREATE INDEX idx_stocks_is_adr ON stocks(is_adr);

CREATE INDEX idx_fundamentals_pe_ratio ON fundamentals(pe_ratio);
CREATE INDEX idx_fundamentals_market_cap ON fundamentals(market_cap);
CREATE INDEX idx_fundamentals_price_to_book ON fundamentals(price_to_book);
CREATE INDEX idx_fundamentals_dividend_yield ON fundamentals(dividend_yield);
CREATE INDEX idx_fundamentals_profit_margin ON fundamentals(profit_margin);
CREATE INDEX idx_fundamentals_beta ON fundamentals(beta);
CREATE INDEX idx_fundamentals_roe ON fundamentals(roe);
CREATE INDEX idx_fundamentals_current_price ON fundamentals(current_price);

CREATE INDEX idx_quarterly_stock_year_quarter ON quarterly_finance(stock_id, year DESC, quarter DESC);
CREATE INDEX idx_quarterly_net_profit ON quarterly_finance(net_profit);
CREATE INDEX idx_quarterly_revenue ON quarterly_finance(revenue);

CREATE INDEX idx_users_email_lookup ON users(email);

CREATE INDEX idx_analyst_targets_stock_id ON analyst_targets(stock_id);
CREATE INDEX idx_analyst_targets_recommendation ON analyst_targets(recommendation);
CREATE INDEX idx_analyst_targets_target_price ON analyst_targets(target_price);
CREATE INDEX idx_analyst_targets_updated_at ON analyst_targets(updated_at);

-- Portfolio performance indexes
CREATE INDEX idx_portfolio_user_id ON portfolio(user_id);
CREATE INDEX idx_portfolio_name ON portfolio(name);

-- Portfolio holdings performance indexes  
CREATE INDEX idx_portfolio_holdings_portfolio_id ON portfolio_holdings(portfolio_id);
CREATE INDEX idx_portfolio_holdings_stock_id ON portfolio_holdings(stock_id);
CREATE INDEX idx_portfolio_holdings_quantity ON portfolio_holdings(quantity);
CREATE INDEX idx_portfolio_holdings_avg_price ON portfolio_holdings(avg_price);
CREATE INDEX idx_portfolio_holdings_updated_at ON portfolio_holdings(updated_at);

ANALYZE TABLE stocks;
ANALYZE TABLE fundamentals;
ANALYZE TABLE quarterly_finance;
ANALYZE TABLE users;
ANALYZE TABLE analyst_targets;
ANALYZE TABLE portfolio;
ANALYZE TABLE portfolio_holdings;

SELECT 'Performance indexes creation completed!' as status;