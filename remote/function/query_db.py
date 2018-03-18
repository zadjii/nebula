from common_util import validate_cloudname
from remote import User, Cloud
from remote.util import get_cloud_by_name


def list_users(instance, argv):
    db = instance.get_db()
    # users = User.query.all()
    users = db.session.query(User).all()
    print 'There are ', len(users), 'users.'
    print '[{:4}] {:16} {:16} {:16}'.format('id', 'username', 'name', 'email')
    for user in users:
        print '[{:4}] {:16} {:16} {:16}'.format(user.id, user.username, user.name, user.email)


def list_clouds(instance, argv):
    db = instance.get_db()
    # clouds = Cloud.query.all()
    clouds = db.session.query(Cloud).all()
    print('There are {} clouds.'.format(len(clouds)))
    print('[{}], {}, {}, {}, {}'.format('id', 'uname/cname', 'privacy', 'max_size', 'owners', 'contributors'))
    for cloud in clouds:
        # owners = ''
        # for owner in cloud.owners:
        #     owners = owners + owner.username + ' '
        owners = [u.username for u in cloud.owners]
        contributors = [u.username for u in cloud.contributors]
        print('[{}], {}, {}, {}B, {}, {}'
              .format(cloud.id, cloud.full_name(), cloud.privacy, cloud.max_size, owners, contributors))


def list_hosts(instance, argv):
    if len(argv) < 1:
        print('usage: list-hosts <cloudname>')
        print('usage: list-hosts [options]')
        print('Options:')
        print('\t--all, -a: Print for all clouds')

    db = instance.get_db()
    list_all = False
    cloudname = None
    if argv[0] == '-a':
        list_all = True
    elif argv[0] == '--all':
        list_all = True
    else:
        cloudname = argv[0]

    if list_all:
        clouds = db.session.query(Cloud).all()
        for cloud in clouds:
            _list_hosts(instance, cloud)
    else:
        rd = validate_cloudname(cloudname)
        if rd.success:
            uname, cname = rd.data
            cloud = get_cloud_by_name(db, uname, cname)
            if cloud is None:
                print('Could not find a cloud with the name {}'.format(cloudname))
            else:
                _list_hosts(instance, cloud)
        else:
            print('{} is not a valid cloud name. '
                  'Cloud names are of the format '
                  '"<username>/<cloudname>"'.format(cloudname))


def _list_hosts(instance, cloud):
    print('Hosts for cloud {}'.format(cloud.full_name()))
    for host in cloud.hosts.all():
        print(host.to_json())
        # print('{}, {}, {}, {}, {}, {}'.format(
        #     host.hostname, host.id, host.cloud_id, host.ipv6, host.last_handshake, host.last_update))
