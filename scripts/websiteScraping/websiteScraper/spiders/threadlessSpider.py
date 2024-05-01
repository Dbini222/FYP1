import scrapy 
import json

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
                try:
                    yield {
                        'product_id': data["id"],
                        'images': product.css('img.img-responsive::attr(data-src)').extract_first(),
                        'description': data["name"],
                        'shop': product.css('a.sf-by-line.pjax-link::text').get(),
                        'website': self.name,
                        'popularity': self.overall_position + int(data["position"]),
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
