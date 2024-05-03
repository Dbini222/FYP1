import os
import shutil
import numpy as np
import xml.etree.ElementTree as ET
import os
from os import listdir, getcwd
from os.path import join

# #Converting xml to txt for YOLOv5
# def convert(size, box):
#     dw = 1. / size[0]
#     dh = 1. / size[1]
#     x = (box[0] + box[1]) / 2.0
#     y = (box[2] + box[3]) / 2.0
#     w = box[1] - box[0]
#     h = box[3] - box[2]
#     x = x * dw
#     w = w * dw
#     y = y * dh
#     h = h * dh
#     return (x, y, w, h)

# def convert_annotation(xml_file):
#     """ Convert annotations in a single XML file to YOLO format """
#     in_file = open(xml_file)
#     out_file_path = join(data_dir, os.path.splitext(os.path.basename(xml_file))[0] + '.txt')
#     out_file = open(out_file_path, 'w')
#     tree = ET.parse(in_file)
#     root = tree.getroot()
#     size = root.find('size')
#     w = int(size.find('width').text)
#     h = int(size.find('height').text)

#     for obj in root.iter('object'):
#         difficult = obj.find('difficult').text
#         cls = obj.find('name').text
#         if int(difficult) == 1:
#             continue
#         xmlbox = obj.find('bndbox')
#         b = (float(xmlbox.find('xmin').text), float(xmlbox.find('xmax').text),
#              float(xmlbox.find('ymin').text), float(xmlbox.find('ymax').text))
#         bb = convert((w, h), b)
#         out_file.write(f"0 {bb[0]} {bb[1]} {bb[2]} {bb[3]}\n")  # Assuming '0' is the class id for all objects

#     in_file.close()
#     out_file.close()

# # Process all XML files in the folder
# files = [f for f in listdir(data_dir) if f.endswith('.xml')]
# for file in files:
#     convert_annotation(join(data_dir, file))

# print("Conversion completed. Outputs are in:", data_dir)

#Splitting data into valid and training 
# Set your dataset directory and target directories for train and validation
import os
import shutil
import numpy as np

# Base directory where the images and labels are located
data_dir = '../../data/raw/od_images/presplit_data'

# Target directories for the split datasets
train_dir = '../../data/raw/od_images/training'
valid_dir = '../../data/raw/od_images/validation'

# Ensure target directories exist
os.makedirs(os.path.join(train_dir, 'images'), exist_ok=True)
os.makedirs(os.path.join(train_dir, 'labels'), exist_ok=True)
os.makedirs(os.path.join(valid_dir, 'images'), exist_ok=True)
os.makedirs(os.path.join(valid_dir, 'labels'), exist_ok=True)

# Function to copy files to their respective directories
def copy_files(files, target_dir):
    for file in files:
        img_path = os.path.join(data_dir, file)
        txt_path = img_path.replace('.jpg', '.txt')  # Adjust if necessary to find the correct .txt files

        # Copy image
        shutil.copy(img_path, os.path.join(target_dir, 'images', file))

        # Check and copy corresponding label file
        if os.path.exists(txt_path):
            shutil.copy(txt_path, os.path.join(target_dir, 'labels', file.replace('.jpg', '.txt')))
        else:
            print(f"Warning: No label file found for {img_path}")

# List all jpg files in the directory
all_images = [f for f in os.listdir(data_dir) if f.endswith('.jpg')]
np.random.shuffle(all_images)  # Shuffle the dataset

# Determine split point for training and validation sets (80% training, 20% validation)
split_index = int(len(all_images) * 0.8)

# Copy files to the respective training and validation directories
copy_files(all_images[:split_index], train_dir)  # Training data
copy_files(all_images[split_index:], valid_dir)  # Validation data

print("Dataset successfully split into training and validation sets.")
