from crawler import Crawler
from database import UrlDB, Database, URL

def main():
    url_db = UrlDB()
    url_db.add_url(URL(url="https://example.com/"))

    db = Database()

    c = Crawler(url_database=url_db, crawl_database=db)
    c.run()

if __name__ == "__main__":
    main()
