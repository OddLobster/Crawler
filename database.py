from sqlalchemy import create_engine, Column, String, DateTime, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

class URL(Base):
    __tablename__ = 'urls'

    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    discovered = Column(Boolean, default=False)


class UrlDB:
    def __init__(self) -> None:
        self.engine = create_engine("sqlite:///url.db", echo=True)
        self.session = sessionmaker(bind=self.engine)()
        Base.metadata.create_all(self.engine)

    def create_session(self):
        return sessionmaker(bind=self.engine)()

    def add_url(self, url):
        self.session.add(url)
        self.session.commit()

    def get_url(self):
        url = (
            self.session.query(URL)
            .filter(URL.discovered == False)
            .order_by(URL.timestamp.asc())
            .first()
        )
        if not url:
            print("There is no discoverable URL in the URL Database")
            return None
        return url.url


class Database:
    def __init__(self) -> None:
        pass

