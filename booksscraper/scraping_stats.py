import datetime
import os
from scrapy import signals
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, Float
from dotenv import load_dotenv

class StatsToPostgres:
    def __init__(self, crawler):
        load_dotenv()  
        self.db_user = os.getenv("POSTGRES_USER")
        self.db_password = os.getenv("POSTGRES_PASSWORD")
        self.db_host = os.getenv("POSTGRES_HOST")
        self.db_port = os.getenv("POSTGRES_PORT")
        self.db_name = os.getenv("POSTGRES_DB")

        self.engine = create_engine(f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}")
        self.metadata = MetaData()
        self.stats_table = Table(
            'books_scrapy_stats', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('spider_name', String),
            Column('item_scraped_count', Integer),
            Column('response_received_count', Integer),
            Column('request_count', Integer),
            Column('start_time', String),
            Column('finish_time', String),
            Column('duration', Float)
        )
        self.metadata.create_all(self.engine)

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls(crawler)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        return ext

    def spider_closed(self, spider, reason):
        stats = spider.crawler.stats.get_stats()
        start_time = stats.get('start_time')
        finish_time = stats.get('finish_time')

        duration = None
        if start_time and finish_time:
            try:
                start_dt = datetime.datetime.fromisoformat(str(start_time))
                finish_dt = datetime.datetime.fromisoformat(str(finish_time))
                duration = (finish_dt - start_dt).total_seconds()
            except ValueError:
                print(f"Error parsing date strings: start_time={start_time}, finish_time={finish_time}")

        with self.engine.connect() as conn:
            conn.execute(self.stats_table.insert().values(
                spider_name=spider.name,
                item_scraped_count=stats.get('item_scraped_count', 0),
                response_received_count=stats.get('response_received_count', 0),
                request_count=stats.get('downloader/request_count', 0),
                start_time=str(start_time),
                finish_time=str(finish_time),
                duration=duration
            ))
            conn.commit()