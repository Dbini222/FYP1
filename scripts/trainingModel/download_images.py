import os
import json
import zipfile
import firebase_admin
from firebase_admin import credentials, firestore, storage
from google.cloud import exceptions

# Initialize Firebase
def initialize_firebase():
    cred_path = '../../fyp-project-83298-firebase-adminsdk-omga1-3c741ce672.json'
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'fyp-project-83298.appspot.com'
    })

# Batch fetch documents
def fetch_documents_in_batches(collection, batch_size=10):
    client = firestore.client()
    last_doc = None
    while True:
        query = client.collection(collection).order_by('__name__').limit(batch_size)
        if last_doc:
            query = query.start_after(last_doc)
        
        docs = list(query.stream())
        if not docs:
            break
        yield docs
        last_doc = docs[-1]

# Download images and process documents
def download_images(local_dir, metadata_filename):
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
    bucket = storage.bucket()
    labels_info = []
    weights_info = []
    
    try:
        for batch in fetch_documents_in_batches('products', 20):
            for doc in batch:
                doc_id = doc.id
                meta_dict = doc.to_dict()
                image_path = f'images/{doc_id}.jpg'  # Changed to .jpg
                local_path = os.path.join(local_dir, f'{doc_id}.jpg')  # Changed to .jpg
                blob = bucket.blob(image_path)
                
                if blob.exists():
                    blob.download_to_filename(local_path)
                    print(f'Downloaded {doc_id}.jpg successfully.')  # Changed to .jpg
                    # Process labels and weights
                    color_vector = [1 if color in meta_dict.get('color', []) else 0 for color in colors]
                    complexity_index = complexities.get(meta_dict.get('complexity', 'normal'))
                    label_vector = color_vector + [complexity_index]
                    labels_info.append([local_path, label_vector])
                    weights_info.append([local_path, meta_dict.get('weight', 0.0)])
                else:
                    print(f'Image {doc_id}.jpg does not exist in storage.')  # Changed to .jpg
    
    except exceptions.GoogleCloudError as e:
        print(f'Error while processing documents: {str(e)}')

    # Save metadata to JSON
    metadata_path = os.path.join(local_dir, metadata_filename)
    with open(metadata_path, 'w') as f:
        json.dump({"labels": labels_info, "weights": weights_info}, f, indent=4)
    return metadata_path

# Zip directory
def zip_dir(folder_path, output_path):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                zipf.write(os.path.join(root, file), arcname=file)
    print(f'Created zip archive at {output_path}')

# Main execution
if __name__ == '__main__':
    initialize_firebase()
    metadata_file = download_images('../../data/processed', 'dataset.json')
    zip_dir('../../data/processed', '../../data/training_dataset.zip')
