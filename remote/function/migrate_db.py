from common.BaseCommand import BaseCommand
from common_util import Success
# I'm aware that right now both the host and remote versions of this are pretty much the same.
# I guess in the future they could diverge, but there's not a lot to do with this necessarily.


class RemoteMigrateCommand(BaseCommand):
    def add_parser(self, subparsers):
        migrate_db = subparsers.add_parser('migrate-db',
                                           description='Generate a database migration, and update the database schema')
        return migrate_db

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData
        instance.migrate()
        return Success()

