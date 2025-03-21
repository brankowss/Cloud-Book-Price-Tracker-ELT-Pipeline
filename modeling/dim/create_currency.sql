CREATE TABLE IF NOT EXISTS dim.currency (
    currency_id SERIAL PRIMARY KEY,
    currency_code CHAR(3) UNIQUE NOT NULL  
);