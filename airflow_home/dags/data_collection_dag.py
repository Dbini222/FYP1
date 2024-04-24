from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import subprocess

# This DAG runs multiple Scrapy spiders and saves the output to CSV files in data/raw
# The main tasks for this DAG is to:
# 1. Run the Scrapy spiders sequentially
# 2. Save the output to CSV files in FYP/data/raw
 
 
default_args = {
    'owner': 'airflow',
    'email': ['dbini222@gmail.com'],
    'start_date': datetime(2023, 1, 1),
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'data_collection_dag',
    default_args=default_args,
    description='DAG to run multiple Scrapy spiders and save output to CSV',
    schedule='0 0 1,15 * *',  # At 00:00 on the 1st and 15th of every month,
    catchup=False
)

def run_scrapy(spider_name):
    """Function to run a specified scrapy spider and output results to CSV"""
    home_dir = os.path.expanduser('~')
    output_path = os.path.join(home_dir, 'FYP', 'data', 'raw')
    if not os.path.exists(output_path):
        os.makedirs(output_path)
        print(f'Created directory {output_path}')
    scrapy_dir = os.path.join(home_dir, 'FYP', 'scripts', 'websiteScraping')
    os.chdir(scrapy_dir)
    try:
        subprocess.run(['scrapy', 'crawl', spider_name, '-o', os.path.join(output_path, f'{spider_name}.csv')], check=True)
        print(f"Successfully ran spider {spider_name} and saved output to {os.path.join(output_path, f'{spider_name}.csv')}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to run spider {spider_name}. Error: {e}")

spider_names = [ 'amazon', 'printerval', 'teefury', 'teepublic', 'threadheads', 'threadless']  # List of spider names
previous_task = None

for spider_name in spider_names:
    task = PythonOperator(
        task_id=f'run_{spider_name}_spider',
        python_callable=run_scrapy,
        op_args=[spider_name],
        dag=dag
    )

    if previous_task:
        previous_task >> task  # Chain tasks sequentially
    previous_task = task