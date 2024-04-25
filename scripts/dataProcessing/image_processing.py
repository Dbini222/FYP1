import firebase_admin
import requests
from pathlib import Path
from PIL import Image, ImageOps
from io import BytesIO
from firebase_admin import credentials, storage, firestore

# Get the path to the directory where this script is running
current_file_path = Path(__file__).resolve()

# Traverse up to find the FYP directory (assuming this script is somewhere inside the FYP directory)
fyp_directory = current_file_path.parent
while fyp_directory.name != 'FYP' and fyp_directory.parent != fyp_directory:
    fyp_directory = fyp_directory.parent

# Now append the relative path to the key file within the FYP directory
firebase_key_path = fyp_directory / 'fyp-project-83298-firebase-adminsdk-omga1-3c741ce672.json'

# Check if the path exists
if not firebase_key_path.exists():
    raise FileNotFoundError(f"Firebase key file not found at {firebase_key_path}")

# Initialize Firebase Admin SDK
cred = credentials.Certificate(firebase_key_path)
firebase_admin.initialize_app(cred, {
    'storageBucket': 'fyp-project-83298.appspot.com'
})

# Get Firestore and Storage clients
bucket = storage.bucket()
db = firestore.client()

# different directories for original and preprocessed images
original_images_dir = 'original_images/'
preprocessed_images_dir = 'preprocessed_images/'

#Fetch metadata from Firestore
def fetch_metadata():
    try:
        metadata = {}
        docs = db.collection('products').stream()
        for doc in docs:
            metadata[doc.id] = doc.to_dict()
        return metadata
    except Exception as e:
        print(f"Failed to fetch metadata from Firestore: {e}")
        return {}

def list_files_in_storage():
    files= []
    blobs = bucket.list_blobs()
    for blob in blobs:
        files.append(blob.name)
    return files

def upload_image(img_byte_arr, filename, dir):
    blob = bucket.blob(dir + filename)
    blob.upload_from_file(img_byte_arr, content_type='image/jpeg')
    print(f"Uploaded image {filename} to Firebase Storage in directory {dir}.")

def process_and_upload_image(image_path, doc_id):
    response = requests.get(image_path)
    if response.status_code == 200:
    # Open the original image and upload it
       og_img = Image.open(BytesIO(response.content))
       og_img_byte_arr = BytesIO()
       og_img.save(og_img_byte_arr, format='JPEG')
       og_img_byte_arr.seek(0)
       original_filename = f"{doc_id}.jpg"  # Keep the original extension
       upload_image(og_img_byte_arr, original_filename, original_images_dir)

    #process image
       preprocessed_img = preprocess_image(og_img)
       preprocessed_byte_arr = BytesIO()
       preprocessed_img
       preprocessed_byte_arr.seek(0)
       preprocessed_filename = f"{doc_id}.jpg"  # Same name as the doc_id for that product
       upload_image(preprocessed_byte_arr, preprocessed_filename, preprocessed_images_dir)
       print(f"Uploaded processed image {preprocessed_filename} to Firebase Storage.")
    else:
        print(f"Failed to download image from {image_path}")

def preprocess_image(img):
    # Apply image preprocessing here
    img = img.resize((1024, 1024))
    img = img.convert('RGB')


    return img

def sync_images_with_metadata():
    metadata = fetch_metadata()
    storage_files = list_files_in_storage()
    metadata_ids = set(metadata.keys())
    storage_ids = set([file.split('.')[0] for file in storage_files]) # get rid of the .jpg extension
    missing_ids = metadata_ids - storage_ids # new ids that need to be uploaded

    for doc_id in missing_ids:
        image_path = metadata[doc_id]['images']
        process_and_upload_image(image_path, doc_id) if image_path in metadata[doc_id] else print(f"No image URL found for document ID {doc_id}")


    