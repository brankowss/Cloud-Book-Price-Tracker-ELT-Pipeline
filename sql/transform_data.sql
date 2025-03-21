ALTER TABLE books_data_raw
ADD COLUMN page_numbers INTEGER,
ADD COLUMN script_type TEXT,
ADD COLUMN year_of_publication INTEGER,
ADD COLUMN old_price_numeric NUMERIC,
ADD COLUMN discount_price_numeric NUMERIC;

-- Convert old_price and discount_price to numeric 
UPDATE books_data_raw
SET 
    old_price_numeric = CASE
        WHEN old_price = 'None' THEN NULL
        WHEN old_price LIKE '%din%' THEN 
            REGEXP_REPLACE(old_price, '[^0-9.]', '', 'g')::NUMERIC
        WHEN old_price LIKE '%RSD%' THEN 
            CASE
                WHEN (REGEXP_REPLACE(old_price, '[^0-9.,]', '', 'g')) ~ ',\d{2}$' THEN
                    (REPLACE((SPLIT_PART(REGEXP_REPLACE(old_price, '[^0-9.,]', '', 'g'), ',', 1)), '.', '') || '.' || SPLIT_PART(REGEXP_REPLACE(old_price, '[^0-9.,]', '', 'g'), ',', 2))::NUMERIC
                WHEN (REGEXP_REPLACE(old_price, '[^0-9.,]', '', 'g')) ~ '\.\d{2}$' THEN
                    (REPLACE((SPLIT_PART(REGEXP_REPLACE(old_price, '[^0-9.,]', '', 'g'), '.', 1)), ',', '') || '.' || SPLIT_PART(REGEXP_REPLACE(old_price, '[^0-9.,]', '', 'g'), '.', 2))::NUMERIC
                ELSE
                    REPLACE(REPLACE(REGEXP_REPLACE(old_price, '[^0-9.,]', '', 'g'), ',', ''), '.', '')::NUMERIC
            END
        ELSE NULL
    END,
    discount_price_numeric = CASE
        WHEN discount_price = 'None' THEN NULL
        WHEN discount_price LIKE '%din%' THEN 
            REGEXP_REPLACE(discount_price, '[^0-9.]', '', 'g')::NUMERIC
        WHEN discount_price LIKE '%RSD%' THEN 
            CASE
                WHEN (REGEXP_REPLACE(discount_price, '[^0-9.,]', '', 'g')) ~ ',\d{2}$' THEN
                    (REPLACE((SPLIT_PART(REGEXP_REPLACE(discount_price, '[^0-9.,]', '', 'g'), ',', 1)), '.', '') || '.' || SPLIT_PART(REGEXP_REPLACE(discount_price, '[^0-9.,]', '', 'g'), ',', 2))::NUMERIC
                WHEN (REGEXP_REPLACE(discount_price, '[^0-9.,]', '', 'g')) ~ '\.\d{2}$' THEN
                    (REPLACE((SPLIT_PART(REGEXP_REPLACE(discount_price, '[^0-9.,]', '', 'g'), '.', 1)), ',', '') || '.' || SPLIT_PART(REGEXP_REPLACE(discount_price, '[^0-9.,]', '', 'g'), '.', 2))::NUMERIC
                ELSE
                    REPLACE(REPLACE(REGEXP_REPLACE(discount_price, '[^0-9.,]', '', 'g'), ',', ''), '.', '')::NUMERIC
            END
        ELSE NULL
    END;


-- Extract page numbers from description 
UPDATE books_data_raw
SET page_numbers = COALESCE(
    CASE
        WHEN description ~* 'Broj strana:\s*(\d+)' THEN (SELECT (REGEXP_MATCHES(description, 'Broj strana:\s*(\d+)'))[1]::INTEGER)
        WHEN description ~* 'Strana:\s*(\d+)' THEN (SELECT (REGEXP_MATCHES(description, 'Strana:\s*(\d+)'))[1]::INTEGER)
        WHEN description ~* 'Страна:\s*(\d+)' THEN (SELECT (REGEXP_MATCHES(description, 'Страна:\s*(\d+)'))[1]::INTEGER)
        WHEN description ~* 'Број страна /.*?(\d+)\s*/' THEN (SELECT (REGEXP_MATCHES(description, 'Број страна /.*?(\d+)\s*/'))[1]::INTEGER)
        WHEN description ~* 'Strana u boji:\s*(\d+)' THEN (SELECT (REGEXP_MATCHES(description, 'Strana u boji:\s*(\d+)'))[1]::INTEGER)
        ELSE books_data_raw.page_numbers
    END,
    page_numbers
);

-- Extract year of publication from description 
UPDATE books_data_raw
SET year_of_publication = CASE
    WHEN LOWER(description) ~ '(1[89]\d{2}|20[0-2]\d|202[0-5])' 
        THEN substring(LOWER(description) from '(1[89]\d{2}|20[0-2]\d|202[0-5])')::INTEGER
    ELSE year_of_publication
END;

-- Extract script type (Cyrillic/Latin) 
UPDATE books_data_raw
SET script_type = CASE
    WHEN LOWER(description) LIKE '%latinica%' OR LOWER(description) LIKE '%latinična%' OR LOWER(description) LIKE '%latinicno%' OR LOWER(description) LIKE '%latinic%' OR LOWER(description) LIKE '%латиница%' OR LOWER(description) LIKE '%latinicirilica%' OR LOWER(description) LIKE '%cirilatinića%' THEN 'Latinica'
    WHEN LOWER(description) LIKE '%ćirilica%' OR LOWER(description) LIKE '%ćirilična%' OR LOWER(description) LIKE '%ćirilicno%' OR LOWER(description) LIKE '%ćirilic%' OR LOWER(description) LIKE '%ћирилица%' THEN 'Ćirilica'
    ELSE script_type
END;
