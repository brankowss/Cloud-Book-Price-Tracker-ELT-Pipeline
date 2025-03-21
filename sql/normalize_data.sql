-- Fix capitalization of publisher names
UPDATE books_data_raw
SET publisher = UPPER(LEFT(publisher, 1)) || LOWER(SUBSTRING(publisher, 2));

-- Replace NULL values with defaults 
UPDATE books_data_raw
SET 
    script_type = COALESCE(NULLIF(script_type, 'None'), 'Unknown');

ALTER TABLE books_data_raw
ADD COLUMN scraped_at_temp TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

UPDATE books_data_raw
SET scraped_at_temp = scraped_at;

-- Drop temporary column
ALTER TABLE books_data_raw
DROP COLUMN scraped_at;

-- Rename column back
ALTER TABLE books_data_raw
RENAME COLUMN scraped_at_temp TO scraped_at;

ALTER TABLE books_data_raw
ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- -- Adjust timestamps want my timezone 
UPDATE books_data_raw
SET scraped_at = scraped_at + INTERVAL '1 hour'; 

UPDATE books_data_raw
SET updated_at = updated_at + INTERVAL '1 hour'; 