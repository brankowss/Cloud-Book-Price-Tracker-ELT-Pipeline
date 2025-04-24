FROM apache/airflow:2.10.0-python3.11

WORKDIR /opt

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt \
    && rm -f requirements.txt

COPY . .

USER root
RUN chown -R airflow:airflow /opt/booksscraper \
    && chown -R airflow:airflow /opt/spider_dbt \
    && chmod -R 755 /opt/booksscraper \
    && chmod -R 755 /opt/spider_dbt

USER airflow

CMD ["bash"]






