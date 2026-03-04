CREATE TABLE IF NOT EXISTS customers (
    customer_id BIGINT PRIMARY KEY,
    country VARCHAR(2) NOT NULL,
    account_age_days INT NOT NULL,
    is_vip BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS merchants (
    merchant_id BIGINT PRIMARY KEY,
    merchant_category VARCHAR(80) NOT NULL,
    risk_tier VARCHAR(16) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(customer_id),
    merchant_id BIGINT NOT NULL REFERENCES merchants(merchant_id),
    amount NUMERIC(12, 2) NOT NULL,
    channel VARCHAR(16) NOT NULL,
    card_present BOOLEAN NOT NULL,
    event_time TIMESTAMP NOT NULL,
    is_fraud BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_customer_time
ON transactions(customer_id, event_time);

CREATE INDEX IF NOT EXISTS idx_transactions_fraud
ON transactions(is_fraud);
