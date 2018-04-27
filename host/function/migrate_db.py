# I'm aware that right now both the host and remote versions of this are pretty much the same.
# I guess in the future they could diverge, but there's not a lot to do with this necessarily.


def add_migrate_db_argparser(subparsers):
    migrate_db = subparsers.add_parser('migrate-db', description='Generate a database migration, and update the database schema')
    migrate_db.set_defaults(func=_do_migrate_db)


def _do_migrate_db(instance, args):
    instance.migrate()
