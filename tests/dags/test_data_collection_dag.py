import pytest
from unittest.mock import patch, MagicMock
import os
from datetime import datetime, timezone
from airflow.models import DagBag, TaskInstance

# Importing the DAG we want to test
# Ensure your environment or CI/CD setup includes the path to where your DAGs are stored
import sys
sys.path.append('../../airflow_home/dags')

@pytest.fixture(scope="class")
def dag_bag():
    return DagBag(dag_folder='../../airflow_home/dags', include_examples=False)

class TestScrapyDataCollectionDAG:
    def test_dag_loaded(self, dag_bag):
        """Ensure the DAG is in the DagBag and there are no errors."""
        dag = dag_bag.get_dag(dag_id='data_collection_dag')
        assert dag_bag.import_errors == {}, "No Import Failures"
        assert dag is not None, "DAG is loaded"

    def test_dag_structure(self, dag_bag):
        """Check the structure of the DAG."""
        dag = dag_bag.get_dag(dag_id='data_collection_dag')
        assert len(dag.tasks) == len(['aliexpress', 'amazon', 'printerval', 'teefury', 'teepublic', 'threadheads', 'threadless']), "All tasks are present"
        for task in dag.tasks:
            downstream_task_ids = set(task.downstream_task_ids)
            expected_task_ids = set()
            if task.task_id != 'run_threadless_spider':
                # Find the next task by sorting tasks and finding the next one
                sorted_tasks = sorted(['aliexpress', 'amazon', 'printerval', 'teefury', 'teepublic', 'threadheads', 'threadless'])
                next_task_index = sorted_tasks.index(task.task_id.split('_')[1]) + 1
                if next_task_index < len(sorted_tasks):
                    expected_task_ids = {f'run_{sorted_tasks[next_task_index]}_spider'}
            assert downstream_task_ids == expected_task_ids, f"Task {task.task_id} has correct downstream tasks"

    @patch('data_collection_dag.run_scrapy', return_value=None)
    def test_run_scrapy_tasks(self, mock_run_scrapy, dag_bag):
        """Test each Scrapy task execution by simulating it."""
        dag = dag_bag.get_dag(dag_id='data_collection_dag')
        execution_date = datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc)        
        for spider_name in ['aliexpress', 'amazon', 'printerval', 'teefury', 'teepublic', 'threadheads', 'threadless']:
            task = dag.get_task(task_id=f'run_{spider_name}_spider')
            if not task:
                raise Exception(f"Task not found: {spider_name}. Check task setup.")
            ti = TaskInstance(task=task, execution_date=execution_date)
            ti.run(ignore_ti_state=True)

# In your test setup or directly in the test
# os.environ['FYP_DATA_PATH'] = 'FYP/data/raw'  # Adjust the path as needed
# os.environ['FYP_SCRAPY_PATH'] = 'FYP/scripts/websiteScraping/'  # Adjust the path as needed

# @pytest.mark.usefixtures("dag_bag")
# class TestEnvironment:
#     def test_environment_variables(self):
#         """Ensure environment variables are correctly set."""
#         assert os.getenv('FYP_DATA_PATH') is not None, "FYP_DATA_PATH is set"
#         assert os.getenv('FYP_SCRAPY_PATH') is not None, "FYP_SCRAPY_PATH is set"
