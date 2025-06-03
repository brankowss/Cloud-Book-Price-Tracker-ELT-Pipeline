{{ config(
    materialized='incremental',
    unique_key=['book_id', 'scraped_at'],
    incremental_strategy='merge',
    tags=["stg"]
) }}

WITH source_data AS (
    SELECT
        md5(trim(s.book_link)) AS book_id, 
        TRIM(s.title)::TEXT AS title,
        CASE
            WHEN s.author IS NULL THEN 'Nepoznat Autor'
            WHEN TRIM(s.author) = '' THEN 'Nepoznat Autor'
            WHEN LOWER(TRIM(s.author)) = 'None' THEN 'Nepoznat Autor'  -- Processing for "None"
            ELSE TRIM(s.author)
        END::TEXT AS author,
        TRIM(s.book_link)::TEXT AS book_link,
        TRIM(s.category)::TEXT AS category,
        TRIM(s.publisher)::TEXT AS original_publisher,
        s.description,
        s.old_price,
        s.discount_price,
        (s.scraped_at AT TIME ZONE 'Europe/Belgrade')::TIMESTAMPTZ AS scraped_at
    FROM {{ source('raw', 'books_data_raw') }} s
    {% if is_incremental() %}
    WHERE s.scraped_at > (SELECT MAX(scraped_at) FROM {{ this }})
    {% endif %}
),

extracted_isbn AS (
    SELECT
        sd.*,
        TRIM(isbn_match.isbn_value)::TEXT AS isbn
    FROM source_data sd
    LEFT JOIN LATERAL (
        SELECT (regexp_matches(sd.description, '(?:ISBN|ИСБН)\s*[: ]?\s*([0-9-]+[0-9X])', 'i'))[1] AS isbn_value
        LIMIT 1
    ) AS isbn_match ON true
),

extracted_publisher_line AS (
    SELECT
        ei.*, 
        (pub_line_match.publisher_line) AS publisher_line_raw 
    FROM extracted_isbn ei
    LEFT JOIN LATERAL (
         SELECT (regexp_matches(ei.description, 'Izdavač:\s*([^\n]+)', 'i'))[1] AS publisher_line
        WHERE ei.description ~* 'Izdavač:'
        LIMIT 1
    ) AS pub_line_match ON true
),

cleaned_publisher_name AS (
    SELECT
        epl.*,
        TRIM(
            regexp_replace(
                epl.publisher_line_raw,
                '\s*(Strana u boji:|Strana:|Povez:|Pismo:|Format:|Godina|Naslov originala:|Izdavač originala:).*$', 
                '',
                'i'
            )
        ) AS publisher_name_from_desc_cleaned
    FROM extracted_publisher_line epl
),

