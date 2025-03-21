import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql
from itemadapter import ItemAdapter
import logging

# Configure logging
logging.basicConfig(filename='scraper.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# PostgreSQL credentials
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')

# Database connection function
def connect_to_postgres():
    try:
        conn = psycopg2.connect(
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT
        )
        return conn
    except psycopg2.Error as e:
        logging.error(f"Error connecting to database: {e}")
        return None  # Return None if connection fails

class PostgreSQLPipeline:
    def open_spider(self, spider):
        self.conn = connect_to_postgres()
        if self.conn:
            self.cursor = self.conn.cursor()
            self.create_table()
        else:
            raise Exception("Failed to connect to database. Spider will be closed.")

    def create_table(self):
        """Creates the books_data_raw if it doesn't exist."""
        create_table_query = '''
            CREATE TABLE IF NOT EXISTS books_data_raw (
                id SERIAL PRIMARY KEY,
                title TEXT,
                author TEXT,
                book_link TEXT, 
                old_price TEXT,
                discount_price TEXT,
                currency TEXT,
                publisher TEXT,
                description TEXT,
                scraped_at TIMESTAMP DEFAULT NOW()
            )
        '''
        self.cursor.execute(create_table_query)
        self.conn.commit()

    def close_spider(self, spider):
        if hasattr(self, 'conn') and self.conn:
            self.cursor.close()
            self.conn.close()

    def process_item(self, item, spider):
        if not hasattr(self, 'conn') or not self.conn:
            logging.error("Database connection not available. Item processing failed.")
            return item

        adapter = ItemAdapter(item)

        try:
            insert_query = sql.SQL('''
                INSERT INTO books_data_raw (title, author, book_link, old_price, discount_price, currency, publisher, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''')
            
            values = (
                str(adapter.get('title')),
                str(adapter.get('author')),
                str(adapter.get('book_link')),
                str(adapter.get('old_price')),
                str(adapter.get('discount_price')),
                str(adapter.get('currency')),  
                str(adapter.get('publisher')),
                str(adapter.get('description'))
            )

            self.cursor.execute(insert_query, values)
            self.conn.commit()

            logging.info(f"Inserted data: {values}")

        except psycopg2.Error as e:
            self.conn.rollback()
            logging.error(f"Database insertion error: {e}")

        return item
