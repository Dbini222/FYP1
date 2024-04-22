import scrapy
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class AliexpressSpider(scrapy.Spider):
    name = "aliexpress"
    start_urls = [
        'https://www.aliexpress.com/w/wholesale-Men-t-shirts.html?g=y&SearchText=Men+t+shirts&sortType=total_tranpro_desc'
        ]
    baseURL = 'https://www.aliexpress.com'
    age = 0
    overall_position = 0
    custom_settings = {
        'CLOSESPIDER_ITEMCOUNT': 2501 # scrape 2500 items as index starts at 0
    }

    def __init__(self):
        # self.path = "/Users/danib/FYP/env/chromedriver"
        # service = Service(self.path)
        self.driver = webdriver.Chrome() # Set the path to your chromedriver executable
        self.name = "aliexpress"

    def parse(self, response):
        self.driver.get(response.url)
        time.sleep(15)
        for product in response.css('div.multi--outWrapper--SeJ8lrF.card--out-wrapper'):
            try:
                self.overall_position += 1
                url = product.css('a.multi--container--1UZxxHY.cards--card--3PJxwBm.search-card-item::attr(href)').get()
                last_slash_index = url.rfind('/')
                html_extension_index = url.find('.html')
                value = url[last_slash_index + 1:html_extension_index]
                image = product.css('img.images--item--3XZa6xf::attr(src)').get()
                if self.overall_position >= self.custom_settings['CLOSESPIDER_ITEMCOUNT']:
                    raise scrapy.exceptions.CloseSpider('reached maximum item count')
                elif value is not None and image is not None:
                    yield {
                        'product_id': value,
                        'images': 'http:' + image,
                        'description': product.css('div.multi--title--G7dOCj3::attr(title)').get() ,
                        'shop': product.css('span.cards--store--3GyJcot::text').get(),
                        'website': self.name,
                        'popularity': self.overall_position,
                        'age': self.age,
                        }
                else:
                    continue
            
            except Exception as e:
                    print('Error: ', e)
        
        while True:
            next = self.driver.find_element(By.CSS_SELECTOR, 'button[class="comet-pagination-item-link"]')
            try:
                next.click()
                AliexpressSpider.parse(self, response)
                # get the data and write it to scrapy items
            except Exception as e:
                print(e)

        self.driver.close()
        
        