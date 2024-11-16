import sqlite3
from itemadapter import ItemAdapter
import csv
import re
import html

def clean_price_format_1(price_str):
    """Cleans prices like '2.560,00 RSD'"""
    if not price_str:
        return 0.0
    price_str = html.unescape(price_str)
    cleaned_str = re.sub(r'[^\d,]', '', price_str).replace(',', '.')
    return round(float(cleaned_str), 2)

def clean_price_format_2(price_str):
    """Cleans prices like '549.00 din' or '770.00 RSD'"""
    if not price_str:
        return 0.0
    price_str = html.unescape(price_str)
    cleaned_str = re.sub(r'[^\d.]', '', price_str)
    return round(float(cleaned_str), 2)

def clean_price_format_3(price_str):
    """Cleans prices like '1,320.50 RSD'"""
    if not price_str:
        return 0.0
    price_str = html.unescape(price_str)
    cleaned_str = re.sub(r'[^\d,.]', '', price_str).replace(',', '')
    return round(float(cleaned_str), 2)


class SQLitePipeline:
    def open_spider(self, spider):
        # Creates a connection to the SQLite database
        self.conn = sqlite3.connect('/data/books.db')
        self.cursor = self.conn.cursor()
        
        # Creates the "books" table if it does not exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                author TEXT,
                book_link TEXT,
                old_price REAL,
                discount_price REAL,
                currency TEXT DEFAULT 'RSD',
                publisher TEXT
            )
        ''')

    def close_spider(self, spider):
        #Fetch all data
        self.cursor.execute('''
            SELECT title, author, book_link, old_price, discount_price, currency, publisher
            FROM books
        ''')
        
        # Fetch the data
        rows = self.cursor.fetchall()

        # Close the connection after fetching the data
        self.conn.commit()
        self.conn.close()

        # Saved the fetched data into a CSV file
        with open('/data/books_data.csv', mode='w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['title', 'author', 'book_link', 'old_price', 'discount_price', 'currency', 'publisher'])
            for row in rows:
                csv_writer.writerow(row)

    def process_item(self, item, spider):
        # Converts `item` to dictionary using ItemAdapter
        adapter = ItemAdapter(item)
        adapter['currency'] = 'RSD'  # Default currency

        # **Data cleaning**:
        # If the value is None or empty, set a default value
        adapter['title'] = adapter.get('title') if adapter.get('title') else 'N/A'
        adapter['author'] = adapter.get('author') if adapter.get('author') else 'Unknown'
        adapter['publisher'] = adapter.get('publisher') if adapter.get('publisher') else 'Unknown'

        if spider.name == 'mikrok':
            item['old_price'] = clean_price_format_1(item.get('old_price', ''))
            item['discount_price'] = clean_price_format_1(item.get('discount_price', ''))
        elif spider.name == 'laguna':
            item['old_price'] = clean_price_format_2(item.get('old_price', ''))
            item['discount_price'] = clean_price_format_2(item.get('discount_price', ''))
        elif spider.name == 'prometej':
            item['old_price'] = clean_price_format_3(item.get('old_price', ''))
            item['discount_price'] = clean_price_format_3(item.get('discount_price', ''))
      
        # Insert data into SQLite database
        self.cursor.execute('''
            INSERT INTO books (title, author, book_link, old_price, discount_price, currency, publisher)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            adapter['title'],
            adapter['author'],
            adapter['book_link'],
            adapter['old_price'],
            adapter['discount_price'],
            adapter['currency'], 
            adapter['publisher']
        ))

        return item
