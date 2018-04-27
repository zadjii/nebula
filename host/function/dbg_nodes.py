from host import FileNode

__author__ = 'zadjii'


def add_dbg_nodes_argparser(subparsers):
    dbg_nodes = subparsers.add_parser('dbg-nodes', description='Debug print all the nodes in the database.')
    dbg_nodes.set_defaults(func=_do_dbg_nodes)


def _do_dbg_nodes(instance, args):
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


