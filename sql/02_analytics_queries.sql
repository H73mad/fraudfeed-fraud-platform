-- Fraud rate by channel
SELECT
    channel,
    COUNT(*) AS tx_count,
    SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END) AS fraud_count,
    ROUND(100.0 * SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END) / COUNT(*), 2) AS fraud_rate_pct
FROM transactions
GROUP BY channel
ORDER BY fraud_rate_pct DESC;

-- Highest-risk merchant categories
SELECT
    m.merchant_category,
    COUNT(*) AS tx_count,
    SUM(CASE WHEN t.is_fraud THEN 1 ELSE 0 END) AS fraud_count,
    ROUND(100.0 * SUM(CASE WHEN t.is_fraud THEN 1 ELSE 0 END) / COUNT(*), 2) AS fraud_rate_pct
FROM transactions t
JOIN merchants m ON t.merchant_id = m.merchant_id
GROUP BY m.merchant_category
HAVING COUNT(*) >= 50
ORDER BY fraud_rate_pct DESC;

-- Customer velocity indicator (same day counts)
SELECT
    customer_id,
    DATE(event_time) AS tx_date,
    COUNT(*) AS tx_per_day,
    SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END) AS fraud_tx_per_day
FROM transactions
GROUP BY customer_id, DATE(event_time)
ORDER BY tx_per_day DESC
LIMIT 50;
