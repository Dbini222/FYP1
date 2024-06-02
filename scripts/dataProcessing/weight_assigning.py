# this file gets all the weights of the products in the database and assigns them weights. Only need to use it in the initial dataset
from pathlib import Path

import firebase_admin
import numpy as np
import pandas as pd
from firebase_admin import credentials, firestore


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

#only getting popularity related weights
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
    max_popularity = np.log(data['popularity'].max() + 0.1)

    data['weight'] = (1- (np.log(max_popularity) / np.log(data['popularity']))) #inverted popularity
    total_weight = data['weight'].sum()
    data['weight'] /= total_weight
    return data

def update_weights_in_firestore(db, data):
    for index, row in data.iterrows():
        doc_id = str(row['document_id'])
        weight = row['weight']
        doc_ref = db.collection('products').document(doc_id)
        try:
            doc_ref.update({'weight': weight})
            print(f"Updated document {doc_id} with new weight: {weight}")
        except Exception as e:
            print(f"Failed to update weight for document {doc_id}: {e}")
if __name__ == "__main__":
    main()
