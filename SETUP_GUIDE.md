# Setup Guide - Cloud Book Price Tracker ELT Pipeline

This guide provides detailed steps for setting up the necessary cloud infrastructure on AWS and deploying the Book Price Tracker ELT pipeline using Docker, Airflow, dbt, and PostgreSQL.

For a general overview of the project, architecture, and features, please refer to the main [README.md](../README.md).

## Prerequisites

Before you begin, ensure you have the following:

1.  **Git:** Installed on your local machine to clone the repository.
2.  **Docker & Docker Compose:** Installed on the machine where you intend to run the deployment (likely your target EC2 instance, but also useful locally for testing). [Install Docker](https://docs.docker.com/engine/install/), [Install Docker Compose](https://docs.docker.com/compose/install/).
3.  **AWS Account:** An active AWS account. While the [AWS Free Tier](https://aws.amazon.com/free/) can be used for some components, be aware of its limitations, especially for EC2 compute resources needed by this project.
4.  **AWS Credentials/Permissions:** Properly configured access to your AWS account for creating and managing resources (S3, RDS, EC2). **Using an IAM Role attached to the EC2 instance is strongly recommended** for secure access to AWS services like S3 from within the running pipeline. If not using an IAM role, you will need an AWS Access Key ID and Secret Access Key with appropriate permissions.
5.  **Telegram Bot:**
    * A Telegram Bot created via BotFather.
    * Your Bot's **Token**.
    * Your personal or a group **Chat ID** where notifications will be sent.

---
## 1. AWS Resource Provisioning

Create the necessary infrastructure components within your preferred AWS Region (e.g., `eu-central-1` Frankfurt):

### 1.1. S3 Bucket

An S3 bucket is used as the landing zone for raw data scraped by Scrapy.

* Navigate to the S3 service in the AWS Management Console.
* Create a new bucket with a **globally unique name** (e.g., `your-name-book-scraper-raw`). Keep the name simple, using lowercase letters, numbers, and hyphens.
* Note down the **Bucket Name** and the **AWS Region**.
* Keep default settings (regarding public access, versioning) unless you have specific needs.

**S3 Free Tier & Storage Costs:**
* **AWS Free Tier for S3:** For the first 12 months after account creation, AWS typically offers 5 GB of S3 Standard storage and a certain number of free requests (e.g., 20,000 Get, 2,000 Put/List).
* **When S3 Charges Apply:**
    1.  Storing more than 5 GB of data.
    2.  After your 12-month Free Tier period expires (you'll be charged for all storage used at standard rates).
    3.  Exceeding the free request limits.
    4.  Data Transfer OUT to the internet (beyond the aggregate 100 GB/month free across AWS services). Data Transfer IN to S3 is free.
* For this project, raw CSV files are stored. The volume is not expected to be excessive for a few months of daily scrapes for a few publishers, but it's good to monitor your S3 storage usage.

---
### 1.2. RDS PostgreSQL Instance

This project uses a PostgreSQL database as its data warehouse, managed by AWS RDS.

* Navigate to the RDS service in the AWS Management Console.
* Click "Create database". Choose "Standard Create" and "PostgreSQL".
* Select a template – **"Free tier"** is recommended for initial setup to minimize costs.
* **Settings:**
    * `DB instance identifier`: Choose a name (e.g., `book-pipeline-db`).
    * `Master username`: Set a username (e.g., `postgres_admin` or a custom one).
    * `Master password`: Set a **strong password** and save it securely.
* **Instance Configuration:** Choose a Free Tier eligible instance class (e.g., `db.t3.micro` or `db.t2.micro`).
* **Storage:**
    * Configure storage according to Free Tier limits (typically 20 GiB General Purpose SSD - gp2/gp3).
* **Connectivity:**
    * Choose the VPC (usually your default VPC is fine).
    * **Crucially:** Under "Public access", select **"No"**. Your database should not be exposed directly to the internet.
    * **VPC security group (e.g., `rds-book-pipeline-sg`):** Choose "Create new" or select an existing one. Immediately after creation (or during), you **must edit the inbound rules** of this security group to:
        * Allow traffic on the PostgreSQL port (TCP 5432).
        * Set the **Source** for this rule to be the **Security Group ID of your EC2 instance** (created in the next step, e.g., `ec2-book-pipeline-sg`) or its Private IP address range within the VPC. This ensures only your EC2 instance can connect to the database.
* **Database options:** Set an **Initial database name** (e.g., `bookdb`).
* Create the database. Wait for it to become available.
* Note down the **RDS Endpoint (hostname)**, the **DB name**, the **master username**, and the **password**.

**RDS Free Tier & Storage Considerations:**
* **AWS Free Tier for RDS:** For the first 12 months after account creation, AWS typically offers:
    * 750 hours per month of a `.micro` instance (e.g., `db.t3.micro` or `db.t2.micro`).
    * 20 GB of General Purpose (SSD) database storage.
    * 20 GB of storage for automated database backups.
* **Storage Allocation & Costs:**
    * When you provision an RDS instance (e.g., the Free Tier default of 20 GB), this allocated storage immediately starts counting towards your monthly "GB-Month" allowance.
    * The database engine's system files, transaction logs (WAL), default databases (`postgres`, `template0`, `template1`), and general overhead will consume a portion of this allocated 20 GB from the start (typically a few GBs).
    * **Charges for RDS storage will apply if:**
        1.  Your total allocated storage exceeds the Free Tier limit (e.g., you increase it beyond 20 GB).
        2.  Your 12-month Free Tier period for RDS expires (for both compute hours and storage).
        3.  Your automated backup storage exceeds your provisioned database storage size (within the Free Tier limit).
    * User data (Airflow metadata, raw data tables, dbt models, indexes) will contribute to filling the allocated 20 GB. For a project running several months with daily data ingestion, it's possible to approach or exceed this 20 GB limit. Monitor your "Free storage space" metric in CloudWatch for your RDS instance.

---
### 1.3. EC2 Instance & Elastic IP

An EC2 instance will host the Dockerized Airflow application.

* Navigate to the EC2 service in the AWS Management Console.
* Click "Launch instances".
* **Amazon Machine Image (AMI):** Choose an AMI – "Ubuntu Server" (latest LTS, e.g., 22.04 or 20.04) is a good choice and usually has a Free Tier option for `t2.micro`/`t3.micro`.
* **Instance Type:**
    * **Initial Exploration (Free Tier):** For initial familiarization, you can select a Free Tier eligible instance like `t2.micro` (1 vCPU, 1 GiB RAM) or `t3.micro` (2 vCPU, 1 GiB RAM, where available in Free Tier).
    * **Project Resource Requirements (Important!):**
        This project, running Apache Airflow (webserver, scheduler, tasks), Docker, Scrapy spiders, and dbt transformations, is resource-intensive.
        * **Micro instances (`t2.micro`, `t3.micro`) with 1 GiB RAM are generally INSUFFICIENT for stable operation of the full stack.** You will likely experience very slow performance or failures during the `docker build` process (especially `pip install` steps) due to memory limitations. Runtime stability can also be challenging.
        * If attempting to use a micro instance, configuring at least **2-4GB of SWAP space** is crucial, but it may not fully compensate for the lack of physical RAM.
        * **Recommended Instance Type (Paid):** For this project to run reliably (e.g., for daily ETL runs over several months for portfolio demonstration), an instance type such as **`t3.small` (2 vCPU, 2 GiB RAM)** is a more realistic minimum. For increased stability, a **`t3.medium` (2 vCPU, 4 GiB RAM)** would offer more comfort.
        * **Be aware that `t3.small`, `t3.medium`, and similar instance types are NOT fully covered by the AWS Free Tier's 750 hours/month allowance and WILL INCUR HOURLY CHARGES.** Plan your budget accordingly.
* **Key pair (login):** Create a new key pair or use an existing one. Download the `.pem` file and keep it secure – you'll need it for SSH access.
* **Network settings:**
    * Select the same VPC as your RDS instance.
    * **Firewall (security groups) (e.g., `ec2-book-pipeline-sg`):** Create a new security group or select an existing one. Configure inbound rules:
        * Allow SSH (TCP port 22) **only from your current IP address** (select "My IP" in the source dropdown for security).
        * Allow HTTP (TCP port 8080, or your chosen Airflow UI port) **only from your current IP address**.
* **Configure storage:** Default Free Tier root volume storage (e.g., 30 GiB gp2/gp3) is usually sufficient for the OS and application files.
* **Advanced details -> IAM instance profile (Highly Recommended):**
    * Create an IAM role (e.g., `EC2-S3-BookPipeline-Role`) with necessary permissions (e.g., `AmazonS3FullAccess` or a more restricted policy allowing read/write to your specific S3 bucket and potentially CloudWatch Logs access).
    * **Attach this IAM role** to the EC2 instance. This allows applications running on EC2 to securely access AWS services without needing explicit Access Keys stored on the instance.
* Launch the instance.

**Elastic IP (EIP) Setup:**
To ensure your EC2 instance has a static public IP address, an Elastic IP should be used.
* In the EC2 console, navigate to "Elastic IPs".
* Click "Allocate Elastic IP address".
* Once allocated, select the EIP and click "Actions" -> "Associate Elastic IP address".
* Choose your running EC2 instance and its private IP (if prompted) to associate the EIP with.
* Note its **Public IPv4 address (this is your Elastic IP)**.
* **EIP Costs:**
    * **One Elastic IP address associated with a RUNNING EC2 instance is FREE.**
    * Charges for an EIP will apply if it's allocated but **NOT associated** with any instance, OR if it's associated with a **STOPPED** instance, OR if it's an **additional** EIP beyond the first free one per region.

---
## 2. Deployment Steps on EC2

1.  **Connect to EC2 via SSH:**
    ```bash
    # Make your key file private first (run on your local machine)
    chmod 400 /path/to/your-key.pem 
    # Connect (replace placeholders)
    ssh -i /path/to/your-key.pem ubuntu@<your-ec2-elastic-ip> 
    ```
    *(Use `ec2-user@...` for Amazon Linux AMIs)*

2.  **Install Dependencies on EC2:**
    ```bash
    sudo apt update
    sudo apt upgrade -y 
    # Install Git, Python3 pip & venv (often pre-installed), Docker, Docker Compose
    sudo apt install -y git python3-pip python3-venv docker.io 
    # Install Docker Compose (example for v2)
    sudo apt install -y docker-compose-plugin # Or follow official Docker docs for latest method

    # Start and enable Docker service
    sudo systemctl start docker
    sudo systemctl enable docker
    # Add current user to the docker group to run docker commands without sudo
    sudo usermod -aG docker ${USER}
    # You will need to log out and log back in for docker group changes to take effect
    exit 
    ```
    **(Log out and SSH back into the instance for the `docker` group membership to apply.)**

3.  **Configure SWAP Space (Highly Recommended, Especially for Micro/Small Instances):**
    If using a memory-constrained instance (like `t2.micro` or even `t3.small`), creating SWAP space can prevent Out-Of-Memory errors.
    ```bash
    # Check if SWAP exists
    sudo swapon --show
    free -h
    # If no SWAP, create a 2GB SWAP file (adjust size if needed)
    sudo fallocate -l 2G /swapfile 
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    # Verify
    sudo swapon --show
    free -h
    # Make SWAP persistent across reboots
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab 
    ```

4.  **Clone Your Project Repository:**
    ```bash   
    git clone [https://github.com/brankowss/Cloud-Book-Price-Tracker-ELT-Pipeline.git](https://github.com/brankowss/Cloud-Book-Price-Tracker-ELT-Pipeline.git)   
    cd Cloud-Book-Price-Tracker-ELT-Pipeline   
    ```

5.  **Configure Environment Variables:**
    * **Create `.env` file:** Copy the example file and fill in your actual credentials. This file should be in the project root, next to `docker-compose.yml`.
        ```bash
        cp .env.example .env
        nano .env  # Edit the file with your actual credentials
        ```
    * **Ensure your `.env.example` (in Git) looks like this template and update your `.env` (on EC2, NOT in Git) accordingly:**
        ```ini
        # ========================
        # AWS RDS Configuration
        # ========================
        POSTGRES_HOST=your-rds-endpoint.region.rds.amazonaws.com
        POSTGRES_PORT=5432
        POSTGRES_USER=your_rds_master_username # e.g., postgres_admin
        POSTGRES_PASSWORD=your_rds_strong_password
        POSTGRES_DB=bookdb # Your initial DB name

        # ========================
        # AWS S3 Configuration
        # ========================
        # If using IAM Role on EC2 (recommended), these might not be needed by Airflow S3Hook
        # but can be useful for other tools or local testing if configured.
        # AWS_ACCESS_KEY_ID=your_aws_access_key_id 
        # AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
        S3_BUCKET_NAME=your-s3-bucket-name # e.g., your-name-book-scraper-raw
        AWS_REGION=your-aws-region # e.g., eu-central-1

        # ========================
        # Airflow Configuration
        # ========================
        AIRFLOW_EXECUTOR=LocalExecutor
        AIRFLOW_DATABASE_CONN=postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
        # Optional: Set Airflow UID to match host user for volume permissions
        # Find your host UID with 'id -u' on EC2 (e.g., 1000 for ubuntu user)
        # AIRFLOW_UID=1000 

        # ========================
        # Telegram Integration
        # ========================
        TELEGRAM_BOT_TOKEN=your_telegram_bot_token
        TELEGRAM_CHAT_ID=your_telegram_chat_id 
        ```
    * **Fill in Values:** Open the `.env` file on EC2 and replace placeholder values with your actual credentials and resource names (RDS endpoint, DB user/pass/name, S3 bucket name, AWS region, Telegram token/chat ID).
    * **Important:** Ensure the `.env` file is gitignored and **NEVER** commit it with real secrets.

6.  **Review `docker-compose.yml` and `Dockerfile`:**
    * Ensure your `docker-compose.yml` uses `build: ./airflow` (if your Dockerfile is in an `airflow` subdirectory) or `build: .` (if Dockerfile is in the root).
    * Ensure your `Dockerfile` correctly copies and installs `requirements.txt`. (Refer to previous advice on simplifying `requirements.txt` to avoid dependency conflicts).

7.  **Build and Run Docker Containers:**
    ```bash
    docker-compose up --build -d 
    ```
    * This step can take a significant amount of time, especially on memory-constrained instances, due to `pip install`. Be patient.
    * Monitor logs: `docker-compose logs -f` (or `docker-compose logs -f airflow-scheduler`, `docker-compose logs -f airflow-webserver`).
    * Allow a few minutes for Airflow services (webserver, scheduler, and the `airflow-init` service which runs `db upgrade` and creates a user) to initialize.

8.  **Initialize dbt & Airflow DAG:**
    * Wait for the Airflow UI to become accessible: `http://<your-ec2-elastic-ip>:8080` (Default login might be `admin`/`admin` if created by the init service, or what you set via `AIRFLOW_USER`/`AIRFLOW_PASSWORD` env vars).
    * **dbt Dependencies & Seed (If using):** Run these commands *inside* the Airflow container that will execute dbt tasks (e.g., `airflow-scheduler` or a dedicated `airflow-worker` service if you have one).
        ```bash
        # Adjust 'airflow-scheduler' if your service is named differently
        # Assumes your dbt project is mounted at /opt/spider_dbt inside the container
        docker-compose exec airflow-scheduler bash -c "cd /opt/spider_dbt && export DBT_PROFILES_DIR=. && dbt deps"
        docker-compose exec airflow-scheduler bash -c "cd /opt/spider_dbt && export DBT_PROFILES_DIR=. && dbt seed --target prod" 
        ```
    * **Unpause DAG:** Find the `book_ingestion_and_transformation` DAG in the Airflow UI and toggle it to **On (Unpause)**.

9.  **Test the Pipeline:**
    * Trigger the DAG manually in the Airflow UI for an initial run or wait for its next scheduled run.
    * Monitor the run via the Graph View and Task Logs in Airflow.
    * Check for Telegram notifications.
    * Verify data landing in S3 and being processed into your RDS database schemas (`raw`, `dbt_prod`).

---
## 3. Deployment Considerations & Portfolio Narrative

This project is designed as a comprehensive portfolio piece. While these setup instructions detail deploying to AWS, it's crucial to understand resource requirements and potential costs, especially concerning the AWS Free Tier.

* **EC2 Sizing:** As noted, `t2.micro`/`t3.micro` instances (1GiB RAM) are **insufficient** for reliable operation of the full stack (Airflow, Docker, Scrapy, dbt). Builds can be extremely slow or fail, and runtime stability is challenging.
    * **Recommendation:** An instance like **`t3.small` (2vCPU, 2GiB RAM)** is a more realistic minimum for development, testing, or a short-term portfolio run. For more robust operation, consider **`t3.medium` (2vCPU, 4GiB RAM)**. Be aware these instances will incur costs beyond the Free Tier.
    * **SWAP Space:** On any memory-constrained instance, configuring 2-4GB of SWAP space is highly recommended as a safety net.
* **RDS Storage:** The 20GB Free Tier storage for RDS can be consumed by user data (raw data, dbt models, Airflow metadata), indexes, and database system overhead over several months of daily data collection. Monitor "Free storage space" in CloudWatch.
* **Dependency Management:** Python dependency conflicts are common in complex projects. Simplifying `requirements.txt` to specify only core packages and allowing `pip` to resolve sub-dependencies is often an effective strategy to ensure successful Docker image builds.
* **Docker Volume Permissions:** Mounted volumes in Docker Compose can lead to permission errors (e.g., Airflow writing logs). Setting the `AIRFLOW_UID` environment variable in the `.env` file (to match the host user's UID, typically 1000 for `ubuntu`) can help resolve these issues when the Docker image supports it (like the official Airflow images).
* **Project Showcase (Interview Narrative):**
    Even if you don't run the pipeline continuously for many months on a paid instance due to budget, the key is to:
    1.  Successfully build and deploy the entire stack on AWS (e.g., on a `t3.small` for a test period to confirm functionality).
    2.  Run the pipeline end-to-end multiple times to validate its design and collect sample data.
    3.  Thoroughly document the architecture, setup (as in this guide), and code.
    4.  Be prepared to discuss the design choices, technologies used, challenges encountered (like resource limitations on Free Tier and how you'd address them with appropriate instance sizing), and how you would manage or scale it in a production-like scenario.
    *This setup guide reflects the steps to build and configure the project. The actual duration of continuous operation and choice of EC2 instance may vary based on individual project goals and budget.*

---
## 4. Decommissioning AWS Resources (Stopping Costs)

When you are finished with the project and want to avoid further AWS charges, you **MUST** delete all created resources.

1.  **RDS Database:**
    * Modify the instance to **disable "Deletion protection"**.
    * (Optional) Take a final snapshot if you want to preserve the data.
    * **Delete** the RDS instance (opt out of final snapshot if you took one, do not retain automated backups).
2.  **EC2 Instance:**
    * **Terminate** the EC2 instance.
    * Verify its associated **EBS Volume** is also deleted (or delete it manually if it persists).
3.  **Elastic IP:**
    * **Disassociate** the EIP from any resource.
    * **Release** the EIP.
4.  **S3 Bucket:**
    * **Empty** the S3 bucket (delete all objects).
    * **Delete** the S3 bucket.
5.  **IAM Role:**
    * Delete the IAM Role created for EC2 if no longer needed.
6.  **Billing Dashboard:**
    * **Check your AWS Billing Dashboard** after 24-48 hours to confirm that charges for these services have stopped.
