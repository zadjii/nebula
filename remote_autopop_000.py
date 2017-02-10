import sys

import remote
from common.Instance import Instance
from remote.NebrInstance import NebrInstance

__author__ = 'zadjii'

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


from remote.models.Cloud import Cloud
from remote.models.User import User
from remote.models.Host import Host


def repop(instance):
    remote_db = instance.get_db()

    asdf = User()
    asdf.created_on = datetime.utcnow()
    asdf.email = 'asdf'
    asdf.name = 'asdf'
    asdf.username = 'asdf'
    asdf.password = generate_password_hash('asdf')

    mike = User()
    mike.created_on = datetime.utcnow()
    mike.email = 'mike'
    mike.name = 'mike'
    mike.username = 'mike'
    mike.password = generate_password_hash('mike')

    admin = User()
    admin.created_on = datetime.utcnow()
    admin.email = 'admin'
    admin.name = 'admin'
    admin.username = 'admin'
    admin.password = generate_password_hash('admin')

    remote_db.session.add(asdf)
    remote_db.session.add(mike)
    remote_db.session.add(admin)

    remote_db.session.commit()

    qwer = Cloud(asdf)
    remote_db.session.add(qwer)
    qwer.name = 'qwer'
    qwer.created_on = datetime.utcnow()
    qwer.last_update = datetime.utcnow()
    # qwer.owners.append(asdf)
    qwer.owners.append(admin)
    qwer.contributors.append(mike)
    qwer.max_size = 4000000

    zxcv = Cloud(admin)
    remote_db.session.add(zxcv)
    zxcv.name = 'zxcv'
    zxcv.created_on = datetime.utcnow()
    zxcv.last_update = datetime.utcnow()
    zxcv.contributors.append(asdf)
    # zxcv.owners.append(admin)
    zxcv.owners.append(mike)
    zxcv.max_size = 4 * 1000 * 1000 * 1000  # 4GB

    remote_db.session.commit()
    print 'Remote DB populated'

if __name__ == '__main__':
    argv = sys.argv
    working_dir, argv = Instance.get_working_dir(argv, True)
    nebr_instance = NebrInstance(working_dir)
    repop(nebr_instance)
