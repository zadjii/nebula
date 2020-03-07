import sys
import os
_NEBULA_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(_NEBULA_ROOT)
from common.Instance import Instance
from remote.NebrInstance import NebrInstance

__author__ = 'zadjii'

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from remote.models.Cloud import Cloud
from remote.models.User import User
from remote.models.Host import Host


"""
Designed to be seperate and comaptable with autopop_000, without being dependent
on it.
Creates a number of users, and a variety of clouds between them.
"""

FOUR_GB = 4 * 1024 * 1024 * 1024

def make_simple_user(db, name):
    user = User()
    user.created_on = datetime.utcnow()
    user.email = name
    user.name = name
    user.username = name.replace(' ', '-')
    # note to future self:
    # The password is based on the *name* e.g. 'Mike Griese' not 'Mike-Griese'
    user.password = generate_password_hash(name)
    db.session.add(user)
    return user


def repop(instance):
    db = instance.get_db()

    mikegr = make_simple_user(db, 'Mike Griese')
    clairabel = make_simple_user(db, 'Claire Bovee')
    hoon = make_simple_user(db, 'Hannah Bovee')
    mr_bovee = make_simple_user(db, 'Mr Bovee')
    sueb = make_simple_user(db, 'Susan Bovee')
    sueg = make_simple_user(db, 'Sue Griese')
    daddio = make_simple_user(db, 'Joe Griese')
    alli = make_simple_user(db, 'Alli Anderson')

    db.session.commit()

    wedding = Cloud(mikegr)
    db.session.add(wedding)
    wedding.name = 'AfterglowWedding2017'
    wedding.created_on = datetime.utcnow()
    # wedding.last_update = datetime.utcnow()
    wedding.max_size = FOUR_GB
    wedding.owners.append(mikegr)
    wedding.owners.append(clairabel)
    # All contributors should be added via API calls
    # wedding.contributors.append(hoon)
    # wedding.contributors.append(mr_bovee)
    # wedding.contributors.append(sueb)
    # wedding.contributors.append(sueg)
    # wedding.contributors.append(daddio)

    bridesmaids = Cloud(clairabel)
    db.session.add(bridesmaids)
    bridesmaids.name = 'Claires-Bridesmaids'
    bridesmaids.created_on = datetime.utcnow()
    # bridesmaids.last_update = datetime.utcnow()
    bridesmaids.max_size = FOUR_GB
    # bridesmaids.owners.append(clairabel)
    # wedding.contributors.append(hoon)
    # bridesmaids.owners.append(alli)

    bachelorette = Cloud(hoon)
    db.session.add(bachelorette)
    bachelorette.name = 'Claires_Bachelorette_Party'
    bachelorette.created_on = datetime.utcnow()
    # bachelorette.last_update = datetime.utcnow()
    bachelorette.max_size = FOUR_GB
    # bachelorette.owners.append(hoon)
    bachelorette.owners.append(alli)

    db.session.commit()

    print('{} privacy={}'.format(wedding.name, wedding.privacy))
    print('{} privacy={}'.format(bridesmaids.name, bridesmaids.privacy))
    print('{} privacy={}'.format(bachelorette.name, bachelorette.privacy))

    print 'Remote DB populated with 001 data - "Wedding"'

if __name__ == '__main__':
    argv = sys.argv
    working_dir, argv = Instance.get_working_dir(argv, True)
    nebr_instance = NebrInstance(working_dir)
    repop(nebr_instance)
