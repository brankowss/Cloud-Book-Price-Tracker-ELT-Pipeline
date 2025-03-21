-- Populate 2020-01-01 to 2030-12-31
INSERT INTO dim.date
SELECT
    TO_CHAR(datum, 'YYYYMMDD')::INT AS date_id,
    datum AS date,
    EXTRACT(DAY FROM datum) AS day,
    EXTRACT(MONTH FROM datum) AS month,
    EXTRACT(YEAR FROM datum) AS year,
    EXTRACT(QUARTER FROM datum) AS quarter,
    TO_CHAR(datum, 'Day') AS day_of_week,
    EXTRACT(ISODOW FROM datum) IN (6,7) AS is_weekend
FROM generate_series('2020-01-01'::date, '2030-12-31'::date, '1 day') datum
ON CONFLICT (date_id) DO NOTHING;