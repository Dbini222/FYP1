import scrapy 


class AmazonSpider(scrapy.Spider):
    name = "amazon"
    start_urls = [
        "https://www.amazon.co.uk/Best-Sellers-Fashion-Mens-T-Shirts/zgbs/fashion/1731028031/ref=zg_bs_pg_1_fashion?_encoding=UTF8&pg=1" 
        ]
    baseURL = 'https://www.amazon.co.uk'

    def parse(self, response):
        for product in response.css('div.a-cardui._cDEzb_grid-cell_1uMOS.expandableGrid.p13n-grid-content'):
            try:
                yield {
                    'product_id':  product.css('div.p13n-sc-uncoverable-faceout').attrib['id'],
                    'images': product.css('img.a-dynamic-image.p13n-sc-dynamic-image.p13n-product-image::attr(src)').get(),
                    'description': product.css('div._cDEzb_p13n-sc-css-line-clamp-3_g3dy1::text').get(),
                    'shop': None,
                    'website': 'amazon',
                    'popularity': int(product.css('span.zg-bdg-text::text').get().replace("#","")),
                    }
        
            except Exception as e:
                    print('Error: ', e)
                
        next_page = self.baseURL + response.css('li.a-last a').attrib['href']
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)

    
