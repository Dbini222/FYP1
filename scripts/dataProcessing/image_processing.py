import os

import pandas as pd
import sys
from collections import OrderedDict
import firebase_admin
import numpy as np
import torch
from firebase_admin import credentials, firestore, storage
from PIL import Image
from sklearn.cluster import KMeans
from torchvision import transforms

# Add yolov5 directory to the system path
current_dir = os.path.dirname(os.path.abspath(__file__))
yolov5_dir = os.path.join(current_dir, '../../yolov5')
sys.path.append(yolov5_dir)

# Load the custom-trained model
# model = torch.hub.load(
#     yolov5_dir, 
#     'custom', 
#     path=os.path.join(yolov5_dir, 'runs/train/exp2/weights/best.pt'), 
#     source='local'
# )
def initialize_firebase():
    """Initializes Firebase if it hasn't been initialized yet."""
    try:
        # Attempt to get the existing app, raises ValueError if not yet initialized
        firebase_admin.get_app()
    except ValueError:
        # If not initialized, do so now
        cred = credentials.Certificate('../../fyp-project-83298-firebase-adminsdk-omga1-3c741ce672.json')
        firebase_admin.initialize_app(cred, {
            'storageBucket': 'fyp-project-83298.appspot.com'
        })
def save_to_firebase(processed_images):
    """Save all processed images and their metadata in batch to Firebase."""
    initialize_firebase()
    db = firestore.client()
    bucket = storage.bucket()
    batch = db.batch()

    for image, path, colors, complexity in processed_images:
        doc_id = os.path.splitext(os.path.basename(path))[0]
        doc_ref = db.collection('products').document(doc_id)
        doc = doc_ref.get()

        if not doc.exists or doc.to_dict().get('image_stored') is None:
            # Process and upload image only if not already done
            temp_path = '/tmp/{}'.format(path)
            processed_image = Image.fromarray((image * 255).astype(np.uint8))
            processed_image.save(temp_path, 'JPEG')

            blob = bucket.blob('images/{}'.format(path))
            blob.upload_from_filename(temp_path)
            url = blob.public_url
            os.remove(temp_path)

            batch.set(doc_ref, {'colors': colors, 'complexity': complexity, 'image_stored': url}, merge=True)

    batch.commit()
    print("Firebase batch update completed.")

# def save_to_firebase(processed_images):
#     initialize_firebase()
#     db = firestore.client()
#     bucket = storage.bucket()
#     for image, path, colors, complexity in processed_images:
#         try:
#             # Save image to a temporary file
#             temp_path = '/tmp/{}'.format(path)
#             processed_image = Image.fromarray((image * 255).astype(np.uint8))
#             processed_image.save(temp_path, 'JPEG')
#             print(temp_path)

#             # Upload to Firebase Storage at the root level
#             blob = bucket.blob('images/{}'.format(path))  # Changed from 'images/{filename}' to just '{filename}'
#             blob.upload_from_filename(temp_path)
            
#             # Get URL of the uploaded file
#             url = blob.public_url
            
#             # Clean up the temporary file
#             os.remove(temp_path)
            
#             # Document ID is the filename without the extension
#             doc_id = os.path.splitext(path)[0]
#             print(doc_id)

#             # Update Firestore with the URL and additional metadata
#             doc_ref = db.collection('products').document(doc_id)
#             doc = doc_ref.get()
#             # Check if the document exists and if it contains the 'color' field
#             if doc.exists and 'color' in doc.to_dict():
#                 # The 'color' field exists, so continue
#                 pass
#             else:
#                 doc_ref.update({'colors': colors})
#                 doc_ref.update({'complexity': complexity})
#                 doc_ref.update({'image_stored': url})
#         except Exception as e:
#             print('Failed to save image to Firebase: /{}', format(e))


def crop_image(img, detection):
    #checking it's not a plain t-shirt
    if detection is None or detection.nelement() == 0:
        print("No valid detection found")
        return None
    try:
        # if detection.dim() == 3:
        #     detection = detection.squeeze(0)
        # if detection.dim() == 1:
        #     detection = detection.unsqueeze(0)
        # detection = detection[0]
        x1, y1, x2, y2, _, _ = detection.tolist()
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        # x1, y1, x2, y2 = detection[:4].item().int()

        

        # Proceed if there are detections
        # if detections.size(0) > 0:
        #     # Here we take the first detection assuming detections are sorted or that any detection is acceptable
        #     detection = detections[0]
        #     detection = detection.squeeze(0) #accessing first detection of the image
        print(x1, y1, x2, y2)
        center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
        box_size = int(min(max(x2 - x1, y2 - y1) * 1.2, max(x2 - x1, y2 - y1)+ 25))
        print (box_size - max(x2 - x1, y2 - y1))
        half_size = box_size // 2
        square_x1 = max(center_x - half_size, 0)
        square_y1 = max(center_y - half_size, 0)
        square_x2 = square_x1 + box_size
        square_y2 = square_y1 + box_size

        if square_x2 > img.width:
            square_x2 = img.width
            square_x1 = max(square_x2 - box_size, 0)
        if square_y2 > img.height:
            square_y2 = img.height
            square_y1 = max(square_y2 - box_size, 0)

        crop = img.crop((square_x1, square_y1, square_x2, square_y2))
        return crop
    except Exception as e:
        print("Failed to crop image: /{}", format(e))
  

