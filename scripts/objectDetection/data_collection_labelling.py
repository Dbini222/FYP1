import os
import glob
import pandas as pd
import numpy as np
import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import random

# List of user agents to rotate
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Mobile Safari/537.36',
]

def get_list_of_images(directory_path):
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

def download_image(url, download_path, index, attempt=1):
    if attempt > 5:  # Limit the number of attempts to avoid infinite loops
        print("Max retries exceeded.")
        return

    if not os.path.exists(download_path):
        os.makedirs(download_path)

    image_filename = f"image_{index}.jpg"  # Sequential filename
    full_path = os.path.join(download_path, image_filename)
    
    session = requests.Session()
    session.headers.update({'User-Agent': random.choice(user_agents)})

    try:
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            with open(full_path, 'wb') as f:
                f.write(response.content)
            print(f"Download successful: {full_path}")
        elif response.status_code == 403:
            print(f"Attempt {attempt}: 403 error received, retrying with new user-agent...")
            time.sleep(3)  # Wait a bit before retrying
            download_image(url, download_path, index, attempt + 1)
        else:
            print(f"Failed to download image: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")

all_images = get_list_of_images('../../data/raw') # Adjust path as needed
for idx, image_url in enumerate(all_images, start=1):
    download_image(image_url, '../../data/raw/od_images', idx)
