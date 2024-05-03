#Things to do in this file:
#get the images from the temporary file it's stored in, we are going to do this in batches
# crop the image based on the yolov5l detection 
# resize image to 1024x1024 pixels 
# normalise pixels 
#ensure images are all RGB
import torch
import os
import numpy as np
from collections import OrderedDict
from sklearn.cluster import KMeans
from PIL import Image
from torchvision import transforms
import firebase_admin
from firebase_admin import credentials, firestore,storage

#Initialise firebase]
cred = credentials.Certificate('../../fyp-project-83298-firebase-adminsdk-omga1-3c741ce672.json')
firebase_admin.initialize_app(cred, {
    'storageBucket': 'fyp-project-83298.appspot.com'
})
db = firestore.client()
bucket = storage.bucket()

def save_to_firebase(image_array, filename, metadata):
    """Saves an image to Firebase Storage at the root level and updates metadata in Firestore."""
    try:
        # Save image to a temporary file
        temp_path = f'/tmp/{filename}'
        processed_image = Image.fromarray((image_array * 255).astype(np.uint8))
        processed_image.save(temp_path, 'JPEG')

        # Upload to Firebase Storage at the root level
        blob = bucket.blob(f'images/{filename}')  # Changed from 'images/{filename}' to just '{filename}'
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
        print(f"Failed to crop image: {e}")
  

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

# Load images from a list of file paths as a list of PIL images
def load_images(image_paths):
    try:
        images = [Image.open(p).convert('RGB') for p in image_paths]  # Ensuring RGB and no alpha channels
        return images
    except Exception as e:
        print(f"Failed to load images: {e}")

model = torch.hub.load('ultralytics/yolov5', 'custom', path='../../yolov5/runs/train/exp/weights/best.pt', force_reload=True) # change path to exp2 if you want yolov5l trained
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
        img = img.resize(size, Image.Resampling.LANCZOS) # Resize image to 1024x1024 pixels, make it smaller if GPU not available
        img_array = np.array(img) / 255.0
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
    
    print(f"Image saved to {save_path}")
    return save_path

def save_debug_image(image_array, file_path):
    # img = Image.fromarray(image_array)
    image_array.save(file_path, format='JPEG')

def process_images_batch(directory, batch_size=32):
    image_paths = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".jpg")]
    # Process images in batches
    for i in range(0, len(image_paths), batch_size):
        batch_paths = image_paths[i:i+batch_size]
        images = load_images(batch_paths)  # Load images as PIL images and return list of images
        results = detect_objects_batch(images, model) # correctly detecting images (use results.show() if needed)
        for img, result, path in zip(images, results.xyxy, batch_paths):
            if len(result) == 0:
                print(f"Skipping image {path} as it has no detections.")
                continue  # Skip images with no detections i.e. plain t-shirts
            cropped_image = crop_image(img, result[0])  # Crop the image based on the first detection
            if cropped_image:
                colors, complexity = get_dominant_colors_and_complexity(cropped_image)
                resized_and_normalized_image = resize_and_normalize(cropped_image)
                # print(f"Colors: {colors}, Complexity: {complexity}", path)
                filename = f'{os.path.splitext(os.path.basename(path))[0]}.jpg'
                print(filename)
                # save_image(resized_and_normalized_image, path, filename) #for testing to see what the image looks like
                save_to_firebase(resized_and_normalized_image, os.path.basename(path), {'colors': colors, 'complexity': complexity})

  

# process_images_batch('../../data/downloaded_images', batch_size=32)