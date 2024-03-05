import httpx
import json
import re
from parsel import Selector
from typing import Dict
import asyncio
import math
import jmespath

# https://scrapfly.io/blog/how-to-scrape-aliexpress/
# Because Aliexpress uses Javascript to dynamically render the page, we have to use hidden web data scraping
def get_aliexpress_data(response) -> Dict:
    # Send a GET request to the URL
    sel = Selector(text=response.text)
    # find the script tag that contains the data
    script_with_data = sel.xpath('//script[contains(.,"_init_data_=")]')
    # Extract the data from the script tag
    data= json.loads(script_with_data.re(r'_init_data_\s*=\s*{\s*data:\s*({.+}) }')[0])
    return data['data']['root']['fields']

def parse_aliexpress_data(reponse):
    # parse search page response for product preview results
    data = get_aliexpress_data(reponse)
    parsed = []
    # print(data)
    for product in data["mods"]["itemList"]["content"]:
        parsed.append(
            {
                "id": product["productId"],
                # "url": f"https://www.aliexpress.com/item/{product['productId']}.html",
                # "type": product["productType"],  # can be either natural or ad
                # "title": product["title"]["displayTitle"],
                # "price": product["prices"]["salePrice"]["minPrice"],
                # "currency": product["prices"]["salePrice"]["currencyCode"],
                # trade represents how many sold
                "trade": product.get("trade", {}).get("tradeDesc"),  # trade line is not always present
                "thumbnail": product["image"]["imgUrl"].lstrip("/"),
                "rating": product["evaluation"]["starRating"],
                # "review_count": product["feedbackRating"]["totalValidNum"],
                # "date": product["publishTime"],
        })
    return parsed

async def scrape_aliexpress(session: httpx.AsyncClient, sort_type="total_tranpro_desc", max_pages: int = None):
    # returns all the search results of a specific page in for men's t-shirts
    async def scrape_search_page(page):
        # print(f"scraping search query mens t-shirt:{page} sorted by {sort_type}")
        resp = await session.get(
           "https://www.aliexpress.com/w/wholesale-men-t-shirts.html?g=y&SearchText=men+t+shirts&sortType=total_tranpro_desc&page={page}"
        )
        return resp

    # scrape first search page and find total result count
    first_page = await scrape_search_page(1)
    first_page_data = get_aliexpress_data(first_page)
    page_size = first_page_data["pageInfo"]["pageSize"]
    total_pages = int(math.ceil(first_page_data["pageInfo"]["totalResults"] / page_size))
    # setting a limit to the number of pages to scrape
    if total_pages > 60:
        # print(f"query has {total_pages}; lowering to max allowed 60 pages")
        total_pages = 60

    # get the number of total pages to scrape
    if max_pages and max_pages < total_pages:
        total_pages = max_pages

    # scrape remaining pages concurrently
    # print(f'scraping search mens t-shirt of total {total_pages} sorted by {sort_type}')

    other_pages = await asyncio.gather(*[scrape_search_page(page=i) for i in range(1, total_pages + 1)])
    for response in [first_page, *other_pages]:
        product_previews = []
        product_previews.extend(parse_aliexpress_data(response))

    return product_previews 

# retrieves how many reviews and the published date of the product
def parse_aliexpress_product(response):
    # parse product HTML page for product data
    # print(response)
    sel = Selector(text=response.text)
    # find the script tag containing our data:
    script_with_data = sel.xpath('//script[contains(text(),"window.runParams")]/text()').get()
    # extract data using a regex pattern:    
    data = re.findall(r".+?data:\s*({.+?)};", script_with_data, re.DOTALL)
    data = json.loads(data[0])
    with open("data.json", "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
    if "skuModule" not in data:
        product = jmespath.search("""{
            name: productInfoComponent.subject,
            total_orders: tradeComponent.formatTradeCount,
            feedback: feedbackComponent.{
                rating: evarageStar,
                count: totalValidNum
            },
            description_url: productDescComponent.descriptionUrl,
            description_short: metaDataComponent.description,
            keywords: metaDataComponent.keywords,
            images: imageComponent.imagePathList,
            stock: inventoryComponent.totalAvailQuantity,
            seller: sellerComponent.{
                id: storeNum,
                url: storeURL,
                name: storeName,
                country: countryCompleteName,
                positive_rating: positiveRate,
                positive_rating_count: positiveNum,
                started_on: openTime,
                is_top_rated: topRatedSeller
            },
            specification: productPropComponent.props[].{
                name: attrName,
                value: attrValue
            },
            variants: priceComponent.skuPriceList[].{
                name: skuAttr,
                sku: skuId,
                available: skuVal.availQuantity,
                stock: skuVal.inventory,
                full_price: skuVal.skuAmount.value,
                discount_price: skuVal.skuActivityAmount.value,
                currency: skuVal.skuAmount.currency
            }
        }""", data)
    else:
        product = jmespath.search("""{
            name: titleModule.subject,
            total_orders: titleModule.formatTradeCount,
            feedback: titleModule.feedbackRating.{
                rating: evarageStar,
                count: totalValidNum                  
            },
            description_url: descriptionModule.descriptionUrl,
            description_short: pageModule.description,
            keywords: pageModule.keywords,
            images: imageModule.imagePathList,
            stock: quantityModule.totalAvailQuantity,
            seller: storeModule.{
                id: storeNum,
                url: storeURL,
                name: storeName,
                country: countryCompleteName,
                positive_rating: positiveRate,
                positive_rating_count: positiveNum,
                started_on: openTime,
                is_top_rated: topRatedSeller
            },
            specification: specsModule.props[].{
                name: attrName,
                value: attrValue
            },
            variants: skuModule.skuPriceList[].{
                name: skuAttr,
                sku: skuId,
                available: skuVal.availQuantity,
                stock: skuVal.inventory,
                full_price: skuVal.skuAmount.value,
                discount_price: skuVal.skuActivityAmount.value,
                currency: skuVal.skuAmount.currency
            }
        }""", data)
    product['specification'] = dict([v.values() for v in product.get('specification', {})])
    return product

async def scrape_products(ids, session: httpx.AsyncClient):
    """scrape aliexpress products by id"""
    # print(f"scraping {len(ids)} products")
    responses = await asyncio.gather(*[session.get(f"https://www.aliexpress.com/item/{id_}.html") for id_ in ids])

    results = []
    for response in responses:
        results.append(parse_aliexpress_product(response))
    return results
# to reduce being blocked, using browser like request headers
BASE_HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "accept-language": "en-US;en;q=0.9",
    "accept-encoding": "gzip, deflate, br",
}
async def run():
    # client = httpx.AsyncClient(follow_redirects=True)
    # data = await scrape_aliexpress(session=client, max_pages=3)
    # print(json.dumps(data, indent=2, ensure_ascii=False))

    async with httpx.AsyncClient(headers=BASE_HEADERS, follow_redirects=True) as session:
        print(json.dumps(await scrape_products(["1005005866501109"], session), indent=2, ensure_ascii=False))



if __name__ == "__main__":
    asyncio.run(run())