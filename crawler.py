from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from time import sleep
import httpx
import datetime
import validators


class DataHandler:
    def __init__(self) -> None:
        self.urls = set()
        self.urls_visited = set()
        self.soup = None

    def init_soup(self, response):
        self.soup = BeautifulSoup(response.text, 'html.parser')

    def get_child_urls(self, response):
        self.urls_visited.add(str(response.url))

        anchor_tags = self.soup.find_all('a')
        child_urls = []
        for anchor_tag in anchor_tags:
            href = anchor_tag.get('href')
            if href == None:
                continue
            if not validators.url(href):
                child_url = urljoin(str(response.url), href)
                if not validators.url(child_url):
                    continue
            else:
                child_url = href
            self.urls.add(child_url)
            domain = urlparse(child_url)
            child_domain = domain.scheme + "://" + domain.netloc
            if child_domain not in self.urls_visited:
                child_urls.append(child_domain)
        return child_urls

    def get_data(self, response):
        meta_tags = self.soup.find_all('meta')
        title = ""
        description = ""
        keywords = []
        for meta in meta_tags:
            print(meta.attrs, )
            if len([x for x in meta.attrs.values() if "description" in x]):
                if "content" in meta.attrs.keys():
                    description = meta.attrs["content"]
                elif "value" in meta.attrs.keys():
                    description = meta.attrs["value"]
            elif len([x for x in meta.attrs.values() if "title" in x]):
                if "content" in meta.attrs.keys():
                    title = meta.attrs["content"]
                elif "value" in meta.attrs.keys():
                    title = meta.attrs["value"]

        print("Website Data")
        print(f"Title: {title}")
        print(f"URL: {response.url}")
        print(f"Description: {description}")
        print(f"Keywords: {keywords}")
        return


class Crawler:
    def __init__(self, url_database, crawl_database, nruns=50) -> None:
        self.url_queue = []
        self.num_runs = nruns
        self.url_db = url_database
        self.crawl_db = crawl_database
        self.handler = DataHandler()

        self.urldb_session = self.url_db.create_session()
        self.url_queue.append(self.url_db.get_url())

    def run(self) -> None:
        urls_crawled = 0
        while self.num_runs > 0 and len(self.url_queue) > 0:
            url = self.url_queue.pop()
            print(f"Crawling {url}", end="")
            response = httpx.get(url)
            print(f" | Status Code: {response.status_code}", end="")
            self.handler.urls_visited.add(url)
            if response.status_code == httpx.codes.OK:
                self.handler.init_soup(response)
                urls_crawled += 1
                child_urls = self.handler.get_child_urls(response)
                for x in child_urls:
                    if x in self.url_queue:
                        continue
                    self.url_queue.append(x)

                data = self.handler.get_data(response)
                
            else:
                #TODO - Handle Other status codes
                pass               
            print(f" | {len(self.url_queue)} | {self.num_runs}")
            self.num_runs -= 1
            sleep(1)
        print(f"Crawled {urls_crawled} urls")