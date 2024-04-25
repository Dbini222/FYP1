import os
import glob
import pandas as pd
import numpy as np
import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def get_list_of_image(directory_path):
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

def download_images(image_list, download_path):
    if not os.path.exists(download_path):
        os.makedirs(download_path)
    
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Referer': 'https://www.threadless.com/'
    }
    
    for i, image_url in enumerate(image_list):
        image_filename = f"image_{i}.jpg"
        image_filepath = os.path.join(download_path, image_filename)
        
        if os.path.isfile(image_filepath):
            print(f"Image already downloaded: {image_filename}")
            continue
        
        try:
            time.sleep(1)  # Sleep for 1 second between requests
            response = session.get(image_url, headers=headers, timeout=10)
            if response.status_code == 200:
                with open(image_filepath, 'wb') as f:
                    f.write(response.content)
                print(f"Downloaded and saved: {image_filename}")
            else:
                print(f"Failed to download image from {image_url}, status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to download image from {image_url}, error: {e}")

all_images = get_list_of_image('../../data/raw') #gotta change this as it won't work being tested
download_images(all_images, '../../data/raw/od_images')

