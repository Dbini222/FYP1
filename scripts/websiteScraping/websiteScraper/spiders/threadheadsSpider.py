# https://threadheads.co.uk/collections/shirts?filter.p.product_type=T-Shirt
# 1600 items
import scrapy 


class ThreadheadsSpider(scrapy.Spider):
    name = "threadheads"
    start_urls = [
        'https://threadheads.co.uk/collections/shirts?filter.p.product_type=T-Shirt',
    ]
    baseURL = 'https://threadheads.co.uk'
    age = 0
    overall_position = 0
    
    custom_settings = {
        'CLOSESPIDER_ITEMCOUNT': 2500 # scrape 2500 items as index starts at 0
    }

    def parse(self, response):
        for product in response.css('div.product-item-box.price-highlight.old-price-highlight'):
            self.overall_position += 1
            if self.overall_position > self.custom_settings['CLOSESPIDER_ITEMCOUNT']:
                raise scrapy.exceptions.CloseSpider('reached maximum item count')
            title_href = product.css('a.product-title::attr(href)').extract_first()
            product_id = title_href.split('p')[-1] #if 'p' in title_href else None
            product_image = product.css('a.product-link img::attr(src)').extract_first()
            product_description = product.css('h2.product-title::text').extract_first()
            product_shop = product.css('a.product-category-link::text').extract_first()
        
            try:
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
                    #     'age': None,
                    #     }

        next_page = response.css('a.pagination_item.group').attrib['href']
        if next_page is not None:
            yield response.follow(self.baseURL + next_page, callback=self.parse)

