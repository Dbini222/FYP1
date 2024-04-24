This directory is to store all the scripts that I will be using in this project. This is limited to MEN'S T-SHIRTS
TODO:
- write tests for what to do if the website is returning none (i.e.e because the website has changed the way it does the tags for example)

AIM:
- go through the several e-commerce website pages get images from their best selling t-shirts
- if they don't have a best selling t-shirt area, think of other alternatives such as filtering by popularity etc
- 

The websites which I am going to use for webscraping are:
- Tee Fury: doesn't give any rating or anything, just the popularity order
- Redbubble : https://www.redbubble.com/shop/?iaCode=u-tees&sortOrder=top%20selling
- Spreadshirt : it's illegal
- Aasaan App
- Shopify
- Aliexpress: https://www.aliexpress.com/w/wholesale-men-t-shirts.html?g=y&SearchText=men+t+shirts&sortType=total_tranpro_desc
- Amazon (top 100 t-shirts): https://www.amazon.co.uk/Best-Sellers-Fashion-Mens-T-Shirts/zgbs/fashion/1731028031/ref=zg_bs_nav_fashion_4_1731025031
- Shopify
- Squarespace
- OpenCart
- BigCommerce

AASAAN APP:


AMAZON:

They have the top best 100 male t-shirts in the link below. The website also shows the following measures:
-Rating
-How many people rated the t-shirt.

https://www.amazon.co.uk/Best-Sellers-Fashion-Mens-T-Shirts/zgbs/fashion/1731028031/ref=zg_bs_nav_fashion_4_1731025031

ALIEXPRESS:

They allow you to order the t-shirt based on how many orders it has, so the link below is ordered based on popular orders first. This website also shows the following measures:
- Rating
-Rough generalising how many people bought it

https://www.aliexpress.com/w/wholesale-men-t-shirts.html?g=y&SearchText=men+t+shirts&sortType=total_tranpro_desc 

REDBUBBLE: 

They allow you to order the t-shirt based on how many orders it has, however in order to access the ratings and stuff, you need to click on the picture. Therefore the website has the following measurements :
- Rating
- how many peoople rated the t-shirt


1- Choosing the Right Tools:
    * For your specific use case, I recommend using a combination of Beautiful Soup and Scrapy:
        -Beautiful Soup: Use it for parsing HTML content and extracting specific data elements (such as t-shirt designs and release dates).
        -Scrapy: Use it for handling large-scale web scraping, navigating complex website structures, and efficiently scraping data from multiple pages.
    *Selenium: While Selenium is powerful for interacting with dynamic websites (e.g., handling JavaScript), it’s generally slower and resource-intensive compared to Scrapy and Beautiful Soup. Reserve Selenium for cases where dynamic content requires browser automation.

2- Planning Your Scraping Project:
    * Identify the 10 websites you want to scrape.
    * Determine the frequency of scraping (one-time, periodic, continuous).
    * Decide on the data format you need (raw HTML, processed data, CSV, JSON, etc.).

3- Scraping Workflow:
    * Set up a Scrapy project to handle the overall scraping process.
    * Use Scrapy to navigate through the websites, follow links, and extract relevant pages.
    * On each page, use Beautiful Soup to parse the HTML content and extract t-shirt designs, release dates, and other relevant information.
4- Handling Reviews and Ratings:
    * For reviews and ratings, consider using Scrapy to scrape review pages.
    * Extract review text, star ratings, and post dates.
    * Handle pagination (if reviews span multiple pages).
5- Efficient Scraping Techniques:
    * Implement rate limiting to avoid overwhelming servers.
    * Use proxy servers and IP rotation to prevent IP bans.
    * Distribute scraping tasks across multiple machines for parallel processing.
    * Store scraped data (including images) in a structured format (e.g., folders for each t-shirt design).
    * Preprocess images (resize, normalize, etc.) before using them for training.
6- Data Storage and Processing:
    * Store scraped data in a database or file system.
    * Process and clean the data as needed.
7- Testing and Monitoring:
    * Test your scraping code thoroughly.
    * Monitor scraping progress and handle any errors.
