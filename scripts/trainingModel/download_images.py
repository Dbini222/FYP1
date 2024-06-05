# Binary encoding for each class, i.e. 00110101012
import json
import os
import zipfile

import firebase_admin
from firebase_admin import credentials, firestore, storage
from firebase_admin.exceptions import FirebaseError

# Initialize Firebase
cred_path = '../../fyp-project-83298-firebase-adminsdk-omga1-3c741ce672.json'
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred, {
    'storageBucket': 'fyp-project-83298.appspot.com'
})
db = firestore.client()
bucket = storage.bucket()

def download_images(metadata_collection, local_dir, metadata_filename):
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    metadata = db.collection(metadata_collection).stream()
    labels_info = []
    weights_info = []

    # Define the color and complexity mappings
    colors = ["red", "green", "blue", "yellow", "orange", "purple", "brown", "grey", "black", "white"]
    complexities = {"simple": 0, "normal": 1, "complex": 2}

    for meta in metadata:
        meta_dict = meta.to_dict()
        product_id = meta_dict['product_id']
        image_path = f'images/{product_id}.png'
        local_path = os.path.join(local_dir, f'{product_id}.png')

        # Create binary color vector
        color_vector = [1 if color in meta_dict.get('color', []) else 0 for color in colors]
        complexity_index = complexities.get(meta_dict.get('complexity', 'normal'))

        # Combine color vector with complexity index
        label_vector = color_vector + [complexity_index]

        # Prepare labels and weights for JSON
        labels_info.append([os.path.join(local_dir, f'{product_id}.png'), label_vector])
        weights_info.append([os.path.join(local_dir, f'{product_id}.png'), meta_dict.get('weight', 0.0)])

        # Download the image
        blob = bucket.blob(image_path)
        try:
            blob.download_to_filename(local_path)
            print(f'Downloaded {product_id}.png successfully.')
        except FirebaseError as e:
            print(f'Failed to download {product_id}.png: {e}')

    # Save metadata to JSON
    metadata_path = os.path.join(local_dir, metadata_filename)
    with open(metadata_path, 'w') as f:
        json.dump({"labels": labels_info, "weights": weights_info}, f, indent=4)

    return metadata_path


def zip_dir(folder_path, output_path):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                zipf.write(os.path.join(root, file), arcname=file)
    print(f'Created zip archive at {output_path}')

# Usage
metadata_file = download_images('products', '../../data/processed', 'dataset.json')
zip_dir('../../data/processed', '../../data/training_dataset.zip')
