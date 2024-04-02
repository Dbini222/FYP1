# This doesn't get the date of which the images were created, which is important. 
# But what you could do is just give those added to the database later higher rewards, so initially, it doesnt change anything
import os
import random
import httpx
import json
import re
import asyncio
import math
import jmespath
from parsel import Selector
from typing import Dict, List
from fake_useragent import UserAgent

# Make a class which abstracts this and has the requirements for what each website has to give you, and then the methods for which they get them, but each can be define separately depending on the website
# https://scrapfly.io/blog/how-to-scrape-aliexpress/
# Because Aliexpress uses Javascript to dynamically render the page, we have to use hidden web data scraping

class AliexpressScraper():
    BASE_URL = "https://www.aliexpress.com"
    def __init__(self):
        super().__init__()
        self.data = None
        self.product_data = None
        self.product_ids = None
        self.images = None
        self.user_agent = UserAgent()
        self.session = httpx.AsyncClient(headers=self.get_base_headers(), follow_redirects=True)
    
    def get_base_headers(self):
        return {
            "user-agent": self.user_agent.random,
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "accept-language": "en-US;en;q=0.9",
            "accept-encoding": "gzip, deflate, br",
        }
    # Extracts the data from the script tag
    async def get_data(self, response) -> Dict:
        # Send a GET request to the URL
        sel = Selector(text=response.text)
        # find the script tag that contains the data
        script_with_data = sel.xpath('//script[contains(.,"_init_data_=")]')
        # Extract the data from the script tag
        data= json.loads(script_with_data.re(r'_init_data_\s*=\s*{\s*data:\s*({.+}) }')[0])
        return data['data']['root']['fields']
    
    # Extracts the product ids from a single search page, and returns as a list
    async def get_product_id(self, response) -> List[Dict]:
        data = await self.get_data(response)
        # print(data)
        parsed = []
        for product in data["mods"]["itemList"]["content"]:
            # print(product)
            # print("\n")
            # print("\n")
            parsed.append({"id": product["productId"]})

        # print(parsed)
        return parsed
    
    # Parses the product HTML page for product data
    async def parse_product(self, response) ->Dict:
        print("Everything is working\n")
        print(response.text)
        # The below isn't working because they suspect suspicious activity, it gives that page
        sel = Selector(text=response.text)
        script_with_data = sel.xpath('//script[contains(text(),"window.runParams")]/text()').get()
        print("parsing product\n")
        print(script_with_data) #this is returning NONE for some reason 
        data = re.findall(r".+?data:\s*({.+?)};", script_with_data, re.DOTALL)
        data = json.loads(data[0])

        if "skuModule" not in data:
            product = {
                "name": data.get("productInfoComponent", {}).get("idStr"),
                "total_orders": data.get("tradeComponent", {}).get("formatTradeCount"),
                "feedback": {
                    "rating": data.get("feedbackComponent", {}).get("evarageStar"),
                    "count": data.get("feedbackComponent", {}).get("totalValidNum"),
                },
                "images": data.get("imageComponent", {}).get("imagePathList", []),
            }
        else:
            product = {
                "name": data.get("titleModule", {}).get("subject"),
                "total_orders": data.get("titleModule", {}).get("formatTradeCount"),
                "feedback": {
                    "rating": data.get("titleModule", {}).get("feedbackRating", {}).get("evarageStar"),
                    "count": data.get("titleModule", {}).get("feedbackRating", {}).get("totalValidNum"),
                },
                "images": data.get("imageModule", {}).get("imagePathList", []),
            }

        product['specification'] = dict([v.values() for v in product.get('specification', {})])
        return product
   
