from common.BaseCommand import BaseCommand
from common_util import Success
from host import Cloud

__author__ = 'zadjii'


################################################################################
class ListCloudsCommand(BaseCommand):
    def add_parser(self, subparsers):
        list_clouds = subparsers.add_parser('list-clouds', description='list all current clouds')
        return list_clouds

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData
        db = instance.get_db()
        clouds = db.session.query(Cloud).all()
        print 'There are ', len(clouds), 'clouds.'
        print '[{}] {:5} {:16} {:24} {:16}'.format('id'
                                                   , 'my_id'
                                                   , 'name'
                                                   , 'root'
                                                   , 'address')
        for cloud in clouds:

            print '[{}] {:5} {}/{}\t\t{:24} {}:{}'\
                .format(cloud.id, cloud.my_id_from_remote, cloud.uname(), cloud.cname()
                        , cloud.root_directory
                        , cloud.remote.remote_address, cloud.remote.remote_port)


        return Success()