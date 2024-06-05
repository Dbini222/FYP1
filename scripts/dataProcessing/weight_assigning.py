
from pathlib import Path
import firebase_admin
import numpy as np
import pandas as pd
from firebase_admin import credentials, firestore

from google.api_core.exceptions import ResourceExhausted, RetryError
import time

def main():
    # Set up Firebase connection
    current_file_path = Path(__file__).resolve()
    fyp_directory = current_file_path.parent
    while fyp_directory.name != 'FYP' and fyp_directory.parent != fyp_directory:
        fyp_directory = fyp_directory.parent

    firebase_key_path = fyp_directory / 'fyp-project-83298-firebase-adminsdk-omga1-3c741ce672.json'
    if not firebase_key_path.exists():
        raise FileNotFoundError(f"Firebase key file not found at {firebase_key_path}")

    cred = credentials.Certificate(str(firebase_key_path))
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print('Starting...')
    # Fetch and process data
    data = fetch_data_from_firestore(db)
    if data.empty:
        print("No data found in Firestore.")
        return
    # data = generate_test_data()
    weighted_data = calculate_weights(data)
    # print(weighted_data)
    update_weights_in_firestore(db, weighted_data)

def generate_test_data():
    np.random.seed(42)  # For reproducible random results

    # Create a DataFrame with 100 entries
    data = pd.DataFrame({
        'product_id': range(1, 101),  # Product IDs from 1 to 100
        'age': np.random.randint(0, 2, size=100),  # Random ages between 1 and 50
        'popularity': np.random.uniform(1, 2501, size=100)  # Random popularity scores between 0.1 and 2501
    })

    # Introduce specific edge cases
    data.loc[95:99, 'age'] = [1, 50, 1, 50, 1]  # Min and max ages
    data.loc[95:99, 'popularity'] = [2501, 2501, 1, 1, 2501]  # Max and min popularity

    return data


def fetch_data_from_firestore(db):
    try:
        collections = db.collection('products').stream()
        data = [{'document_id': doc.id, **doc.to_dict()} for doc in collections]
        df = pd.DataFrame(data)
        if df['popularity'].isna().any():
            nan_popularity_ids = df[df['popularity'].isna()]['document_id'].tolist()
            print(f"Entries with NaN in 'popularity': {nan_popularity_ids}")
        return df
    except Exception as e:
        print(f"Failed to fetch data from Firestore: {e}")
        return pd.DataFrame()


def calculate_weights(data):
    data['popularity'] = data['popularity'].astype(float)

    print(data)

    max_popularity = np.log(data['popularity'].max() + 0.1)

    total_weight = data['weight'].sum()
    data['weight'] /= total_weight
    return data


def update_weights_in_firestore(db, data):
    batch_size = 500
    batch = db.batch()
    changes_made = False
    retry_count = 0
    max_retries = 5
    base_wait_time = 2  # seconds

    for index, row in data.iterrows():
        doc_id = str(row['document_id'])
        weight = row['weight']
        doc_ref = db.collection('products').document(doc_id)
        doc = doc_ref.get()
        if doc.exists:
            existing_weight = doc.to_dict().get('weight', None)
            if existing_weight != weight:
                batch.update(doc_ref, {'weight': weight})
                changes_made = True
        if (index + 1) % batch_size == 0:
            commit_batch(batch, retry_count, max_retries, base_wait_time)
            batch = db.batch()

    if changes_made:
        commit_batch(batch, retry_count, max_retries, base_wait_time)
        print("Batch update committed.")


def commit_batch(batch, retry_count, max_retries, base_wait_time):
    while retry_count < max_retries:
        try:
            batch.commit()
            return
        except (ResourceExhausted, RetryError) as e:
            wait_time = base_wait_time * (2 ** retry_count)
            print(f"Quota exceeded. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            retry_count += 1
    print("Max retries exceeded. Some updates may not have been committed.")


if __name__ == "__main__":
    main()
