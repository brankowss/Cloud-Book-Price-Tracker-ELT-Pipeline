-- Remove unnecessary columns
ALTER TABLE books_data_raw
DROP COLUMN IF EXISTS old_price,
DROP COLUMN IF EXISTS discount_price,
DROP COLUMN IF EXISTS description;

-- Ispravljeni SQL:
ALTER TABLE books_data_raw
RENAME COLUMN old_price_numeric TO old_price;

ALTER TABLE books_data_raw
RENAME COLUMN discount_price_numeric TO discount_price;

