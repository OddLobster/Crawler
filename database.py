from sqlalchemy import create_engine, Column, String, DateTime, Integer, Boolean, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
from contextlib import contextmanager
from sqlalchemy.dialects.sqlite import insert

Base = declarative_base()

class URL(Base):
    __tablename__ = 'urls'

    url = Column(String, nullable=False, unique=True)

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    discovered = Column(Boolean, default=False)
    retry = Column(Boolean, default=True)


class UrlDB:
    def __init__(self) -> None:
        self.engine = create_engine("sqlite:///url.db", echo=False)
        Base.metadata.create_all(self.engine)

    @contextmanager
    def create_session(self):
        session = sessionmaker(bind=self.engine)()
        try:
            yield session
            session.commit()
        except Exception as e:
            print("E: ", e)
            session.rollback()
            raise KeyboardInterrupt #TODO create proper Error
        finally:
            session.close()

    def add_url(self, url):
        with self.create_session() as session:
            session.add(url)

    def add_urls(self, urls):
        with self.create_session() as session:
            # for url in urls:
            #     if not session.query(URL).filter(URL.url == url).first():
            #         new_url = URL(url=url)
            #         session.add(new_url)
            url_objects = [URL(url=url) for url in urls]
            # for url in url_objects:
            #     del url["_sa_instance_state"]
            stmt = insert(URL).values(url_objects)
            stmt = stmt.on_conflict_do_nothing(index_elements=['url'])  # Specify the unique index column(s)
            session.execute(stmt)


    def update_discovered_urls(self, visited_urls):
        with self.create_session() as session:
            for url in visited_urls:
                url_record = session.query(URL).filter(URL.url == url).filter(URL.discovered == False).first()
                if url_record:
                    url_record.discovered = True

    def get_url(self, num_urls=1):
        with self.create_session() as session:
            urls = (
                session.query(URL)
                .filter(URL.discovered == False)
                .order_by(URL.timestamp.asc())
                .limit(num_urls)
            )
            if not urls:
                print("There is no discoverable URL in the URL Database")
                return None

            url_strs = [url.url for url in urls]
        return url_strs
    

    
    def is_discovered_url(self, url):
        with self.create_session() as session:
            try:
                url_record = session.query(URL).filter(URL.url == url).first()
                if url_record:
                    return url_record.discovered
            except Exception as e:
                print(f"An error occurred: {e}")
                return False

    def set_retry(self, url, value):
        with self.create_session() as session:
            url_record = session.query(URL).filter(URL.url == url).first()
            if url_record:
                url_record.retry = value 

    def debug(self, url):
        with self.create_session() as session:
            url_record = session.query(URL).filter(URL.url == url).first()
            if url_record:
                print(f"ID: {url_record.id}")
                print(f"URL: {url_record.url}")
                print(f"Timestamp: {url_record.timestamp}")
                print(f"Discovered: {url_record.discovered}")
            else:
                print("No record found for this URL.")

class Database:
    def __init__(self) -> None:
        pass

