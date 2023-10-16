from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from time import sleep
from dataclasses import dataclass, field
from icecream import ic
from pympler.asizeof import asizeof
import httpx
import datetime
import validators
import threading

ic.disable()

url_db_lock = threading.Lock()
page_db_lock = threading.Lock()

@dataclass
class PageInfo:
    title: str = field(default="")
    url: str = field(default="")
    description: str = field(default="")
    keywords: str = field(default="")
    headers: list = field(default_factory=list)
    image_descriptions: list = field(default_factory=list)
    urls: list = field(default_factory=list)

class DataHandler:
    def __init__(self, url_db) -> None:
        self.urls = set()
        self.urls_visited = set()
        self.soup = None
        self.url_db = url_db

    def init_soup(self, response):
        self.soup = BeautifulSoup(response.text, 'html.parser')

    def get_child_urls(self, response):
        self.urls_visited.add(str(response.url))
        self.urls.add(str(response.url))

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
            if child_domain not in self.urls_visited: #and not self.url_db.is_discovered_url(child_domain):
                child_urls.append(child_domain)
        return child_urls
    
    def handle_meta_tag(self, info):
        page_title = ""
        description = ""
        keywords = []

        meta_tags = self.soup.find_all('meta')
        for meta in meta_tags:
            if len([x for x in meta.attrs.values() if "description" in x]):
                if "content" in meta.attrs.keys():
                    description = meta.attrs["content"]
                elif "value" in meta.attrs.keys():
                    description = meta.attrs["value"]
            elif len([x for x in meta.attrs.values() if "title" in x]):
                if "content" in meta.attrs.keys():
                    page_title = meta.attrs["content"]
                elif "value" in meta.attrs.keys():
                    page_title = meta.attrs["value"]
            elif len([x for x in meta.attrs.values() if "keyword" in x]):
                if "content" in meta.attrs.keys():
                    keywords = meta.attrs["content"].split(",")
                elif "value" in meta.attrs.keys():
                    keywords = meta.attrs["value"].split(",")

        if page_title == "":
            title = self.soup.find("title")
            if not title:
                page_title = ""
            else:
                page_title = title.text.strip()

        info.title = page_title
        info.description = description
        info.keywords = keywords

    def handle_headers(self, info):
        header_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        headers = []
        for tag in header_tags:
            headers.extend([header.text.strip() for header in self.soup.find_all(tag)])
        info.headers = list(set(headers))

    def handle_img_descriptions(self, info):
        img_alts = set([img.get("alt") for img in self.soup.find_all('img')])
        img_alts = list(filter(lambda string: string != '', img_alts))
        info.image_descriptions = img_alts

    def populate_data(self, info):
        self.handle_meta_tag(info)
        self.handle_headers(info)
        self.handle_img_descriptions(info)

    def print_info(info):
        print("Website Data")
        print(f"Title: {info.page_title}")
        print(f"URL: {info.url}")
        print(f"Description: {info.description}")
        print(f"Keywords: {info.keywords}")
        print(f"Headers: {info.headers}")
        print(f"IMG Descriptions: {info.img_alts}")

    def write_urls_to_db(self):
        if len(self.urls) > 5:
            url_db_lock.acquire()
            self.url_db.add_urls(self.urls)
            url_db_lock.release()


class Crawler(threading.Thread):
    def __init__(self, url_database, crawl_database, id, nruns=50, num_seeds_initial=5, write_to_db_interval=100) -> None:
        super(Crawler, self).__init__()
        self.url_queue = []
        self.num_runs = nruns
        self.url_db = url_database
        self.crawl_db = crawl_database
        self.handler = DataHandler(url_database)
        self.save_db_interval = write_to_db_interval
        self.id = id

        init_urls = self.url_db.get_url(num_seeds_initial)
        self.url_queue.extend(init_urls)
    
    def write_data_to_db(self, data):
        page_db_lock.acquire()
        self.crawl_db.insert_pages(data)
        page_db_lock.release()

    def run(self) -> None:
        urls_crawled = 0
        data = []

        while self.num_runs > 0 and len(self.url_queue) > 0:
            info_string = ""
            if (urls_crawled + 1) % self.save_db_interval == 0:
                self.write_data_to_db(data)
                self.handler.write_urls_to_db()

            url = self.url_queue.pop()
            info_string += f"Crawler: {self.id} | Crawling {url[:27]+'...' if len(url) > 30 else url :<30}"
        
            try:
                url_db_lock.acquire()
                if self.url_db.is_discovered_url(url):
                    info_string += f" Skipped due to duplicate"
                    url_db_lock.release()
                    continue
                url_db_lock.release()
                response = httpx.get(url)
            except:
                info_string += "Error during HTTPX request"
                self.handler.urls_visited.add(url)
                continue
            finally:
                url_db_lock.acquire()
                self.url_db.update_discovered_urls([url])
                url_db_lock.release()
        
            self.handler.urls_visited.add(url)
            info_string += f" | Status Code: {response.status_code:<3}"
            if response.status_code == httpx.codes.OK:
                page_info = PageInfo(url=url)
                self.handler.init_soup(response)
                urls_crawled += 1
                child_urls = self.handler.get_child_urls(response)
                page_info.urls = list(set(child_urls))
                for x in child_urls:
                    if x in self.url_queue:
                        continue
                    self.url_queue.append(x)

                try:
                    self.handler.populate_data(page_info)
                except:
                    info_string += "Error while extracting data"
                    continue

                data.append(page_info)
            else:
                #TODO - Handle Other status codes
                url_db_lock.acquire()
                self.url_db.set_retry(url, False)
                url_db_lock.release()
                pass

            info_string += f" | {len(self.url_queue):<5} | {self.num_runs:<5}"
            self.num_runs -= 1
            print(info_string)
            sleep(0.33)


        info_string = ""
        info_string += f"Crawler: {self.id} | Crawled {urls_crawled} urls\n"
        info_string += f"Crawler: {self.id} | Total Information: {asizeof(data)}\n"
        print(info_string)

        self.write_data_to_db(data)
        self.handler.write_urls_to_db()

