import os
import glob
import pandas as pd
import numpy as np
import requests
import labelImg
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# collect 500 images, label the design and use  pretrained model YOLO
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

def collect_images(directory_path):
    # from each csv in directory except teefury.csv, get 100 random images using the image url
    #create directory in data/raw called od_images

    csv_files = glob.glob(os.path.join(directory_path, '*.csv'))
    all_images = []
    for file in csv_files:
        if 'teefury' in file:
            continue
        df = pd.read_csv(file)
        images = df['images'].tolist()
        # get 100 random images
        np.random.shuffle(images)
        all_images.extend(images[:100])

    return all_images

all_images = collect_images('../../data/raw') #gotta change this as it won't work being tested
download_images(all_images, '../../data/raw/od_images')

