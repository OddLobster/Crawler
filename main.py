from crawler import Crawler
from url_database import UrlDB
from page_database import PageDB

NUM_CRAWLER = 250

def main():
    url_db = UrlDB()
    # url_db.add_url(URL(url="https://example.com/"))
    # url_db.add_url(URL(url="https://en.m.wikipedia.org/wiki/Mars"))
    # url_db.add_url(URL(url="https://refactoring.guru/"))
    # url_db.add_url(URL(url="https://www.scrapehero.com/how-to-fake-and-rotate-user-agents-using-python-3/"))

    db = PageDB()
    
    crawlers = [Crawler(url_database=url_db, crawl_database=db, id=i, nruns=100, num_seeds_initial=10) for i in range(NUM_CRAWLER)]
    for crawler in crawlers:
        crawler.start()

    for crawler in crawlers:
        crawler.join()

if __name__ == "__main__":
    main()
