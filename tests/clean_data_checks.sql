/* Data Quality Checks for Cleaned Books Data */

-- 1. Completeness Check: Verify no data loss during cleaning
WITH missing_ids AS (
  SELECT COUNT(*) AS missing_count
  FROM books_data_raw_backup r
  LEFT JOIN books_cleaned_data c ON r.id = c.id 
  WHERE c.id IS NULL
)
SELECT 'Missing records in cleaned data' AS test_name,
       CASE WHEN missing_count > 0 THEN 'FAIL' ELSE 'PASS' END AS status
FROM missing_ids;

-- 2. Validity Check: Page numbers must be positive integers
SELECT 'Invalid page numbers' AS test_name,
       COUNT(*) AS invalid_count,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status
FROM books_cleaned_data
WHERE page_numbers::TEXT !~ '^[1-9]\d*$';  -- Exclude zero and negative numbers

-- 3. Temporal Validity: Publication year sanity check
SELECT 'Future publication years' AS test_name,
       COUNT(*) AS future_years,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status
FROM books_cleaned_data 
WHERE year_of_publication > EXTRACT(YEAR FROM CURRENT_DATE);

-- 4. Price Consistency: Validate numeric prices and discount logic
SELECT 'Invalid price formats' AS test_name,
       COUNT(*) AS invalid_prices,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status
FROM books_cleaned_data
WHERE old_price::TEXT !~ '^\d+(\.\d{1,2})?$'
   OR discount_price::TEXT !~ '^\d+(\.\d{1,2})?$'
   OR discount_price > old_price;

-- 5. Price Outliers: Detect abnormally high prices for both old and discount prices 4 times bigger the AVG
SELECT 'Price outliers' AS test_name,
       COUNT(*) AS outlier_count,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status
FROM books_cleaned_data
WHERE old_price > (SELECT AVG(old_price) + 4 * STDDEV(old_price) FROM books_cleaned_data)
   OR discount_price > (SELECT AVG(discount_price) + 4 * STDDEV(discount_price) FROM books_cleaned_data);

-- 6. Timeliness Check: Updated_at tracking
SELECT 'Missing update timestamps' AS test_name,
       COUNT(*) AS missing_updates,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status
FROM books_cleaned_data
WHERE updated_at IS NULL;
