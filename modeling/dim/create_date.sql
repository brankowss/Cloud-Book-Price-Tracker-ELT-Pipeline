CREATE TABLE IF NOT EXISTS dim.date (
    date_id INT PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    day INT NOT NULL,
    month INT NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    day_of_week VARCHAR(9) NOT NULL,
    is_weekend BOOLEAN NOT NULL
);