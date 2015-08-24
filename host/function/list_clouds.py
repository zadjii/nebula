from host import Cloud, get_db

__author__ = 'zadjii'


def list_clouds(argv):
    db = get_db()
    clouds = db.session.query(Cloud).all()
    print 'There are ', len(clouds), 'clouds.'
    print '[{}] {:5} {:16} {:24} {:16} {:8}'.format('id'
                                                    , 'my_id'
                                                    , 'name'
                                                    , 'root'
                                                    , 'address'
                                                    , 'port')
    for cloud in clouds:

        print '[{}] {:5} {:16} {:24} {:16} {:8}'\
            .format(cloud.id, cloud.my_id_from_remote, cloud.name
                    , cloud.root_directory
                    , cloud.remote_host, cloud.remote_port)