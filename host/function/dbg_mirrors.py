from host import FileNode
from host.models.Cloud import Cloud
from common.BaseCommand import BaseCommand
from common_util import ResultAndData, Error, Success
from argparse import Namespace

__author__ = 'zadjii'

class DebugMirrorsCommand(BaseCommand):
    def add_parser(self, subparsers):
        dbg_mirrors = subparsers.add_parser('dbg-mirrors', description='Debug print all the mirrors on this device')
        return dbg_mirrors

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData
        db = instance.get_db()
        mirrors = db.session.query(Cloud).all()
        for mirror in mirrors:
            print(
                '[{:3}]\t{}/{}, {}, {}, {}\n\t{}'
                .format(
                    mirror.id
                    , mirror.username
                    , mirror.name
                    , mirror.created_on
                    , mirror.last_update
                    , mirror.completed_mirroring
                    , [child.name for child in mirror.children.all()]
                )
            )
        return Success()