#   Scrape product details for the given product ids
    async def scrape_products(self, ids) -> List[Dict]:
        responses = await asyncio.gather(*[self.session.get(f"{self.BASE_URL}/item/{id_}.html") for id_ in ids])
        results = []
        for response in responses:
            results.append(await self.parse_product(response))
            await asyncio.sleep(random.uniform(1, 3)) # Random delay between requests
        return results
    # Scrape Aliexpress for product details, returns a list of product data
    async def scrape(self, sort_type="total_tranpro_desc", max_pages: int = None) -> List[Dict]:
        async def page_response(page):
            resp = await self.session.get(f"{self.BASE_URL}/w/wholesale-men-t-shirts.html?g=y&SearchText=men+t+shirts&sortType={sort_type}&page={page}")
            return resp
        
        async def get_all_product_ids():
            product_ids = []
            first_page = await page_response(1)
            first_page_data = await self.get_data(first_page)
            try:
                total_results = first_page_data["pageInfo"]["totalResults"]
                page_size = first_page_data["pageInfo"]["pageSize"]
                total_pages = min(60, max_pages or math.ceil(total_results / page_size))
            except KeyError as e:
                print(f"KeyError: {e}. 'pageInfo' not found in response: {first_page_data}")
                total_pages = 50 # Set a default value for total_pages

            for page in range(1, total_pages + 1):
                search_page = await page_response(page)
                product_ids.extend(await self.get_product_id(search_page))
                await asyncio.sleep(random.uniform(1, 3))  # Random delay between requests


            return [product['id'] for product in product_ids]
        
        product_previews = await get_all_product_ids()
        product_details = await self.scrape_products(product_previews)

        # Organize data into the desired structure
        data_to_store = {}
        for index, product in enumerate(product_details):
            product_id = product['id']
            data_to_store[product_id] = {
                'rank': index,
                'images': product.get('images', []),
                'relevancy': 1,  # Initially set to 1
                'total_orders': product.get('total_orders', 0)
            }

        # Save data to a JSON file
        output_folder = 'output'  # Specify the folder to store the JSON file
        os.makedirs(output_folder, exist_ok=True)  # Create the output folder if it doesn't exist
        output_file = os.path.join(output_folder, 'aliexpress.json')

        with open(output_file, 'w') as f:
            json.dump(data_to_store, f, indent=2)
        return product_details

    async def run(self):
        data = await self.scrape(max_pages=3)
        print(json.dumps(data, indent=2, ensure_ascii=False))

    # Close HTTP session
    async def close_session(self):
        await self.session.aclose()

    



# def get_data(response) -> Dict:
#     # Send a GET request to the URL
#     sel = Selector(text=response.text)
#     # find the script tag that contains the data
#     script_with_data = sel.xpath('//script[contains(.,"_init_data_=")]')
#     # Extract the data from the script tag
#     data= json.loads(script_with_data.re(r'_init_data_\s*=\s*{\s*data:\s*({.+}) }')[0])
#     return data['data']['root']['fields']

# # retrives the product_ids from a single search page, and returns as a list
# def get_product_id(reponse):
#     # parse search page response for product preview results
#     data = get_data(reponse)
#     parsed = []
#     # print(data)
#     for product in data["mods"]["itemList"]["content"]:
#         parsed.append(
#             {
#                 "id": product["productId"],
#                 # "url": f"https://www.aliexpress.com/item/{product['productId']}.html",
#                 # "type": product["productType"],  # can be either natural or ad
#                 # "title": product["title"]["displayTitle"],
#                 # "price": product["prices"]["salePrice"]["minPrice"],
#                 # "currency": product["prices"]["salePrice"]["currencyCode"],
#                 # trade represents how many sold
#                 # "trade": product.get("trade", {}).get("tradeDesc"),  # trade line is not always present
#                 # "thumbnail": product["image"]["imgUrl"].lstrip("/"),
#                 # "rating": product["evaluation"]["starRating"],
#                 # "review_count": product["feedbackRating"]["totalValidNum"],
#                 # "date": product["publishTime"],
#             })
#         return parsed

# # retrieves a list of a list of product ids, each list corresponds to a search page, and returns as a list of a list. length of the list is the number of pages 
# async def scrape_aliexpress(session: httpx.AsyncClient, sort_type="total_tranpro_desc", max_pages: int = None):
#     # get all the search results of a specific page in for men's t-shirts
#     async def page_response(page):
#         # print(f"scraping search query mens t-shirt:{page} sorted by {sort_type}")
#         resp = await session.get(
#         "https://www.aliexpress.com/w/wholesale-men-t-shirts.html?g=y&SearchText=men+t+shirts&sortType=total_tranpro_desc&page={page}"
#         )
#         return resp
#     # get all product IDs from search results
#     async def get_all_product_ids():
#         product_ids = []
#         first_page = await page_response(1)
#         first_page_data = get_data(first_page)
#         total_pages = min(60, max_pages or math.ceil(first_page_data["pageInfo"]["totalResults"] / first_page_data["pageInfo"]["pageSize"]))

