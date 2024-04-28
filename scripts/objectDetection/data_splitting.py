import os
import shutil
import numpy as np

# Set your dataset directory and target directories for train and validation
data_dir = '../../data/raw/od_images'
train_dir = '../../data/raw/od_images/training'
valid_dir = '../../data/raw/od_images/validation'

# Create train and validation directories if they don't exist
os.makedirs(train_dir, exist_ok=True)
os.makedirs(valid_dir, exist_ok=True)

# Get all image filenames
all_images = [os.path.join(data_dir, fname) for fname in os.listdir(data_dir) if fname.endswith('.jpg')]
np.random.shuffle(all_images)  # Shuffle the data

# Split the dataset
train_images = all_images[:397]
valid_images = all_images[397:]

# Function to copy images and their corresponding XML files to a target directory
def copy_files(image_list, target_dir):
    for img_path in image_list:
        shutil.copy(img_path, target_dir)  # Copy the image
        xml_path = img_path.replace('.jpg', '.xml')  # Get the corresponding XML file path
        shutil.copy(xml_path, target_dir)  # Copy the XML file

# Copy images to respective directories
copy_files(train_images, train_dir)
copy_files(valid_images, valid_dir)
