# https://www.teepublic.com/t-shirts
import scrapy 


class TeepublicSpider(scrapy.Spider):
    name = "teepublic"
    start_urls = [
        'https://www.teepublic.com/t-shirts?safe_search=false',
    ]
    baseURL = 'https://www.teepublic.com'
    overall_position = 0
    
    custom_settings = {
        'CLOSESPIDER_ITEMCOUNT': 2500 # scrape 2500 items as index starts at 0
    }

    def parse(self, response):
        for product in response.css('div.m-tiles__tile.jsDesignContainer'):
            if product is None or product == []:
                print('No products found, refer back to website incase they have changed their structure')
                break
            self.overall_position += 1
            if self.overall_position > self.custom_settings['CLOSESPIDER_ITEMCOUNT']:
                    raise scrapy.exceptions.CloseSpider('reached maximum item count')
            product_id = product.attrib['data-design-id'],
            product_image = product.attrib['data-image-url']
            product_description = product.attrib['data-gtm-design-title']
            product_shop = product.attrib['data-gtm-designer-name']
        
            try:
                if product_id and product_image and product_description is not None:
                    # highest_resolution_image = self.get_highest_resolution(product_image)
                    yield {
                        'product_id': product_id,
                        'images': product_image,
                        'description':  product_description,
                        'shop': product_shop,
                        'website': self.name,
                        'popularity': self.overall_position,
                        'age': self.age,
                        }
        
            except Exception as e:
                print('Error: ', e)
                    # yield {
                    #     'product_id': None,
                    #     'images': None,
                    #     'description': None,
                    #     'shop': None,
                    #     'website': None,
                    #     'popularity':None,
                    #     }
        try:
            next_page = response.css('a[rel="next"]::attr(href)').get()
            if next_page is not None:
                yield response.follow(self.baseURL + next_page, callback=self.parse)
        except Exception as e:
            print('Error: ', e)
            # log.msg(f'Error: {e}', level=log.ERROR)

#they don't control the resolution through the URL
# def get_highest_resolution(self, image_url):
#         resolutions = ['4000x', '3000x', '2000x', '1000x']  # Common resolutions to try
#         for resolution in resolutions:
#             new_url = image_url.replace("300x", resolution)
#             if self.url_exists(new_url):
#                 return new_url
#         # If none of the modified URLs work, return the original one
#         return image_url

# def url_exists(self, url):
#     request = scrapy.Request(url, method='HEAD')
#     response = self.crawler.engine.download(request, self)
#     return response.status == 200

