import datetime
import os
import json
from scrapy import signals
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, Float
from dotenv import load_dotenv
import boto3  # New import

class StatsToPostgresAndS3:  # Renamed class
    def __init__(self, crawler):
        load_dotenv()
        
        # PostgreSQL setup (existing)
        self.db_user = os.getenv("POSTGRES_USER")
        self.db_password = os.getenv("POSTGRES_PASSWORD")
        self.db_host = os.getenv("POSTGRES_HOST")
        self.db_port = os.getenv("POSTGRES_PORT")
        self.db_name = os.getenv("POSTGRES_DB")
        
        # S3 setup (new)
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.s3_bucket = os.getenv("S3_STATS_BUCKET")  # Add to .env
        
        self.engine = create_engine(f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}")
        self.s3 = boto3.client(  # New S3 client
            's3',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key
        )
        
        # Existing table creation
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
            Column('duration', Float),
            schema='pipeline_monitoring' 
        )
        self.metadata.create_all(self.engine)

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls(crawler)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        return ext

    def spider_closed(self, spider, reason):
        stats = spider.crawler.stats.get_stats()
        
        # Existing time calculation
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

        # Existing PostgreSQL insert
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

        # New S3 upload logic
        try:
            # Create stats payload
            stats_data = {
                "spider": spider.name,
                "stats": {
                    "items_scraped": stats.get('item_scraped_count', 0),
                    "responses_received": stats.get('response_received_count', 0),
                    "requests_made": stats.get('downloader/request_count', 0),
                    "start_time": str(start_time),
                    "finish_time": str(finish_time),
                    "duration_seconds": duration,
                    "completion_reason": reason
                },
                "metadata": {
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "project_version": "1.0"
                }
            }

            # Generate S3 key
            timestamp = datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')
            s3_key = f"stats/{spider.name}/{timestamp}-stats.json"

            # Upload to S3
            self.s3.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=json.dumps(stats_data, indent=2),
                ContentType='application/json'
            )
            
            spider.logger.info(f"Successfully uploaded stats to S3: s3://{self.s3_bucket}/{s3_key}")
            
        except Exception as e:
            spider.logger.error(f"Failed to upload stats to S3: {str(e)}")