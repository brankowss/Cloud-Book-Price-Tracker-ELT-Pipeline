SELECT *
FROM {{ ref('stg_books') }}
WHERE isbn IS NOT NULL
  AND REGEXP_REPLACE(isbn, '[-\s]', '', 'g') !~ '^(\d{9}[0-9Xx]|\d{13})$'


