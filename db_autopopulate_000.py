__author__ = 'zadjii'

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from host import host_db
from remote import remote_db

from host.models.Cloud import Cloud
from host.models.FileNode import FileNode
from host.models.IncomingHostEntry import IncomingHostEntry

from remote.models.Cloud import Cloud
from remote.models.User import User
from remote.models.Host import Host

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

qwer = Cloud()
remote_db.session.add(qwer)
qwer.name = 'qwer'
qwer.created_on = datetime.utcnow()
qwer.owners.append(asdf)
qwer.owners.append(admin)
qwer.contributors.append(mike)
qwer.max_size = 4000000

zxcv = Cloud()
remote_db.session.add(zxcv)
zxcv.name = 'zxcv'
zxcv.created_on = datetime.utcnow()
zxcv.contributors.append(asdf)
zxcv.owners.append(admin)
zxcv.owners.append(mike)
zxcv.max_size = 4 * 1000 * 1000 * 1000  # 4GB

remote_db.session.commit()



