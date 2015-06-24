from migrate.versioning import api
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
__author__ = 'Mike'


class SimpleDB(object):
    def __init__(self, database_uri):
        self.db_uri = database_uri
        self.engine = engine = create_engine(database_uri, echo=True)
        Session = sessionmaker(bind=engine)  # create a configured "Session" class
        self.session = Session()  # create a Session
        self.Base = declarative_base()
        # Base.metadata.create_all(engine, checkfirst=True)

    def create_all(self):
        self.Base.metadata.create_all(self.engine, checkfirst=True)
    def create_all_and_repo(self, migrate_repo, database_uri):
        self.create_all()

        print 'The database should have been created here'

        if not os.path.exists(migrate_repo):
            api.create(migrate_repo, 'database repository')
            api.version_control(database_uri, migrate_repo)
        else:
            api.version_control(database_uri, migrate_repo, api.version(migrate_repo))

        print 'The migration repo should have been created here'