from datetime import datetime
import getpass
from werkzeug.security import check_password_hash
from remote import User, Cloud
from remote import remote_db as db

__author__ = 'zadjii'


def create(argv):
    """Creates a new cloud in the db to be tracked. Needs the credentials of the
    User who owns it."""
    print 'Creating a new cloud. First, enter credentials for the owner'
    owner_uname = raw_input('Enter the owner\'s username: ')
    owner_pass = getpass.getpass('Enter the owner\'s password: ')
    owner = User.query.filter_by(username=owner_uname).first()

    if (owner is None) or (not (check_password_hash(owner.password, owner_pass))):
        print 'username/password combination invalid.'
        return
    cloud_name_in = raw_input('Please enter the name of the new cloud: ')
    owned_clouds_dups_check = owner.owned_clouds\
        .filter_by(name=cloud_name_in)\
        .first()
    contributed_clouds_dups_check = owner.contributed_clouds\
        .filter_by(name=cloud_name_in)\
        .first()
    if (owned_clouds_dups_check is not None) \
            or (contributed_clouds_dups_check is not None):
        print owner.name, 'already has a cloud named', cloud_name_in
        return
    max_size = raw_input(
        'Enter a max size for the cloud in bytes' +
        ' (leave blank to default to 4 MB(4000000)'
    )
    if max_size is None or max_size is '':
        max_size = 4000000
    else:
        max_size = int(max_size)
    create_cloud(owner_uname, owner_pass, cloud_name_in, max_size)
    print 'Successfully created the', cloud_name_in, 'cloud for', owner_uname


def create_cloud(username, password, cloudname, max_size):
    owner = User.query.filter_by(username=username).first()
    if (owner is None) or (not (check_password_hash(owner.password, password))):
        raise Exception('Owner username/password combination invalid.')
    owned_clouds_dups_check = owner.owned_clouds\
        .filter_by(name=cloudname)\
        .first()
    contributed_clouds_dups_check = owner.contributed_clouds\
        .filter_by(name=cloudname)\
        .first()
    if (owned_clouds_dups_check is not None) \
            or (contributed_clouds_dups_check is not None):
        raise Exception(owner.name, 'already has a cloud named', cloudname)

    if max_size is None:
        max_size = 4000000
    new_cloud = Cloud(
        name=cloudname
        , created_on=datetime.utcnow()
        , last_update=datetime.utcnow()
        , max_size=max_size
    )
    db.session.add(new_cloud)
    new_cloud.owners.append(owner)
    new_cloud.contributors.append(owner)
    db.session.commit()