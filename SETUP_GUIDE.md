# Setup Guide - Cloud Book Price Tracker ELT Pipeline

This guide provides detailed steps for setting up the necessary cloud infrastructure on AWS and deploying the Book Price Tracker ELT pipeline using Docker, Airflow, dbt, and PostgreSQL.

For a general overview of the project, architecture, and features, please refer to the main [README.md](../README.md).

## Prerequisites

Before you begin, ensure you have the following:

1.  **Git:** Installed on your local machine to clone the repository.
2.  **Docker & Docker Compose:** Installed on the machine where you intend to run the deployment (likely your target EC2 instance, but also useful locally for testing). [Install Docker](https://docs.docker.com/engine/install/), [Install Docker Compose](https://docs.docker.com/compose/install/).
3.  **AWS Account:** An active AWS account. Using the [AWS Free Tier](https://aws.amazon.com/free/) is recommended for minimizing costs during development and for portfolio purposes.
4.  **AWS Credentials/Permissions:** Properly configured access to your AWS account for creating and managing resources (S3, RDS, EC2). **Using an IAM Role attached to the EC2 instance is strongly recommended** for secure access to AWS services like S3 from within the running pipeline. If not using an IAM role, you will need an AWS Access Key ID and Secret Access Key with appropriate permissions.
5.  **Telegram Bot:**
    * A Telegram Bot created via BotFather.
    * Your Bot's **Token**.
    * Your personal or a group **Chat ID** where notifications will be sent.

## 1. AWS Resource Provisioning

Create the necessary infrastructure components within your preferred AWS Region (e.g., `eu-central-1` Frankfurt):

1.  **S3 Bucket:**
    * Navigate to the S3 service in the AWS Management Console.
    * Create a new bucket with a **globally unique name** (e.g., `your-name-book-scraper-raw`). Keep the name simple, using lowercase letters, numbers, and hyphens.
    * Note down the **Bucket Name** and the **AWS Region**.
    * Keep default settings (regarding public access, versioning) unless you have specific needs.

2.  **RDS PostgreSQL Instance:**
    * Navigate to the RDS service.
    * Click "Create database". Choose "Standard Create" and "PostgreSQL".
    * Select a template – "Free tier" is recommended for this project.
    * **Settings:**
        * `DB instance identifier`: Choose a name (e.g., `book-pipeline-db`).
        * `Master username`: Set a username (e.g., `postgres` or a custom one).
        * `Master password`: Set a **strong password** and save it securely.
    * **Instance Configuration:** Choose a Free Tier eligible instance class (e.g., `db.t3.micro` or `db.t2.micro`).
    * **Storage:** Configure storage according to Free Tier limits (e.g., 20 GiB General Purpose SSD).
    * **Connectivity:**
        * Choose the VPC (usually your default VPC is fine).
        * **Crucially:** Under "Public access", select **"No"**. Your database should not be exposed directly to the internet.
        * **VPC security group:** Choose "Create new" or select an existing one. Immediately after creation (or during), you **must edit the inbound rules** of this security group to:
            * Allow traffic on the PostgreSQL port (TCP 5432).
            * Set the **Source** for this rule to be the **Security Group ID of your EC2 instance** (created in the next step) or its Private IP address range within the VPC. This ensures only your EC2 instance can connect to the database.
    * **Database options:** Set an initial **Database name** (e.g., `bookdb`).
    * Create the database. Wait for it to become available.
    * Note down the **RDS Endpoint (hostname)**, the **DB name**, the **master username**, and the **password**.

3.  **EC2 Instance:**
    * Navigate to the EC2 service.
    * Click "Launch instances".
    * Choose an Amazon Machine Image (AMI) – "Ubuntu Server" (latest LTS) is a good choice and usually has a Free Tier option.
    * Choose an instance type – `t2.micro` or `t3.micro` are typically Free Tier eligible.
    * **Key pair (login):** Create a new key pair or use an existing one. Download the `.pem` file and keep it secure – you'll need it for SSH access.
    * **Network settings:**
        * Select the same VPC as your RDS instance.
        * Ensure "Auto-assign public IP" is enabled (or use an Elastic IP later).
        * **Firewall (security groups):** Create a new security group or select an existing one. Configure inbound rules:
            * Allow SSH (TCP port 22) **only from your current IP address** (select "My IP" in the source dropdown).
            * Allow HTTP (TCP port 8080, or your chosen Airflow UI port) **only from your current IP address**.
            * (Optional) Allow Custom TCP port 5432 temporarily from your IP if you need to connect *directly* to RDS from your local machine for setup/debugging (remember to restrict it later).
    * **Configure storage:** Default Free Tier storage (e.g., 30 GiB gp2/gp3) is usually sufficient.
    * **Advanced details -> IAM instance profile (Highly Recommended):** Create an IAM role with necessary permissions (e.g., `AmazonS3FullAccess` or a more restricted policy allowing read/write to your specific S3 bucket) and **attach this IAM role** to the EC2 instance. This allows applications running on EC2 (like Airflow/S3Hook) to securely access AWS services without needing explicit Access Keys stored on the instance.
    * Launch the instance. Note its **Public IPv4 address**.

## 2. Deployment Steps on EC2

1.  **Connect to EC2 via SSH:**
    ```bash
    # Make your key file private first
    chmod 400 /path/to/your-key.pem 
    # Connect (replace placeholders)
    ssh -i /path/to/your-key.pem ubuntu@<your-ec2-public-ip> 
    ```
    *(Use `ec2-user@...` for Amazon Linux AMIs)*

2.  **Install Dependencies:**
    ```bash
    sudo apt update
    sudo apt upgrade -y 
    sudo apt install -y git python3-pip python3-venv docker.io docker-compose
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker ${USER}
    # Log out and log back in for docker group changes to take effect
    exit
    # SSH back into the instance
    ```

3.  **Clone Your Project Repository:**
    ```bash  
    git clone https://github.com/brankowss/Cloud-Book-Price-Tracker-ELT-Pipeline.git  
    cd Books-Scraper  
    ```

4.  **Configure Environment Variables:**
    * **Create `.env` file:** Copy the example file and fill in your actual credentials.
        ```bash
        cp .env.example .env
        nano .env  # Edit the file with your actual credentials
        ```
        * **`.env.example` (Template - include this in your Git repo):**
        ```ini
        # ========================
        # AWS RDS Configuration
        # ========================
        POSTGRES_HOST=your-rds-endpoint.region.rds.amazonaws.com
        POSTGRES_PORT=5432
        POSTGRES_USER=rds_admin_user
        POSTGRES_PASSWORD=your_strong_password
        POSTGRES_DB=book_db

        # ========================
        # AWS S3 Configuration
        # ========================
        S3_BUCKET_NAME=your-prod-bucket
        AWS_REGION=your-aws-region

        # ========================
        # Airflow Configuration
        # ========================
        AIRFLOW_EXECUTOR=LocalExecutor
        AIRFLOW_DATABASE_CONN=postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

        # ========================
        # Telegram Integration
        # ========================
        TELEGRAM_BOT_TOKEN=your_bot_token
        TELEGRAM_CHAT_ID=your_chat_id 
        ```
     **Fill in Values:** Open the `.env` file and replace the placeholder values with your actual credentials and resource names obtained during AWS provisioning (RDS endpoint, DB user/pass/name, S3 bucket name, AWS region, Telegram token/chat ID).
    * **AWS Keys:** If you are **not** using an IAM role for the EC2 instance, uncomment and fill in `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`. Otherwise, leave them commented out or empty.
    * Ensure the `.env` file is located in the same directory as your `docker-compose.yml`.

5.  **Configure Airflow Connections/Variables (Alternative/Complementary to `.env`):**
    * You will configure these via the Airflow UI *after* starting the containers (Step 6). **Do this especially if you prefer not to put credentials like the Telegram token or DB password directly in the `.env` file.**
    * **Access Airflow UI:** Open `http://<your-ec2-public-ip>:8080` in your browser (allow time for services to start). Default login is often `airflow`/`airflow`.
    * Go to `Admin` -> `Connections`.
    * **Add/Edit `postgres_conn`:**
        * `Conn Id`: `postgres_conn` (must match `postgres_conn_id` in your DAG)
        * `Conn Type`: `Postgres`
        * `Host`: Your **RDS Endpoint**
        * `Schema`: Your **RDS DB Name**
        * `Login`: Your **RDS Master Username**
        * `Password`: Your **RDS Master Password**
        * `Port`: `5432`
    * **Add/Edit `aws_conn`:**
        * `Conn Id`: `aws_conn` (must match `aws_conn_id` in your DAG)
        * `Conn Type`: `Amazon Web Services`
        * **If using IAM Role:** Leave `AWS Access Key ID` and `AWS Secret Access Key` **empty**. Ensure your EC2 instance has the correct role attached.
        * **If NOT using IAM Role:** Enter your `AWS Access Key ID` and `AWS Secret Access Key` here.
        * (Optional) You can specify the AWS Region in `Extra`.
    * **Add/Edit `telegram_conn`:**
        * `Conn Id`: `telegram_conn` (must match `conn_id` in `send_telegram_message`)
        * `Conn Type`: `HTTP`
        * `Host`: `https://api.telegram.org`
        * `Login`: Your **Telegram Chat ID**
        * `Password`: Your **Telegram Bot Token** (Yes, token goes in the password field for HTTP connections).
        
        Go to `Admin` -> `Variables`.

        | Variable Key          | Value Example                      | 
        |-----------------------|------------------------------------|
        | `S3_BUCKET_NAME`      | `your-book-scraper-bucket`         | 
        | `TELEGRAM_CHAT_ID`    | `-your-chat-id`                    |
        | `PUBLISHERS`          | `["laguna", "mikrok", "prometej"]` | 

        Or et up Variables in terminal:
        ```bash
        # Set variables
        docker-compose exec airflow-worker airflow variables set S3_BUCKET_NAME "your-bucket"
        docker-compose exec airflow-worker airflow variables set TELEGRAM_CHAT_ID "your_chat_id"
        docker-compose exec airflow-worker airflow variables set PUBLISHERS '["laguna", "mikrok", "prometej"]' --json
        ```
6.  **Build and Run Docker Containers:**
    ```bash
    docker-compose up --build -d 
    ```
    * Monitor logs: `docker-compose logs -f`
    * Allow a few minutes for Airflow services (webserver, scheduler, worker) to initialize.

7.  **Initialize dbt & Airflow DAG:**
    * Wait for the Airflow UI to become accessible.
    * **dbt Dependencies:** Run `dbt deps` inside the container where dbt commands will execute (likely the worker or scheduler service defined in your `docker-compose.yml`).
        ```bash
        # Example assuming 'airflow-worker' is the service name
        docker-compose exec airflow-worker bash -c "cd /path/to/dbt_project && export DBT_PROFILES_DIR=. && dbt deps"
        ```
        *(Replace `/path/to/dbt_project` with the actual path *inside the container*)*
    * **dbt Seed (If using):**
        ```bash
        docker-compose exec airflow-worker bash -c "cd /path/to/dbt_project && export DBT_PROFILES_DIR=. && dbt seed --target prod" 
        ```
    * **Unpause DAG:** Find the `book_ingestion_and_transformation` DAG in the Airflow UI and toggle it to **On (Unpause)**.

8.  **Database Migration (If Applicable):**
    * If you need to transfer data from your local PostgreSQL to RDS, do this *before* the first DAG run on AWS that expects historical data. Use `pg_dump` locally and `pg_restore` targeting the RDS instance.

9.  **Test the Pipeline:**
    * Trigger the DAG manually in the Airflow UI or wait for its next scheduled run.
    * Monitor the run via the Graph View and Task Logs in Airflow.
    * Check for Telegram notifications.
    * Verify data landing in S3 and being processed into your RDS database schemas (`raw`, `dbt_prod`, `snapshots`).