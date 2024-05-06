import scrapy 
import json
import re
#Fix this so that it doesn't have to do popularity like that, instead make it a counter which is more reliable like the other code
class ThreadlessSpider(scrapy.Spider):
    name = "threadless"
    start_urls = [
        'https://www.threadless.com/search?shop=threadless&sort=popular&departments=mens&style=t-shirt',
    ]
    baseURL = 'https://www.threadless.com'
    overall_position = 0
    
    custom_settings = {
        'CLOSESPIDER_ITEMCOUNT': 2501 # scrape 2500 items as index starts at 0
    }

    def parse(self, response):
        for product in response.css('div.media-card'):
            if product is None or product == []:
                print('No products found, refer back to website incase they have changed their structure')
                break
            data = json.loads(product.css('a.pjax-link.media-image.discover-as-product-linkback-mc').attrib['data-ec-trigger'])
            if self.overall_position + int(data["position"]) >= self.custom_settings['CLOSESPIDER_ITEMCOUNT']:
                    raise scrapy.exceptions.CloseSpider('reached maximum item count')
            else:
                product_id = data["id"]
                image = product.css('img.img-responsive::attr(data-src)').extract_first()
                description = data["name"]
                shop = product.css('a.sf-by-line.pjax-link::text').get()
                popularity = self.overall_position + int(data["position"])
                try:
                    if product_id and image and description is not None:
                        highest_resolution_image = self.get_highest_resolution(image)
                        yield {
                            'product_id': product_id,
                            'images': highest_resolution_image,
                            'description': description,
                            'shop': shop,
                            'website': self.name,
                            'popularity': popularity,
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
                    #     'age': None,
                    #     }

        self.overall_position += int(data["position"])
        next_page = self.baseURL + response.css('a[aria-label="Next"].pjax-link').attrib['href']
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)


    def get_highest_resolution(self, image_url):
        pattern = re.compile(r"v=\d+&d")
        new_url = pattern.sub("v=4000&d", image_url)
        return new_url

    # def url_exists(self, url):
    #     request = scrapy.Request(url, method='HEAD')
    #     response = self.crawler.engine.download(request, self)
    #     return response.status == 200


