from common_util import validate_cloudname
from remote import User, Cloud
from remote.util import get_cloud_by_name
from common.BaseCommand import BaseCommand
from common_util import ResultAndData, Error, Success
from argparse import Namespace

class ListUsersCommand(BaseCommand):
    def add_parser(self, subparsers):
        list_users = subparsers.add_parser('list-users', description='list all current users')
        return list_users

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData
        db = instance.get_db()
        # users = User.query.all()
        users = db.session.query(User).all()
        print 'There are ', len(users), 'users.'
        print '[{:4}] {:16} {:16} {:16}'.format('id', 'username', 'name', 'email')
        for user in users:
            print '[{:4}] {:16} {:16} {:16}'.format(user.id, user.username, user.name, user.email)
        return Success()


################################################################################
class ListCloudsCommand(BaseCommand):
    def add_parser(self, subparsers):
        list_users = subparsers.add_parser('list-clouds', description='list all current clouds')
        return list_users

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData
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
        return Success()


################################################################################
class ListHostsCommand(BaseCommand):
    def add_parser(self, subparsers):
        list_hosts = subparsers.add_parser('list-hosts', description='Lists details about hosts')
        list_hosts.add_argument('-a', '--all'
                                , action='store_true'
                                , help='Print for all clouds on this remote')
        list_hosts.add_argument('cloud_name', metavar='cloud-name'
                                , nargs='?'
                                , help='Name of the cloud to print the hosts for, in <username>/<cloudname> format')
        return list_hosts

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData
        output_all = args.all
        cloudname = args.cloud_name
        if not output_all and cloudname is None:
            return Error('error: must input a cloudname or use --all to print all clouds')
        return do_list_hosts(instance, output_all, cloudname)


def do_list_hosts(instance, list_all, cloudname):
    db = instance.get_db()
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
################################################################################
