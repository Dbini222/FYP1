import json
import os
import zipfile
from pathlib import Path

import firebase_admin
import numpy as np
import pandas as pd
from firebase_admin import credentials, firestore, storage
from firebase_admin.exceptions import FirebaseError


def main():
    # Setup and initialize Firebase
    current_file_path = Path(__file__).resolve()
    fyp_directory = current_file_path.parent
    while fyp_directory.name != 'FYP' and fyp_directory.parent != fyp_directory:
        fyp_directory = fyp_directory.parent

    firebase_key_path = fyp_directory / 'fyp-project-83298-firebase-adminsdk-omga1-3c741ce672.json'
    if not firebase_key_path.exists():
        raise FileNotFoundError(f"Firebase key file not found at {firebase_key_path}")

    cred = credentials.Certificate(str(firebase_key_path))
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'fyp-project-83298.appspot.com'
    })
    db = firestore.client()
    bucket = storage.bucket()

    # Specify directory paths and metadata filename
    local_dir = fyp_directory / 'data' / 'processed'  # Path for saving downloaded images and metadata
    metadata_filename = 'dataset.json'  # Metadata JSON filename
    collection_name = 'products'  # Firestore collection name

    download_and_process_images(db, bucket, collection_name, local_dir, metadata_filename)

def download_and_process_images(db, bucket, collection_name, local_dir, metadata_filename):
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    metadata = db.collection(collection_name).stream()
    labels_info = []
    weights_info = []

    colors = ["red", "green", "blue", "yellow", "orange", "purple", "brown", "grey", "black", "white"]
    complexities = {"simple": 0, "normal": 1, "complex": 2}

    for meta in metadata:
        meta_dict = meta.to_dict()
        product_id = meta_dict['product_id']
        image_path = f'images/{product_id}.png'
        local_path = local_dir / f'{product_id}.png'

        # Create binary color vector and complexity index
        color_vector = [1 if color in meta_dict.get('color', []) else 0 for color in colors]
        complexity_index = complexities.get(meta_dict.get('complexity', 'normal'), 1)
        label_vector = color_vector + [complexity_index]

        labels_info.append([str(local_path), label_vector])
        weights_info.append([str(local_path), meta_dict.get('weight', 0.0)])

        # Download the image
        blob = bucket.blob(image_path)
        try:
            blob.download_to_filename(local_path)
            print(f'Downloaded {product_id}.png successfully.')
        except FirebaseError as e:
            print(f'Failed to download {product_id}.png: {e}')

    # Save metadata to JSON
    metadata_path = local_dir / metadata_filename
    with open(metadata_path, 'w') as f:
        json.dump({"labels": labels_info, "weights": weights_info}, f, indent=4)

    # Zip the directory with images and metadata
    zip_dir(local_dir, local_dir.parent / 'training_dataset.zip')

def zip_dir(folder_path, output_path):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname=arcname)
    print(f'Created zip archive at {output_path}')

if __name__ == "__main__":
    main()

# from pathlib import Path

# import firebase_admin
# import numpy as np
# import pandas as pd
# from firebase_admin import credentials, firestore


# def main():
#     # Set up Firebase connection
#     current_file_path = Path(__file__).resolve()
#     fyp_directory = current_file_path.parent
#     while fyp_directory.name != 'FYP' and fyp_directory.parent != fyp_directory:
#         fyp_directory = fyp_directory.parent

#     firebase_key_path = fyp_directory / 'fyp-project-83298-firebase-adminsdk-omga1-3c741ce672.json'
#     if not firebase_key_path.exists():
#         raise FileNotFoundError(f"Firebase key file not found at {firebase_key_path}")

#     cred = credentials.Certificate(str(firebase_key_path))
#     firebase_admin.initialize_app(cred)
#     db = firestore.client()

#     # Fetch and process data
#     data = fetch_data_from_firestore(db)
#     if data.empty:
#         print("No data found in Firestore.")
#         return
#     # data = generate_test_data()
#     weighted_data = calculate_weights(data)
#     # print(weighted_data)
#     update_weights_in_firestore(db, weighted_data)

# def generate_test_data():
#     np.random.seed(42)  # For reproducible random results

#     # Create a DataFrame with 100 entries
#     data = pd.DataFrame({
#         'product_id': range(1, 101),  # Product IDs from 1 to 100
#         'age': np.random.randint(0, 2, size=100),  # Random ages between 1 and 50
#         'popularity': np.random.uniform(1, 2501, size=100)  # Random popularity scores between 0.1 and 2501
#     })

#     # Introduce specific edge cases
#     data.loc[95:99, 'age'] = [1, 50, 1, 50, 1]  # Min and max ages
#     data.loc[95:99, 'popularity'] = [2501, 2501, 1, 1, 2501]  # Max and min popularity

#     return data

# def fetch_data_from_firestore(db):
#     try:
#         collections = db.collection('products').stream()
#         data = [{'product_id': str(doc.id), **doc.to_dict()} for doc in collections]
#         df = pd.DataFrame(data)
#         df['age'] = df['age'].replace(0, 0.01)
#         df['age'].fillna
#         if df['age'].notna().sum() != df['popularity'].notna().sum():
#             raise ValueError("Mismatch in non-NaN counts between 'age' and 'popularity'")
#         if df['age'].isna().any():
#             raise ValueError("'age' contains NaN values")
#         if df['popularity'].isna().any():
#             raise ValueError("'popularity' contains NaN values")
#         return df
#     except Exception as e:
#         print(f"Failed to fetch data from Firestore: {e}")
#         return pd.DataFrame()

# def calculate_weights(data):
#     data['age'] = data['age'].replace(0, 0.01)
#     data['age'] = data['age'].astype(float)
#     data['popularity'] = data['popularity'].astype(float)
#     max_age = data['age'].max() + 1
#     max_popularity = np.log(data['popularity'].max() + 1)

#     data['weight'] = (1 / ((data['age'] + 1) / max_age)) * (np.log(max_popularity) / np.log(data['popularity'] + 1))
#     total_weight = data['weight'].sum()
#     data['weight'] /= total_weight
#     return data

# def update_weights_in_firestore(db, data):
#     for index, row in data.iterrows():
#         product_id = str(row['product_id'] )                                                                                                         
#         weight = row['weight']
#         doc_ref = db.collection('products').document(product_id)
#         try:
#             doc_ref.update({'weight': weight})  # Use update to modify only the weight field
#             print(f"Updated product {product_id} with new weight: {weight}")
#         except Exception as e:
#             print(f"Failed to update weight for product {product_id}: {e}")

# if __name__ == "__main__":
#     main()
