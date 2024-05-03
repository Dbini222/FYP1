import scrapy
import firebase_admin
from firebase_admin import credentials, firestore
from scrapy.http import Request
import os

class ImageDownloaderSpider(scrapy.Spider):
    name = 'image_downloader'

    def __init__(self, *args, **kwargs):
        super(ImageDownloaderSpider, self).__init__(*args, **kwargs)
        self.init_firebase()
        self.image_data = self.fetch_image_data()

    def init_firebase(self):
        cred_path = '../../fyp-project-83298-firebase-adminsdk-omga1-3c741ce672.json'
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    def fetch_image_data(self):
        """Fetching image URLs and document IDs from Firestore where 'is_new' is true."""
        image_data = []
        try:
            docs = self.db.collection('products').where('is_new', '==', True).stream()
            for doc in docs:
                data = doc.to_dict()
                if 'images' in data:
                    image_data.append({'url': data['images'], 'doc_id': doc.id})
        except Exception as e:
            self.logger.error(f"Failed to fetch image data: {e}")
        return image_data

    def start_requests(self):
        for data in self.image_data:
            yield Request(data['url'], self.parse_img, meta={'doc_id': data['doc_id']})

    def parse_img(self, response):
        directory = "../../data/raw/preprocessed_images"  # Define the directory for saved images
        if not os.path.exists(directory):
            os.makedirs(directory)

        doc_id = response.meta['doc_id']
        file_path = os.path.join(directory, f"{doc_id}.png")

        with open(file_path, 'wb') as f:
            f.write(response.body)
        self.log(f'Saved file {file_path}')
