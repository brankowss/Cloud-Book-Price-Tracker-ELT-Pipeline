CREATE TABLE IF NOT EXISTS dim.publisher (
    publisher_id SERIAL PRIMARY KEY,
    publisher_name TEXT UNIQUE NOT NULL,
    scraped_at TIMESTAMP
);