#         for page in range(1, total_pages + 1):
#             search_page = await page_response(page)
#             product_ids.extend(get_product_id(search_page))

#         return product_ids
    
#     # get product detals for each product ID
#     async def get_product_details(product_ids):
#         return await scrape_products(product_ids, session)
    
#     # scrape first search page and find total result count
#     first_page = await page_response(1)
#     first_page_data = get_data(first_page)
#     page_size = first_page_data["pageInfo"]["pageSize"]
#     total_pages = int(math.ceil(first_page_data["pageInfo"]["totalResults"] / page_size))
#     # setting a limit to the number of pages to scrape
#     if total_pages > 60:
#         # print(f"query has {total_pages}; lowering to max allowed 60 pages")
#         total_pages = 60

#     # get the number of total pages to scrape
#     if max_pages and max_pages < total_pages:
#         total_pages = max_pages

#     # scrape remaining pages concurrently
#     # print(f'scraping search mens t-shirt of total {total_pages} sorted by {sort_type}')

#     other_pages = await asyncio.gather(*[page_response(page=i) for i in range(1, total_pages + 1)])
#     for response in [first_page, *other_pages]:
#         product_previews = []
#         product_previews.extend(get_product_id(response))

#     return product_previews 

# # returns a dictionary of product data after scraping a product page
# def parse_aliexpress_product(response):
#     # parse product HTML page for product data
#     sel = Selector(text=response.text)
#     # find the script tag containing our data:
#     script_with_data = sel.xpath('//script[contains(text(),"window.runParams")]/text()').get()
#     # extract data using a regex pattern:    
#     data = re.findall(r".+?data:\s*({.+?)};", script_with_data, re.DOTALL)
#     data = json.loads(data[0])

#     if "skuModule" not in data:
#         product = {
#             "name": data.get("productInfoComponent", {}).get("idStr"),
#             "total_orders": data.get("tradeComponent", {}).get("formatTradeCount"),
#             "feedback": {
#                 "rating": data.get("feedbackComponent", {}).get("evarageStar"),
#                 "count": data.get("feedbackComponent", {}).get("totalValidNum"),
#             },
#             "images": data.get("imageComponent", {}).get("imagePathList", []),
#         }
#     else:
#         product = {
#             "name": data.get("titleModule", {}).get("subject"),
#             "total_orders": data.get("titleModule", {}).get("formatTradeCount"),
#             "feedback": {
#                 "rating": data.get("titleModule", {}).get("feedbackRating", {}).get("evarageStar"),
#                 "count": data.get("titleModule", {}).get("feedbackRating", {}).get("totalValidNum"),
#             },
#             "images": data.get("imageModule", {}).get("imagePathList", []),
#         }

#     product['specification'] = dict([v.values() for v in product.get('specification', {})])
#     return product


# # Taking a list of product ids, and returns a list of product data after scraping  
# async def scrape_products(ids, session: httpx.AsyncClient):
#     """scrape aliexpress products by id"""
#     # print(f"scraping {len(ids)} products")
#     responses = await asyncio.gather(*[session.get(f"https://www.aliexpress.com/item/{id_}.html") for id_ in ids])

#     results = []
#     for response in responses:
#         results.append(parse_aliexpress_product(response))
#     return results
# # to reduce being blocked, using browser like request headers
# BASE_HEADERS = {
#     "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
#     "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
#     "accept-language": "en-US;en;q=0.9",
#     "accept-encoding": "gzip, deflate, br",
# }

# # main function to run the scraper
# async def run():
#     # client = httpx.AsyncClient(follow_redirects=True)
#     # data = await scrape_aliexpress(session=client, max_pages=3)
#     # print(json.dumps(data, indent=2, ensure_ascii=False))

#     async with httpx.AsyncClient(headers=BASE_HEADERS, follow_redirects=True) as session:
#         print(json.dumps(await scrape_products(["1005005866501109"], session), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    AliexpressScraper = AliexpressScraper()
    asyncio.run(AliexpressScraper.run())

