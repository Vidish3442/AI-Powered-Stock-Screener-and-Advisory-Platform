CREATE DATABASE IF NOT EXISTS stock_db;
USE stock_db;
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE stocks (
    stock_id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    company_name VARCHAR(100),
    sector VARCHAR(50),
    industry VARCHAR(50),
    exchange VARCHAR(20),
    country VARCHAR(50) DEFAULT 'US',
    market_cap_category ENUM('Mega', 'Large', 'Mid', 'Small', 'Micro') DEFAULT 'Large',
    is_adr BOOLEAN DEFAULT FALSE
);
CREATE TABLE fundamentals (
    fundamental_id INT AUTO_INCREMENT PRIMARY KEY,
    stock_id INT UNIQUE,
    pe_ratio DECIMAL(10,2),
    eps DECIMAL(10,2),
    market_cap BIGINT,
    roe DECIMAL(5,2),
    debt_equity DECIMAL(5,2),
    price_to_book DECIMAL(10,2),
    dividend_yield DECIMAL(5,4),
    profit_margin DECIMAL(5,4),
    beta DECIMAL(5,2),
    current_price DECIMAL(10,2),
    updated_at TIMESTAMP,
    CONSTRAINT fk_fund_stock
        FOREIGN KEY (stock_id)
        REFERENCES stocks(stock_id)
        ON DELETE CASCADE
);
CREATE TABLE quarterly_finance (
    qf_id INT AUTO_INCREMENT PRIMARY KEY,
    stock_id INT,
    quarter VARCHAR(5),
    year INT,
    revenue BIGINT,
    ebitda BIGINT,
    net_profit BIGINT,
    UNIQUE (stock_id, quarter, year),
    CONSTRAINT fk_qf_stock
        FOREIGN KEY (stock_id)
        REFERENCES stocks(stock_id)
        ON DELETE CASCADE
);
CREATE TABLE portfolio (
    portfolio_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL DEFAULT 'My Portfolio',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_port_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,
    UNIQUE (user_id, name)
);

CREATE TABLE portfolio_holdings (
    holding_id INT AUTO_INCREMENT PRIMARY KEY,
    portfolio_id INT NOT NULL,
    stock_id INT NOT NULL,
    quantity INT NOT NULL CHECK (quantity >= 0),
    avg_price DECIMAL(10,2) NOT NULL CHECK (avg_price >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_ph_portfolio
        FOREIGN KEY (portfolio_id)
        REFERENCES portfolio(portfolio_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_ph_stock
        FOREIGN KEY (stock_id)
        REFERENCES stocks(stock_id)
        ON DELETE CASCADE,
    UNIQUE (portfolio_id, stock_id)
);
CREATE TABLE alerts (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    stock_id INT,
    portfolio_id INT,
    metric VARCHAR(50) NOT NULL,
    operator VARCHAR(10) NOT NULL,
    threshold DECIMAL(10,2) NOT NULL,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_alert_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,
    
    CONSTRAINT fk_alert_stock
        FOREIGN KEY (stock_id)
        REFERENCES stocks(stock_id)
        ON DELETE CASCADE,
    
    CONSTRAINT fk_alert_portfolio
        FOREIGN KEY (portfolio_id)
        REFERENCES portfolio(portfolio_id)
        ON DELETE CASCADE,
    
    INDEX idx_user_alerts (user_id),
    INDEX idx_stock_alerts (stock_id),
    INDEX idx_active_alerts (is_active)
);

CREATE TABLE alert_event (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    alert_id INT NOT NULL,
    stock_id INT NOT NULL,
    triggered_value DECIMAL(10,2) NOT NULL,
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_event_alert
        FOREIGN KEY (alert_id)
        REFERENCES alerts(alert_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_event_stock
        FOREIGN KEY (stock_id)
        REFERENCES stocks(stock_id)
        ON DELETE CASCADE
);

CREATE TABLE analyst_targets (
    target_id INT AUTO_INCREMENT PRIMARY KEY,
    stock_id INT NOT NULL,
    target_price DECIMAL(10,2),
    current_price DECIMAL(10,2),
    recommendation ENUM('Buy', 'Hold', 'Sell'),
    analyst_firm VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_target_stock
        FOREIGN KEY (stock_id)
        REFERENCES stocks(stock_id)
        ON DELETE CASCADE
);
CREATE USER 'stock_user'@'localhost' IDENTIFIED BY 'Stock@123';

GRANT SELECT, INSERT, UPDATE, DELETE
ON stock_db.*
TO 'stock_user'@'localhost';


FLUSH PRIVILEGES;
