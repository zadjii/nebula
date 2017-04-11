# I'm aware that right now both the host and remote versions of this are pretty much the same.
# I guess in the future they could diverge, but there's not a lot to do with this necessarily.


def migrate_db(instance, argv):
    instance.migrate()
