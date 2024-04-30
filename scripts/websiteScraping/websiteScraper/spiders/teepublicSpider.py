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
            self.overall_position += 1
            if self.overall_position > self.custom_settings['CLOSESPIDER_ITEMCOUNT']:
                    raise scrapy.exceptions.CloseSpider('reached maximum item count')
            product_id = product.attrib['data-design-id'],
            product_image = product.attrib['data-image-url']
            product_description = product.attrib['data-gtm-design-title']
            product_shop = product.attrib['data-gtm-designer-name']
        
            try:
                yield {
                    'product_id': product_id,
                    'images': product_image,
                    'description':  product_description,
                    'shop': product_shop,
                    'website': self.name,
                    'popularity': self.overall_position,
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
                

