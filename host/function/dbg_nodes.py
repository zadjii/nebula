from common.BaseCommand import BaseCommand
from common_util import Success
from host import FileNode

__author__ = 'zadjii'


class DebugNodesCommand(BaseCommand):
    def add_parser(self, subparsers):
        dbg_nodes = subparsers.add_parser('dbg-nodes', description='Debug print all the nodes in the database.')

        return dbg_nodes

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData
        db = instance.get_db()
        nodes = db.session.query(FileNode).all()
        for node in nodes:
            print(
                '[{:3}]<{}>{}({},{})\t[{:4},{:4}]\t{}'
                .format(
                    node.id
                    , node.name
                    , ' ' * (16 - len(node.name))
                    , node.created_on
                    , node.last_modified
                    , node.parent_id
                    , node.cloud_id
                    , [child.id for child in node.children.all()]
                )
            )
        return Success()
