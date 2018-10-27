import logging
import os
import unittest
from host import models
from common.SimpleDB import SimpleDB
from common_util import RelativePath, get_path_elements


class HostDbTestBase(unittest.TestCase):

    def setUp(self):
        db_uri = 'sqlite:///'
        db_models = models.nebs_base

        simple_db = SimpleDB(db_uri, db_models)
        simple_db.engine.echo = False

        # Clear anything out first
        # simple_db.session.remove()
        # simple_db.drop_all()
        simple_db.create_all()

        self.db = simple_db

    def tearDown(self):
        # self.db.session.remove()
        # self.db.drop_all()
        pass

def main():
    unittest.main()

if __name__ == '__main__':
    main()
