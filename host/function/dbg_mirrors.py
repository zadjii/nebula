from host import FileNode
from host.models.Cloud import Cloud

__author__ = 'zadjii'


def add_dbg_mirrors_argparser(subparsers):
    dbg_mirrors = subparsers.add_parser('dbg-mirrors', description='Debug print all the mirrors on this device')
    dbg_mirrors.set_defaults(func=_do_dbg_mirrors)


def _do_dbg_mirrors(instance, args):
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


