/* Raw Data Quality Assessment */

-- 1. Data Freshness Check
SELECT 'Stale data' AS test_name,
       COUNT(*) AS stale_records,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status
FROM books_data_raw_backup
WHERE scraped_at < NOW() - INTERVAL '25 HOURS';  -- 24h + 1h buffer

-- 2. Identifier Uniqueness
SELECT 'Duplicate IDs' AS test_name,
       COUNT(*) AS duplicate_ids,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status
FROM (
  SELECT id, COUNT(*)
  FROM books_data_raw_backup
  GROUP BY id
  HAVING COUNT(*) > 1
) duplicates;

-- 3. Mandatory Field Check
SELECT 'Missing mandatory fields' AS test_name,
       COUNT(*) AS missing_fields,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status
FROM books_data_raw_backup
WHERE title IS NULL 
   OR author IS NULL 
   OR book_link IS NULL;

-- 4. Check: At least one price column has any value 
SELECT 'Price presence check' AS test_name,
       COUNT(*) AS missing_prices,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status
FROM books_data_raw_backup
WHERE old_price IS NULL 
  AND discount_price IS NULL;

-- 5. Currency Standardization
SELECT 'Non-standard currency' AS test_name,
       COUNT(*) AS invalid_currency,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status
FROM books_data_raw_backup
WHERE currency != 'RSD';