calculated_fields AS (
  SELECT
      cpn.*,

      INITCAP(
          CASE
              WHEN LOWER(cpn.book_link) LIKE '%mikroknjiga.rs%' 
                   AND cpn.publisher_name_from_desc_cleaned IS NOT NULL 
                   AND cpn.publisher_name_from_desc_cleaned != '' 
              THEN cpn.publisher_name_from_desc_cleaned 
              ELSE cpn.original_publisher 
          END
      )::TEXT AS publisher,

      -- Cleaned Prices Based on Domain
      CASE
          WHEN cpn.old_price = 'None' OR cpn.old_price IS NULL THEN NULL
          WHEN LOWER(cpn.book_link) LIKE '%mikroknjiga.rs%' THEN
              NULLIF(
                  CASE
                      WHEN (REGEXP_REPLACE(cpn.old_price, '[^0-9.,]', '', 'g')) ~ ',\d{2}$' THEN
                          REPLACE(SPLIT_PART(REGEXP_REPLACE(cpn.old_price, '[^0-9.,]', '', 'g'), ',', 1), '.', '') || '.' || SPLIT_PART(REGEXP_REPLACE(cpn.old_price, '[^0-9.,]', '', 'g'), ',', 2)
                      WHEN (REGEXP_REPLACE(cpn.old_price, '[^0-9.,]', '', 'g')) ~ '\.\d{2}$' THEN
                          REPLACE(SPLIT_PART(REGEXP_REPLACE(cpn.old_price, '[^0-9.,]', '', 'g'), '.', 1), ',', '') || '.' || SPLIT_PART(REGEXP_REPLACE(cpn.old_price, '[^0-9.,]', '', 'g'), '.', 2)
                      ELSE
                          REPLACE(REPLACE(REGEXP_REPLACE(cpn.old_price, '[^0-9.,]', '', 'g'), ',', ''), '.', '')
                  END, ''
              )::NUMERIC
          ELSE
              NULLIF(
                  CASE
                      WHEN (REGEXP_REPLACE(cpn.old_price, '[^0-9.,]', '', 'g')) ~ ',\d{2}$' THEN
                          REPLACE(SPLIT_PART(REGEXP_REPLACE(cpn.old_price, '[^0-9.,]', '', 'g'), ',', 1), '.', '') || '.' || SPLIT_PART(REGEXP_REPLACE(cpn.old_price, '[^0-9.,]', '', 'g'), ',', 2)
                      WHEN (REGEXP_REPLACE(cpn.old_price, '[^0-9.,]', '', 'g')) ~ '\.\d{2}$' THEN
                          REPLACE(SPLIT_PART(REGEXP_REPLACE(cpn.old_price, '[^0-9.,]', '', 'g'), '.', 1), ',', '') || '.' || SPLIT_PART(REGEXP_REPLACE(cpn.old_price, '[^0-9.,]', '', 'g'), '.', 2)
                      ELSE
                          REPLACE(REPLACE(REGEXP_REPLACE(cpn.old_price, '[^0-9.,]', '', 'g'), ',', ''), '.', '')
                  END, ''
              )::NUMERIC
      END AS cleaned_old_price,

      CASE
          WHEN cpn.discount_price = 'None' OR cpn.discount_price IS NULL THEN NULL
          WHEN LOWER(cpn.book_link) LIKE '%mikroknjiga.rs%' THEN
              NULLIF(
                  CASE
                      WHEN (REGEXP_REPLACE(cpn.discount_price, '[^0-9.,]', '', 'g')) ~ ',\d{2}$' THEN
                          REPLACE(SPLIT_PART(REGEXP_REPLACE(cpn.discount_price, '[^0-9.,]', '', 'g'), ',', 1), '.', '') || '.' || SPLIT_PART(REGEXP_REPLACE(cpn.discount_price, '[^0-9.,]', '', 'g'), ',', 2)
                      WHEN (REGEXP_REPLACE(cpn.discount_price, '[^0-9.,]', '', 'g')) ~ '\.\d{2}$' THEN
                          REPLACE(SPLIT_PART(REGEXP_REPLACE(cpn.discount_price, '[^0-9.,]', '', 'g'), '.', 1), ',', '') || '.' || SPLIT_PART(REGEXP_REPLACE(cpn.discount_price, '[^0-9.,]', '', 'g'), '.', 2)
                      ELSE
                          REPLACE(REPLACE(REGEXP_REPLACE(cpn.discount_price, '[^0-9.,]', '', 'g'), ',', ''), '.', '')
                  END, ''
              )::NUMERIC
          ELSE
              NULLIF(
                  CASE
                      WHEN (REGEXP_REPLACE(cpn.discount_price, '[^0-9.,]', '', 'g')) ~ ',\d{2}$' THEN
                          REPLACE(SPLIT_PART(REGEXP_REPLACE(cpn.discount_price, '[^0-9.,]', '', 'g'), ',', 1), '.', '') || '.' || SPLIT_PART(REGEXP_REPLACE(cpn.discount_price, '[^0-9.,]', '', 'g'), ',', 2)
                      WHEN (REGEXP_REPLACE(cpn.discount_price, '[^0-9.,]', '', 'g')) ~ '\.\d{2}$' THEN
                          REPLACE(SPLIT_PART(REGEXP_REPLACE(cpn.discount_price, '[^0-9.,]', '', 'g'), '.', 1), ',', '') || '.' || SPLIT_PART(REGEXP_REPLACE(cpn.discount_price, '[^0-9.,]', '', 'g'), '.', 2)
                      ELSE
                          REPLACE(REPLACE(REGEXP_REPLACE(cpn.discount_price, '[^0-9.,]', '', 'g'), ',', ''), '.', '')
                  END, ''
              )::NUMERIC
      END AS cleaned_discount_price,

      'RSD' AS currency,
    --   CURRENT_TIMESTAMP AS updated_at,
    (CURRENT_TIMESTAMP AT TIME ZONE 'Europe/Belgrade') AS updated_at, 
    


      CASE 
          WHEN LOWER(cpn.description) LIKE '%latinica%' OR LOWER(cpn.description) LIKE '%latinična%' OR LOWER(cpn.description) LIKE '%latinicno%' OR LOWER(cpn.description) LIKE '%latinic%' OR LOWER(cpn.description) LIKE '%латиница%' OR LOWER(cpn.description) LIKE '%latinicirilica%' OR LOWER(cpn.description) LIKE '%cirilatinića%' THEN 'Latinica'
          WHEN LOWER(cpn.description) LIKE '%ćirilica%' OR LOWER(cpn.description) LIKE '%ćirilična%' OR LOWER(cpn.description) LIKE '%ćirilicno%' OR LOWER(cpn.description) LIKE '%ćirilic%' OR LOWER(cpn.description) LIKE '%ћирилица%' THEN 'Ćirilica'
          ELSE NULL
      END AS script_type,

      COALESCE(
          (SELECT (regexp_matches(cpn.description, 'Broj strana:\s*(\d+)'))[1]::INTEGER),
          (SELECT (regexp_matches(cpn.description, 'Strana:\s*(\d+)'))[1]::INTEGER),
          (SELECT (regexp_matches(cpn.description, 'Страна:\s*(\d+)'))[1]::INTEGER),
          (SELECT (regexp_matches(cpn.description, 'Број страна /.*?(\d+)\s*/'))[1]::INTEGER),
          (SELECT (regexp_matches(cpn.description, 'Strana u boji:\s*(\d+)'))[1]::INTEGER),
          NULL
      ) AS page_numbers,

      CASE
          WHEN LOWER(cpn.description) ~ '(1[89]\d{2}|20[0-2]\d|202[0-5])' 
          THEN substring(LOWER(cpn.description) from '(1[89]\d{2}|20[0-2]\d|202[0-5])')::INTEGER
          ELSE NULL
      END AS year_of_publication
      
  FROM cleaned_publisher_name cpn 
),

final_selection AS (
  SELECT 
      cf.book_id,
      cf.title,
      cf.author,
      cf.book_link,
      cf.category,
      cf.publisher,
      cf.cleaned_old_price AS old_price,
      cf.cleaned_discount_price AS discount_price,
      cf.currency,
      CASE
        WHEN cf.isbn IS NULL THEN NULL
        WHEN TRIM(cf.isbn) = '' THEN NULL
        WHEN REGEXP_REPLACE(TRIM(cf.isbn), '[-\s]', '', 'g') ~ '^(\d{9}[0-9Xx]|\d{13})$'
            THEN REPLACE(TRIM(cf.isbn), '-', '')
        ELSE NULL
      END AS isbn,
      cf.scraped_at, 
      cf.updated_at, 
      cf.script_type,
      cf.page_numbers,
      cf.year_of_publication
  FROM calculated_fields cf
  WHERE cf.cleaned_old_price IS NOT NULL OR cf.cleaned_discount_price IS NOT NULL -- Keep only rows where at least one price exists
)

SELECT * FROM final_selection




