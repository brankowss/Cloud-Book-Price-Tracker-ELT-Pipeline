# pipelines.py

import os
import boto3
import pandas as pd
from io import StringIO, BytesIO
from itemadapter import ItemAdapter
import logging
from datetime import datetime
import pytz 

class S3Pipeline:
    def __init__(self):
        self.s3 = None
        self.bucket = os.getenv('S3_BUCKET_NAME')
        self.items = []

    def open_spider(self, spider):
        # IAM Role-based authentication
        session = boto3.Session()
        self.s3 = session.client('s3', region_name=os.getenv('AWS_REGION'))
        logging.info(f"S3Pipeline initialized for {spider.name} using IAM role")

    def process_item(self, item, spider):
        self.items.append(ItemAdapter(item).asdict())
        return item

    def close_spider(self, spider):
        if not self.items:
            logging.info(f"No items scraped by {spider.name}, skipping S3 upload.")
            return

        new_df = pd.DataFrame(self.items)

        now_utc = datetime.now(pytz.utc)
        new_df["scraped_at"] = now_utc.strftime("%Y-%m-%d %H:%M:%S %Z") 

        # Generate a unique key for this file
        timestamp_str = now_utc.strftime("%Y%m%d_%H%M%S_%f")
        s3_key = f"books_publishers/{spider.name}/{timestamp_str}.csv" 

        logging.info(f"Attempting to upload {len(new_df)} items from {spider.name} to s3://{self.bucket}/{s3_key}")

        try:
            csv_buffer = StringIO()
            new_df.to_csv(csv_buffer, index=False)
            self.s3.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=csv_buffer.getvalue(),
                ContentType='text/csv'
            )
            logging.info(f"Successfully uploaded {len(new_df)} items to {s3_key}")
        except Exception as e:
            logging.error(f"Error uploading data for {spider.name} to S3: {e}")
           

    def _upload_to_s3(self, df, key): 
        try:
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False)
            self.s3.put_object(
                Bucket=self.bucket,
                Key=key, 
                Body=csv_buffer.getvalue(),
                ContentType='text/csv'
            )
        except Exception as e:
             logging.error(f"Error in _upload_to_s3 for key {key}: {e}")
             raise 