def get_dominant_colors_and_complexity(image, num_colors=10):
    #using k means clustering to determine dominant colours and complexity of an image
    image = image.resize((200, 200))  # as dominant color extraction is usually in smaller images
    image = image.convert('RGB')
    data = np.reshape(np.array(image), (-1, 3))
    kmeans = KMeans(n_clusters=num_colors).fit(data)
    colors = kmeans.cluster_centers_
    print(colors)
    colors_arr = [find_nearest_color(color) for color in colors.astype(int)]
    unique_colors = list(OrderedDict.fromkeys(colors_arr)) #preserving original order of most common colors
    complexity = (
        'simple' if len(unique_colors) <= 2 else
        'normal' if len(unique_colors) <= 3 else 
        'complex'
    )
    return unique_colors, complexity

def replace_transparent_background(image_path, background_color=(255, 255, 255)):
    # Open the image
    img = Image.open(image_path).convert("RGBA")

    # Create a new image with the same size and the desired background color
    background = Image.new("RGBA", img.size, background_color + (255,))

    # Composite the original image on the background
    combined = Image.alpha_composite(background, img)

    # Convert to RGB (discard alpha channel)
    return combined.convert("RGB")
# Load images from a list of file paths as a list of PIL images
def load_images(image_paths):
    try:
        images = [replace_transparent_background(p) for p in image_paths]  # Ensuring RGB and no alpha channels
        return images
    except Exception as e:
        print("Failed to load images: /{}", format(e))

def detect_objects_batch(images, model):
    try:
        results = model(images)
        return results
    except Exception as e:
        print("Failed to detect objects: /{}", format(e))
        return None

def resize_and_normalize(img, size=(1024, 1024)):
    """Resize and normalize a single image."""
    if img is None:
        return None
    try:
        img = img.resize(size, Image.Resampling.LANCZOS) # Resize image to 1024x1024 pixels, make it smaller if GPU not available
        img_array = np.array(img) / 255.0
        return img_array
    except Exception as e:
        print("Failed to resize and normalize image: /{}", format(e))
        return None

def find_nearest_color(rgb):
    color_names = {
    "red": (255, 0, 0),
    "green": (0, 128, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "orange": (255, 165, 0),
    "purple": (128, 0, 128),
    # "pink": (255, 192, 203),
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "gray": (128, 128, 128),
    "brown": (150, 75, 0)
    }
    # min_distance = float('inf')
    # nearest_color = None
    # for color, value in color_names.items():
    #     distance = np.sqrt(sum((np.array(rgb) - np.array(value)) ** 2))
    #     if distance < min_distance:
    #         min_distance = distance
    #         nearest_color = color
    # return nearest_color
    # calculates euclidean distance between RGB and every colormap entry and returns the color for shortest distance
    return min(color_names, key=lambda x: np.linalg.norm(np.array(rgb) - np.array(color_names[x]))) 

def save_image(image_array, original_path, filename):
    """Save the image to a 'processed' subdirectory within the original image directory."""
    # Determine the directory of the original image
    directory = os.path.dirname(original_path)
    
    # Create a 'processed' subdirectory if it doesn't already exist
    processed_dir = os.path.join(directory, 'processed')
    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir)
    
    # Construct the path for saving the processed image
    save_path = os.path.join(processed_dir, filename)
    
    # Convert the image array back to an image and save it
    processed_image = Image.fromarray((image_array * 255).astype(np.uint8))
    processed_image.save(save_path, 'JPEG')  # Saving as JPEG; change format if necessary
    
    print("Image saved to /{}", format(save_path))
    return save_path


def process_images_batch(batch_index, batch_size=16):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    yolov5_dir = os.path.join(current_dir, '../../yolov5')
    sys.path.append(yolov5_dir)
    model = torch.hub.load(yolov5_dir, 'custom', path=os.path.join(yolov5_dir, 'runs/train/exp2/weights/best.pt'), source='local')
    
    directory = "../../data/raw/preprocessed_images"
    image_paths = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".png") or f.endswith(".jpg")]
    processed_images = []

    start_index = batch_index * batch_size
    end_index = start_index + batch_size
    batch_paths = image_paths[start_index:end_index]
    images = load_images(batch_paths)
    results = detect_objects_batch(images, model)

    for img, result, path in zip(images, results.xyxy, batch_paths):
        if len(result) == 0:
            print("Skipping image /{} as it has no detections.", format(path))
            continue
        cropped_image = crop_image(img, result[0])
        if cropped_image:
            colors, complexity = get_dominant_colors_and_complexity(cropped_image)
            # if pd.isna(colors) or pd.isna(complexity):
            #     print("Skipping image /{} due to missing color or complexity data.", format(path))
            #     continue
            resized_and_normalized_image = resize_and_normalize(cropped_image)
            filename = '{}.jpg'.format(os.path.splitext(os.path.basename(path))[0])
            # save_image(resized_and_normalized_image, path, filename)
            processed_images.append((resized_and_normalized_image, filename, colors, complexity))

    if processed_images:
        save_to_firebase(processed_images)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python process_images_batch.py <batch_index>")
        sys.exit(1)
    batch_index = int(sys.argv[1])
    process_images_batch(batch_index)