import csv
import os
import subprocess
from datetime import datetime, timedelta

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator

"""
Steps:
1. Run each Scrapy spider to collect data
2. Increment the age of the data 
3. Update the CSV file with the new age
"""
default_args = {
    'owner': 'airflow',
    'email': ['dbini222@gmail.com'],
    'start_date': datetime(2023, 1, 1),
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retry_delay': timedelta(minutes=5),
}

dag1 = DAG(
    'data_collection_dag',
    default_args=default_args,
    description='DAG to run multiple Scrapy spiders and save output to CSV with dynamic age',
    schedule='0 0 1,15 * *',  # At 00:00 on the 1st and 15th of every month
    catchup=False
)


def run_scrapy(spider_name):
    """Function to run a specified scrapy spider and output results to CSV"""
    home_dir = os.path.expanduser('~')
    output_path = os.path.join(home_dir, 'FYP', 'data', 'raw')
    scrapy_dir = os.path.join(home_dir, 'FYP', 'scripts', 'websiteScraping')
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    os.chdir(scrapy_dir)
    subprocess.run(['scrapy', 'crawl', spider_name, '-o', os.path.join(output_path, f'{spider_name}.csv')], check=True)

def include_age_and_update_csv(spider_name):
    """Update the CSV file to include this age"""
    home_dir = os.path.expanduser('~')
    csv_file_path = os.path.join(home_dir, 'FYP', 'data', 'raw', f'{spider_name}.csv')
    temp_file_path = os.path.join(home_dir, 'FYP', 'data', 'raw', f'temp_{spider_name}.csv')
     
    age = int(Variable.get("age", default_var=0))
       
    # Add age to CSV
    with open(csv_file_path, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        data = list(reader)
        fieldnames = reader.fieldnames + ['age']
    
    with open(temp_file_path, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            row['age'] = age
            writer.writerow(row)
    
    os.replace(temp_file_path, csv_file_path)

def increment_age():
    age = int(Variable.get("age", default_var=0)) + 1
    Variable.set("age", age)

# download images from the URLs, saves them in data/raw/preprocessed_images
def data_processor():
    home_dir = os.path.expanduser('~')
    data_process_dir = os.path.join(home_dir, 'FYP', 'scripts', 'dataProcessing')
    try:
        os.chdir(data_process_dir)
        print("Deduplicating metadata in database and new data")
        subprocess.run(['python', 'deduplication_metadata.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error deduplicating: {e}")
    spider_name = 'image_downloader'
    data_process_dir = os.path.join(home_dir, 'FYP', 'scripts', 'websiteScraping')
    try:
        subprocess.run(['scrapy', 'crawl', spider_name], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Scrapy spider: {e}")
    try:
        print("Processing images")
        subprocess.run(['python', 'image_processing.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error processing images: {e}")

spider_names = ['amazon', 'printerval', 'teefury', 'teepublic', 'threadheads', 'threadless']
previous_task = None

for spider_name in spider_names:
    run_task = PythonOperator(
        task_id=f'run_{spider_name}_spider',
        python_callable=run_scrapy,
        op_args=[spider_name],
        dag=dag1
    )
    
    include_age_task = PythonOperator(
        task_id=f'include_age_and_update_{spider_name}_csv',
        python_callable=include_age_and_update_csv,
        op_args=[spider_name],
        dag=dag1
    )
    
    if previous_task:
        previous_task >> run_task
    run_task >> include_age_task  # Chain to run after the spider
    previous_task = include_age_task

final_task = PythonOperator(
    task_id='increment_age_final',
    python_callable=increment_age,
    dag=dag1
)

process_data = PythonOperator(
    task_id='process_data',
    python_callable=data_processor,
    dag=dag1
)




previous_task >> final_task >> process_data
