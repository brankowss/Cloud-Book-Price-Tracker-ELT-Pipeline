/* Data Model Integrity Checks */
-- 1. Books must have valid publishers ✅
SELECT 'Books without publishers' AS test_name,
       COUNT(*) AS orphaned_books,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status
FROM fact.books
WHERE publisher_id IS NULL;

-- 2. Duplicate book entries (title + publisher) ✅
SELECT 'Duplicate book entries' AS test_name,
       COUNT(*) AS duplicate_count,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status
FROM (
  SELECT title, publisher_id, COUNT(*)
  FROM fact.books
  GROUP BY title, publisher_id
  HAVING COUNT(*) > 1
) duplicates;

-- 3. Publisher activity check ✅
SELECT 'Publishers without books' AS test_name,
       COUNT(*) AS inactive_publishers,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status
FROM dim.publisher p
LEFT JOIN fact.books b ON p.publisher_id = b.publisher_id
WHERE b.book_id IS NULL;

-- 4. Price coverage check ✅ 
SELECT 'Books without price records' AS test_name,
       COUNT(*) AS unpriced_books,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status
FROM fact.books b
LEFT JOIN fact.books_prices bp ON b.book_id = bp.book_id  
WHERE bp.book_id IS NULL;

-- 5. Price sanity checks ✅ 
SELECT 'Invalid price values' AS test_name,
       COUNT(*) AS invalid_prices,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status
FROM fact.books_prices 
WHERE old_price < 0 
   OR discount_price < 0
   OR old_price < discount_price;

-- 6. Author-book relationships ✅
SELECT 'Books without authors' AS test_name,
       COUNT(*) AS authorless_books,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status
FROM fact.books b
LEFT JOIN brg.book_author ba ON b.book_id = ba.book_id
WHERE ba.author_id IS NULL;

-- 7. Author reference integrity ✅
SELECT 'Invalid author-book links' AS test_name,
       COUNT(*) AS broken_links,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status
FROM brg.book_author ba
LEFT JOIN fact.books b ON ba.book_id = b.book_id
LEFT JOIN dim.author a ON ba.author_id = a.author_id
WHERE b.book_id IS NULL OR a.author_id IS NULL;

-- 8. Author duplication check ✅
SELECT 'Duplicate author entries per book' AS test_name,
       COUNT(*) AS duplicate_authors,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status
FROM (
  SELECT book_id, author_id, COUNT(*)
  FROM brg.book_author
  GROUP BY book_id, author_id
  HAVING COUNT(*) > 1
) duplicates;

-- 9. Orphaned authors ✅
SELECT 'Authors without books' AS test_name,
       COUNT(*) AS orphaned_authors,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status
FROM dim.author a
LEFT JOIN brg.book_author ba ON a.author_id = ba.author_id
WHERE ba.book_id IS NULL;

-- 10. Date reference integrity ✅ 
SELECT 'Invalid date references' AS test_name,
       COUNT(*) AS invalid_dates,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status
FROM fact.books_prices bp  
LEFT JOIN dim.date d ON bp.date_id = d.date_id
WHERE d.date_id IS NULL;

-- 11. Date coverage ✅
SELECT 'Unmapped scraped dates' AS test_name,
       COUNT(*) AS missing_dates,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status
FROM (
    SELECT DISTINCT scraped_at::DATE AS scraped_date 
    FROM public.books_cleaned_data
) src
LEFT JOIN dim.date d ON src.scraped_date = d.date
WHERE d.date_id IS NULL;

-- 12. Future date check ✅
SELECT 'Future dates in dim.date' AS test_name,
       COUNT(*) AS future_dates,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status
FROM dim.date
WHERE date > CURRENT_DATE;

-- 13. Weekend flags ✅
SELECT 'Invalid weekend flags' AS test_name,
       COUNT(*) AS invalid_flags,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status
FROM dim.date
WHERE is_weekend != (EXTRACT(ISODOW FROM date) IN (6,7));
