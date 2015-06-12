from sqlalchemy.ext.declarative import declarative_base

__author__ = 'Mike'

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class SimpleDB(object):
    def __init__(self, database_uri):
        self.db_uri = database_uri
        self.engine = engine = create_engine(database_uri, echo=True)  # We don't really want logging, right?
        # Base = declarative_base()  # This is the 'base' for declaring orm mappings
        Session = sessionmaker(bind=engine)  # create a configured "Session" class
        self.session = Session()  # create a Session
        self.Base = declarative_base()
        # Base.metadata.create_all(engine, checkfirst=True)

    def create_all(self):
        self.Base.metadata.create_all(self.engine, checkfirst=True)