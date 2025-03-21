# Book Scraper & Data Pipeline Project

## Overview  

This project is a complete data pipeline. I am using **Scrapy** for scraping, **SQL** for cleaning, modeling, and testing books data from multiple publishers. Then, **Airflow** for workflow orchestration, **PostgreSQL** for data storage, **Docker** for containerization, and **Telegram** bot notifications for monitoring pipeline execution.

![Architecture Diagram](/screenshots/architecture_diagram.png)  

## Key Components  

| Component         | Technology     | Purpose                          |
|-------------------|----------------|----------------------------------|
| Scraping Engine   | Scrapy         | Extract raw books data from publishers |
| Data Lake         | PostgreSQL     | Store raw/cleaned data in `public` schema |
| Data Warehouse    | PostgreSQL     | Modeled data in `dim`/`fact`/`brg` schemas |
| Orchestration     | Airflow        | Pipeline scheduling & monitoring |
| Alerting          | Telegram Bot   | Real-time pipeline notifications |
| Infrastructure    | Docker         | Environment consistency          |

## Project Structure
```
.
├── airflow
│   ├── dags
│   │   ├── clean_data.py
│   │   ├── model_data.py
│   │   ├── scrape_publishers.py
│   │   └── validation_data.py
│   ├── logs
│   └── plugins
├── booksscraper
│   ├── __init__.py
│   ├── items.py
│   ├── middlewares.py
│   ├── pipelines.py
│   ├── scraping_stats.py
│   ├── settings.py
│   └── spiders
│       ├── __init__.py
│       ├── publisher1_spider.py
│       ├── publisher2_spider.py
│       └── publisher3_spider.py
├── docker-compose.yml
├── Dockerfile
├── modeling
│   ├── brg
│   │   ├── create_book_author.sql
│   │   └── insert_book_author.sql
│   ├── create_schemas.sql
│   ├── dim
│   │   ├── create_authors.sql
│   │   ├── create_currency.sql
│   │   ├── create_date.sql
│   │   ├── create_publishers.sql
│   │   ├── insert_authors.sql
│   │   ├── insert_currency.sql
│   │   ├── insert_date.sql
│   │   └── insert_publishers.sql
│   └── fact
│       ├── create_book_prices.sql
│       ├── create_books.sql
│       ├── insert_book_prices.sql
│       └── insert_books.sql
├── README.md
├── requirements.txt
├── scrapy.cfg
├── screenshots
│   ├── architecture_diagram.png
│   ├── dag_1.png
│   ├── dag_2.png
│   ├── dag_3.png
│   ├── dag_44.png
│   ├── dag_list.png
│   └── telegram_alert.jpg
├── sql
│   ├── backup.sql
│   ├── clean_data.sql
│   ├── delete_rename.sql
│   ├── load_cleaned_data.sql
│   ├── normalize_data.sql
│   └── transform_data.sql
└── tests
    ├── clean_data_checks.sql
    ├── model_checks.sql
    └── raw_data_checks.sql
```

## Database Schema (Modeled Data)  
### Star Schema Design  
#### Dimensions (`dim` schema)  
- **dim.publishers**: Publishing houses  
- **dim.authors**: Book authors (supports many-to-many relationships)  
- **dim.currency**: Currency metadata   
- **dim.date**: Time dimension (2020-2030 for historical analysis)  

#### Facts (`fact` schema)  
- **fact.books**: Core book attributes   
- **fact.books_prices**: Historical price tracking with `is_current` flag  

#### Bridge Tables (`brg` schema)  
- **brg.book_author**: Links books to their authors  

## Setup and Installation  

### 1. Clone the Repository  
```bash  
git clone https://github.com/brankowss/Books-Scraper.git  
cd Books-Scraper  
```

### 2. Configure Environment Variables  
Create `.env` in the project root:
```ini  
POSTGRES_USER=your_postgres_user  
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_DB=your_database_name
POSTGRES_HOST=postgres  # Important: The service name in docker-compose
POSTGRES_PORT=5432
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
AIRFLOW_EXECUTOR=LocalExecutor
AIRFLOW_DATABASE_CONN=postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
TELEGRAM_BOT_TOKEN=your_bot_token  
TELEGRAM_CHAT_ID=your_chat_id  
```

### 3. Start Containers  
```bash  
docker-compose up --build  
```

### Airflow/Telegram Configuration  
4.  **Configure Airflow and Telegram connections:**

    -   Open the Airflow UI in your browser (usually `http://localhost:8080`).
    -   Go to `Admin` -> `Connections`.
    -   Create a new connection for PostgreSQL with the following details:
        -   `Conn Id`: `postgres_default`
        -   `Conn Type`: `Postgres`
        -   `Host`: `postgres`
        -   `Login`: `your_user_name`
        -   `Password`: `your_password`
        -   `Port`: `5432`
    -   Create a new connection for Telegram with the following details:
        -   `Conn Id`: `telegram_conn`
        -   `Conn Type`: `HTTP`
        -   `Host`: `https://api.telegram.org`
        -   `Login`: `{TELEGRAM_CHAT_ID}`
        -   `Password`: `{TELEGRAM_BOT_TOKEN}`  

    **Ensure you have a Telegram bot set up and configured before proceeding.**

### Airflow DAG 📸 Screenshots  

### 1️⃣ DAGs List  
Shows all registered DAGs and their statuses.  
![DAGs List](/screenshots/dag_list.png)

### 2️⃣ DAG 1 scrapy_to_postgres
 
![DAG 1 Graph View](/screenshots/dag_1.png)

### 3️⃣ DAG 2 clean_data 

![DAG 2 Graph View](/screenshots/dag_2.png)

### 4️⃣ DAG 3 model_data
 
![DAG 3 Graph View](/screenshots/dag_3.png)

### 5️⃣ DAG 4 validation_data

![DAG 4 Graph View](/screenshots/dag_4.png)


## Real-Time Monitoring  
Receive Telegram alerts for:  
- Pipeline failures  
- Pipeline success

![Telegram Notification](/screenshots/telegram_alert.jpg)  


## Future Improvements  
- **Scalability**: Again(YES) that was a reason why I was build book_prices and date tables.
- **Cloud Integration**: Migrate to AWS.  
- **Dashboard**: Build a dashboard for analytics and much more.  






