import host

__author__ = 'zadjii'

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


from host.models.Cloud import Cloud
from host.models.FileNode import FileNode
from host.models.IncomingHostEntry import IncomingHostEntry


def repop():
    # host_db = host.get_db()
    # does nothing
    #fixme rewrite to use an instance DB
    print 'Host DB populated'

if __name__ == '__main__':
    repop()
