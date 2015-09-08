from host import get_db, FileNode

__author__ = 'zadjii'


def dbg_nodes(argv):
    db = get_db()
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


