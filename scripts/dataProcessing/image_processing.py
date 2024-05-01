#Things to do in this file:
#get the images from the temporary file it's stored in, we are going to do this in batches
# crop the image based on the yolov5l detection 
# resize image to 1024x1024 pixels 
# normalise pixels 
#ensure images are all RGB
import torch
import os
import numpy as np
from sklearn.cluster import KMeans
from PIL import Image
import firebase_admin
from firebase_admin import credentials, firestore,storage

#Initialise firebase
cred = credentials.Certificate('../../fyp-project-83298-firebase-adminsdk-omga1-3c741ce672.json')
firebase_admin.initialize_app(cred, {
    'storageBucket': 'fyp-project-83298.appspot.com'
})
db = firestore.client()
bucket = storage.bucket()

def save_to_firebase(img, filename, metadata):
    """Saves an image to Firebase Storage at the root level and updates metadata in Firestore."""
    try:
        # Save image to a temporary file
        temp_path = f'/tmp/{filename}'
        img.save(temp_path, 'JPEG')

        # Upload to Firebase Storage at the root level
        blob = bucket.blob(filename)  # Changed from 'images/{filename}' to just '{filename}'
        blob.upload_from_filename(temp_path)
        
        # Get URL of the uploaded file
        url = blob.public_url
        
        # Clean up the temporary file
        os.remove(temp_path)
        
        # Document ID is the filename without the extension
        doc_id = os.path.splitext(filename)[0]

        # Update Firestore with the URL and additional metadata
        doc_ref = db.collection('products').document(doc_id)
        doc_ref.set({**metadata, 'image_stored': url})

        return url
    except Exception as e:
        print(f"Failed to save image to Firebase: {e}")


model = torch.hub.load('ultralytics/yolov5', 'custom', path='../../yolov5/runs/train/exp/weights/best.pt', force_reload=True) # change path to exp2 if you want yolov5l trained
def crop_image(img, detection):
    #checking it's not a plain t-shirt
    if detection is None:
        return None
    try:
        x1, y1, x2, y2 = map(int, detection[:4])
        center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
        box_size = int(max(x2 - x1, y2 - y1) * 1.2)
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
        print(f"Failed to crop image: {e}")
  

def get_dominant_colors_and_complexity(image, num_colors=10):
    #using k means clustering to determine dominant colours and complexity of an image
    image = image.resize((100, 100))  # as dominant color extraction is usually in smaller images
    data = np.reshape(np.array(image), (-1, 3))
    kmeans = KMeans(n_clusters=num_colors).fit(data)
    unique_labels = len(set(kmeans.labels_))
    complexity = 'simple' if unique_labels <= 2 else 'normal' if unique_labels <= 5 else 'complex'
    colors = kmeans.cluster_centers_
    return [find_nearest_color(color) for color in colors.astype(int)], complexity


def load_images(image_paths):
    try:
        images = [Image.open(p) for p in image_paths]
        images = [np.array(img)[:, :, ::-1] for img in images]
        return images
    except Exception as e:
        print(f"Failed to load images: {e}")

def detect_objects_batch(images, model):
    try:
        results = model(images)
        return results
    except Exception as e:
        print(f"Failed to detect objects: {e}")
        return None

def resize_and_normalize(img, size=(1024, 1024)):
    """Resize and normalize a single image."""
    if img is None:
        return None
    try:
        img = img.resize(size, Image.Resampling.LANCZOS)
        img_array = np.array(img) / 255.0
        #removing any transparency alpha channels 
        if img_array.shape[2] == 4:
            img_array = img_array[:, :, :3]
        return img_array
    except Exception as e:
        print(f"Failed to resize and normalize image: {e}")
        return None

def find_nearest_color(rgb):
    color_names = {
    "red": (255, 0, 0),
    "green": (0, 128, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "orange": (255, 165, 0),
    "purple": (128, 0, 128),
    "pink": (255, 192, 203),
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "gray": (128, 128, 128),
    "brown": (165, 42, 42),
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




def process_images_batch(directory, batch_size=32):
    image_paths = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".jpg")]
    for i in range(0, len(image_paths), batch_size):
        batch_paths = image_paths[i:i+batch_size]
        images = load_images(batch_paths)
        results = detect_objects_batch(images, model)

        for img, result, path in zip(images, results.xyxy[0], batch_paths):
            if len(result) == 0:
                continue  # Skip images with no detections i.e. plain t-shirts
            img_pil = Image.fromarray(img[:, :, ::-1])  # Convert BGR back to RGB and to PIL
            cropped_image = crop_image(img_pil, result[0])  # Crop the image based on the first detection
            if cropped_image:
                resized_and_normalized_image = resize_and_normalize(cropped_image)
                colors, complexity = get_dominant_colors_and_complexity(cropped_image)
                filename = f'{os.path.splitext(os.path.basename(path))[0]}.jpg'
                print(filename)
                # save_to_firebase(resized_and_normalized_image, os.path.basename(path), {'colors': colors, 'complexity': complexity})
            else:
                print(f"Skipping image {path} as it has no detections.")





# Example usage
process_images_batch('../../data/raw/preprocessed_images', batch_size=32)