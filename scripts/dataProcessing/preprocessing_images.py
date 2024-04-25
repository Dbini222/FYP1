import pandas as pd
import numpy as np
import cv2
import glob
import os
import requests
import matplotlib.pyplot as plt
from PIL import Image, ImageOps
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def get_list_of_image(directory_path):
    # for each csv, get the first 10 images and add to a list
    csv_files = glob.glob(os.path.join(directory_path, '*.csv'))
    all_images = []
    for file in csv_files:
        df = pd.read_csv(file)
        images = df['images'].tolist()
        all_images.extend(images[:10])
    return all_images

def download_images(image_list, download_path):
    if not os.path.exists(download_path):
        os.makedirs(download_path)
    
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    
    for i, image_url in enumerate(image_list):
        image_filename = f"image_{i}.jpg"
        image_filepath = os.path.join(download_path, image_filename)
        
        if os.path.isfile(image_filepath):
            print(f"Image already downloaded: {image_filename}")
            continue
        
        try:
            response = session.get(image_url, headers=headers, timeout=10)
            if response.status_code == 200:
                with open(image_filepath, 'wb') as f:
                    f.write(response.content)
                print(f"Downloaded and saved: {image_filename}")
            else:
                print(f"Failed to download image from {image_url}, status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to download image from {image_url}, error: {e}")

def crop_design(img):
    # Convert the PIL image to a NumPy array for OpenCV processing
    img = img.convert('RGB')
    open_cv_image = np.array(img)
    # Convert RGB to BGR for OpenCV
    open_cv_image = open_cv_image[:, :, ::-1]

    # Convert the image to grayscale
    gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)

    # Apply a threshold to get a binary image
    _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Assuming that the largest contour is the T-shirt design
    max_contour = max(contours, key=cv2.contourArea)

    # Get the bounding box of the largest contour
    x, y, w, h = cv2.boundingRect(max_contour)

    # Crop the image using the bounding box
    cropped_img = open_cv_image[y:y+h, x:x+w]

    # Convert the cropped image back to a PIL image
    pil_cropped_img = Image.fromarray(cropped_img[:, :, ::-1])  # Convert BGR back to RGB

    return pil_cropped_img

def preprocess_images(image_dir, processed_image_dir):
    # Ensure the processed image directory exists
    if not os.path.exists(processed_image_dir):
        os.makedirs(processed_image_dir)
    
    originals = []
    processed = []
    cropped = []

    # Preprocess the images in the image_dir
    for image_filename in os.listdir(image_dir):
        if image_filename.endswith(".jpg"):
            image_path = os.path.join(image_dir, image_filename)
            img = Image.open(image_path)

            # Crop the design from the image
            try: 
                img_cropped = crop_design(img)
                cropped_path = os.path.join(processed_image_dir, "cropped_" + image_filename)
                img_cropped.save(cropped_path)
                cropped.append(cropped_path)  # Append the file path
            except Exception as e:
                print(f"Failed to crop image {image_filename}: {e}")
                continue
            
            # Perform preprocessing: resizing and converting to RGB
            processed_img = img.resize((1024, 1024), Image.Resampling.LANCZOS)
            processed_img = processed_img.convert('RGB')
            
            # Save the preprocessed image to the new directory
            processed_path = os.path.join(processed_image_dir, image_filename)
            processed_img.save(processed_path)
            
            # Append paths for display
            originals.append(image_path)
            processed.append(processed_path)

    return originals, cropped, processed  # Return lists of file paths

def display_images(original_paths, cropped_paths, processed_paths):
    assert len(original_paths) == len(cropped_paths) == len(processed_paths), "The number of original, cropped, and processed images must match."

    num_images = len(original_paths)
    
    for i in range(num_images):
        # Create a new figure for each set of images
        plt.figure(figsize=(15, 5))  # Adjusted figure size

        # Load original image
        original_img = Image.open(original_paths[i])
        plt.subplot(1, 3, 1)  # First of three columns
        plt.imshow(original_img)
        plt.title("Original")
        plt.axis('off')

        # Load cropped image
        cropped_img = Image.open(cropped_paths[i])
        plt.subplot(1, 3, 2)  # Second of three columns
        plt.imshow(cropped_img)
        plt.title("Cropped")
        plt.axis('off')

        # Load processed image
        processed_img = Image.open(processed_paths[i])
        plt.subplot(1, 3, 3)  # Third of three columns
        plt.imshow(processed_img)
        plt.title("Processed")
        plt.axis('off')
        
        # Show the plot
        plt.tight_layout()
        plt.show()



directory_path = '../../data/raw'
download_path = '../../data/downloaded_images'
processed_image_dir = '../../data/processed/processed_images'
image_list = get_list_of_image(directory_path)
# download_images(image_list, download_path)
originals, processed, cropped = preprocess_images(download_path, processed_image_dir)
display_images(originals, processed, cropped)




