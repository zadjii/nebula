import os
__author__ = 'Mike'



host_basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE_URI = 'sqlite:///' + os.path.join(host_basedir, 'host.db')
MIGRATE_REPO = os.path.join(host_basedir, 'db_repository')