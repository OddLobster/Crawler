import datetime
from pymongo import MongoClient

class PageDB:
    def __init__(self) -> None:
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['page_db']
        self.collection = self.db['page_infos']

    def insert_pages(self, page_objects):
        page_data = [page.__dict__ for page in page_objects]
        self.collection.insert_many(page_data)