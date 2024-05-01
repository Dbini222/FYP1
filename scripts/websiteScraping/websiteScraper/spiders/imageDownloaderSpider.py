import scrapy
import glob
import os
import pandas as pd
import numpy as np
from scrapy.http import Request

#Script for image downloading, can be used to download a certain amount or all. Created to download images for object detection training
class ImageDownloaderSpider(scrapy.Spider):
    name = 'image_downloader'

    def __init__(self, *args, **kwargs):
        super(ImageDownloaderSpider, self).__init__(*args, **kwargs)
        self.image_counter = 1  # Initialize the image counter at 1

    def start_requests(self):
        directory_path = "../../data/raw"  # Changed to relative path from project root
        csv_files = glob.glob(os.path.join(directory_path, '*.csv'))
        self.logger.info("CSV files found: " + str(csv_files))
        
        for file in csv_files:
            if 'teefury' in file:
                continue
            df = pd.read_csv(file)
            images = df['images'].tolist()
            np.random.shuffle(images)  # Shuffle to randomize selection
            selected_images = images[:100]  # Select the first 100 random images
            for url in selected_images:
                yield Request(url, self.parse_img)

    def parse_img(self, response):
        directory = "../../data/raw/od_images"  # Define the directory for saved images
        if not os.path.exists(directory):
            os.makedirs(directory)  # Ensure the directory exists

        # Build the file path using the image counter for naming
        file_path = os.path.join(directory, f'image{self.image_counter}.jpg')
        self.image_counter += 1  # Increment the counter after each image

        # Save the image to the defined file path
        with open(file_path, 'wb') as f:
            f.write(response.body)
        self.log(f'Saved file {file_path}')
