# this file should be called before training the style-gan ada. It currently gets all the datasets, labels etc and zips it with the images so that it is dijestable for train.py
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
    images_info = []

    for meta in metadata:
        meta_dict = meta.to_dict()
        product_id = meta_dict['product_id']
        image_path = f'images/{product_id}.png'
        local_path = os.path.join(local_dir, f'{product_id}.png')
        #prepare metadata info for JSON
        images_info.append({
            "filename": f'{product_id}.png',
            "weight": meta_dict.get('weight', 0),  # Default weight if not specified
            "labels": {
                "colors": meta_dict.get('color', ["red", "green","blue", "yellow", "orange", "purple", "black", "white", "gray", "brown"]),  # Default color if not specified
                "complexity": meta_dict.get('complexity', 'normal')  # Default complexity if not specified
            }
        })

        # Download the image
        blob = bucket.blob(image_path)
        try:
            blob.download_to_filename(local_path)
            print(f'Downloaded {product_id}.png successfully.')
        except FirebaseError as e:
            print(f'Failed to download {product_id}.png: {e}')

        metadata_path = os.path.join(local_dir, metadata_filename)
        with open(metadata_path, 'w') as f:
            json.dump({"images": images_info}, f, indent=4)
        
    return metadata_path

def zip_dir(folder_path, output_path):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                zipf.write(os.path.join(root, file), arcname=file)
    print(f'Created zip archive at {output_path}')

    


# Usage
metadata_file = download_images('products', '../../data/training_images', 'dataset.json')
zip_dir('../../data/training_images', '../../data/training_dataset.zip')
