FROM apache/airflow:2.10.0-python3.11

# Set the working directory to the folder where the project is located
WORKDIR /opt

# Copy the requirements.txt file to the working directory
COPY requirements.txt .

# Install all required dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the remaining files to the directory
COPY . .

# Switch to root to modify permissions
USER root
RUN chmod -R 777 /opt/booksscraper 
RUN chmod -R 777 /opt/spider_dbt
# Switch back to airflow user for security
USER airflow






