from datetime import datetime
import getpass
from werkzeug.security import check_password_hash

from common_util import Error, Success
from remote import User, Cloud
# from remote import remote_db as db

__author__ = 'zadjii'

FOUR_GB = 4 * 1000 * 1000 * 1000


def create(instance, argv):
    """Creates a new cloud in the db to be tracked. Needs the credentials of the
    User who owns it."""
    db = instance.get_db()
    print 'Creating a new cloud. First, enter credentials for the owner'
    owner_uname = raw_input('Enter the owner\'s username: ')
    owner_pass = getpass.getpass('Enter the owner\'s password: ')
    owner = db.session.query(User).filter_by(username=owner_uname).first()

    if (owner is None) or (not (check_password_hash(owner.password, owner_pass))):
        print('username/password combination invalid.')
        return
    cloud_name_in = raw_input('Please enter the name of the new cloud: ')
    owned_clouds_dups_check = owner.owned_clouds\
        .filter_by(name=cloud_name_in)\
        .first()
    # contributed_clouds_dups_check = owner.contributed_clouds\
    #     .filter_by(name=cloud_name_in)\
    #     .first()
    if (owned_clouds_dups_check is not None): # \
            # or (contributed_clouds_dups_check is not None):
        print('{} already has a cloud named {}'.format(owner.name, cloud_name_in))
        return

    max_size = raw_input(
        'Enter a max size for the cloud in bytes' +
        ' (leave blank to default to 4 GB(40000000000)'
    )

    if max_size is None or max_size is '':
        max_size = FOUR_GB
    else:
        max_size = int(max_size)
    
    rd = create_cloud(db, owner_uname, owner_pass, cloud_name_in, max_size)
    
    print 'Successfully created the', cloud_name_in, 'cloud for', owner_uname


def create_cloud(db, username, password, cloudname, max_size):
    rd = Error()

    owner = db.session.query(User).filter_by(username=username).first()
    
    if (owner is None) or (not (check_password_hash(owner.password, password))):
        msg = 'Owner username/password combination invalid.'
        print(msg)
        return Error(msg)
        # raise Exception('Owner username/password combination invalid.')
    
    owned_clouds_dups_check = owner.owned_clouds\
        .filter_by(name=cloudname)\
        .first()
    
    # contributed_clouds_dups_check = owner.contributed_clouds\
    #     .filter_by(name=cloudname)\
    #     .first()
    if (owned_clouds_dups_check is not None): # \
            # or (contributed_clouds_dups_check is not None):
        msg = '{} already has a cloud named {}'.format(owner.name, cloud_name_in)
        print msg
        return Error(msg)
        # print('{} already has a cloud named {}'.format(owner.name, cloud_name_in))
        # raise Exception(owner.name, 'already has a cloud named', cloudname)

    if max_size is None:
        max_size = FOUR_GB
    new_cloud = Cloud(
        creator=owner
        , name=cloudname
        , created_on=datetime.utcnow()
        , last_update=datetime.utcnow()
        , max_size=max_size
    )
    db.session.add(new_cloud)
    # new_cloud.owners.append(owner)
    new_cloud.contributors.append(owner)
    db.session.commit()


def do_create_cloud(db, creator, cloudname, max_size=FOUR_GB):
    # type: (SimpleDB, User, str, int) -> ResultAndData
    # type: (SimpleDB, User, str, int) -> ResultAndData(True, Cloud)
    # type: (SimpleDB, User, str, int) -> ResultAndData(False, str)
    """
    This doesn't actually check any user credentials. We kinda just make a cloud for that user.

    :param db:
    :param creator:
    :param cloudname:
    :param max_size:
    :return:
    """
    # todo:31 change the other functions here to use this function
    if creator is None:
        return Error('Cloud creator was None')
    created_clouds = creator.created_clouds
    duplicate_cloud = created_clouds.filter_by(name=cloudname).first()
    if duplicate_cloud is not None:
        return Error('Another cloud with the name {} already exists'.format(duplicate_cloud.full_name()))

    new_cloud = Cloud(creator)
    new_cloud.name = cloudname
    new_cloud.max_size = max_size

    db.session.add(new_cloud)
    db.session.commit()
    return Success(new_cloud)




